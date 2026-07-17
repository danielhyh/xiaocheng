---
title: 运动子系统
scope: 前后左右差速的业务语义层，不感知 GPIO
code: app/subsystems/motion.py
last_verified: 2026-06-25
decisions: [ADR-008]
---
# 运动子系统

## 职责
把控制指令（vx/vy 或方向语义）翻译成左右轮差速，调用 motor 驱动层。运动状态变化联动灯光（刹车/倒车）与音频（倒车提示）。

## 关键实现 / 注意事项
- 业务语义层，只调用 motor 子系统接口，不直接碰 GPIO。
- 倒车判定 `vy < -0.1` 自动触发倒车提示音与倒车灯。
