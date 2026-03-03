"""
Tests for StateMachine properties and utility methods.

Covers: name, current_state, current_state_name, states, triggers,
get_available_triggers, get_reachable_states, transition_exists,
debug_info, print_debug_info, validate_transition_completeness.

All tests use real FSM components — no mocking.
"""

import pytest

from fast_fsm.core import State, StateMachine, CallbackState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def traffic_light_fsm():
    """3-state cyclic FSM: red → green → yellow → red."""
    fsm = StateMachine.quick_build(
        "red",
        [
            ("timer", "red", "green"),
            ("timer", "green", "yellow"),
            ("timer", "yellow", "red"),
        ],
        name="TrafficLight",
    )
    return fsm


@pytest.fixture
def linear_fsm():
    """Linear FSM: a → b → c (no return path)."""
    fsm = StateMachine.quick_build(
        "a",
        [("next", "a", "b"), ("next", "b", "c")],
        name="Linear",
    )
    return fsm


# ---------------------------------------------------------------------------
# Property accessors
# ---------------------------------------------------------------------------


class TestProperties:
    def test_name(self, traffic_light_fsm):
        assert traffic_light_fsm.name == "TrafficLight"

    def test_current_state_returns_state(self, traffic_light_fsm):
        state = traffic_light_fsm.current_state
        assert isinstance(state, State)
        assert state.name == "red"

    def test_current_state_name(self, traffic_light_fsm):
        assert traffic_light_fsm.current_state_name == "red"

    def test_current_state_name_updates_after_trigger(self, traffic_light_fsm):
        traffic_light_fsm.trigger("timer")
        assert traffic_light_fsm.current_state_name == "green"

    def test_states_returns_all_names(self, traffic_light_fsm):
        assert set(traffic_light_fsm.states) == {"red", "green", "yellow"}

    def test_triggers_returns_all_triggers(self, traffic_light_fsm):
        assert set(traffic_light_fsm.triggers) == {"timer"}

    def test_triggers_multi(self, linear_fsm):
        # linear_fsm uses "next" from two states — still just one trigger name
        assert "next" in linear_fsm.triggers


# ---------------------------------------------------------------------------
# get_available_triggers
# ---------------------------------------------------------------------------


class TestGetAvailableTriggers:
    def test_default_uses_current_state(self, traffic_light_fsm):
        triggers = traffic_light_fsm.get_available_triggers()
        assert "timer" in triggers

    def test_explicit_state(self, traffic_light_fsm):
        triggers = traffic_light_fsm.get_available_triggers("green")
        assert "timer" in triggers

    def test_dead_end_state_returns_empty(self, linear_fsm):
        # "c" has no outgoing transitions
        assert linear_fsm.get_available_triggers("c") == []

    def test_nonexistent_state_returns_empty(self, linear_fsm):
        assert linear_fsm.get_available_triggers("nonexistent") == []


# ---------------------------------------------------------------------------
# get_reachable_states
# ---------------------------------------------------------------------------


class TestGetReachableStates:
    def test_default_uses_current_state(self, traffic_light_fsm):
        reachable = traffic_light_fsm.get_reachable_states()
        assert "green" in reachable

    def test_explicit_from_state(self, traffic_light_fsm):
        reachable = traffic_light_fsm.get_reachable_states("green")
        assert "yellow" in reachable

    def test_dead_end_has_no_reachable(self, linear_fsm):
        assert linear_fsm.get_reachable_states("c") == []


# ---------------------------------------------------------------------------
# transition_exists
# ---------------------------------------------------------------------------


class TestTransitionExists:
    def test_exists(self, traffic_light_fsm):
        assert traffic_light_fsm.transition_exists("timer", "red", "green")

    def test_wrong_to_state(self, traffic_light_fsm):
        assert not traffic_light_fsm.transition_exists("timer", "red", "yellow")

    def test_wrong_trigger(self, traffic_light_fsm):
        assert not traffic_light_fsm.transition_exists("nonexistent", "red")

    def test_defaults_to_current_state(self, traffic_light_fsm):
        # Current state is "red", so "timer" from red should exist
        assert traffic_light_fsm.transition_exists("timer")


# ---------------------------------------------------------------------------
# debug_info / print_debug_info
# ---------------------------------------------------------------------------


class TestDebugInfo:
    def test_debug_info_structure(self, traffic_light_fsm):
        info = traffic_light_fsm.debug_info()
        assert info["name"] == "TrafficLight"
        assert info["current_state"] == "red"
        assert set(info["states"]) == {"red", "green", "yellow"}
        assert "timer" in info["triggers"]
        assert "timer" in info["available_triggers"]
        assert "green" in info["reachable_states"]
        assert info["transition_count"] == 3

    def test_debug_info_after_transition(self, traffic_light_fsm):
        traffic_light_fsm.trigger("timer")
        info = traffic_light_fsm.debug_info()
        assert info["current_state"] == "green"
        assert "yellow" in info["reachable_states"]

    def test_print_debug_info_produces_output(self, traffic_light_fsm, capsys):
        traffic_light_fsm.print_debug_info()
        captured = capsys.readouterr()
        assert "TrafficLight" in captured.out
        assert "red" in captured.out
        assert "timer" in captured.out


# ---------------------------------------------------------------------------
# validate_transition_completeness
# ---------------------------------------------------------------------------


class TestValidateTransitionCompleteness:
    def test_linear_fsm_has_dead_end(self, linear_fsm):
        issues = linear_fsm.validate_transition_completeness()
        assert "c" in issues["dead_end_states"]

    def test_cyclic_fsm_no_dead_ends(self, traffic_light_fsm):
        issues = traffic_light_fsm.validate_transition_completeness()
        assert issues["dead_end_states"] == []

    def test_unreachable_state_detected(self):
        fsm = StateMachine.from_states("a", "b", "orphan", initial="a", name="test")
        fsm.add_transition("go", "a", "b")
        issues = fsm.validate_transition_completeness()
        assert "orphan" in issues["unreachable_states"]

    def test_well_formed_has_no_issues(self, traffic_light_fsm):
        issues = traffic_light_fsm.validate_transition_completeness()
        assert issues["dead_end_states"] == []
        assert issues["unreachable_states"] == []


# ---------------------------------------------------------------------------
# CallbackState
# ---------------------------------------------------------------------------


class TestCallbackState:
    def test_callback_state_creation(self):
        cs = CallbackState("test")
        assert cs.name == "test"

    def test_on_enter_callback(self):
        log = []
        cs = CallbackState("s", on_enter=lambda *a, **kw: log.append("enter"))
        cs.on_enter(State("from"), "trigger")
        assert log == ["enter"]

    def test_on_exit_callback(self):
        log = []
        cs = CallbackState("s", on_exit=lambda *a, **kw: log.append("exit"))
        cs.on_exit(State("to"), "trigger")
        assert log == ["exit"]

    def test_no_callbacks_does_nothing(self):
        cs = CallbackState("s")
        cs.on_enter(State("from"), "trigger")  # should not raise
        cs.on_exit(State("to"), "trigger")

    def test_callback_state_in_fsm(self):
        log = []
        a = CallbackState("a", on_exit=lambda *args, **kw: log.append("exit_a"))
        b = CallbackState("b", on_enter=lambda *args, **kw: log.append("enter_b"))
        fsm = StateMachine(a, name="cb_test")
        fsm.add_state(b)
        fsm.add_transition("go", "a", "b")
        fsm.trigger("go")
        assert "exit_a" in log
        assert "enter_b" in log

    def test_state_create_returns_callback_state(self):
        """State.create() should produce a CallbackState."""
        cs = State.create("test", on_enter=lambda *a, **kw: None)
        assert isinstance(cs, CallbackState)
