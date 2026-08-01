"""
drivers/led/real.py — PCA9685 前大灯真实驱动

通过原始 I2C 操作控制 PCA9685,驱动 IRF520 MOSFET → 3W LED。
零第三方依赖,只在 Orange Pi 上运行。

PCA9685 基础:
  - 16 通道 12-bit PWM (0-4095)
  - I2C 地址默认 0x40
  - 每通道有 ON/OFF 两个 12-bit 寄存器控制占空比
  - 内部 25MHz 振荡器,通过 prescale 设置 PWM 频率
"""

import os
import struct
import fcntl
import time
import logging

from app import config

logger = logging.getLogger(__name__)

I2C_SLAVE = 0x0703

# PCA9685 寄存器
_MODE1 = 0x00
_MODE2 = 0x01
_PRESCALE = 0xFE
_LED0_ON_L = 0x06  # 每通道 4 字节: ON_L, ON_H, OFF_L, OFF_H

# MODE1 位
_SLEEP = 0x10
_ALLCALL = 0x01
_AI = 0x20  # Auto-Increment

# MODE2 位
_OUTDRV = 0x04  # 推挽输出


class RealLedDriver:
    """
    PCA9685 前大灯驱动。

    使用原始 I2C 操作,不依赖 adafruit 等库。
    左右大灯各占一个 PCA9685 通道,通过 IRF520 MOSFET 驱动 3W LED。
    """

    def __init__(self):
        self._fd: int | None = None
        self._bus = config.I2C_BUS
        self._addr = config.PCA9685_ADDR
        self._left_ch = config.LED_LEFT_CHANNEL
        self._right_ch = config.LED_RIGHT_CHANNEL

    def init(self) -> None:
        if self._left_ch is None or self._right_ch is None:
            raise RuntimeError(
                "旧 PCA9685 大灯驱动已禁用；完成 P8-01 Pin 33 sysfs PWM "
                "迁移前请保持 XIAOCHENG_ENABLE_LIGHTING=0"
            )
        self._fd = os.open(f"/dev/i2c-{self._bus}", os.O_RDWR)
        fcntl.ioctl(self._fd, I2C_SLAVE, self._addr)

        # 复位 PCA9685
        self._write_reg(_MODE1, _ALLCALL)
        time.sleep(0.005)

        # 设置 PWM 频率 (1kHz,与电机 PWM 一致)
        self._set_pwm_freq(config.LED_PWM_FREQ)

        # 推挽输出
        mode2 = self._read_reg(_MODE2)
        self._write_reg(_MODE2, mode2 | _OUTDRV)

        # 关闭所有灯
        self.set_both(0)

        logger.info(
            f"RealLedDriver 初始化完成 "
            f"(bus={self._bus}, addr=0x{self._addr:02x}, "
            f"left=ch{self._left_ch}, right=ch{self._right_ch})"
        )

    def _write_reg(self, reg: int, value: int) -> None:
        os.write(self._fd, bytes([reg, value & 0xFF]))

    def _read_reg(self, reg: int) -> int:
        os.write(self._fd, bytes([reg]))
        return os.read(self._fd, 1)[0]

    def _set_pwm_freq(self, freq_hz: int) -> None:
        """设置 PCA9685 PWM 频率"""
        # prescale = round(25MHz / (4096 * freq)) - 1
        prescale = round(25_000_000.0 / (4096 * freq_hz)) - 1
        prescale = max(3, min(255, prescale))

        old_mode = self._read_reg(_MODE1)
        # 必须先进入 sleep 模式才能改 prescale
        self._write_reg(_MODE1, (old_mode & 0x7F) | _SLEEP)
        self._write_reg(_PRESCALE, prescale)
        self._write_reg(_MODE1, old_mode)
        time.sleep(0.005)
        # 启用 auto-increment + restart
        self._write_reg(_MODE1, old_mode | _AI | 0x80)

        logger.debug(f"PCA9685 PWM 频率: {freq_hz}Hz (prescale={prescale})")

    def _set_pwm(self, channel: int, on: int, off: int) -> None:
        """设置单个通道的 PWM 占空比 (12-bit: 0-4095)"""
        reg = _LED0_ON_L + 4 * channel
        os.write(self._fd, bytes([
            reg,
            on & 0xFF, (on >> 8) & 0x0F,
            off & 0xFF, (off >> 8) & 0x0F,
        ]))

    def set_brightness(self, channel: str, brightness: int) -> None:
        brightness = max(0, min(100, brightness))
        ch = self._left_ch if channel == "left" else self._right_ch

        if brightness == 0:
            # 全灭: OFF 位 bit12 = 1
            self._set_pwm(ch, 0, 4096)
        elif brightness == 100:
            # 全亮: ON 位 bit12 = 1
            self._set_pwm(ch, 4096, 0)
        else:
            # PWM 调光: duty = brightness% of 4095
            duty = round(brightness / 100 * 4095)
            self._set_pwm(ch, 0, duty)

        logger.debug(f"LED {channel}: {brightness}%")

    def set_both(self, brightness: int) -> None:
        self.set_brightness("left", brightness)
        self.set_brightness("right", brightness)

    def cleanup(self) -> None:
        if self._fd is not None:
            self.set_both(0)
            os.close(self._fd)
            self._fd = None
            logger.info("RealLedDriver 资源已释放")
