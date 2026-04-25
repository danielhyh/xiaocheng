# 小橙 4WD 智能小车 — Phase 2.2

> 系统设计 v0.2 · FastAPI + WebSocket + Vue 控制面板

## 快速启动

### PC 开发 (Mock 模式)

```bash
# 后端
cd xiaocheng
pip install -r requirements.txt
XIAOCHENG_MOCK=1 uvicorn app.main:app --reload

# 前端 (另一个终端)
cd xiaocheng/frontend
npm install
npm run dev
```

打开 `http://localhost:5173`,摇杆和 HUD 已可交互。

### 开发板部署

```bash
# 需要预装 wiringpi
uvicorn app.main:app --host 0.0.0.0
```

### 运行测试

```bash
XIAOCHENG_MOCK=1 python -m pytest tests/ -v
```

## 目录结构

```
xiaocheng/
├── app/
│   ├── main.py              # FastAPI 入口,组装所有层
│   ├── config.py            # 板级常量 + USE_MOCK 开关
│   ├── api/
│   │   ├── http.py          # HTTP: /api/status, /api/config
│   │   ├── websocket.py     # WS: /ws/control (envelope 协议)
│   │   └── stream.py        # MJPEG: /stream/camera (Phase 3)
│   ├── business/
│   │   ├── dispatcher.py    # 指令分发 (type → handler)
│   │   ├── mode_manager.py  # 模式状态机 (manual/avoid/track/...)
│   │   ├── safety.py        # 安全看门狗 (断连自动停车)
│   │   └── telemetry.py     # 遥测推送 (tel.motion + tel.sensors)
│   ├── subsystems/
│   │   └── motion.py        # 运动子系统 (vx/vy → 差速驱动)
│   └── drivers/
│       └── motor/
│           ├── __init__.py   # Mock 开关 (自动选实现)
│           ├── protocol.py   # 驱动接口定义
│           ├── real.py       # 真实驱动 (sysfs PWM + GPIO)
│           └── mock.py       # Mock 驱动 (日志 + 状态)
├── frontend/
│   ├── src/
│   │   ├── App.vue           # 根组件 (横屏布局)
│   │   ├── main.ts           # Vue 入口
│   │   ├── components/
│   │   │   ├── TopBar.vue      # 连接状态 + 电量 + 模式
│   │   │   ├── CameraView.vue  # 摄像头占位 (Phase 3)
│   │   │   ├── MotionControl.vue # 虚拟摇杆 + 速度环 + HUD
│   │   │   └── FuncButtons.vue   # 功能按钮占位 (P6/P8/P9/P10)
│   │   ├── composables/
│   │   │   └── useWebSocket.ts # WS 连接 + 重连 + 消息路由
│   │   └── stores/
│   │       └── carStore.ts     # Pinia: 遥测缓存
│   └── package.json
├── tests/
│   └── test_motion.py        # 差速映射测试 (5 cases)
├── requirements.txt
└── README.md
```

## WebSocket 协议 (envelope)

```json
{ "type": "cmd.motion", "ts": 1744876800.123, "payload": { "vx": 0.5, "vy": 0.8 } }
```

详见系统设计文档 §4。

## 扩展新功能

以 Phase 6 云台为例,需要改的地方:

1. `config.py` — 加 I2C 地址、舵机行程常量
2. `drivers/servo/` — 新建 real.py + mock.py
3. `subsystems/gimbal.py` — 封装角度/限位/平滑
4. `business/dispatcher.py` — 注册 `cmd.gimbal` handler
5. `frontend/src/components/GimbalControl.vue` — 新组件

核心骨架 (API 层、envelope、WS 路由) 一行不改。

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
