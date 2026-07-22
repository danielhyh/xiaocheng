import os
import asyncio

os.environ["XIAOCHENG_MOCK"] = "1"

import pytest
from app.business.dispatcher import Dispatcher
from app.business.mode_manager import Mode, ModeManager
from app.subsystems.motion import MotionSubsystem


@pytest.mark.asyncio
async def test_cmd_brake_dispatches_to_motion_brake():
    motion = MotionSubsystem()
    mode_manager = ModeManager()
    dispatcher = Dispatcher(motion, mode_manager)

    motion.init()
    motion.handle_command(0.5, 0.8)

    reply = await dispatcher.dispatch({
        "type": "cmd.brake",
        "id": "brake-1",
        "payload": {},
    })

    state = motion.telemetry
    assert state["speed"] == 0
    assert state["direction"] == "idle"
    assert state["left_speed"] == 0
    assert state["right_speed"] == 0
    assert reply is not None
    assert reply["type"] == "event.ack"
    assert reply["id"] == "brake-1"
    assert reply["payload"] == {"braked": True}
    motion.cleanup()


@pytest.mark.asyncio
async def test_cmd_brake_temporarily_suppresses_stale_motion():
    motion = MotionSubsystem()
    mode_manager = ModeManager()
    dispatcher = Dispatcher(motion, mode_manager)

    motion.init()
    await dispatcher.dispatch({"type": "cmd.brake", "payload": {}})
    await dispatcher.dispatch({"type": "cmd.motion", "payload": {"vx": 0, "vy": 1}})

    state = motion.telemetry
    assert state["speed"] == 0
    assert state["direction"] == "idle"
    assert state["left_speed"] == 0
    assert state["right_speed"] == 0
    motion.cleanup()


@pytest.mark.asyncio
async def test_manual_motion_is_ignored_outside_manual_mode():
    class TrackModeManager:
        current = Mode.TRACK

    motion = MotionSubsystem()
    dispatcher = Dispatcher(motion, TrackModeManager())

    motion.init()
    await dispatcher.dispatch({
        "type": "cmd.motion",
        "payload": {"vx": 0, "vy": 1},
    })

    state = motion.telemetry
    assert state["speed"] == 0
    assert state["left_speed"] == 0
    assert state["right_speed"] == 0
    motion.cleanup()
