"""
subsystems/motion.py — 运动子系统

职责: 将归一化 vx/vy 指令映射到四轮差速电机控制。
不感知 GPIO,只依赖 MotorDriver 接口。

坐标约定 (对标摇杆):
    vx: -1 (左) ~ +1 (右)
    vy: -1 (后) ~ +1 (前)
    速度 = sqrt(vx² + vy²), 钳位到 [0, 1]
"""

import math
import logging
import time

from app.drivers.motor import MotorDriver

logger = logging.getLogger(__name__)


class MotionSubsystem:
    """运动子系统: vx/vy → 差速驱动"""

    def __init__(self):
        self._driver = MotorDriver()
        self._vx = 0.0
        self._vy = 0.0
        self._last_cmd_time = 0.0

    def init(self) -> None:
        self._driver.init()
        logger.info("MotionSubsystem 初始化完成")

    def handle_command(self, vx: float, vy: float) -> None:
        """
        处理前端摇杆指令。

        差速转向算法 (arcade drive):
            左轮速度 = vy + vx
            右轮速度 = vy - vx
            归一化到 [-1, 1],再乘以 100 映射到电机百分比。

        为什么用 arcade drive:
            摇杆的 vy 控制前后,vx 控制转向,
            arcade drive 是最直觉的映射方式:
            - 纯推前 (0, 1) → 左右同速前进
            - 纯推右 (1, 0) → 左前右后 = 原地右旋
            - 右前方 (0.5, 0.5) → 左轮快右轮慢 = 右弧线
        """
        self._vx = max(-1.0, min(1.0, vx))
        self._vy = max(-1.0, min(1.0, vy))
        self._last_cmd_time = time.time()

        left = self._vy + self._vx
        right = self._vy - self._vx

        # 如果超出 [-1, 1],等比缩放保持转向比
        max_val = max(abs(left), abs(right), 1.0)
        left /= max_val
        right /= max_val

        self._driver.set_motors(left * 100, right * 100)

    def stop(self) -> None:
        """停车"""
        self._vx = 0
        self._vy = 0
        self._driver.stop()

    def brake(self) -> None:
        """紧急制动"""
        self._vx = 0
        self._vy = 0
        self._driver.brake()

    def cleanup(self) -> None:
        self._driver.cleanup()

    @property
    def telemetry(self) -> dict:
        """返回运动遥测数据"""
        speed = math.sqrt(self._vx ** 2 + self._vy ** 2)
        speed = min(speed, 1.0)

        if speed < 0.1:
            direction = "idle"
        else:
            angle = math.atan2(self._vy, self._vx) * 180 / math.pi
            if 45 < angle <= 135:
                direction = "forward"
            elif -45 < angle <= 45:
                direction = "right"
            elif -135 < angle <= -45:
                direction = "backward"
            else:
                direction = "left"

        return {
            "vx": round(self._vx, 2),
            "vy": round(self._vy, 2),
            "speed": round(speed * 100),
            "direction": direction,
            **self._driver.current_state,
        }
