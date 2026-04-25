"""
api/stream.py — MJPEG 视频流端点

Phase 3 实现。当前返回占位响应。
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/stream/camera")
async def camera_stream():
    """Phase 3: OV5640 MJPEG 流"""
    return PlainTextResponse(
        "Camera not available (Phase 3)",
        status_code=503,
    )
