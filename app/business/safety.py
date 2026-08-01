"""
business/safety.py — 安全看门狗

安全功能:
  - WS 断连后 500ms 内自动停车
  - 前方障碍物自动停车
  - 后方障碍物倒车自动刹停
  - 低电压告警 (联动音频)
  - 断连时停止鸣笛/灯效/云台/氮气
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from app.business.mode_manager import ModeManager
from app import config

if TYPE_CHECKING:
    from app.subsystems.motion import MotionSubsystem

logger = logging.getLogger(__name__)


class SafetyWatchdog:
    """
    安全看门狗。

    前端每收到一条消息就喂狗 (touch)。
    如果超过 WS_DISCONNECT_TIMEOUT 没收到消息,自动停车。
    """

    def __init__(self, motion: MotionSubsystem | None, mode_manager: ModeManager):
        self._motion = motion
        self._mode = mode_manager
        self._audio = None
        self._lighting = None
        self._gimbal = None
        self._obstacle = None
        self._nitro = None
        self._last_heartbeat = time.time()
        self._running = False
        self._has_connection = False

    def set_audio(self, audio) -> None:
        """注入音频子系统引用"""
        self._audio = audio

    def set_lighting(self, lighting) -> None:
        """注入灯光子系统引用"""
        self._lighting = lighting

    def set_gimbal(self, gimbal) -> None:
        """注入云台子系统引用"""
        self._gimbal = gimbal

    def set_obstacle(self, obstacle) -> None:
        """注入避障子系统引用"""
        self._obstacle = obstacle
        # 注册避障回调
        if obstacle:
            obstacle.set_callbacks(
                on_front_blocked=self._on_front_blocked,
                on_rear_blocked=self._on_rear_blocked,
            )

    def set_nitro(self, nitro) -> None:
        """注入氮气子系统引用"""
        self._nitro = nitro

    def _on_front_blocked(self) -> None:
        """前方障碍物回调: 停车"""
        logger.warning("安全: 前方障碍物,自动停车")
        if self._motion:
            self._motion.stop()

    def _on_rear_blocked(self) -> None:
        """后方障碍物回调: 停车"""
        logger.warning("安全: 后方障碍物,倒车自动刹停")
        if self._motion:
            self._motion.brake()

    def touch(self) -> None:
        """喂狗: 收到任何 WS 消息时调用"""
        self._last_heartbeat = time.time()
        self._has_connection = True

    def on_disconnect(self) -> None:
        """WS 真正断连时调用"""
        self._has_connection = False
        self._on_heartbeat_timeout("WebSocket 断连")
        # 停止鸣笛和倒车提示
        if self._audio:
            self._audio.stop_horn_and_reverse()
        # 停止灯效 (大灯保持)
        if self._lighting:
            self._lighting.stop_all()
        # 停止云台移动
        if self._gimbal:
            self._gimbal.stop_all()
        # 停止氮气
        if self._nitro:
            self._nitro.stop_all()

    def _on_heartbeat_timeout(self, reason: str) -> None:
        """心跳超时: 只停车"""
        logger.warning(f"安全停车: {reason}")
        if self._motion:
            self._motion.stop()
        self._mode.force_manual(reason)

    async def run(self) -> None:
        """后台看门狗循环"""
        self._running = True
        while self._running:
            if self._has_connection:
                elapsed = time.time() - self._last_heartbeat
                if elapsed > config.WS_DISCONNECT_TIMEOUT:
                    self._on_heartbeat_timeout(f"心跳超时 {elapsed:.1f}s")
                    self._has_connection = False
            await asyncio.sleep(0.1)

    def stop(self) -> None:
        self._running = False
