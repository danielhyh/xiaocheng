"""
subsystems/audio.py — 音频子系统

职责:
  - 预录音效播放 (play)
  - TTS 文字转语音 (tts)
  - 音量控制 (volume)
  - 低电量告警音联动 (alert)

不感知 ALSA / amixer 细节,只依赖 AudioDriver 接口。
"""

import asyncio
import logging
import os

from app.drivers.audio import AudioDriver
from app import config

logger = logging.getLogger(__name__)


class AudioSubsystem:
    """音频子系统: 音效播放 + TTS + 音量控制 + 低压告警"""

    def __init__(self):
        self._driver = AudioDriver()
        self._clips: dict[str, str] = {}
        self._alert_task: asyncio.Task | None = None
        self._alert_active = False

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

    async def handle_command(self, payload: dict) -> dict:
        """
        处理 cmd.audio 指令。

        payload 格式:
          { "action": "play",   "data": { "clip": "horn" } }
          { "action": "tts",    "data": { "text": "你好", "voice": "" } }
          { "action": "volume", "data": { "level": 75 } }
          { "action": "stop" }
          { "action": "get_volume" }
          { "action": "list_clips" }
        """
        action = payload.get("action", "")
        data = payload.get("data", {})

        if action == "play":
            return await self._action_play(data)
        elif action == "tts":
            return await self._action_tts(data)
        elif action == "volume":
            return self._action_volume(data)
        elif action == "get_volume":
            return {"volume": self._driver.get_volume()}
        elif action == "stop":
            self._driver.stop()
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
        asyncio.create_task(self._driver.play(filepath))
        return {"playing": clip}

    async def _action_tts(self, data: dict) -> dict:
        """TTS 文字转语音"""
        text = data.get("text", "")
        voice = data.get("voice", "")
        if not text.strip():
            return {"error": "empty text"}

        asyncio.create_task(self._driver.tts(text, voice))
        return {"tts": text}

    def _action_volume(self, data: dict) -> dict:
        """设置音量"""
        level = data.get("level")
        if level is None:
            return {"error": "missing level"}
        level = max(0, min(100, int(level)))
        self._driver.set_volume(level)
        return {"volume": level}

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
        while self._alert_active:
            if alert_clip:
                await self._driver.play(alert_clip)
            else:
                # 没有告警音效文件时用 TTS
                await self._driver.tts("电量不足,请及时充电")
            await asyncio.sleep(config.AUDIO_ALERT_INTERVAL)

    def stop_low_voltage_alert(self) -> None:
        """停止低电量告警音"""
        self._alert_active = False
        if self._alert_task and not self._alert_task.done():
            self._alert_task.cancel()
            self._alert_task = None
        self._driver.stop()
        logger.info("低电量告警音已停止")

    @property
    def volume(self) -> int:
        """当前音量"""
        return self._driver.get_volume()

    def cleanup(self) -> None:
        self.stop_low_voltage_alert()
        self._driver.cleanup()
