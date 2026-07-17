"""
drivers/servo/protocol.py — 舵机驱动接口定义

所有舵机驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。

舵机通过 PCA9685 I2C PWM 驱动 (与前大灯共用同一块 PCA9685)。
"""

from typing import Protocol


class ServoDriverProtocol(Protocol):
    """舵机驱动接口"""

    def init(self) -> None:
        """初始化 PCA9685 (如果尚未初始化)"""
        ...

    def set_angle(self, channel: int, angle: float) -> None:
        """
        设置指定通道舵机角度。

        参数:
            channel: PCA9685 通道号
            angle: 目标角度 (0-180)
        """
        ...

    def get_angle(self, channel: int) -> float:
        """获取指定通道当前角度"""
        ...

    def cleanup(self) -> None:
        """释放资源,舵机回中"""
        ...
