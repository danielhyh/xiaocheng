---
title: 电机驱动
scope: sysfs PWM + GPIO 电机驱动，三层抽象（PWMChannel / Motor / Car），含 Real/Mock 双实现
code: app/drivers/motor/
last_verified: 2026-06-25
decisions: [ADR-002, ADR-008]
---
# 电机驱动

## 职责
封装 L298N + sysfs PWM，向上提供 Car 级语义（前后/转向/刹车），向下管理 PWM 通道与方向 GPIO。Real/Mock 同 Protocol，由 `config.USE_MOCK` 切换。

## 关键实现 / 注意事项
- **PWM 极性反转**：RK3588S 上 `PWM_INVERTED = True`（已实测，见 ISS-01）。
- **pwmchip 路径**：PWM13_M2 → pwmchip2，PWM14_M2 → pwmchip3（见 ISS-03）。
- **死区校准**：低占空比电机不转，需补偿起转死区。
- 接 PWM 前必须拔掉 L298N 的 ENA/ENB 跳线帽（见 ISS-02）。
- `last_verified` 是旧线束的真板结论；KF301 重接后须按前进/后退/左转/右转/刹车重新验收，未复验前实物状态为 ♻️。
