"""
Boundary and negative tests for core FSM operations.

Covers: empty names, duplicates, None arguments, invalid operations,
edge cases in add_state, add_transition, trigger, from_states, quick_build.

All tests use real FSM components — no mocking.
"""

import pytest

from fast_fsm.core import State, StateMachine, TransitionResult
from fast_fsm.conditions import Condition


# ---------------------------------------------------------------------------
# State edge cases
# ---------------------------------------------------------------------------


class TestStateEdgeCases:
    def test_empty_string_name(self):
        """State with an empty name — should not crash."""
        s = State("")
        assert s.name == ""

    def test_whitespace_name(self):
        s = State("  ")
        assert s.name == "  "

    def test_state_str_repr(self):
        s = State("idle")
        assert str(s) == "idle"
        assert "idle" in repr(s)

    def test_state_on_enter_default_noop(self):
        """Base State.on_enter does nothing (no crash)."""
        s = State("s")
        s.on_enter(State("from"), "t")  # should not raise

    def test_state_on_exit_default_noop(self):
        s = State("s")
        s.on_exit(State("to"), "t")

    def test_state_can_transition_default_true(self):
        """Base State.can_transition returns True."""
        s = State("s")
        assert s.can_transition("trigger", State("other")) is True

    def test_state_handle_event_returns_result(self):
        s = State("s")
        result = s.handle_event("evt")
        assert isinstance(result, TransitionResult)


# ---------------------------------------------------------------------------
# StateMachine construction edge cases
# ---------------------------------------------------------------------------


class TestStateMachineConstruction:
    def test_single_state_fsm(self):
        fsm = StateMachine(State("only"), name="solo")
        assert fsm.states == ["only"]
        assert fsm.triggers == []

    def test_add_state_already_exists(self):
        """Adding a state with a duplicate name — behaviour depends on impl."""
        fsm = StateMachine(State("a"), name="dup")
        fsm.add_state(State("b"))
        # Adding 'b' again — should overwrite silently (dict-based)
        fsm.add_state(State("b"))
        assert fsm.states.count("b") == 1

    def test_from_states_no_args_raises(self):
        with pytest.raises(ValueError, match="At least one state name"):
            StateMachine.from_states()

    def test_from_states_single(self):
        fsm = StateMachine.from_states("only")
        assert fsm.current_state.name == "only"

    def test_from_states_initial_not_found_raises(self):
        with pytest.raises(StopIteration):
            StateMachine.from_states("a", "b", initial="nonexistent")

    def test_quick_build_empty_transitions(self):
        fsm = StateMachine.quick_build("idle", [])
        assert fsm.current_state.name == "idle"
        assert fsm.triggers == []

    def test_default_name(self):
        fsm = StateMachine(State("s"))
        assert fsm.name == "FSM"


# ---------------------------------------------------------------------------
# Transition edge cases
# ---------------------------------------------------------------------------


class TestTransitionEdgeCases:
    def test_trigger_nonexistent_trigger(self):
        fsm = StateMachine(State("a"), name="test")
        result = fsm.trigger("nonexistent")
        assert not result.success
        assert "No transition" in result.error

    def test_trigger_from_wrong_state(self):
        fsm = StateMachine.quick_build("a", [("go", "a", "b"), ("ret", "b", "a")])
        # We're in "a", trigger "ret" which only works from "b"
        result = fsm.trigger("ret")
        assert not result.success

    def test_self_transition(self):
        """A trigger that loops back to the same state."""
        fsm = StateMachine(State("loop"), name="self")
        fsm.add_transition("spin", "loop", "loop")
        result = fsm.trigger("spin")
        assert result.success
        assert fsm.current_state.name == "loop"

    def test_multiple_source_states(self):
        fsm = StateMachine.from_states("a", "b", "c", initial="a")
        fsm.add_transition("next", "a", "b")
        fsm.add_transition("reset", ["a", "b", "c"], "a")
        fsm.trigger("next")
        assert fsm.current_state.name == "b"
        result = fsm.trigger("reset")
        assert result.success
        assert fsm.current_state.name == "a"

    def test_add_transitions_batch(self):
        fsm = StateMachine.from_states("a", "b", "c", initial="a")
        fsm.add_transitions(
            [
                ("go_b", "a", "b"),
                ("go_c", "b", "c"),
                ("reset", "c", "a"),
            ]
        )
        assert fsm.trigger("go_b").success
        assert fsm.trigger("go_c").success
        assert fsm.trigger("reset").success
        assert fsm.current_state.name == "a"


# ---------------------------------------------------------------------------
# TransitionResult edge cases
# ---------------------------------------------------------------------------


class TestTransitionResult:
    def test_success_fields(self):
        r = TransitionResult(True, from_state="a", to_state="b", trigger="go")
        assert r.success is True
        assert r.from_state == "a"
        assert r.to_state == "b"
        assert r.trigger == "go"
        assert r.error is None

    def test_failure_fields(self):
        r = TransitionResult(False, from_state="a", trigger="go", error="oops")
        assert r.success is False
        assert r.error == "oops"
        assert r.to_state is None

    def test_minimal_creation(self):
        r = TransitionResult(True)
        assert r.success
        assert r.from_state is None

    def test_repr(self):
        r = TransitionResult(True, from_state="a", to_state="b", trigger="go")
        text = repr(r)
        assert "True" in text or "success" in text.lower()


# ---------------------------------------------------------------------------
# safe_trigger
# ---------------------------------------------------------------------------


class TestSafeTrigger:
    def test_safe_trigger_normal(self):
        fsm = StateMachine.quick_build("a", [("go", "a", "b")])
        result = fsm.safe_trigger("go")
        assert result.success

    def test_safe_trigger_catches_exception(self):
        """safe_trigger wraps any exception into a TransitionResult."""

        class BombCondition(Condition):
            def __init__(self):
                super().__init__("bomb", "boom")

            def check(self, **kwargs) -> bool:
                raise RuntimeError("bomb went off")

        fsm = StateMachine(State("a"), name="bomb_test")
        fsm.add_state(State("b"))
        fsm.add_transition("go", "a", "b", BombCondition())

        # Normal trigger — condition exceptions are already caught by trigger()
        result = fsm.trigger("go")
        assert not result.success
        assert "bomb went off" in result.error

        # safe_trigger should also handle it gracefully
        fsm._current_state = fsm._states["a"]
        result = fsm.safe_trigger("go")
        assert not result.success


# ---------------------------------------------------------------------------
# can_trigger edge cases
# ---------------------------------------------------------------------------


class TestCanTrigger:
    def test_can_trigger_true(self):
        fsm = StateMachine.quick_build("a", [("go", "a", "b")])
        assert fsm.can_trigger("go")

    def test_can_trigger_false_wrong_state(self):
        fsm = StateMachine.quick_build("a", [("go", "a", "b")])
        fsm.trigger("go")  # now in "b"
        assert not fsm.can_trigger("go")

    def test_can_trigger_nonexistent(self):
        fsm = StateMachine(State("a"), name="test")
        assert not fsm.can_trigger("nonexistent")

    def test_can_trigger_with_failing_condition(self):
        class No(Condition):
            def __init__(self):
                super().__init__("no", "always no")

            def check(self, **kwargs) -> bool:
                return False

        fsm = StateMachine(State("a"), name="test")
        fsm.add_state(State("b"))
        fsm.add_transition("go", "a", "b", No())
        assert not fsm.can_trigger("go")
