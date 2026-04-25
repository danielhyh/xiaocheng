"""
business/mode_manager.py — 模式管理器

决定"此刻谁控车"。Phase 2.2 只实现 manual 模式,
其他模式 (avoid/track/nav/voice) 留好枚举占位。
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Mode(str, Enum):
    MANUAL = "manual"
    AVOID = "avoid"      # Phase 4
    TRACK = "track"      # Phase 5
    NAV = "nav"          # Phase 14
    VOICE = "voice"      # Phase 13


class ModeManager:
    """
    全局模式状态机。

    为什么集中管理:
        避免每个子系统各自判断"该不该动"。
        所有人都看 ModeManager 的当前状态,统一权威。
    """

    def __init__(self):
        self._mode = Mode.MANUAL

    @property
    def current(self) -> Mode:
        return self._mode

    def switch(self, target: str) -> Mode:
        """
        切换模式。返回切换后的模式。

        TODO: 后续 Phase 加校验 (如 track 要求 vision 已启动)
        """
        try:
            new_mode = Mode(target)
        except ValueError:
            logger.warning(f"未知模式: {target}, 保持 {self._mode.value}")
            return self._mode

        # Phase 2.2 只允许 manual
        if new_mode != Mode.MANUAL:
            logger.info(f"模式 {new_mode.value} 尚未实现, 保持 manual")
            return self._mode

        old = self._mode
        self._mode = new_mode
        logger.info(f"模式切换: {old.value} → {new_mode.value}")
        return self._mode

    def force_manual(self, reason: str) -> None:
        """安全降级: 强制切回 manual"""
        old = self._mode
        self._mode = Mode.MANUAL
        logger.warning(f"安全降级 → manual (原因: {reason}, 原模式: {old.value})")
