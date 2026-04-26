# 音效文件目录

将 `.wav` 或 `.mp3` 音效文件放在此目录下。
文件名（不含扩展名）即为音效 clip 名称。

## 建议音效

| 文件名 | 用途 |
|---|---|
| `horn.wav` | 鸣笛 |
| `low_battery.wav` | 低电量告警 (循环播放) |
| `reverse.wav` | 倒车提示音 |
| `startup.wav` | 开机音效 |
| `warning.wav` | 通用警告音 |

## 格式要求

- 采样率: 48000 Hz (USB 声卡仅支持此采样率)
- 格式: 16-bit PCM (S16_LE)
- 声道: 双声道 (stereo)

生成测试音效 (440Hz 蜂鸣 1 秒):
```bash
ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -ar 48000 -ac 2 horn.wav
```
