"""
drivers/led/protocol.py — 前大灯驱动接口定义

所有前大灯驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。

前大灯通过 PCA9685 PWM → IRF520 MOSFET 驱动 3W LED。
左右大灯独立控制,支持 PWM 调光。
"""

from typing import Protocol


class LedDriverProtocol(Protocol):
    """前大灯驱动接口"""

    def init(self) -> None:
        """初始化 PCA9685 (I2C 通信 + PWM 频率设置)"""
        ...

    def set_brightness(self, channel: str, brightness: int) -> None:
        """
        设置指定大灯亮度。

        参数:
            channel: "left" 或 "right"
            brightness: 0 (灭) ~ 100 (全亮)
        """
        ...

    def set_both(self, brightness: int) -> None:
        """
        同时设置左右大灯亮度。

        参数:
            brightness: 0 ~ 100
        """
        ...

    def cleanup(self) -> None:
        """关闭大灯,释放资源"""
        ...
