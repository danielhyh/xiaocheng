---
title: 系统架构
scope: 分层边界、依赖组装、传输通道、并发模型、Mock 约束
decisions: [ADR-003, ADR-004, ADR-005, ADR-008]
---
# 小橙系统架构文档

> 本文只记录不应随单个功能频繁变化的架构约束。阶段进度见
> [roadmap.md](roadmap.md)，硬件连接见 [hardware-wiring.md](hardware-wiring.md)，
> 具体取舍及代价见 [decisions.md](decisions.md)。

---

## 1. 六层架构

```
前端层   (Vue 3 / React Native)     ← 人机交互
  ↕
接口层   (FastAPI + WebSocket)      ← 传输、协议边界
  ↕
业务层   (Dispatcher / Mode / WD)   ← 指令编排、模式、安全
  ↕
子系统层 (motion / sensing / ...)   ← 领域语义，不感知板级细节
  ↕
驱动层   (motor / adc / camera/...) ← 硬件封装，Real + Mock 双实现
  ↕
硬件层   (电机 / 传感器 / 摄像头 / ...)
```

依赖默认由上向下。`app/main.py` 是组合根，可以感知所有后端层并负责创建、注入、启动和清理组件；其他模块不得绕过子系统直接操作硬件。视频流等专用 API可以接收子系统门面，但不能自行创建驱动。

---

## 2. 核心原则

**① 分层解耦，副作用下沉**  
硬件操作只出现在驱动层。上层单测不需要真板；换板子只换驱动实现，上层代码不动。

**② Mock 友好是一等公民**  
不是调试开关，是架构约束。每个驱动提供 `RealXxx` + `MockXxx` 两个实现，统一 `Protocol`，由 `config.USE_MOCK` 切换。前端在 PC 上可跑全链路。

**③ 边界协议与内部调用分开**
WebSocket envelope 只用于前后端边界。后端内部由 `main.py` 注入依赖，通过明确的方法调用、状态读取或回调协作，不把内部调用伪装成网络消息。

**④ 安全约束集中管理**
断连、心跳超时、障碍物联锁等跨子系统安全行为集中在 `SafetyWatchdog` 与`Dispatcher`，驱动不自行决定业务降级策略。

---

## 3. 驱动层规范

硬件驱动以独立目录组织，统一暴露不带 Real/Mock 差异的入口：

```
drivers/
  motor/
    __init__.py   # 根据 USE_MOCK 选择实现
    real.py       # RealMotorDriver
    mock.py       # MockMotorDriver
  camera/
    __init__.py
    protocol.py
    real.py
    mock.py
```

Mock 实现要求：
- 接口与 Real 完全一致（同一 Protocol/ABC）
- 不访问真实硬件资源
- 产生合理的伪状态或遥测数据
- 维护可供测试断言的内部状态

板级引脚、地址和阈值集中在 `app/config.py`，不散落到业务或前端代码中。

---

## 4. 组装与协作

| 组件 | 职责 |
|---|---|
| `app/main.py` | 组合根；创建组件、注入依赖、管理生命周期 |
| `Dispatcher` | 将外部指令路由到子系统，并承载跨子系统联动 |
| `ModeManager` | 管理全局运行模式 |
| `SafetyWatchdog` | 处理断连、心跳超时和安全降级 |
| `TelemetryPublisher` | 汇总子系统状态并经 WebSocket 发布 |

依赖通过构造函数或显式 setter 注入。生命周期遵循“组合根初始化、后台任务启动、
逆序清理”的方式；不要在模块 import 时隐式启动硬件或线程。

---

## 5. 协议边界

### 5.1 统一 Envelope

```json
{
  "type": "cmd.motion",
  "id": "optional-uuid",
  "ts": 1744876800.123,
  "payload": {}
}
```

type 前缀固定为：

- `cmd.*`：前端发往后端的指令
- `tel.*`：后端发往前端的周期状态
- `event.*`：确认、告警及其他事件

本文不复制完整 type 与 payload 清单。当前可接收指令以`app/business/dispatcher.py` 的 handler 注册表为准，当前遥测以
`app/business/telemetry.py` 为准；协议取舍见 ADR-004。

---

## 6. 接口层传输通道

| 通道 | 方向 | 用途 |
|---|---|---|
| HTTP `GET/POST` | 请求/响应 | 配置、状态查询（低频） |
| WebSocket `/ws/control` | 双向 | 指令 + 遥测（高频） |
| MJPEG `/stream/camera` | 单向 | 后置摄像头倒车影像；前端左上角 `ReversePiP` 显示 |
| Static | 单向 | Vue 构建产物的生产部署 |

视频流独立于 WS 原因：避免 binary 帧干扰 JSON 指令；浏览器 `<img src>` 原生支持 MJPEG。

---

## 7. 并发与阻塞边界

| 任务类型 | 实现方式 |
|---|---|
| HTTP + WS + 业务逻辑 | 主进程 asyncio |
| 安全看门狗、遥测、异步音频任务 | `asyncio` 后台任务 |
| 摄像头持续采集与 JPEG 编码 | 独立线程，锁保护最新帧 |
| MJPEG 等待新帧 | executor 等待，避免阻塞事件循环 |
| 后续长时间硬件或 NPU 计算 | 在线程或进程中隔离，按共享状态与故障边界选择 |

任何可能长时间阻塞的调用都不得直接运行在 FastAPI 事件循环中。

---

## 8. Mock 模式

`XIAOCHENG_MOCK=1` 是整条后端链路的硬件替身开关。上层始终从驱动包入口导入统一名称，由入口选择 Real 或 Mock 实现；业务层不得自行判断运行平台。Mock 模式用于 PC 端开发、接口联调与自动化测试。真实模式用于 Orange Pi，二者必须经过相同的子系统、业务和 API 路径，避免形成只在 Mock 中存在的第二套逻辑。
