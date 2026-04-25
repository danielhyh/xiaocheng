"""
drivers/adc/real.py — ADS1115 真实 ADC 驱动

通过原始 I2C (os + fcntl) 读取 ADS1115,零第三方依赖。
只在 Orange Pi 上运行。
"""

import os
import struct
import fcntl
import time
import logging

from app import config

logger = logging.getLogger(__name__)

I2C_SLAVE = 0x0703

# ADS1115 寄存器地址
_REG_CONVERSION = 0x00
_REG_CONFIG = 0x01

# 配置位模板 (单次转换, FSR=±4.096V, 128SPS)
# Bit [15]    OS     = 1  (开始单次转换)
# Bit [14:12] MUX    = 1xx (AINx vs GND, 由 channel 决定)
# Bit [11:9]  PGA    = 001 (±4.096V)
# Bit [8]     MODE   = 1  (单次)
# Bit [7:5]   DR     = 100 (128SPS)
# Bit [4]     COMP_MODE = 0
# Bit [3:2]   COMP_POL/LAT = 00
# Bit [1:0]   COMP_QUE = 11 (禁用比较器)
_CONFIG_BASE = 0b1_000_001_1_100_0_0_0_11  # 0x8383, MUX=000 即 AIN0


class RealADCDriver:
    """
    ADS1115 I2C ADC 驱动。

    使用原始 I2C 操作,不依赖 smbus2 / adafruit 等库。
    FSR 固定 ±4.096V,LSB = 0.000125V。
    """

    def __init__(self):
        self._fd: int | None = None
        self._bus = config.I2C_BUS
        self._addr = config.ADS1115_ADDR

    def init(self) -> None:
        self._fd = os.open(f"/dev/i2c-{self._bus}", os.O_RDWR)
        fcntl.ioctl(self._fd, I2C_SLAVE, self._addr)
        logger.info(
            f"RealADCDriver 初始化完成 (bus={self._bus}, addr=0x{self._addr:02x})"
        )

    def read_voltage(self, channel: int = 0) -> float:
        """
        单次转换读取指定通道电压。

        参数:
            channel: 0-3, 对应 AIN0-AIN3 vs GND

        返回:
            ADC 引脚电压 (V)
        """
        if self._fd is None:
            raise RuntimeError("ADC 未初始化,请先调用 init()")

        if not 0 <= channel <= 3:
            raise ValueError(f"channel 必须是 0-3, 收到 {channel}")

        # 设置 MUX 位: AINx vs GND → MUX = 100 + channel
        # MUX 在 bit [14:12], 值 = 0b100 + channel
        mux = (0b100 + channel) << 12
        cfg = (_CONFIG_BASE & 0b0_000_111_1_111_1_1_1_11) | mux | (1 << 15)

        # 写配置寄存器,启动转换
        os.write(self._fd, struct.pack(">BH", _REG_CONFIG, cfg))

        # 等待转换完成 (~8ms for 128SPS, 留余量)
        time.sleep(0.01)

        # 读转换结果
        os.write(self._fd, bytes([_REG_CONVERSION]))
        raw = os.read(self._fd, 2)
        value = struct.unpack(">h", raw)[0]

        # FSR=±4.096V, 16位有符号 → LSB = 4.096 / 32768
        voltage = value * config.ADS1115_FSR / 32768.0
        return voltage

    def cleanup(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            logger.info("RealADCDriver 资源已释放")
