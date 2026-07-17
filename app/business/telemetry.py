"""
business/telemetry.py — 遥测发布器

周期性汇总子系统状态,通过 WS 推送给前端。

推送频道:
  - tel.motion:   运动状态 (高频)
  - tel.sensors:  传感器数据 (低频)
  - tel.obstacle: 避障数据 (中频)
"""

import asyncio
import logging
import os
import subprocess
import time
from typing import Callable, Awaitable

from app.subsystems.motion import MotionSubsystem
from app.subsystems.sensing import SensingSubsystem
from app import config

logger = logging.getLogger(__name__)


class TelemetryPublisher:
    """
    遥测发布器。

    注册多个遥测源,各自独立频率推送。
    send_fn 是 WS 发送回调,由 API 层注入。
    """

    def __init__(self, motion: MotionSubsystem, sensing: SensingSubsystem):
        self._motion = motion
        self._sensing = sensing
        self._obstacle = None
        self._gimbal = None
        self._nitro = None
        self._send_fn: Callable[[dict], Awaitable[None]] | None = None
        self._running = False

    def set_obstacle(self, obstacle) -> None:
        """注入避障子系统"""
        self._obstacle = obstacle

    def set_gimbal(self, gimbal) -> None:
        """注入云台子系统"""
        self._gimbal = gimbal

    def set_nitro(self, nitro) -> None:
        """注入氮气子系统"""
        self._nitro = nitro

    def set_send_fn(self, fn: Callable[[dict], Awaitable[None]]) -> None:
        """注入 WS 发送函数"""
        self._send_fn = fn

    async def _send(self, msg: dict) -> None:
        if self._send_fn:
            try:
                await self._send_fn(msg)
            except Exception:
                pass

    async def _publish_motion(self) -> None:
        """推送 tel.motion (高频)"""
        while self._running:
            payload = self._motion.telemetry
            # 附加氮气状态
            if self._nitro:
                payload["nitro_active"] = self._nitro.is_active
                payload["nitro_boost"] = self._nitro.boost_factor
            await self._send({
                "type": "tel.motion",
                "ts": time.time(),
                "payload": payload,
            })
            await asyncio.sleep(config.TELEMETRY_MOTION_INTERVAL)

    async def _publish_sensors(self) -> None:
        """
        推送 tel.sensors (低频)。

        Phase 7 增强: WiFi RSSI, CPU 占用率, WS 延迟。
        """
        while self._running:
            sensor_data = self._sensing.telemetry

            # Phase 7: 增强遥测
            sensor_data["wifi_rssi"] = self._read_wifi_rssi()
            sensor_data["cpu_usage"] = self._read_cpu_usage()

            # 云台状态
            if self._gimbal:
                sensor_data["gimbal_pan"] = round(self._gimbal.pan, 1)
                sensor_data["gimbal_tilt"] = round(self._gimbal.tilt, 1)

            # 避障数据
            if self._obstacle:
                sensor_data.update({
                    "front_distance": self._obstacle.front_distance,
                    "rear_distance": self._obstacle.rear_distance,
                    "front_blocked": self._obstacle.front_blocked,
                    "rear_blocked": self._obstacle.rear_blocked,
                })

            await self._send({
                "type": "tel.sensors",
                "ts": time.time(),
                "payload": sensor_data,
            })
            await asyncio.sleep(config.TELEMETRY_SENSORS_INTERVAL)

    @staticmethod
    def _read_wifi_rssi() -> int | None:
        """读取 WiFi 信号强度 (dBm)"""
        if config.USE_MOCK:
            import math
            return -62 + int(2 * math.sin(time.time() / 3))

        try:
            with open("/proc/net/wireless", "r") as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    parts = lines[2].split()
                    if len(parts) >= 4:
                        return int(float(parts[3]))
        except Exception:
            pass
        return None

    @staticmethod
    def _read_cpu_usage() -> float | None:
        """读取 CPU 使用率 (%)"""
        if config.USE_MOCK:
            import math
            return round(18 + 7 * math.sin(time.time() / 6), 1)

        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            parts = line.split()
            if parts[0] == "cpu":
                values = [int(x) for x in parts[1:8]]
                idle = values[3]
                total = sum(values)
                if total > 0:
                    return round((1 - idle / total) * 100, 1)
        except Exception:
            pass
        return None

    async def run(self) -> None:
        """启动所有遥测推送任务"""
        self._running = True
        await asyncio.gather(
            self._publish_motion(),
            self._publish_sensors(),
        )

    def stop(self) -> None:
        self._running = False
