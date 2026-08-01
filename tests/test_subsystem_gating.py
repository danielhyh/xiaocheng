"""真板外设启用开关与延迟导入的防回归测试。"""

import os
import subprocess
import sys

import pytest

from app import config


@pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
def test_enabled_switch_accepts_true_values(monkeypatch, value):
    monkeypatch.setenv("XIAOCHENG_TEST_SWITCH", value)
    assert config._env_enabled("XIAOCHENG_TEST_SWITCH") is True


@pytest.mark.parametrize("value", ["0", "false", "NO", "off"])
def test_enabled_switch_accepts_false_values(monkeypatch, value):
    monkeypatch.setenv("XIAOCHENG_TEST_SWITCH", value)
    assert config._env_enabled("XIAOCHENG_TEST_SWITCH") is False


def test_enabled_switch_rejects_ambiguous_value(monkeypatch):
    monkeypatch.setenv("XIAOCHENG_TEST_SWITCH", "maybe")
    with pytest.raises(ValueError, match="XIAOCHENG_TEST_SWITCH"):
        config._env_enabled("XIAOCHENG_TEST_SWITCH")


def test_real_startup_with_every_hardware_subsystem_disabled():
    env = os.environ.copy()
    env["XIAOCHENG_MOCK"] = "0"
    for name in (
        "MOTION",
        "SENSING",
        "VISION",
        "AUDIO",
        "LIGHTING",
        "GIMBAL",
        "OBSTACLE",
        "NITRO",
    ):
        env[f"XIAOCHENG_ENABLE_{name}"] = "0"

    script = """
import asyncio
import sys
import app.main as main

assert not any(main.config.SUBSYSTEMS_ENABLED.values())
assert main.motion is None
assert main.sensing is None
assert main.vision is None
assert main.audio is None
assert main.lighting is None
assert main.gimbal is None
assert main.obstacle is None
assert main.nitro is None

for module in (
    'app.drivers.motor.real',
    'app.drivers.adc.real',
    'app.drivers.audio.real',
    'app.drivers.led.real',
    'app.drivers.strip.real',
    'app.drivers.servo.real',
    'app.drivers.ultrasonic.real',
    'app.drivers.camera.real',
):
    assert module not in sys.modules, module

async def verify_lifespan():
    async with main.lifespan(main.app):
        pass

asyncio.run(verify_lifespan())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
