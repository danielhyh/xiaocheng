"""
drivers/adc/protocol.py — ADC 驱动接口定义

所有 ADC 驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。
"""

from typing import Protocol


class ADCDriverProtocol(Protocol):
    """ADC 驱动接口"""

    def init(self) -> None:
        """初始化硬件资源 (打开 I2C 总线等)"""
        ...

    def read_voltage(self, channel: int = 0) -> float:
        """
        读取指定通道的电压值。

        参数:
            channel: ADC 通道号 (0-3)

        返回:
            ADC 引脚上的实际电压 (V),未经分压还原。
            例如分压后 2.65V 就返回 2.65,由上层乘以分压比。
        """
        ...

    def cleanup(self) -> None:
        """释放硬件资源"""
        ...
