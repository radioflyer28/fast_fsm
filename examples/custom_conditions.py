#!/usr/bin/env python3
"""Tier 2: write small, reusable domain conditions with clear inputs."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from fast_fsm import Condition, State, StateMachine


class BatteryBelow(Condition):
    """Pass when numeric ``battery_pct`` is below the configured threshold."""

    __slots__ = ("_threshold",)

    def __init__(self, threshold: float) -> None:
        super().__init__("battery_below", f"battery below {threshold}%")
        self._threshold = threshold

    def check(self, *args: Any, **kwargs: Any) -> bool:
        value = kwargs.get("battery_pct")
        return type(value) in (int, float) and value < self._threshold


class HeartbeatOlderThan(Condition):
    """Pass when numeric ``heartbeat_at`` is stale according to an injected clock."""

    __slots__ = ("_clock", "_seconds")

    def __init__(self, seconds: float, clock: Callable[[], float]) -> None:
        super().__init__("heartbeat_stale", f"heartbeat older than {seconds}s")
        self._seconds = seconds
        self._clock = clock

    def check(self, *args: Any, **kwargs: Any) -> bool:
        heartbeat_at = kwargs.get("heartbeat_at")
        return (
            type(heartbeat_at) in (int, float)
            and self._clock() - heartbeat_at >= self._seconds
        )


class PayloadMatches(Condition):
    """Pass when mapping ``payload`` has a string field matching one pattern."""

    __slots__ = ("_field", "_pattern")

    def __init__(self, field: str, pattern: str) -> None:
        super().__init__("payload_matches", f"payload.{field} matches {pattern!r}")
        self._field = field
        self._pattern = re.compile(pattern)

    def check(self, *args: Any, **kwargs: Any) -> bool:
        payload = kwargs.get("payload")
        value = payload.get(self._field) if isinstance(payload, Mapping) else None
        return isinstance(value, str) and self._pattern.fullmatch(value) is not None


class InventoryAvailable(Condition):
    """Pass when mapping ``inventory`` contains at least integer ``quantity``."""

    __slots__ = ("_sku",)

    def __init__(self, sku: str) -> None:
        super().__init__("inventory_available", f"inventory has {sku}")
        self._sku = sku

    def check(self, *args: Any, **kwargs: Any) -> bool:
        inventory = kwargs.get("inventory")
        quantity = kwargs.get("quantity")
        available = inventory.get(self._sku) if isinstance(inventory, Mapping) else None
        return (
            type(quantity) is int and type(available) is int and available >= quantity
        )


def transition_result(machine: StateMachine, trigger: str, **kwargs: Any) -> str:
    """Run one event and return deterministic output for this runnable guide."""
    result = machine.trigger(trigger, **kwargs)
    return f"{trigger}={result.success} destination={machine.current_state.name}"


def main() -> None:
    clock_now = 100.0

    power = StateMachine(State("flying"), name="Power", clock=lambda: clock_now)
    power.add_state(State("landing"))
    power.add_transition("telemetry", "flying", "landing", BatteryBelow(20.0))
    print(transition_result(power, "telemetry", battery_pct=15.0))

    heartbeat = StateMachine(
        State("connected"), name="Heartbeat", clock=lambda: clock_now
    )
    heartbeat.add_state(State("reconnecting"))
    heartbeat.add_transition(
        "tick",
        "connected",
        "reconnecting",
        HeartbeatOlderThan(10.0, clock=lambda: clock_now),
    )
    print(transition_result(heartbeat, "tick", heartbeat_at=85.0))

    parser = StateMachine(State("waiting"), name="Payload")
    parser.add_state(State("accepted"))
    parser.add_transition(
        "receive", "waiting", "accepted", PayloadMatches("kind", "order")
    )
    print(transition_result(parser, "receive", payload={"kind": "order"}))

    warehouse = StateMachine(State("open"), name="Warehouse")
    warehouse.add_state(State("reserved"))
    warehouse.add_transition(
        "reserve", "open", "reserved", InventoryAvailable("widget")
    )
    print(transition_result(warehouse, "reserve", inventory={"widget": 3}, quantity=2))


if __name__ == "__main__":
    main()
