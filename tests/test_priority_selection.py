"""Focused synchronous selection contracts for priority candidate groups."""

from __future__ import annotations

import asyncio

import pytest

from fast_fsm.conditions import AsyncCondition, Condition
from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    CallbackState,
    DeclarativeState,
    State,
    StateMachine,
    transition,
)


class _RecordingCondition(Condition):
    """Guard that records its evaluation without mocking the dispatch path."""

    __slots__ = ("_events", "_label", "_outcome", "_payloads")

    def __init__(
        self,
        events: list[str],
        label: str,
        outcome: bool | BaseException,
        payloads: list[tuple[tuple[object, ...], dict[str, object]]],
    ) -> None:
        super().__init__(label, "priority selection test guard")
        self._events = events
        self._label = label
        self._outcome = outcome
        self._payloads = payloads

    def check(self, *args: object, **kwargs: object) -> bool:
        self._events.append(self._label)
        self._payloads.append((args, dict(kwargs)))
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


class _SequentialAsyncCondition(AsyncCondition):
    """Async guard that makes ordered, non-speculative evaluation observable."""

    __slots__ = ("_active", "_events", "_label", "_outcome")

    def __init__(
        self,
        events: list[str],
        active: list[int],
        label: str,
        outcome: bool | BaseException,
    ) -> None:
        super().__init__(label, "priority selection async guard")
        self._active = active
        self._events = events
        self._label = label
        self._outcome = outcome

    async def check_async(self, *args: object, **kwargs: object) -> bool:
        self._active[0] += 1
        try:
            assert self._active[0] == 1
            self._events.append(f"guard:{self._label}")
            await asyncio.sleep(0)
            if isinstance(self._outcome, BaseException):
                raise self._outcome
            return self._outcome
        finally:
            self._active[0] -= 1


class _GatedAsyncCondition(AsyncCondition):
    """Wait for a test-controlled handshake before yielding one guard outcome."""

    __slots__ = ("_events", "_label", "_outcome", "cancellation", "started", "release")

    def __init__(
        self,
        events: list[str],
        label: str,
        outcome: bool,
        started: asyncio.Event,
        release: asyncio.Event,
    ) -> None:
        super().__init__(label, "priority selection async handshake guard")
        self._events = events
        self._label = label
        self._outcome = outcome
        self.cancellation: asyncio.CancelledError | None = None
        self.started = started
        self.release = release

    async def check_async(self, *args: object, **kwargs: object) -> bool:
        self._events.append(f"guard:{self._label}")
        self.started.set()
        try:
            await asyncio.wait_for(self.release.wait(), timeout=5)
        except asyncio.CancelledError as cancellation:
            self.cancellation = cancellation
            raise
        return self._outcome


def test_out_of_order_group_registration_preserves_order_dispatch_identity_and_atomicity() -> (
    None
):
    """Public registration publishes one ordered immutable slot or nothing."""
    source = State("source")
    alternate_source = State("alternate-source")
    lowest = State("lowest")
    middle = State("middle")
    highest = State("highest")
    conflicting = State("conflicting")
    machine = StateMachine(source, name="priority-linear-insertion")
    for state in (alternate_source, lowest, middle, highest, conflicting):
        machine.add_state(state)
    machine.enable_history()

    evaluated: list[str] = []

    class RecordingCondition(Condition):
        __slots__ = ("label", "outcome")

        def __init__(self, label: str, outcome: bool) -> None:
            super().__init__(label, "linear insertion test guard")
            self.label = label
            self.outcome = outcome

        def check(self, *args: object, **kwargs: object) -> bool:
            evaluated.append(self.label)
            return self.outcome

    reject_lowest = RecordingCondition("lowest", False)
    accept_middle = RecordingCondition("middle", True)
    accept_highest = RecordingCondition("highest", True)

    # Register end, beginning, then middle to exercise all local insertion points.
    machine.add_transition("advance", source, highest, accept_highest, priority=30)
    machine.add_transition("advance", source, lowest, reject_lowest, priority=10)
    machine.add_transition("advance", source, middle, accept_middle, priority=20)

    published_slot = machine._transitions[source.name]["advance"]
    assert tuple(entry.priority for entry in published_slot.entries) == (10, 20, 30)

    result = machine.trigger("advance")

    assert result.success is True
    assert result.to_state == "middle"
    assert result.priority == 20
    assert machine.history[-1].priority == 20
    assert evaluated == ["lowest", "middle"]

    graph_version = machine._graph_version
    machine.add_transition("advance", source, middle, accept_middle, priority=20)

    assert machine._transitions[source.name]["advance"] is published_slot
    assert machine._graph_version == graph_version

    with pytest.raises(
        ValueError, match="transition priority is already registered for this slot"
    ):
        machine.add_transition(
            "advance", [source, alternate_source], conflicting, priority=20
        )

    assert machine._transitions[source.name]["advance"] is published_slot
    assert "advance" not in machine._transitions[alternate_source.name]
    assert machine._graph_version == graph_version


@pytest.mark.asyncio
async def test_async_group_awaits_one_candidate_at_a_time_in_priority_order() -> None:
    """Async dispatch must select one ordered winner before lifecycle starts."""
    events: list[str] = []
    active = [0]
    source = State("source")
    rejected = State("rejected")
    winner = State("winner")
    later = State("later")
    machine = AsyncStateMachine(source, name="priority-async-sequential")
    for state in (rejected, winner, later):
        machine.add_state(state)
    machine.add_transition(
        "go",
        source,
        later,
        _SequentialAsyncCondition(events, active, "later", True),
        priority=4,
    )
    machine.add_transition(
        "go",
        source,
        winner,
        _SequentialAsyncCondition(events, active, "winner", True),
        priority=0,
    )
    machine.add_transition(
        "go",
        source,
        rejected,
        _SequentialAsyncCondition(events, active, "rejected", False),
        priority=-2,
    )
    machine.on_trigger("go", lambda *_args, **_kwargs: events.append("trigger"))

    result = await machine.trigger_async("go")

    assert result.success is True
    assert result.to_state == "winner"
    assert events == ["guard:rejected", "guard:winner", "trigger"]
    assert active == [0]


@pytest.mark.asyncio
async def test_can_trigger_async_scans_the_same_order_without_lifecycle() -> None:
    """The async query shares eligibility selection but remains observer-free."""
    events: list[str] = []
    active = [0]
    source = State("source")
    rejected = State("rejected")
    winner = State("winner")
    machine = AsyncStateMachine(source, name="priority-async-query")
    machine.add_state(rejected)
    machine.add_state(winner)
    machine.enable_history()
    machine.add_transition(
        "go",
        source,
        rejected,
        _SequentialAsyncCondition(events, active, "rejected", False),
        priority=-1,
    )
    machine.add_transition(
        "go",
        source,
        winner,
        _SequentialAsyncCondition(events, active, "winner", True),
        priority=1,
    )
    machine.on_trigger("go", lambda *_args, **_kwargs: events.append("trigger"))
    machine.on_failed(lambda *_args, **_kwargs: events.append("failed"))

    assert await machine.can_trigger_async("go") is True
    assert events == ["guard:rejected", "guard:winner"]
    assert machine.current_state is source
    assert machine.history == []


@pytest.mark.asyncio
async def test_async_group_does_not_speculate_beyond_the_current_candidate() -> None:
    """A lower candidate must finish before the next candidate can begin."""
    events: list[str] = []
    started = asyncio.Event()
    release = asyncio.Event()
    source = State("source")
    rejected = State("rejected")
    winner = State("winner")
    machine = AsyncStateMachine(source, name="priority-async-no-speculation")
    machine.add_state(rejected)
    machine.add_state(winner)
    first = _GatedAsyncCondition(events, "first", False, started, release)
    machine.add_transition("go", source, rejected, first, priority=-1)
    machine.add_transition(
        "go",
        source,
        winner,
        _SequentialAsyncCondition(events, [0], "winner", True),
        priority=1,
    )

    pending = asyncio.create_task(machine.trigger_async("go"))
    await asyncio.wait_for(started.wait(), timeout=5)
    assert events == ["guard:first"]
    release.set()
    result = await asyncio.wait_for(pending, timeout=5)

    assert result.success is True
    assert events == ["guard:first", "guard:winner"]


@pytest.mark.asyncio
async def test_async_group_terminal_exception_and_exhaustion_finalize_once() -> None:
    """Only normal false falls through a group; exceptions and exhaustion are final."""
    events: list[str] = []
    failure = RuntimeError("candidate-secret")
    source = State("source")
    failed = State("failed")
    later = State("later")
    machine = AsyncStateMachine(source, name="priority-async-terminal")
    machine.add_state(failed)
    machine.add_state(later)
    machine.add_transition(
        "go",
        source,
        failed,
        _SequentialAsyncCondition(events, [0], "failed", failure),
        priority=-1,
    )
    machine.add_transition(
        "go",
        source,
        later,
        _SequentialAsyncCondition(events, [0], "later", True),
        priority=1,
    )
    observed: list[tuple[str, str, str]] = []
    machine.on_failed(
        lambda trigger, from_state, error, **_kwargs: observed.append(
            (trigger, from_state, error)
        )
    )

    result = await machine.trigger_async("go")

    assert result.success is False
    assert result.stage == "guard"
    assert result.cause is failure
    assert events == ["guard:failed"]
    assert observed == [("go", "source", "Transition guard raised an exception")]

    exhaustion_events: list[str] = []
    exhausted = AsyncStateMachine(State("source"), name="priority-async-exhaustion")
    exhausted.add_state(State("first"))
    exhausted.add_state(State("second"))
    exhausted.add_transition(
        "go",
        "source",
        "first",
        _SequentialAsyncCondition(exhaustion_events, [0], "first", False),
        priority=-1,
    )
    exhausted.add_transition(
        "go",
        "source",
        "second",
        _SequentialAsyncCondition(exhaustion_events, [0], "second", False),
        priority=1,
    )
    exhausted_observed: list[str] = []
    exhausted.on_failed(lambda *_args, **_kwargs: exhausted_observed.append("failed"))

    exhaustion = await exhausted.trigger_async("go")

    assert exhaustion.success is False
    assert exhaustion.committed is False
    assert exhaustion.stage == "selection"
    assert exhaustion.error == "No eligible transition candidate"
    assert exhaustion.cause is None
    assert exhaustion_events == ["guard:first", "guard:second"]
    assert exhausted_observed == ["failed"]


@pytest.mark.asyncio
async def test_async_candidate_cancellation_finalizes_once_and_releases_ownership() -> (
    None
):
    """Trigger cancellation is terminal, observer-visible, and leaves no busy owner."""
    events: list[str] = []
    started = asyncio.Event()
    release = asyncio.Event()
    source = State("source")
    blocked = State("blocked")
    later = State("later")
    recovered = State("recovered")
    machine = AsyncStateMachine(source, name="priority-async-cancellation")
    for state in (blocked, later, recovered):
        machine.add_state(state)
    condition = _GatedAsyncCondition(events, "blocked", True, started, release)
    machine.add_transition("go", source, blocked, condition, priority=-1)
    machine.add_transition(
        "go",
        source,
        later,
        _SequentialAsyncCondition(events, [0], "later", True),
        priority=1,
    )
    machine.add_transition("recover", source, recovered)
    observed: list[tuple[str, str, str]] = []
    machine.on_failed(
        lambda trigger, from_state, error, **_kwargs: observed.append(
            (trigger, from_state, error)
        )
    )

    pending = asyncio.create_task(machine.trigger_async("go"))
    await asyncio.wait_for(started.wait(), timeout=5)
    pending.cancel()
    with pytest.raises(asyncio.CancelledError) as cancellation:
        await asyncio.wait_for(pending, timeout=5)

    assert cancellation.value is condition.cancellation
    assert events == ["guard:blocked"]
    assert observed == [("go", "source", "Transition cancelled at guard")]
    assert machine.current_state is source
    assert (await machine.trigger_async("recover")).success is True


@pytest.mark.asyncio
async def test_async_permission_cancellation_uses_permission_stage_without_fallback() -> (
    None
):
    """Cancellation in the last candidate stage is still terminal and truthful."""
    started = asyncio.Event()
    release = asyncio.Event()
    events: list[str] = []

    class Source(State):
        __slots__ = ("cancellation",)

        def __init__(self) -> None:
            super().__init__("source")
            self.cancellation: asyncio.CancelledError | None = None

        async def can_transition_async(
            self, trigger: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            started.set()
            try:
                await asyncio.wait_for(release.wait(), timeout=5)
            except asyncio.CancelledError as cancellation:
                self.cancellation = cancellation
                raise
            return True

    source = Source()
    blocked = State("blocked")
    later = State("later")
    machine = AsyncStateMachine(source, name="priority-async-permission-cancel")
    machine.add_state(blocked)
    machine.add_state(later)
    machine.add_transition("go", source, blocked, priority=-1)
    machine.add_transition(
        "go",
        source,
        later,
        _SequentialAsyncCondition(events, [0], "later", True),
        priority=1,
    )
    observed: list[tuple[str, str, str]] = []
    machine.on_failed(
        lambda trigger, from_state, error, **_kwargs: observed.append(
            (trigger, from_state, error)
        )
    )

    pending = asyncio.create_task(machine.trigger_async("go"))
    await asyncio.wait_for(started.wait(), timeout=5)
    pending.cancel()
    with pytest.raises(asyncio.CancelledError) as cancellation:
        await asyncio.wait_for(pending, timeout=5)

    assert cancellation.value is source.cancellation
    assert events == []
    assert observed == [("go", "source", "Transition cancelled at state-permission")]


@pytest.mark.asyncio
async def test_async_declarative_cancellation_and_query_cancellation_do_not_fall_through() -> (
    None
):
    """Cancellation exits its candidate stage without a trigger/query fallback."""
    events: list[str] = []
    started = asyncio.Event()
    release = asyncio.Event()

    async def declarative_guard(*_args: object, **_kwargs: object) -> bool:
        events.append("declarative")
        started.set()
        await asyncio.wait_for(release.wait(), timeout=5)
        return True

    class Source(AsyncDeclarativeState):
        __slots__ = ()

        @transition("go", to_state="blocked", condition=declarative_guard)
        async def go(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("cancelled candidate handler must not run")

    source = Source("source")
    blocked = State("blocked")
    later = State("later")
    machine = AsyncStateMachine(source, name="priority-async-declarative-cancel")
    machine.add_state(blocked)
    machine.add_state(later)
    machine.add_transition("go", source, blocked, priority=-1)
    machine.add_transition(
        "go",
        source,
        later,
        _SequentialAsyncCondition(events, [0], "later", True),
        priority=1,
    )
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("failed"))

    pending = asyncio.create_task(machine.trigger_async("go"))
    await asyncio.wait_for(started.wait(), timeout=5)
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(pending, timeout=5)

    assert events == ["declarative"]
    assert observed == ["failed"]

    query_events: list[str] = []
    query_started = asyncio.Event()
    query_release = asyncio.Event()
    query_source = State("query-source")
    query_blocked = State("query-blocked")
    query_later = State("query-later")
    query_machine = AsyncStateMachine(query_source, name="priority-async-query-cancel")
    query_machine.add_state(query_blocked)
    query_machine.add_state(query_later)
    query_condition = _GatedAsyncCondition(
        query_events, "blocked", True, query_started, query_release
    )
    query_machine.add_transition(
        "go", query_source, query_blocked, query_condition, priority=-1
    )
    query_machine.add_transition(
        "go",
        query_source,
        query_later,
        _SequentialAsyncCondition(query_events, [0], "later", True),
        priority=1,
    )
    query_observed: list[str] = []
    query_machine.on_failed(lambda *_args, **_kwargs: query_observed.append("failed"))

    query = asyncio.create_task(query_machine.can_trigger_async("go"))
    await asyncio.wait_for(query_started.wait(), timeout=5)
    query.cancel()
    with pytest.raises(asyncio.CancelledError) as query_cancellation:
        await asyncio.wait_for(query, timeout=5)

    assert query_cancellation.value is query_condition.cancellation
    assert query_events == ["guard:blocked"]
    assert query_observed == []


def test_sync_group_selects_the_first_fully_eligible_candidate_before_lifecycle() -> (
    None
):
    """Priority selection retains the exact target handler and caller payload."""
    events: list[str] = []
    guard_payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []
    handler_payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def declarative_guard(*args: object, **kwargs: object) -> bool:
        events.append("declarative-guard")
        assert args == ("telemetry",)
        assert kwargs == {"priority": "caller-payload", "battery": 41}
        return True

    class Source(DeclarativeState):
        __slots__ = ("_events",)

        def __init__(self) -> None:
            self._events = events
            super().__init__("source")

        def can_transition(
            self, trigger_name: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            self._events.append("permission")
            assert trigger_name == "go"
            assert to_state.name == "winner"
            assert args == ("telemetry",)
            assert kwargs == {"priority": "caller-payload", "battery": 41}
            return super().can_transition(trigger_name, to_state, *args, **kwargs)

        def on_exit(
            self, to_state: State, trigger_name: str, *args: object, **kwargs: object
        ) -> None:
            self._events.append("source-exit")

        @transition("go", to_state="winner", condition=declarative_guard)
        def go(self, *args: object, **kwargs: object) -> None:
            events.append("handler")
            handler_payloads.append((args, dict(kwargs)))

    source = Source()
    rejected = State("rejected")
    winner = State("winner")
    later = State("later")
    machine = StateMachine(source, name="priority-sync-winner")
    for state in (rejected, winner, later):
        machine.add_state(state)
    machine.enable_history()

    class Listener:
        def before_transition(self, *_args: object, **_kwargs: object) -> None:
            events.append("before-transition")

    machine.add_listener(Listener())
    machine.on_trigger("go", lambda *_args, **_kwargs: events.append("trigger"))
    machine.after_transition(
        lambda *_args, **_kwargs: events.append("after-transition")
    )

    # Register out of precedence order.  The negative candidate rejects; the
    # zero candidate wins; the positive candidate must never be inspected.
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(events, "guard-later", True, guard_payloads),
        priority=9,
    )
    machine.add_transition(
        "go",
        source,
        winner,
        _RecordingCondition(events, "guard-winner", True, guard_payloads),
        priority=0,
    )
    machine.add_transition(
        "go",
        source,
        rejected,
        _RecordingCondition(events, "guard-rejected", False, guard_payloads),
        priority=-5,
    )

    result = machine.trigger("go", "telemetry", priority="caller-payload", battery=41)

    assert result.success is True
    assert result.from_state == "source"
    assert result.to_state == "winner"
    assert machine.current_state is winner
    assert [
        (record.from_state, record.trigger, record.to_state)
        for record in machine.history
    ] == [("source", "go", "winner")]
    assert events == [
        "guard-rejected",
        "guard-winner",
        "declarative-guard",
        "permission",
        "before-transition",
        "source-exit",
        "handler",
        "trigger",
        "after-transition",
    ]
    assert guard_payloads == [
        (("telemetry",), {"priority": "caller-payload", "battery": 41}),
        (("telemetry",), {"priority": "caller-payload", "battery": 41}),
    ]
    assert handler_payloads == [
        (("telemetry",), {"priority": "caller-payload", "battery": 41})
    ]


def test_sync_group_rejections_fall_through_each_eligibility_stage() -> None:
    """Normal false values advance locally until one candidate is fully eligible."""
    events: list[str] = []
    payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def declarative_guard(*_args: object, **_kwargs: object) -> bool:
        events.append("declarative-guard")
        return False

    class Source(DeclarativeState):
        __slots__ = ("_events",)

        def __init__(self) -> None:
            self._events = events
            super().__init__("source")

        def can_transition(
            self, trigger_name: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            self._events.append(f"permission:{to_state.name}")
            if to_state.name == "permission-rejected":
                return False
            return super().can_transition(trigger_name, to_state, *args, **kwargs)

        @transition("go", to_state="declarative-rejected", condition=declarative_guard)
        def go(self) -> None:
            raise AssertionError("rejected declarative handler must not run")

    source = Source()
    guard_rejected = State("guard-rejected")
    declarative_rejected = State("declarative-rejected")
    permission_rejected = State("permission-rejected")
    winner = State("winner")
    machine = StateMachine(source, name="priority-fallthrough")
    for state in (
        guard_rejected,
        declarative_rejected,
        permission_rejected,
        winner,
    ):
        machine.add_state(state)
    machine.add_transition(
        "go",
        source,
        winner,
        _RecordingCondition(events, "winner-guard", True, payloads),
        priority=4,
    )
    machine.add_transition("go", source, permission_rejected, priority=2)
    machine.add_transition("go", source, declarative_rejected, priority=0)
    machine.add_transition(
        "go",
        source,
        guard_rejected,
        _RecordingCondition(events, "guard-rejected", False, payloads),
        priority=-3,
    )

    result = machine.trigger("go")

    assert result.success is True
    assert machine.current_state is winner
    assert events == [
        "guard-rejected",
        "declarative-guard",
        "permission:permission-rejected",
        "winner-guard",
        "permission:winner",
    ]


def test_sync_group_exhaustion_is_one_redacted_selection_failure() -> None:
    """Rejected candidates are scan control, not individually observed failures."""
    events: list[str] = []
    payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []
    source = State("source")
    first = State("first")
    second = State("second")
    machine = StateMachine(source, name="priority-exhaustion")
    machine.add_state(first)
    machine.add_state(second)
    machine.enable_history()
    machine.add_transition(
        "go",
        source,
        first,
        _RecordingCondition(events, "first-guard", False, payloads),
        priority=-1,
    )
    machine.add_transition(
        "go",
        source,
        second,
        _RecordingCondition(events, "second-guard", False, payloads),
        priority=3,
    )
    observed: list[tuple[str, str, str, dict[str, object]]] = []
    machine.on_failed(
        lambda trigger_name, from_state, error, **kwargs: observed.append(
            (trigger_name, from_state, error, dict(kwargs))
        )
    )

    result = machine.trigger("go", secret="caller-secret", priority="payload")

    assert result.success is False
    assert result.committed is False
    assert result.stage == "selection"
    assert result.to_state is None
    assert result.cause is None
    assert result.error == "No eligible transition candidate"
    assert "first" not in result.error
    assert "second" not in result.error
    assert "caller-secret" not in result.error
    assert machine.current_state is source
    assert machine.history == []
    assert events == ["first-guard", "second-guard"]
    assert observed == [
        (
            "go",
            "source",
            "No eligible transition candidate",
            {"secret": "caller-secret", "priority": "payload"},
        )
    ]


def test_sync_group_guard_exception_is_terminal_and_finalized_once() -> None:
    """An eligibility exception cannot activate a lower-priority candidate."""
    events: list[str] = []
    payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []
    failure = RuntimeError("guard-secret")
    source = State("source")
    failed = State("failed")
    later = State("later")
    machine = StateMachine(source, name="priority-guard-exception")
    machine.add_state(failed)
    machine.add_state(later)
    machine.enable_history()
    machine.add_transition(
        "go",
        source,
        failed,
        _RecordingCondition(events, "raising-guard", failure, payloads),
        priority=-1,
    )
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(events, "later-guard", True, payloads),
        priority=2,
    )
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("observer"))

    result = machine.trigger("go")

    assert result.success is False
    assert result.stage == "guard"
    assert result.cause is failure
    assert machine.current_state is source
    assert machine.history == []
    assert events == ["raising-guard"]
    assert observed == ["observer"]


def test_sync_group_declarative_and_permission_exceptions_stop_selection() -> None:
    """Both remaining eligibility seams are terminal before lifecycle work."""
    declarative_events: list[str] = []
    declarative_failure = RuntimeError("declarative-secret")

    def failing_declarative_guard(*_args: object, **_kwargs: object) -> bool:
        declarative_events.append("declarative-guard")
        raise declarative_failure

    class DeclarativeSource(DeclarativeState):
        __slots__ = ()

        @transition("go", to_state="failed", condition=failing_declarative_guard)
        def go(self) -> None:
            raise AssertionError("failed candidate handler must not run")

    source = DeclarativeSource("source")
    failed = State("failed")
    later = State("later")
    machine = StateMachine(source, name="priority-declarative-exception")
    machine.add_state(failed)
    machine.add_state(later)
    machine.add_transition("go", source, failed, priority=-1)
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(declarative_events, "later-guard", True, []),
        priority=1,
    )

    declarative_result = machine.trigger("go")

    assert declarative_result.stage == "guard"
    assert declarative_result.cause is declarative_failure
    assert declarative_events == ["declarative-guard"]

    permission_events: list[str] = []
    permission_failure = RuntimeError("permission-secret")

    class PermissionSource(State):
        __slots__ = ()

        def can_transition(
            self, trigger_name: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            raise permission_failure

    permission_source = PermissionSource("permission-source")
    permission_failed = State("permission-failed")
    permission_later = State("permission-later")
    permission_machine = StateMachine(
        permission_source, name="priority-permission-exception"
    )
    permission_machine.add_state(permission_failed)
    permission_machine.add_state(permission_later)
    permission_machine.add_transition(
        "go", permission_source, permission_failed, priority=-1
    )
    permission_machine.add_transition(
        "go",
        permission_source,
        permission_later,
        _RecordingCondition(permission_events, "later-guard", True, []),
        priority=1,
    )

    permission_result = permission_machine.trigger("go")

    assert permission_result.stage == "state-permission"
    assert permission_result.cause is permission_failure
    assert permission_events == []


def test_can_trigger_uses_selection_order_without_observers_or_mutation() -> None:
    """Queries share the candidate boundary but do not enter the lifecycle."""
    events: list[str] = []
    payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []
    source = State("source")
    rejected = State("rejected")
    winner = State("winner")
    machine = StateMachine(source, name="priority-query")
    machine.add_state(rejected)
    machine.add_state(winner)
    machine.enable_history()
    machine.add_transition(
        "go",
        source,
        rejected,
        _RecordingCondition(events, "rejected-guard", False, payloads),
        priority=-2,
    )
    machine.add_transition(
        "go",
        source,
        winner,
        _RecordingCondition(events, "winner-guard", True, payloads),
        priority=0,
    )
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("observer"))

    assert machine.can_trigger("go", priority="caller-payload") is True

    assert events == ["rejected-guard", "winner-guard"]
    assert machine.current_state is source
    assert machine.history == []
    assert observed == []


def test_can_trigger_does_not_advance_after_a_condition_or_permission_exception() -> (
    None
):
    """Queries preserve terminal outward exceptions and never inspect a lower edge."""
    failure = RuntimeError("query-guard-secret")
    events: list[str] = []
    source = State("source")
    failed = State("failed")
    later = State("later")
    machine = StateMachine(source, name="priority-query-guard-exception")
    machine.add_state(failed)
    machine.add_state(later)
    machine.add_transition(
        "go",
        source,
        failed,
        _RecordingCondition(events, "raising", failure, []),
        priority=-1,
    )
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(events, "later", True, []),
        priority=1,
    )

    with pytest.raises(RuntimeError) as raised:
        machine.can_trigger("go")

    assert raised.value is failure
    assert events == ["raising"]

    permission_failure = RuntimeError("query-permission-secret")

    class PermissionSource(State):
        __slots__ = ()

        def can_transition(
            self, trigger_name: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            raise permission_failure

    permission_source = PermissionSource("permission-source")
    permission_target = State("permission-target")
    permission_later = State("permission-later")
    permission_machine = StateMachine(
        permission_source, name="priority-query-permission"
    )
    permission_machine.add_state(permission_target)
    permission_machine.add_state(permission_later)
    permission_machine.add_transition(
        "go", permission_source, permission_target, priority=-1
    )
    permission_machine.add_transition(
        "go",
        permission_source,
        permission_later,
        _RecordingCondition(events, "permission-later", True, []),
        priority=1,
    )

    with pytest.raises(RuntimeError) as permission_raised:
        permission_machine.can_trigger("go")

    assert permission_raised.value is permission_failure
    assert events == ["raising"]


def test_can_trigger_treats_a_declarative_exception_as_terminal_false() -> None:
    """The declarative query compatibility path cannot fall through on error."""
    events: list[str] = []
    failure = RuntimeError("query-declarative-secret")

    def failing_guard(*_args: object, **_kwargs: object) -> bool:
        events.append("declarative-guard")
        raise failure

    class Source(DeclarativeState):
        __slots__ = ()

        @transition("go", to_state="failed", condition=failing_guard)
        def go(self) -> None:
            raise AssertionError("failing candidate handler must not run")

    source = Source("source")
    failed = State("failed")
    later = State("later")
    machine = StateMachine(source, name="priority-query-declarative")
    machine.add_state(failed)
    machine.add_state(later)
    machine.add_transition("go", source, failed, priority=-1)
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(events, "later-guard", True, []),
        priority=1,
    )

    assert machine.can_trigger("go") is False

    assert events == ["declarative-guard"]
    assert machine.current_state is source


def test_lifecycle_failure_after_selection_never_evaluates_a_lower_candidate() -> None:
    """Lifecycle failure is a result of the selected edge, not scan control."""
    events: list[str] = []
    payloads: list[tuple[tuple[object, ...], dict[str, object]]] = []
    failure = RuntimeError("destination-secret")

    def fail_destination(*_args: object, **_kwargs: object) -> None:
        raise failure

    source = State("source")
    selected = CallbackState("selected", on_enter=fail_destination)
    later = State("later")
    machine = StateMachine(source, name="priority-lifecycle-failure")
    machine.add_state(selected)
    machine.add_state(later)
    machine.enable_history()
    machine.add_transition("go", source, selected, priority=-1)
    machine.add_transition(
        "go",
        source,
        later,
        _RecordingCondition(events, "later-guard", True, payloads),
        priority=1,
    )
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("observer"))

    result = machine.trigger("go")

    assert result.success is False
    assert result.stage == "destination-enter"
    assert result.committed is True
    assert result.cause is failure
    assert machine.current_state is selected
    assert len(machine.history) == 1
    assert events == []
    assert observed == ["observer"]
