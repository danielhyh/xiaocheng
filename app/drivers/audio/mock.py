"""
drivers/audio/mock.py — Mock 音频驱动

接口与 RealAudioDriver 完全一致。
只打日志,PC 上开发测试用。
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class MockAudioDriver:
    """
    Mock 音频驱动。

    所有操作只打日志,不播放声音。
    """

    def __init__(self):
        self._volume = 80
        self._initialized = False

    def init(self) -> None:
        self._initialized = True
        logger.info("[MOCK] AudioDriver 初始化完成")

    async def play(self, filepath: str) -> None:
        logger.info(f"[MOCK] 播放音频: {filepath}")
        # 模拟播放耗时
        await asyncio.sleep(0.1)

    async def tts(self, text: str, voice: str = "") -> None:
        logger.info(f"[MOCK] TTS: '{text}' (voice={voice or 'default'})")
        await asyncio.sleep(0.2)

    def set_volume(self, level: int) -> None:
        self._volume = max(0, min(100, level))
        logger.info(f"[MOCK] 音量设置: {self._volume}%")

    def get_volume(self) -> int:
        return self._volume

    def stop(self) -> None:
        logger.info("[MOCK] 停止播放")

    def cleanup(self) -> None:
        if self._initialized:
            self._initialized = False
            logger.info("[MOCK] AudioDriver 资源已释放")
