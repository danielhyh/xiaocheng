"""
drivers/audio/protocol.py — 音频驱动接口定义

所有音频驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。
"""

from typing import Protocol


class AudioDriverProtocol(Protocol):
    """音频驱动接口"""

    def init(self) -> None:
        """初始化音频设备 (检测声卡等)"""
        ...

    async def play(self, filepath: str, channel: str = "main") -> None:
        """
        播放音频文件。

        参数:
            filepath: wav/mp3 文件路径
        """
        ...

    async def play_loop(self, filepath: str, channel: str = "main") -> None:
        """循环播放音频文件,直到对应通道被停止或任务被取消。"""
        ...

    async def tts(self, text: str, voice: str = "", channel: str = "main") -> None:
        """
        文字转语音并播放。

        参数:
            text: 要朗读的文本
            voice: TTS 语音名称 (空字符串使用默认)
        """
        ...

    def set_volume(self, level: int) -> None:
        """
        设置音量。

        参数:
            level: 0-100 百分比
        """
        ...

    def get_volume(self) -> int:
        """获取当前音量 (0-100)"""
        ...

    def stop(self) -> None:
        """停止当前播放"""
        ...

    def stop_channel(self, channel: str) -> None:
        """停止指定播放通道"""
        ...

    def cleanup(self) -> None:
        """释放资源"""
        ...
