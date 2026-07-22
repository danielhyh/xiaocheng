---
title: 传感器子系统
scope: 传感器汇总——电池电压/电量百分比/等级 + CPU 温度
code: app/subsystems/sensing.py
last_verified: 2026-06-25
decisions: [ADR-006]
---
# 传感器子系统

## 职责
聚合 ADC 电压读数与 CPU 温度，输出电量百分比/等级，供 telemetry 推送与低压告警判断。

## 关键实现 / 注意事项
- 目标低压安全边界为 7.2V；当前 `config.py` 仍保留 6.8V/6.2V 旧常量，必须在板端复验前统一（见 ISS-05）。
- CPU 温度读自 sysfs thermal zone。
- `last_verified` 是重接线前的软件/真板记录，不表示当前 ADS1115 已完成 KF301 复接。
