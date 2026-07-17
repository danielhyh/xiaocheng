"""
drivers/camera/mock.py — Mock 摄像头驱动

接口与 RealCameraDriver 完全一致。

优先加载 frontend/public/mock-bg.png 作为背景帧,
找不到时退回到 OpenCV 生成的测试图案。
"""

import os
import time
import logging

import cv2
import numpy as np

from app import config

logger = logging.getLogger(__name__)

# 背景图搜索路径 (从项目根目录出发, 优先 assets/)
_BG_SEARCH_PATHS = [
    os.path.join("assets", "mock-bg.png"),
    os.path.join("assets", "mock-bg.jpg"),
    os.path.join("frontend", "public", "mock-bg.png"),
    os.path.join("frontend", "public", "mock-bg.jpg"),
]


def _find_bg_image() -> str | None:
    """在项目目录中搜索背景图"""
    for rel in _BG_SEARCH_PATHS:
        if os.path.isfile(rel):
            return rel
    return None


class MockCameraDriver:
    """
    Mock 摄像头驱动。

    优先使用 mock-bg.png 背景图 (赛博朋克风格),
    找不到时生成动态测试图案。
    """

    def __init__(self):
        self._width = config.CAMERA_WIDTH
        self._height = config.CAMERA_HEIGHT
        self._opened = False
        self._frame_count = 0
        self._bg_frame: np.ndarray | None = None

    def init(self) -> None:
        self._opened = True
        self._frame_count = 0

        # 尝试加载背景图
        bg_path = _find_bg_image()
        if bg_path:
            img = cv2.imread(bg_path)
            if img is not None:
                # 缩放到目标分辨率
                self._bg_frame = cv2.resize(img, (self._width, self._height))
                logger.info(
                    f"[MOCK] CameraDriver 使用背景图: {bg_path} "
                    f"({self._width}x{self._height})"
                )
            else:
                logger.warning(f"[MOCK] 背景图加载失败: {bg_path}, 退回测试图案")
        else:
            logger.info(
                f"[MOCK] 未找到背景图, 使用测试图案 "
                f"({self._width}x{self._height})"
            )

    def read_frame(self) -> np.ndarray | None:
        if not self._opened:
            return None

        self._frame_count += 1

        if self._bg_frame is not None:
            return self._read_bg_frame()
        else:
            return self._read_generated_frame()

    def _read_bg_frame(self) -> np.ndarray:
        """使用背景图 + 叠加 HUD 信息"""
        frame = self._bg_frame.copy()
        cx, cy = self._width // 2, self._height // 2

        # 左上角时间戳
        ts = time.strftime("%H:%M:%S")
        cv2.putText(
            frame, ts, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 220, 255), 1,
            cv2.LINE_AA,
        )

        # 右上角帧计数
        cv2.putText(
            frame, f"F:{self._frame_count}", (self._width - 90, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 200), 1,
            cv2.LINE_AA,
        )

        return frame

    def _read_generated_frame(self) -> np.ndarray:
        """生成测试图案 (无背景图时的 fallback)"""
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
