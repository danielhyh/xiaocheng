"""
subsystems/nitro.py — 氮气加速彩蛋子系统

职责:
  - 触发氮气加速效果 (电机突破常规上限)
  - 灯效联动 (大灯闪烁 + 灯带特效)
  - 音效联动 (nitro 音效)
  - 冷却机制 (CD 计时)
  - 持续时间限制

架构位置: 子系统层,上接 dispatcher,协调 motion/lighting/audio。
"""

import asyncio
import logging
import time

from app import config

logger = logging.getLogger(__name__)


class NitroSubsystem:
    """
    氮气加速彩蛋。

    触发后:
      1. 电机速度乘以 NITRO_BOOST_FACTOR (如 1.3x)
      2. 大灯快速闪烁
      3. 灯带显示火焰色
      4. 播放 nitro 音效
      5. 持续 NITRO_DURATION 秒后自动结束
      6. 进入冷却期 NITRO_COOLDOWN 秒
    """

    def __init__(self):
        self._active = False
        self._last_trigger = 0.0
        self._nitro_task: asyncio.Task | None = None

        # 外部引用 (由 main.py 注入)
        self._motion = None
        self._lighting = None
        self._audio = None

    def set_dependencies(self, motion=None, lighting=None, audio=None) -> None:
        """注入子系统依赖"""
        self._motion = motion
        self._lighting = lighting
        self._audio = audio

    async def handle_command(self, payload: dict) -> dict:
        """
        处理 cmd.nitro 指令。

        payload 格式:
          { "action": "trigger" }
          { "action": "status" }
        """
        action = payload.get("action", "")

        if action == "trigger":
            return await self._trigger()
        elif action == "status":
            return self._get_status()
        else:
            return {"error": f"unknown action: {action}"}

    async def _trigger(self) -> dict:
        """触发氮气加速"""
        if self._active:
            return {"nitro": "already_active"}

        # 冷却检查
        now = time.monotonic()
        elapsed = now - self._last_trigger
        if elapsed < config.NITRO_COOLDOWN:
            remaining = round(config.NITRO_COOLDOWN - elapsed, 1)
            return {"nitro": "cooling", "cooldown_remaining": remaining}

        self._active = True
        self._last_trigger = now
        if self._lighting:
            self._lighting.start_nitro_effect()
        self._nitro_task = asyncio.create_task(self._nitro_effect())
        logger.info("🔥 氮气加速触发!")
        return {"nitro": "activated", "duration": config.NITRO_DURATION}

    async def _nitro_effect(self) -> None:
        """氮气加速效果循环"""
        current_task = asyncio.current_task()
        try:
            # 播放音效
            if self._audio:
                asyncio.create_task(
                    self._audio.handle_command({
                        "action": "play",
                        "data": {"clip": "nitro"},
                    })
                )

            # 持续 NITRO_DURATION 秒
            await asyncio.sleep(config.NITRO_DURATION)

        except asyncio.CancelledError:
            pass
        finally:
            # 被取消的旧任务不得覆盖后来重触发的新任务状态
            if self._nitro_task is current_task:
                self._nitro_task = None
                self._active = False
                if self._lighting:
                    self._lighting.stop_nitro_effect()
                logger.info("氮气加速结束,进入冷却")

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def boost_factor(self) -> float:
        """当前加速倍率 (1.0 = 正常)"""
        return config.NITRO_BOOST_FACTOR if self._active else 1.0

    @property
    def cooldown_remaining(self) -> float:
        """距离下次可触发的剩余秒数。冷却从触发时刻开始计算。"""
        if self._last_trigger <= 0:
            return 0.0
        elapsed = time.monotonic() - self._last_trigger
        return round(max(0.0, config.NITRO_COOLDOWN - elapsed), 1)

    def _get_status(self) -> dict:
        return {
            "active": self._active,
            "cooling": not self._active and self.cooldown_remaining > 0,
            "cooldown_remaining": self.cooldown_remaining,
            "boost_factor": self.boost_factor,
        }

    def stop_all(self) -> None:
        """断连安全回调"""
        if self._nitro_task and not self._nitro_task.done():
            self._nitro_task.cancel()
        self._nitro_task = None
        self._active = False
        if self._lighting:
            self._lighting.stop_nitro_effect()

    def cleanup(self) -> None:
        self.stop_all()
