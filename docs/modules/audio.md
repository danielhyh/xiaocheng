---
title: 音频子系统
scope: 音效播放、TTS、鸣笛循环、倒车提示、低压告警
code: app/subsystems/audio.py
last_verified: 2026-06-25
decisions: [ADR-008]
---
# 音频子系统

## 职责
封装 USB 声卡（aplay/ffplay/edge-tts/amixer），提供音效播放、中文 TTS、按住鸣笛循环、开机音效、倒车提示、低电量告警循环。驱动层在 `app/drivers/audio/`（Real/Mock）。

## 关键实现 / 注意事项
- USB 免驱声卡 Jieli UACDemoV1.0（card3，48000Hz/S16LE/2ch），`AUDIODEV=hw:3,0`。
- wav 用 aplay、mp3 用 ffplay（曾用 mpv，已替换）。
- TTS：edge-tts，zh-CN-YunxiNeural。音量：amixer numid=4（0–147）。
- 音效套装由 Python 程序合成（horn/startup/low_battery/reverse/warning/nitro/connect/disconnect）。
- 倒车提示由 motion `vy < -0.1` 联动触发。
