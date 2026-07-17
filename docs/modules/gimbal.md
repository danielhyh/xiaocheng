---
title: 云台子系统
scope: PCA9685 舵机驱动 + 2-DOF 云台角度映射/限位/平滑
code: app/subsystems/gimbal.py
---
# 云台子系统

## 职责
驱动 PCA9685（地址 0x40，共用 I2C1_M4）上的 SG90 舵机，提供 pan/tilt 角度映射、限位、平滑，供手动 FPV 观察与后续视觉追踪的云台补偿。

## 关键实现 / 注意事项
- CH0=pan / CH1=tilt / CH2=前扫描舵机（Phase 6 预留）。
- 40-pin PWM 已被电机/大灯占满，舵机一律走 PCA9685 I2C PWM。
- **Phase 4 实施中**：未填 `last_verified`，看板显示「编写中」。
