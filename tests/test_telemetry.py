import asyncio
import os

os.environ["XIAOCHENG_MOCK"] = "1"

import pytest

from app import config
from app.business.telemetry import TelemetryPublisher


class FakeMotion:
    @property
    def telemetry(self) -> dict:
        return {"speed": 0}


class FakeSensing:
    @property
    def telemetry(self) -> dict:
        return {"battery_voltage": 8.0}


@pytest.mark.asyncio
async def test_each_connection_receives_independent_telemetry(monkeypatch):
    monkeypatch.setattr(config, "TELEMETRY_MOTION_INTERVAL", 0.005)
    monkeypatch.setattr(config, "TELEMETRY_SENSORS_INTERVAL", 0.005)

    publisher = TelemetryPublisher(FakeMotion(), FakeSensing())
    first_messages: list[dict] = []
    second_messages: list[dict] = []

    async def send_first(message: dict) -> None:
        first_messages.append(message)

    async def send_second(message: dict) -> None:
        second_messages.append(message)

    first_task = asyncio.create_task(publisher.run(send_first))
    second_task = asyncio.create_task(publisher.run(send_second))
    await asyncio.sleep(0.025)

    first_task.cancel()
    second_task.cancel()
    await asyncio.gather(first_task, second_task, return_exceptions=True)

    assert {message["type"] for message in first_messages} == {
        "tel.motion", "tel.sensors",
    }
    assert {message["type"] for message in second_messages} == {
        "tel.motion", "tel.sensors",
    }
    assert first_messages is not second_messages
