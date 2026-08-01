"""
config.py — 板级常量 + Mock 总开关

所有硬件相关的配置集中在这里。
换板子 / 换接线只改这个文件,其余代码不动。
"""

import os

# ============================================================
#  Mock 开关
# ============================================================
USE_MOCK = os.getenv("XIAOCHENG_MOCK", "0") == "1"


def _env_enabled(name: str, *, real_default: bool = False) -> bool:
    """读取外设启用开关；Mock 默认全开，真板按安全默认值启动。"""
    raw = os.getenv(name)
    if raw is None:
        return True if USE_MOCK else real_default

    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        f"{name}={raw!r} 无效；请使用 1/0、true/false、yes/no 或 on/off"
    )


# 真板默认只启用当前已接的摄像头。输出型硬件和待重接传感器必须显式开启，
# 避免未验收外设在应用 import/startup 阶段访问 GPIO、I2C、SPI 或声卡。
ENABLE_MOTION = _env_enabled("XIAOCHENG_ENABLE_MOTION")
ENABLE_SENSING = _env_enabled("XIAOCHENG_ENABLE_SENSING")
ENABLE_VISION = _env_enabled("XIAOCHENG_ENABLE_VISION", real_default=True)
ENABLE_AUDIO = _env_enabled("XIAOCHENG_ENABLE_AUDIO")
ENABLE_LIGHTING = _env_enabled("XIAOCHENG_ENABLE_LIGHTING")
ENABLE_GIMBAL = _env_enabled("XIAOCHENG_ENABLE_GIMBAL")
ENABLE_OBSTACLE = _env_enabled("XIAOCHENG_ENABLE_OBSTACLE")
ENABLE_NITRO = _env_enabled("XIAOCHENG_ENABLE_NITRO")

SUBSYSTEMS_ENABLED: dict[str, bool] = {
    "motion": ENABLE_MOTION,
    "sensing": ENABLE_SENSING,
    "vision": ENABLE_VISION,
    "audio": ENABLE_AUDIO,
    "lighting": ENABLE_LIGHTING,
    "gimbal": ENABLE_GIMBAL,
    "obstacle": ENABLE_OBSTACLE,
    "nitro": ENABLE_NITRO and ENABLE_MOTION,
}

# ============================================================
#  电机 (L298N) — Phase 2
# ============================================================
# 左侧电机
LEFT_IN1 = 5          # wPi 编号, 物理引脚 11
LEFT_IN2 = 7          # wPi 编号, 物理引脚 13
LEFT_PWM_CHIP = "/sys/class/pwm/pwmchip2"   # PWM13
LEFT_PWM_CH = "0"

# 右侧电机
RIGHT_IN3 = 13        # wPi 编号, 物理引脚 22
RIGHT_IN4 = 16        # wPi 编号, 物理引脚 26
RIGHT_PWM_CHIP = "/sys/class/pwm/pwmchip3"  # PWM14
RIGHT_PWM_CH = "0"

# PWM 参数
PWM_PERIOD_NS = 1_000_000   # 1ms = 1kHz
PWM_INVERTED = True          # RK3588S 极性反转

# 电机死区
MOTOR_DEAD_ZONE = 40         # 40% 以下电机不转

# ============================================================
#  WebSocket
# ============================================================
WS_HEARTBEAT_INTERVAL = 1.0       # 心跳间隔 (秒)
WS_DISCONNECT_TIMEOUT = 0.5       # 断连后多久自动停车 (秒)
MOTION_CMD_RATE_LIMIT = 30        # 运动指令最大频率 (Hz)

# ============================================================
#  遥测
# ============================================================
TELEMETRY_SENSORS_INTERVAL = 1.0  # tel.sensors 推送间隔 (秒)
TELEMETRY_MOTION_INTERVAL = 0.1   # tel.motion 推送间隔 (秒)

# ============================================================
#  ADS1115 ADC — Phase 2.pre
# ============================================================
I2C_BUS = 1                       # /dev/i2c-1 (I2C1_M4, 物理脚 3/5)
ADS1115_ADDR = 0x48               # ADDR 引脚接 GND 时默认地址
ADS1115_CHANNEL = 0               # A0 通道
ADS1115_FSR = 4.096               # 满量程 ±4.096V

# ============================================================
#  电池参数 (2S 18650)
# ============================================================
BATTERY_DIVIDER_RATIO = 3.026     # 实测校准值 (万用表: 总压7.99V / 分压2.64V)
BATTERY_FULL = 8.4                # 满充电压 (V)
BATTERY_LOW = 6.8                 # 低压告警 (V)
BATTERY_CRITICAL = 6.2            # 极低压,应停车 (V)

# 电压滤波 (EMA: 指数移动平均)
BATTERY_EMA_ALPHA = 0.01          # EMA 平滑系数 (越小越平滑; 1s 采样间隔下 0.01 约 100 次才收敛)
BATTERY_EMA_INIT_SAMPLES = 8      # 启动时取前 N 次读数的均值作为 EMA 初始值
BATTERY_PERCENT_DROP_RATE = 2     # 百分比每秒最大下降速率 (%/s)
BATTERY_PERCENT_RISE_RATE = 0.5   # 百分比每秒最大上升速率 (%/s)

# ============================================================
#  摄像头 (前置 OV13855 MIPI / 后置 OV5640 USB)
# ============================================================
_camera_device = os.getenv("XIAOCHENG_CAMERA", "auto")
CAMERA_DEVICE: int | str = (
    int(_camera_device) if _camera_device.isdecimal() else _camera_device
)
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30                   # OV13855 经 RKISP 输出约 15fps；USB 摄像头按自身能力回退
CAMERA_JPEG_QUALITY = 80          # JPEG 压缩质量 (0-100, 越高越清晰但带宽越大)
CAMERA_STREAM_FPS = 30            # MJPEG 流输出帧率 (匹配采集帧率)
CAMERA_USE_MJPG = True            # USB 摄像头优先 MJPG；MIPI RKISP 节点自动改用 NV12

# ============================================================
#  音频 (USB 声卡) — Phase 9
# ============================================================
AUDIO_CARD = 3                        # USB 声卡卡号 (aplay -l 查看)
AUDIO_VOLUME_NUMID = 4                # amixer numid (PCM Playback Volume)
AUDIO_VOLUME_MAX = 147                # amixer 最大原始值
AUDIO_DEFAULT_VOLUME = 80             # 启动默认音量 (%)
AUDIO_TTS_VOICE = "zh-CN-YunxiNeural" # edge-tts 中文男声
AUDIO_CLIPS_DIR = "assets/sounds"     # 音效文件目录
AUDIO_ALERT_INTERVAL = 10.0           # 低电量告警音循环间隔 (秒)
AUDIO_ALERT_VOLTAGE = 7.2             # 低电量告警阈值 (V),可调

# ============================================================
#  前大灯 (Pin 33 / PWM15_M2, 自带驱动) — Phase 8
# ============================================================
PCA9685_ADDR = 0x40               # PCA9685 I2C 地址 (与 ADS1115 共用 I2C1_M4)
HEADLIGHT_PHYSICAL_PIN = 33       # 40-pin 物理引脚
HEADLIGHT_WPI_PIN = 22            # wiringOP 编号；PWM 模式由 overlay 接管
HEADLIGHT_PWM_OVERLAY = "pwm15-m2"

# 旧 PCA9685 大灯驱动仍待 P8-01 替换。设为 None 使误启用时失败关闭，
# 防止占用已分配给前云台的 CH0/1。
LED_LEFT_CHANNEL: None = None
LED_RIGHT_CHANNEL: None = None
LED_PWM_FREQ = 1000               # PWM 频率 (Hz)
LED_DEFAULT_BRIGHTNESS = 80       # 默认大灯亮度 (0-100)

# ============================================================
#  WS2812B 灯带 — Phase 8
# ============================================================
STRIP_NUM_LEDS = 10               # 灯珠数量
STRIP_SPI_DEV = "/dev/spidev0.0"  # SPI 设备 (MOSI → Data In)
STRIP_SPI_SPEED = 6_400_000       # SPI 时钟 6.4MHz (WS2812B 时序)
STRIP_DEFAULT_BRIGHTNESS = 128    # 默认亮度 (0-255)

# 灯带分段映射 (索引范围,含两端)
STRIP_SEGMENTS: dict[str, tuple[int, int]] = {
    "left":  (0, 2),   # 左侧 3 颗
    "tail":  (3, 6),   # 尾灯中央 4 颗
    "right": (7, 9),   # 右侧 3 颗
}

# 灯带预设颜色 (R, G, B)
STRIP_COLOR_TAIL    = (80, 0, 0)      # 尾灯: 暗红
STRIP_COLOR_BRAKE   = (255, 0, 0)     # 刹车: 亮红
STRIP_COLOR_REVERSE = (255, 255, 255) # 倒车: 白色

# ============================================================
#  舵机 (PCA9685 + SG90) — Phase 4
# ============================================================
SERVO_FRONT_PAN_CHANNEL = 0       # 前云台水平
SERVO_FRONT_TILT_CHANNEL = 1      # 前云台垂直
SERVO_SCAN_CHANNEL = 2            # 可选前超声波扫描舵机
SERVO_REAR_PAN_CHANNEL = 3        # 后云台水平
SERVO_REAR_TILT_CHANNEL = 4       # 后云台垂直

# 云台角度限位 (0-180, 中位 90)
GIMBAL_PAN_MIN = 10               # 水平最小角度
GIMBAL_PAN_MAX = 170              # 水平最大角度
GIMBAL_TILT_MIN = 30              # 垂直最小角度 (防止低头撞车身)
GIMBAL_TILT_MAX = 150             # 垂直最大角度
GIMBAL_STEP = 3.0                 # 摇杆增量步进 (度/次)
GIMBAL_TRACKING_GAIN = 5.0        # 自动追踪增益 (度/偏移量)

# ============================================================
#  超声波 (HC-SR04 × 2) — Phase 6
# ============================================================
# 前方 HC-SR04 (GPIO wPi 编号)
US_FRONT_TRIG = 19                # wPi 19, 物理引脚 29
US_FRONT_ECHO = 20                # wPi 20, 物理引脚 31；3.3V 供电时直连

# 后方 HC-SR04
US_REAR_TRIG = 23                 # wPi 23, 物理引脚 35
US_REAR_ECHO = 25                 # wPi 25, 物理引脚 37；3.3V 供电时直连

US_SCAN_INTERVAL = 0.1            # 扫描间隔 (秒)
US_FRONT_STOP_DISTANCE = 25.0     # 前方停车距离 (cm)
US_FRONT_WARN_DISTANCE = 50.0     # 前方警告距离 (cm)
US_REAR_STOP_DISTANCE = 20.0      # 后方停车距离 (cm)

# ============================================================
#  氮气加速彩蛋 — Phase 10
# ============================================================
NITRO_DURATION = 3.0              # 氮气持续时间 (秒)
NITRO_COOLDOWN = 10.0             # 冷却时间 (秒)
NITRO_BOOST_FACTOR = 1.3          # 加速倍率

# ============================================================
#  服务器
# ============================================================
HOST = "0.0.0.0"
PORT = 8000
