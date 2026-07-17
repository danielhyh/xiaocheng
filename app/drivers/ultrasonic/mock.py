"""
drivers/ultrasonic/mock.py — Mock 超声波驱动

接口与 RealUltrasonicDriver 完全一致。
返回模拟距离值,PC 上开发测试用。
"""

import random
import logging

logger = logging.getLogger(__name__)


class MockUltrasonicDriver:
    """
    Mock 超声波驱动。

    模拟前后方障碍物距离,带随机波动。
    """

    def __init__(self):
        self._initialized = False
        self._distances = {
            "front": 120.0,  # 前方 120cm
            "rear": 80.0,    # 后方 80cm
        }

    def init(self) -> None:
        self._initialized = True
        logger.info("[MOCK] UltrasonicDriver 初始化完成")

    def measure(self, sensor: str) -> float | None:
        if sensor not in self._distances:
            return None

        # 模拟距离缓慢变化 + 噪声
        base = self._distances[sensor]
        base += random.uniform(-0.5, 0.5)
        base = max(5, min(300, base))
        self._distances[sensor] = base

        noise = random.uniform(-1.0, 1.0)
        distance = round(base + noise, 1)

        logger.debug(f"[MOCK] Ultrasonic {sensor}: {distance}cm")
        return distance

    def cleanup(self) -> None:
        if self._initialized:
            self._initialized = False
            logger.info("[MOCK] UltrasonicDriver 资源已释放")
