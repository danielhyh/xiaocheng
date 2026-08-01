"""
business/telemetry.py — 遥测发布器

周期性汇总子系统状态,通过 WS 推送给前端。

推送频道:
  - tel.motion:   运动状态 (高频)
  - tel.sensors:  传感器数据 (低频)
  - tel.obstacle: 避障数据 (中频)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Awaitable, TYPE_CHECKING

from app import config

if TYPE_CHECKING:
    from app.subsystems.motion import MotionSubsystem
    from app.subsystems.sensing import SensingSubsystem

logger = logging.getLogger(__name__)


class TelemetryPublisher:
    """
    遥测发布器。

    注册多个遥测源,各自独立频率推送。
    send_fn 是 WS 发送回调,由 API 层注入。
    """

    def __init__(
        self,
        motion: MotionSubsystem | None,
        sensing: SensingSubsystem | None,
    ):
        self._motion = motion
        self._sensing = sensing
        self._obstacle = None
        self._gimbal = None
        self._nitro = None

    def set_obstacle(self, obstacle) -> None:
        """注入避障子系统"""
        self._obstacle = obstacle

    def set_gimbal(self, gimbal) -> None:
        """注入云台子系统"""
        self._gimbal = gimbal

    def set_nitro(self, nitro) -> None:
        """注入氮气子系统"""
        self._nitro = nitro

    @staticmethod
    async def _send(
        send_fn: Callable[[dict], Awaitable[None]],
        msg: dict,
    ) -> None:
        try:
            await send_fn(msg)
        except Exception:
            logger.debug("遥测发送失败，等待连接任务结束", exc_info=True)

    async def _publish_motion(
        self,
        send_fn: Callable[[dict], Awaitable[None]],
    ) -> None:
        """推送 tel.motion (高频)"""
        while True:
            if self._motion:
                payload = {"available": True, **self._motion.telemetry}
            else:
                payload = {
                    "available": False,
                    "vx": 0,
                    "vy": 0,
                    "speed": 0,
                    "direction": "unavailable",
                    "left_speed": 0,
                    "right_speed": 0,
                }
            # 附加氮气状态
            if self._nitro:
                payload["nitro_active"] = self._nitro.is_active
                payload["nitro_boost"] = self._nitro.boost_factor
            await self._send(send_fn, {
                "type": "tel.motion",
                "ts": time.time(),
                "payload": payload,
            })
            await asyncio.sleep(config.TELEMETRY_MOTION_INTERVAL)

    async def _publish_sensors(
        self,
        send_fn: Callable[[dict], Awaitable[None]],
    ) -> None:
        """
        推送 tel.sensors (低频)。

        Phase 7 增强: WiFi RSSI, CPU 占用率, WS 延迟。
        """
        while True:
            if self._sensing:
                sensor_data = {"available": True, **self._sensing.telemetry}
            else:
                sensor_data = {
                    "available": False,
                    "battery_voltage": None,
                    "battery_percent": None,
                    "battery_level": "unknown",
                    "cpu_temp": None,
                }

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

            await self._send(send_fn, {
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

    async def run(
        self,
        send_fn: Callable[[dict], Awaitable[None]],
    ) -> None:
        """为一个连接启动独立的遥测推送任务。"""
        await asyncio.gather(
            self._publish_motion(send_fn),
            self._publish_sensors(send_fn),
        )
