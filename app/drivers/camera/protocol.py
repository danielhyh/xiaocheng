"""
drivers/camera/protocol.py — 摄像头驱动接口定义

所有摄像头驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。
"""

from typing import Protocol
import numpy as np


class CameraDriverProtocol(Protocol):
    """摄像头驱动接口"""

    def init(self) -> None:
        """初始化摄像头硬件 (打开设备、设置分辨率等)"""
        ...

    def read_frame(self) -> np.ndarray | None:
        """
        读取一帧图像。

        返回:
            BGR 格式的 numpy 数组 (OpenCV 标准格式),
            如果读取失败返回 None。
        """
        ...

    @property
    def is_opened(self) -> bool:
        """摄像头是否已打开"""
        ...

    @property
    def resolution(self) -> tuple[int, int]:
        """返回 (宽, 高)"""
        ...

    def cleanup(self) -> None:
        """释放摄像头资源"""
        ...
