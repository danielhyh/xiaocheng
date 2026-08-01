"""
api/stream.py — MJPEG 视频流端点

提供 /stream/camera 端点,输出 multipart/x-mixed-replace MJPEG 流。
浏览器 <img src="/stream/camera"> 即可直接显示。

独立于 WebSocket 通道,避免 binary 帧干扰 JSON 指令。
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse

from app import config

if TYPE_CHECKING:
    from app.subsystems.vision import VisionSubsystem

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局引用,由 main.py 注入
_vision: VisionSubsystem | None = None


def init(vision: VisionSubsystem | None) -> None:
    global _vision
    _vision = vision


async def _mjpeg_generator():
    """
    异步生成器: 逐帧产出 MJPEG multipart 数据。

    在线程池中等待新帧 (避免阻塞 asyncio 事件循环),
    然后包装成 multipart boundary 格式输出。
    """
    loop = asyncio.get_event_loop()
    target_interval = 1.0 / config.CAMERA_STREAM_FPS

    while True:
        # 在线程池中等待新帧,不阻塞事件循环
        frame = await loop.run_in_executor(
            None, _vision.wait_for_new_frame, 2.0
        )

        if frame is None:
            # 超时,继续等待
            await asyncio.sleep(0.1)
            continue

        # multipart boundary 格式
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(frame)).encode() + b"\r\n"
            b"\r\n" + frame + b"\r\n"
        )

        # 流帧率控制
        await asyncio.sleep(target_interval)


@router.get("/stream/camera")
async def camera_stream():
    """MJPEG 摄像头流"""
    if _vision is None or not _vision.is_active:
        return JSONResponse(
            {"error": "摄像头未就绪"},
            status_code=503,
        )

    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/stream/status")
async def camera_status():
    """摄像头状态查询"""
    if _vision is None:
        return JSONResponse({"active": False, "reason": "未初始化"})

    return JSONResponse({
        "active": _vision.is_active,
        "resolution": list(_vision.resolution),
        "fps": round(_vision.fps, 1),
        "frame_count": _vision.frame_count,
    })
