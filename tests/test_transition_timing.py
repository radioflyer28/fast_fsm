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
from fast_fsm.core import AsyncDeclarativeState, DeclarativeState, TransitionResult


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


@pytest.mark.parametrize("after, within", [(2, 2), (3, 2)])
def test_empty_timing_windows_are_rejected_atomically(
    after: float, within: float
) -> None:
    clock = FakeClock()
    machine = machine_with_target(clock=clock)

    with pytest.raises(ValueError, match="less than"):
        machine.add_transition("go", "source", "target", after=after, within=within)
    assert machine.triggers == []


def test_invalid_or_regressing_clocks_fail_closed_without_commit() -> None:
    clock = FakeClock()
    machine = machine_with_target(clock=clock)
    machine.add_transition("go", "source", "target", after=1)
    clock.now = -1

    with pytest.raises(ValueError, match="state entry"):
        machine.can_trigger("go")
    result = machine.trigger("go")
    assert not result.success
    assert result.error == "Transition timing is unavailable"
    assert machine.current_state_name == "source"


def test_untimed_singleton_does_not_read_the_clock_during_selection() -> None:
    clock = FakeClock()
    machine = machine_with_target(clock=clock)
    machine.add_transition("go", "source", "target")
    before_query = clock.calls

    assert machine.can_trigger("go")
    assert clock.calls == before_query


def test_legacy_transition_preparation_preserves_resolution_and_guard_context() -> None:
    """The compatibility lookup keeps failures and sanitized guard context distinct."""
    source = State("source")
    machine = StateMachine(source)
    target = State("target")
    alternate = State("alternate")
    machine.add_state(target)
    machine.add_state(alternate)

    missing = machine._resolve_trigger("missing")
    assert isinstance(missing, TransitionResult)
    assert missing.stage == "resolution"

    condition = FuncCondition(lambda **kwargs: bool(kwargs))
    machine.add_transition("guarded", source, target, condition)
    prepared = machine._prepare_transition(
        "guarded", (), {"visible": "yes", "_private": "hidden"}
    )
    assert not isinstance(prepared, TransitionResult)
    assert prepared.condition_kwargs == {"visible": "yes"}
    resolved_entry, resolved_source = machine._resolve_trigger("guarded")
    assert resolved_entry is prepared.entry
    assert resolved_source == "source"

    machine.add_transition("ranked", source, target, priority=0)
    machine.add_transition("ranked", source, alternate, priority=1)
    grouped = machine._resolve_trigger("ranked")
    assert isinstance(grouped, TransitionResult)
    assert grouped.stage == "resolution"


def test_sync_declarative_guard_seam_contains_legacy_query_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Direct compatibility queries get a safe false result and redacted warning."""

    def exploding_guard(*_args: object, **_kwargs: object) -> bool:
        raise ValueError("guard-secret")

    class Source(DeclarativeState):
        @transition("advance", to_state="target", condition=exploding_guard)
        def handle_advance(self) -> None:
            pass

    source = Source("source")
    machine = StateMachine(source)
    machine.add_state(State("target"))
    machine.add_transition("advance", source, "target")
    prepared = machine._prepare_transition("advance", (), {})
    assert not isinstance(prepared, TransitionResult)

    with caplog.at_level("WARNING"):
        assert not machine._evaluate_declarative_condition_sync(prepared)

    assert "Condition evaluation failed" in caplog.text
    assert "type=ValueError" in caplog.text
    assert "guard-secret" not in caplog.text


@pytest.mark.asyncio
async def test_async_declarative_guard_seam_contains_legacy_query_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Async direct compatibility queries get the same safe, redacted false result."""

    async def exploding_guard(*_args: object, **_kwargs: object) -> bool:
        raise ValueError("async-guard-secret")

    class Source(AsyncDeclarativeState):
        @transition("advance", to_state="target", condition=exploding_guard)
        async def handle_advance(self) -> None:
            pass

    source = Source("source")
    machine = AsyncStateMachine(source)
    machine.add_state(State("target"))
    machine.add_transition("advance", source, "target")
    prepared = machine._prepare_transition("advance", (), {})
    assert not isinstance(prepared, TransitionResult)

    with caplog.at_level("WARNING"):
        assert not await machine._evaluate_declarative_condition_async(prepared)

    assert "Async condition evaluation failed" in caplog.text
    assert "type=ValueError" in caplog.text
    assert "async-guard-secret" not in caplog.text


def test_commit_resets_entry_time_before_destination_callback_failure() -> None:
    clock = FakeClock()

    class FailingDestination(State):
        __slots__ = ("machine",)

        def __init__(self) -> None:
            super().__init__("target")
            self.machine: StateMachine | None = None

        def on_enter(self, *args: object, **kwargs: object) -> None:
            assert self.machine is not None
            assert self.machine._state_entered_at == 4
            raise RuntimeError("expected test failure")

    target = FailingDestination()
    machine = StateMachine(State("source"), clock=clock)
    target.machine = machine
    machine.add_state(target)
    machine.add_transition("go", "source", "target")
    clock.now = 4

    result = machine.trigger("go")
    assert not result.success and result.committed
    assert machine.current_state is target
    assert machine._state_entered_at == 4


@pytest.mark.parametrize("control", ("force_state", "reset", "restore"))
def test_direct_controls_leave_state_and_history_unchanged_on_clock_failure(
    control: str,
) -> None:
    """Every direct-control commit reads the injected clock before mutation."""
    failure = OSError("direct-control-clock-failure")
    fail_commit = False

    def clock() -> float:
        if fail_commit:
            raise failure
        return 0.0

    source = State("source")
    destination = State("destination")
    machine = StateMachine(source, clock=clock)
    machine.add_state(destination)
    machine.enable_history()

    if control == "reset":
        machine.add_transition("advance", "source", "destination")
        assert machine.trigger("advance").success
    state_before = machine.current_state
    history_before = machine.history
    fail_commit = True

    with pytest.raises(OSError) as raised:
        if control == "force_state":
            machine.force_state("destination")
        elif control == "reset":
            machine.reset()
        else:
            machine.restore({"state": "destination", "version": 1})

    assert raised.value is failure
    assert machine.current_state is state_before
    assert machine.history == history_before


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


def test_timing_round_trips_and_routes_through_factories_builder_and_decorator() -> (
    None
):
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

    declarative = (
        FSMBuilder(Source("source"), clock=clock)
        .add_state(State("target"))
        .add_transition("go", "source", "target")
        .build()
    )
    clock.now = 1
    for machine in (direct, rebuilt, builder, declarative):
        assert machine.can_trigger("go")
        assert machine.clone()._clock is clock
