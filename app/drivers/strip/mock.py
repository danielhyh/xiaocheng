"""
drivers/strip/mock.py — Mock WS2812B 灯带驱动

接口与 RealStripDriver 完全一致。
只打日志,PC 上开发测试用。
"""

import logging

from app import config

logger = logging.getLogger(__name__)


class MockStripDriver:
    """
    Mock 灯带驱动。

    维护像素缓冲区用于状态查询,所有操作只打日志。
    """

    def __init__(self):
        self._num_leds = config.STRIP_NUM_LEDS
        self._brightness = config.STRIP_DEFAULT_BRIGHTNESS
        self._buffer = [(0, 0, 0)] * self._num_leds
        self._segments = config.STRIP_SEGMENTS
        self._initialized = False

    @property
    def num_leds(self) -> int:
        return self._num_leds

    def init(self) -> None:
        self._initialized = True
        logger.info(f"[MOCK] StripDriver 初始化完成 (leds={self._num_leds})")

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        if 0 <= index < self._num_leds:
            self._buffer[index] = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b)),
            )

    def set_segment(self, segment: str, r: int, g: int, b: int) -> None:
        if segment == "all":
            for i in range(self._num_leds):
                self.set_pixel(i, r, g, b)
        elif segment in self._segments:
            start, end = self._segments[segment]
            for i in range(start, end + 1):
                self.set_pixel(i, r, g, b)

    def show(self) -> None:
        # 只在有非零像素时打日志,避免刷屏
        active = [(i, rgb) for i, rgb in enumerate(self._buffer) if any(rgb)]
        if active:
            logger.debug(f"[MOCK] Strip show: {len(active)} active pixels")

    def clear(self) -> None:
        self._buffer = [(0, 0, 0)] * self._num_leds
        logger.debug("[MOCK] Strip cleared")

    def set_brightness(self, brightness: int) -> None:
        self._brightness = max(0, min(255, brightness))
        logger.debug(f"[MOCK] Strip brightness: {self._brightness}/255")

    def cleanup(self) -> None:
        if self._initialized:
            self._buffer = [(0, 0, 0)] * self._num_leds
            self._initialized = False
            logger.info("[MOCK] StripDriver 资源已释放")
