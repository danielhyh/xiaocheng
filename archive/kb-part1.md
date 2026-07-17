# 知识库 Part 1 — 硬件平台 + 电源系统 + 电机驱动 + PWM

---

## 1. 硬件平台基础

### 1.1 Orange Pi 5 Pro (RK3588S)

Orange Pi 5 Pro 是一款基于 Rockchip RK3588S 芯片的单板计算机 (SBC)，类似树莓派但性能更强。

**核心规格：**

| 项目 | 参数 |
|---|---|
| CPU | 4× Cortex-A76 (大核 2.4GHz) + 4× Cortex-A55 (小核 1.8GHz) |
| NPU | 6TOPS，支持 INT4/INT8/INT16/FP16 |
| RAM | 8GB LPDDR4X |
| 存储 | TF 卡 (本项目用 64GB A2 级) |
| GPIO | 40-pin 扩展口，兼容树莓派引脚布局 |
| 接口 | USB 3.0 × 2、USB 2.0 × 2、HDMI × 2、PCIe、I2C、SPI、UART |
| 功耗 | 典型 5-10W，峰值约 15W |

**为什么选它：** RK3588S 自带 6TOPS NPU，Phase 5 的 YOLO 推理和 Phase 13 的本地 LLM 都可以不依赖云端。40-pin GPIO 满足全部 14 个 Phase 的外设需求。

### 1.2 40-pin GPIO 引脚系统

OPi 5 Pro 的 40-pin 引脚有三套编号系统，容易混淆：

| 编号系统 | 说明 | 使用场景 |
|---|---|---|
| 物理引脚 (Physical) | 1-40，按板子上的实际位置编号 | 接线时对照图纸 |
| wiringPi 编号 (wPi) | wiringOP 库使用的逻辑编号 | 代码中 `wiringpi.pinMode(wPi, ...)` |
| BCM 编号 | 树莓派 BCM 编号，OPi 部分兼容 | 一般不用 |

**本项目用 wiringPi 编号**，因为驱动层用 wiringOP-Python。

### 1.3 wiringOP-Python

wiringOP 是 Orange Pi 官方维护的 GPIO 库，是树莓派 wiringPi 的移植版。

**关键 API：**
```python
import wiringpi
from wiringpi import GPIO

wiringpi.wiringPiSetup()              # 初始化 (必须第一步)
wiringpi.pinMode(pin, GPIO.OUTPUT)    # 设置引脚模式
wiringpi.digitalWrite(pin, GPIO.HIGH) # 写高电平
wiringpi.digitalRead(pin)             # 读引脚
```

**安装方式（必须从源码编译）：**
```bash
git clone https://github.com/orangepi-xunlong/wiringOP.git -b next
cd wiringOP && sudo ./build
cd python && sudo python3 setup.py install
```
不能 `pip install wiringpi`，那是旧版，不支持 RK3588S。

### 1.4 sysfs 接口

Linux 内核通过 `/sys` 文件系统暴露硬件控制接口，读写文件即可控制硬件。

```
/sys/class/pwm/pwmchip2/    ← PWM 控制器
/sys/class/gpio/            ← GPIO 控制
/sys/class/thermal/         ← 温度传感器
/proc/net/wireless          ← WiFi 信号强度
/proc/stat                  ← CPU 使用率
```

本项目的 PWM 电机控制完全通过 sysfs 实现，不依赖 wiringOP 的 PWM 功能（wiringOP PWM 在 RK3588S 上有兼容性问题）。

---

## 2. 电源系统

### 2.1 整体电源拓扑

```
EVE 18650 × 2 (2S1P)
    │  7.4V 标称 / 8.4V 满充 / 6.0V 截止
    │
    ├──→ L298N 电机驱动 (直接供电, 6-12V)
    │
    └──→ LM2596S 降压模块
              │  输出 5.0V
              │
              ├──→ Orange Pi 5 Pro (5V 2A)
              ├──→ PCA9685 (5V 逻辑)
              ├──→ HC-SR04 超声波 (5V)
              └──→ USB 声卡 (通过 OPi USB 口)
```

### 2.2 18650 锂电池 (2S1P)

**2S1P 含义：**
- 2S = 2 节串联 (Series)，电压叠加：3.7V × 2 = 7.4V 标称
- 1P = 1 并联 (Parallel)，容量不变

**电压区间：**

| 状态 | 单节电压 | 总电压 |
|---|---|---|
| 满充 | 4.2V | 8.4V |
| 标称 | 3.7V | 7.4V |
| 低压告警 | 3.6V | 7.2V |
| 截止 | 3.0V | 6.0V |

**为什么要监控电压：** LM2596S 降压模块需要约 7V 最低输入才能稳定输出 5V。电池低于 7V 时，OPi 可能无声断电，导致 TF 卡文件系统损坏。这是本项目接 ADS1115 的核心原因。

### 2.3 LM2596S 降压模块

LM2596S 是一款开关型降压 (Buck) 稳压芯片，效率远高于线性稳压器 (LDO)。

**工作原理（Buck 变换器）：**
```
输入 → 开关管 (高频通断) → 电感 → 输出
                              ↑
                           续流二极管
```
通过调节开关管的占空比控制输出电压。占空比 = 输出/输入，例如 8V 输入、5V 输出，占空比约 62.5%。

**关键参数：**
- 输入范围：4.5V - 40V
- 输出范围：1.25V - 37V（通过电位器调节）
- 最大电流：3A
- 效率：约 75-92%（远优于 LDO 的 (Vout/Vin) × 100%）
- **最低输入约 7V** 才能稳定输出 5V（压差约 2V）

**调压方法：** 顺时针旋转电位器升压，逆时针降压。用万用表测输出端，调到 5.0V。

### 2.4 18650 保护板 (3A 过充保护)

保护板集成在电池组中，提供：
- **过充保护**：单节超过 4.25V 时切断充电
- **过放保护**：单节低于 2.5V 时切断放电
- **过流保护**：电流超过 3A 时切断

**注意：** 保护板的过流限制是 3A，L298N 电机堵转时电流可能超过此值，导致保护板跳闸。实际使用中电机不会长时间堵转，问题不大。

### 2.5 电量百分比计算

不能简单线性映射，因为锂电池放电曲线是非线性的：

```python
def voltage_to_percent(voltage: float) -> int:
    # 分段线性近似锂电池放电曲线
    if voltage >= 8.4:  return 100
    if voltage >= 8.0:  return int(80 + (voltage - 8.0) / 0.4 * 20)
    if voltage >= 7.6:  return int(50 + (voltage - 7.6) / 0.4 * 30)
    if voltage >= 7.2:  return int(20 + (voltage - 7.2) / 0.4 * 30)
    if voltage >= 6.8:  return int(5  + (voltage - 6.8) / 0.4 * 15)
    return 0
```

中间段（7.6-8.0V）电压变化缓慢，对应大部分使用时间；两端变化较快。

---

## 3. 电机驱动原理

### 3.1 直流电机基础

直流电机通过电磁感应将电能转化为机械能。

**转速控制：** 转速与电压成正比。降低电压 → 降低转速。实际中用 PWM 模拟不同电压。

**转向控制：** 改变电流方向 → 改变磁场方向 → 改变转向。H 桥电路实现这一功能。

### 3.2 H 桥电路

H 桥是控制直流电机正反转的标准电路，因形状像字母 H 而得名。

```
VCC
 │
S1 ──┬── S2
     │
    Motor
     │
S3 ──┴── S4
 │
GND
```

| S1 | S2 | S3 | S4 | 效果 |
|---|---|---|---|---|
| ON | OFF | OFF | ON | 正转 |
| OFF | ON | ON | OFF | 反转 |
| ON | OFF | ON | OFF | 制动 (两端接 VCC) |
| OFF | ON | OFF | ON | 制动 (两端接 GND) |
| OFF | OFF | OFF | OFF | 滑行停止 |

**制动 vs 滑行：** 制动时两端短路，产生反向电动势阻止转动，停车更快。滑行时电机自由转动直到摩擦停止。

### 3.3 L298N 电机驱动模块

L298N 是一款集成双 H 桥的电机驱动芯片，可同时控制两路电机。

**引脚说明：**

| 引脚 | 功能 |
|---|---|
| IN1, IN2 | 左电机方向控制 |
| IN3, IN4 | 右电机方向控制 |
| ENA | 左电机使能 (PWM 调速) |
| ENB | 右电机使能 (PWM 调速) |
| OUT1-4 | 电机输出 |
| VCC | 电机电源 (6-12V) |
| 5V | 逻辑电源 (可由内部稳压提供) |

**方向控制逻辑：**

| IN1 | IN2 | 效果 |
|---|---|---|
| HIGH | LOW | 正转 |
| LOW | HIGH | 反转 |
| HIGH | HIGH | 制动 |
| LOW | LOW | 停止 |

**关键坑：ENA/ENB 跳线帽**  
L298N 出厂时 ENA/ENB 通过跳线帽短接到 5V（固定全速使能）。接 PWM 调速前**必须先拔掉跳线帽**，否则 PWM 信号被覆盖，电机始终全速。

### 3.4 死区 (Dead Zone)

电机存在最低启动电压，低于此电压时电机不转但有电流（发热）。

本项目设 `MOTOR_DEAD_ZONE = 40`，意味着：
- 用户输入 0-100% 的速度
- 实际输出 40-100% 的 PWM 占空比
- 低于 40% 的 PWM 电机不转，直接输出 0

```python
def _map_speed(self, speed: float) -> float:
    if speed <= 0:
        return 0
    dz = config.MOTOR_DEAD_ZONE  # 40
    return dz + speed * (100 - dz) / 100
    # 输入 50% → 输出 40 + 50*(60/100) = 70%
    # 输入 100% → 输出 40 + 100*(60/100) = 100%
```

---

## 4. PWM 脉宽调制

### 4.1 PWM 基本原理

PWM (Pulse Width Modulation，脉宽调制) 通过快速开关信号模拟模拟量输出。

**关键参数：**
- **频率 (Frequency)**：每秒开关多少次，单位 Hz。本项目 1kHz（周期 1ms）
- **占空比 (Duty Cycle)**：高电平时间占一个周期的比例，0-100%
- **等效电压**：占空比 × 电源电压。50% 占空比 ≈ 2.5V（5V 系统）

```
100% 占空比:  ████████████  (全速)
 50% 占空比:  ██░░██░░██░░  (半速)
  0% 占空比:  ░░░░░░░░░░░░  (停止)
```

**为什么 1kHz：** 太低（<100Hz）电机会抖动，能听到嗡嗡声；太高（>20kHz）超出 L298N 响应速度。1kHz 是电机驱动的常用频率。

### 4.2 RK3588S sysfs PWM

RK3588S 通过 Linux sysfs 接口控制硬件 PWM，操作方式是读写文件：

```bash
# 1. 导出 PWM 通道
echo 0 > /sys/class/pwm/pwmchip2/export

# 2. 设置周期 (纳秒)
echo 1000000 > /sys/class/pwm/pwmchip2/pwm0/period   # 1ms = 1kHz

# 3. 设置占空比 (纳秒，必须 ≤ period)
echo 500000 > /sys/class/pwm/pwmchip2/pwm0/duty_cycle  # 50%

# 4. 设置极性
echo normal > /sys/class/pwm/pwmchip2/pwm0/polarity
# 或
echo inversed > /sys/class/pwm/pwmchip2/pwm0/polarity

# 5. 使能
echo 1 > /sys/class/pwm/pwmchip2/pwm0/enable
```

Python 代码中用 `open(path, 'w').write(str(value))` 实现同样操作。

### 4.3 PWM 极性反转 (RK3588S 特有坑)

**现象：** 写入占空比 100% 时电机反而最慢，写入 0% 时全速。

**根因：** RK3588S 的 sysfs PWM 默认极性与预期相反。写入 `duty_cycle = X` 实际高电平时间是 `period - X`。

**解决：** 设置 `polarity = inversed`，或在代码中反转计算：

```python
PWM_INVERTED = True  # config.py

def set_duty(self, percent: float):
    actual = (100 - percent) if self.inverted else percent
    duty_ns = int(self.period_ns * actual / 100)
    self._write(f"{self.pwm_path}/duty_cycle", duty_ns)
```

### 4.4 PWM 通道与 pwmchip 编号

RK3588S 有多个 PWM 控制器，每个对应一个 pwmchip：

| PWM 通道 | pwmchip | 物理引脚 | 用途 |
|---|---|---|---|
| PWM13_M2 | pwmchip2 | 7 | 左电机 ENA |
| PWM14_M2 | pwmchip3 | 32 | 右电机 ENB |

**如何确认 pwmchip 编号：**
```bash
ls /sys/class/pwm/
# 输出: pwmchip0  pwmchip1  pwmchip2  pwmchip3 ...

# 查看每个 chip 对应哪个 PWM 控制器
cat /sys/class/pwm/pwmchip2/device/uevent
```

### 4.5 PCA9685 的 PWM（I2C 扩展）

除了 sysfs 硬件 PWM，本项目还用 PCA9685 芯片通过 I2C 扩展出 16 路 PWM，用于舵机和大灯控制。详见第 9 章。

两种 PWM 的对比：

| 特性 | sysfs 硬件 PWM | PCA9685 I2C PWM |
|---|---|---|
| 通道数 | 受限（RK3588S 约 4 路可用） | 16 路 |
| 精度 | 纳秒级 | 12-bit (4096 级) |
| CPU 占用 | 零（硬件生成） | 极低（I2C 写寄存器） |
| 用途 | 电机调速（需要高精度） | 舵机、LED 调光 |
