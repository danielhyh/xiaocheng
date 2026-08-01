---
title: 安全 Watchdog
scope: WS 断连/指令超时 500ms 自动停车，断连回调注入各子系统 stop
code: app/business/safety.py
last_verified: 2026-08-01
---
# 安全 Watchdog

## 职责
监控 `cmd.motion` 心跳，超时（500ms）或 WS 断连即强制停车，并注入各子系统的 stop 回调（电机停转、灯光复位等）。

## 关键实现 / 注意事项
- 超时阈值 500ms 与前端 100ms 发送间隔余量偏紧，网络抖动可能误触发（见 ISS-06）。
- 断连回调注入 `lighting.stop_all()` 等，保证失联时硬件回到安全态。
- motion 未启用时 Watchdog 仍可维护连接/模式状态，但不会导入或调用电机驱动。
