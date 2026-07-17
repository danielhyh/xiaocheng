"""
drivers/led — 前大灯驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import LedDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.led.mock import MockLedDriver as LedDriver
else:
    from app.drivers.led.real import RealLedDriver as LedDriver

__all__ = ["LedDriver"]
