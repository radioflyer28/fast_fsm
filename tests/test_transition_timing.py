"""Deterministic transition-entry timing contracts."""

from __future__ import annotations

import math

import pytest

from fast_fsm import (
    AsyncCondition,
    AsyncStateMachine,
    FSMBuilder,
    FuncCondition,
    State,
    StateMachine,
    transition,
)
from fast_fsm.core import DeclarativeState


class FakeClock:
    __slots__ = ("calls", "now")

    def __init__(self, now: float = 0.0) -> None:
        self.now = now
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return self.now


def machine_with_target(*, clock: FakeClock) -> StateMachine:
    machine = StateMachine(State("source"), clock=clock)
    machine.add_state(State("target"))
    return machine


@pytest.mark.parametrize("value", [True, False, -1, math.inf, -math.inf, math.nan])
def test_timing_values_are_rejected_before_topology_mutation(value: object) -> None:
    clock = FakeClock()
    machine = machine_with_target(clock=clock)

    with pytest.raises((TypeError, ValueError)):
        machine.add_transition("go", "source", "target", after=value)
    with pytest.raises((TypeError, ValueError)):
        machine.add_transition("go", "source", "target", within=value)
    assert machine.triggers == []


def test_time_window_is_half_open_and_queries_are_observational() -> None:
    clock = FakeClock()
    machine = machine_with_target(clock=clock)
    machine.add_transition("go", "source", "target", after=2, within=5)

    assert not machine.can_trigger("go")
    clock.now = 2
    assert machine.can_trigger("go")
    assert machine._state_entered_at == 0
    clock.now = 5
    assert not machine.can_trigger("go")


def test_timing_is_checked_before_guards_and_one_clock_sample_serves_group() -> None:
    clock = FakeClock()
    machine = StateMachine(State("source"), clock=clock)
    machine.add_state(State("late"))
    machine.add_state(State("fallback"))
    guard_calls: list[str] = []
    machine.add_transition(
        "go",
        "source",
        "late",
        FuncCondition(lambda: guard_calls.append("late") or True),
        priority=1,
        after=3,
    )
    machine.add_transition(
        "go",
        "source",
        "fallback",
        FuncCondition(lambda: guard_calls.append("fallback") or True),
        priority=2,
    )

    before_query = clock.calls
    assert machine.can_trigger("go")
    assert clock.calls == before_query + 1
    assert guard_calls == ["fallback"]
    assert machine.trigger("go").to_state == "fallback"


@pytest.mark.asyncio
async def test_async_selection_uses_the_same_window_before_awaiting_guards() -> None:
    class AsyncGuard(AsyncCondition):
        __slots__ = ("calls",)

        def __init__(self) -> None:
            super().__init__("async-guard")
            self.calls = 0

        async def check_async(self, *args: object, **kwargs: object) -> bool:
            self.calls += 1
            return True

    clock = FakeClock()
    guard = AsyncGuard()
    machine = AsyncStateMachine(State("source"), clock=clock)
    machine.add_state(State("target"))
    machine.add_transition("go", "source", "target", guard, after=1)

    assert not await machine.can_trigger_async("go")
    assert guard.calls == 0
    clock.now = 1
    assert await machine.can_trigger_async("go")
    assert guard.calls == 1


def test_timing_round_trips_and_routes_through_factories_builder_and_decorator() -> None:
    clock = FakeClock()
    rows = [("go", "source", "target", None, 0, 1, 3)]
    direct = StateMachine.quick_build("source", rows, name="direct", clock=clock)
    rebuilt = StateMachine.from_dict(direct.to_dict(), clock=clock)
    builder = (
        FSMBuilder(State("source"), clock=clock)
        .add_state(State("target"))
        .add_transition("go", "source", "target", after=1, within=3)
        .build()
    )

    class Source(DeclarativeState):
        @transition("go", from_state="source", to_state="target", after=1, within=3)
        def handle(self) -> None:
            pass

    declarative = FSMBuilder(Source("source"), clock=clock).add_state(
        State("target")
    ).build()
    clock.now = 1
    for machine in (direct, rebuilt, builder, declarative):
        assert machine.can_trigger("go")
        assert machine.clone()._clock is clock
