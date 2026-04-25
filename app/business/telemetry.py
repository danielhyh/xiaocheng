"""
business/telemetry.py — 遥测发布器

周期性汇总子系统状态,通过 WS 推送给前端。
Phase 2.2 推送: tel.motion + tel.sensors (mock 值)。
"""

import asyncio
import logging
import time
import random
from typing import Callable, Awaitable

from app.subsystems.motion import MotionSubsystem
from app import config

logger = logging.getLogger(__name__)


class TelemetryPublisher:
    """
    遥测发布器。

    注册多个遥测源,各自独立频率推送。
    send_fn 是 WS 发送回调,由 API 层注入。
    """

    def __init__(self, motion: MotionSubsystem):
        self._motion = motion
        self._send_fn: Callable[[dict], Awaitable[None]] | None = None
        self._running = False

    def set_send_fn(self, fn: Callable[[dict], Awaitable[None]]) -> None:
        """注入 WS 发送函数"""
        self._send_fn = fn

    async def _send(self, msg: dict) -> None:
        if self._send_fn:
            try:
                await self._send_fn(msg)
            except Exception:
                pass  # 连接断了就跳过

    async def _publish_motion(self) -> None:
        """推送 tel.motion (高频)"""
        while self._running:
            await self._send({
                "type": "tel.motion",
                "ts": time.time(),
                "payload": self._motion.telemetry,
            })
            await asyncio.sleep(config.TELEMETRY_MOTION_INTERVAL)

    async def _publish_sensors(self) -> None:
        """
        推送 tel.sensors (低频)。
        Phase 2.2 用 mock 值,后续 Phase 7 接入 ADS1115 真实读数。
        """
        while self._running:
            await self._send({
                "type": "tel.sensors",
                "ts": time.time(),
                "payload": {
                    "battery_voltage": round(11.8 + random.uniform(-0.2, 0.2), 1),
                    "cpu_temp": round(45 + random.uniform(-3, 5), 1),
                    "cpu_usage": round(random.uniform(10, 35), 1),
                    "wifi_rssi": round(-45 + random.uniform(-10, 5)),
                    "ws_latency_ms": round(random.uniform(3, 15), 1),
                },
            })
            await asyncio.sleep(config.TELEMETRY_SENSORS_INTERVAL)

    async def run(self) -> None:
        """启动所有遥测推送任务"""
        self._running = True
        await asyncio.gather(
            self._publish_motion(),
            self._publish_sensors(),
        )

    def stop(self) -> None:
        self._running = False
