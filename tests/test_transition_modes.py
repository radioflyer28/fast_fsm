"""Focused behavioral oracle for explicit internal and external self-transitions."""

from __future__ import annotations

import pytest

from fast_fsm.core import DeclarativeState, State, StateMachine, transition


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

    with pytest.raises(TypeError, match="internal"):
        machine.force_state("target", internal=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="internal"):
        machine.reset(internal=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="internal"):
        machine.restore({}, internal=True)  # type: ignore[call-arg]


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
