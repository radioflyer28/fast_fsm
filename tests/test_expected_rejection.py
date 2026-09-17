"""Requirement-labelled oracle for expected domain transition rejection."""

from __future__ import annotations

import logging

import pytest

from fast_fsm import (
    DeclarativeState,
    AsyncCondition,
    AsyncDeclarativeState,
    AsyncStateMachine,
    State,
    StateMachine,
    TransitionError,
    TransitionRejected,
    TransitionResult,
    transition,
)


@pytest.mark.parametrize(
    "code",
    [
        "a",
        "a" * 64,
        "mission.altitude_limit",
        "battery.low",
        "link-lost",
    ],
)
def test_reject_01_public_signal_constructs_valid_exact_codes(code: str) -> None:
    """REJECT-01: a bounded exact code is the only public signal payload."""
    signal = TransitionRejected(code)

    assert signal.code == code
    with pytest.raises(AttributeError):
        signal.code = "other"  # type: ignore[misc]


class _StringSubclass(str):
    pass


@pytest.mark.parametrize(
    ("code", "error_type"),
    [
        (None, TypeError),
        (_StringSubclass("valid"), TypeError),
        ("", ValueError),
        ("a" * 65, ValueError),
        ("Upper", ValueError),
        ("contains space", ValueError),
        ("contains/slash", ValueError),
        ("unicode-λ", ValueError),
    ],
)
def test_reject_01_public_signal_rejects_invalid_codes(
    code: object, error_type: type[Exception]
) -> None:
    """REJECT-01: the control signal does not coerce or normalize input."""
    with pytest.raises(error_type):
        TransitionRejected(code)  # type: ignore[arg-type]


def test_reject_05_result_tail_is_read_only_and_preserves_error_boundary() -> None:
    """REJECT-05: rejection has stable result metadata and uses TransitionError."""
    rejected = TransitionResult(
        False,
        from_state="armed",
        trigger="takeoff",
        error="Transition rejected: battery.low",
        stage="guard",
        priority=-5,
        internal=True,
        rejection_code="battery.low",
    )
    legacy_equal = TransitionResult(
        False,
        from_state="armed",
        trigger="takeoff",
        error="Transition rejected: battery.low",
        stage="guard",
        priority=-5,
        internal=True,
    )

    assert rejected.rejected is True
    assert rejected.cause is None
    assert rejected.committed is False
    assert rejected.to_state is None
    assert rejected == legacy_equal
    assert "rejection_code='battery.low'" in repr(rejected)
    with pytest.raises(TransitionError) as raised:
        rejected.raise_if_failed()
    assert raised.value.result is rejected

    success = TransitionResult(True)
    assert success.rejected is False
    assert success.raise_if_failed() is success


def test_reject_03_transition_guard_converts_signal_to_terminal_result() -> None:
    """REJECT-03: a transition guard turns the signal into one failed result."""
    source = State("armed")
    target = State("airborne")
    machine = StateMachine(source, name="expected-rejection")
    machine.add_state(target)

    def reject_for_battery() -> bool:
        raise TransitionRejected("battery.low")

    machine.add_transition("takeoff", source, target, reject_for_battery, priority=-5)

    result = machine.trigger("takeoff")

    assert result.success is False
    assert result.rejected is True
    assert result.rejection_code == "battery.low"
    assert result.error == "Transition rejected: battery.low"
    assert result.cause is None
    assert result.committed is False
    assert result.from_state == "armed"
    assert result.to_state is None
    assert result.trigger == "takeoff"
    assert result.stage == "guard"
    assert result.priority == -5
    assert result.internal is False
    assert machine.current_state is source


def test_reject_02_corrupt_signal_stays_an_unexpected_guard_failure() -> None:
    """REJECT-02: conversion revalidates the scalar before exposing it."""
    source = State("armed")
    target = State("airborne")
    machine = StateMachine(source, name="corrupt-expected-rejection")
    machine.add_state(target)
    signal = TransitionRejected("battery.low")
    signal._code = "Upper"  # type: ignore[attr-defined]

    def raise_corrupt_signal() -> bool:
        raise signal

    machine.add_transition("takeoff", source, target, raise_corrupt_signal)

    result = machine.trigger("takeoff")

    assert result.rejected is False
    assert result.rejection_code is None
    assert result.error == "Transition guard raised an exception"
    assert result.cause is signal


@pytest.mark.parametrize(
    "boundary", ("transition_guard", "declarative_guard", "state_permission")
)
@pytest.mark.parametrize("internal", (False, True))
def test_reject_03_approved_boundaries_abort_priority_groups(
    boundary: str, internal: bool
) -> None:
    """REJECT-03/04: each approved seam returns terminal selection metadata."""
    events: list[str] = []
    rejected_name = "source" if internal else "rejected"

    def reject(*_args: object, **_kwargs: object) -> bool:
        events.append(boundary)
        raise TransitionRejected("mission.altitude_limit")

    if boundary == "declarative_guard":

        class Source(DeclarativeState):
            @transition("go", to_state=rejected_name, condition=reject)
            def go(self) -> None:
                raise AssertionError("rejected declarative handler must not run")

        source: State = Source("source")
    elif boundary == "state_permission":

        class Source(State):
            def can_transition(
                self,
                trigger_name: str,
                to_state: State,
                *args: object,
                **kwargs: object,
            ) -> bool:
                if to_state.name == rejected_name:
                    return reject(*args, **kwargs)
                return super().can_transition(trigger_name, to_state, *args, **kwargs)

        source = Source("source")
    else:
        source = State("source")

    rejected = source if internal else State(rejected_name)
    later = State("later")
    machine = StateMachine(source, name=f"expected-rejection-{boundary}-{internal}")
    if not internal:
        machine.add_state(rejected)
    machine.add_state(later)
    machine.enable_history()
    machine.on_exit(source.name, lambda *_args, **_kwargs: events.append("exit"))
    machine.on_enter(rejected.name, lambda *_args, **_kwargs: events.append("enter"))

    def lower_candidate(*_args: object, **_kwargs: object) -> bool:
        events.append("lower-candidate")
        return True

    machine.add_transition(
        "go",
        source,
        rejected,
        reject if boundary == "transition_guard" else None,
        priority=-4,
        internal=internal,
    )
    machine.add_transition("go", source, later, lower_candidate, priority=3)

    result = machine.trigger("go")

    assert result.success is False
    assert result.rejected is True
    assert result.rejection_code == "mission.altitude_limit"
    assert result.error == "Transition rejected: mission.altitude_limit"
    assert result.stage == (
        "state-permission" if boundary == "state_permission" else "guard"
    )
    assert result.priority == -4
    assert result.internal is internal
    assert result.cause is None
    assert result.committed is False
    assert result.to_state is None
    assert machine.current_state is source
    assert machine.history == []
    assert events == [boundary]


def test_reject_04_false_candidate_falls_through_to_terminal_rejection() -> None:
    """REJECT-04: ordinary false advances once, then rejection ends the group."""
    source = State("source")
    rejected = State("rejected")
    later = State("later")
    machine = StateMachine(source, name="false-before-expected-rejection")
    machine.add_state(rejected)
    machine.add_state(later)
    events: list[str] = []

    machine.add_transition(
        "go", source, rejected, lambda: events.append("false") or False, priority=-8
    )

    def reject() -> bool:
        events.append("reject")
        raise TransitionRejected("battery.low")

    machine.add_transition("go", source, rejected, reject, priority=0)
    machine.add_transition(
        "go", source, later, lambda: events.append("later") or True, priority=8
    )

    result = machine.trigger("go")

    assert result.rejected is True
    assert result.rejection_code == "battery.low"
    assert result.priority == 0
    assert result.committed is False
    assert machine.current_state is source
    assert events == ["false", "reject"]


@pytest.mark.asyncio
async def test_reject_04_async_false_candidate_falls_through_to_terminal_rejection() -> (
    None
):
    """REJECT-04: async false advances once without making rejection fall through."""
    source = State("source")
    rejected = State("rejected")
    later = State("later")
    machine = AsyncStateMachine(source, name="async-false-before-rejection")
    machine.add_state(rejected)
    machine.add_state(later)
    events: list[str] = []

    async def false_guard() -> bool:
        events.append("false")
        return False

    async def reject() -> bool:
        events.append("reject")
        raise TransitionRejected("battery.low")

    async def later_guard() -> bool:
        events.append("later")
        return True

    machine.add_transition("go", source, rejected, false_guard, priority=-8)
    machine.add_transition("go", source, rejected, reject, priority=0)
    machine.add_transition("go", source, later, later_guard, priority=8)

    result = await machine.trigger_async("go")

    assert result.rejected is True
    assert result.rejection_code == "battery.low"
    assert result.priority == 0
    assert result.committed is False
    assert machine.current_state is source
    assert events == ["false", "reject"]


def test_reject_07_observers_finalize_once_and_reentry_stays_isolated() -> None:
    """REJECT-07: rejection keeps the existing failure-observer ownership seam."""
    source = State("source")
    target = State("target")
    machine = StateMachine(source, name="expected-rejection-observers")
    machine.add_state(target)
    machine.add_transition(
        "go",
        source,
        target,
        lambda: (_ for _ in ()).throw(TransitionRejected("battery.low")),
    )
    events: list[str] = []

    def failing_observer(*_args: object, **_kwargs: object) -> None:
        events.append("failing")
        raise RuntimeError("observer failure")

    def reentering_observer(*_args: object, **_kwargs: object) -> None:
        with pytest.raises(
            RuntimeError, match=r"^FSM ownership violation: reentrant trigger$"
        ):
            machine.trigger("missing")
        events.append("reentrant")

    machine.on_failed(failing_observer)
    machine.on_failed(reentering_observer)
    machine.on_failed(lambda *_args, **_kwargs: events.append("later"))

    result = machine.trigger("go")

    assert result.rejection_code == "battery.low"
    assert events == ["failing", "reentrant", "later"]


def test_reject_02_logging_uses_only_debug_code_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """REJECT-02: expected control flow does not expose signal or caller reprs."""

    class HostilePayload:
        def __init__(self) -> None:
            self.repr_calls = 0

        def __repr__(self) -> str:
            self.repr_calls += 1
            return "caller-repr-secret"

    class HostileSignal(TransitionRejected):
        def __repr__(self) -> str:
            return "signal-repr-secret"

    source = State("source")
    target = State("target")
    logger_name = "fast_fsm.expected-rejection-logging"
    machine = StateMachine(
        source, name="expected-rejection-logging", logger_name=logger_name
    )
    machine.add_state(target)

    def reject(*_args: object, **_kwargs: object) -> bool:
        raise HostileSignal("link.lost")

    machine.add_transition("go", source, target, reject)
    payload = HostilePayload()

    with caplog.at_level(logging.DEBUG, logger=logger_name):
        result = machine.trigger("go", payload=payload)

    assert result.rejection_code == "link.lost"
    assert payload.repr_calls == 0
    assert any(
        record.levelno == logging.DEBUG and "link.lost" in record.getMessage()
        for record in caplog.records
    )
    assert all(record.levelno < logging.WARNING for record in caplog.records)
    assert "caller-repr-secret" not in caplog.text
    assert "signal-repr-secret" not in caplog.text


@pytest.mark.parametrize(
    ("surface", "stage", "committed"),
    [
        ("source_exit", "source-exit", False),
        ("destination_enter", "destination-enter", True),
    ],
)
def test_reject_09_outside_boundary_lifecycle_signal_stays_an_ordinary_failure(
    surface: str, stage: str, committed: bool
) -> None:
    """REJECT-09: lifecycle signals never use selector-only rejection metadata."""
    signal = TransitionRejected("battery.low")
    events: list[str] = []

    class Source(State):
        def on_exit(
            self, to_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            if surface == "source_exit":
                raise signal
            super().on_exit(to_state, trigger, *args, **kwargs)

    class Destination(State):
        def on_enter(
            self, from_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            if surface == "destination_enter":
                raise signal
            super().on_enter(from_state, trigger, *args, **kwargs)

    source = Source("source")
    destination = Destination("destination")
    fallback = State("fallback")
    machine = StateMachine(source, name=f"outside-boundary-{surface}")
    machine.add_state(destination)
    machine.add_state(fallback)
    machine.enable_history()
    machine.add_transition("go", source, destination, priority=-2)
    machine.add_transition(
        "go",
        source,
        fallback,
        lambda: events.append("fallback") or True,
        priority=4,
    )
    machine.on_failed(lambda *_args, **_kwargs: events.append("observer"))

    result = machine.trigger("go")

    assert result.success is False
    assert result.rejected is False
    assert result.rejection_code is None
    assert result.cause is signal
    assert result.stage == stage
    assert result.committed is committed
    assert result.priority == -2
    assert result.internal is False
    assert result.to_state == ("destination" if committed else None)
    assert machine.current_state is (destination if committed else source)
    assert len(machine.history) == int(committed)
    assert events == ["observer"]


def test_reject_09_timing_signal_stays_an_ordinary_selection_failure() -> None:
    """REJECT-09: timing evaluation is not an approved conversion boundary."""
    signal = TransitionRejected("battery.low")
    source = State("source")
    target = State("target")
    fallback = State("fallback")

    clock_calls = 0

    def reject_clock() -> float:
        nonlocal clock_calls
        clock_calls += 1
        if clock_calls > 1:
            raise signal
        return 0.0

    machine = StateMachine(source, name="outside-boundary-timing", clock=reject_clock)
    machine.add_state(target)
    machine.add_state(fallback)
    machine.enable_history()
    machine.add_transition("go", source, target, after=0)
    machine.add_transition("go", source, fallback, priority=3)

    result = machine.trigger("go")

    assert result.success is False
    assert result.rejected is False
    assert result.rejection_code is None
    assert result.cause is signal
    assert result.stage == "selection"
    assert result.committed is False
    assert result.priority is None
    assert result.internal is False
    assert result.to_state is None
    assert machine.current_state is source
    assert machine.history == []


def test_reject_07_observer_signal_remains_isolated_from_trigger_result() -> None:
    """REJECT-07/09: observer signals cannot relabel an ordinary failure."""
    source = State("source")
    target = State("target")
    original_cause = RuntimeError("guard failure")
    observer_signal = TransitionRejected("battery.low")
    events: list[str] = []
    machine = StateMachine(source, name="outside-boundary-observer")
    machine.add_state(target)
    machine.add_transition(
        "go", source, target, lambda: (_ for _ in ()).throw(original_cause)
    )

    def rejecting_observer(*_args: object, **_kwargs: object) -> None:
        events.append("rejecting-observer")
        raise observer_signal

    machine.on_failed(rejecting_observer)
    machine.on_failed(lambda *_args, **_kwargs: events.append("later-observer"))

    result = machine.trigger("go")

    assert result.success is False
    assert result.rejected is False
    assert result.rejection_code is None
    assert result.cause is original_cause
    assert result.stage == "guard"
    assert events == ["rejecting-observer", "later-observer"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("surface", "expected_stage", "expected_committed"),
    (
        ("source-exit", "source-exit-callback", False),
        ("destination-enter", "destination-enter-callback", True),
        ("declarative-handler", "declarative-handler", True),
    ),
)
async def test_reject_09_async_lifecycle_signal_stays_an_ordinary_failure(
    surface: str, expected_stage: str, expected_committed: bool
) -> None:
    """REJECT-09: async-only lifecycle seams never classify the signal."""
    signal = TransitionRejected(f"lifecycle.{surface}")

    if surface == "declarative-handler":

        class Source(AsyncDeclarativeState):
            @transition("go")
            async def go(self) -> None:
                raise signal

        source: State = Source("source")
    else:
        source = State("source")

    destination = State("destination")
    machine = AsyncStateMachine(source, name=f"async-outside-boundary-{surface}")
    machine.add_state(destination)
    machine.enable_history()
    machine.add_transition("go", source, destination, priority=-3)

    async def reject_from_callback(*_args: object, **_kwargs: object) -> None:
        raise signal

    if surface == "source-exit":
        machine.on_exit_async(source.name, reject_from_callback)
    elif surface == "destination-enter":
        machine.on_enter_async(destination.name, reject_from_callback)

    result = await machine.trigger_async("go")

    assert result.success is False
    assert result.rejected is False
    assert result.rejection_code is None
    assert result.cause is signal
    assert result.stage == expected_stage
    assert result.committed is expected_committed
    assert result.priority == -3
    assert result.to_state == ("destination" if expected_committed else None)
    assert machine.current_state is (destination if expected_committed else source)
    assert len(machine.history) == int(expected_committed)


@pytest.mark.parametrize(
    "boundary", ("transition_guard", "declarative_guard", "state_permission")
)
@pytest.mark.parametrize("topology", ("singleton", "grouped"))
@pytest.mark.parametrize("internal", (False, True))
def test_reject_06_sync_query_stops_at_every_approved_boundary(
    boundary: str, topology: str, internal: bool
) -> None:
    """REJECT-06: a query consumes rejection without finalizing any work."""
    events: list[str] = []
    rejected_name = "source" if internal else "rejected"

    def reject(*_args: object, **_kwargs: object) -> bool:
        events.append(boundary)
        raise TransitionRejected("battery.low")

    if boundary == "declarative_guard":

        class Source(DeclarativeState):
            @transition("go", to_state=rejected_name, condition=reject)
            def go(self) -> None:
                raise AssertionError("a rejected query must not invoke the handler")

        source: State = Source("source")
    elif boundary == "state_permission":

        class Source(State):
            def can_transition(
                self,
                trigger_name: str,
                to_state: State,
                *args: object,
                **kwargs: object,
            ) -> bool:
                if to_state.name == rejected_name:
                    return reject(*args, **kwargs)
                return super().can_transition(trigger_name, to_state, *args, **kwargs)

        source = Source("source")
    else:
        source = State("source")

    rejected = source if internal else State(rejected_name)
    machine = StateMachine(source, name=f"sync-query-{boundary}-{topology}-{internal}")
    if not internal:
        machine.add_state(rejected)
    machine.enable_history()
    machine.add_transition(
        "go",
        source,
        rejected,
        reject if boundary == "transition_guard" else None,
        priority=-2,
        internal=internal,
    )
    if topology == "grouped":
        later = State("later")
        machine.add_state(later)

        def lower_candidate(*_args: object, **_kwargs: object) -> bool:
            events.append("lower")
            return True

        machine.add_transition("go", source, later, lower_candidate, priority=4)
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("failed"))
    machine.on_exit(source.name, lambda *_args, **_kwargs: events.append("exit"))
    machine.on_enter(rejected.name, lambda *_args, **_kwargs: events.append("enter"))

    assert machine.can_trigger("go") is False
    assert events == [boundary]
    assert observed == []
    assert machine.current_state is source
    assert machine.history == []

    result = machine.trigger("go")

    assert result.rejected is True
    assert result.rejection_code == "battery.low"
    assert result.stage == (
        "state-permission" if boundary == "state_permission" else "guard"
    )
    assert result.priority == -2
    assert result.internal is internal
    assert result.committed is False
    assert result.to_state is None
    assert events == [boundary, boundary]
    assert observed == ["failed"]
    assert machine.current_state is source
    assert machine.history == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "boundary", ("transition_guard", "declarative_guard", "state_permission")
)
@pytest.mark.parametrize("topology", ("singleton", "grouped"))
@pytest.mark.parametrize("internal", (False, True))
async def test_reject_06_async_query_stops_at_every_approved_boundary(
    boundary: str, topology: str, internal: bool
) -> None:
    """REJECT-03/04/06/07: async selection shares terminal query semantics."""
    events: list[str] = []
    rejected_name = "source" if internal else "rejected"

    async def reject(*_args: object, **_kwargs: object) -> bool:
        events.append(boundary)
        raise TransitionRejected("battery.low")

    class RejectionCondition(AsyncCondition):
        __slots__ = ()

        def __init__(self) -> None:
            super().__init__("expected-rejection", "raises a domain rejection")

        async def check_async(self, *args: object, **kwargs: object) -> bool:
            return await reject(*args, **kwargs)

    if boundary == "declarative_guard":

        class Source(AsyncDeclarativeState):
            @transition("go", to_state=rejected_name, condition=reject)
            async def go(self) -> None:
                raise AssertionError("a rejected query must not invoke the handler")

        source: State = Source("source")
    elif boundary == "state_permission":

        class Source(State):
            async def can_transition_async(
                self,
                trigger_name: str,
                to_state: State,
                *args: object,
                **kwargs: object,
            ) -> bool:
                if to_state.name == rejected_name:
                    return await reject(*args, **kwargs)
                return self.can_transition(trigger_name, to_state, *args, **kwargs)

        source = Source("source")
    else:
        source = State("source")

    rejected = source if internal else State(rejected_name)
    machine = AsyncStateMachine(
        source, name=f"async-query-{boundary}-{topology}-{internal}"
    )
    if not internal:
        machine.add_state(rejected)
    machine.enable_history()
    machine.add_transition(
        "go",
        source,
        rejected,
        RejectionCondition() if boundary == "transition_guard" else None,
        priority=-2,
        internal=internal,
    )
    if topology == "grouped":
        later = State("later")
        machine.add_state(later)

        async def lower_candidate(*_args: object, **_kwargs: object) -> bool:
            events.append("lower")
            return True

        machine.add_transition("go", source, later, lower_candidate, priority=4)
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("failed"))
    machine.on_exit(source.name, lambda *_args, **_kwargs: events.append("exit"))
    machine.on_enter(rejected.name, lambda *_args, **_kwargs: events.append("enter"))

    assert await machine.can_trigger_async("go") is False
    assert events == [boundary]
    assert observed == []
    assert machine.current_state is source
    assert machine.history == []

    result = await machine.trigger_async("go")

    assert result.rejected is True
    assert result.rejection_code == "battery.low"
    assert result.stage == (
        "state-permission" if boundary == "state_permission" else "guard"
    )
    assert result.priority == -2
    assert result.internal is internal
    assert result.committed is False
    assert result.to_state is None
    assert events == [boundary, boundary]
    assert observed == ["failed"]
    assert machine.current_state is source
    assert machine.history == []
