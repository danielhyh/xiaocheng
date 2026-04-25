"""
drivers/camera — 摄像头驱动的双实现入口

根据 config.USE_MOCK 决定加载真实驱动还是 Mock 驱动。
上层代码只 import CameraDriver,不关心具体实现。
"""

from app.config import USE_MOCK

if USE_MOCK:
    from app.drivers.camera.mock import MockCameraDriver as CameraDriver
else:
    from app.drivers.camera.real import RealCameraDriver as CameraDriver

__all__ = ["CameraDriver"]
