"""
api/http.py — HTTP 路由

低频请求/响应: 状态查询、配置读取。
"""

from fastapi import APIRouter
from app import config
from app.business.mode_manager import ModeManager

router = APIRouter()

_mode_manager: ModeManager | None = None


def init(mode_manager: ModeManager):
    global _mode_manager
    _mode_manager = mode_manager


@router.get("/api/status")
async def get_status():
    """整车状态概览"""
    return {
        "mode": _mode_manager.current.value if _mode_manager else "unknown",
        "mock": config.USE_MOCK,
        "version": "0.2.0",
        "phase": "2.2",
    }


@router.get("/api/config")
async def get_config():
    """返回前端需要的配置参数"""
    return {
        "ws_path": "/ws/control",
        "stream_path": "/stream/camera",   # Phase 3
        "telemetry_intervals": {
            "motion": config.TELEMETRY_MOTION_INTERVAL,
            "sensors": config.TELEMETRY_SENSORS_INTERVAL,
        },
    }
