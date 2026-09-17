"""Requirement-labelled oracle for expected domain transition rejection."""

from __future__ import annotations

import pytest

from fast_fsm import (
    State,
    StateMachine,
    TransitionError,
    TransitionRejected,
    TransitionResult,
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
