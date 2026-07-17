"""
drivers/servo — 舵机驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import ServoDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.servo.mock import MockServoDriver as ServoDriver
else:
    from app.drivers.servo.real import RealServoDriver as ServoDriver

__all__ = ["ServoDriver"]
