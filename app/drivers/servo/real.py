"""
drivers/servo/real.py — PCA9685 舵机真实驱动

通过 PCA9685 I2C PWM 控制 SG90 舵机。
与前大灯共用同一块 PCA9685 (地址 0x40, I2C1_M4)。

SG90 舵机参数:
  - PWM 频率: 50Hz (周期 20ms)
  - 0°:   脉宽 ~0.5ms  → duty = 0.5/20 * 4096 ≈ 102
  - 90°:  脉宽 ~1.5ms  → duty = 1.5/20 * 4096 ≈ 307
  - 180°: 脉宽 ~2.5ms  → duty = 2.5/20 * 4096 ≈ 512

注意: PCA9685 的 PWM 频率会影响所有通道。
舵机需要 50Hz,而大灯用 1kHz。解决方案:
  大灯在 50Hz 下仍可正常调光 (只是频率低了,肉眼不可见闪烁)。
  初始化时将 PCA9685 频率设为 50Hz。
"""

import os
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
_LED0_ON_L = 0x06

_SLEEP = 0x10
_ALLCALL = 0x01
_AI = 0x20
_OUTDRV = 0x04

# SG90 脉宽参数 (50Hz 下的 12-bit 值)
_SERVO_MIN = 102   # 0.5ms → 0°
_SERVO_MAX = 512   # 2.5ms → 180°
_SERVO_FREQ = 50   # 舵机 PWM 频率


class RealServoDriver:
    """
    PCA9685 舵机驱动。

    使用原始 I2C 操作,与 LedDriver 共用 PCA9685 硬件。
    注意: 初始化会将 PCA9685 频率改为 50Hz (舵机需要)。
    """

    def __init__(self):
        self._fd: int | None = None
        self._bus = config.I2C_BUS
        self._addr = config.PCA9685_ADDR
        self._angles: dict[int, float] = {}

    def init(self) -> None:
        self._fd = os.open(f"/dev/i2c-{self._bus}", os.O_RDWR)
        fcntl.ioctl(self._fd, I2C_SLAVE, self._addr)

        # 复位
        self._write_reg(_MODE1, _ALLCALL)
        time.sleep(0.005)

        # 设置 50Hz (舵机频率)
        self._set_pwm_freq(_SERVO_FREQ)

        # 推挽输出
        mode2 = self._read_reg(_MODE2)
        self._write_reg(_MODE2, mode2 | _OUTDRV)

        # 舵机回中
        for ch in (config.SERVO_PAN_CHANNEL, config.SERVO_TILT_CHANNEL):
            self.set_angle(ch, 90)

        logger.info(
            f"RealServoDriver 初始化完成 "
            f"(bus={self._bus}, addr=0x{self._addr:02x}, "
            f"pan=ch{config.SERVO_PAN_CHANNEL}, tilt=ch{config.SERVO_TILT_CHANNEL})"
        )

    def _write_reg(self, reg: int, value: int) -> None:
        os.write(self._fd, bytes([reg, value & 0xFF]))

    def _read_reg(self, reg: int) -> int:
        os.write(self._fd, bytes([reg]))
        return os.read(self._fd, 1)[0]

    def _set_pwm_freq(self, freq_hz: int) -> None:
        prescale = round(25_000_000.0 / (4096 * freq_hz)) - 1
        prescale = max(3, min(255, prescale))

        old_mode = self._read_reg(_MODE1)
        self._write_reg(_MODE1, (old_mode & 0x7F) | _SLEEP)
        self._write_reg(_PRESCALE, prescale)
        self._write_reg(_MODE1, old_mode)
        time.sleep(0.005)
        self._write_reg(_MODE1, old_mode | _AI | 0x80)

        logger.debug(f"PCA9685 PWM 频率: {freq_hz}Hz (prescale={prescale})")

    def _set_pwm(self, channel: int, on: int, off: int) -> None:
        reg = _LED0_ON_L + 4 * channel
        os.write(self._fd, bytes([
            reg,
            on & 0xFF, (on >> 8) & 0x0F,
            off & 0xFF, (off >> 8) & 0x0F,
        ]))

    def set_angle(self, channel: int, angle: float) -> None:
        angle = max(0, min(180, angle))
        duty = int(_SERVO_MIN + (_SERVO_MAX - _SERVO_MIN) * angle / 180)
        self._set_pwm(channel, 0, duty)
        self._angles[channel] = angle
        logger.debug(f"Servo ch{channel}: {angle:.1f}° (duty={duty})")

    def get_angle(self, channel: int) -> float:
        return self._angles.get(channel, 90.0)

    def cleanup(self) -> None:
        if self._fd is not None:
            # 回中
            for ch in (config.SERVO_PAN_CHANNEL, config.SERVO_TILT_CHANNEL):
                self.set_angle(ch, 90)
            time.sleep(0.3)
            # 关闭 PWM 输出 (避免舵机抖动)
            for ch in (config.SERVO_PAN_CHANNEL, config.SERVO_TILT_CHANNEL):
                self._set_pwm(ch, 0, 4096)
            os.close(self._fd)
            self._fd = None
            logger.info("RealServoDriver 资源已释放")
