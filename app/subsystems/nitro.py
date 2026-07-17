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
        self._cooling = False
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
        self._nitro_task = asyncio.create_task(self._nitro_effect())
        logger.info("🔥 氮气加速触发!")
        return {"nitro": "activated", "duration": config.NITRO_DURATION}

    async def _nitro_effect(self) -> None:
        """氮气加速效果循环"""
        try:
            # 播放音效
            if self._audio:
                asyncio.create_task(
                    self._audio.handle_command({
                        "action": "play",
                        "data": {"clip": "nitro"},
                    })
                )

            # 灯效: 灯带火焰色
            if self._lighting:
                self._lighting._stop_mode_task()
                self._lighting._strip_mode = "nitro"
                self._lighting._mode_active = True
                self._lighting._mode_task = asyncio.create_task(
                    self._flame_loop()
                )

            # 持续 NITRO_DURATION 秒
            start = time.monotonic()
            while time.monotonic() - start < config.NITRO_DURATION:
                # 大灯闪烁
                if self._lighting and self._lighting._headlight_on:
                    self._lighting._led.set_both(100)
                    await asyncio.sleep(0.1)
                    self._lighting._led.set_both(
                        self._lighting._headlight_brightness
                    )
                    await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(0.2)

        except asyncio.CancelledError:
            pass
        finally:
            self._active = False
            self._cooling = True
            # 恢复灯效
            if self._lighting:
                self._lighting._stop_mode_task()
                self._lighting._strip_mode = "off"
                self._lighting._strip.clear()
                if self._lighting._headlight_on:
                    self._lighting._led.set_both(
                        self._lighting._headlight_brightness
                    )
            logger.info("氮气加速结束,进入冷却")

            # 冷却计时
            await asyncio.sleep(config.NITRO_COOLDOWN)
            self._cooling = False

    async def _flame_loop(self) -> None:
        """火焰灯效: 红橙黄随机闪烁"""
        import random
        strip = self._lighting._strip
        try:
            while self._lighting._mode_active:
                for i in range(strip._num_leds):
                    # 火焰色: 红为主,随机橙黄
                    r = random.randint(200, 255)
                    g = random.randint(20, 100)
                    b = 0
                    strip.set_pixel(i, r, g, b)
                strip.show()
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            strip.clear()

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def boost_factor(self) -> float:
        """当前加速倍率 (1.0 = 正常)"""
        return config.NITRO_BOOST_FACTOR if self._active else 1.0

    def _get_status(self) -> dict:
        now = time.monotonic()
        cooldown_remaining = 0.0
        if self._last_trigger > 0:
            elapsed = now - self._last_trigger
            if elapsed < config.NITRO_COOLDOWN:
                cooldown_remaining = round(config.NITRO_COOLDOWN - elapsed, 1)

        return {
            "active": self._active,
            "cooling": self._cooling,
            "cooldown_remaining": cooldown_remaining,
            "boost_factor": self.boost_factor,
        }

    def stop_all(self) -> None:
        """断连安全回调"""
        if self._nitro_task and not self._nitro_task.done():
            self._nitro_task.cancel()
            self._nitro_task = None
        self._active = False

    def cleanup(self) -> None:
        self.stop_all()
