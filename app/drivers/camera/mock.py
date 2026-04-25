"""
drivers/camera/mock.py — Mock 摄像头驱动

接口与 RealCameraDriver 完全一致。
生成带时间戳和网格的测试图案,PC 上开发前端时用。
"""

import time
import logging

import cv2
import numpy as np

from app import config

logger = logging.getLogger(__name__)


class MockCameraDriver:
    """
    Mock 摄像头驱动。

    生成动态测试图案:
    - 深色背景 + 网格线
    - 中心十字准星
    - 实时时间戳
    - 帧计数器
    - 模拟 FPV 风格
    """

    def __init__(self):
        self._width = config.CAMERA_WIDTH
        self._height = config.CAMERA_HEIGHT
        self._opened = False
        self._frame_count = 0

    def init(self) -> None:
        self._opened = True
        self._frame_count = 0
        logger.info(
            f"[MOCK] CameraDriver 初始化完成: "
            f"{self._width}x{self._height}"
        )

    def read_frame(self) -> np.ndarray | None:
        if not self._opened:
            return None

        self._frame_count += 1
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)

        # 深色背景渐变
        for y in range(self._height):
            v = int(20 + 15 * (y / self._height))
            frame[y, :] = (v, v + 2, v + 5)

        # 网格线
        grid_color = (40, 45, 50)
        for x in range(0, self._width, 40):
            cv2.line(frame, (x, 0), (x, self._height), grid_color, 1)
        for y in range(0, self._height, 40):
            cv2.line(frame, (0, y), (self._width, y), grid_color, 1)

        cx, cy = self._width // 2, self._height // 2

        # 中心十字准星
        cross_color = (0, 180, 230)
        cv2.line(frame, (cx - 30, cy), (cx + 30, cy), cross_color, 1)
        cv2.line(frame, (cx, cy - 30), (cx, cy + 30), cross_color, 1)
        cv2.circle(frame, (cx, cy), 20, cross_color, 1)

        # 角落标记
        bracket_color = (44, 132, 232)
        blen = 25
        for (bx, by, dx, dy) in [
            (40, 40, 1, 1), (self._width - 40, 40, -1, 1),
            (40, self._height - 40, 1, -1), (self._width - 40, self._height - 40, -1, -1),
        ]:
            cv2.line(frame, (bx, by), (bx + blen * dx, by), bracket_color, 2)
            cv2.line(frame, (bx, by), (bx, by + blen * dy), bracket_color, 2)

        # 时间戳
        ts = time.strftime("%H:%M:%S")
        cv2.putText(
            frame, ts, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
        )

        # 帧计数
        cv2.putText(
            frame, f"F:{self._frame_count}", (self._width - 80, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1,
        )

        # MOCK 标识
        cv2.putText(
            frame, "MOCK CAM", (cx - 45, self._height - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 80, 80), 1,
        )

        return frame

    @property
    def is_opened(self) -> bool:
        return self._opened

    @property
    def resolution(self) -> tuple[int, int]:
        return (self._width, self._height)

    def cleanup(self) -> None:
        if self._opened:
            self._opened = False
            self._frame_count = 0
            logger.info("[MOCK] CameraDriver 资源已释放")
