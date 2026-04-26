"""
drivers/audio — 音频驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import AudioDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.audio.mock import MockAudioDriver as AudioDriver
else:
    from app.drivers.audio.real import RealAudioDriver as AudioDriver

__all__ = ["AudioDriver"]
