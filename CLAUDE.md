# 小橙（XiaoCheng）— 智能四驱轮式机器人

> Orange Pi 5 Pro (RK3588S) 驱动的四轮小车，支持 Web 远程控制、FPV 画面、NPU 视觉推理。

---

## 一句话定位

手机 → Vue 控制面板 → WebSocket → FastAPI → GPIO → 电机。可扩展至视觉追踪、语音控制、SLAM 导航。

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 硬件 | Orange Pi 5 Pro (RK3588S 8核 6TOPS NPU)，L298N 电机驱动，EVE 18650 2S1P 7.4V,18650锂电池3A过充保护模块, LM2596S, HC-SR04超声波模块, ZY-ADS1115, 舵机SG90+云台, IIR520驱动模块, 5v3wLED灯珠*2, PCA9685A, 500万像素OV5640摄像头, 小喇叭扬声器8Ω2w, USB转音频免驱, 可编程RGB灯带 |
| 固件/驱动 | Python 3，sysfs PWM，wiringOP-Python（已编译） |
| 后端 | FastAPI + uvicorn，WebSocket，asyncio |
| 前端 | Vue 3 + TypeScript + Pinia + Vite |
| 视觉（规划） | OpenCV，YOLOv8n，RKNN（NPU 推理） |
| OS | Ubuntu on TF 卡（64GB A2 级），静态 IP via NetworkManager |

---

## 核心模块

| 模块/文件 | 职责 | 状态 |
|---|---|---|
| `app/drivers/motor/` | sysfs PWM + GPIO 电机驱动，含 Real/Mock 双实现 | ✅ P2.1 完成 |
| `app/subsystems/motion.py` | 前后左右差速，业务语义层 | ✅ P2.1 完成 |
| `app/api/websocket.py` | WS envelope 解析 + 路由 | ✅ P2.2 完成 |
| `app/business/dispatcher.py` | 指令分发到子系统 | ✅ P2.2 完成 |
| `app/business/safety.py` | Watchdog：WS 断连/超时 500ms 停车 | ✅ P2.2 完成 |
| `app/business/telemetry.py` | `tel.motion` + `tel.sensors` 推送（真实电压 + CPU 温度） | ✅ P2.pre 完成 |
| `app/drivers/adc/` | ADS1115 I2C ADC 电池电压读取，含 Real/Mock | ✅ P2.pre 完成 |
| `app/subsystems/sensing.py` | 传感器汇总（真实电压/电量/CPU温度） | ✅ P2.pre 完成 |
| `frontend/` | Vue 控制面板：虚拟摇杆、WASD、刹车、电量/状态 HUD | ✅ P2.2 完成 |

---

## 当前阶段

**Phase 2.pre 已完成（电源验收 + ADS1115 电压监控）**

1. ☑ LM2596S 降压模块接线并调至 5.0V
2. ☑ ADS1115 接 I2C1_M4（物理脚 3/5），20KΩ+10KΩ 分压（÷3），I2C 通信正常
3. ☑ ADS1115 驱动（Real/Mock）与 sensing 子系统落地，接入真实电压遥测
4. ☐ 全链路端对端测试（手机→Vue→WS→FastAPI→GPIO→电机 + 真实电压显示）
5. ☐ 万用表校准分压比（当前理论值 3.0，可能需微调）

**下一阶段：Phase 3 — FPV 摄像头（OV5640 + OpenCV + MJPEG 流）**

---

## 文档索引

| 文档 | 内容 |
|---|---|
| `docs/architecture.md` | 六层架构、WebSocket 协议、Mock 模式、并发模型 |
| `docs/hardware-wiring.md` | 引脚映射、接线图、电源拓扑、已踩坑 |
| `docs/decisions.md` | 重大技术决策及理由（ADR） |
| `docs/known-issues.md` | 已知问题与 workaround |
| `docs/changelog.md` | 每日进展（最近 4 周） |
| `docs/archive/` | 归档的历史 changelog |

---

## 快速上手

```bash
# 开发板（真实模式）
cd ~/xiaocheng
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

---

## 关键约束 / 注意事项

- **wiringOP-Python 必须从源码编译**，不能 pip 安装：`github.com/orangepi-xunlong/wiringOP`（next 分支）
- **LM2596S 最低输入 ~7V** 才能稳定输出 5V，电池低于该电压会导致 OPi 无声断电 → ADS1115 电压监控是**安全必选项**，不是可选功能
- **静态 IP 通过 NetworkManager** 配置（`nmcli`/`nmtui`），不要直接改 `/etc/network/interfaces`
- **PWM 极性**：RK3588S 上 `PWM_INVERTED = True`（已在 motor.py 实测确认）
- **I2C 总线选择**：ADS1115 挂 I2C1_M4（物理脚 3/5），已确认与电机引脚无冲突
