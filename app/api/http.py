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
        "subsystems": dict(config.SUBSYSTEMS_ENABLED),
        "version": "0.3.0",
        "phase": "10",
    }


@router.get("/api/config")
async def get_config():
    """返回前端需要的配置参数"""
    return {
        "ws_path": "/ws/control",
        "stream_path": "/stream/camera",
        "subsystems": dict(config.SUBSYSTEMS_ENABLED),
        "telemetry_intervals": {
            "motion": config.TELEMETRY_MOTION_INTERVAL,
            "sensors": config.TELEMETRY_SENSORS_INTERVAL,
        },
        "gimbal": {
            "pan_min": config.GIMBAL_PAN_MIN,
            "pan_max": config.GIMBAL_PAN_MAX,
            "tilt_min": config.GIMBAL_TILT_MIN,
            "tilt_max": config.GIMBAL_TILT_MAX,
        },
        "obstacle": {
            "front_stop": config.US_FRONT_STOP_DISTANCE,
            "front_warn": config.US_FRONT_WARN_DISTANCE,
            "rear_stop": config.US_REAR_STOP_DISTANCE,
        },
        "nitro": {
            "duration": config.NITRO_DURATION,
            "cooldown": config.NITRO_COOLDOWN,
            "boost_factor": config.NITRO_BOOST_FACTOR,
        },
    }
