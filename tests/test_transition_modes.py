"""Focused behavioral oracle for explicit internal and external self-transitions."""

from __future__ import annotations

import asyncio

import pytest

from fast_fsm.conditions import AsyncCondition, FuncCondition
from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    DeclarativeState,
    State,
    StateMachine,
    TransitionResult,
    transition,
)


class _RecordingState(State):
    """State-local recorder that makes lifecycle differences observable."""

    __slots__ = ("events",)

    def __init__(self, events: list[str]) -> None:
        super().__init__("hover")
        self.events = events

    def on_exit(
        self, to_state: State, trigger: str, *args: object, **kwargs: object
    ) -> None:
        self.events.append("state-exit")

    def on_enter(
        self, from_state: State | None, trigger: str, *args: object, **kwargs: object
    ) -> None:
        self.events.append("state-enter")


class _LifecycleListener:
    """Record listener calls without importing fixtures from another suite."""

    def __init__(self, events: list[str]) -> None:
        self._events = events

    def before_transition(self, *args: object, **kwargs: object) -> None:
        self._events.append("before")

    def on_exit_state(self, *args: object, **kwargs: object) -> None:
        self._events.append("exit-listener")

    def on_enter_state(self, *args: object, **kwargs: object) -> None:
        self._events.append("enter-listener")

    def after_transition(self, *args: object, **kwargs: object) -> None:
        self._events.append("after")


def _assert_internal_selection_failure(
    result: TransitionResult,
    stage: str,
    *,
    cause: BaseException | None = None,
) -> None:
    """Assert that a selected internal candidate retains pre-commit truth."""
    assert result.success is False
    assert result.committed is False
    assert result.stage == stage
    assert result.priority == 7
    assert result.internal is True
    assert result.cause is cause


def test_registered_transition_entry_is_immutable_after_validation() -> None:
    """Published entries cannot bypass registration's internal-edge invariant."""
    source = State("source")
    target = State("target")
    machine = StateMachine(source)
    machine.add_state(target)
    machine.add_transition("advance", source, target)
    entry = machine._transitions["source"]["advance"]

    for attribute, value in (
        ("to_state", source),
        ("condition", None),
        ("priority", 7),
        ("condition_ref", "other"),
        ("after", 1.0),
        ("within", 2.0),
        ("internal", True),
    ):
        with pytest.raises(AttributeError):
            setattr(entry, attribute, value)

    result = machine.trigger("advance")

    assert result.success is True
    assert result.internal is False
    assert machine.current_state is target


def test_default_and_false_self_transitions_keep_the_external_lifecycle() -> None:
    """Omitted and explicit ``False`` retain ordinary exit/re-entry behavior."""
    events: list[str] = []
    state = _RecordingState(events)
    machine = StateMachine(state, clock=lambda: 5.0)
    machine.enable_history()
    machine.add_transition("default", state, state)
    machine.add_transition("false", state, state, internal=False)
    machine.add_listener(_LifecycleListener(events))
    machine.on_exit("hover", lambda *_args, **_kwargs: events.append("exit-callback"))
    machine.on_enter("hover", lambda *_args, **_kwargs: events.append("enter-callback"))
    machine.on_trigger(
        "default", lambda *_args, **_kwargs: events.append("trigger-callback")
    )
    machine.on_trigger(
        "false", lambda *_args, **_kwargs: events.append("trigger-callback")
    )

    for trigger in ("default", "false"):
        events.clear()
        result = machine.trigger(trigger)

        assert result.success is True
        assert result.committed is True
        assert result.internal is False
        assert machine.history[-1].internal is False
        assert events == [
            "before",
            "state-exit",
            "exit-callback",
            "exit-listener",
            "state-enter",
            "enter-callback",
            "enter-listener",
            "trigger-callback",
            "after",
        ]


def test_internal_self_transition_commits_without_state_lifecycle_or_payload_injection() -> (
    None
):
    """An internal event retains transition work while skipping all state surfaces."""
    events: list[str] = []
    received_kwargs: list[dict[str, object]] = []
    state = _RecordingState(events)
    machine = StateMachine(state, clock=lambda: 5.0)
    machine.enable_history()
    machine.add_transition("refresh", state, state, internal=True)
    machine.add_listener(_LifecycleListener(events))
    machine.on_exit("hover", lambda *_args, **_kwargs: events.append("exit-callback"))
    machine.on_enter("hover", lambda *_args, **_kwargs: events.append("enter-callback"))

    def trigger_callback(*args: object, **kwargs: object) -> None:
        received_kwargs.append(dict(kwargs))
        events.append("trigger-callback")

    machine.on_trigger("refresh", trigger_callback)

    result = machine.trigger("refresh", payload="caller-value")

    assert result.success is True
    assert result.committed is True
    assert result.internal is True
    assert machine.history[-1].internal is True
    assert received_kwargs == [{"payload": "caller-value"}]
    assert events == ["before", "trigger-callback", "after"]


def test_batch_internal_row_commits_with_the_same_mode_and_history_truth() -> None:
    """The retained batch adapter carries internal mode into canonical selection."""
    state = State("hover")
    machine = StateMachine(state)
    machine.enable_history()
    machine.add_transitions([("refresh", state, state, None, -2, None, None, True)])

    result = machine.trigger("refresh")

    assert result.success is True
    assert result.priority == -2
    assert result.internal is True
    assert machine.history[-1].internal is True


def test_internal_transition_retains_only_transition_surfaces_in_exact_order() -> None:
    """A selected internal edge bypasses all six state lifecycle families."""
    events: list[str] = []

    class RefreshState(DeclarativeState):
        __slots__ = ()

        @transition("refresh", from_state="hover", to_state="hover")
        def on_refresh(self, *args: object, **kwargs: object) -> None:
            events.append("declarative-handler")

    state = RefreshState("hover")
    machine = StateMachine(state, clock=lambda: 5.0)
    machine.enable_history()
    machine.add_transition("refresh", state, state, internal=True)
    machine.add_listener(_LifecycleListener(events))
    machine.on_exit("hover", lambda *_args, **_kwargs: events.append("exit-callback"))
    machine.on_enter("hover", lambda *_args, **_kwargs: events.append("enter-callback"))
    machine.on_trigger(
        "refresh", lambda *_args, **_kwargs: events.append("trigger-callback")
    )

    result = machine.trigger("refresh")

    assert result.success is True
    assert result.committed is True
    assert result.internal is True
    assert events == [
        "before",
        "declarative-handler",
        "trigger-callback",
        "after",
    ]


def test_direct_controls_remain_external_and_accept_no_internal_mode() -> None:
    """Only registered event transitions may select internal lifecycle semantics."""
    source = State("source")
    target = State("target")
    machine = StateMachine(source)
    machine.add_state(target)

    with pytest.raises(TypeError):
        machine.force_state("target", internal=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        machine.reset(internal=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        machine.restore({}, internal=True)  # type: ignore[call-arg]


def test_sync_internal_selection_failures_preserve_selected_mode() -> None:
    """Every singleton pre-commit rejection keeps its selected edge metadata."""
    timing_state = State("hover")
    timing_machine = StateMachine(timing_state, clock=lambda: 0.0)
    timing_machine.add_transition(
        "refresh", timing_state, timing_state, after=1, internal=True, priority=7
    )
    _assert_internal_selection_failure(timing_machine.trigger("refresh"), "selection")

    direct_guard_state = State("hover")
    direct_guard_machine = StateMachine(direct_guard_state)
    direct_guard_machine.add_transition(
        "reject",
        direct_guard_state,
        direct_guard_state,
        FuncCondition(lambda **_kwargs: False),
        internal=True,
        priority=7,
    )
    direct_guard_failure = RuntimeError("direct-guard")

    def raise_direct_guard(**_kwargs: object) -> bool:
        raise direct_guard_failure

    direct_guard_machine.add_transition(
        "raise",
        direct_guard_state,
        direct_guard_state,
        FuncCondition(raise_direct_guard),
        internal=True,
        priority=7,
    )
    _assert_internal_selection_failure(direct_guard_machine.trigger("reject"), "guard")
    _assert_internal_selection_failure(
        direct_guard_machine.trigger("raise"), "guard", cause=direct_guard_failure
    )

    declarative_failure = RuntimeError("declarative-guard")

    def reject_declarative_guard(**_kwargs: object) -> bool:
        return False

    def raise_declarative_guard(**_kwargs: object) -> bool:
        raise declarative_failure

    class DeclarativeSource(DeclarativeState):
        __slots__ = ()

        @transition(
            "reject",
            from_state="hover",
            to_state="hover",
            condition=reject_declarative_guard,
        )
        def reject(self) -> None:
            raise AssertionError("rejected declarative handler must not run")

        @transition(
            "raise",
            from_state="hover",
            to_state="hover",
            condition=raise_declarative_guard,
        )
        def raise_(self) -> None:
            raise AssertionError("failing declarative handler must not run")

    declarative_state = DeclarativeSource("hover")
    declarative_machine = StateMachine(declarative_state)
    declarative_machine.add_transition(
        "reject",
        declarative_state,
        declarative_state,
        internal=True,
        priority=7,
    )
    declarative_machine.add_transition(
        "raise",
        declarative_state,
        declarative_state,
        internal=True,
        priority=7,
    )
    _assert_internal_selection_failure(declarative_machine.trigger("reject"), "guard")
    _assert_internal_selection_failure(
        declarative_machine.trigger("raise"), "guard", cause=declarative_failure
    )

    permission_failure = RuntimeError("permission")

    class PermissionSource(State):
        __slots__ = ()

        def can_transition(
            self, trigger: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            if trigger == "raise":
                raise permission_failure
            return False

    permission_state = PermissionSource("hover")
    permission_machine = StateMachine(permission_state)
    for trigger in ("reject", "raise"):
        permission_machine.add_transition(
            trigger,
            permission_state,
            permission_state,
            internal=True,
            priority=7,
        )
    _assert_internal_selection_failure(
        permission_machine.trigger("reject"), "state-permission"
    )
    _assert_internal_selection_failure(
        permission_machine.trigger("raise"),
        "state-permission",
        cause=permission_failure,
    )


@pytest.mark.asyncio
async def test_async_internal_selection_failures_preserve_selected_mode() -> None:
    """Async singleton selection reports the same truthful internal metadata."""
    timing_state = State("hover")
    timing_machine = AsyncStateMachine(timing_state, clock=lambda: 0.0)
    timing_machine.add_transition(
        "refresh", timing_state, timing_state, after=1, internal=True, priority=7
    )
    _assert_internal_selection_failure(
        await timing_machine.trigger_async("refresh"), "selection"
    )

    class AsyncGuard(AsyncCondition):
        __slots__ = ("_outcome",)

        def __init__(self, outcome: bool | BaseException) -> None:
            super().__init__("async-selection-guard", "phase 28 selection guard")
            self._outcome = outcome

        async def check_async(self, **_kwargs: object) -> bool:
            if isinstance(self._outcome, BaseException):
                raise self._outcome
            return self._outcome

    direct_guard_state = State("hover")
    direct_guard_machine = AsyncStateMachine(direct_guard_state)
    direct_guard_machine.add_transition(
        "reject",
        direct_guard_state,
        direct_guard_state,
        AsyncGuard(False),
        internal=True,
        priority=7,
    )
    direct_guard_failure = RuntimeError("async-direct-guard")
    direct_guard_machine.add_transition(
        "raise",
        direct_guard_state,
        direct_guard_state,
        AsyncGuard(direct_guard_failure),
        internal=True,
        priority=7,
    )
    _assert_internal_selection_failure(
        await direct_guard_machine.trigger_async("reject"), "guard"
    )
    _assert_internal_selection_failure(
        await direct_guard_machine.trigger_async("raise"),
        "guard",
        cause=direct_guard_failure,
    )

    declarative_failure = RuntimeError("async-declarative-guard")

    async def reject_declarative_guard(**_kwargs: object) -> bool:
        return False

    async def raise_declarative_guard(**_kwargs: object) -> bool:
        raise declarative_failure

    class DeclarativeSource(AsyncDeclarativeState):
        __slots__ = ()

        @transition(
            "reject",
            from_state="hover",
            to_state="hover",
            condition=reject_declarative_guard,
        )
        async def reject(self) -> None:
            raise AssertionError("rejected declarative handler must not run")

        @transition(
            "raise",
            from_state="hover",
            to_state="hover",
            condition=raise_declarative_guard,
        )
        async def raise_(self) -> None:
            raise AssertionError("failing declarative handler must not run")

    declarative_state = DeclarativeSource("hover")
    declarative_machine = AsyncStateMachine(declarative_state)
    for trigger in ("reject", "raise"):
        declarative_machine.add_transition(
            trigger,
            declarative_state,
            declarative_state,
            internal=True,
            priority=7,
        )
    _assert_internal_selection_failure(
        await declarative_machine.trigger_async("reject"), "guard"
    )
    _assert_internal_selection_failure(
        await declarative_machine.trigger_async("raise"),
        "guard",
        cause=declarative_failure,
    )

    permission_failure = RuntimeError("async-permission")

    class PermissionSource(State):
        __slots__ = ()

        async def can_transition_async(
            self, trigger: str, to_state: State, *args: object, **kwargs: object
        ) -> bool:
            if trigger == "raise":
                raise permission_failure
            return False

    permission_state = PermissionSource("hover")
    permission_machine = AsyncStateMachine(permission_state)
    for trigger in ("reject", "raise"):
        permission_machine.add_transition(
            trigger,
            permission_state,
            permission_state,
            internal=True,
            priority=7,
        )
    _assert_internal_selection_failure(
        await permission_machine.trigger_async("reject"), "state-permission"
    )
    _assert_internal_selection_failure(
        await permission_machine.trigger_async("raise"),
        "state-permission",
        cause=permission_failure,
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_committed"),
    (
        ("before-transition", False),
        ("commit", False),
        ("trigger-callback", True),
        ("after-transition", True),
    ),
)
def test_internal_failure_truth_is_staged_and_finalized_once(
    failure_stage: str, expected_committed: bool
) -> None:
    """Retained internal work reports one truthful pre/post-commit failure."""
    state_events: list[str] = []
    observer_events: list[tuple[str | None, str | None, str, dict[str, object]]] = []
    state = _RecordingState(state_events)
    fail_commit = False
    failure = RuntimeError(f"{failure_stage}-secret")

    def clock() -> float:
        if fail_commit:
            raise failure
        return 1.0

    machine = StateMachine(state, clock=clock)
    machine.enable_history()
    machine.add_transition("refresh", state, state, internal=True, priority=7)
    machine.on_failed(
        lambda trigger, source, error, **kwargs: observer_events.append(
            (trigger, source, error, dict(kwargs))
        )
    )

    if failure_stage == "before-transition":

        class FailingBefore:
            def before_transition(self, *_args: object, **_kwargs: object) -> None:
                raise failure

        machine.add_listener(FailingBefore())
    elif failure_stage == "commit":
        fail_commit = True
    elif failure_stage == "trigger-callback":
        machine.on_trigger(
            "refresh", lambda *_args, **_kwargs: (_ for _ in ()).throw(failure)
        )
    else:

        class FailingAfter:
            def after_transition(self, *_args: object, **_kwargs: object) -> None:
                raise failure

        machine.add_listener(FailingAfter())

    result = machine.trigger("refresh", payload="caller-value")

    assert result.success is False
    assert result.stage == failure_stage
    assert result.committed is expected_committed
    assert result.internal is True
    assert result.priority == 7
    assert result.cause is failure
    assert machine.current_state is state
    assert state_events == []
    assert len(machine.history) == int(expected_committed)
    if expected_committed:
        assert machine.history[-1].internal is True
    assert observer_events == [
        ("refresh", "hover", result.error, {"payload": "caller-value"})
    ]
    assert "secret" not in result.error


def test_internal_declarative_failure_is_committed_and_skips_state_surfaces() -> None:
    """A retained declarative handler failure stops the suffix after commit."""
    events: list[str] = []
    failure = RuntimeError("declarative-secret")

    class FailingRefreshState(DeclarativeState):
        __slots__ = ()

        @transition("refresh", from_state="hover", to_state="hover")
        def on_refresh(self, *args: object, **kwargs: object) -> None:
            events.append("declarative-handler")
            raise failure

        def on_exit(
            self, to_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            events.append("state-exit")

        def on_enter(
            self,
            from_state: State | None,
            trigger: str,
            *args: object,
            **kwargs: object,
        ) -> None:
            events.append("state-enter")

    state = FailingRefreshState("hover")
    machine = StateMachine(state)
    machine.enable_history()
    machine.add_transition("refresh", state, state, internal=True)
    machine.on_trigger("refresh", lambda *_args, **_kwargs: events.append("trigger"))
    machine.add_listener(_LifecycleListener(events))
    observed: list[str] = []
    machine.on_failed(lambda *_args, **_kwargs: observed.append("observer"))

    result = machine.trigger("refresh")

    assert result.success is False
    assert result.stage == "declarative-handler"
    assert result.committed is True
    assert result.internal is True
    assert result.cause is failure
    assert machine.current_state is state
    assert len(machine.history) == 1
    assert machine.history[-1].internal is True
    assert events == ["before", "declarative-handler"]
    assert observed == ["observer"]


class _BlockingInternalGuard(AsyncCondition):
    """A handshake-driven async guard used to prove pre-commit cancellation."""

    def __init__(self, started: asyncio.Event, release: asyncio.Event) -> None:
        super().__init__("blocking-internal-guard", "phase 28 cancellation guard")
        self.started = started
        self.release = release
        self.cancellation: asyncio.CancelledError | None = None

    async def check_async(self, **_kwargs: object) -> bool:
        self.started.set()
        try:
            await asyncio.wait_for(self.release.wait(), timeout=5)
        except asyncio.CancelledError as cancellation:
            self.cancellation = cancellation
            raise
        return True


@pytest.mark.asyncio
async def test_async_internal_transition_retains_transition_work_and_skips_all_state_surfaces() -> (
    None
):
    """The async lifecycle uses the same internal seam as synchronous dispatch."""
    events: list[str] = []

    class RefreshingState(AsyncDeclarativeState):
        __slots__ = ()

        def on_exit(
            self, to_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            events.append("state-exit")

        def on_enter(
            self,
            from_state: State | None,
            trigger: str,
            *args: object,
            **kwargs: object,
        ) -> None:
            events.append("state-enter")

        @transition("refresh", from_state="hover", to_state="hover")
        async def refresh(self, *args: object, **kwargs: object) -> None:
            events.append("declarative-handler")

    state = RefreshingState("hover")
    machine = AsyncStateMachine(state)
    machine.enable_history()
    machine.add_transition("refresh", state, state, internal=True, priority=7)
    machine.add_listener(_LifecycleListener(events))
    machine.on_exit("hover", lambda *_args, **_kwargs: events.append("exit-callback"))
    machine.on_enter("hover", lambda *_args, **_kwargs: events.append("enter-callback"))

    async def exit_async(*_args: object, **_kwargs: object) -> None:
        events.append("exit-async")

    async def enter_async(*_args: object, **_kwargs: object) -> None:
        events.append("enter-async")

    machine.on_exit_async("hover", exit_async)
    machine.on_enter_async("hover", enter_async)
    machine.on_trigger(
        "refresh", lambda *_args, **_kwargs: events.append("trigger-callback")
    )

    result = await machine.trigger_async("refresh", payload="caller-value")

    assert result.success is True
    assert result.committed is True
    assert result.priority == 7
    assert result.internal is True
    assert machine.history[-1].internal is True
    assert events == ["before", "declarative-handler", "trigger-callback", "after"]


@pytest.mark.asyncio
async def test_async_internal_guard_cancellation_is_uncommitted_mode_true_and_reusable() -> (
    None
):
    """A selected internal guard cancellation finalizes once before commit."""
    started = asyncio.Event()
    release = asyncio.Event()
    state = State("hover")
    guard = _BlockingInternalGuard(started, release)
    machine = AsyncStateMachine(state)
    machine.enable_history()
    machine.add_transition("refresh", state, state, guard, internal=True, priority=7)
    observed: list[str] = []
    machine.on_failed(
        lambda _trigger, _source, error, **_kwargs: observed.append(error)
    )

    pending = asyncio.create_task(machine.trigger_async("refresh"))
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(pending, timeout=5)

        assert isinstance(guard.cancellation, asyncio.CancelledError)
        selected = machine._transitions[state.name]["refresh"]
        assert selected.priority == 7
        assert selected.internal is True
        assert machine.current_state is state
        assert machine.history == []
        assert observed == ["Transition cancelled at guard"]
        assert machine._async_owner_task is None
        assert machine._async_owner_root is None
        assert not machine._async_ownership_lock.locked()

        release.set()
        reused = await machine.trigger_async("refresh")
        assert reused.success is True
        assert reused.internal is True
    finally:
        release.set()
        if not pending.done():
            pending.cancel()
        await asyncio.gather(pending, return_exceptions=True)


@pytest.mark.asyncio
async def test_async_internal_postcommit_cancellation_is_mode_true_and_reusable() -> (
    None
):
    """Cancellation in retained declarative work preserves commit and history truth."""
    started = asyncio.Event()
    release = asyncio.Event()
    events: list[str] = []

    class RefreshingState(AsyncDeclarativeState):
        __slots__ = ()

        def on_exit(
            self, to_state: State, trigger: str, *args: object, **kwargs: object
        ) -> None:
            events.append("state-exit")

        def on_enter(
            self,
            from_state: State | None,
            trigger: str,
            *args: object,
            **kwargs: object,
        ) -> None:
            events.append("state-enter")

        @transition("refresh", from_state="hover", to_state="hover")
        async def refresh(self, *args: object, **kwargs: object) -> None:
            events.append("declarative-handler")
            started.set()
            await asyncio.wait_for(release.wait(), timeout=5)

    state = RefreshingState("hover")
    machine = AsyncStateMachine(state)
    machine.enable_history()
    machine.add_transition("refresh", state, state, internal=True, priority=7)
    machine.on_trigger("refresh", lambda *_args, **_kwargs: events.append("trigger"))
    machine.after_transition(lambda *_args, **_kwargs: events.append("after"))
    observed: list[str] = []
    machine.on_failed(
        lambda _trigger, _source, error, **_kwargs: observed.append(error)
    )

    pending = asyncio.create_task(machine.trigger_async("refresh"))
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(pending, timeout=5)

        selected = machine._transitions[state.name]["refresh"]
        assert selected.priority == 7
        assert selected.internal is True
        assert machine.current_state is state
        assert len(machine.history) == 1
        assert machine.history[-1].internal is True
        assert events == ["declarative-handler"]
        assert observed == ["Transition cancelled at declarative-handler"]
        assert machine._async_owner_task is None
        assert machine._async_owner_root is None
        assert not machine._async_ownership_lock.locked()

        release.set()
        reused = await machine.trigger_async("refresh")
        assert reused.success is True
        assert reused.internal is True
        assert events == [
            "declarative-handler",
            "declarative-handler",
            "trigger",
            "after",
        ]
    finally:
        release.set()
        if not pending.done():
            pending.cancel()
        await asyncio.gather(pending, return_exceptions=True)


@pytest.mark.asyncio
async def test_mixed_mode_priority_selects_the_same_internal_entry_sync_and_async() -> (
    None
):
    """Priority chooses a candidate before its selected lifecycle mode matters."""
    sync_state = State("hover")
    sync_machine = StateMachine(sync_state)
    sync_machine.enable_history()
    sync_machine.add_transition("refresh", sync_state, sync_state, priority=5)
    sync_machine.add_transition(
        "refresh", sync_state, sync_state, internal=True, priority=-1
    )

    async_state = State("hover")
    async_machine = AsyncStateMachine(async_state)
    async_machine.enable_history()
    async_machine.add_transition("refresh", async_state, async_state, priority=5)
    async_machine.add_transition(
        "refresh", async_state, async_state, internal=True, priority=-1
    )

    sync_result = sync_machine.trigger("refresh")
    async_result = await async_machine.trigger_async("refresh")

    assert (sync_result.success, sync_result.priority, sync_result.internal) == (
        True,
        -1,
        True,
    )
    assert (async_result.success, async_result.priority, async_result.internal) == (
        True,
        -1,
        True,
    )
    assert sync_machine.history[-1].internal is True
    assert async_machine.history[-1].internal is True
