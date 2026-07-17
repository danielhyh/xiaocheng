"""
drivers/ultrasonic — 超声波驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import UltrasonicDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.ultrasonic.mock import MockUltrasonicDriver as UltrasonicDriver
else:
    from app.drivers.ultrasonic.real import RealUltrasonicDriver as UltrasonicDriver

__all__ = ["UltrasonicDriver"]
