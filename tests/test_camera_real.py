"""真实摄像头设备选择逻辑的纯单元测试（不访问硬件）。"""

import os

import numpy as np
import cv2

os.environ.setdefault("XIAOCHENG_MOCK", "1")

from app.drivers.camera.real import RealCameraDriver


def test_auto_candidates_prefer_isp_alias(monkeypatch):
    """MIPI ISP 稳定别名必须优先于数字 video 节点。"""
    paths = {
        "/dev/video-camera*": ["/dev/video-camera0"],
        "/dev/v4l/by-id/*": ["/dev/v4l/by-id/usb-rear"],
        "/dev/video[0-9]*": ["/dev/video0", "/dev/video11"],
    }
    monkeypatch.setattr(
        "app.drivers.camera.real.glob.glob", lambda pattern: paths[pattern]
    )
    monkeypatch.setattr(
        "app.drivers.camera.real.os.path.realpath",
        lambda path: "/dev/video11" if path == "/dev/video-camera0" else path,
    )

    assert RealCameraDriver._auto_candidates() == [
        "/dev/video-camera0",
        "/dev/v4l/by-id/usb-rear",
        "/dev/video0",
    ]


def test_isp_alias_is_processed_capture_node():
    assert RealCameraDriver._is_isp_capture_device("/dev/video-camera0")


def test_raw_rkcif_node_is_filtered(monkeypatch):
    monkeypatch.setattr(
        RealCameraDriver, "_v4l2_name", lambda _device: "stream_cif_mipi_id0"
    )
    assert RealCameraDriver._is_raw_or_metadata_device("/dev/video0")


def test_isp_auxiliary_node_is_filtered(monkeypatch):
    monkeypatch.setattr(
        RealCameraDriver, "_v4l2_name", lambda _device: "rkisp_fbcpath"
    )
    assert RealCameraDriver._is_raw_or_metadata_device("/dev/video13")


def test_usb_node_is_not_filtered(monkeypatch):
    monkeypatch.setattr(
        RealCameraDriver, "_v4l2_name", lambda _device: "usb 2.0 camera"
    )
    assert not RealCameraDriver._is_raw_or_metadata_device("/dev/video0")


def test_nv12_frame_is_reshaped_and_converted_to_bgr():
    class FakeCapture:
        def read(self):
            raw = np.zeros((1, 4 * 2 * 3 // 2), dtype=np.uint8)
            return True, raw

    driver = RealCameraDriver()
    driver._cap = FakeCapture()
    driver._width = 4
    driver._height = 2
    driver._use_nv12 = True

    frame = driver.read_frame()

    assert frame is not None
    assert frame.shape == (2, 4, 3)


class FakeCapture:
    def __init__(self, actual_format: str, accepted: bool = True):
        self.actual_format = actual_format
        self.accepted = accepted
        self.set_calls: list[tuple[int, float]] = []

    def isOpened(self):
        return True

    def set(self, prop: int, value: float):
        self.set_calls.append((prop, value))
        if prop == cv2.CAP_PROP_FOURCC:
            return self.accepted
        return True

    def get(self, prop: int):
        values = {
            cv2.CAP_PROP_FRAME_WIDTH: 1280,
            cv2.CAP_PROP_FRAME_HEIGHT: 720,
            cv2.CAP_PROP_FPS: 15,
            cv2.CAP_PROP_FOURCC: cv2.VideoWriter_fourcc(*self.actual_format),
        }
        return values.get(prop, 0)


def _init_with_capture(monkeypatch, capture, device: str):
    monkeypatch.setattr(
        RealCameraDriver,
        "_find_camera_device",
        classmethod(lambda _cls, _preferred: device),
    )
    monkeypatch.setattr(
        "app.drivers.camera.real.cv2.VideoCapture",
        lambda _device, _backend: capture,
    )
    driver = RealCameraDriver()
    driver.init()
    return driver


def test_mipi_uses_raw_nv12_only_when_actual_format_matches(monkeypatch):
    capture = FakeCapture("NV12")

    driver = _init_with_capture(monkeypatch, capture, "/dev/video-camera0")

    assert driver.pixel_format == "NV12"
    assert driver._use_nv12 is True
    assert (cv2.CAP_PROP_CONVERT_RGB, 0) in capture.set_calls


def test_mipi_falls_back_to_opencv_conversion_for_other_format(monkeypatch):
    capture = FakeCapture("UYVY", accepted=False)

    driver = _init_with_capture(monkeypatch, capture, "/dev/video-camera0")

    assert driver.pixel_format == "UYVY"
    assert driver._use_nv12 is False
    assert (cv2.CAP_PROP_CONVERT_RGB, 0) not in capture.set_calls


def test_usb_falls_back_when_mjpg_is_not_available(monkeypatch):
    capture = FakeCapture("YUYV", accepted=False)

    driver = _init_with_capture(monkeypatch, capture, "/dev/v4l/by-id/usb-rear")

    assert driver.pixel_format == "YUYV"
    assert driver.use_mjpg is False
    assert (cv2.CAP_PROP_BUFFERSIZE, 1) in capture.set_calls
