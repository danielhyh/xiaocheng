# 开发阶段路线图

> 项目整体规划与进度追踪。各 Phase 详细变更记录见 `changelog.md`。  
> 状态标记：✅ 已完成 | 🚧 进行中 | 📋 待开始

---

## 基础阶段

**Phase 1 —— 硬件组装 + GPIO 基础** ✅  
系统烧录、wiringOP 验证、PWM 通道启用（pwm13-m2 / pwm14-m2）、引脚规划。

**Phase 2.1 —— 电机控制模块** ✅  
三层抽象（PWMChannel / Motor / Car）、PWM 极性反转（`PWM_INVERTED = True`）、死区校准、前后转向全动作验证。

**Phase 2.2 —— FastAPI + WebSocket + Vue 控制面板** ✅  
后端 Mock 模式（PC 无硬件可跑）、WebSocket JSON envelope 协议、Vue 控制面板（D-Pad + 虚拟摇杆 + 刹车）、全链路联调（手机→Vue→WS→FastAPI→GPIO→电机）。

**Phase 2.pre —— 电源验收 + 电压监控** ✅  
LM2596S 降压至 5.0V、ADS1115 I2C ADC 驱动（Real/Mock 双实现，零第三方依赖）、20KΩ+10KΩ 分压电路、sensing 子系统（电池电压/电量百分比/等级 + CPU 温度）、`tel.sensors` 遥测接入真实数据。

> 遗留：万用表校准分压比（当前理论值 3.0）、全链路端对端测试。

---

## 感知与自主阶段

**Phase 3 —— FPV 摄像头流媒体** 📋  
OV5640 UVC 摄像头已装好并验证通过（固定在云台上，位于车顶最高点）。本阶段完成软件侧：OpenCV 采集 + MJPEG 独立 endpoint（`/stream/camera`）、Vue 面板嵌入实时画面。120° 广角提供室内宽视野。

**Phase 4 —— PCA9685 舵机驱动 + 摄像头云台** 📋  
硬件已就绪：SG90 × 2 + 2-DOF 云台支架已组装，OV5640 已安装在云台上。本阶段完成：PCA9685 I2C 驱动（地址 0x40，与 ADS1115 共用 I2C1_M4 总线 Pin 3/5）、舵机驱动层（Real/Mock 双实现）、gimbal 子系统（角度映射/限位/平滑）、控制面板加入云台摇杆（手动 FPV 观察）。

> **为什么需要 PCA9685：** 40-pin 上仅剩 PWM15（Pin 33）一路空闲硬件 PWM，不够驱动 2 个舵机（pan + tilt）。PCA9685 通过 I2C 提供 16 路 PWM，一次解决当前和后续所有舵机需求。  
> **延后项：** 云台自动瞄准（YOLO 检测目标 → 云台自动转向保持目标居中），在 Phase 5 视觉追踪基础上可追加。

**Phase 5 —— YOLOv8n 视觉识别与追踪** 📋  
ultralytics 部署、RK3588S NPU（RKNN）加速推理、目标检测 + 追踪控制闭环。结合 Phase 4 云台实现两种追踪模式：云台跟踪（目标偏移 → 舵机补偿，车体不动）和差速跟踪（目标偏移 → 整车转向，适合跟随场景）。

**Phase 6 —— 超声波避障（前后双 HC-SR04）** 📋  
HC-SR04 × 2 已到货，扫描舵机待采购到货。本阶段采用前后双超声波方案：

- **前方 HC-SR04**：分两步实施。第一步固定安装朝正前方，实现基础前方避障；扫描舵机到货后接入 PCA9685 空闲通道，升级为 ±60° 扇形扫描构建距离扇面图，服务于自主导航避障决策。
- **后方 HC-SR04**：固定安装朝正后方，无需舵机。仅在倒车时启用测距，距离 < 阈值（如 20cm）自动刹停 + 前端告警，非倒车状态不采集以省资源。
- **接线**：两个 HC-SR04 各需独立 Trig + Echo GPIO，Echo 均需 5V→3.3V 分压（2KΩ+1KΩ）。
- **软件**：ultrasonic 驱动层（Real/Mock 双实现）、obstacle 子系统（前方扫描 + 后方防撞）、避障算法 + 手动/自动模式切换、倒车防撞安全联锁。

---

## 外设与体验阶段

**Phase 7 —— 遥测仪表盘增强** 📋  
ADS1115 电池电压与 CPU 温度已在 Phase 2.pre 接入。本阶段补齐剩余遥测项：Wi-Fi RSSI、WebSocket 往返延迟、CPU 占用率。前端仪表盘 UI 增强（历史曲线、告警动画）。

**Phase 8 —— 车灯系统** 📋  
IRF520 驱动 3W 前大灯（PWM 调光），WS2812B RGB 灯带分段管理（尾灯/警灯/氛围灯），与运动状态联动（刹车尾灯加亮、自主模式警灯闪烁、倒车灯）。板载 LED 可通过 sysfs 复用为系统状态指示（heartbeat / solid / fast-blink）。

**Phase 9 —— 音频系统** ✅  
USB 免驱声卡（Jieli UACDemoV1.0，card3，48000Hz/S16LE）、aplay 播放 wav、ffplay 播放 mp3、edge-tts 中文语音合成（zh-CN-YunxiNeural）、amixer 音量控制。音效套装（horn/startup/low_battery/reverse/warning/nitro/connect/disconnect）由 Python 程序合成。功能：按住鸣笛循环、开机音效、倒车提示音联动（vy<-0.1 自动触发）、低电量告警循环、前端音量滑块 + TTS 输入框。

**Phase 10 —— 氮气加速彩蛋** 📋  
整合 Phase 8 灯效 + Phase 9 音效 + 电机突破常规上限 + 大灯闪烁，冷却机制（CD 计时），前端按钮 + 动画反馈。

---

## 联网与移动端阶段

**Phase 11 —— 跨网远程控制** 📋  
Tailscale 部署（零配置组网）、验证跨网 WebSocket 稳定性、远程 FPV 延迟测试、多客户端并发控制策略落地（单控制者锁或 last-write-wins）。

**Phase 12 —— React Native 移动 App** 📋  
复用已有 RN 经验、Material Design 风格 UI、与 Vue Web 客户端并存、原生摇杆手感优化。

---

## 高阶智能阶段

**Phase 13 —— 大模型智能控制** 📋  
麦克风接入、STT 流水线、LLM tool calling 设计（指令解析→子系统调用）、TTS 语音回复。先用云端 API 跑通，再切本地 RKLLM（RK3588S NPU 推理）实现离线智能。

**Phase 14 —— 激光雷达 + SLAM** 📋  
RPLIDAR 接入、2D 占用栅格地图构建、地图前端可视化、路径点导航、语义地图（与 LLM 整合实现「去厨房」类自然语言导航指令）。

---

## 40-pin PWM 引脚分配总览

| PWM 通道 | 物理引脚 | 用途 | 启用 overlay | 接入阶段 |
|---|---|---|---|---|
| PWM13_M2 | 7 | 左电机 ENA | `pwm13-m2` ✅ | Phase 2.1 |
| PWM14_M2 | 32 | 右电机 ENB | `pwm14-m2` ✅ | Phase 2.1 |
| PWM15_M2 | 33 | 备用 | `pwm15-m2`（待启用） | 待定 |

> **注：** 摄像头云台双舵机（Phase 4）通过 PCA9685 I2C PWM 驱动，不占用 40-pin 硬件 PWM 通道。前方超声波扫描舵机到货后也接入 PCA9685 空闲通道，后方超声波固定安装无需舵机，PWM15 保留备用。

---

## 当前阶段

> ⚠️ **当前阶段信息统一在本文件维护，其他文档（AGENTS.md / CLAUDE.md / README.md）不再重复。**

**Phase 9 已完成（音频系统）** ✅

1. ☑ USB 声卡识别（Jieli UACDemoV1.0，card3，48000Hz/S16LE/2ch）
2. ☑ aplay 播放 wav + ffplay 播放 mp3（AUDIODEV=hw:3,0）
3. ☑ edge-tts 中文语音合成（zh-CN-YunxiNeural）
4. ☑ amixer 音量控制（numid=4，0-147）
5. ☑ 音效套装程序合成（horn/startup/low_battery/reverse/warning/nitro/connect/disconnect）
6. ☑ 按住鸣笛循环（horn_start/horn_stop）
7. ☑ 开机音效自动播放
8. ☑ 倒车提示音联动（vy < -0.1 自动触发）
9. ☑ 前端 AudioPanel：音量滑块 + TTS 输入框

**下一阶段：Phase 3 — FPV 摄像头（OV5640 + OpenCV + MJPEG 流）**
