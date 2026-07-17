# 知识库 Part 4 — WebSocket + Vue 3 + 软件架构 + 信号滤波 + 差速算法 + 安全系统

---

## 15. WebSocket 实时通信

### 15.1 WebSocket vs HTTP

| 特性 | HTTP | WebSocket |
|---|---|---|
| 连接模式 | 请求-响应，每次新连接 | 持久连接，全双工 |
| 延迟 | 每次请求有握手开销 | 建立后几乎零开销 |
| 服务端推送 | 不支持（需轮询） | 原生支持 |
| 适用场景 | 低频查询、文件传输 | 实时控制、遥测推送 |

小橙的控制指令需要 100ms 级别的实时性，遥测需要服务端主动推送，WebSocket 是唯一合理选择。

### 15.2 WebSocket 握手

WebSocket 基于 HTTP 升级协议：

```
客户端 → 服务端:
GET /ws/control HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==

服务端 → 客户端:
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

握手完成后，连接升级为 WebSocket，双方可以随时发送消息。

### 15.3 Envelope 协议设计

本项目所有 WS 消息使用统一的 Envelope 格式：

```json
{
  "type": "cmd.motion",
  "id": "optional-uuid-for-ack",
  "ts": 1744876800.123,
  "payload": {
    "vx": 0.5,
    "vy": 0.8
  }
}
```

**type 前缀规则：**
- `cmd.*`：前端 → 后端，控制指令
- `tel.*`：后端 → 前端，遥测数据
- `event.*`：双向，事件通知

**为什么用 Envelope：** 随着功能增加，消息类型从 2 种增长到 20+。统一格式让前端可以用一个 switch 路由所有消息，新增功能只加新 type，协议层零改动。

### 15.4 FastAPI WebSocket 实现

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/control")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    safety.touch()

    # 启动遥测推送
    telemetry.set_send_fn(websocket.send_json)
    tel_task = asyncio.create_task(telemetry.run())

    try:
        while True:
            data = await websocket.receive_json()
            safety.touch()  # 喂狗

            result = await dispatcher.dispatch(data)
            if result:
                await websocket.send_json(result)

    except WebSocketDisconnect:
        safety.on_disconnect()
    finally:
        tel_task.cancel()
        telemetry.set_send_fn(None)
```

### 15.5 前端 WebSocket（Vue）

```typescript
// composables/useWebSocket.ts
const ws = new WebSocket('ws://192.168.0.x:8000/ws/control')

ws.onopen = () => { connected.value = true }
ws.onclose = () => { connected.value = false }

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data)
  switch (msg.type) {
    case 'tel.motion':
      carStore.updateMotion(msg.payload)
      break
    case 'tel.sensors':
      carStore.updateSensors(msg.payload)
      break
    case 'event.pong':
      // 计算 WS 延迟
      latency.value = Date.now() - pingTime
      break
  }
}

// 发送指令
function send(type: string, payload: object) {
  ws.send(JSON.stringify({ type, ts: Date.now() / 1000, payload }))
}
```

### 15.6 持续运动策略

摇杆拖拽时，前端每 100ms 重发当前 vx/vy：

```typescript
// 摇杆移动时
onJoystickMove(vx: number, vy: number) {
  this.currentVx = vx
  this.currentVy = vy
}

// 定时器每 100ms 发送
setInterval(() => {
  if (connected.value) {
    send('cmd.motion', { vx: currentVx, vy: currentVy })
  }
}, 100)
```

**为什么需要重发：** 安全看门狗超时 500ms 停车。如果只在摇杆变化时发送，摇杆静止时 500ms 后会误停车。持续重发既保活看门狗，又让后端始终知道最新摇杆位置。

### 15.7 WS 延迟测量（ping/pong）

```typescript
// 前端每 5 秒发一次 ping
setInterval(() => {
  pingTime = Date.now()
  send('cmd.ping', {})
}, 5000)

// 收到 pong 时计算延迟
case 'event.pong':
  wsLatency.value = Date.now() - pingTime
  break
```

后端立即回复：
```python
def _handle_ping(self, payload: dict) -> dict:
    return {
        "type": "event.pong",
        "ts": time.time(),
        "payload": {},
    }
```

---

## 16. Vue 3 前端框架

### 16.1 Vue 3 核心概念

**Composition API（组合式 API）：** Vue 3 的主要编程模型，用 `setup()` 函数或 `<script setup>` 语法组织逻辑。

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const count = ref(0)           // 响应式基本类型
const doubled = computed(() => count.value * 2)  // 计算属性

onMounted(() => {
  console.log('组件挂载完成')
})
</script>

<template>
  <button @click="count++">{{ count }} (doubled: {{ doubled }})</button>
</template>
```

### 16.2 Pinia 状态管理

Pinia 是 Vue 3 官方推荐的状态管理库，替代 Vuex。

```typescript
// stores/carStore.ts
import { defineStore } from 'pinia'

export const useCarStore = defineStore('car', {
  state: () => ({
    connected: false,
    battery: { voltage: 0, percent: 0, level: 'unknown' },
    motion: { vx: 0, vy: 0, speed: 0, direction: 'idle' },
    sensors: { cpu_temp: 0, wifi_rssi: null },
  }),

  actions: {
    updateMotion(payload: any) {
      this.motion = { ...this.motion, ...payload }
    },
    updateSensors(payload: any) {
      this.sensors = { ...this.sensors, ...payload }
      if (payload.voltage) this.battery.voltage = payload.voltage
    },
  },
})
```

**在组件中使用：**
```vue
<script setup>
import { useCarStore } from '@/stores/carStore'
const store = useCarStore()
</script>

<template>
  <div>电量: {{ store.battery.percent }}%</div>
</template>
```

### 16.3 虚拟摇杆实现

虚拟摇杆通过 touch/mouse 事件计算偏移量，映射到 vx/vy：

```typescript
function onTouchMove(event: TouchEvent) {
  const touch = event.touches[0]
  const rect = joystickEl.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2

  let dx = touch.clientX - centerX
  let dy = touch.clientY - centerY

  // 限制在圆形范围内
  const maxRadius = rect.width / 2
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist > maxRadius) {
    dx = dx / dist * maxRadius
    dy = dy / dist * maxRadius
  }

  // 归一化到 [-1, 1]
  vx.value = dx / maxRadius
  vy.value = -dy / maxRadius  // Y 轴反转（屏幕向下为正，但前进为正）
}
```

### 16.4 Vite 构建工具

Vite 是现代前端构建工具，开发时用原生 ES Module，构建时用 Rollup。

**开发代理配置（`vite.config.ts`）：**
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/ws': {
        target: 'ws://192.168.0.x:8000',
        ws: true,
      },
      '/stream': {
        target: 'http://192.168.0.x:8000',
      },
      '/api': {
        target: 'http://192.168.0.x:8000',
      },
    },
  },
})
```

开发时前端跑在 localhost:5173，通过代理转发到 OPi 后端，避免 CORS 问题。

---

## 17. 软件架构设计模式

### 17.1 六层架构

```
前端层   (Vue 3)              ← 人机交互，无业务逻辑
  ↕  WebSocket / HTTP / MJPEG
接口层   (FastAPI)             ← 协议解析，envelope 路由
  ↕  Python 函数调用
业务层   (Dispatcher/Safety)   ← 编排、安全、遥测
  ↕  Python 函数调用
子系统层 (motion/lighting/...) ← 领域语义，不感知 GPIO
  ↕  Protocol 接口
驱动层   (motor/adc/camera/...) ← 硬件封装，Real+Mock 双实现
  ↕  sysfs/I2C/SPI/USB
硬件层   (电机/传感器/摄像头/...)
```

**核心原则：每层只依赖其直接下层，禁止跨层调用。**

### 17.2 Protocol 模式（接口隔离）

每个驱动定义一个 Protocol（Python 的结构化子类型），Real 和 Mock 都实现同一接口：

```python
# drivers/motor/protocol.py
from typing import Protocol

class MotorDriverProtocol(Protocol):
    def init(self) -> None: ...
    def set_motors(self, left: float, right: float) -> None: ...
    def stop(self) -> None: ...
    def brake(self) -> None: ...
    def cleanup(self) -> None: ...
    @property
    def current_state(self) -> dict: ...
```

```python
# drivers/motor/__init__.py
from app import config

if config.USE_MOCK:
    from .mock import MockMotorDriver as MotorDriver
else:
    from .real import RealMotorDriver as MotorDriver

__all__ = ["MotorDriver"]
```

**好处：**
- 子系统层只依赖 Protocol，不关心是 Real 还是 Mock
- 换硬件只改驱动层，上层代码不动
- Mock 实现强制与 Real 保持接口一致

### 17.3 Dispatcher 模式（命令路由）

Dispatcher 是一个命令路由表，将 WS 消息 type 映射到处理函数：

```python
self._handlers = {
    "cmd.motion":   self._handle_motion,
    "cmd.brake":    self._handle_brake,
    "cmd.gimbal":   self._handle_gimbal,
    "cmd.light":    self._handle_light,
    "cmd.audio":    self._handle_audio,
    "cmd.nitro":    self._handle_nitro,
    "cmd.obstacle": self._handle_obstacle,
}

async def dispatch(self, message: dict):
    handler = self._handlers.get(message["type"])
    if handler:
        return await handler(message["payload"])
```

**新增功能只需：** 写新 handler → 注册到 `_handlers` → 完成。核心 dispatch 逻辑不动。

### 17.4 观察者模式（回调注入）

子系统间的事件通知用回调函数，避免直接依赖：

```python
# obstacle 子系统不直接调用 safety，而是通过回调
class ObstacleSubsystem:
    def set_callbacks(self, on_front_blocked=None, on_rear_blocked=None):
        self._on_front_blocked = on_front_blocked
        self._on_rear_blocked = on_rear_blocked

    def _check_distance(self, distance):
        if distance < STOP_DISTANCE:
            if self._on_front_blocked:
                self._on_front_blocked()  # 调用注入的回调

# main.py 中注入
safety.set_obstacle(obstacle)  # safety 内部注册回调
```

**好处：** obstacle 不需要 import safety，两者解耦。

### 17.5 依赖注入（构造函数注入）

子系统的外部依赖通过构造函数或 setter 注入，而不是在内部创建：

```python
# 好的做法：依赖从外部注入
class NitroSubsystem:
    def set_dependencies(self, motion=None, lighting=None, audio=None):
        self._motion = motion
        self._lighting = lighting
        self._audio = audio

# main.py 中组装
nitro.set_dependencies(motion=motion, lighting=lighting, audio=audio)
```

**好处：** 测试时可以注入 Mock 对象，不需要真实硬件。

---

## 18. 信号滤波与数据平滑

### 18.1 为什么需要滤波

传感器读数包含噪声：
- ADC 量化噪声（最低有效位抖动）
- 电源纹波干扰
- 电磁干扰（电机 PWM 对 I2C 的干扰）

直接显示原始数据会导致数值跳动，影响用户体验和决策准确性。

### 18.2 EMA（指数移动平均）

EMA 是最简单高效的实时滤波算法：

```python
class EMAFilter:
    def __init__(self, alpha: float, init_value: float = 0.0):
        self.alpha = alpha      # 平滑系数，0 < alpha < 1
        self.value = init_value

    def update(self, new_sample: float) -> float:
        self.value = self.alpha * new_sample + (1 - self.alpha) * self.value
        return self.value
```

**alpha 选择指南：**

| alpha | 特性 | 适用场景 |
|---|---|---|
| 0.01 | 极平滑，响应慢（~100 次收敛） | 电池电压（变化极慢） |
| 0.1 | 较平滑，响应中等（~10 次收敛） | 温度、距离 |
| 0.5 | 轻微平滑，响应快（~3 次收敛） | 需要快速响应的信号 |

**EMA vs 移动平均（SMA）：**
- SMA 需要存储 N 个历史值，内存占用随窗口大小增加
- EMA 只需存储一个值，内存 O(1)
- EMA 对近期数据权重更高，响应更自然

### 18.3 变化速率限制（Rate Limiting）

防止数值突变（噪声尖峰或传感器故障）：

```python
def rate_limited_update(current: float, target: float,
                        max_rate: float, dt: float) -> float:
    """
    current: 当前值
    target:  目标值
    max_rate: 每秒最大变化量
    dt:      时间步长（秒）
    """
    max_delta = max_rate * dt
    delta = target - current
    delta = max(-max_delta, min(max_delta, delta))
    return current + delta
```

本项目电量百分比：下降最快 2%/s，上升最快 0.5%/s。

### 18.4 超声波测距滤波

HC-SR04 偶尔会返回异常值（0 或极大值）：

```python
def measure_filtered(self, direction: str) -> float | None:
    readings = []
    for _ in range(3):  # 取 3 次读数
        d = self._raw_measure(direction)
        if d is not None and 2 < d < 400:  # 有效范围 2-400cm
            readings.append(d)
        time.sleep(0.01)

    if not readings:
        return None
    return sorted(readings)[len(readings) // 2]  # 取中位数
```

中位数滤波对异常值（outlier）有很好的抑制效果。

---

## 19. 差速转向算法

### 19.1 差速驱动原理

四轮小车（实际上是两驱差速，前后轮同侧联动）通过左右轮速度差实现转向：

- 左右同速 → 直线行驶
- 左快右慢 → 右转
- 左慢右快 → 左转
- 左前右后 → 原地右旋
- 左后右前 → 原地左旋

### 19.2 Arcade Drive 算法

本项目使用 Arcade Drive（街机驾驶）算法，将摇杆的 vx/vy 映射到左右轮速：

```python
def handle_command(self, vx: float, vy: float) -> None:
    # vx: -1(左) ~ +1(右)，控制转向
    # vy: -1(后) ~ +1(前)，控制前后

    left  = vy + vx   # 左轮 = 前后 + 转向
    right = vy - vx   # 右轮 = 前后 - 转向

    # 等比缩放，保持转向比，防止超出 [-1, 1]
    max_val = max(abs(left), abs(right), 1.0)
    left  /= max_val
    right /= max_val

    self._driver.set_motors(left * 100, right * 100)
```

**直觉验证：**

| vx | vy | left | right | 效果 |
|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 全速前进 |
| 0 | -1 | -1 | -1 | 全速后退 |
| 1 | 0 | 1 | -1 | 原地右旋 |
| -1 | 0 | -1 | 1 | 原地左旋 |
| 0.5 | 0.5 | 1.0 | 0.0 | 右弧线前进（缩放后） |
| 1 | 1 | 1.0 | 0.0 | 右弧线前进（缩放后，max=2） |

### 19.3 等比缩放的必要性

不缩放时，`vx=1, vy=1` 会得到 `left=2, right=0`，超出电机范围。

简单截断（`left = min(left, 1.0)`）会破坏转向比：
- 截断前：left=2, right=0，比值 2:0
- 截断后：left=1, right=0，比值 1:0（相同，OK）
- 但 `vx=0.5, vy=1` → left=1.5, right=0.5，截断后 left=1, right=0.5，比值从 3:1 变成 2:1

等比缩放保持比值：
```python
max_val = max(abs(left), abs(right), 1.0)  # 找最大绝对值
left /= max_val   # 等比缩放
right /= max_val
```

### 19.4 氮气加速的速度叠加

氮气激活时，vx/vy 乘以加速倍率，但需要重新钳位到 [-1, 1]：

```python
if self._nitro and self._nitro.is_active:
    boost = self._nitro.boost_factor  # 1.3
    vx = max(-1.0, min(1.0, vx * boost))
    vy = max(-1.0, min(1.0, vy * boost))
```

**效果：** 原来 vy=0.77 的速度，乘以 1.3 后 = 1.0（钳位），达到最大速度。对于已经接近最大速度的指令，氮气效果更明显。

---

## 20. 安全系统设计

### 20.1 安全层次

小橙的安全系统分三层：

```
第一层: 硬件安全
  - 18650 保护板（过充/过放/过流）
  - LM2596S 欠压保护

第二层: 软件安全（SafetyWatchdog）
  - WS 断连/超时自动停车
  - 前方障碍物自动停车
  - 后方障碍物倒车刹停
  - 低电压告警

第三层: 用户界面安全
  - 刹车按钮优先级最高
  - 断连时 UI 显示离线状态
  - 电量 HUD 实时显示
```

### 20.2 看门狗（Watchdog）原理

看门狗是一种超时检测机制：定期"喂狗"（重置计时器），如果超时未喂狗，触发安全动作。

```python
class SafetyWatchdog:
    def touch(self):
        """喂狗：收到任何 WS 消息时调用"""
        self._last_heartbeat = time.time()
        self._has_connection = True

    async def run(self):
        while self._running:
            if self._has_connection:
                elapsed = time.time() - self._last_heartbeat
                if elapsed > WS_DISCONNECT_TIMEOUT:  # 500ms
                    self._motion.stop()
                    self._has_connection = False
            await asyncio.sleep(0.1)  # 100ms 轮询
```

**超时阈值选择：** 500ms。前端每 100ms 发一次运动指令，正常情况下看门狗每 100ms 被喂一次。500ms 超时 = 允许连续 5 次丢包，足够应对短暂网络抖动，又不会让失控小车跑太远。

### 20.3 刹车优先级与保护窗口

刹车指令优先级高于运动指令。刹车后有 300ms 保护窗口，期间忽略运动指令：

```python
BRAKE_SUPPRESS_SECONDS = 0.3

def _handle_brake(self, payload):
    self._brake_until = time.monotonic() + BRAKE_SUPPRESS_SECONDS
    self._motion.brake()

def _handle_motion(self, payload):
    if time.monotonic() < self._brake_until and (vx != 0 or vy != 0):
        logger.debug("忽略刹车保护窗口内的运动指令")
        return
    # 正常处理运动指令
```

**为什么需要保护窗口：** 前端发送刹车时，队列中可能已有运动指令在途。没有保护窗口，刹车后立即被运动指令覆盖，刹车无效。

### 20.4 避障安全联锁

避障是硬联锁（不可绕过），在 dispatcher 层实现：

```python
def _handle_motion(self, payload):
    # 前方避障：阻止前进
    if self._obstacle and self._obstacle.front_blocked and vy > 0:
        vy = 0  # 强制清零前进分量，但允许转向

    # 后方避障：阻止倒车
    if self._obstacle and self._obstacle.rear_blocked and vy < 0:
        vy = 0  # 强制清零后退分量
```

**设计细节：** 只清零 vy（前后），保留 vx（转向）。前方有障碍时，用户仍可以原地转向，找到出路。

### 20.5 低电压告警流程

```
SensingSubsystem 读取电压
    ↓
voltage < BATTERY_LOW (6.8V)
    ↓
推送 event.alert 到前端（TopBar 显示红色警告）
    ↓
AudioSubsystem.start_low_voltage_alert()
    ↓
每 10 秒循环播放 "电量不足，请及时充电"
    ↓
voltage < BATTERY_CRITICAL (6.2V)
    ↓
强制停车 + 持续告警
```

**告警阈值设计：**
- `BATTERY_LOW = 6.8V`：开始告警，仍可行驶
- `BATTERY_CRITICAL = 6.2V`：强制停车，防止 LM2596S 欠压导致 OPi 断电

### 20.6 断连安全回调链

WS 断连时，SafetyWatchdog 触发一系列安全动作：

```python
def on_disconnect(self):
    self._motion.stop()          # 停车
    self._mode.force_manual()    # 强制回手动模式
    self._audio.stop_horn_and_reverse()  # 停止鸣笛和倒车提示
    self._lighting.stop_all()    # 停止动态灯效（大灯保持）
    self._gimbal.stop_all()      # 停止云台移动
    self._nitro.stop_all()       # 停止氮气加速
```

**大灯为什么不关：** 断连时小车可能在黑暗环境中，关大灯会让用户找不到小车。安全考虑优先于节能。
