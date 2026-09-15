"""Behavioral contract for explicit final-state semantics."""

import pytest

from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    CallbackState,
    DeclarativeState,
    State,
    StateMachine,
)


class _TruthyObject:
    """Fail if a final-state validator tries to coerce this instance."""

    def __bool__(self) -> bool:
        raise AssertionError("final validation must not coerce caller input")


class TestStateFinalMetadata:
    """Explicit state metadata is immutable, exact, and slotted."""

    def test_state_final_defaults_to_false_and_accepts_true_by_keyword(self) -> None:
        assert State("pending").final is False
        assert State("done", final=True).final is True

    def test_state_final_is_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            State("done", True)

    @pytest.mark.parametrize("value", [1, 0, "true", _TruthyObject()])
    def test_state_final_rejects_non_bool_without_coercion(self, value: object) -> None:
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            State("done", final=value)  # type: ignore[arg-type]

    def test_state_final_is_read_only_and_state_stays_slotted(self) -> None:
        state = State("done", final=True)

        with pytest.raises(AttributeError):
            state.final = False  # type: ignore[misc]
        with pytest.raises(AttributeError):
            _ = state.__dict__


class TestTerminationQuery:
    """Termination derives solely from the canonical current State."""

    def test_initial_final_state_is_terminated(self) -> None:
        done = State("done", final=True)
        machine = StateMachine(done)

        assert machine.current_state is done
        assert machine.is_terminated is True

    def test_async_machine_inherits_the_same_termination_query(self) -> None:
        machine = AsyncStateMachine(State("done", final=True))

        assert machine.is_terminated is True
        assert "is_terminated" not in AsyncStateMachine.__dict__

    def test_incoming_transition_to_final_state_is_terminated(self) -> None:
        idle = State("idle")
        done = State("done", final=True)
        machine = StateMachine(idle)
        machine.add_state(done)
        machine.add_transition("finish", idle, done)

        result = machine.trigger("finish")

        assert result.success is True
        assert machine.current_state is done
        assert machine.is_terminated is True


class TestFinalConstructionSurfaces:
    """Every public State constructor preserves exact immutable finality."""

    def test_state_create_preserves_callbacks_and_final_metadata(self) -> None:
        events: list[tuple[str, str, int, str]] = []

        def on_enter(
            _from_state: State | None, trigger: str, value: int, *, tag: str
        ) -> None:
            events.append(("enter", trigger, value, tag))

        def on_exit(
            _to_state: State | None, trigger: str, value: int, *, tag: str
        ) -> None:
            events.append(("exit", trigger, value, tag))

        state = State.create("done", on_enter, on_exit, final=True)

        state.on_enter(None, "finish", 1, tag="entry")
        state.on_exit(None, "reset", 2, tag="exit")

        assert state.final is True
        assert events == [
            ("enter", "finish", 1, "entry"),
            ("exit", "reset", 2, "exit"),
        ]

    def test_callback_state_preserves_callbacks_and_final_metadata(self) -> None:
        events: list[tuple[str, str]] = []
        state = CallbackState(
            "done",
            lambda _from_state, trigger, *args, **kwargs: events.append(
                ("enter", trigger)
            ),
            lambda _to_state, trigger, *args, **kwargs: events.append(
                ("exit", trigger)
            ),
            final=True,
        )

        state.on_enter(None, "finish")
        state.on_exit(None, "reset")

        assert state.final is True
        assert events == [("enter", "finish"), ("exit", "reset")]

    def test_declarative_state_surfaces_forward_final_metadata(self) -> None:
        declarative = DeclarativeState("done", "test.final", final=True)
        async_declarative = AsyncDeclarativeState(
            "async-done", "test.final", final=True
        )

        assert declarative.final is True
        assert async_declarative.final is True

    def test_all_explicit_construction_surfaces_reject_non_bool_final(self) -> None:
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            State.create("done", final=1)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            CallbackState("done", final=1)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            DeclarativeState("done", final=1)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            AsyncDeclarativeState("done", final=1)  # type: ignore[arg-type]

    def test_all_explicit_construction_surfaces_keep_final_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            State.create("done", None, None, True)
        with pytest.raises(TypeError):
            CallbackState("done", None, None, True)
        with pytest.raises(TypeError):
            DeclarativeState("done", "test.final", True)
        with pytest.raises(TypeError):
            AsyncDeclarativeState("done", "test.final", True)

    def test_interpreted_subclass_can_forward_final_to_base_state(self) -> None:
        class UserState(State):
            def __init__(self, name: str, *, final: bool = False) -> None:
                super().__init__(name, final=final)

        assert UserState("done", final=True).final is True

    def test_non_final_sink_is_not_terminated(self) -> None:
        sink = State("sink")
        machine = StateMachine(sink)

        assert machine.get_available_triggers() == []
        assert machine.is_terminated is False

    def test_trigger_from_final_uses_ordinary_missing_transition_result(self) -> None:
        done = State("done", final=True)
        machine = StateMachine(done)

        result = machine.trigger("finish")

        assert result.success is False
        assert result.error is not None
        assert "No transition" in result.error
        assert result.stage == "resolution"
        assert machine.current_state is done
        assert machine.is_terminated is True
