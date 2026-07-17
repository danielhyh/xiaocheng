---
title: 指令分发
scope: 把解析后的 cmd.* 指令分发到对应子系统
code: app/business/dispatcher.py
last_verified: 2026-06-25
---
# 指令分发

## 职责
注册各子系统 handler（`cmd.motion` / `cmd.light` / `cmd.audio` / `cmd.gimbal` 等），按 type 分发，并处理跨子系统联动（如刹车/倒车灯联动）。

## 关键实现 / 注意事项
- 子系统注册式，新增子系统只加 handler，不改路由核心。
- 联动逻辑（运动 → 灯光/音频）集中在此编排。
