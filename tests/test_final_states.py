"""Behavioral contract for explicit final-state semantics."""

import pytest

from fast_fsm.core import State, StateMachine


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
