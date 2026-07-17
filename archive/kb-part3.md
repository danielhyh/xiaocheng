# 知识库 Part 3 — 摄像头/视频流 + 音频系统 + asyncio + FastAPI

---

## 11. 摄像头与视频流

### 11.1 OV5640 摄像头

OV5640 是一款 500 万像素 CMOS 图像传感器，通过 USB UVC 协议连接到 OPi。

**UVC (USB Video Class)：** Linux 内核原生支持的 USB 摄像头标准，无需额外驱动，插上即用，设备文件为 `/dev/video0`（或 video1、video2 等）。

**关键参数：**
- 分辨率：最高 2592×1944，本项目用 1280×720
- 帧率：720P 下约 12-30fps（取决于光线和 USB 带宽）
- 格式：MJPG（硬件压缩 JPEG）或 YUYV（原始 YUV）

### 11.2 OpenCV 采集

```python
import cv2

cap = cv2.VideoCapture(0)  # 打开 /dev/video0
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

# 使用 MJPG 格式（硬件压缩，大幅降低 CPU 占用）
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

ret, frame = cap.read()  # frame 是 numpy array (H, W, 3) BGR
```

**MJPG vs YUYV：**
- YUYV：原始 YUV 格式，每帧 720P = 1280×720×2 ≈ 1.8MB，USB 带宽压力大，CPU 需要解码
- MJPG：摄像头内部 JPEG 压缩，每帧约 50-200KB，USB 带宽小，CPU 只需解压

本项目用 MJPG，实测 CPU 占用从 ~40% 降到 ~5%。

### 11.3 MJPEG 流媒体

MJPEG (Motion JPEG) 是最简单的视频流格式：连续发送 JPEG 图片，用 HTTP multipart 协议分隔。

**HTTP multipart 格式：**
```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame

--frame
Content-Type: image/jpeg
Content-Length: 12345

[JPEG 二进制数据]
--frame
Content-Type: image/jpeg
...
```

浏览器的 `<img src="...">` 原生支持这种格式，会持续更新显示最新帧。

**FastAPI 实现：**
```python
from fastapi.responses import StreamingResponse

async def generate():
    while True:
        frame = vision.get_latest_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n'
                   + frame + b'\r\n')
        await asyncio.sleep(1/30)  # 30fps

@router.get("/stream/camera")
async def camera_stream():
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
```

### 11.4 采集线程架构

摄像头采集是阻塞操作（`cap.read()` 会等待下一帧），不能在 asyncio 主循环中直接调用。

**解决方案：** 独立线程 + 共享帧缓冲

```python
import threading

class VisionSubsystem:
    def __init__(self):
        self._frame = None          # 最新帧（JPEG bytes）
        self._lock = threading.Lock()
        self._thread = None
        self._running = False

    def _capture_loop(self):
        cap = cv2.VideoCapture(0)
        while self._running:
            ret, frame = cap.read()
            if ret:
                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                with self._lock:
                    self._frame = jpeg.tobytes()

    def get_latest_frame(self):
        with self._lock:
            return self._frame
```

**为什么用线程而不是 asyncio：** `cap.read()` 是同步阻塞调用，无法 await。用 `run_in_executor` 也可以，但独立线程更简洁，且摄像头采集是持续高频操作，线程更合适。

### 11.5 延迟分析

```
摄像头曝光 → USB 传输 → OpenCV 解码 → JPEG 编码 → HTTP 发送 → 浏览器解码 → 显示
   ~33ms       ~5ms        ~2ms          ~5ms         ~网络          ~5ms
```

局域网总延迟约 50-100ms，对 FPV 遥控可接受（专业 FPV 要求 <50ms，需要 WebRTC）。

---

## 12. 音频系统

### 12.1 USB 声卡 (Jieli UACDemoV1.0)

USB 免驱声卡通过 USB Audio Class (UAC) 协议工作，Linux 内核原生支持。

**查看声卡：**
```bash
aplay -l
# card 3: UACDemoV10 [UACDemoV1.0], device 0: USB Audio [USB Audio]
```

**关键参数：**
- 卡号：3（`AUDIO_CARD = 3`）
- 采样率：48000Hz
- 格式：S16LE（16-bit 小端有符号整数）

### 12.2 aplay 播放 WAV

```bash
aplay -D hw:3,0 audio.wav
# -D hw:3,0 指定声卡 3 设备 0
```

Python 中用 subprocess 调用：
```python
import subprocess
proc = subprocess.Popen(
    ["aplay", "-D", f"hw:{AUDIO_CARD},0", filepath],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
await asyncio.get_event_loop().run_in_executor(None, proc.wait)
```

### 12.3 ffplay 播放 MP3

aplay 只支持 WAV，MP3 需要 ffplay（FFmpeg 的播放器）：

```bash
ffplay -nodisp -autoexit -loglevel quiet \
       -af "volume=2.0" \
       -i audio.mp3
```

`-nodisp`：不显示视频窗口  
`-autoexit`：播放完自动退出  
`-af "volume=2.0"`：音量放大 2 倍

### 12.4 edge-tts 文字转语音

edge-tts 是微软 Edge 浏览器 TTS 引擎的 Python 客户端，免费，中文效果好。

```python
import edge_tts
import asyncio

async def tts(text: str, output_file: str):
    communicate = edge_tts.Communicate(
        text,
        voice="zh-CN-YunxiNeural"  # 中文男声
    )
    await communicate.save(output_file)

# 生成后用 ffplay 播放
```

**可用中文声音：**
- `zh-CN-YunxiNeural`：男声（本项目默认）
- `zh-CN-XiaoxiaoNeural`：女声
- `zh-CN-YunjianNeural`：男声（更成熟）

### 12.5 amixer 音量控制

amixer 是 ALSA 的命令行混音器：

```bash
# 查看控件
amixer -c 3 controls

# 设置音量（通过 numid）
amixer -c 3 cset numid=4 80%

# 查询当前音量
amixer -c 3 cget numid=4
```

Python 中：
```python
def set_volume(level: int):  # level: 0-100
    raw = int(level / 100 * AUDIO_VOLUME_MAX)  # 映射到 0-147
    subprocess.run(
        ["amixer", "-c", str(AUDIO_CARD), "cset", f"numid={AUDIO_VOLUME_NUMID}", str(raw)],
        capture_output=True
    )
```

### 12.6 多通道音频管理

本项目同时可能有多个音频来源（鸣笛、倒车提示、TTS、告警），需要管理优先级：

| 通道 | 用途 | 优先级 |
|---|---|---|
| horn | 鸣笛（按住循环） | 最高，压制其他 |
| tts | 文字转语音 | 高，暂停倒车提示 |
| alert | 低电量告警 | 中 |
| reverse | 倒车提示音 | 低，可被其他打断 |
| sfx | 普通音效 | 最低 |

**实现方式：** 每个通道独立 subprocess，需要打断时 `proc.kill()`。

---

## 13. Python asyncio 异步编程

### 13.1 为什么需要异步

小橙后端需要同时处理：
- WebSocket 消息（高频，每 100ms 一条）
- 遥测推送（10Hz motion + 1Hz sensors）
- 摄像头流（30fps）
- 安全看门狗（100ms 轮询）
- 避障扫描（100ms 轮询）

如果用同步代码，这些任务会互相阻塞。asyncio 让单线程可以并发处理多个 I/O 任务。

### 13.2 事件循环与协程

```python
import asyncio

# 协程函数（用 async def 定义）
async def say_hello():
    print("Hello")
    await asyncio.sleep(1)  # 让出控制权，不阻塞事件循环
    print("World")

# 运行
asyncio.run(say_hello())
```

**关键概念：**
- **事件循环 (Event Loop)**：单线程调度器，轮流执行各协程
- **协程 (Coroutine)**：可暂停/恢复的函数，`await` 处暂停
- **Task**：包装协程，让事件循环调度它
- **await**：暂停当前协程，让事件循环运行其他任务

### 13.3 并发执行多个任务

```python
# 方式 1: create_task（立即调度，不等待）
task = asyncio.create_task(some_coroutine())

# 方式 2: gather（等待所有完成）
results = await asyncio.gather(
    coroutine_a(),
    coroutine_b(),
    coroutine_c(),
)

# 方式 3: 后台任务（fire and forget）
asyncio.create_task(background_loop())
```

本项目的遥测推送：
```python
async def run(self):
    self._running = True
    await asyncio.gather(
        self._publish_motion(),   # 10Hz
        self._publish_sensors(),  # 1Hz
    )
```

### 13.4 阻塞操作的处理

asyncio 是单线程的，任何阻塞调用都会卡住整个事件循环。

**规则：** 阻塞操作必须放到线程池执行：

```python
loop = asyncio.get_event_loop()

# I2C 读取（阻塞）
result = await loop.run_in_executor(None, blocking_i2c_read)

# 超声波测距（阻塞，需要等待 echo）
distance = await loop.run_in_executor(None, driver.measure, "front")
```

`run_in_executor(None, func, *args)` 将 `func(*args)` 放到默认线程池执行，返回 awaitable。

### 13.5 asyncio 与 FastAPI 的集成

FastAPI 基于 asyncio，路由处理函数可以是协程：

```python
@app.websocket("/ws/control")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()  # 等待消息，不阻塞
        result = await dispatcher.dispatch(data)
        if result:
            await websocket.send_json(result)
```

**lifespan 中启动后台任务：**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    safety_task = asyncio.create_task(safety.run())
    yield
    # 关闭
    safety_task.cancel()
```

### 13.6 asyncio 常见陷阱

**陷阱 1：忘记 await**
```python
# 错误：协程对象没有被执行
result = some_coroutine()  # 只创建了协程对象

# 正确
result = await some_coroutine()
```

**陷阱 2：在协程中调用阻塞函数**
```python
# 错误：time.sleep 阻塞整个事件循环
async def bad():
    time.sleep(1)

# 正确
async def good():
    await asyncio.sleep(1)
```

**陷阱 3：Task 异常被吞掉**
```python
# create_task 的异常不会自动传播
task = asyncio.create_task(risky_coroutine())
# 如果 risky_coroutine 抛异常，会被静默忽略

# 解决：添加异常回调
task.add_done_callback(lambda t: t.exception() and logger.error(t.exception()))
```

---

## 14. FastAPI Web 框架

### 14.1 FastAPI 基础

FastAPI 是基于 Starlette 和 Pydantic 的现代 Python Web 框架，原生支持 asyncio。

**核心特性：**
- 自动生成 OpenAPI 文档（访问 `/docs`）
- 类型提示驱动的请求/响应验证
- 原生 WebSocket 支持
- 与 asyncio 生态无缝集成

### 14.2 路由注册

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter(prefix="/api")

@router.get("/status")
async def get_status():
    return {"status": "ok"}

app.include_router(router)
```

本项目将路由分散到三个模块：
- `api/http.py`：HTTP REST 接口（状态查询、配置）
- `api/websocket.py`：WebSocket 控制通道
- `api/stream.py`：MJPEG 视频流

### 14.3 lifespan 生命周期管理

FastAPI 的 lifespan 替代了旧的 `startup`/`shutdown` 事件：

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段：初始化所有子系统
    motion.init()
    sensing.init()
    safety_task = asyncio.create_task(safety.run())

    yield  # 应用运行中

    # 关闭阶段：清理资源
    safety_task.cancel()
    motion.cleanup()

app = FastAPI(lifespan=lifespan)
```

**为什么用 lifespan：** 确保资源在应用退出时正确释放（GPIO 复位、PWM 关闭等），避免下次启动时硬件状态异常。

### 14.4 CORS 中间件

开发时前端（localhost:5173）和后端（localhost:8000）端口不同，浏览器会拒绝跨域请求。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境应限制为具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 14.5 静态文件服务

生产部署时，Vue 构建产物可以由 FastAPI 直接服务：

```python
from fastapi.staticfiles import StaticFiles

# 挂载到根路径，html=True 表示 SPA 模式（所有路径返回 index.html）
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

**注意：** 静态文件挂载必须在所有路由注册之后，否则会拦截 API 请求。

### 14.6 依赖注入模式

本项目用简单的模块级全局变量 + `init()` 函数注入依赖，而不是 FastAPI 的 `Depends()`：

```python
# api/websocket.py
_dispatcher: Dispatcher = None
_safety: SafetyWatchdog = None

def init(dispatcher, safety, telemetry):
    global _dispatcher, _safety, _telemetry
    _dispatcher = dispatcher
    _safety = safety
    _telemetry = telemetry
```

这种方式更简单，适合单实例应用。FastAPI 的 `Depends()` 更适合需要请求级别作用域的场景（如数据库连接）。
