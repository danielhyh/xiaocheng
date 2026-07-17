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
- 电量等级映射 + 低压阈值 7.2V（告警联动待落地，见 ISS-05）。
- CPU 温度读自 sysfs thermal zone。
