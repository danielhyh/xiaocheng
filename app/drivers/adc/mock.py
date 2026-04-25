"""
drivers/adc/mock.py — Mock ADC 驱动

接口与 RealADCDriver 完全一致。
返回模拟电压值,PC 上开发测试用。
"""

import random
import logging

from app import config

logger = logging.getLogger(__name__)


class MockADCDriver:
    """
    Mock ADC 驱动。

    模拟一个缓慢放电的电池:
    - 初始电压 ~2.6V (对应电池 ~7.8V)
    - 每次读取微降,模拟放电过程
    - 叠加小幅随机噪声
    """

    def __init__(self):
        self._initialized = False
        # 模拟分压后的 ADC 电压 (~7.8V / 3 = 2.6V)
        self._simulated_voltage = 2.6

    def init(self) -> None:
        self._initialized = True
        logger.info("[MOCK] ADCDriver 初始化完成")

    def read_voltage(self, channel: int = 0) -> float:
        """返回模拟电压值,带微小波动"""
        # 缓慢放电 (每次读取降 ~0.0001V,约 1000 次读取降 0.1V)
        self._simulated_voltage -= 0.0001
        self._simulated_voltage = max(self._simulated_voltage, 1.8)

        # 叠加噪声 ±0.01V
        noise = random.uniform(-0.01, 0.01)
        voltage = self._simulated_voltage + noise

        logger.debug(f"[MOCK] ADC ch{channel}: {voltage:.4f}V")
        return voltage

    def cleanup(self) -> None:
        if self._initialized:
            self._initialized = False
            logger.info("[MOCK] ADCDriver 资源已释放")
