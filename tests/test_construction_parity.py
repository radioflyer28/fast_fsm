"""Focused observable-semantics oracle for Phase 30 construction adapters."""

from __future__ import annotations

import pytest

from fast_fsm.core import (
    DeclarativeState,
    FSMBuilder,
    State,
    StateMachine,
    TransitionRejected,
    transition,
)


def test_declarative_builder_internal_transition_executes_exactly_once() -> None:
    """A complete declaration becomes one internal builder-owned edge."""
    events: list[str] = []
    calls = {"guard": 0, "handler": 0}

    def guarded_refresh(*_args: object, **_kwargs: object) -> bool:
        calls["guard"] += 1
        return True

    class Hover(DeclarativeState):
        __slots__ = ()

        @transition(
            "refresh",
            from_state="hover",
            to_state="hover",
            condition=guarded_refresh,
            internal=True,
        )
        def refresh(self, *_args: object, **_kwargs: object) -> bool:
            calls["handler"] += 1
            events.append("handler")
            return True

        def on_exit(
            self, _to_state: State, _trigger: str, *_args: object, **_kwargs: object
        ) -> None:
            events.append("state-exit")

        def on_enter(
            self,
            _from_state: State | None,
            _trigger: str,
            *_args: object,
            **_kwargs: object,
        ) -> None:
            events.append("state-enter")

    state = Hover("hover")
    builder = FSMBuilder(state)
    machine = builder.build()
    machine.enable_history()
    machine.on_trigger("refresh", lambda *_args, **_kwargs: events.append("trigger"))

    result = machine.trigger("refresh")

    entry = machine._transitions["hover"]["refresh"]
    assert entry.condition is None
    assert result.success is True
    assert result.committed is True
    assert result.internal is True
    assert machine.current_state is state
    assert machine.history[-1].internal is True
    assert calls == {"guard": 1, "handler": 1}
    assert events == ["handler", "trigger"]
    assert builder.build() is machine


def test_declarative_builder_failure_keeps_staging_and_cache_unchanged() -> None:
    """Late canonical final/mode failures cannot mutate the reusable builder."""

    class NonSelfInternal(DeclarativeState):
        @transition("refresh", to_state="other", internal=True)
        def refresh(self, *_args: object, **_kwargs: object) -> bool:
            return True

    invalid_mode = FSMBuilder(NonSelfInternal("hover")).add_state(State("other"))
    mode_before = (
        tuple((name, id(state)) for name, state in invalid_mode._states.items()),
        tuple(id(request) for request in invalid_mode._transitions),
        invalid_mode._machine,
    )

    with pytest.raises(ValueError, match="identical canonical source and target"):
        invalid_mode.build()

    assert (
        tuple((name, id(state)) for name, state in invalid_mode._states.items()),
        tuple(id(request) for request in invalid_mode._transitions),
        invalid_mode._machine,
    ) == mode_before

    class FinalSource(DeclarativeState):
        @transition("refresh", to_state="done")
        def refresh(self, *_args: object, **_kwargs: object) -> bool:
            return True

    invalid_final = FSMBuilder(FinalSource("done", final=True))
    final_before = (
        tuple((name, id(state)) for name, state in invalid_final._states.items()),
        tuple(id(request) for request in invalid_final._transitions),
        invalid_final._machine,
    )

    with pytest.raises(ValueError, match="final state cannot be a transition source"):
        invalid_final.build()

    assert (
        tuple((name, id(state)) for name, state in invalid_final._states.items()),
        tuple(id(request) for request in invalid_final._transitions),
        invalid_final._machine,
    ) == final_before


def test_declarative_builder_rejection_is_terminal_for_internal_candidate() -> None:
    """A builder-imported declarative guard rejects before any lower priority row."""
    events: list[str] = []

    def reject(*_args: object, **_kwargs: object) -> bool:
        events.append("declarative-guard")
        raise TransitionRejected("mission.altitude_limit")

    class Source(DeclarativeState):
        @transition(
            "go",
            to_state="source",
            condition=reject,
            priority=-4,
            internal=True,
        )
        def go(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("rejected declarative handler must not run")

    source = Source("source")
    later = State("later")
    machine = (
        FSMBuilder(source)
        .add_state(later)
        .add_transition(
            "go",
            "source",
            "later",
            lambda *_args, **_kwargs: events.append("lower-candidate") or True,
            priority=3,
        )
        .build()
    )
    machine.enable_history()

    result = machine.trigger("go")

    assert result.success is False
    assert result.rejected is True
    assert result.rejection_code == "mission.altitude_limit"
    assert result.priority == -4
    assert result.internal is True
    assert result.committed is False
    assert machine.current_state is source
    assert machine.history == []
    assert events == ["declarative-guard"]


def test_internal_declaration_never_binds_an_external_manual_edge() -> None:
    """The legacy external-to-internal fallback remains deliberately one-way."""
    events: list[str] = []

    def must_not_run(*_args: object, **_kwargs: object) -> bool:
        events.append("guard")
        return True

    class Source(DeclarativeState):
        @transition("go", to_state="source", condition=must_not_run, internal=True)
        def go(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("internal declaration must not bind external edge")

    source = Source("source")
    machine = StateMachine(source)
    machine.add_transition("go", source, source)

    result = machine.trigger("go")

    assert result.success is True
    assert result.internal is False
    assert events == []
