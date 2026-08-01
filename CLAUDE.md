# 小橙（XiaoCheng）— 智能四驱轮式机器人

> Orange Pi 5 Pro (RK3588S) 驱动的四轮小车，支持 Web 远程控制、FPV 画面、NPU 视觉推理。

---

## 一句话定位

手机 → Vue 控制面板 → WebSocket → FastAPI → GPIO → 电机。可扩展至视觉追踪、语音控制、SLAM 导航。

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 硬件 | Orange Pi 5 Pro（RK3588S，6 TOPS NPU）+ 四驱底盘；清单、接线与当前装配见 [hardware-wiring.md](docs/hardware-wiring.md) |
| 固件/驱动 | Python 3，sysfs PWM，wiringOP-Python（已编译） |
| 后端 | FastAPI + uvicorn，WebSocket，asyncio |
| 前端 | Vue 3 + TypeScript + Pinia + Vite |
| 视觉（规划） | OpenCV，YOLOv8n，RKNN（NPU 推理） |
| OS | Ubuntu on TF 卡（64GB A2 级），静态 IP via NetworkManager |

---

## 核心模块

> 此表只描述代码能力；当前实物是否接通及本轮验收状态以 `docs/hardware-wiring.md` 和 `docs/roadmap.md` 为准。

| 模块/文件 | 职责 | 代码状态 |
|---|---|---|
| `app/drivers/motor/` | sysfs PWM + GPIO 电机驱动，含 Real/Mock 双实现 | ✅ 已实现；实物待重接验收 |
| `app/subsystems/motion.py` | 前后左右差速，业务语义层 | ✅ 已实现；实物待重接验收 |
| `app/api/websocket.py` | WS envelope 解析 + 路由 | ✅ P2.2 完成 |
| `app/business/dispatcher.py` | 指令分发到子系统 | ✅ P2.2 完成 |
| `app/business/safety.py` | Watchdog：WS 断连/超时 500ms 停车 | ✅ P2.2 完成 |
| `app/business/telemetry.py` | `tel.motion` + `tel.sensors` 推送（真实电压 + CPU 温度） | 🚧 已实现；低压闭环待验收 |
| `app/drivers/adc/` | ADS1115 I2C ADC 电池电压读取，含 Real/Mock | ✅ 已实现；实物待重接验收 |
| `app/subsystems/sensing.py` | 传感器汇总（真实电压/电量/CPU温度） | 🚧 已实现；低压闭环待验收 |
| `frontend/` | Vue 控制面板：虚拟摇杆、WASD、刹车、电量/状态 HUD | ✅ P2.2 完成 |
| `app/drivers/audio/` | USB 声卡驱动（aplay/ffplay/edge-tts/amixer），含 Real/Mock | ✅ 已实现；实物待重接验收 |
| `app/subsystems/audio.py` | 音效播放、TTS、鸣笛循环、倒车提示、低压告警 | ✅ 已实现；实物待重接验收 |
| `frontend/src/components/AudioPanel.vue` | 音量滑块 + TTS 输入框 | ✅ P9 完成 |

---

## 当前阶段

> 📌 **当前阶段信息统一在 `docs/roadmap.md` 维护，此处不再重复。** 请查阅 roadmap 底部的「当前阶段」章节。

---

## 文档索引

| 文档 | 内容 |
|---|---|
| `docs/roadmap.md` | 阶段状态、任务依赖、可并行工作与当前主线（**唯一维护点**） |
| `docs/architecture.md` | 稳定分层边界、传输通道、Mock 与并发约束 |
| `docs/hardware-wiring.md` | 实物清单、电源拓扑、引脚和板上连接的唯一来源 |
| `docs/decisions.md` | 技术决策（ADR）与已知问题/workaround（ISS）的唯一来源 |
| `docs/modules/` | 模块级概要，按需查阅 |
| `archive/` | 归档的历史资料 |

> 本项目不再维护 `docs/known-issues.md`；新问题以 `ISS-xx` 追加到 `docs/decisions.md`。

---

## 快速上手

> ⚠️ **所有 Python 命令必须在 `.venv` 虚拟环境中执行。**

```bash
# 进入虚拟环境（Windows PowerShell）
.venv\Scripts\activate

# 进入虚拟环境（Linux / Orange Pi）
source .venv/bin/activate
```

```bash
# 开发板（真实模式，先激活 venv）
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# PC 端（Mock 模式，无需硬件）
XIAOCHENG_MOCK=1 uvicorn app.main:app --reload

# 前端开发
cd frontend && npm run dev
```

后端测试：

```bash
XIAOCHENG_MOCK=1 python -m pytest tests/ -v
```

Windows PowerShell 常用命令：

```powershell
$env:XIAOCHENG_MOCK="1"; python -m uvicorn app.main:app --reload
deactivate
```

---

## 关键约束 / 注意事项

- **wiringOP-Python 必须从源码编译**，不能 pip 安装：`github.com/orangepi-xunlong/wiringOP`（next 分支）
- **LM2596S 最低输入 ~7V** 才能稳定输出 5V，电池低于该电压会导致 OPi 无声断电 → ADS1115 电压监控是**安全必选项**，不是可选功能
- **静态 IP 通过 NetworkManager** 配置（`nmcli`/`nmtui`），不要直接改 `/etc/network/interfaces`
- **PWM 极性**：RK3588S 上 `PWM_INVERTED = True`（已在 motor.py 实测确认）
- **I2C 总线选择**：ADS1115 挂 I2C1_M4（物理脚 3/5），已确认与电机引脚无冲突

---

## 小橙网络代理

> 小橙（Orange Pi）访问 GitHub / PyPI 需要走本地代理，否则超时。

**代理地址：`192.168.0.103:7897`（HTTP/HTTPS）**

在小橙上执行任何需要联网的命令前，先设置代理环境变量：

```bash
export http_proxy=http://192.168.0.103:7897
export https_proxy=http://192.168.0.103:7897
```

或者一行前缀写法（临时生效）：

```bash
https_proxy=http://192.168.0.103:7897 http_proxy=http://192.168.0.103:7897 git pull
```

**git 拉取代码：**

```bash
cd /root/xiaocheng
export http_proxy=http://192.168.0.103:7897
export https_proxy=http://192.168.0.103:7897
git pull
```

**pip 安装依赖：**

```bash
source .venv/bin/activate
pip install -r requirements.txt \
  --index-url https://pypi.org/simple \
  -i https://mirrors.aliyun.com/pypi/simple/   # 可选：换国内镜像加速
# 或直接走代理
https_proxy=http://192.168.0.103:7897 pip install -r requirements.txt
```

> ⚠️ 代理仅在局域网内有效，确保运行代理的 PC（192.168.0.103）与小橙在同一网段且代理软件已开启「允许局域网连接」。
