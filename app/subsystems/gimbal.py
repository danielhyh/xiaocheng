"""
subsystems/gimbal.py — 云台子系统

职责:
  - 管理 pan/tilt 双轴舵机
  - 角度映射与限位
  - 平滑移动 (插值)
  - 回中 / 归位
  - 自动追踪接口 (Phase 5 用)

架构位置: 子系统层,上接 dispatcher,下接 servo 驱动。
"""

import asyncio
import logging

from app.drivers.servo import ServoDriver
from app import config

logger = logging.getLogger(__name__)


class GimbalSubsystem:
    """
    摄像头云台子系统。

    Pan (水平): 0-180°, 中位 90°, 左转增大
    Tilt (垂直): 0-180°, 中位 90°, 抬头增大

    支持:
      - 绝对角度设置
      - 相对增量调整 (摇杆映射)
      - 平滑移动
      - 回中
    """

    def __init__(self):
        self._driver = ServoDriver()
        self._pan = 90.0    # 当前水平角度
        self._tilt = 90.0   # 当前垂直角度
        self._smooth_task: asyncio.Task | None = None

    def init(self) -> None:
        self._driver.init()
        self._pan = 90.0
        self._tilt = 90.0
        logger.info("GimbalSubsystem 初始化完成")

    async def handle_command(self, payload: dict) -> dict:
        """
        处理 cmd.gimbal 指令。

        payload 格式:
          { "action": "set",    "data": { "pan": 90, "tilt": 90 } }
          { "action": "move",   "data": { "dx": 5, "dy": -3 } }
          { "action": "center" }
          { "action": "status" }
        """
        action = payload.get("action", "")
        data = payload.get("data", {})

        if action == "set":
            return self._action_set(data)
        elif action == "move":
            return self._action_move(data)
        elif action == "center":
            return await self._action_center()
        elif action == "status":
            return self._get_status()
        else:
            logger.warning(f"未知云台动作: {action}")
            return {"error": f"unknown action: {action}"}

    def _action_set(self, data: dict) -> dict:
        """设置绝对角度"""
        if "pan" in data:
            self._pan = self._clamp_pan(float(data["pan"]))
        if "tilt" in data:
            self._tilt = self._clamp_tilt(float(data["tilt"]))
        self._apply()
        return self._get_status()

    def _action_move(self, data: dict) -> dict:
        """相对增量移动 (摇杆映射)"""
        dx = float(data.get("dx", 0))
        dy = float(data.get("dy", 0))

        # 增量乘以步进系数
        step = config.GIMBAL_STEP
        self._pan = self._clamp_pan(self._pan + dx * step)
        self._tilt = self._clamp_tilt(self._tilt + dy * step)
        self._apply()
        return self._get_status()

    async def _action_center(self) -> dict:
        """平滑回中"""
        await self._smooth_move(90.0, 90.0, duration=0.5)
        return self._get_status()

    def _clamp_pan(self, angle: float) -> float:
        return max(config.GIMBAL_PAN_MIN, min(config.GIMBAL_PAN_MAX, angle))

    def _clamp_tilt(self, angle: float) -> float:
        return max(config.GIMBAL_TILT_MIN, min(config.GIMBAL_TILT_MAX, angle))

    def _apply(self) -> None:
        """将当前角度写入舵机"""
        self._driver.set_angle(config.SERVO_FRONT_PAN_CHANNEL, self._pan)
        self._driver.set_angle(config.SERVO_FRONT_TILT_CHANNEL, self._tilt)

    async def _smooth_move(self, target_pan: float, target_tilt: float,
                           duration: float = 0.5) -> None:
        """平滑移动到目标角度"""
        if self._smooth_task and not self._smooth_task.done():
            self._smooth_task.cancel()

        steps = int(duration / 0.02)  # 50Hz 更新
        if steps < 1:
            steps = 1

        start_pan = self._pan
        start_tilt = self._tilt

        for i in range(1, steps + 1):
            t = i / steps
            # 缓动函数 (ease-in-out)
            t = t * t * (3 - 2 * t)
            self._pan = start_pan + (target_pan - start_pan) * t
            self._tilt = start_tilt + (target_tilt - start_tilt) * t
            self._apply()
            await asyncio.sleep(0.02)

    def set_tracking_target(self, offset_x: float, offset_y: float) -> None:
        """
        自动追踪接口 (Phase 5 用)。

        参数:
            offset_x: 目标在画面中的水平偏移 (-1 ~ 1, 负=左)
            offset_y: 目标在画面中的垂直偏移 (-1 ~ 1, 负=上)
        """
        gain = config.GIMBAL_TRACKING_GAIN
        self._pan = self._clamp_pan(self._pan - offset_x * gain)
        self._tilt = self._clamp_tilt(self._tilt + offset_y * gain)
        self._apply()

    def _get_status(self) -> dict:
        return {
            "pan": round(self._pan, 1),
            "tilt": round(self._tilt, 1),
        }

    @property
    def pan(self) -> float:
        return self._pan

    @property
    def tilt(self) -> float:
        return self._tilt

    def stop_all(self) -> None:
        """断连安全回调"""
        if self._smooth_task and not self._smooth_task.done():
            self._smooth_task.cancel()
            self._smooth_task = None

    def cleanup(self) -> None:
        self.stop_all()
        self._driver.cleanup()
