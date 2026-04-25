"""
tests/test_motion.py — 运动子系统单元测试

在 mock 模式下验证 vx/vy → 差速映射逻辑。
运行: XIAOCHENG_MOCK=1 python -m pytest tests/
"""

import os
import math

# 强制 mock 模式
os.environ["XIAOCHENG_MOCK"] = "1"

from app.subsystems.motion import MotionSubsystem


def test_forward():
    """纯前进: vx=0, vy=1 → 左右同速"""
    m = MotionSubsystem()
    m.init()
    m.handle_command(0, 1)
    state = m.telemetry
    assert state["direction"] == "forward"
    assert state["speed"] == 100
    m.cleanup()


def test_idle():
    """摇杆归中: vx=0, vy=0 → idle"""
    m = MotionSubsystem()
    m.init()
    m.handle_command(0, 0)
    state = m.telemetry
    assert state["direction"] == "idle"
    assert state["speed"] == 0
    m.cleanup()


def test_turn_right():
    """右转: vx=1, vy=0 → 左前右后 (原地右旋)"""
    m = MotionSubsystem()
    m.init()
    m.handle_command(1, 0)
    state = m.telemetry
    assert state["direction"] == "right"
    # arcade drive: left = 0 + 1 = 1, right = 0 - 1 = -1
    assert state["left_speed"] == 100
    assert state["right_speed"] == -100
    m.cleanup()


def test_diagonal():
    """右前方: vx=0.5, vy=0.5 → 左轮快右轮慢"""
    m = MotionSubsystem()
    m.init()
    m.handle_command(0.5, 0.5)
    state = m.telemetry
    # left = 0.5 + 0.5 = 1.0, right = 0.5 - 0.5 = 0.0
    assert state["left_speed"] == 100
    assert state["right_speed"] == 0
    m.cleanup()


def test_stop():
    """stop() 后状态归零"""
    m = MotionSubsystem()
    m.init()
    m.handle_command(0.5, 0.8)
    m.stop()
    state = m.telemetry
    assert state["speed"] == 0
    assert state["direction"] == "idle"
    m.cleanup()


def test_brake():
    """brake() 后运动状态归零"""
    m = MotionSubsystem()
    m.init()
    m.handle_command(0.5, 0.8)
    m.brake()
    state = m.telemetry
    assert state["speed"] == 0
    assert state["direction"] == "idle"
    assert state["left_speed"] == 0
    assert state["right_speed"] == 0
    m.cleanup()
