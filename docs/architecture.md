---
title: 系统架构
scope: 六层架构、WebSocket 协议、Mock 模式、并发模型
decisions: [ADR-003, ADR-004, ADR-005, ADR-008]
---
# 小橙系统架构文档

> 对应系统设计 v0.1，随 Phase 演进持续精化。  
> 最后更新：Phase 2.2 完成，按当前代码同步

---

## 1. 六层架构

```
前端层   (Vue 3 / React Native)     ← 人机交互，无业务逻辑
  ↕
接口层   (FastAPI + WebSocket)       ← 协议契约，envelope 解析
  ↕
业务层   (Dispatcher / Mode / WD)    ← 编排、模式、安全
  ↕
子系统层 (motion / sensing / ...)    ← 领域语义，不感知 GPIO
  ↕
驱动层   (motor / adc / camera /...) ← 硬件封装，Real + Mock 双实现
  ↕
硬件层   (电机 / 传感器 / 摄像头/...)
```

**跨层调用原则：每层只依赖其直接下层，禁止跨层调用。**

---

## 2. 三条核心原则

**① 分层解耦，副作用下沉**  
硬件操作只出现在驱动层。上层单测不需要真板；换板子只换驱动实现，上层代码不动。

**② Mock 友好是一等公民**  
不是调试开关，是架构约束。每个驱动提供 `RealXxx` + `MockXxx` 两个实现，统一 `Protocol`，由 `config.USE_MOCK` 切换。前端在 PC 上可跑全链路。

**③ 消息 + 状态通信，不直接调用**  
子系统间走 WebSocket envelope + 共享状态，不互相 import。新增子系统 = 新增 type + 注册 dispatcher，核心不动。

---

## 3. 驱动层规范

每个驱动一个目录，结构固定：

```
drivers/
  motor/
    __init__.py   # 根据 USE_MOCK 选择实现
    real.py       # RealMotorDriver
    mock.py       # MockMotorDriver
  adc/            # ✅ ADS1115 over I2C (Phase 2.pre)
  camera/         # Phase 3
  servo/          # Phase 6
  led/            # Phase 8
  audio/          # Phase 9
```

Mock 实现要求：
- 接口与 Real 完全一致（同一 Protocol/ABC）
- 打印关键动作到 logger.info，肉眼可验证
- 产生合理的伪遥测数据，数值范围需贴近当前硬件电源方案
- 维护内部状态（current_speed、gimbal_angle 等），支持断言

---

## 4. 业务层关键组件

| 组件 | 职责 |
|---|---|
| `Dispatcher` | 解析 envelope type，路由到对应子系统方法 |
| `ModeManager` | 全局状态机（manual / avoid / track / nav / voice） |
| `SafetyWatchdog` | WS 断连/超时 500ms 停车；强制回 manual |
| `TelemetryPublisher` | 10Hz 推送 `tel.motion`；1Hz 推送 `tel.sensors`（真实电压 + CPU 温度） |
| `MockSwitch` | `config.USE_MOCK` 总开关 |

**模式切换规则：**
1. 前端 `cmd.mode` 显式触发 → 后端校验 → 广播 `event.mode_changed`
2. 安全降级：当前已支持 WS 断连/超时 → 强制回 `manual` + 停车；低压/传感器故障待接入
3. 手动优先：自动模式下收到 `cmd.motion` → 临时接管 3 秒（可配）

---

## 5. WebSocket 协议

### 5.1 统一 Envelope

```json
{
  "type": "cmd.motion",
  "id": "optional-uuid",
  "ts": 1744876800.123,
  "payload": {}
}
```

type 前缀规则：`cmd.*`（前端→后端）/ `tel.*`（后端→前端，遥测）/ `event.*`（双向，事件）

### 5.2 指令（前端 → 后端）

| type | payload | Phase |
|---|---|---|
| `cmd.motion` | `{ vx, vy, speed }` | P2 ✅ |
| `cmd.brake` | `{}` | P2 ✅ |
| `cmd.mode` | `{ mode: "manual"\|"avoid"\|"track"\|"nav"\|"voice" }` | P2 ✅（状态切换骨架） |
| `cmd.gimbal` | `{ pan, tilt }` | P6 |
| `cmd.light` | `{ headlight: 0-100, strip: "off"\|"ambient"\|... }` | P8 |
| `cmd.audio` | `{ action: "play"\|"tts", data: ... }` | P9 |
| `cmd.nitro` | `{}` | P10 |
| `cmd.nav` | `{ target: {x, y} }` | P14 |

**持续运动策略：** 摇杆拖拽中每 100ms 重发当前 vx/vy（安全看门狗依赖此保活）。

**刹车优先级：** `cmd.brake` 优先级高于 `cmd.motion`，后端保护窗口内忽略队列中的旧运动指令。

### 5.3 遥测（后端 → 前端）

| type | payload | 频率 | Phase |
|---|---|---|---|
| `tel.motion` | 方向、速度 | 10-30Hz | P2 ✅ |
| `tel.sensors` | 电池电压/电量/等级、CPU温度 | 1Hz | P2.pre ✅（ADS1115 真实电压 + sysfs CPU 温度） |
| `tel.ultrasonic` | 各方向距离 | 10Hz | P4 |
| `tel.detection` | YOLO bbox list | 帧率 | P5 |
| `tel.nav` | 位姿、路径 | 按需 | P14 |

### 5.4 事件

| type | 语义 |
|---|---|
| `event.alert` | 告警：急停 / 低压 / 避障触发 / 超温 |
| `event.ack` | 关键指令确认（mode切换、nitro等） |
| `event.mode_changed` | 模式切换广播（含原因） |

---

## 6. 接口层传输通道

| 通道 | 方向 | 用途 |
|---|---|---|
| HTTP `GET/POST` | 请求/响应 | 配置、状态查询（低频） |
| WebSocket `/ws/control` | 双向 | 指令 + 遥测（高频） |
| MJPEG `/stream/camera` | 单向 | 当前 503 占位；P3 接入摄像头 |
| Static | 单向 | Vue dist 生产部署 |

视频流独立于 WS 原因：避免 binary 帧干扰 JSON 指令；浏览器 `<img src>` 原生支持 MJPEG。

---

## 7. 后端并发模型

| 任务类型 | 实现方式 |
|---|---|
| HTTP + WS + 业务逻辑 | 主进程 asyncio |
| 硬件 I/O（I2C read/write） | `run_in_executor`（线程池） |
| 遥测采集 | `asyncio.create_task` 定时任务 |
| 摄像头采集（P3） | 独立线程 + 无锁环形队列 |
| YOLO 推理（P5） | 独立进程（NPU 阻塞调用），`multiprocessing.Queue` |
| LIDAR（P14） | 独立线程读串口，SLAM 独立进程 |

**原则：阻塞的扔进程，短同步扔线程池，其他走 asyncio。**

---

## 8. Mock 模式

```python
# config.py
USE_MOCK = os.getenv("XIAOCHENG_MOCK", "0") == "1"

# drivers/motor/__init__.py
if USE_MOCK:
    from .mock import MockMotorDriver as MotorDriver
else:
    from .real import RealMotorDriver as MotorDriver
```

```bash
# PC 端开发
XIAOCHENG_MOCK=1 uvicorn app.main:app --reload

# 开发板生产
uvicorn app.main:app --host 0.0.0.0
```

---

## 9. 目录结构

```
xiaocheng/
├── CLAUDE.md
├── docs/
│   ├── architecture.md      ← 本文件
│   ├── hardware-wiring.md   ← 硬件清单总览 + 接线
│   ├── decisions.md
│   ├── known-issues.md
│   ├── roadmap.md
│   └── modules/
├── archive/                 ← 归档历史知识库（已移出 docs/）
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── http.py
│   │   ├── websocket.py
│   │   └── stream.py
│   ├── business/
│   │   ├── dispatcher.py
│   │   ├── mode_manager.py
│   │   ├── safety.py
│   │   └── telemetry.py
│   ├── subsystems/
│   │   ├── motion.py        ✅
│   │   ├── sensing.py       ✅ (ADS1115 电压 + CPU 温度)
│   │   ├── vision.py        (P3)
│   │   ├── gimbal.py        (P6)
│   │   ├── lighting.py      (P8)
│   │   ├── audio.py         (P9)
│   │   ├── voice.py         (P13)
│   │   └── navigation.py    (P14)
│   └── drivers/
│       ├── motor/           ✅ real.py + mock.py
│       ├── adc/             ✅ real.py + mock.py (ADS1115)
│       ├── camera/          (P3)
│       ├── ultrasonic/      (P4)
│       ├── servo/           (P6)
│       ├── led/             (P8)
│       └── audio/           (P9)
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── TopBar.vue
│       │   ├── CameraView.vue
│       │   ├── MotionControl.vue
│       │   ├── TelemetryDashboard.vue
│       │   └── ...
│       ├── composables/
│       │   └── useWebSocket.ts
│       └── stores/
└── tests/
    ├── test_motion.py       ← 运动映射测试
    └── test_dispatcher.py   ← 刹车分发与保护窗口测试
```

---

## 10. 新增子系统 Checklist

以 P6 云台为例，需改动点：

1. `hardware-wiring.md` 补充 PCA9685 I2C 地址和舵机接线
2. `config.py` 新增 I2C 地址、舵机行程常量
3. `drivers/servo/real.py` + `mock.py`
4. `subsystems/gimbal.py` 封装角度/限位/平滑
5. `business/dispatcher.py` 注册 `cmd.gimbal`
6. `business/telemetry.py` 注册 `tel.gimbal`（如需显示角度）
7. 前端 `GimbalControl.vue` 替换占位区

**核心骨架（API 层、envelope、ModeManager、WS 路由）一行不改。**
