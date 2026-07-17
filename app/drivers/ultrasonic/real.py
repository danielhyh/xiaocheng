"""
drivers/ultrasonic/real.py — HC-SR04 超声波真实驱动

通过 wiringOP GPIO 控制 HC-SR04 模块。
前后各一个,独立 Trig + Echo 引脚。

测距原理:
  1. Trig 拉高 10μs 触发
  2. 等待 Echo 变高
  3. 计时 Echo 高电平持续时间
  4. 距离 = 时间 × 声速(343m/s) / 2

注意: Echo 引脚需要 5V→3.3V 分压 (2KΩ+1KΩ)。
"""

import time
import logging

import wiringpi
from wiringpi import GPIO

from app import config

logger = logging.getLogger(__name__)

# 声速 343m/s = 34300 cm/s, 来回除以 2 = 17150 cm/s
_SPEED_OF_SOUND_HALF = 17150.0
_TIMEOUT = 0.03  # 30ms 超时 (~5m 距离)


class RealUltrasonicDriver:
    """
    HC-SR04 双超声波驱动。

    前方 + 后方各一个 HC-SR04,独立 GPIO 控制。
    """

    def __init__(self):
        self._sensors = {
            "front": {
                "trig": config.US_FRONT_TRIG,
                "echo": config.US_FRONT_ECHO,
            },
            "rear": {
                "trig": config.US_REAR_TRIG,
                "echo": config.US_REAR_ECHO,
            },
        }
        self._initialized = False

    def init(self) -> None:
        # wiringPiSetup 可能已被 motor 驱动调用过
        try:
            wiringpi.wiringPiSetup()
        except Exception:
            pass

        for name, pins in self._sensors.items():
            wiringpi.pinMode(pins["trig"], GPIO.OUTPUT)
            wiringpi.pinMode(pins["echo"], GPIO.INPUT)
            wiringpi.digitalWrite(pins["trig"], GPIO.LOW)

        self._initialized = True
        time.sleep(0.05)  # 等待传感器稳定
        logger.info("RealUltrasonicDriver 初始化完成")

    def measure(self, sensor: str) -> float | None:
        if sensor not in self._sensors:
            logger.warning(f"未知超声波传感器: {sensor}")
            return None

        pins = self._sensors[sensor]
        trig = pins["trig"]
        echo = pins["echo"]

        # 触发: Trig 拉高 10μs
        wiringpi.digitalWrite(trig, GPIO.LOW)
        time.sleep(0.000002)
        wiringpi.digitalWrite(trig, GPIO.HIGH)
        time.sleep(0.00001)
        wiringpi.digitalWrite(trig, GPIO.LOW)

        # 等待 Echo 变高
        start_wait = time.monotonic()
        while wiringpi.digitalRead(echo) == GPIO.LOW:
            if time.monotonic() - start_wait > _TIMEOUT:
                return None

        # 计时 Echo 高电平
        pulse_start = time.monotonic()
        while wiringpi.digitalRead(echo) == GPIO.HIGH:
            if time.monotonic() - pulse_start > _TIMEOUT:
                return None

        pulse_end = time.monotonic()
        duration = pulse_end - pulse_start
        distance = duration * _SPEED_OF_SOUND_HALF

        # 有效范围 2-400cm
        if distance < 2 or distance > 400:
            return None

        return round(distance, 1)

    def cleanup(self) -> None:
        if self._initialized:
            for pins in self._sensors.values():
                wiringpi.digitalWrite(pins["trig"], GPIO.LOW)
            self._initialized = False
            logger.info("RealUltrasonicDriver 资源已释放")
