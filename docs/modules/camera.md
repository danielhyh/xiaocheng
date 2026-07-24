---
title: 摄像头驱动 / 倒车影像
scope: 后置 OV5640 UVC 摄像头采集 + MJPEG 倒车影像，含 Real/Mock
code: app/drivers/camera/
last_verified: 2026-07-23
decisions: [ADR-005, ADR-008]
---
# 摄像头驱动 / 倒车影像

## 职责
OpenCV V4L2 采集后置 `/dev/video0`，经独立 MJPEG endpoint（`app/api/stream.py`）推流，前端左上角 `ReversePiP` 直接嵌入。Real/Mock 双实现。中央 `FPVStage` 预留给未来的前置主摄像头。

## 关键实现 / 注意事项
- MJPEG 走独立连接，与 WS 控制通道隔离，视频卡顿不影响指令实时性（见 ADR-005）。
- 倒车时 `ReversePiP` 根据 `motion.vy < 0` 自动放大，也支持手动放大/缩小。
- 2026-07-22 已完成板端实测：MJPG 1280×720，实际约 12–12.5 FPS。
- 当前单摄阶段沿用 `/stream/camera`；增加前置主摄像头时再拆分为 `/stream/front` 与 `/stream/rear`。
