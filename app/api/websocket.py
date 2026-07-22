"""
api/websocket.py — WebSocket 路由

处理 /ws/control 端点:
- 接收 envelope 格式的 JSON 指令
- 分发到 Dispatcher
- 遥测数据通过 TelemetryPublisher 推送
"""

import asyncio
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.business.dispatcher import Dispatcher
from app.business.safety import SafetyWatchdog
from app.business.telemetry import TelemetryPublisher

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局引用,由 main.py 注入
_dispatcher: Dispatcher | None = None
_safety: SafetyWatchdog | None = None
_telemetry: TelemetryPublisher | None = None


def init(dispatcher: Dispatcher, safety: SafetyWatchdog, telemetry: TelemetryPublisher):
    global _dispatcher, _safety, _telemetry
    _dispatcher = dispatcher
    _safety = safety
    _telemetry = telemetry


@router.websocket("/ws/control")
async def ws_control(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket 连接建立")

    async def send_json(msg: dict):
        await ws.send_json(msg)

    # 每个连接拥有独立遥测任务，互不覆盖发送目标和运行状态
    telemetry_task = asyncio.create_task(_telemetry.run(send_json))

    try:
        while True:
            raw = await ws.receive_text()
            _safety.touch()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"无效 JSON: {raw[:100]}")
                continue

            # 分发指令
            reply = await _dispatcher.dispatch(message)
            if reply:
                await ws.send_json(reply)

    except WebSocketDisconnect:
        logger.info("WebSocket 断开")
        _safety.on_disconnect()
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        _safety.on_disconnect()
    finally:
        telemetry_task.cancel()
        try:
            await telemetry_task
        except asyncio.CancelledError:
            pass
