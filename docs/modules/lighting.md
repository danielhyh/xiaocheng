---
title: 灯光子系统
scope: 车灯模式管理（off/tail/brake/reverse/police/ambient）+ 运动联动
code: app/subsystems/lighting.py
last_verified: 2026-08-01
decisions: [ADR-011]
---
# 灯光子系统

## 职责
管理前大灯与 WS2812B 尾灯灯带（SPI bitbang，软件分段 left/tail/right），提供模式切换并与运动状态联动（刹车加亮尾灯、倒车白灯、警灯闪烁）。

## 关键实现 / 注意事项
- 目标硬件接线：大灯自带驱动，正极走电池轨、负极共地、SIG 直连 Pin33/PWM15_M2；PCA9685 只服务舵机（见 ADR-011）。
- `app/drivers/led/` 当前仍是 PCA9685 I2C 实现，与目标硬件不一致；Real 初始化已失败关闭，完成 `P8-01` 前必须保持 lighting 禁用。
- 灯带驱动 `app/drivers/strip/` 仍为 WS2812B + Pin19 SPI + 74AHCT125 方案。
- `last_verified` 只表示禁用隔离与冲突保护已核对；Pin 33 驱动迁移及重接后的真板实测未完成。
- 断连时由 safety 注入 `stop_all()` 复位。
