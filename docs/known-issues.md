# 已知问题与 Workaround

> 随时追加，问题解决后标记 [RESOLVED]。  
> 格式：[状态] 问题描述 | 复现条件 | Workaround / 根因

---

## 硬件类

### [RESOLVED] PWM 极性反转导致速度控制反向

**现象：** 占空比越高电机速度反而越慢，占空比为 0 时全速转。  
**根因：** RK3588S sysfs PWM 的 polarity 默认行为与预期相反。  
**解决：** `motor.py` 中设 `PWM_INVERTED = True`，即写入 `polarity = inversed`。

---

### [RESOLVED] ENB 跳线帽导致 PWM 失效

**现象：** 连接 PWM 信号后电机始终全速，速度控制无效。  
**根因：** L298N 出厂 ENA/ENB 跳线帽短接到 5V（固定使能），覆盖了外部 PWM 信号。  
**解决：** 接 PWM 前必须先拔掉 ENA/ENB 跳线帽。

---

### [RESOLVED] OPi 4 Pro 的 pwmchip 路径迁移到 5 Pro 需要修改

**现象：** 迁移到 OPi 5 Pro 后 PWM 初始化失败，找不到 sysfs 路径。  
**根因：** 不同 SoC 的 pwmchip 编号不同。4 Pro (Allwinner) 和 5 Pro (RK3588S) 的路径不一样。  
**解决：** 5 Pro 上确认：PWM13_M2 → `/sys/class/pwm/pwmchip2`，PWM14_M2 → `/sys/class/pwm/pwmchip3`。

---

### [OPEN] HC-SR04 Echo 引脚电平问题（Phase 4 预警）

**现象：** 尚未接线，但已知 HC-SR04 Echo 输出 5V 电平。  
**风险：** 直接连 OPi 3.3V GPIO 可能损坏 IO 口。  
**计划：** Phase 4 接线时加 2KΩ + 1KΩ 分压电路（5V → 3.3V），或使用双向电平转换模块。

---

### [OPEN] LM2596S 低压死区（已知风险，监控待落地）

**现象：** 电池电压低于约 7V 时，LM2596S 无法维持稳定 5V 输出，OPi 可能无声断电。  
**影响：** SD 卡文件系统可能损坏。  
**缓解计划：** ADS1115 电压监控 + 低压告警（阈值 7.2V），在电压下降到危险区前强制停车并通知用户。  
**状态：** 当前只有 mock `tel.sensors`；ADS1115 驱动、sensing 子系统和真板接线仍待完成（Phase 2.pre）。

---

## 软件类

### [OPEN] 前端持续运动指令在网络抖动时可能误触发停车

**现象：** 摇杆保持固定位置时，前端每 100ms 发一次 `cmd.motion`。若 WiFi 出现短暂抖动（>500ms），安全 Watchdog 会误判为断连并停车。  
**根因：** Watchdog 超时阈值（500ms）与持续发送间隔（100ms）之间的余量不足。  
**当前状态：** 尚未系统测试，实际影响待确认。  
**候选方案：** 增大 Watchdog 超时至 1000ms；或加入心跳消息与运动指令分离的保活机制。

---

### [OPEN] 多客户端并发控制策略未定

**现象：** 若两个手机同时连接控制面板，两者的 `cmd.motion` 都会被执行，导致指令冲突。  
**现状：** Phase 2.2 暂不处理，局域网单用户使用。  
**计划：** Phase 11（跨网）前需确定策略：last-write-wins / 单控制者锁 / 仅允许局域网连接。

---

## 环境/工具类

### [RESOLVED] wiringOP-Python 无法通过 pip 安装

**现象：** `pip install wiringpi` 安装的是旧版，不支持 OPi 5 Pro。  
**解决：** 必须从源码编译：  

```bash
git clone https://github.com/orangepi-xunlong/wiringOP.git -b next
cd wiringOP && sudo ./build
cd python && sudo python3 setup.py install
```

---

### [RESOLVED] 从旧 TF 卡克隆到新卡后遗留问题多

**现象：** 克隆方式迁移后，系统遗留旧配置、wiringOP 版本等问题，排查困难。  
**解决：** 换 TF 卡时重新烧录新 OS 镜像，重新从零配置，比克隆省时间。
