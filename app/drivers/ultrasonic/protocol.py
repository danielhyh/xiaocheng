"""
drivers/ultrasonic/protocol.py — 超声波驱动接口定义

所有超声波驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。

HC-SR04 超声波模块:
  - Trig: 10μs 高电平触发
  - Echo: 高电平持续时间 = 距离 × 2 / 声速
  - 测距范围: 2cm ~ 400cm
  - Echo 需 5V→3.3V 分压 (2KΩ+1KΩ)
"""

from typing import Protocol


class UltrasonicDriverProtocol(Protocol):
    """超声波驱动接口"""

    def init(self) -> None:
        """初始化 GPIO"""
        ...

    def measure(self, sensor: str) -> float | None:
        """
        测量距离。

        参数:
            sensor: "front" 或 "rear"

        返回:
            距离 (cm),测量失败返回 None。
        """
        ...

    def cleanup(self) -> None:
        """释放 GPIO"""
        ...
