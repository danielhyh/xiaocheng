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
from app.subsystems.lighting import LightingSubsystem
from app.subsystems.gimbal import GimbalSubsystem
from app.subsystems.obstacle import ObstacleSubsystem
from app.subsystems.nitro import NitroSubsystem
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
                 audio: AudioSubsystem | None = None,
                 lighting: LightingSubsystem | None = None,
                 gimbal: GimbalSubsystem | None = None,
                 obstacle: ObstacleSubsystem | None = None,
                 nitro: NitroSubsystem | None = None):
        self._motion = motion
        self._mode = mode_manager
        self._audio = audio
        self._lighting = lighting
        self._gimbal = gimbal
        self._obstacle = obstacle
        self._nitro = nitro
        self._brake_until = 0.0

        # type → handler 映射表
        self._handlers: dict[str, Any] = {
            "cmd.motion": self._handle_motion,
            "cmd.brake": self._handle_brake,
            "cmd.mode": self._handle_mode,
            "cmd.ping": self._handle_ping,
            "cmd.audio": self._handle_audio,
            "cmd.light": self._handle_light,
            "cmd.gimbal": self._handle_gimbal,
            "cmd.obstacle": self._handle_obstacle,
            "cmd.nitro": self._handle_nitro,
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
            # 支持 async handler
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
            logger.debug("忽略非手动模式下的手动运动指令")
            return

        vx = float(payload.get("vx", 0))
        vy = float(payload.get("vy", 0))
        if time.monotonic() < self._brake_until and (vx != 0 or vy != 0):
            logger.debug("忽略刹车保护窗口内的运动指令")
            return

        # 氮气加速倍率
        if self._nitro and self._nitro.is_active:
            boost = self._nitro.boost_factor
            vx = max(-1.0, min(1.0, vx * boost))
            vy = max(-1.0, min(1.0, vy * boost))

        # 前方避障安全联锁
        if self._obstacle and self._obstacle.front_blocked and vy > 0:
            logger.debug("前方障碍物,阻止前进")
            vy = 0

        # 后方避障安全联锁
        if self._obstacle and self._obstacle.rear_blocked and vy < 0:
            logger.debug("后方障碍物,阻止倒车")
            vy = 0

        self._motion.handle_command(vx, vy)

        # 倒车提示音联动
        is_reversing = vy < -0.1
        if self._audio:
            if is_reversing:
                self._audio.start_reverse_beep()
            else:
                self._audio.stop_reverse_beep()

        # 倒车灯联动
        if self._lighting:
            if is_reversing:
                self._lighting.on_reverse_start()
            else:
                self._lighting.on_reverse_stop()

        # 倒车状态通知避障子系统
        if self._obstacle:
            self._obstacle.set_reversing(is_reversing)

    def _handle_brake(self, payload: dict) -> dict:
        """处理 cmd.brake: 立即制动并清零运动状态。"""
        self._brake_until = time.monotonic() + BRAKE_SUPPRESS_SECONDS
        self._motion.brake()

        # 刹车灯联动
        if self._lighting:
            self._lighting.on_brake()
            asyncio.get_event_loop().call_later(
                BRAKE_SUPPRESS_SECONDS + 0.2,
                self._lighting.on_brake_release,
            )

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

    async def _handle_light(self, payload: dict) -> dict | None:
        """处理 cmd.light: { action, data }"""
        if not self._lighting:
            logger.warning("灯光子系统未初始化")
            return {"error": "lighting not available"}
        return await self._lighting.handle_command(payload)

    async def _handle_gimbal(self, payload: dict) -> dict | None:
        """处理 cmd.gimbal: { action, data }"""
        if not self._gimbal:
            logger.warning("云台子系统未初始化")
            return {"error": "gimbal not available"}
        return await self._gimbal.handle_command(payload)

    async def _handle_obstacle(self, payload: dict) -> dict | None:
        """处理 cmd.obstacle: { action }"""
        if not self._obstacle:
            logger.warning("避障子系统未初始化")
            return {"error": "obstacle not available"}
        return await self._obstacle.handle_command(payload)

    async def _handle_nitro(self, payload: dict) -> dict | None:
        """处理 cmd.nitro: { action }"""
        if not self._nitro:
            logger.warning("氮气子系统未初始化")
            return {"error": "nitro not available"}
        return await self._nitro.handle_command(payload)
