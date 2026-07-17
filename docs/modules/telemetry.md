---
title: 遥测推送
scope: tel.motion + tel.sensors 推送（真实电压 + 电量 + CPU 温度）
code: app/business/telemetry.py
last_verified: 2026-06-25
decisions: [ADR-006]
---
# 遥测推送

## 职责
周期性采集运动状态与传感器数据，封装成 `tel.motion` / `tel.sensors` envelope 推送给前端 HUD。

## 关键实现 / 注意事项
- 传感器数据来自 sensing 子系统（电压/电量/CPU 温度），已接真实 ADS1115。
- 后续（Phase 7）补 Wi-Fi RSSI、WS 往返延迟、CPU 占用率。
