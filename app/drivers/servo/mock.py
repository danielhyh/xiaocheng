"""
drivers/servo/mock.py — Mock 舵机驱动

接口与 RealServoDriver 完全一致。
只打日志,PC 上开发测试用。
"""

import logging

logger = logging.getLogger(__name__)


class MockServoDriver:
    """
    Mock 舵机驱动。

    维护角度状态,所有操作只打日志。
    """

    def __init__(self):
        self._initialized = False
        self._angles: dict[int, float] = {}

    def init(self) -> None:
        self._initialized = True
        self._angles = {}
        logger.info("[MOCK] ServoDriver 初始化完成")

    def set_angle(self, channel: int, angle: float) -> None:
        angle = max(0, min(180, angle))
        self._angles[channel] = angle
        logger.debug(f"[MOCK] Servo ch{channel}: {angle:.1f}°")

    def get_angle(self, channel: int) -> float:
        return self._angles.get(channel, 90.0)

    def cleanup(self) -> None:
        if self._initialized:
            self._angles = {}
            self._initialized = False
            logger.info("[MOCK] ServoDriver 资源已释放")
