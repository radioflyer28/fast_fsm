"""Focused observable-semantics oracle for Phase 30 construction adapters."""

from __future__ import annotations

import warnings

import pytest

from fast_fsm.core import (
    CallbackState,
    DeclarativeState,
    FSMBuilder,
    State,
    StateMachine,
    TransitionRejected,
    quick_fsm,
    simple_fsm,
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


def _exercise_final_and_internal_topology(machine: StateMachine) -> tuple[object, ...]:
    """Return the observable contract shared by every construction adapter."""
    events: list[str] = []
    machine.enable_history()
    machine.on_exit("source", lambda *_args, **_kwargs: events.append("exit"))
    machine.on_enter("done", lambda *_args, **_kwargs: events.append("enter"))
    machine.on_trigger(
        "refresh", lambda *_args, **_kwargs: events.append("refresh-trigger")
    )
    machine.on_trigger(
        "finish", lambda *_args, **_kwargs: events.append("finish-trigger")
    )

    refresh = machine.trigger("refresh")
    refresh_events = tuple(events)
    events.clear()
    finish = machine.trigger("finish")

    return (
        (refresh.success, refresh.committed, refresh.priority, refresh.internal),
        refresh_events,
        machine.history[0].internal,
        (finish.success, finish.committed, finish.priority, finish.internal),
        tuple(events),
        machine.current_state.name,
        machine.is_terminated,
        machine.history[1].internal,
    )


def _capture_deprecated_machine(factory) -> StateMachine:
    """Return one helper-built machine after proving its warning is contained."""
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        machine = factory()

    assert len(captured) == 1
    assert captured[0].category is DeprecationWarning
    return machine


def test_construction_parity_covers_final_destination_and_internal_batch_row() -> None:
    """Direct, batch, builder, declarative, and callback adapters agree visibly."""

    def direct() -> StateMachine:
        source = State("source")
        done = State("done", final=True)
        machine = StateMachine(source)
        machine.add_state(done)
        machine.add_transition("refresh", source, source, priority=-2, internal=True)
        machine.add_transition("finish", source, done, priority=4)
        return machine

    def batch() -> StateMachine:
        source = State("source")
        done = State("done", final=True)
        machine = StateMachine(source)
        machine.add_state(done)
        machine.add_transitions(
            [
                ("refresh", source, source, None, -2, None, None, True),
                ("finish", source, done, None, 4),
            ]
        )
        return machine

    def builder() -> StateMachine:
        source = State("source")
        done = State("done", final=True)
        return (
            FSMBuilder(source)
            .add_state(done)
            .add_transition("refresh", "source", "source", priority=-2, internal=True)
            .add_transition("finish", "source", "done", priority=4)
            .build()
        )

    def declarative() -> StateMachine:
        class Source(DeclarativeState):
            @transition(
                "refresh",
                from_state="source",
                to_state="source",
                priority=-2,
                internal=True,
            )
            def refresh(self, *_args: object, **_kwargs: object) -> bool:
                return True

            @transition("finish", from_state="source", to_state="done", priority=4)
            def finish(self, *_args: object, **_kwargs: object) -> bool:
                return True

        return FSMBuilder(Source("source")).add_state(State("done", final=True)).build()

    def callback() -> StateMachine:
        source = CallbackState("source", lambda *_args, **_kwargs: None)
        done = CallbackState("done", lambda *_args, **_kwargs: None, final=True)
        machine = StateMachine(source)
        machine.add_state(done)
        machine.add_transition("refresh", source, source, priority=-2, internal=True)
        machine.add_transition("finish", source, done, priority=4)
        return machine

    machines = (direct(), batch(), builder(), declarative(), callback())
    outcomes = tuple(
        _exercise_final_and_internal_topology(machine) for machine in machines
    )
    expected = outcomes[0]

    for machine, outcome in zip(machines, outcomes, strict=True):
        assert machine._states["source"] is machine._initial_state
        assert machine._states["done"].final is True
        assert outcome == expected


@pytest.mark.parametrize(
    "factory",
    (
        lambda: simple_fsm("source", "done", initial="source"),
        lambda: StateMachine.from_states("source", "done", initial="source"),
    ),
    ids=("simple_fsm", "from_states"),
)
def test_deprecated_state_only_helpers_keep_identity_and_mode_registration_parity(
    factory,
) -> None:
    """State-only helpers stay ordinary adapters after their one warning."""
    machine = _capture_deprecated_machine(factory)
    source = machine._states["source"]
    done = machine._states["done"]

    machine.add_transition("refresh", source, source, priority=-2, internal=True)
    machine.add_transition("finish", source, done, priority=4)
    outcome = _exercise_final_and_internal_topology(machine)

    assert source is machine._initial_state
    assert done.final is False
    assert outcome[0] == (True, True, -2, True)
    assert outcome[6] is False


@pytest.mark.parametrize(
    "factory",
    ("quick_build", "quick_fsm"),
)
def test_deprecated_quick_helpers_keep_final_internal_priority_and_atomicity(
    factory: str,
) -> None:
    """Quick helpers retain the canonical final/internal transaction."""

    def rows(source: State, done: State) -> list[tuple[object, ...]]:
        return [
            (
                "refresh",
                source,
                source,
                lambda *_args, **_kwargs: False,
                -3,
                None,
                None,
                True,
            ),
            (
                "refresh",
                source,
                source,
                lambda *_args, **_kwargs: True,
                2,
                None,
                None,
                True,
            ),
            ("finish", source, done, None, 4),
        ]

    source = State("source")
    done = State("done", final=True)
    transition_rows = rows(source, done)
    if factory == "quick_build":
        machine = _capture_deprecated_machine(
            lambda: StateMachine.quick_build(source, transition_rows)
        )
    else:
        machine = _capture_deprecated_machine(
            lambda: quick_fsm("source", transition_rows)
        )

    machine.enable_history()
    refresh = machine.trigger("refresh")
    finish = machine.trigger("finish")

    assert machine._states["source"] is source
    assert machine._states["done"] is done
    assert refresh.success is True
    assert refresh.priority == 2
    assert refresh.internal is True
    assert finish.success is True
    assert finish.internal is False
    assert machine.is_terminated is True

    result = None
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with pytest.raises(TypeError, match="priority"):
            if factory == "quick_build":
                result = StateMachine.quick_build(
                    "source",
                    [
                        ("valid", "source", "done"),
                        ("broken", "source", "done", None, True),
                    ],
                )
            else:
                result = quick_fsm(
                    "source",
                    [
                        ("valid", "source", "done"),
                        ("broken", "source", "done", None, True),
                    ],
                )

    assert result is None
    assert len(captured) == 1
