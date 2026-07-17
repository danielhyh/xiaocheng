"""
drivers/led/mock.py — Mock 前大灯驱动

接口与 RealLedDriver 完全一致。
只打日志,PC 上开发测试用。
"""

import logging

logger = logging.getLogger(__name__)


class MockLedDriver:
    """
    Mock 前大灯驱动。

    模拟左右大灯亮度状态,所有操作只打日志。
    """

    def __init__(self):
        self._initialized = False
        self._brightness = {"left": 0, "right": 0}

    def init(self) -> None:
        self._initialized = True
        logger.info("[MOCK] LedDriver 初始化完成")

    def set_brightness(self, channel: str, brightness: int) -> None:
        brightness = max(0, min(100, brightness))
        self._brightness[channel] = brightness
        logger.debug(f"[MOCK] LED {channel}: {brightness}%")

    def set_both(self, brightness: int) -> None:
        self.set_brightness("left", brightness)
        self.set_brightness("right", brightness)

    def cleanup(self) -> None:
        if self._initialized:
            self._brightness = {"left": 0, "right": 0}
            self._initialized = False
            logger.info("[MOCK] LedDriver 资源已释放")
