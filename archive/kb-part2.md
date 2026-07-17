# 知识库 Part 2 — I2C + ADC + 分压电路 + SPI/WS2812B + PCA9685 + MOSFET

---

## 5. I2C 总线通信

### 5.1 I2C 基本原理

I2C (Inter-Integrated Circuit) 是一种两线串行通信协议，由飞利浦（现 NXP）发明。

**两根线：**
- **SDA (Serial Data)**：数据线，双向
- **SCL (Serial Clock)**：时钟线，由主设备控制

**特点：**
- 一主多从：一个主设备可挂多个从设备，通过 7-bit 地址区分
- 半双工：同一时刻只能单向传输
- 速度：标准 100kHz，快速 400kHz，高速 3.4MHz
- 需要上拉电阻（通常 4.7kΩ）将总线拉到高电平

### 5.2 I2C 通信时序

```
START  地址(7bit) R/W  ACK  数据(8bit)  ACK  STOP
  ↓       ↓       ↓    ↓       ↓        ↓     ↓
SDA: ‾\_  [AAAAAAA][W]  _  [DDDDDDDD]  _   _/‾
SCL: ‾‾  ___________  ‾‾  __________  ‾‾  ‾‾
```

- **START**：SCL 高时 SDA 下降沿
- **STOP**：SCL 高时 SDA 上升沿
- **ACK**：从设备拉低 SDA 表示收到
- **NACK**：SDA 保持高表示未收到或结束

### 5.3 OPi 5 Pro 的 I2C 总线

RK3588S 有多个 I2C 控制器，本项目使用 **I2C1_M4**：

| 总线 | 物理引脚 | 设备文件 | 挂载设备 |
|---|---|---|---|
| I2C1_M4 | 3 (SDA), 5 (SCL) | /dev/i2c-1 | ADS1115 (0x48) + PCA9685 (0x40) |

**检测 I2C 设备：**
```bash
i2cdetect -y 1
# 输出矩阵中 40 = PCA9685, 48 = ADS1115
```

### 5.4 原始 I2C 操作（Python）

本项目不用 smbus2 等第三方库，直接用 Python 的 `ioctl` 操作 I2C：

```python
import os
import fcntl
import struct

I2C_SLAVE = 0x0703

fd = os.open("/dev/i2c-1", os.O_RDWR)
fcntl.ioctl(fd, I2C_SLAVE, 0x48)  # 选择从设备地址

# 写寄存器
os.write(fd, bytes([reg_addr, value_high, value_low]))

# 读数据
os.write(fd, bytes([reg_addr]))    # 先写寄存器地址
data = os.read(fd, 2)              # 再读 2 字节
```

**为什么不用 smbus2：** 零第三方依赖，代码透明，便于理解底层原理，也避免了依赖版本问题。

---

## 6. ADC 模数转换 (ADS1115)

### 6.1 为什么需要 ADC

OPi 5 Pro 没有内置 ADC（模数转换器）。GPIO 引脚只能读数字信号（高/低），无法直接读取电池电压这样的模拟量。

ADS1115 是一款通过 I2C 通信的外置 16-bit ADC，解决了这个问题。

### 6.2 ADS1115 规格

| 参数 | 值 |
|---|---|
| 分辨率 | 16-bit（实际 15-bit + 符号位） |
| 通道数 | 4 路单端 (A0-A3) 或 2 路差分 |
| 接口 | I2C，地址 0x48-0x4B（由 ADDR 引脚决定） |
| 采样率 | 8-860 SPS（可配置） |
| 满量程 (FSR) | ±0.256V 到 ±6.144V（6 档可配置） |
| 工作电压 | 2.0V - 5.5V |

**地址配置：**

| ADDR 引脚 | I2C 地址 |
|---|---|
| GND | 0x48（本项目） |
| VCC | 0x49 |
| SDA | 0x4A |
| SCL | 0x4B |

### 6.3 ADS1115 寄存器

ADS1115 有 4 个 16-bit 寄存器：

| 寄存器 | 地址 | 功能 |
|---|---|---|
| Conversion | 0x00 | 转换结果（只读） |
| Config | 0x01 | 配置（量程/通道/采样率等） |
| Lo_thresh | 0x02 | 低阈值（比较器模式用） |
| Hi_thresh | 0x03 | 高阈值（比较器模式用） |

**Config 寄存器关键位（16-bit）：**

```
Bit 15:    OS      - 单次转换触发 (写1启动)
Bit 14-12: MUX     - 通道选择 (100=A0 vs GND)
Bit 11-9:  PGA     - 增益/量程 (001=±4.096V)
Bit 8:     MODE    - 0=连续, 1=单次
Bit 7-5:   DR      - 采样率 (100=128SPS)
```

### 6.4 读取流程

```python
# 1. 写 Config 寄存器，触发单次转换
config_val = 0xC183  # OS=1(启动), MUX=100(A0), PGA=001(±4.096V), MODE=1(单次)
os.write(fd, struct.pack('>BH', 0x01, config_val))

# 2. 等待转换完成 (约 8ms @ 128SPS)
time.sleep(0.01)

# 3. 读 Conversion 寄存器
os.write(fd, bytes([0x00]))
raw = os.read(fd, 2)
value = struct.unpack('>h', raw)[0]  # 有符号 16-bit

# 4. 转换为电压
voltage = value * 4.096 / 32767.0   # FSR=4.096V, 满量程 32767
```

### 6.5 16-bit 精度意味着什么

FSR = ±4.096V，分辨率 = 4.096 / 32767 ≈ **0.125mV/LSB**

对于 8V 电池电压（经分压后约 2.64V），精度约 0.125mV，换算回原始电压约 0.38mV。远超实际需求（告警精度 0.1V 级别即可）。

---

## 7. 分压电路与电压监控

### 7.1 分压电路原理

ADS1115 的 FSR 最大 ±4.096V，但电池电压最高 8.4V，超出量程。需要分压电路将电压缩小到可测范围。

**分压公式：**
```
Vout = Vin × R2 / (R1 + R2)
```

本项目：R1 = 20kΩ，R2 = 10kΩ

```
Vbat ──[20kΩ]──┬──[10kΩ]── GND
               │
              ADS1115 A0
```

**理论分压比：** (20+10)/10 = **3.0**

**实测校准：** 万用表测得总压 7.99V，ADS1115 读数 2.64V，实际比值 = 7.99/2.64 = **3.026**（已写入 `config.BATTERY_DIVIDER_RATIO`）

**还原公式：**
```python
battery_voltage = adc_voltage * BATTERY_DIVIDER_RATIO
```

### 7.2 为什么用 20kΩ + 10kΩ

- **阻值不能太小**：分压电路持续消耗电流，R 越小电流越大。20kΩ+10kΩ 时电流 = 8.4V/30kΩ ≈ 0.28mA，功耗约 2.4mW，可接受。
- **阻值不能太大**：太大时 ADS1115 输入阻抗影响读数精度（ADS1115 输入阻抗约 10MΩ，远大于 10kΩ，影响可忽略）。
- **分压后电压**：8.4V/3 = 2.8V，在 ADS1115 的 ±4.096V 量程内，有足够余量。

### 7.3 EMA 滤波（指数移动平均）

ADC 读数有噪声，直接显示会抖动。用 EMA 平滑：

```python
# EMA: Exponential Moving Average
# alpha 越小越平滑，但响应越慢
alpha = 0.01  # config.BATTERY_EMA_ALPHA

ema = alpha * new_reading + (1 - alpha) * ema
```

**直觉理解：** alpha=0.01 时，新读数只占 1%，历史值占 99%。约需 100 次采样（100 秒）才能完全响应一个阶跃变化。对于缓慢变化的电池电压，这是合适的。

**启动初始化：** 冷启动时 EMA 初始值为 0，需要多次采样才能收敛。本项目取前 8 次读数的均值作为初始值：

```python
samples = [read_adc() for _ in range(BATTERY_EMA_INIT_SAMPLES)]
ema = sum(samples) / len(samples)
```

### 7.4 电量百分比变化速率限制

即使 EMA 后，电量百分比仍可能因噪声出现短暂跳变。加入变化速率限制：

```python
# 每秒最多下降 2%，最多上升 0.5%
max_drop = BATTERY_PERCENT_DROP_RATE * dt   # 2 * 1.0 = 2%/s
max_rise = BATTERY_PERCENT_RISE_RATE * dt   # 0.5 * 1.0 = 0.5%/s

delta = new_percent - current_percent
delta = max(-max_drop, min(max_rise, delta))
current_percent += delta
```

上升速率限制更严（0.5%/s），防止噪声导致电量虚假回升。

---

## 8. SPI 总线与 WS2812B 灯带

### 8.1 SPI 基本原理

SPI (Serial Peripheral Interface) 是一种四线同步串行通信协议，速度比 I2C 快得多。

**四根线：**
- **MOSI** (Master Out Slave In)：主发从收
- **MISO** (Master In Slave Out)：从发主收
- **SCLK** (Serial Clock)：时钟
- **CS/SS** (Chip Select)：片选，低有效

**特点：**
- 全双工（同时收发）
- 无地址，用 CS 选择设备
- 速度可达几十 MHz
- WS2812B 只用 MOSI（单线协议，借用 SPI 时序）

### 8.2 WS2812B 灯珠原理

WS2812B 是一种集成了控制芯片的 RGB LED，每颗灯珠内置 IC，通过单线串行协议控制。

**数据格式：** 每颗灯珠接收 24-bit 数据（GRB 顺序，注意不是 RGB）：
```
[G7 G6 G5 G4 G3 G2 G1 G0] [R7 R6 R5 R4 R3 R2 R1 R0] [B7 B6 B5 B4 B3 B2 B1 B0]
```

**时序要求（极严格）：**
- 逻辑 1：高电平 0.8μs + 低电平 0.45μs
- 逻辑 0：高电平 0.4μs + 低电平 0.85μs
- 复位：低电平 > 50μs

这个时序精度要求在 Python 中无法用 GPIO 直接实现（Python 太慢），需要借用 SPI 硬件。

### 8.3 SPI Bitbang 模拟 WS2812B 时序

**核心思路：** 用 SPI 的 MOSI 信号模拟 WS2812B 的单线时序。

SPI 时钟设为 6.4MHz，每个 SPI bit 周期 = 1/6.4MHz ≈ 156ns。

用 3 个 SPI bit 表示 1 个 WS2812B bit：
- WS2812B 逻辑 1 → SPI 发送 `110`（高高低）≈ 312ns 高 + 156ns 低
- WS2812B 逻辑 0 → SPI 发送 `100`（高低低）≈ 156ns 高 + 312ns 低

```python
def _encode_byte(byte_val: int) -> list[int]:
    """将 1 字节编码为 WS2812B SPI 序列"""
    result = []
    for bit in range(7, -1, -1):
        if byte_val & (1 << bit):
            result.extend([0b110])  # 逻辑 1
        else:
            result.extend([0b100])  # 逻辑 0
    return result
```

每颗灯珠 24-bit → 72 个 SPI bit → 9 字节 SPI 数据。10 颗灯珠 = 90 字节。

### 8.4 灯带分段控制

本项目 10 颗灯珠按位置分为三段：

```
[0][1][2]  [3][4][5][6]  [7][8][9]
  左侧        尾灯中央       右侧
```

```python
STRIP_SEGMENTS = {
    "left":  (0, 2),   # 索引 0-2，共 3 颗
    "tail":  (3, 6),   # 索引 3-6，共 4 颗
    "right": (7, 9),   # 索引 7-9，共 3 颗
}
```

`set_segment("tail", 255, 0, 0)` 只点亮尾灯段为红色，其余不变。

### 8.5 电平转换（5V 信号问题）

WS2812B 数据线需要 5V 逻辑电平，而 OPi 的 SPI MOSI 是 3.3V。

**解决方案：** 74AHCT125 单向电平转换芯片（3.3V → 5V），或直接用 3.3V 信号（部分 WS2812B 可接受，但不保证稳定）。

---

## 9. PCA9685 PWM 扩展芯片

### 9.1 为什么需要 PCA9685

RK3588S 的硬件 PWM 通道有限（可用的约 4 路），而本项目需要：
- 2 路大灯 PWM（左/右独立调光）
- 2 路舵机 PWM（pan/tilt）

PCA9685 通过 I2C 扩展出 16 路 12-bit PWM，一颗芯片解决所有需求。

### 9.2 PCA9685 规格

| 参数 | 值 |
|---|---|
| PWM 通道 | 16 路 |
| 分辨率 | 12-bit（4096 级） |
| 频率范围 | 24Hz - 1526Hz（可配置） |
| 接口 | I2C，地址 0x40-0x7F |
| 工作电压 | 2.3V - 5.5V |
| 输出电流 | 每路最大 25mA（直接驱动 LED），驱动电机/大灯需外接 MOSFET |

### 9.3 PWM 频率设置

PCA9685 通过预分频寄存器设置 PWM 频率：

```python
# 内部振荡器 25MHz
# prescale = round(25MHz / (4096 * freq)) - 1
prescale = round(25_000_000 / (4096 * freq)) - 1

# 写入前需先进入 SLEEP 模式
write_reg(0x00, 0x10)          # MODE1: SLEEP=1
write_reg(0xFE, prescale)      # PRE_SCALE
write_reg(0x00, 0x00)          # MODE1: 唤醒
time.sleep(0.005)
write_reg(0x00, 0xA0)          # MODE1: AUTO_INCREMENT=1
```

### 9.4 通道控制寄存器

每个通道有 4 个字节的寄存器（ON_L, ON_H, OFF_L, OFF_H）：

```
ON  = 上升沿时刻 (0-4095)
OFF = 下降沿时刻 (0-4095)
占空比 = (OFF - ON) / 4096
```

通常 ON=0，只设 OFF 值：

```python
def set_pwm(channel: int, on: int, off: int):
    base = 0x06 + channel * 4
    write_reg(base,     on  & 0xFF)
    write_reg(base + 1, on  >> 8)
    write_reg(base + 2, off & 0xFF)
    write_reg(base + 3, off >> 8)

# 50% 占空比
set_pwm(0, 0, 2048)

# 全亮 (特殊值)
set_pwm(0, 0, 4096)  # OFF bit 12 = 1 表示全开

# 全灭
set_pwm(0, 0, 0)
```

### 9.5 舵机控制

SG90 舵机通过 PWM 控制角度：
- 频率：50Hz（周期 20ms）
- 脉宽 0.5ms（占空比 2.5%）→ 0°
- 脉宽 1.5ms（占空比 7.5%）→ 90°（中位）
- 脉宽 2.5ms（占空比 12.5%）→ 180°

```python
def angle_to_pwm(angle: float, freq: int = 50) -> int:
    """角度转 PCA9685 OFF 值"""
    # 脉宽范围 0.5ms - 2.5ms
    pulse_ms = 0.5 + (angle / 180.0) * 2.0
    # 转换为 4096 级
    period_ms = 1000.0 / freq  # 20ms
    return int(pulse_ms / period_ms * 4096)
```

### 9.6 通道分配（本项目）

| PCA9685 通道 | 用途 | 频率 |
|---|---|---|
| 0 | 左大灯 (IRF520 MOSFET) | 1kHz |
| 1 | 右大灯 (IRF520 MOSFET) | 1kHz |
| 2 | 云台水平舵机 (pan) | 50Hz |
| 3 | 云台垂直舵机 (tilt) | 50Hz |

**注意：** 大灯和舵机频率不同，但 PCA9685 所有通道共用同一个频率设置。解决方案：大灯用 PWM 占空比调光（1kHz 对 MOSFET 没问题），舵机用 50Hz。实际上 50Hz 对大灯调光也可以，只是频率低时肉眼可能看到闪烁。本项目选择 50Hz 以兼容舵机。

---

## 10. MOSFET 功率开关 (IRF520)

### 10.1 为什么需要 MOSFET

PCA9685 每路输出最大 25mA，而 3W LED 在 5V 下电流约 600mA，远超 PCA9685 的驱动能力。

IRF520 是一款 N 沟道 MOSFET，作为功率开关，用 PCA9685 的小信号控制大电流负载。

### 10.2 MOSFET 工作原理

MOSFET 有三个引脚：
- **Gate (G)**：控制极，输入电压控制开关
- **Drain (D)**：漏极，电流从这里流入
- **Source (S)**：源极，电流从这里流出

**N 沟道 MOSFET：**
- Vgs（Gate-Source 电压）> 阈值电压（约 2-4V）→ 导通（开关闭合）
- Vgs < 阈值电压 → 截止（开关断开）

```
PCA9685 PWM → Gate
                │
LED+ ──────── Drain
                │
              Source ── GND
```

### 10.3 IRF520 参数

| 参数 | 值 |
|---|---|
| 类型 | N 沟道增强型 MOSFET |
| Vds（最大漏源电压） | 100V |
| Id（最大漏极电流） | 9.7A |
| Vgs(th)（阈值电压） | 2-4V |
| Rds(on)（导通电阻） | 0.27Ω |

**为什么选 IRF520：** 阈值电压 2-4V，PCA9685 输出 3.3V 可以驱动（勉强，实测可行）。更好的选择是 IRLZ44N（逻辑电平 MOSFET，阈值 1-2V，3.3V 完全驱动）。

### 10.4 PWM 调光原理

MOSFET 在 PWM 信号下快速开关，LED 的平均亮度 = 占空比 × 最大亮度。

```
占空比 100% → LED 全亮
占空比  50% → LED 半亮（视觉上约 70% 亮度，因为人眼对亮度感知是非线性的）
占空比   0% → LED 熄灭
```

**频率选择：** 1kHz 对 MOSFET 开关损耗可忽略，且远超人眼临界融合频率（约 60Hz），不会看到闪烁。
