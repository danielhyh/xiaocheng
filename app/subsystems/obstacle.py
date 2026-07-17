"""
subsystems/obstacle.py — 避障子系统

职责:
  - 前方超声波测距 (固定朝前,后续可升级扫描舵机)
  - 后方超声波测距 (仅倒车时启用)
  - 避障决策 (距离 < 阈值 → 停车/告警)
  - 倒车防撞安全联锁
  - 手动/自动模式切换

架构位置: 子系统层,上接 dispatcher/safety,下接 ultrasonic 驱动。
"""

import asyncio
import logging
import time

from app.drivers.ultrasonic import UltrasonicDriver
from app import config

logger = logging.getLogger(__name__)


class ObstacleSubsystem:
    """
    避障子系统。

    后台任务周期性测距,维护最新距离数据。
    safety 层可查询距离做安全决策。
    """

    def __init__(self):
        self._driver = UltrasonicDriver()
        self._front_distance: float | None = None
        self._rear_distance: float | None = None
        self._scan_task: asyncio.Task | None = None
        self._running = False
        self._reversing = False  # 是否正在倒车
        self._front_blocked = False
        self._rear_blocked = False

        # 回调 (由 safety 注入)
        self._on_front_blocked: callable = None
        self._on_rear_blocked: callable = None

    def init(self) -> None:
        self._driver.init()
        logger.info("ObstacleSubsystem 初始化完成")

    def start_scanning(self) -> None:
        """启动后台扫描任务"""
        if self._running:
            return
        self._running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        logger.info("避障扫描已启动")

    def stop_scanning(self) -> None:
        """停止扫描"""
        self._running = False
        if self._scan_task and not self._scan_task.done():
            self._scan_task.cancel()
            self._scan_task = None

    async def _scan_loop(self) -> None:
        """后台扫描循环"""
        loop = asyncio.get_event_loop()
        try:
            while self._running:
                # 前方始终扫描
                front = await loop.run_in_executor(
                    None, self._driver.measure, "front"
                )
                if front is not None:
                    self._front_distance = front
                    was_blocked = self._front_blocked
                    self._front_blocked = front < config.US_FRONT_STOP_DISTANCE
                    if self._front_blocked and not was_blocked:
                        logger.warning(f"前方障碍物! 距离={front:.1f}cm")
                        if self._on_front_blocked:
                            self._on_front_blocked()

                # 后方仅倒车时扫描
                if self._reversing:
                    rear = await loop.run_in_executor(
                        None, self._driver.measure, "rear"
                    )
                    if rear is not None:
                        self._rear_distance = rear
                        was_blocked = self._rear_blocked
                        self._rear_blocked = rear < config.US_REAR_STOP_DISTANCE
                        if self._rear_blocked and not was_blocked:
                            logger.warning(f"后方障碍物! 距离={rear:.1f}cm")
                            if self._on_rear_blocked:
                                self._on_rear_blocked()

                await asyncio.sleep(config.US_SCAN_INTERVAL)
        except asyncio.CancelledError:
            pass

    def set_reversing(self, reversing: bool) -> None:
        """设置倒车状态 (由 dispatcher 调用)"""
        self._reversing = reversing
        if not reversing:
            self._rear_blocked = False
            self._rear_distance = None

    def set_callbacks(self, on_front_blocked=None, on_rear_blocked=None) -> None:
        """注入阻塞回调"""
        self._on_front_blocked = on_front_blocked
        self._on_rear_blocked = on_rear_blocked

    async def handle_command(self, payload: dict) -> dict:
        """
        处理 cmd.obstacle 指令。

        payload 格式:
          { "action": "status" }
          { "action": "scan_start" }
          { "action": "scan_stop" }
        """
        action = payload.get("action", "")

        if action == "status":
            return self._get_status()
        elif action == "scan_start":
            self.start_scanning()
            return {"scanning": True}
        elif action == "scan_stop":
            self.stop_scanning()
            return {"scanning": False}
        else:
            return {"error": f"unknown action: {action}"}

    def _get_status(self) -> dict:
        return {
            "front_distance": self._front_distance,
            "rear_distance": self._rear_distance,
            "front_blocked": self._front_blocked,
            "rear_blocked": self._rear_blocked,
            "scanning": self._running,
        }

    @property
    def front_distance(self) -> float | None:
        return self._front_distance

    @property
    def rear_distance(self) -> float | None:
        return self._rear_distance

    @property
    def front_blocked(self) -> bool:
        return self._front_blocked

    @property
    def rear_blocked(self) -> bool:
        return self._rear_blocked

    @property
    def telemetry(self) -> dict:
        return {
            "front_distance": self._front_distance,
            "rear_distance": self._rear_distance,
            "front_blocked": self._front_blocked,
            "rear_blocked": self._rear_blocked,
        }

    def cleanup(self) -> None:
        self.stop_scanning()
        self._driver.cleanup()
