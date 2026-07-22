# 小橙 4WD 智能小车

> Orange Pi 5 Pro · FastAPI + WebSocket + Vue 控制面板

## 当前项目口径

- 当前电池组：EVE 18650 **2S2P** + 2S 保护板。
- OV13855：前置 FPV/视觉主摄；OV5640 UVC：后置倒车/后视。
- ADS1115：采样电池总压，服务电量显示与 7.2V 低压安全边界。
- ESP32-C3 + AMS1117：Phase 15 带外电源管理，用于待机、远程开机和优雅断电；当前不接入。
- 当前正在用 Board-A/Board-B、KF301 和排针重做线束。以前接通过的模块在重接后重新验收前记为“待复验”。

信息源分工：实施顺序和当前阶段看 [`docs/roadmap.md`](docs/roadmap.md)；硬件角色、引脚和实物状态只看 [`docs/hardware-wiring.md`](docs/hardware-wiring.md)；软件模块状态看 [`docs/modules/`](docs/modules/)。

## 快速启动

> ⚠️ **所有 Python 命令必须在 `.venv` 虚拟环境中执行。**

### PC 开发 (Mock 模式)

```bash
# 激活虚拟环境
.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate   # Linux / macOS

# 后端
pip install -r requirements.txt
XIAOCHENG_MOCK=1 uvicorn app.main:app --reload

# 前端 (另一个终端)
cd xiaocheng/frontend
npm install
npm run dev
```

打开 `http://localhost:5173`，摇杆和 HUD 已可交互。

### 开发板部署

```bash
# 激活虚拟环境
source .venv/bin/activate

# 需要预装 wiringpi（从源码编译）
uvicorn app.main:app --host 0.0.0.0
```

### 运行测试

```bash
source .venv/bin/activate   # 或 Windows: .venv\Scripts\activate
XIAOCHENG_MOCK=1 python -m pytest tests/ -v
```

## 目录结构

```
xiaocheng/
├── app/
│   ├── main.py              # FastAPI 入口与生命周期组装
│   ├── config.py            # 当前软件常量（目标硬件接线以 hardware-wiring.md 为准）
│   ├── api/                 # HTTP / WebSocket / MJPEG
│   ├── business/            # dispatcher / safety / telemetry / mode
│   ├── subsystems/          # motion / sensing / vision / gimbal / lighting / audio / obstacle / nitro
│   └── drivers/             # motor / adc / camera / servo / led / strip / audio / ultrasonic
├── frontend/                # Vue 3 + CyberpunkPanel
├── tests/                   # 后端单元测试
├── docs/                    # 路线、架构、硬件、ADR、模块文档
├── requirements.txt
└── README.md
```

## WebSocket 协议 (envelope)

```json
{ "type": "cmd.motion", "ts": 1744876800.123, "payload": { "vx": 0.5, "vy": 0.8 } }
```

详见 [`docs/architecture.md`](docs/architecture.md) 的 WebSocket 协议章节。

## 扩展新功能

新硬件遵循 Real/Mock 驱动 → 子系统 → dispatcher/API → 前端的分层方式。完整约束见 [`docs/architecture.md`](docs/architecture.md)，不要从业务层直接操作 GPIO/I2C。

## 当前控制行为说明

### 运动指令持续发送

前端摇杆或 WASD/方向键被按住时，会每 100ms 通过 WebSocket 持续发送一次当前运动指令：

```json
{ "type": "cmd.motion", "ts": 1744876800.123, "payload": { "vx": 0.5, "vy": 0.8 } }
```

这样即使摇杆停在某个固定位置不动，后端安全看门狗也会持续收到控制消息，不会误判为心跳超时。松开摇杆或键盘时，前端会发送 `{ "vx": 0, "vy": 0 }` 让车辆停车。

### 刹车指令

右侧功能栏顶部的 `BRAKE` 按钮会发送：

```json
{ "type": "cmd.brake", "ts": 1744876800.123, "payload": {} }
```

后端收到后会立即调用 `MotionSubsystem.brake()`，清零运动状态，并调用电机驱动的 `brake()` 方法。Mock 模式下可以在后端日志中看到 `[MOCK] motors: BRAKE`。

刹车优先级高于普通运动指令。前端触发刹车时会先锁定当前拖拽/按键输入，直到用户松开后才允许重新控制；后端也会在刹车后的短保护窗口内忽略旧的非零 `cmd.motion`，避免排队中的运动指令覆盖刹车。
