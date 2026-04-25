import os

os.environ["XIAOCHENG_MOCK"] = "1"

from app.business.dispatcher import Dispatcher
from app.business.mode_manager import ModeManager
from app.subsystems.motion import MotionSubsystem


def test_cmd_brake_dispatches_to_motion_brake():
    motion = MotionSubsystem()
    mode_manager = ModeManager()
    dispatcher = Dispatcher(motion, mode_manager)

    motion.init()
    motion.handle_command(0.5, 0.8)

    reply = dispatcher.dispatch({
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


def test_cmd_brake_temporarily_suppresses_stale_motion():
    motion = MotionSubsystem()
    mode_manager = ModeManager()
    dispatcher = Dispatcher(motion, mode_manager)

    motion.init()
    dispatcher.dispatch({"type": "cmd.brake", "payload": {}})
    dispatcher.dispatch({"type": "cmd.motion", "payload": {"vx": 0, "vy": 1}})

    state = motion.telemetry
    assert state["speed"] == 0
    assert state["direction"] == "idle"
    assert state["left_speed"] == 0
    assert state["right_speed"] == 0
    motion.cleanup()
