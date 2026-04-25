"""
drivers/motor — 电机驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import MotorDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.motor.mock import MockMotorDriver as MotorDriver
else:
    from app.drivers.motor.real import RealMotorDriver as MotorDriver

__all__ = ["MotorDriver"]
