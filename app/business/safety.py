"""
business/safety.py — 安全看门狗

WS 断连后 500ms 内自动停车。
后续 Phase 加入: 低电压告警、超温保护、急停。
"""

import asyncio
import logging
import time

from app.subsystems.motion import MotionSubsystem
from app.business.mode_manager import ModeManager
from app import config

logger = logging.getLogger(__name__)


class SafetyWatchdog:
    """
    安全看门狗。

    前端每收到一条消息就喂狗 (touch)。
    如果超过 WS_DISCONNECT_TIMEOUT 没收到消息,自动停车。
    """

    def __init__(self, motion: MotionSubsystem, mode_manager: ModeManager):
        self._motion = motion
        self._mode = mode_manager
        self._last_heartbeat = time.time()
        self._running = False
        self._has_connection = False

    def touch(self) -> None:
        """喂狗: 收到任何 WS 消息时调用"""
        self._last_heartbeat = time.time()
        self._has_connection = True

    def on_disconnect(self) -> None:
        """WS 断连时调用"""
        self._has_connection = False
        self._emergency_stop("WebSocket 断连")

    def _emergency_stop(self, reason: str) -> None:
        """紧急停车"""
        logger.warning(f"安全停车: {reason}")
        self._motion.stop()
        self._mode.force_manual(reason)

    async def run(self) -> None:
        """后台看门狗循环"""
        self._running = True
        while self._running:
            if self._has_connection:
                elapsed = time.time() - self._last_heartbeat
                if elapsed > config.WS_DISCONNECT_TIMEOUT:
                    self._emergency_stop(f"心跳超时 {elapsed:.1f}s")
                    self._has_connection = False
            await asyncio.sleep(0.1)

    def stop(self) -> None:
        self._running = False
