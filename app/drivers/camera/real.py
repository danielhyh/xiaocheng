"""
drivers/camera/real.py — 真实摄像头驱动

使用 OpenCV VideoCapture 读取 V4L2 设备 (OV5640 USB/CSI)。
只在 Orange Pi 上运行。
"""

import logging

import cv2
import numpy as np

from app import config

logger = logging.getLogger(__name__)


class RealCameraDriver:
    """
    OV5640 摄像头驱动。

    通过 OpenCV V4L2 后端打开设备,设置分辨率和帧率。
    read_frame() 返回 BGR numpy 数组。
    """

    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._width = config.CAMERA_WIDTH
        self._height = config.CAMERA_HEIGHT

    def init(self) -> None:
        self._cap = cv2.VideoCapture(config.CAMERA_DEVICE, cv2.CAP_V4L2)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"无法打开摄像头设备 {config.CAMERA_DEVICE}"
            )

        # 设置分辨率和帧率
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        # 减小缓冲区,降低延迟
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # 读回实际值
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._width = actual_w
        self._height = actual_h

        logger.info(
            f"RealCameraDriver 初始化完成: "
            f"{actual_w}x{actual_h} @ {actual_fps:.0f}fps, "
            f"设备={config.CAMERA_DEVICE}"
        )

    def read_frame(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    @property
    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    @property
    def resolution(self) -> tuple[int, int]:
        return (self._width, self._height)

    def cleanup(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("RealCameraDriver 资源已释放")
