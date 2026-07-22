"""
subsystems/lighting.py — 灯光子系统

职责:
  - 前大灯控制 (开/关/调光)
  - 灯带分段控制 (尾灯/左侧/右侧)
  - 灯光模式管理 (常亮/刹车/倒车/警灯/氛围灯)
  - 与 motion 联动 (刹车尾灯加亮、倒车白灯、转向灯)

不感知 PCA9685 / SPI 细节,只依赖 LedDriver + StripDriver 接口。
"""

import asyncio
import logging
import random

from app.drivers.led import LedDriver
from app.drivers.strip import StripDriver
from app import config

logger = logging.getLogger(__name__)


class LightingSubsystem:
    """灯光子系统: 前大灯 + WS2812B 灯带"""

    STRIP_MODES = frozenset({
        "off", "tail", "brake", "reverse", "police", "ambient", "nitro",
    })

    def __init__(self):
        self._led = LedDriver()
        self._strip = StripDriver()

        # 前大灯状态
        self._headlight_on = False
        self._headlight_brightness = config.LED_DEFAULT_BRIGHTNESS

        # 灯带模式
        self._strip_mode = "off"  # off / tail / brake / reverse / police / ambient
        self._mode_task: asyncio.Task | None = None
        self._mode_active = False
        self._nitro_restore_mode: str | None = None

        # 联动状态 (由 dispatcher 调用)
        self._braking = False
        self._reversing = False

    def init(self) -> None:
        self._led.init()
        self._strip.init()
        logger.info("LightingSubsystem 初始化完成")

    async def handle_command(self, payload: dict) -> dict:
        """
        处理 cmd.light 指令。

        payload 格式:
          { "action": "headlight",  "data": { "on": true } }
          { "action": "headlight",  "data": { "brightness": 80 } }
          { "action": "strip_mode", "data": { "mode": "tail" } }
          { "action": "strip_brightness", "data": { "brightness": 128 } }
          { "action": "status" }
        """
        action = payload.get("action", "")
        data = payload.get("data", {})

        if action == "headlight":
            return self._action_headlight(data)
        elif action == "strip_mode":
            return await self._action_strip_mode(data)
        elif action == "strip_brightness":
            return self._action_strip_brightness(data)
        elif action == "status":
            return self._get_status()
        else:
            logger.warning(f"未知灯光动作: {action}")
            return {"error": f"unknown action: {action}"}

    # ---- 前大灯 ----

    def _action_headlight(self, data: dict) -> dict:
        """控制前大灯"""
        if "on" in data:
            self._headlight_on = bool(data["on"])
        if "brightness" in data:
            self._headlight_brightness = max(0, min(100, int(data["brightness"])))

        if self._headlight_on:
            self._led.set_both(self._headlight_brightness)
        else:
            self._led.set_both(0)

        return {
            "headlight": self._headlight_on,
            "brightness": self._headlight_brightness,
        }

    # ---- 灯带模式 ----

    async def _action_strip_mode(self, data: dict) -> dict:
        """切换灯带模式"""
        mode = data.get("mode", "off")
        if mode == "nitro":
            return {"error": "nitro mode is managed by NitroSubsystem"}
        if mode not in self.STRIP_MODES:
            logger.warning(f"未知灯带模式: {mode}")
            return {"error": f"unknown strip mode: {mode}"}
        if self._strip_mode == "nitro":
            return {"error": "nitro effect is active"}
        if mode == self._strip_mode:
            return {"strip_mode": mode}

        # 停止当前模式
        self._stop_mode_task()
        self._start_strip_mode(mode)

        return {"strip_mode": mode}

    def _action_strip_brightness(self, data: dict) -> dict:
        """设置灯带全局亮度"""
        brightness = max(0, min(255, int(data.get("brightness", 128))))
        self._strip.set_brightness(brightness)
        # 重新刷新当前模式
        self._refresh_current_mode()
        return {"strip_brightness": brightness}

    # ---- 静态灯效 ----

    def _apply_tail(self) -> None:
        """尾灯: 中央红色低亮度"""
        self._strip.set_segment("all", 0, 0, 0)
        self._strip.set_segment("tail", *config.STRIP_COLOR_TAIL)
        self._strip.show()

    def _apply_brake(self) -> None:
        """刹车灯: 中央红色高亮度"""
        self._strip.set_segment("all", 0, 0, 0)
        self._strip.set_segment("tail", *config.STRIP_COLOR_BRAKE)
        self._strip.show()

    def _apply_reverse(self) -> None:
        """倒车灯: 中央白色"""
        self._strip.set_segment("all", 0, 0, 0)
        self._strip.set_segment("tail", *config.STRIP_COLOR_REVERSE)
        self._strip.show()

    # ---- 动态灯效 (异步循环) ----

    async def _police_loop(self) -> None:
        """警灯: 左红右蓝交替闪烁"""
        try:
            while self._mode_active:
                # 左红 右灭
                self._strip.set_segment("all", 0, 0, 0)
                self._strip.set_segment("left", 255, 0, 0)
                self._strip.set_segment("tail", 255, 0, 0)
                self._strip.show()
                await asyncio.sleep(0.15)

                # 全灭
                self._strip.clear()
                await asyncio.sleep(0.05)

                # 左灭 右蓝
                self._strip.set_segment("all", 0, 0, 0)
                self._strip.set_segment("right", 0, 0, 255)
                self._strip.set_segment("tail", 0, 0, 255)
                self._strip.show()
                await asyncio.sleep(0.15)

                # 全灭
                self._strip.clear()
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

    async def _ambient_loop(self) -> None:
        """氛围灯: 彩虹渐变循环"""
        offset = 0
        try:
            while self._mode_active:
                for i in range(self._strip.num_leds):
                    hue = ((i * 256 // self._strip.num_leds) + offset) % 256
                    r, g, b = self._hsv_to_rgb(hue, 255, 200)
                    self._strip.set_pixel(i, r, g, b)
                self._strip.show()
                offset = (offset + 4) % 256
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

    async def _nitro_loop(self) -> None:
        """氮气灯效: 火焰色灯带 + 已开启大灯快速闪烁。"""
        try:
            while self._mode_active and self._strip_mode == "nitro":
                for i in range(self._strip.num_leds):
                    self._strip.set_pixel(
                        i,
                        random.randint(200, 255),
                        random.randint(20, 100),
                        0,
                    )
                self._strip.show()
                if self._headlight_on:
                    self._led.set_both(100)
                await asyncio.sleep(0.1)
                if self._headlight_on:
                    self._led.set_both(self._headlight_brightness)
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            if self._headlight_on:
                self._led.set_both(self._headlight_brightness)

    @staticmethod
    def _hsv_to_rgb(h: int, s: int, v: int) -> tuple[int, int, int]:
        """简易 HSV → RGB (h: 0-255, s: 0-255, v: 0-255)"""
        if s == 0:
            return v, v, v
        region = h // 43
        remainder = (h - region * 43) * 6
        p = (v * (255 - s)) >> 8
        q = (v * (255 - ((s * remainder) >> 8))) >> 8
        t = (v * (255 - ((s * (255 - remainder)) >> 8))) >> 8
        if region == 0:
            return v, t, p
        elif region == 1:
            return q, v, p
        elif region == 2:
            return p, v, t
        elif region == 3:
            return p, q, v
        elif region == 4:
            return t, p, v
        else:
            return v, p, q

    # ---- Motion 联动 ----

    def on_brake(self) -> None:
        """刹车联动: 尾灯加亮红色 (由 dispatcher 调用)"""
        if self._braking:
            return
        self._braking = True
        if self._strip_mode in ("off", "tail"):
            self._stop_mode_task()
            self._strip_mode = "brake"
            self._apply_brake()
            # 大灯闪一下
            if self._headlight_on:
                self._led.set_both(100)

    def on_brake_release(self) -> None:
        """刹车释放: 恢复之前的灯效"""
        if not self._braking:
            return
        self._braking = False
        if self._strip_mode == "brake":
            if self._headlight_on:
                self._strip_mode = "tail"
                self._apply_tail()
                self._led.set_both(self._headlight_brightness)
            else:
                self._strip_mode = "off"
                self._strip.clear()

    def on_reverse_start(self) -> None:
        """倒车联动: 白色倒车灯 (由 dispatcher 调用)"""
        if self._reversing:
            return
        self._reversing = True
        if self._strip_mode in ("off", "tail"):
            self._stop_mode_task()
            self._strip_mode = "reverse"
            self._apply_reverse()

    def on_reverse_stop(self) -> None:
        """倒车结束: 恢复"""
        if not self._reversing:
            return
        self._reversing = False
        if self._strip_mode == "reverse":
            if self._headlight_on:
                self._strip_mode = "tail"
                self._apply_tail()
            else:
                self._strip_mode = "off"
                self._strip.clear()

    # ---- 内部工具 ----

    def start_nitro_effect(self) -> None:
        """启动临时氮气灯效，并记住当前模式以便结束后恢复。"""
        if self._strip_mode == "nitro":
            return
        self._nitro_restore_mode = self._strip_mode
        self._stop_mode_task()
        self._start_strip_mode("nitro")

    def stop_nitro_effect(self) -> None:
        """停止氮气灯效并恢复触发前的灯带模式。"""
        if self._strip_mode != "nitro":
            return
        restore_mode = self._nitro_restore_mode or "off"
        self._nitro_restore_mode = None
        self._stop_mode_task()
        self._start_strip_mode(restore_mode)

    def _start_strip_mode(self, mode: str) -> None:
        """应用一个已校验的灯带模式。调用前须先停止当前动态任务。"""
        self._strip_mode = mode
        if mode == "off":
            self._strip.clear()
        elif mode == "tail":
            self._apply_tail()
        elif mode == "brake":
            self._apply_brake()
        elif mode == "reverse":
            self._apply_reverse()
        elif mode == "police":
            self._mode_active = True
            self._mode_task = asyncio.create_task(self._police_loop())
        elif mode == "ambient":
            self._mode_active = True
            self._mode_task = asyncio.create_task(self._ambient_loop())
        elif mode == "nitro":
            self._mode_active = True
            self._mode_task = asyncio.create_task(self._nitro_loop())

    def _stop_mode_task(self) -> None:
        """停止当前动态灯效任务"""
        self._mode_active = False
        if self._mode_task and not self._mode_task.done():
            self._mode_task.cancel()
            self._mode_task = None

    def _refresh_current_mode(self) -> None:
        """亮度变更后重新应用当前静态模式"""
        if self._strip_mode == "tail":
            self._apply_tail()
        elif self._strip_mode == "brake":
            self._apply_brake()
        elif self._strip_mode == "reverse":
            self._apply_reverse()

    def _get_status(self) -> dict:
        """返回当前灯光状态"""
        return {
            "headlight_on": self._headlight_on,
            "headlight_brightness": self._headlight_brightness,
            "strip_mode": self._strip_mode,
        }

    def stop_all(self) -> None:
        """断连安全回调: 关闭所有灯效"""
        self._stop_mode_task()
        self._strip_mode = "off"
        self._nitro_restore_mode = None
        self._strip.clear()
        # 大灯保持当前状态 (断连不关大灯,安全考虑)
        logger.info("灯光子系统: 灯效已停止")

    def cleanup(self) -> None:
        self._stop_mode_task()
        self._led.cleanup()
        self._strip.cleanup()
