"""Executable lifecycle contract for real Fast FSM transition objects."""

from dataclasses import dataclass
import asyncio
import logging

import pytest

from fast_fsm.conditions import Condition
from fast_fsm.core import (
    AsyncStateMachine,
    CallbackState,
    State,
    StateMachine,
    TransitionError,
)


class LifecycleRecorder:
    """Record observable callback order without mocking the machine."""

    def __init__(self) -> None:
        self.events: list[str] = []
        self.observer_kwargs: list[dict[str, object]] = []

    def add(self, event: str) -> None:
        self.events.append(event)


class _DestinationEnterFailure(RuntimeError):
    """Distinct sentinel exception retained by identity in the result."""


class _ResultCondition(Condition):
    """Return or raise one configured guard outcome for lifecycle tests."""

    def __init__(self, outcome: bool | BaseException) -> None:
        super().__init__("lifecycle-guard", "lifecycle test guard")
        self._outcome = outcome

    def check(self, *args: object, **kwargs: object) -> bool:
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


class _PermissionState(State):
    """State policy with a configurable synchronous permission outcome."""

    __slots__ = ("_outcome",)

    def __init__(self, name: str, outcome: bool | BaseException) -> None:
        super().__init__(name)
        self._outcome = outcome

    def can_transition(
        self, trigger: str, to_state: State, *args: object, **kwargs: object
    ) -> bool:
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


class _AsyncPermissionState(State):
    """State policy with a configurable asynchronous permission outcome."""

    __slots__ = ("_outcome",)

    def __init__(self, name: str, outcome: bool | BaseException) -> None:
        super().__init__(name)
        self._outcome = outcome

    async def can_transition_async(
        self, trigger: str, to_state: State, *args: object, **kwargs: object
    ) -> bool:
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


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


@pytest.mark.parametrize(
    ("family", "outcome", "expected_stage", "expected_cause"),
    (
        ("resolution", None, "resolution", None),
        ("guard-false", False, "guard", None),
        (
            "guard-raises",
            RuntimeError("guard-secret"),
            "guard",
            "guard-secret",
        ),
        ("permission-false", False, "state-permission", None),
        (
            "permission-raises",
            RuntimeError("permission-secret"),
            "state-permission",
            "permission-secret",
        ),
    ),
)
def test_precommit_failures_are_truthful_and_finalize_once(
    family: str,
    outcome: bool | BaseException | None,
    expected_stage: str,
    expected_cause: str | None,
) -> None:
    """Every synchronous preparation failure uses one pre-commit result seam."""
    if family == "resolution":
        source = State("source")
        machine = StateMachine(source, name=f"{family}-lifecycle")
        trigger = "missing"
        expected = None
    elif family.startswith("guard"):
        source = State("source")
        machine = StateMachine(source, name=f"{family}-lifecycle")
        machine.add_state(State("destination"))
        machine.add_transition(
            "advance", "source", "destination", _ResultCondition(outcome)
        )
        trigger = "advance"
        expected = outcome if isinstance(outcome, BaseException) else None
    else:
        source = _PermissionState("source", outcome)
        machine = StateMachine(source, name=f"{family}-lifecycle")
        machine.add_state(State("destination"))
        machine.add_transition("advance", "source", "destination")
        trigger = "advance"
        expected = outcome if isinstance(outcome, BaseException) else None

    machine.enable_history()
    observed: list[tuple[str | None, str | None, str, dict[str, object]]] = []
    machine.on_failed(
        lambda observed_trigger, from_state, error, **kwargs: observed.append(
            (observed_trigger, from_state, error, dict(kwargs))
        )
    )

    result = machine.trigger(trigger, payload="caller-payload")

    assert result.success is False
    assert result.committed is False
    assert result.stage == expected_stage
    assert result.cause is expected
    assert machine.current_state is source
    assert machine.history == []
    assert observed == [
        (trigger, "source", result.error, {"payload": "caller-payload"})
    ]
    if expected_cause is not None:
        assert expected_cause not in result.error


def test_failure_observers_continue_after_baseexceptions_without_recursion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Observer failures cannot replace a preparation result or skip later observers."""
    machine = StateMachine(State("source"), name="observer-isolation")
    observer_events: list[str] = []

    def failing_observer(name: str, error: BaseException):
        def observer(*_args: object, **_kwargs: object) -> None:
            observer_events.append(name)
            raise error

        return observer

    machine.on_failed(failing_observer("runtime", RuntimeError("runtime-secret")))
    machine.on_failed(
        failing_observer("cancel", asyncio.CancelledError("cancel-secret"))
    )
    machine.on_failed(
        failing_observer("interrupt", KeyboardInterrupt("interrupt-secret"))
    )
    machine.on_failed(failing_observer("exit", SystemExit("exit-secret")))
    machine.on_failed(lambda *_args, **_kwargs: observer_events.append("later"))

    with caplog.at_level(logging.WARNING):
        result = machine.trigger("missing", payload="caller-payload")

    assert result.success is False
    assert result.stage == "resolution"
    assert result.cause is None
    assert observer_events == ["runtime", "cancel", "interrupt", "exit", "later"]
    for secret in (
        "runtime-secret",
        "cancel-secret",
        "interrupt-secret",
        "exit-secret",
        "caller-payload",
    ):
        assert secret not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("family", "outcome", "expected_stage", "expected_cause"),
    (
        ("resolution", None, "resolution", None),
        ("guard-false", False, "guard", None),
        (
            "guard-raises",
            RuntimeError("async-guard-secret"),
            "guard",
            "async-guard-secret",
        ),
        ("permission-false", False, "state-permission", None),
        (
            "permission-raises",
            RuntimeError("async-permission-secret"),
            "state-permission",
            "async-permission-secret",
        ),
    ),
)
async def test_async_precommit_failures_match_the_result_finalizer_contract(
    family: str,
    outcome: bool | BaseException | None,
    expected_stage: str,
    expected_cause: str | None,
) -> None:
    """Async preparation failures preserve the same result and observer contract."""
    if family == "resolution":
        source = State("source")
        machine = AsyncStateMachine(source, name=f"async-{family}-lifecycle")
        trigger = "missing"
        expected = None
    elif family.startswith("guard"):
        source = State("source")
        machine = AsyncStateMachine(source, name=f"async-{family}-lifecycle")
        machine.add_state(State("destination"))
        machine.add_transition(
            "advance", "source", "destination", _ResultCondition(outcome)
        )
        trigger = "advance"
        expected = outcome if isinstance(outcome, BaseException) else None
    else:
        source = _AsyncPermissionState("source", outcome)
        machine = AsyncStateMachine(source, name=f"async-{family}-lifecycle")
        machine.add_state(State("destination"))
        machine.add_transition("advance", "source", "destination")
        trigger = "advance"
        expected = outcome if isinstance(outcome, BaseException) else None

    machine.enable_history()
    observed: list[tuple[str | None, str | None, str, dict[str, object]]] = []
    machine.on_failed(
        lambda observed_trigger, from_state, error, **kwargs: observed.append(
            (observed_trigger, from_state, error, dict(kwargs))
        )
    )

    result = await machine.trigger_async(trigger, payload="caller-payload")

    assert result.success is False
    assert result.committed is False
    assert result.stage == expected_stage
    assert result.cause is expected
    assert machine.current_state is source
    assert machine.history == []
    assert observed == [
        (trigger, "source", result.error, {"payload": "caller-payload"})
    ]
    if expected_cause is not None:
        assert expected_cause not in result.error
