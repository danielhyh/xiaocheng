---
title: 灯光子系统
scope: 车灯模式管理（off/tail/brake/reverse/police/ambient）+ 运动联动
code: app/subsystems/lighting.py
decisions: [ADR-009]
---
# 灯光子系统

## 职责
管理前大灯（PCA9685 PWM 调光）与 WS2812B 尾灯灯带（SPI bitbang，软件分段 left/tail/right），提供模式切换并与运动状态联动（刹车加亮尾灯、倒车白灯、警灯闪烁）。

## 关键实现 / 注意事项
- 大灯驱动 `app/drivers/led/`（PCA9685 I2C，原始 I2C 零依赖）；灯带驱动 `app/drivers/strip/`（WS2812B）。
- 大灯走 MOS 触发模块而非 IRF520（3.3V 无法有效驱动，见 ADR-009）。
- **软件侧已实现，硬件接线与真板实测待落地**（Phase 8）：故未填 `last_verified`。
- 断连时由 safety 注入 `stop_all()` 复位。
