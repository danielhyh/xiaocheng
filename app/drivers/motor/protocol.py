"""
drivers/motor/protocol.py — 电机驱动接口定义

所有电机驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。
"""

from typing import Protocol


class MotorDriverProtocol(Protocol):
    """电机驱动接口"""

    def init(self) -> None:
        """初始化硬件资源"""
        ...

    def set_motors(self, left_speed: float, right_speed: float) -> None:
        """
        直接设置左右电机速度。

        参数:
            left_speed:  -100 到 100, 正=前进, 负=后退
            right_speed: -100 到 100, 正=前进, 负=后退
        """
        ...

    def stop(self) -> None:
        """停止所有电机"""
        ...

    def brake(self) -> None:
        """紧急制动"""
        ...

    def cleanup(self) -> None:
        """释放硬件资源"""
        ...

    @property
    def current_state(self) -> dict:
        """返回当前电机状态 (用于遥测)"""
        ...
