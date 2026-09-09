#!/usr/bin/env python3
"""Tier 2: resolve deterministic async sensor guards by transition priority."""

import asyncio
from collections.abc import Sequence

from fast_fsm import AsyncCondition, AsyncStateMachine, State


class ScriptedSensor:
    """Return a deterministic sequence while retaining an async adapter boundary."""

    def __init__(self, readings: Sequence[float]) -> None:
        self._readings = iter(readings)

    async def read(self) -> float:
        await asyncio.sleep(0)
        return next(self._readings)


class ReadingAtLeast(AsyncCondition):
    __slots__ = ("sensor", "minimum")

    def __init__(self, sensor: ScriptedSensor, minimum: float, name: str) -> None:
        super().__init__(name)
        self.sensor = sensor
        self.minimum = minimum

    async def check_async(self, **_context: object) -> bool:
        reading = await self.sensor.read()
        print(f"guard={self.name} reading={reading}")
        return reading >= self.minimum


async def main() -> None:
    monitor = State("Monitoring")
    machine = AsyncStateMachine(monitor, name="SensorMonitor")
    machine.add_state(State("Warning"))
    machine.add_state(State("Critical"))

    critical = ReadingAtLeast(ScriptedSensor([70, 95]), 90, "critical")
    warning = ReadingAtLeast(ScriptedSensor([70]), 60, "warning")
    machine.add_transition(
        "sensor_tick", "Monitoring", "Critical", critical, priority=0
    )
    machine.add_transition("sensor_tick", "Monitoring", "Warning", warning, priority=10)

    result = await machine.trigger_async("sensor_tick")
    print(f"selected={result.to_state} priority={result.priority}")
    machine.reset()
    result = await machine.trigger_async("sensor_tick")
    print(f"selected={result.to_state} priority={result.priority}")


if __name__ == "__main__":
    asyncio.run(main())
