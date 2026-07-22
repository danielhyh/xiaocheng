---
title: 云台子系统
scope: PCA9685 舵机驱动 + 2-DOF 云台角度映射/限位/平滑
code: app/subsystems/gimbal.py
---
# 云台子系统

## 职责
驱动 PCA9685（地址 0x40，共用 I2C1_M4）上的 SG90 舵机，提供 pan/tilt 角度映射、限位、平滑，供手动 FPV 观察与后续视觉追踪的云台补偿。

## 关键实现 / 注意事项
- 目标通道：CH0=前 Pan、CH1=前 Tilt、CH2=前扫描舵机预留、CH3=后 Pan、CH4=后 Tilt。
- 当前代码仅配置 CH2/CH3，且与“大灯占 CH0/1”的旧软件方案耦合；重接线前必须按目标通道修正，不能把当前常量当接线依据。
- 40-pin PWM 已被电机/大灯占满，舵机一律走 PCA9685 I2C PWM。
- 大灯走 Pin33，不占 PCA9685 通道。
- **软件骨架已存在，重接后的 PCA9685/双云台真板复验未完成**：未填 `last_verified`。
