---
title: 云台子系统
scope: PCA9685 舵机驱动 + 2-DOF 云台角度映射/限位/平滑
code: app/subsystems/gimbal.py
last_verified: 2026-08-01
---
# 云台子系统

## 职责
驱动 PCA9685（地址 0x40，共用 I2C1_M4）上的 SG90 舵机，提供 pan/tilt 角度映射、限位、平滑，供手动 FPV 观察与后续视觉追踪的云台补偿。

## 关键实现 / 注意事项
- 目标通道：CH0=前 Pan、CH1=前 Tilt、CH2=前扫描舵机预留、CH3=后 Pan、CH4=后 Tilt。
- 当前单云台代码已切到前云台 CH0/1；CH2 与后云台 CH3/4 已在板级配置中预留，双云台状态模型仍由 `P4-01/P4-02` 实施。
- 40-pin PWM 已被电机/大灯占满，舵机一律走 PCA9685 I2C PWM。
- 大灯走 Pin33，不占 PCA9685 通道。
- `last_verified` 只表示软件映射已核对；PCA9685 与双云台仍未重接验收。
