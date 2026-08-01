---
title: 摄像头驱动 / 视频流
scope: OV13855 MIPI NV12 与 OV5640 USB MJPG 单活动流采集，含 Real/Mock
code: app/drivers/camera/
last_verified: 2026-08-01
decisions: [ADR-005, ADR-008]
---
# 摄像头驱动 / 视频流

## 职责
OpenCV V4L2 自动发现 OV13855 的 RKISP 成像节点或 OV5640 USB 节点，经独立 MJPEG endpoint（`app/api/stream.py`）推流。当前仍是单活动实例；front/rear 双实例与双端点由 `P3-03` 实施。

## 关键实现 / 注意事项
- MJPEG 走独立连接，与 WS 控制通道隔离，视频卡顿不影响指令实时性（见 ADR-005）。
- 倒车时 `ReversePiP` 根据 `motion.vy < 0` 自动放大，也支持手动放大/缩小。
- 设备发现优先 `/dev/video-camera*`、USB by-id，再扫描普通 `/dev/videoN`；过滤 RKISP/RKCIF 的 RAW、统计、参数与辅助节点。
- MIPI 请求 NV12、USB 请求 MJPG，但最终以驱动读回的 FOURCC 决定解码；请求被拒绝时回退到 OpenCV 的 BGR 转换，不能把其他格式误按 NV12 reshape。
- 2026-08-01 OV13855 板端复验：`/dev/video-camera0 → /dev/video11`、NV12 1280×720，直接采集约 13.6 FPS，完整 vision 生命周期约 12.6 FPS。
- OV5640 的 MJPG 路径此前已实测；本轮未接 USB 摄像头，格式回退由纯单测覆盖。
