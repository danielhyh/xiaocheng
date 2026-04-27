"""
drivers/audio/real.py — 真实音频驱动

通过 aplay 播放 wav,edge-tts 合成语音,amixer 控制音量。
只在 Orange Pi 上运行 (需要 ALSA + USB 声卡)。
"""

import asyncio
import logging
import os
import tempfile

from app import config

logger = logging.getLogger(__name__)


class RealAudioDriver:
    """
    真实音频驱动。

    - 播放: aplay (wav) / mpv (mp3/其他格式)
    - TTS: edge-tts → 临时 mp3 → mpv 播放
    - 音量: amixer 控制 USB 声卡
    """

    def __init__(self):
        self._card = config.AUDIO_CARD
        self._device = f"hw:{self._card},0"
        self._numid = config.AUDIO_VOLUME_NUMID
        self._vol_max = config.AUDIO_VOLUME_MAX
        self._current_process: asyncio.subprocess.Process | None = None
        self._tts_voice = config.AUDIO_TTS_VOICE

    def init(self) -> None:
        """检测声卡是否存在"""
        card_path = f"/proc/asound/card{self._card}"
        if not os.path.exists(card_path):
            logger.warning(
                f"声卡 card{self._card} 未检测到 ({card_path}),"
                "音频功能将不可用"
            )
        else:
            logger.info(
                f"RealAudioDriver 初始化完成 (card={self._card},"
                f" device={self._device})"
            )
        # 设置初始音量
        self.set_volume(config.AUDIO_DEFAULT_VOLUME)

    async def play(self, filepath: str) -> None:
        """播放音频文件 (wav 用 aplay, 其他用 mpv)"""
        if not os.path.isfile(filepath):
            logger.warning(f"音频文件不存在: {filepath}")
            return

        # 停止当前播放
        self.stop()

        if filepath.endswith(".wav"):
            cmd = ["aplay", "-D", self._device, filepath]
        else:
            # ffplay 播放 mp3 等格式 (-nodisp 无窗口, -autoexit 播完退出)
            cmd = [
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "error",
                filepath,
            ]

        logger.info(f"播放: {filepath}")
        try:
            # ffplay 需要 AUDIODEV 环境变量指定 ALSA 设备
            env = dict(os.environ)
            env["AUDIODEV"] = self._device
            self._current_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            _, stderr = await self._current_process.communicate()
            if self._current_process.returncode != 0:
                err = stderr.decode().strip() if stderr else "unknown"
                logger.warning(f"播放失败 (rc={self._current_process.returncode}): {err}")
        except FileNotFoundError as e:
            logger.error(f"播放命令不存在: {e}")
        finally:
            self._current_process = None

    async def tts(self, text: str, voice: str = "") -> None:
        """edge-tts 合成语音并播放"""
        if not text.strip():
            return

        voice = voice or self._tts_voice

        # 生成临时 mp3
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            # 调用 edge-tts CLI
            cmd = [
                "edge-tts",
                "--voice", voice,
                "--text", text,
                "--write-media", tmp_path,
            ]
            logger.info(f"TTS: '{text}' (voice={voice})")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode != 0:
                err = stderr.decode().strip() if stderr else "unknown"
                logger.warning(f"edge-tts 合成失败: {err}")
                return

            # 播放合成的 mp3
            await self.play(tmp_path)
        except FileNotFoundError:
            logger.error("edge-tts 未安装,请运行: pip install edge-tts")
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def set_volume(self, level: int) -> None:
        """通过 amixer 设置音量 (0-100 映射到 0-vol_max)"""
        level = max(0, min(100, level))
        raw = round(level / 100 * self._vol_max)

        try:
            os.popen(
                f"amixer -c {self._card} cset numid={self._numid} {raw},{raw}"
            ).read()
            logger.debug(f"音量设置: {level}% (raw={raw}/{self._vol_max})")
        except Exception as e:
            logger.warning(f"设置音量失败: {e}")

    def get_volume(self) -> int:
        """读取当前音量"""
        try:
            output = os.popen(
                f"amixer -c {self._card} cget numid={self._numid}"
            ).read()
            # 解析 ": values=X,X"
            for line in output.splitlines():
                if ": values=" in line:
                    val_str = line.split("=")[1].split(",")[0]
                    raw = int(val_str)
                    return round(raw / self._vol_max * 100)
        except Exception as e:
            logger.warning(f"读取音量失败: {e}")
        return 0

    def stop(self) -> None:
        """停止当前播放"""
        if self._current_process and self._current_process.returncode is None:
            try:
                self._current_process.terminate()
            except ProcessLookupError:
                pass
            self._current_process = None

    def cleanup(self) -> None:
        self.stop()
        logger.info("RealAudioDriver 资源已释放")
