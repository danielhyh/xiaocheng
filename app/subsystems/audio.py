"""
subsystems/audio.py — 音频子系统

职责:
  - 预录音效播放 (play)
  - 鸣笛循环 (horn_start / horn_stop): 按住持续鸣笛
  - TTS 文字转语音 (tts)
  - 音量控制 (volume)
  - 低电量告警音联动 (alert)
  - 启动音效 (startup)
  - 倒车提示音 (reverse)

不感知 ALSA / amixer 细节,只依赖 AudioDriver 接口。
"""

import asyncio
import logging
import os

from app.drivers.audio import AudioDriver
from app import config

logger = logging.getLogger(__name__)


class AudioSubsystem:
    """音频子系统: 音效播放 + TTS + 音量控制 + 低压告警 + 鸣笛循环 + 倒车提示"""

    def __init__(self):
        self._driver = AudioDriver()
        self._clips: dict[str, str] = {}
        self._alert_task: asyncio.Task | None = None
        self._alert_active = False
        self._horn_task: asyncio.Task | None = None
        self._horn_active = False
        self._reverse_task: asyncio.Task | None = None
        self._reverse_active = False
        self._tts_task: asyncio.Task | None = None
        self._tts_active = False

    def init(self) -> None:
        self._driver.init()
        self._scan_clips()
        logger.info(
            f"AudioSubsystem 初始化完成 (音效: {len(self._clips)} 个)"
        )

    def _scan_clips(self) -> None:
        """扫描音效目录,建立 clip_name → filepath 映射"""
        clips_dir = config.AUDIO_CLIPS_DIR
        if not os.path.isdir(clips_dir):
            logger.info(f"音效目录不存在,创建: {clips_dir}")
            os.makedirs(clips_dir, exist_ok=True)
            return

        for fname in os.listdir(clips_dir):
            if fname.endswith((".wav", ".mp3")):
                name = os.path.splitext(fname)[0]
                self._clips[name] = os.path.join(clips_dir, fname)
                logger.debug(f"  音效: {name} → {fname}")

    async def play_startup(self) -> None:
        """播放开机音效 (启动时调用)"""
        clip = self._clips.get("startup")
        if clip:
            await self._driver.play(clip, channel="sfx")
            logger.info("开机音效播放完毕")

    async def handle_command(self, payload: dict) -> dict:
        """
        处理 cmd.audio 指令。

        payload 格式:
          { "action": "play",       "data": { "clip": "horn" } }
          { "action": "horn_start" }
          { "action": "horn_stop" }
          { "action": "tts",        "data": { "text": "你好", "voice": "" } }
          { "action": "volume",     "data": { "level": 75 } }
          { "action": "stop" }
          { "action": "get_volume" }
          { "action": "list_clips" }
        """
        action = payload.get("action", "")
        data = payload.get("data", {})

        if action == "play":
            return await self._action_play(data)
        elif action == "horn_start":
            return self._action_horn_start()
        elif action == "horn_stop":
            return self._action_horn_stop()
        elif action == "tts":
            return await self._action_tts(data)
        elif action == "volume":
            return self._action_volume(data)
        elif action == "get_volume":
            return {"volume": self._driver.get_volume()}
        elif action == "stop":
            self._stop_all_playback()
            return {"stopped": True}
        elif action == "list_clips":
            return {"clips": list(self._clips.keys())}
        else:
            logger.warning(f"未知音频动作: {action}")
            return {"error": f"unknown action: {action}"}

    async def _action_play(self, data: dict) -> dict:
        """播放预录音效"""
        clip = data.get("clip", "")
        filepath = self._clips.get(clip)
        if not filepath:
            available = list(self._clips.keys())
            logger.warning(f"音效 '{clip}' 不存在,可用: {available}")
            return {"error": f"clip not found: {clip}", "available": available}

        # 异步播放,不阻塞指令处理
        if self._horn_active:
            return {"playing": clip, "skipped": "horn_active"}
        asyncio.create_task(self._driver.play(filepath, channel="sfx"))
        return {"playing": clip}

    async def _action_tts(self, data: dict) -> dict:
        """TTS 文字转语音"""
        text = data.get("text", "")
        voice = data.get("voice", "")
        if not text.strip():
            return {"error": "empty text"}

        if self._horn_active:
            return {"tts": text, "skipped": "horn_active"}

        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()
            self._driver.stop_channel("tts")
        self._tts_task = asyncio.create_task(self._run_tts(text, voice))
        return {"tts": text}

    async def _run_tts(self, text: str, voice: str) -> None:
        """播放 TTS。TTS 期间暂停倒车提示,播完后倒车循环会自动恢复。"""
        self._tts_active = True
        self._driver.stop_channel("reverse")
        try:
            await self._driver.tts(text, voice, channel="tts")
        except asyncio.CancelledError:
            self._driver.stop_channel("tts")
        finally:
            self._tts_active = False

    def _action_volume(self, data: dict) -> dict:
        """设置音量"""
        level = data.get("level")
        if level is None:
            return {"error": "missing level"}
        level = max(0, min(100, int(level)))
        self._driver.set_volume(level)
        return {"volume": level}

    # ---- 鸣笛循环 (按住不松) ----

    def _action_horn_start(self) -> dict:
        """开始循环鸣笛"""
        if self._horn_active:
            return {"horn": "already_playing"}
        self._horn_active = True
        self._driver.stop_channel("reverse")
        self._driver.stop_channel("alert")
        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()
            self._driver.stop_channel("tts")
        self._horn_task = asyncio.create_task(self._horn_loop())
        return {"horn": "started"}

    def _action_horn_stop(self) -> dict:
        """停止鸣笛"""
        self._horn_active = False
        if self._horn_task and not self._horn_task.done():
            self._horn_task.cancel()
            self._horn_task = None
        self._driver.stop_channel("horn")
        return {"horn": "stopped"}

    async def _horn_loop(self) -> None:
        """循环播放 horn 音效直到松开"""
        horn_clip = self._clips.get("horn")
        if not horn_clip:
            return
        try:
            await self._driver.play_loop(horn_clip, channel="horn")
        except asyncio.CancelledError:
            self._driver.stop_channel("horn")

    # ---- 倒车提示音 ----

    def start_reverse_beep(self) -> None:
        """开始倒车提示音 (由 motion 子系统调用)"""
        if self._reverse_active:
            return
        self._reverse_active = True
        self._reverse_task = asyncio.create_task(self._reverse_loop())
        logger.debug("倒车提示音启动")

    def stop_reverse_beep(self) -> None:
        """停止倒车提示音"""
        if not self._reverse_active:
            return
        self._reverse_active = False
        if self._reverse_task and not self._reverse_task.done():
            self._reverse_task.cancel()
            self._reverse_task = None
        self._driver.stop_channel("reverse")
        logger.debug("倒车提示音停止")

    async def _reverse_loop(self) -> None:
        """循环播放倒车音效"""
        reverse_clip = self._clips.get("reverse")
        if not reverse_clip:
            return
        try:
            while self._reverse_active:
                if self._horn_active or self._tts_active:
                    self._driver.stop_channel("reverse")
                    await asyncio.sleep(0.1)
                    continue
                await self._driver.play(reverse_clip, channel="reverse")
                if self._reverse_active:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            self._driver.stop_channel("reverse")

    # ---- 低电量告警联动 ----

    async def start_low_voltage_alert(self) -> None:
        """开始循环播放低电量告警音"""
        if self._alert_active:
            return
        self._alert_active = True
        self._alert_task = asyncio.create_task(self._alert_loop())
        logger.warning("低电量告警音已启动")

    async def _alert_loop(self) -> None:
        """循环播放告警音效"""
        alert_clip = self._clips.get("low_battery")
        try:
            while self._alert_active:
                if self._horn_active:
                    self._driver.stop_channel("alert")
                    await asyncio.sleep(0.5)
                    continue
                if alert_clip:
                    await self._driver.play(alert_clip, channel="alert")
                else:
                    await self._driver.tts("电量不足,请及时充电", channel="alert")
                await asyncio.sleep(config.AUDIO_ALERT_INTERVAL)
        except asyncio.CancelledError:
            self._driver.stop_channel("alert")

    def stop_low_voltage_alert(self) -> None:
        """停止低电量告警音"""
        self._alert_active = False
        if self._alert_task and not self._alert_task.done():
            self._alert_task.cancel()
            self._alert_task = None
        self._driver.stop_channel("alert")
        logger.info("低电量告警音已停止")

    @property
    def volume(self) -> int:
        """当前音量"""
        return self._driver.get_volume()

    def _stop_all_playback(self) -> None:
        self._alert_active = False
        self._horn_active = False
        self._reverse_active = False
        self._tts_active = False
        for task in (self._alert_task, self._horn_task, self._reverse_task, self._tts_task):
            if task and not task.done():
                task.cancel()
        self._alert_task = None
        self._horn_task = None
        self._reverse_task = None
        self._tts_task = None
        self._driver.stop()

    def cleanup(self) -> None:
        self._stop_all_playback()
        self._driver.cleanup()
