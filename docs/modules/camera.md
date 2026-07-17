---
title: 摄像头驱动 / FPV
scope: OV5640 UVC 摄像头采集 + MJPEG 流，含 Real/Mock
code: app/drivers/camera/
last_verified: 2026-06-25
decisions: [ADR-005, ADR-008]
---
# 摄像头驱动 / FPV

## 职责
OpenCV V4L2 采集 `/dev/video0`，经独立 MJPEG endpoint（`app/api/stream.py`）推流，前端 `<img>` 直接嵌入。Real/Mock 双实现。

## 关键实现 / 注意事项
- MJPEG 走独立连接，与 WS 控制通道隔离，视频卡顿不影响指令实时性（见 ADR-005）。
- 摄像头固定在云台上（车顶最高点）。软件侧已完成，待板端接 `/dev/video0` 实测（Phase 3）。
