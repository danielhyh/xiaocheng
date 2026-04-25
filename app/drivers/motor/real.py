"""
drivers/motor/real.py — 真实电机驱动

封装 sysfs PWM + wiringOP GPIO,只在 Orange Pi 上运行。
从原 motor.py 重构而来,保留所有经过实测验证的逻辑。
"""

import os
import time
import atexit
import logging

import wiringpi
from wiringpi import GPIO

from app import config

logger = logging.getLogger(__name__)


class _PWMChannel:
    """sysfs PWM 封装 (从原 motor.py 移植)"""

    def __init__(self, chip_path: str, channel: str, period_ns: int, inverted: bool = False):
        self.chip_path = chip_path
        self.channel = channel
        self.pwm_path = f"{chip_path}/pwm{channel}"
        self.period_ns = period_ns
        self.inverted = inverted
        self._exported = False

    def init(self):
        if not os.path.exists(self.pwm_path):
            self._write(f"{self.chip_path}/export", self.channel)
            time.sleep(0.1)
            self._exported = True
        self._write(f"{self.pwm_path}/period", self.period_ns)
        self._write(f"{self.pwm_path}/duty_cycle", 0)
        self._write(f"{self.pwm_path}/enable", 1)

    def set_duty(self, percent: float):
        percent = max(0, min(100, percent))
        actual = (100 - percent) if self.inverted else percent
        duty_ns = int(self.period_ns * actual / 100)
        self._write(f"{self.pwm_path}/duty_cycle", duty_ns)

    def cleanup(self):
        try:
            self._write(f"{self.pwm_path}/duty_cycle", 0)
            self._write(f"{self.pwm_path}/enable", 0)
            if self._exported:
                self._write(f"{self.chip_path}/unexport", self.channel)
        except Exception:
            pass

    @staticmethod
    def _write(path, value):
        with open(path, "w") as f:
            f.write(str(value))


class _Motor:
    """单侧电机控制 (从原 motor.py 移植)"""

    def __init__(self, name: str, pin_a: int, pin_b: int, pwm: _PWMChannel):
        self.name = name
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.pwm = pwm

    def init(self):
        wiringpi.pinMode(self.pin_a, GPIO.OUTPUT)
        wiringpi.pinMode(self.pin_b, GPIO.OUTPUT)
        wiringpi.digitalWrite(self.pin_a, GPIO.LOW)
        wiringpi.digitalWrite(self.pin_b, GPIO.LOW)
        self.pwm.init()

    def forward(self, speed: float):
        wiringpi.digitalWrite(self.pin_a, GPIO.HIGH)
        wiringpi.digitalWrite(self.pin_b, GPIO.LOW)
        self.pwm.set_duty(speed)

    def backward(self, speed: float):
        wiringpi.digitalWrite(self.pin_a, GPIO.LOW)
        wiringpi.digitalWrite(self.pin_b, GPIO.HIGH)
        self.pwm.set_duty(speed)

    def stop(self):
        self.pwm.set_duty(0)
        wiringpi.digitalWrite(self.pin_a, GPIO.LOW)
        wiringpi.digitalWrite(self.pin_b, GPIO.LOW)

    def brake(self):
        self.pwm.set_duty(0)
        wiringpi.digitalWrite(self.pin_a, GPIO.HIGH)
        wiringpi.digitalWrite(self.pin_b, GPIO.HIGH)

    def cleanup(self):
        self.stop()
        self.pwm.cleanup()


class RealMotorDriver:
    """
    真实电机驱动,管理 L298N 的两侧电机。

    接口: set_motors(left_speed, right_speed)
    速度范围: -100 ~ 100, 正=前进, 负=后退
    内部做死区映射。
    """

    def __init__(self):
        left_pwm = _PWMChannel(
            config.LEFT_PWM_CHIP, config.LEFT_PWM_CH,
            config.PWM_PERIOD_NS, config.PWM_INVERTED,
        )
        right_pwm = _PWMChannel(
            config.RIGHT_PWM_CHIP, config.RIGHT_PWM_CH,
            config.PWM_PERIOD_NS, config.PWM_INVERTED,
        )
        self._left = _Motor("左侧", config.LEFT_IN1, config.LEFT_IN2, left_pwm)
        self._right = _Motor("右侧", config.RIGHT_IN3, config.RIGHT_IN4, right_pwm)
        self._initialized = False
        self._left_speed = 0.0
        self._right_speed = 0.0

    def init(self) -> None:
        wiringpi.wiringPiSetup()
        self._left.init()
        self._right.init()
        self._initialized = True
        atexit.register(self.cleanup)
        logger.info("RealMotorDriver 初始化完成")

    def _map_speed(self, speed: float) -> float:
        """死区映射: 用户 0-100 → 电机 DEAD_ZONE-100"""
        if speed <= 0:
            return 0
        speed = min(speed, 100)
        dz = config.MOTOR_DEAD_ZONE
        return dz + speed * (100 - dz) / 100

    def _drive_motor(self, motor: _Motor, speed: float):
        if speed > 0:
            motor.forward(self._map_speed(speed))
        elif speed < 0:
            motor.backward(self._map_speed(abs(speed)))
        else:
            motor.stop()

    def set_motors(self, left_speed: float, right_speed: float) -> None:
        self._left_speed = left_speed
        self._right_speed = right_speed
        self._drive_motor(self._left, left_speed)
        self._drive_motor(self._right, right_speed)

    def stop(self) -> None:
        self._left_speed = 0
        self._right_speed = 0
        self._left.stop()
        self._right.stop()

    def brake(self) -> None:
        self._left_speed = 0
        self._right_speed = 0
        self._left.brake()
        self._right.brake()

    def cleanup(self) -> None:
        if self._initialized:
            self._left.cleanup()
            self._right.cleanup()
            self._initialized = False
            logger.info("RealMotorDriver 资源已释放")

    @property
    def current_state(self) -> dict:
        return {
            "left_speed": self._left_speed,
            "right_speed": self._right_speed,
        }
