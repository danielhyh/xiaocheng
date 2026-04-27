"""
business/dispatcher.py — 指令分发器

解析前端 envelope,路由到对应子系统。
新增功能只需在 _HANDLERS 注册新 type,核心不变。
"""

import asyncio
import logging
import time
from typing import Any

from app.subsystems.motion import MotionSubsystem
from app.subsystems.audio import AudioSubsystem
from app.business.mode_manager import ModeManager, Mode

logger = logging.getLogger(__name__)

BRAKE_SUPPRESS_SECONDS = 0.3


class Dispatcher:
    """
    指令分发器。

    收到 WS 消息后:
    1. 解析 envelope (type + payload)
    2. 根据 type 路由到对应 handler
    3. handler 调用对应子系统
    """

    def __init__(self, motion: MotionSubsystem, mode_manager: ModeManager,
                 audio: AudioSubsystem | None = None):
        self._motion = motion
        self._mode = mode_manager
        self._audio = audio
        self._brake_until = 0.0

        # type → handler 映射表
        # 新增子系统时只需在这里加一行
        self._handlers: dict[str, Any] = {
            "cmd.motion": self._handle_motion,
            "cmd.brake": self._handle_brake,
            "cmd.mode": self._handle_mode,
            "cmd.ping": self._handle_ping,
            "cmd.audio": self._handle_audio,
            # "cmd.gimbal": self._handle_gimbal,   # Phase 6
            # "cmd.light": self._handle_light,     # Phase 8
            # "cmd.nitro": self._handle_nitro,     # Phase 10
        }

    async def dispatch(self, message: dict) -> dict | None:
        """
        分发一条 WS 消息。

        参数: 解析后的 JSON dict (envelope 格式)
        返回: 需要回复的消息 (如 ack),或 None
        """
        msg_type = message.get("type", "")
        payload = message.get("payload", {})
        msg_id = message.get("id")

        handler = self._handlers.get(msg_type)
        if handler is None:
            logger.warning(f"未知指令类型: {msg_type}")
            return None

        try:
            result = handler(payload)
            # 支持 async handler (如 cmd.audio)
            if asyncio.iscoroutine(result):
                result = await result
        except Exception as e:
            logger.error(f"处理 {msg_type} 失败: {e}")
            return None

        # cmd.ping 总是回复 (不需要 id)
        if msg_type == "cmd.ping" and result:
            return result

        # 带 id 的指令需要 ack
        if msg_id and result:
            return {
                "type": "event.ack",
                "id": msg_id,
                "ts": time.time(),
                "payload": result,
            }
        return None

    def _handle_motion(self, payload: dict) -> None:
        """处理 cmd.motion: { vx, vy }"""
        if self._mode.current != Mode.MANUAL:
            pass

        vx = float(payload.get("vx", 0))
        vy = float(payload.get("vy", 0))
        if time.monotonic() < self._brake_until and (vx != 0 or vy != 0):
            logger.debug("忽略刹车保护窗口内的运动指令")
            return
        self._motion.handle_command(vx, vy)

        # 倒车提示音联动
        if self._audio:
            if vy < -0.1:
                self._audio.start_reverse_beep()
            else:
                self._audio.stop_reverse_beep()

    def _handle_brake(self, payload: dict) -> dict:
        """处理 cmd.brake: 立即制动并清零运动状态。"""
        self._brake_until = time.monotonic() + BRAKE_SUPPRESS_SECONDS
        self._motion.brake()
        return {"braked": True}

    def _handle_mode(self, payload: dict) -> dict:
        """处理 cmd.mode: { mode }"""
        target = payload.get("mode", "manual")
        new_mode = self._mode.switch(target)
        return {"mode": new_mode.value}

    def _handle_ping(self, payload: dict) -> dict:
        """处理 cmd.ping: 立即回复 event.pong 用于延迟测量"""
        return {
            "type": "event.pong",
            "ts": time.time(),
            "payload": {},
        }

    async def _handle_audio(self, payload: dict) -> dict | None:
        """处理 cmd.audio: { action, data }"""
        if not self._audio:
            logger.warning("音频子系统未初始化")
            return {"error": "audio not available"}
        return await self._audio.handle_command(payload)
