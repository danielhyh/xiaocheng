"""
drivers/camera/real.py — 真实摄像头驱动

使用 OpenCV VideoCapture 读取 V4L2 设备 (OV5640 USB/CSI)。
只在 Orange Pi 上运行。
"""

import glob
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

    设备号自动探测: 如果配置的设备打不开,会扫描 /dev/video*
    找到第一个可用的 V4L2 摄像头 (跳过 codec/media 节点)。
    """

    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._width = config.CAMERA_WIDTH
        self._height = config.CAMERA_HEIGHT

    @staticmethod
    def _find_camera_device(preferred: int) -> int | str:
        """
        尝试打开 preferred 设备号,失败则扫描 /dev/video* 。
        返回设备号 (int) 或设备路径 (str, 如 "/dev/video1")。
        """
        # 先试配置值 (保持 int,V4L2 后端不接受纯数字字符串)
        cap = cv2.VideoCapture(preferred, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.release()
            return preferred

        logger.warning(
            f"配置的摄像头设备 {preferred} 打不开,开始自动扫描..."
        )

        # 扫描 /dev/video* (排除 codec/media 节点)
        for path in sorted(glob.glob("/dev/video[0-9]*")):
            cap = cv2.VideoCapture(path, cv2.CAP_V4L2)
            if cap.isOpened():
                # 验证是否真的能采集 (排除 metadata 节点)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                ret, _ = cap.read()
                cap.release()
                if ret:
                    logger.info(f"自动探测到摄像头: {path}")
                    return path
            cap.release()

        raise RuntimeError(
            "未找到可用的摄像头设备,请检查 USB 连接"
        )

    def init(self) -> None:
        device = self._find_camera_device(config.CAMERA_DEVICE)
        self._cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"无法打开摄像头设备 {device}"
            )

        # 设置 MJPG 采集格式 (必须在设置分辨率之前)
        # MJPG 由摄像头硬件压缩,比 YUYV 带宽低 5-10 倍,帧率更高
        if config.CAMERA_USE_MJPG:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            self._cap.set(cv2.CAP_PROP_FOURCC, fourcc)

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
        actual_fourcc = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        fourcc_str = "".join(chr((actual_fourcc >> (8 * i)) & 0xFF) for i in range(4))
        self._width = actual_w
        self._height = actual_h
        self._use_mjpg = fourcc_str == "MJPG"
        self._device = device

        logger.info(
            f"RealCameraDriver 初始化完成: "
            f"{actual_w}x{actual_h} @ {actual_fps:.0f}fps, "
            f"格式={fourcc_str}, 设备={device}"
        )

    def read_frame(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    @property
    def use_mjpg(self) -> bool:
        """是否成功启用了 MJPG 采集格式"""
        return self._use_mjpg

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
