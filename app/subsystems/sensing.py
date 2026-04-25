"""
subsystems/sensing.py — 传感器子系统

职责: 汇总传感器数据 (电池电压、CPU 温度等)。
不感知 I2C 细节,只依赖 ADCDriver 接口。

Phase 2.pre: ADS1115 电池电压 (真实值)
             CPU 温度 / WiFi RSSI (系统读取)
"""

import logging

from app.drivers.adc import ADCDriver
from app import config

logger = logging.getLogger(__name__)


class SensingSubsystem:
    """传感器子系统: ADC 电压 + 系统信息"""

    def __init__(self):
        self._adc = ADCDriver()

    def init(self) -> None:
        self._adc.init()
        logger.info("SensingSubsystem 初始化完成")

    def read_battery(self) -> dict:
        """
        读取电池状态。

        返回:
            {
                "voltage": 7.95,       # 真实电池电压 (V)
                "percent": 81,         # 电量百分比 (0-100)
                "level": "ok"          # "ok" / "low" / "critical"
            }
        """
        try:
            adc_voltage = self._adc.read_voltage(config.ADS1115_CHANNEL)
            battery_voltage = round(adc_voltage * config.BATTERY_DIVIDER_RATIO, 2)
        except Exception as e:
            logger.warning(f"ADC 读取失败: {e}")
            return {
                "voltage": 0.0,
                "percent": 0,
                "level": "unknown",
            }

        # 电量百分比: 线性映射 CRITICAL ~ FULL → 0% ~ 100%
        v_range = config.BATTERY_FULL - config.BATTERY_CRITICAL
        if v_range > 0:
            percent = (battery_voltage - config.BATTERY_CRITICAL) / v_range * 100
            percent = max(0, min(100, round(percent)))
        else:
            percent = 0

        # 电量等级
        if battery_voltage <= config.BATTERY_CRITICAL:
            level = "critical"
        elif battery_voltage <= config.BATTERY_LOW:
            level = "low"
        else:
            level = "ok"

        return {
            "voltage": battery_voltage,
            "percent": percent,
            "level": level,
        }

    def _read_cpu_temp(self) -> float | None:
        """读取 CPU 温度 (°C),失败返回 None"""
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
