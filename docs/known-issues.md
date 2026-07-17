---
title: 已知问题与 Workaround
scope: 踩过的坑与绕过方案，优先喂给 AI 避免重复踩坑
---
# 已知问题与 Workaround

> 随时追加。每条一个 ISS 编号，`**状态**` 取值 open / workaround / fixed，看板按状态分组。

---

## ISS-01 PWM 极性反转导致速度控制反向
**现象**：占空比越高电机速度反而越慢，占空比为 0 时全速转。
**根因**：RK3588S sysfs PWM 的 polarity 默认行为与预期相反。
**Workaround**：`motor.py` 中设 `PWM_INVERTED = True`，即写入 `polarity = inversed`。
**状态**：fixed

## ISS-02 ENB 跳线帽导致 PWM 失效
**现象**：连接 PWM 信号后电机始终全速，速度控制无效。
**根因**：L298N 出厂 ENA/ENB 跳线帽短接到 5V（固定使能），覆盖了外部 PWM 信号。
**Workaround**：接 PWM 前必须先拔掉 ENA/ENB 跳线帽。
**状态**：fixed

## ISS-03 pwmchip 路径从 OPi 4 Pro 迁移到 5 Pro 需修改
**现象**：迁移到 OPi 5 Pro 后 PWM 初始化失败，找不到 sysfs 路径。
**根因**：不同 SoC 的 pwmchip 编号不同（4 Pro Allwinner ≠ 5 Pro RK3588S）。
**Workaround**：5 Pro 上确认 PWM13_M2 → `/sys/class/pwm/pwmchip2`，PWM14_M2 → `/sys/class/pwm/pwmchip3`。
**状态**：fixed

## ISS-04 HC-SR04 Echo 5V 电平可能损坏 3.3V GPIO
**现象**：HC-SR04 Echo 输出 5V 电平，直接连 OPi 3.3V GPIO 有损坏 IO 口风险（尚未接线）。
**Workaround**：Phase 6 接线时加 2KΩ + 1KΩ 分压（5V → 3.3V），或用双向电平转换模块。
**状态**：open

## ISS-05 LM2596S 低压死区（监控待落地）
**现象**：电池电压低于约 7V 时 LM2596S 无法维持稳定 5V，OPi 可能无声断电，SD 卡文件系统可能损坏。
**Workaround**：ADS1115 电压监控 + 低压告警（阈值 7.2V），在危险区前强制停车并通知用户。驱动与 sensing 已落地（Phase 2.pre），告警联动与真板校准待完成。
**状态**：open

## ISS-06 前端持续运动指令在网络抖动时可能误触发停车
**现象**：摇杆固定时前端每 100ms 发一次 `cmd.motion`，WiFi 短暂抖动（>500ms）会让安全 Watchdog 误判断连并停车。
**根因**：Watchdog 超时阈值（500ms）与发送间隔（100ms）之间余量不足。
**Workaround**：候选——增大 Watchdog 超时至 1000ms；或心跳与运动指令分离的保活机制。尚未系统测试。
**状态**：open

## ISS-07 多客户端并发控制策略未定
**现象**：两个手机同时连接控制面板时，两者的 `cmd.motion` 都会执行，导致指令冲突。
**Workaround**：Phase 2.2 暂不处理，局域网单用户使用。Phase 11 前需确定策略：last-write-wins / 单控制者锁 / 仅允许局域网连接。
**状态**：open

## ISS-08 wiringOP-Python 无法通过 pip 安装
**现象**：`pip install wiringpi` 安装的是旧版，不支持 OPi 5 Pro。
**Workaround**：必须从源码编译——
```bash
git clone https://github.com/orangepi-xunlong/wiringOP.git -b next
cd wiringOP && sudo ./build
cd python && sudo python3 setup.py install
```
**状态**：fixed

## ISS-09 从旧 TF 卡克隆到新卡遗留问题多
**现象**：克隆方式迁移后系统遗留旧配置、wiringOP 版本等问题，排查困难。
**Workaround**：换 TF 卡时重新烧录新 OS 镜像，从零配置，比克隆省时间。
**状态**：fixed
