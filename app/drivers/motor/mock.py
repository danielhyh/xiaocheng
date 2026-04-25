"""
drivers/motor/mock.py — Mock 电机驱动

接口与 RealMotorDriver 完全一致。
打印关键动作到日志,维护内部状态,产生合理的伪遥测。
PC 上开发前端时用这个,不需要真板子。
"""

import logging

logger = logging.getLogger(__name__)


class MockMotorDriver:
    """
    Mock 电机驱动。

    - 接口完全一致 (同 Protocol)
    - 关键动作打日志
    - 维护内部速度状态
    """

    def __init__(self):
        self._left_speed = 0.0
        self._right_speed = 0.0
        self._initialized = False

    def init(self) -> None:
        self._initialized = True
        logger.info("[MOCK] MotorDriver 初始化完成")

    def set_motors(self, left_speed: float, right_speed: float) -> None:
        self._left_speed = max(-100, min(100, left_speed))
        self._right_speed = max(-100, min(100, right_speed))
        logger.debug(
            f"[MOCK] motors: L={self._left_speed:+.1f}% R={self._right_speed:+.1f}%"
        )

    def stop(self) -> None:
        self._left_speed = 0
        self._right_speed = 0
        logger.debug("[MOCK] motors: STOP")

    def brake(self) -> None:
        self._left_speed = 0
        self._right_speed = 0
        logger.debug("[MOCK] motors: BRAKE")

    def cleanup(self) -> None:
        if self._initialized:
            self.stop()
            self._initialized = False
            logger.info("[MOCK] MotorDriver 资源已释放")

    @property
    def current_state(self) -> dict:
        return {
            "left_speed": self._left_speed,
            "right_speed": self._right_speed,
        }
