"""Executable lifecycle contract for real Fast FSM transition objects."""

from dataclasses import dataclass
import asyncio
import logging

import pytest

from fast_fsm.conditions import AsyncCondition, Condition
from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    CallbackState,
    DeclarativeState,
    State,
    StateMachine,
    TransitionError,
    TransitionResult,
    transition,
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


class _BlockingAsyncCondition(AsyncCondition):
    """Coordinate guard cancellation without relying on timing sleeps."""

    def __init__(self, started: asyncio.Event, release: asyncio.Event) -> None:
        super().__init__("blocking-guard", "lifecycle cancellation guard")
        self._started = started
        self._release = release
        self.cancellation: asyncio.CancelledError | None = None

    async def check_async(self, **kwargs: object) -> bool:
        self._started.set()
        try:
            await self._release.wait()
        except asyncio.CancelledError as cancellation:
            self.cancellation = cancellation
            raise
        return True


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


def test_sync_lifecycle_runs_the_locked_order_and_preserves_registration_order() -> (
    None
):
    """One successful sync trigger visits every callback slot in its public order."""
    events: list[str] = []

    class Source(DeclarativeState):
        __slots__ = ("events",)

        def __init__(self) -> None:
            self.events = events
            super().__init__("source")

        def on_exit(
            self, to_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            self.events.append("source-exit")

        @transition("advance")
        def advance(self, *args: object, **kwargs: object) -> None:
            self.events.append("declarative-handler")

    source = Source()
    destination = CallbackState(
        "destination",
        on_enter=lambda *_args, **_kwargs: events.append("destination-enter"),
    )
    machine = StateMachine(source, name="sync-lifecycle-order")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.enable_history()

    class Listener:
        def __init__(self, suffix: str) -> None:
            self._suffix = suffix

        def before_transition(self, *_args: object, **_kwargs: object) -> None:
            events.append(f"before-{self._suffix}")

        def on_exit_state(self, *_args: object, **_kwargs: object) -> None:
            events.append(f"exit-listener-{self._suffix}")

        def on_enter_state(self, *_args: object, **_kwargs: object) -> None:
            events.append(f"enter-listener-{self._suffix}")

        def after_transition(self, *_args: object, **_kwargs: object) -> None:
            events.append(f"after-{self._suffix}")

    machine.add_listener(Listener("one"), Listener("two"))
    machine.on_exit(
        "source", lambda *_args, **_kwargs: events.append("source-callback-one")
    )
    machine.on_exit(
        "source", lambda *_args, **_kwargs: events.append("source-callback-two")
    )
    machine.on_enter(
        "destination",
        lambda *_args, **_kwargs: events.append("destination-callback-one"),
    )
    machine.on_enter(
        "destination",
        lambda *_args, **_kwargs: events.append("destination-callback-two"),
    )
    machine.on_trigger(
        "advance", lambda *_args, **_kwargs: events.append("trigger-callback-one")
    )
    machine.on_trigger(
        "advance", lambda *_args, **_kwargs: events.append("trigger-callback-two")
    )

    result = machine.trigger("advance", payload="caller-payload")

    assert result == TransitionResult(
        True,
        from_state="source",
        to_state="destination",
        trigger="advance",
        committed=True,
    )
    assert events == [
        "before-one",
        "before-two",
        "source-exit",
        "source-callback-one",
        "source-callback-two",
        "exit-listener-one",
        "exit-listener-two",
        "destination-enter",
        "destination-callback-one",
        "destination-callback-two",
        "enter-listener-one",
        "enter-listener-two",
        "declarative-handler",
        "trigger-callback-one",
        "trigger-callback-two",
        "after-one",
        "after-two",
    ]
    assert [
        (item.from_state, item.trigger, item.to_state) for item in machine.history
    ] == [("source", "advance", "destination")]


@pytest.mark.parametrize(
    ("failing_stage", "expected_committed"),
    (
        ("before-transition", False),
        ("source-exit", False),
        ("source-exit-callback", False),
        ("exit-state-listener", False),
        ("destination-enter", True),
        ("destination-enter-callback", True),
        ("enter-state-listener", True),
        ("trigger-callback", True),
        ("after-transition", True),
    ),
)
def test_sync_lifecycle_callback_failure_stops_the_suffix_at_its_stage(
    failing_stage: str, expected_committed: bool
) -> None:
    """Every synchronous callback slot yields one truthful fail-fast result."""
    events: list[str] = []
    failure = RuntimeError(f"{failing_stage}-secret")

    def callback(stage: str):
        def run(*_args: object, **_kwargs: object) -> None:
            events.append(stage)
            if stage == failing_stage:
                raise failure

        return run

    source = CallbackState("source", on_exit=callback("source-exit"))
    destination = CallbackState("destination", on_enter=callback("destination-enter"))
    machine = StateMachine(source, name=f"sync-{failing_stage}")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.enable_history()

    class Listener:
        def before_transition(self, *_args: object, **_kwargs: object) -> None:
            callback("before-transition")()

        def on_exit_state(self, *_args: object, **_kwargs: object) -> None:
            callback("exit-state-listener")()

        def on_enter_state(self, *_args: object, **_kwargs: object) -> None:
            callback("enter-state-listener")()

        def after_transition(self, *_args: object, **_kwargs: object) -> None:
            callback("after-transition")()

    machine.add_listener(Listener())
    machine.on_exit("source", callback("source-exit-callback"))
    machine.on_enter("destination", callback("destination-enter-callback"))
    machine.on_trigger("advance", callback("trigger-callback"))
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("observer"))

    result = machine.trigger("advance")

    assert result.success is False
    assert result.committed is expected_committed
    assert result.stage == failing_stage
    assert result.cause is failure
    assert observed == ["observer"]
    assert machine.current_state is (destination if expected_committed else source)
    assert len(machine.history) == int(expected_committed)
    assert events[-1] == failing_stage


@pytest.mark.parametrize(
    ("outcome", "expected_cause"),
    (
        (False, None),
        (TransitionResult(False, error="handler-result-secret"), None),
        ("invalid", None),
        (RuntimeError("handler-exception-secret"), "exception"),
    ),
)
def test_sync_declarative_failure_is_postcommit_and_finalized_once(
    outcome: object, expected_cause: str | None
) -> None:
    """Ordinary declarative outcomes control the transition completion once."""
    invocations: list[str] = []

    class Source(DeclarativeState):
        __slots__ = ()

        @transition("advance")
        def advance(self, *args: object, **kwargs: object) -> object:
            invocations.append("handler")
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

    source = Source("source")
    destination = State("destination")
    machine = StateMachine(source, name="sync-declarative-failure")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.enable_history()
    observer_calls: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observer_calls.append("observer"))

    result = machine.trigger("advance")

    assert invocations == ["handler"]
    assert result.success is False
    assert result.committed is True
    assert result.stage == "declarative-handler"
    assert result.cause is (outcome if expected_cause is not None else None)
    assert machine.current_state is destination
    assert len(machine.history) == 1
    assert observer_calls == ["observer"]


@pytest.mark.asyncio
async def test_async_lifecycle_awaits_callbacks_at_their_matching_slots() -> None:
    """Async callbacks run beside, rather than after, their synchronous slot."""
    events: list[str] = []

    class Source(AsyncDeclarativeState):
        __slots__ = ()

        def on_exit(
            self, to_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            events.append("source-exit")

        @transition("advance")
        async def advance(self, *args: object, **kwargs: object) -> None:
            events.append("declarative-handler")

    source = Source("source")
    destination = CallbackState(
        "destination",
        on_enter=lambda *_args, **_kwargs: events.append("destination-enter"),
    )
    machine = AsyncStateMachine(source, name="async-lifecycle-order")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.on_exit("source", lambda *_args, **_kwargs: events.append("exit-sync"))

    async def exit_async(*_args: object, **_kwargs: object) -> None:
        events.append("exit-async")

    async def enter_async(*_args: object, **_kwargs: object) -> None:
        events.append("enter-async")

    machine.on_exit_async("source", exit_async)
    machine.on_enter(
        "destination", lambda *_args, **_kwargs: events.append("enter-sync")
    )
    machine.on_enter_async("destination", enter_async)
    machine.on_trigger(
        "advance", lambda *_args, **_kwargs: events.append("trigger-callback")
    )
    machine.after_transition(
        lambda *_args, **_kwargs: events.append("after-transition")
    )

    result = await machine.trigger_async("advance", "positional", payload="caller")

    assert result.success is True
    assert events == [
        "source-exit",
        "exit-sync",
        "exit-async",
        "destination-enter",
        "enter-sync",
        "enter-async",
        "declarative-handler",
        "trigger-callback",
        "after-transition",
    ]


@pytest.mark.asyncio
async def test_async_callback_failure_is_the_matching_staged_result() -> None:
    """An awaited async callback fails fast without an after-the-fact suffix."""
    source = State("source")
    destination = State("destination")
    machine = AsyncStateMachine(source, name="async-callback-failure")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    machine.enable_history()
    failure = RuntimeError("async-callback-secret")
    events: list[str] = []

    async def exit_async(*_args: object, **_kwargs: object) -> None:
        events.append("exit-async")
        raise failure

    machine.on_exit_async("source", exit_async)
    machine.on_trigger(
        "advance", lambda *_args, **_kwargs: events.append("trigger-callback")
    )
    machine.on_failed(lambda *_args, **_kwargs: events.append("observer"))

    result = await machine.trigger_async("advance")

    assert result.success is False
    assert result.stage == "source-exit-callback"
    assert result.committed is False
    assert result.cause is failure
    assert machine.current_state is source
    assert machine.history == []
    assert events == ["exit-async", "observer"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("boundary", "expected_stage", "expected_committed"),
    (
        ("guard", "guard", False),
        ("source-exit", "source-exit-callback", False),
        ("destination-enter", "destination-enter-callback", True),
        ("declarative-handler", "declarative-handler", True),
    ),
)
async def test_async_cancellation_finalizes_once_at_the_reached_boundary(
    boundary: str, expected_stage: str, expected_committed: bool
) -> None:
    """Cancellation preserves its identity, commits only when reached, and stops.

    Every wait is coordinated through an event handshake: no timing assumption is
    permitted in the cancellation contract.
    """
    started = asyncio.Event()
    release = asyncio.Event()
    events: list[str] = []
    observed_cancellation: list[asyncio.CancelledError] = []

    async def block(label: str) -> None:
        events.append(label)
        started.set()
        try:
            await release.wait()
        except asyncio.CancelledError as cancellation:
            observed_cancellation.append(cancellation)
            raise

    if boundary == "declarative-handler":

        class Source(AsyncDeclarativeState):
            __slots__ = ()

            @transition("advance")
            async def advance(self, *args: object, **kwargs: object) -> None:
                await block("declarative-handler")

        source: State = Source("source")
        condition = None
    else:
        source = State("source")
        condition = (
            _BlockingAsyncCondition(started, release) if boundary == "guard" else None
        )
    destination = State("destination")
    machine = AsyncStateMachine(source, name=f"cancel-{boundary}")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination", condition)
    machine.enable_history()
    if boundary == "source-exit":

        async def source_exit(*_args: object, **_kwargs: object) -> None:
            await block("source-exit")

        machine.on_exit_async("source", source_exit)
    if boundary == "destination-enter":

        async def destination_enter(*_args: object, **_kwargs: object) -> None:
            await block("destination-enter")

        machine.on_enter_async("destination", destination_enter)
    machine.on_trigger(
        "advance", lambda *_args, **_kwargs: events.append("trigger-callback")
    )
    machine.after_transition(
        lambda *_args, **_kwargs: events.append("after-transition")
    )
    observer_events: list[tuple[str, str, str]] = []
    machine.on_failed(
        lambda trigger, from_state, error, **_kwargs: observer_events.append(
            (trigger, from_state, error)
        )
    )
    machine.on_failed(
        lambda trigger, from_state, error, **_kwargs: observer_events.append(
            (trigger, from_state, error)
        )
    )

    pending = asyncio.create_task(machine.trigger_async("advance"))
    await started.wait()
    pending.cancel()
    with pytest.raises(asyncio.CancelledError) as raised:
        await pending

    if boundary == "guard":
        assert condition is not None
        assert isinstance(condition, _BlockingAsyncCondition)
        assert condition.cancellation is raised.value
    else:
        assert observed_cancellation == [raised.value]
    assert observer_events == [
        ("advance", "source", f"Transition cancelled at {expected_stage}"),
        ("advance", "source", f"Transition cancelled at {expected_stage}"),
    ]
    assert machine.current_state is (destination if expected_committed else source)
    assert len(machine.history) == int(expected_committed)
    assert "trigger-callback" not in events
    assert "after-transition" not in events


@pytest.mark.asyncio
async def test_async_failure_observer_cancellation_cannot_replace_the_cause() -> None:
    """Observer cancellation stays local to one ordinary callback failure."""
    source = State("source")
    destination = State("destination")
    machine = AsyncStateMachine(source, name="observer-cancellation")
    machine.add_state(destination)
    machine.add_transition("advance", "source", "destination")
    failure = RuntimeError("ordinary-callback-secret")
    observed: list[str] = []

    async def failing_callback(*_args: object, **_kwargs: object) -> None:
        raise failure

    def cancelling_observer(*_args: object, **_kwargs: object) -> None:
        observed.append("cancelling-observer")
        raise asyncio.CancelledError("observer-cancellation-secret")

    def later_observer(*_args: object, **_kwargs: object) -> None:
        observed.append("later-observer")

    machine.on_exit_async("source", failing_callback)
    machine.on_failed(cancelling_observer)
    machine.on_failed(later_observer)

    result = await machine.trigger_async("advance")

    assert result.success is False
    assert result.stage == "source-exit-callback"
    assert result.cause is failure
    assert observed == ["cancelling-observer", "later-observer"]
