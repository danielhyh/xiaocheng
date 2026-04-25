"""
subsystems/vision.py — 视觉子系统

职责:
  - 管理摄像头驱动的生命周期
  - 独立线程持续采集,主线程无阻塞
  - 提供最新帧的 JPEG 字节 (用于 MJPEG 流)
  - 线程安全: 写线程产出帧,读线程(可多个)消费

架构位置: 子系统层,上接 API 层,下接驱动层。
"""

import threading
import time
import logging

import cv2

from app import config
from app.drivers.camera import CameraDriver

logger = logging.getLogger(__name__)


class VisionSubsystem:
    """
    视觉子系统。

    采集线程以目标帧率循环读帧 → JPEG 编码 → 存入 _latest_frame。
    API 层通过 get_jpeg_frame() 获取最新帧。

    使用 threading.Event 通知等待者有新帧可用,
    避免 API 层轮询。
    """

    def __init__(self):
        self._driver = CameraDriver()
        self._latest_frame: bytes | None = None
        self._frame_lock = threading.Lock()
        self._new_frame_event = threading.Event()
        self._capture_thread: threading.Thread | None = None
        self._running = False
        self._frame_count = 0
        self._fps_actual = 0.0

    def init(self) -> None:
        """初始化摄像头并启动采集线程"""
        self._driver.init()
        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            name="camera-capture",
            daemon=True,
        )
        self._capture_thread.start()
        logger.info(
            f"VisionSubsystem 启动: "
            f"{self._driver.resolution[0]}x{self._driver.resolution[1]}, "
            f"JPEG quality={config.CAMERA_JPEG_QUALITY}"
        )

    def _capture_loop(self) -> None:
        """采集线程主循环"""
        target_interval = 1.0 / config.CAMERA_FPS
        fps_counter = 0
        fps_timer = time.monotonic()
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.CAMERA_JPEG_QUALITY]

        while self._running:
            t0 = time.monotonic()

            frame = self._driver.read_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            # JPEG 编码
            ok, jpeg = cv2.imencode(".jpg", frame, encode_params)
            if not ok:
                continue

            jpeg_bytes = jpeg.tobytes()

            # 更新最新帧 (写锁)
            with self._frame_lock:
                self._latest_frame = jpeg_bytes
                self._frame_count += 1

            # 通知等待者
            self._new_frame_event.set()

            # FPS 统计
            fps_counter += 1
            elapsed = time.monotonic() - fps_timer
            if elapsed >= 2.0:
                self._fps_actual = fps_counter / elapsed
                fps_counter = 0
                fps_timer = time.monotonic()
                logger.debug(f"摄像头实际帧率: {self._fps_actual:.1f} fps")

            # 帧率控制
            dt = time.monotonic() - t0
            sleep_time = target_interval - dt
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_jpeg_frame(self, timeout: float = 1.0) -> bytes | None:
        """
        获取最新的 JPEG 帧。

        如果当前没有帧,最多等待 timeout 秒。
        用于 MJPEG 流端点。

        返回:
            JPEG 字节数据,超时返回 None。
        """
        # 等待新帧
        if self._latest_frame is None:
            self._new_frame_event.wait(timeout=timeout)

        with self._frame_lock:
            frame = self._latest_frame
            # 清除事件,等待下一帧
            self._new_frame_event.clear()

        return frame

    def wait_for_new_frame(self, timeout: float = 1.0) -> bytes | None:
        """
        等待下一个新帧到来。

        与 get_jpeg_frame 不同,这个方法会阻塞直到有新帧,
        用于 MJPEG 流的逐帧推送。

        返回:
            JPEG 字节数据,超时返回 None。
        """
        self._new_frame_event.clear()
        got_new = self._new_frame_event.wait(timeout=timeout)
        if not got_new:
            return None

        with self._frame_lock:
            return self._latest_frame

    @property
    def is_active(self) -> bool:
        """摄像头是否正在采集"""
        return self._running and self._driver.is_opened

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def fps(self) -> float:
        return self._fps_actual

    @property
    def resolution(self) -> tuple[int, int]:
        return self._driver.resolution

    def cleanup(self) -> None:
        """停止采集线程并释放摄像头"""
        self._running = False
        # 唤醒可能在等待的线程
        self._new_frame_event.set()
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
            self._capture_thread = None
        self._driver.cleanup()
        logger.info("VisionSubsystem 已关闭")
