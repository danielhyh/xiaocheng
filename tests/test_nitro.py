import asyncio
import os

os.environ["XIAOCHENG_MOCK"] = "1"

import pytest

from app import config
from app.subsystems.lighting import LightingSubsystem
from app.subsystems.nitro import NitroSubsystem


@pytest.mark.asyncio
async def test_nitro_uses_public_lighting_effect_and_restores_mode(monkeypatch):
    monkeypatch.setattr(config, "NITRO_DURATION", 0.02)
    monkeypatch.setattr(config, "NITRO_COOLDOWN", 1.0)

    lighting = LightingSubsystem()
    lighting.init()
    await lighting.handle_command({
        "action": "strip_mode",
        "data": {"mode": "tail"},
    })

    nitro = NitroSubsystem()
    nitro.set_dependencies(lighting=lighting)

    result = await nitro.handle_command({"action": "trigger"})
    assert result == {"nitro": "activated", "duration": 0.02}
    assert nitro.is_active is True
    assert (await lighting.handle_command({"action": "status"}))["strip_mode"] == "nitro"

    await asyncio.sleep(0.04)

    status = await nitro.handle_command({"action": "status"})
    light_status = await lighting.handle_command({"action": "status"})
    assert status["active"] is False
    assert status["cooling"] is True
    assert 0 < status["cooldown_remaining"] <= 1.0
    assert light_status["strip_mode"] == "tail"

    lighting.cleanup()


@pytest.mark.asyncio
async def test_unknown_strip_mode_does_not_corrupt_current_mode():
    lighting = LightingSubsystem()
    lighting.init()
    await lighting.handle_command({
        "action": "strip_mode",
        "data": {"mode": "tail"},
    })

    result = await lighting.handle_command({
        "action": "strip_mode",
        "data": {"mode": "not-a-mode"},
    })

    assert result == {"error": "unknown strip mode: not-a-mode"}
    assert (await lighting.handle_command({"action": "status"}))["strip_mode"] == "tail"
    lighting.cleanup()


@pytest.mark.asyncio
async def test_manual_strip_change_is_rejected_while_nitro_is_active():
    lighting = LightingSubsystem()
    lighting.init()
    lighting.start_nitro_effect()

    result = await lighting.handle_command({
        "action": "strip_mode",
        "data": {"mode": "tail"},
    })

    assert result == {"error": "nitro effect is active"}
    assert (await lighting.handle_command({"action": "status"}))["strip_mode"] == "nitro"
    lighting.stop_nitro_effect()
    lighting.cleanup()


@pytest.mark.asyncio
async def test_nitro_can_retrigger_when_derived_cooldown_expires(monkeypatch):
    monkeypatch.setattr(config, "NITRO_DURATION", 0.01)
    monkeypatch.setattr(config, "NITRO_COOLDOWN", 0.03)

    nitro = NitroSubsystem()
    first = await nitro.handle_command({"action": "trigger"})
    assert first["nitro"] == "activated"

    await asyncio.sleep(0.015)
    cooling = await nitro.handle_command({"action": "trigger"})
    assert cooling["nitro"] == "cooling"

    await asyncio.sleep(0.025)
    second = await nitro.handle_command({"action": "trigger"})
    assert second["nitro"] == "activated"
    nitro.stop_all()
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_cancelled_nitro_task_cannot_clear_a_new_trigger(monkeypatch):
    monkeypatch.setattr(config, "NITRO_DURATION", 1.0)
    monkeypatch.setattr(config, "NITRO_COOLDOWN", 0.0)

    nitro = NitroSubsystem()
    await nitro.handle_command({"action": "trigger"})
    nitro.stop_all()
    await nitro.handle_command({"action": "trigger"})
    await asyncio.sleep(0)

    assert nitro.is_active is True
    nitro.stop_all()
    await asyncio.sleep(0)
