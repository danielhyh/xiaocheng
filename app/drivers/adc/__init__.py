"""
drivers/adc — ADC 驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import ADCDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.adc.mock import MockADCDriver as ADCDriver
else:
    from app.drivers.adc.real import RealADCDriver as ADCDriver

__all__ = ["ADCDriver"]
