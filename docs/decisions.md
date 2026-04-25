# 技术决策记录（Architecture Decision Records）

> 记录重大技术决策及其理由。AI 理解决策背景后，给出的建议才不会和设计哲学冲突。  
> 格式：[日期] 决策 | 背景 | 选择理由 | 放弃的方案

---

## ADR-001：计算平台选择 Orange Pi 5 Pro

**背景：** 项目需要一块能跑 Python/FastAPI、有 GPIO、能跑本地 NPU 推理的 SBC。

**选择理由：**
- RK3588S 自带 6TOPS NPU，Phase 5/13 的 YOLO 和本地 LLM 推理可以不依赖云端
- 40pin 扩展口丰富，能满足全部 14 个 Phase 的外设需求
- 社区活跃，wiringOP 工具链完善
- 已有 OPi 4 Pro 使用经验，迁移成本低

**放弃的方案：** Raspberry Pi 5（GPIO 够用但无 NPU，本地推理需外接加速棒）；Jetson Nano（成本更高，功耗更大）

---

## ADR-002：用 sysfs PWM 而不是 wiringOP-Python 的 pwmWrite

**背景：** 电机调速需要硬件 PWM，有两条路：wiringOP 的 `pwmWrite` API 或内核 sysfs PWM。

**选择理由：**
- sysfs 是内核标准接口，行为确定、跨 SoC 兼容
- wiringOP 的硬件 PWM 在某些 Allwinner 芯片上存在兼容性问题（OPi 4 Pro 上实测过坑）
- sysfs 方式代码透明，每一步写文件都可以单独调试，适合学习和排障
- 换板子只需修改 pwmchip 路径，其余代码不动

**放弃的方案：** `pigpio`（RK3588S 不支持）；wiringOP pwmWrite（有坑，可移植性差）

---

## ADR-003：后端框架选 FastAPI 而不是 Flask

**背景：** 需要同时支持 HTTP REST + WebSocket + MJPEG 流。

**选择理由：**
- FastAPI 原生支持 asyncio，WebSocket 和 MJPEG 流不需要额外插件
- 类型提示和自动 API 文档对项目维护有帮助
- 和 asyncio 生态（硬件 IO 的 run_in_executor、定时任务等）配合更自然

**放弃的方案：** Flask + flask-socketio（同步阻塞模型，高频 WS 消息性能差）；aiohttp（生态和工具链不如 FastAPI 成熟）

---

## ADR-004：WebSocket 使用统一 Envelope 而不是裸消息

**背景：** 随着功能增加，WS 消息类型会从 2 种增长到 20+。

**选择理由：**
- `{ "type": "cmd.motion", "ts": ..., "payload": {...} }` 结构让前端可以统一路由，不需要为每种消息写单独解析
- type 用点号分层（`cmd.*` / `tel.*` / `event.*`），含义清晰
- 新增功能只加新 type，协议层零改动，兼容旧客户端

**放弃的方案：** 不同 endpoint（如 `/ws/motion`、`/ws/telemetry`）——管理成本高，前端需要维护多个 WS 连接

---

## ADR-005：视频流用独立 MJPEG endpoint 而不是 WebSocket Binary

**背景：** Phase 3 需要把摄像头画面传到前端。

**选择理由：**
- 浏览器 `<img src="...">` 原生支持 MJPEG，零前端代码
- 视频帧（大量 binary 数据）和 JSON 控制指令共用一个 WS 连接会互相干扰
- MJPEG 独立连接，即使视频卡顿也不影响控制指令的实时性

**放弃的方案：** WS Binary 帧（干扰控制通道）；WebRTC（低延迟更好，但初期复杂度太高，Phase 3 先用 MJPEG 跑通，后续可替换）

---

## ADR-006：ADS1115 作为安全必选项（不是可选的遥测功能）

**背景：** LM2596S 降压模块需要约 7V 最低输入才能稳定输出 5V，而 OPi 工作需要稳定 5V。

**选择理由：**
- 电池从 8.4V 放电到 7V 时，LM2596S 输出开始不稳定 → OPi 可能无声断电
- 断电会导致 SD 卡文件系统损坏，数据丢失
- 没有电压监控时，用户无法感知电池快耗尽，因此电压监控是安全边界，不是仪表盘装饰
- 目标方案：低压告警阈值设 7.2V（安全余量），强制停车并推送 `event.alert`

**放弃的方案：** 不接 ADC，靠"感觉"判断电量——不可接受，存在硬件损坏风险

---

## ADR-007：静态 IP 通过 NetworkManager 配置

**背景：** 开发板需要固定 IP 才能稳定连接。

**选择理由：**
- OPi 5 Pro 的 Debian/Ubuntu 镜像使用 NetworkManager 管理网络
- 直接改 `/etc/network/interfaces` 会与 NetworkManager 冲突，导致网络异常

**方式：** `nmcli con mod "eth0" ipv4.addresses 192.168.x.x/24 ipv4.method manual`，或用 `nmtui` 图形界面配置。IP 应选在路由器 DHCP 分配范围之外，避免地址冲突。

---

## ADR-008：Mock 模式作为架构约束而非调试开关

**背景：** 硬件不总是在手边，但需要能持续开发和测试软件逻辑。

**选择理由：**
- 如果 Mock 只是 `if debug: print()` 这样的零星开关，架构会腐化——真实和 Mock 路径渐渐不同步，Mock 不再可信
- 把 Real/Mock 抽成同一个 Protocol 的两个实现，强制接口对齐，任何时候 Mock 都能真实反映 Real 的行为契约
- 前端开发、子系统单测、CI 跑测都不需要真板

**实现：** 已在电机驱动落地：`real.py` 和 `mock.py` 实现同一 Protocol，由 `config.USE_MOCK` 全局切换。后续 ADC/舵机/灯光沿用该模式。
