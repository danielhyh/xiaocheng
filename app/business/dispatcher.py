"""
business/dispatcher.py — 指令分发器

解析前端 envelope,路由到对应子系统。
新增功能只需在 _HANDLERS 注册新 type,核心不变。
"""

import logging
import time
from typing import Any

from app.subsystems.motion import MotionSubsystem
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

    def __init__(self, motion: MotionSubsystem, mode_manager: ModeManager):
        self._motion = motion
        self._mode = mode_manager
        self._brake_until = 0.0

        # type → handler 映射表
        # 新增子系统时只需在这里加一行
        self._handlers: dict[str, Any] = {
            "cmd.motion": self._handle_motion,
            "cmd.brake": self._handle_brake,
            "cmd.mode": self._handle_mode,
            # "cmd.gimbal": self._handle_gimbal,   # Phase 6
            # "cmd.light": self._handle_light,     # Phase 8
            # "cmd.audio": self._handle_audio,     # Phase 9
            # "cmd.nitro": self._handle_nitro,     # Phase 10
        }

    def dispatch(self, message: dict) -> dict | None:
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
        except Exception as e:
            logger.error(f"处理 {msg_type} 失败: {e}")
            return None

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
            # 自动模式下收到手动指令 → 临时让出 (TODO: 实现 3 秒超时)
            pass

        vx = float(payload.get("vx", 0))
        vy = float(payload.get("vy", 0))
        if time.monotonic() < self._brake_until and (vx != 0 or vy != 0):
            logger.debug("忽略刹车保护窗口内的运动指令")
            return
        self._motion.handle_command(vx, vy)

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
