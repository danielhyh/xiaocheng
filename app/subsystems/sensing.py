"""
subsystems/sensing.py — 传感器子系统

职责: 汇总传感器数据 (电池电压、CPU 温度等)。
不感知 I2C 细节,只依赖 ADCDriver 接口。

Phase 2.pre: ADS1115 电池电压 (真实值)
             CPU 温度 / WiFi RSSI (系统读取)

滤波策略:
  1. EMA (指数移动平均) 平滑原始电压,消除电机启停造成的瞬时压降/回弹
  2. 百分比限速: 每秒最大下降 N%、上升 M%,避免数字跳动
  3. 启动阶段: 前 N 次采样取均值快速收敛,不会长时间显示错误值
"""

import logging
import time

from app.drivers.adc import ADCDriver
from app import config

logger = logging.getLogger(__name__)


class SensingSubsystem:
    """传感器子系统: ADC 电压 + 系统信息 + EMA 滤波"""

    def __init__(self):
        self._adc = ADCDriver()

        # EMA 滤波状态
        self._ema_voltage: float | None = None       # 平滑后的电池电压
        self._init_samples: list[float] = []          # 启动阶段采样缓冲
        self._ema_ready = False                       # EMA 是否已初始化

        # 百分比限速状态
        self._last_percent: float | None = None       # 上次输出的百分比 (浮点)
        self._last_read_time: float | None = None     # 上次读取时间戳

    def init(self) -> None:
        self._adc.init()
        logger.info("SensingSubsystem 初始化完成 (EMA α=%.2f)", config.BATTERY_EMA_ALPHA)

    def _raw_battery_voltage(self) -> float:
        """读取一次原始电池电压 (经分压还原)"""
        adc_voltage = self._adc.read_voltage(config.ADS1115_CHANNEL)
        return round(adc_voltage * config.BATTERY_DIVIDER_RATIO, 3)

    def _update_ema(self, raw_v: float) -> float:
        """
        更新 EMA 滤波器,返回平滑后的电压。

        启动阶段: 收集 N 个样本取均值作为初始值,避免冷启动偏差。
        稳态阶段: EMA 递推  →  ema = α * raw + (1-α) * ema
        """
        if not self._ema_ready:
            self._init_samples.append(raw_v)
            if len(self._init_samples) >= config.BATTERY_EMA_INIT_SAMPLES:
                self._ema_voltage = sum(self._init_samples) / len(self._init_samples)
                self._ema_ready = True
                self._init_samples.clear()
                logger.info("EMA 初始化完成, 初始电压=%.2fV", self._ema_voltage)
            else:
                # 还没收集够,先返回当前均值
                return sum(self._init_samples) / len(self._init_samples)

        # 稳态 EMA 更新
        alpha = config.BATTERY_EMA_ALPHA
        self._ema_voltage = alpha * raw_v + (1 - alpha) * self._ema_voltage
        return self._ema_voltage

    def _voltage_to_percent(self, voltage: float) -> float:
        """电压 → 百分比 (线性映射, 返回浮点)"""
        v_range = config.BATTERY_FULL - config.BATTERY_CRITICAL
        if v_range <= 0:
            return 0.0
        pct = (voltage - config.BATTERY_CRITICAL) / v_range * 100
        return max(0.0, min(100.0, pct))

    def _rate_limited_percent(self, target_pct: float) -> int:
        """
        对百分比做限速处理,防止跳动。

        - 下降: 每秒最多降 BATTERY_PERCENT_DROP_RATE %
        - 上升: 每秒最多升 BATTERY_PERCENT_RISE_RATE % (极慢，抑制电机停止后的电压回弹)
        """
        now = time.monotonic()

        if self._last_percent is None or self._last_read_time is None:
            # 首次,直接采用
            self._last_percent = target_pct
            self._last_read_time = now
            return round(target_pct)

        dt = now - self._last_read_time
        self._last_read_time = now

        if dt <= 0:
            return round(self._last_percent)

        max_drop = config.BATTERY_PERCENT_DROP_RATE * dt
        max_rise = config.BATTERY_PERCENT_RISE_RATE * dt

        diff = target_pct - self._last_percent

        if diff < 0:
            # 下降: 限制下降速率
            change = max(diff, -max_drop)
        else:
            # 上升: 限制上升速率 (防回弹)
            change = min(diff, max_rise)

        self._last_percent += change
        self._last_percent = max(0.0, min(100.0, self._last_percent))

        return round(self._last_percent)

    def read_battery(self) -> dict:
        """
        读取电池状态 (带 EMA 滤波 + 百分比限速)。

        返回:
            {
                "voltage": 7.95,       # EMA 平滑后的电池电压 (V)
                "percent": 81,         # 限速后的电量百分比 (0-100)
                "level": "ok"          # "ok" / "low" / "critical"
            }
        """
        try:
            raw_v = self._raw_battery_voltage()
            smooth_v = self._update_ema(raw_v)
            smooth_v = round(smooth_v, 2)
        except Exception as e:
            logger.warning(f"ADC 读取失败: {e}")
            return {
                "voltage": 0.0,
                "percent": 0,
                "level": "unknown",
            }

        # 百分比: 先从平滑电压算目标值,再限速
        target_pct = self._voltage_to_percent(smooth_v)
        percent = self._rate_limited_percent(target_pct)

        # 电量等级 (基于平滑电压)
        if smooth_v <= config.BATTERY_CRITICAL:
            level = "critical"
        elif smooth_v <= config.BATTERY_LOW:
            level = "low"
        else:
            level = "ok"

        return {
            "voltage": smooth_v,
            "percent": percent,
            "level": level,
        }

    def _read_cpu_temp(self) -> float | None:
        """读取 CPU 温度 (°C)"""
        if config.USE_MOCK:
            import math
            return round(52 + 3 * math.sin(time.time() / 10), 1)

        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return round(int(f.read().strip()) / 1000.0, 1)
        except Exception:
            return None

    @property
    def telemetry(self) -> dict:
        """返回传感器遥测数据"""
        battery = self.read_battery()
        cpu_temp = self._read_cpu_temp()

        return {
            "battery_voltage": battery["voltage"],
            "battery_percent": battery["percent"],
            "battery_level": battery["level"],
            "cpu_temp": cpu_temp,
        }

    def cleanup(self) -> None:
        self._adc.cleanup()
