"""
drivers/strip — WS2812B 灯带驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import StripDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.strip.mock import MockStripDriver as StripDriver
else:
    from app.drivers.strip.real import RealStripDriver as StripDriver

__all__ = ["StripDriver"]
