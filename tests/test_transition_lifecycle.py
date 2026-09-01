"""Executable lifecycle contract for real Fast FSM transition objects."""

from dataclasses import dataclass
import logging

import pytest

from fast_fsm.core import CallbackState, StateMachine, TransitionError


class LifecycleRecorder:
    """Record observable callback order without mocking the machine."""

    def __init__(self) -> None:
        self.events: list[str] = []
        self.observer_kwargs: list[dict[str, object]] = []

    def add(self, event: str) -> None:
        self.events.append(event)


class _DestinationEnterFailure(RuntimeError):
    """Distinct sentinel exception retained by identity in the result."""


@dataclass(frozen=True)
class LifecycleProbe:
    """One spec-less lifecycle family reserved for its owning implementation wave."""

    identifier: str
    owner_plan: str
    expectation: str


LIFECYCLE_PROBES = (
    LifecycleProbe("LIFE-01", "17-03", "exact sync/async callback order"),
    LifecycleProbe("LIFE-02", "17-03", "pre-commit failure preserves source"),
    LifecycleProbe("LIFE-03", "17-03", "post-commit failure preserves destination"),
    LifecycleProbe("LIFE-04-adjacency", "17-02", "observers run exactly once"),
    LifecycleProbe("LIFE-04-empty", "17-02", "empty and single observer behavior"),
    LifecycleProbe("LIFE-04-ordering", "17-02", "observer registration ordering"),
    LifecycleProbe("LIFE-05", "17-04", "committed-only history and cancellation"),
    LifecycleProbe("LIFE-06", "17-04", "sync/async semantic parity"),
)


def test_lifecycle_probe_inventory_accounts_for_all_spec_less_families() -> None:
    """Wave 0 records all eight families without pre-implementing later slices."""
    assert [(probe.identifier, probe.owner_plan) for probe in LIFECYCLE_PROBES] == [
        ("LIFE-01", "17-03"),
        ("LIFE-02", "17-03"),
        ("LIFE-03", "17-03"),
        ("LIFE-04-adjacency", "17-02"),
        ("LIFE-04-empty", "17-02"),
        ("LIFE-04-ordering", "17-02"),
        ("LIFE-05", "17-04"),
        ("LIFE-06", "17-04"),
    ]


def test_tracer_destination_enter_failure_commits_and_finalizes_once(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A post-commit state hook failure stops the suffix without losing truth."""
    recorder = LifecycleRecorder()
    failure = _DestinationEnterFailure("destination-secret")

    def source_exit(*_args: object, **_kwargs: object) -> None:
        recorder.add("source-exit")

    def destination_enter(*_args: object, **_kwargs: object) -> None:
        recorder.add("destination-enter")
        raise failure

    source = CallbackState("source", on_exit=source_exit)
    destination = CallbackState("destination", on_enter=destination_enter)
    machine = StateMachine(source, name="lifecycle-tracer")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.enable_history()

    machine.on_enter(
        "destination", lambda *_args, **_kwargs: recorder.add("enter-callback")
    )
    machine.on_trigger(
        "advance", lambda *_args, **_kwargs: recorder.add("trigger-callback")
    )
    machine.after_transition(lambda *_args, **_kwargs: recorder.add("after-transition"))

    def failing_observer(
        trigger: str, from_state: str, error: str, **kwargs: object
    ) -> None:
        assert (trigger, from_state) == ("advance", "source")
        assert "destination-secret" not in error
        recorder.add("observer-one")
        recorder.observer_kwargs.append(dict(kwargs))
        raise RuntimeError("observer-secret")

    def later_observer(
        trigger: str, from_state: str, error: str, **kwargs: object
    ) -> None:
        assert (trigger, from_state) == ("advance", "source")
        assert "destination-secret" not in error
        recorder.add("observer-two")
        recorder.observer_kwargs.append(dict(kwargs))

    machine.on_failed(failing_observer)
    machine.on_failed(later_observer)

    with caplog.at_level(logging.WARNING):
        result = machine.trigger("advance", payload="caller-secret")

    assert recorder.events == [
        "source-exit",
        "destination-enter",
        "observer-one",
        "observer-two",
    ]
    assert recorder.observer_kwargs == [
        {"payload": "caller-secret"},
        {"payload": "caller-secret"},
    ]
    assert result.success is False
    assert result.committed is True
    assert result.stage == "destination-enter"
    assert result.cause is failure
    assert machine.current_state is destination
    assert [
        (record.from_state, record.trigger, record.to_state)
        for record in machine.history
    ] == [("source", "advance", "destination")]
    assert "destination-secret" not in repr(result)
    assert "destination-secret" not in caplog.text
    assert "observer-secret" not in caplog.text

    with pytest.raises(TransitionError) as raised:
        result.raise_if_failed()
    assert raised.value.result is result
    assert raised.value.__cause__ is failure
    assert "destination-secret" not in str(raised.value)
