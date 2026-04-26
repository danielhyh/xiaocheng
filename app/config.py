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

# ============================================================
#  摄像头 (OV5640) — Phase 3
# ============================================================
CAMERA_DEVICE = int(os.getenv("XIAOCHENG_CAMERA", "0"))  # /dev/video0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30                   # 采集帧率
CAMERA_JPEG_QUALITY = 70          # JPEG 压缩质量 (0-100, 越高越清晰但带宽越大)
CAMERA_STREAM_FPS = 20            # MJPEG 流输出帧率 (可低于采集帧率,省带宽)

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
#  服务器
# ============================================================
HOST = "0.0.0.0"
PORT = 8000
