---
title: 工程决策与问题记录
scope: 长期技术取舍（ADR）和可复用问题/Workaround（ISS）的唯一来源
---
# 工程决策与问题记录

> `ADR-xxx` 记录长期技术取舍，`ISS-xx` 记录仍可能复现的问题与处理方式。
> 模块行为看代码，阶段进度看 [roadmap.md](roadmap.md)，物理连接看
> [hardware-wiring.md](hardware-wiring.md)。

---

## 技术决策（ADR）

### ADR-001：计算平台选择 Orange Pi 5 Pro

**决定：** 主控使用 Orange Pi 5 Pro（RK3588S）。

**理由：** 一块板同时提供 Linux/Python、40-pin GPIO 和 6TOPS NPU，覆盖控制与本地视觉推理。

**代价：** 板级驱动和工具链不如 Raspberry Pi 通用，需要维护 RK3588S 专用配置。

---

### ADR-002：用 sysfs PWM 而不是 wiringOP-Python 的 pwmWrite

**决定：** 电机硬件 PWM 通过 Linux sysfs 控制；wiringOP-Python 只负责普通 GPIO。

**理由：** sysfs 行为可观察、可单步排查，并已在 RK3588S 真板验证；`pwmWrite` 和 `pigpio` 不可靠或不支持该平台。

**代价：** pwmchip 路径和 overlay 属于板级配置，换 SoC 时必须重新确认。

---

### ADR-003：后端框架选 FastAPI 而不是 Flask

**决定：** 后端使用 FastAPI + asyncio。

**理由：** 同一应用可承载 HTTP、WebSocket、MJPEG 和后台任务，且类型提示适合维护协议边界。

**代价：** 阻塞硬件调用必须主动隔离，生命周期和任务取消也需要显式管理。

---

### ADR-004：WebSocket 使用统一 Envelope 而不是裸消息

**决定：** WebSocket 使用 `{type, id?, ts?, payload}` envelope；type 命名空间固定为 `cmd.*`、`tel.*`、`event.*`。

**理由：** 单连接即可统一路由指令、遥测和事件，新增消息不需要新增 endpoint。

**代价：** 前后端必须共同维护 payload 契约，并处理未知 type 和版本兼容。

---

### ADR-005：视频流用独立 MJPEG endpoint 而不是 WebSocket Binary

**决定：** 视频使用独立 MJPEG HTTP endpoint，不进入控制 WebSocket。

**理由：** 浏览器可直接显示，且视频拥塞不会阻塞 JSON 控制指令。

**代价：** MJPEG 带宽和延迟高于现代视频协议；远程控制阶段可再评估 WebRTC。

---

### ADR-006：ADS1115 作为安全必选项（不是可选的遥测功能）

**决定：** ADS1115 电池电压监控属于安全边界，不能作为可选遥测移除。

**理由：** 电池接近 LM2596S 最低输入时 OPi 可能无声断电并损坏文件系统，必须提前告警和停车。

**代价：** 分压倍率和安全阈值需要真板校准；未完成联锁前不能把电量显示视为完整保护。

---

### ADR-007：静态 IP 通过 NetworkManager 配置

**决定：** 静态 IP 只通过 NetworkManager（`nmcli`/`nmtui`）配置。

**理由：** 系统镜像由 NetworkManager 管理网络，直接修改 `/etc/network/interfaces` 会产生冲突。

**代价：** 网络配置保存在设备系统中而非仓库，重装系统后需要重新配置。

---

### ADR-008：Mock 模式作为架构约束而非调试开关

**决定：** 每个硬件驱动提供同一 Protocol 下的 Real/Mock 双实现，由 `config.USE_MOCK` 统一选择。

**理由：** PC 开发、前端联调和自动化测试必须经过与真板相同的上层路径。

**代价：** 每次接口变化都要同步维护两套实现，Mock 也必须模拟合理状态而不只是打印日志。

---

### ADR-009：大灯使用自带驱动，Pin 33 只提供 PWM 信号

**决定：** 两颗大灯使用其自带恒流/开关驱动，正负极接电源与共地，SIG 并联接 Pin 33；不再使用 PCA9685、IRF520 或外置 MOS 模块驱动大灯功率回路。

**理由：** 实物已经提供 3.3V 逻辑/PWM 输入；额外功率级没有收益，而 IRF520 在 3.3V 栅压下尤其不安全。

**代价：** 两颗大灯共用一路亮度控制；现有 PCA9685 大灯代码必须在真板接线前同步到 Pin 33 方案。

---

### ADR-010：ESP32-C3 定位为带外电源管理控制器，单独立项

**决定：** ESP32-C3 只承担 OPi 的带外电源管理，并作为独立阶段实施，不兼任当前外设协处理器。

**理由：** ESP32 可在 OPi 完全断电时低功耗待命，并控制高边开关；职责类似简化的 BMC。

**硬约束：** 必须先通知 OPi 正常关机并等待回告，之后才能切断电源。现有 Pin 16/18、AMS1117 焊位和 KF301 接入点只做预留。

**代价：** 增加常供电源、UART 协议和高边开关；即时唤醒与 deep-sleep 功耗之间仍需取舍。

---

## 问题与 Workaround（ISS）

> 只保留可能再次踩到、仍需处理或已被其他文档引用的问题。状态取值：
> `open` / `workaround` / `fixed`。

### ISS-01 PWM 极性反转导致速度控制反向

RK3588S 实测 PWM 极性与默认预期相反；驱动固定设置 `PWM_INVERTED = True`（`polarity = inversed`）。

**状态**：fixed

### ISS-02 ENB 跳线帽导致 PWM 失效

L298N 的 ENA/ENB 跳线帽会把使能脚固定到 5V，接 PWM 前必须拔掉，否则电机始终全速。

**状态**：fixed

### ISS-03 pwmchip 路径从 OPi 4 Pro 迁移到 5 Pro 需修改

OPi 5 Pro 使用 PWM13_M2 → `pwmchip2`、PWM14_M2 → `pwmchip3`；不能沿用其他 SoC 的 sysfs 路径。

**状态**：fixed

### ISS-04 HC-SR04 Echo 电平取决于实物版本

本项目的 RCWL-9200 宽压版使用 3.3V 供电，Echo 可直连；若更换为 5V 老款，必须增加分压或电平转换，不能直接接 OPi。

**状态**：fixed

### ISS-05 LM2596S 低压死区仍缺完整联锁

ADS1115 采集和电量分级已经存在，但真板校准、低压自动停车与安全关机尚未形成完整闭环；闭环完成前仍可能在约 7V 附近无声掉电。

**状态**：open

### ISS-06 前端持续运动指令在网络抖动时可能误触发停车

运动指令约每 100ms 重发，而 Watchdog 500ms 超时；Wi-Fi 抖动可能触发非预期停车。需通过真车网络测试决定增大阈值还是拆分独立心跳，不能凭感觉放宽安全边界。

**状态**：open

### ISS-07 多客户端并发控制策略未定

当前仅按局域网单控制者使用。多个客户端不仅会让 `cmd.motion` 互相覆盖：遥测发送回调与运行状态也是全局单实例，一个连接可能覆盖另一个，任一断开还会停止全局遥测。跨网开放前必须改为每连接独立生命周期，并实现控制者租约或其他明确仲裁策略。

**状态**：open

### ISS-08 wiringOP-Python 无法通过 pip 安装

PyPI 上的 `wiringpi` 不支持 OPi 5 Pro；必须使用 Orange Pi 官方 `wiringOP` 仓库的 `next` 分支并从源码编译 Python 绑定。

**状态**：workaround

### ISS-09 从旧 TF 卡克隆到新卡遗留问题多

克隆旧 TF 卡会携带网络、驱动和 wiringOP 历史配置；迁移时重新烧录系统并按项目步骤配置。

**状态**：fixed

### ISS-10 UVC 摄像头在部分 USB 2.0 口枚举失败

部分 USB 2.0 口会报 `device descriptor read/64, error -62` 且不生成视频设备；改接蓝色 USB 3.0 Host 口后可稳定以 480 Mbps UVC 枚举。

**状态**：workaround

### ISS-11 Real 模式会无条件初始化未接外设

`main.py` 当前会初始化并启动灯光、云台、超声波等计划外设；实物未接或仍使用旧引脚时，可能启动失败或误操作冲突 GPIO。完成 `HW-01`、`HW-02` 前，真板运行必须显式避开未验收外设。

**状态**：open

### ISS-12 自主模式缺少统一控制权仲裁

当前 dispatcher 没有统一管理 manual、avoid、track、voice、nav 的所有权、抢占和模式切换；后续能力若各自直接写入 motion，可能相互覆盖或绕开安全停车。完成 roadmap 的 `CTRL-01`、`CTRL-02` 前，只允许单一人工控制链实际驱动车体。

**状态**：open
