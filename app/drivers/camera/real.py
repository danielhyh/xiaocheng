"""
drivers/camera/real.py — 真实摄像头驱动

使用 OpenCV VideoCapture 读取 V4L2 设备。
支持 OV13855 MIPI（RKISP NV12）与 OV5640 USB（MJPG）。
只在 Orange Pi 上运行。
"""

import glob
import logging
import os

import cv2
import numpy as np

from app import config

logger = logging.getLogger(__name__)


class RealCameraDriver:
    """
    Orange Pi 摄像头驱动。

    通过 OpenCV V4L2 后端打开设备,设置分辨率和帧率。
    read_frame() 返回 BGR numpy 数组。

    自动探测优先使用 /dev/video-camera*（RKISP 处理后节点），
    再尝试 USB by-id 和普通 /dev/video*，避免把 MIPI RAW 节点
    当成彩色成像节点。
    """

    def __init__(self):
        self._cap: cv2.VideoCapture | None = None
        self._width = config.CAMERA_WIDTH
        self._height = config.CAMERA_HEIGHT
        self._use_mjpg = False
        self._use_nv12 = False
        self._pixel_format = ""
        self._device: int | str | None = None

    @staticmethod
    def _device_path(device: int | str) -> str:
        """把设备号转换为可查询 sysfs 的 /dev/videoN 路径。"""
        if isinstance(device, int):
            return f"/dev/video{device}"
        return os.path.realpath(device)

    @classmethod
    def _v4l2_name(cls, device: int | str) -> str:
        """读取 V4L2 节点名称；不可用时返回空字符串。"""
        base = os.path.basename(cls._device_path(device))
        name_path = f"/sys/class/video4linux/{base}/name"
        try:
            with open(name_path, encoding="utf-8") as file:
                return file.read().strip().lower()
        except OSError:
            return ""

    @classmethod
    def _is_isp_capture_device(cls, device: int | str) -> bool:
        """判断是否为 RKISP 处理后的彩色输出节点。"""
        if isinstance(device, str) and os.path.basename(device).startswith(
            "video-camera"
        ):
            return True
        name = cls._v4l2_name(device)
        return name in {"rkisp_mainpath", "rkisp_selfpath"}

    @classmethod
    def _is_raw_or_metadata_device(cls, device: int | str) -> bool:
        """过滤 MIPI RAW、统计和参数节点。"""
        name = cls._v4l2_name(device)
        blocked = (
            "stream_cif",
            "rkcif",
            "rkisp-statistics",
            "rkisp-input-params",
            "rkisp_fbcpath",
            "rkisp_iqtool",
            "rkisp_raw",
        )
        return any(token in name for token in blocked)

    @staticmethod
    def _fourcc_string(value: float) -> str:
        """把 OpenCV 返回的 FOURCC 数字转成可读字符串。"""
        fourcc = int(value)
        return "".join(
            chr((fourcc >> (8 * index)) & 0xFF) for index in range(4)
        ).rstrip("\x00")

    @staticmethod
    def _probe(device: int | str) -> bool:
        """验证节点不仅能打开，而且能真实读取一帧。"""
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap.release()
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        ret, frame = cap.read()
        cap.release()
        return bool(ret and frame is not None)

    @staticmethod
    def _auto_candidates() -> list[str]:
        """按稳定成像节点、USB 稳定链接、普通节点的顺序列候选。"""
        candidates = [
            *sorted(glob.glob("/dev/video-camera*")),
            *sorted(glob.glob("/dev/v4l/by-id/*")),
            *sorted(glob.glob("/dev/video[0-9]*")),
        ]
        result: list[str] = []
        seen: set[str] = set()
        for path in candidates:
            real_path = os.path.realpath(path)
            if real_path in seen:
                continue
            seen.add(real_path)
            result.append(path)
        return result

    @classmethod
    def _find_camera_device(cls, preferred: int | str) -> int | str:
        """
        尝试 preferred，失败或设为 auto 时按优先级自动扫描。
        返回设备号 (int) 或设备路径 (str, 如 "/dev/video1")。
        """
        if preferred != "auto":
            if not cls._is_raw_or_metadata_device(preferred) and cls._probe(
                preferred
            ):
                return preferred
            logger.warning(
                f"配置的摄像头设备 {preferred} 不可采集,开始自动扫描..."
            )

        for path in cls._auto_candidates():
            if cls._is_raw_or_metadata_device(path):
                continue
            if cls._probe(path):
                logger.info(
                    f"自动探测到摄像头: {path} "
                    f"({cls._v4l2_name(path) or 'unknown'})"
                )
                return path

        raise RuntimeError(
            "未找到可用的摄像头成像节点,请检查 MIPI/USB 连接和设备树 overlay"
        )

    def init(self) -> None:
        device = self._find_camera_device(config.CAMERA_DEVICE)
        self._cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"无法打开摄像头设备 {device}"
            )

        # 格式必须在分辨率之前设置。RKISP 主节点输出 NV12；
        # USB UVC 摄像头继续优先使用硬件压缩的 MJPG。
        is_isp = self._is_isp_capture_device(device)
        requested_format = ""
        if is_isp:
            requested_format = "NV12"
            fourcc = cv2.VideoWriter_fourcc(*requested_format)
            if not self._cap.set(cv2.CAP_PROP_FOURCC, fourcc):
                logger.warning("RKISP 拒绝 NV12 请求,将使用驱动实际格式")
        elif config.CAMERA_USE_MJPG:
            requested_format = "MJPG"
            fourcc = cv2.VideoWriter_fourcc(*requested_format)
            if not self._cap.set(cv2.CAP_PROP_FOURCC, fourcc):
                logger.warning("USB 摄像头拒绝 MJPG 请求,将使用驱动实际格式")

        # 设置分辨率和帧率
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        # 读回实际值
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
        fourcc_str = self._fourcc_string(
            self._cap.get(cv2.CAP_PROP_FOURCC)
        )

        if requested_format and fourcc_str != requested_format:
            logger.warning(
                "摄像头格式回退: requested=%s, actual=%s",
                requested_format,
                fourcc_str or "unknown",
            )

        # 只有实际格式确为 NV12 且 OpenCV 接受关闭隐式转换时，才按
        # 原始 NV12 解码。否则保留 OpenCV 的 BGR 输出，避免格式误判。
        self._use_nv12 = bool(
            is_isp
            and fourcc_str == "NV12"
            and self._cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        )

        # USB 摄像头减小缓冲区可降低延迟；RKISP 多平面节点设置为 1
        # 会把实测帧率从约 12.5fps 降到 4.7fps，因此保留驱动默认值。
        if not is_isp:
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._width = actual_w
        self._height = actual_h
        self._use_mjpg = fourcc_str == "MJPG"
        self._pixel_format = fourcc_str
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
        if self._use_nv12:
            expected_size = self._width * self._height * 3 // 2
            if frame.size != expected_size:
                logger.error(
                    f"NV12 帧大小异常: expected={expected_size}, "
                    f"actual={frame.size}"
                )
                return None
            nv12 = frame.reshape((self._height * 3 // 2, self._width))
            return cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)
        return frame

    @property
    def use_mjpg(self) -> bool:
        """是否成功启用了 MJPG 采集格式"""
        return self._use_mjpg

    @property
    def pixel_format(self) -> str:
        """驱动最终采用的 V4L2 像素格式。"""
        return self._pixel_format

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
