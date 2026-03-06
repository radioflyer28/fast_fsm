#!/usr/bin/env python3
"""
Advanced Functionality Tests

Tests for advanced StateMachine features that weren't covered in basic tests.
Focuses on Priority 1 gaps identified in coverage analysis.
"""

from fast_fsm import State, StateMachine, Condition


class TestAdvancedTransitions:
    """Test advanced transition methods"""

    def test_add_bidirectional_transition(self):
        """Test adding bidirectional transitions between states"""
        running = State("running")
        paused = State("paused")

        fsm = StateMachine(running, name="bidirectional_test")
        fsm.add_state(paused)

        # Add bidirectional transition
        fsm.add_bidirectional_transition("pause", "resume", "running", "paused")

        # Test transition from running to paused
        result = fsm.trigger("pause")
        assert result.success
        assert fsm.current_state.name == "paused"

        # Test reverse transition from paused to running
        result = fsm.trigger("resume")
        assert result.success
        assert fsm.current_state.name == "running"

        # Verify both directions exist
        assert fsm.transition_exists("pause", "running", "paused")
        assert fsm.transition_exists("resume", "paused", "running")

    def test_add_bidirectional_transition_with_conditions(self):
        """Test bidirectional transitions with different conditions"""

        class EnergyCondition(Condition):
            def __init__(self, min_energy):
                super().__init__(
                    f"energy_{min_energy}", f"Requires at least {min_energy} energy"
                )
                self.min_energy = min_energy

            def check(self, **kwargs):
                return kwargs.get("energy", 0) >= self.min_energy

        running = State("running")
        paused = State("paused")

        fsm = StateMachine(running, name="conditional_bidirectional")
        fsm.add_state(paused)

        # Add bidirectional transition with different conditions
        pause_condition = EnergyCondition(0)  # Can always pause
        resume_condition = EnergyCondition(10)  # Need energy to resume

        fsm.add_bidirectional_transition(
            "pause", "resume", "running", "paused", pause_condition, resume_condition
        )

        # Can pause without energy
        result = fsm.trigger("pause", energy=0)
        assert result.success
        assert fsm.current_state.name == "paused"

        # Cannot resume without enough energy
        result = fsm.trigger("resume", energy=5)
        assert not result.success
        assert fsm.current_state.name == "paused"

        # Can resume with enough energy
        result = fsm.trigger("resume", energy=15)
        assert result.success
        assert fsm.current_state.name == "running"

    def test_add_emergency_transition(self):
        """Test adding emergency transitions from all states"""
        idle = State("idle")
        processing = State("processing")
        completing = State("completing")
        error = State("error")

        fsm = StateMachine(idle, name="emergency_test")
        for state in [processing, completing, error]:
            fsm.add_state(state)

        # Add normal transitions
        fsm.add_transition("start", "idle", "processing")
        fsm.add_transition("finish", "processing", "completing")
        fsm.add_transition("complete", "completing", "idle")

        # Add emergency transition from ALL states to error state
        fsm.add_emergency_transition("emergency_stop", "error")

        # Test emergency from idle
        result = fsm.trigger("emergency_stop")
        assert result.success
        assert fsm.current_state.name == "error"

        # Reset to processing state
        fsm._current_state = processing
        result = fsm.trigger("emergency_stop")
        assert result.success
        assert fsm.current_state.name == "error"

        # Reset to completing state
        fsm._current_state = completing
        result = fsm.trigger("emergency_stop")
        assert result.success
        assert fsm.current_state.name == "error"

        # Verify emergency transition exists from all states
        for state_name in ["idle", "processing", "completing", "error"]:
            assert fsm.transition_exists("emergency_stop", state_name, "error")

    def test_add_emergency_transition_with_condition(self):
        """Test emergency transition with condition"""

        class CriticalCondition(Condition):
            def __init__(self):
                super().__init__("critical", "Critical situation detected")

            def check(self, **kwargs):
                return kwargs.get("critical", False)

        idle = State("idle")
        processing = State("processing")
        emergency = State("emergency")

        fsm = StateMachine(idle, name="conditional_emergency")
        fsm.add_state(processing)
        fsm.add_state(emergency)

        fsm.add_transition("start", "idle", "processing")

        # Add conditional emergency transition
        critical_condition = CriticalCondition()
        fsm.add_emergency_transition("alert", "emergency", critical_condition)

        # Should not trigger without critical flag
        result = fsm.trigger("alert", critical=False)
        assert not result.success
        assert fsm.current_state.name == "idle"

        # Should trigger with critical flag
        result = fsm.trigger("alert", critical=True)
        assert result.success
        assert fsm.current_state.name == "emergency"


class TestStateTriggerMethods:
    """Test different trigger methods and their behavior"""

    def test_safe_trigger_vs_trigger(self):
        """Test differences between safe_trigger and trigger methods"""

        class ExceptionCondition(Condition):
            def __init__(self, should_raise=False):
                super().__init__(
                    "exception_test", "Condition that can raise exceptions"
                )
                self.should_raise = should_raise

            def check(self, **kwargs):
                if self.should_raise:
                    raise ValueError("Condition evaluation failed")
                return True

        state1 = State("state1")
        state2 = State("state2")

        fsm = StateMachine(state1, name="trigger_test")
        fsm.add_state(state2)

        # Add transition with condition that can raise exception
        condition = ExceptionCondition(should_raise=True)
        fsm.add_transition("test", "state1", "state2", condition)

        # Regular trigger should handle the exception gracefully
        result = fsm.trigger("test")
        assert not result.success
        assert result.error and "raised exception" in result.error
        assert fsm.current_state.name == "state1"

        # safe_trigger should also handle the exception gracefully
        result = fsm.safe_trigger("test")
        assert not result.success
        assert result.error and "raised exception" in result.error
        assert fsm.current_state.name == "state1"

        # Test with non-exception condition
        condition.should_raise = False
        result = fsm.trigger("test")
        assert result.success
        assert fsm.current_state.name == "state2"

        # Reset and test safe_trigger with good condition
        fsm._current_state = state1
        result = fsm.safe_trigger("test")
        assert result.success
        assert fsm.current_state.name == "state2"

    def test_safe_trigger_with_invalid_trigger(self):
        """Test safe_trigger with completely invalid trigger"""
        state1 = State("state1")
        fsm = StateMachine(state1, name="safe_trigger_test")

        # Test invalid trigger with regular trigger
        result = fsm.trigger("nonexistent")
        assert not result.success
        assert "No transition" in result.error

        # Test invalid trigger with safe_trigger
        result = fsm.safe_trigger("nonexistent")
        assert not result.success
        assert "No transition" in result.error


class TestStateCallbacks:
    """Test state entry and exit callbacks thoroughly"""

    def test_on_enter_on_exit_execution_order(self):
        """Test that callbacks execute in correct order during transitions"""
        execution_log = []

        def log_enter_state1(*args, **kwargs):
            execution_log.append("enter_state1")

        def log_exit_state1(*args, **kwargs):
            execution_log.append("exit_state1")

        def log_enter_state2(*args, **kwargs):
            execution_log.append("enter_state2")

        def log_exit_state2(*args, **kwargs):
            execution_log.append("exit_state2")

        def log_enter_state3(*args, **kwargs):
            execution_log.append("enter_state3")

        state1 = State.create("state1", on_exit=log_exit_state1)
        state2 = State.create(
            "state2", on_enter=log_enter_state2, on_exit=log_exit_state2
        )
        state3 = State.create("state3", on_enter=log_enter_state3)

        fsm = StateMachine(initial_state=state1, name="callback_order_test")
        fsm.add_state(state2)
        fsm.add_state(state3)

        fsm.add_transition("go12", "state1", "state2")
        fsm.add_transition("go23", "state2", "state3")

        execution_log.clear()

        # First transition: state1 -> state2
        result = fsm.trigger("go12")
        assert result.success
        assert execution_log == ["exit_state1", "enter_state2"]

        execution_log.clear()

        # Second transition: state2 -> state3
        result = fsm.trigger("go23")
        assert result.success
        assert execution_log == ["exit_state2", "enter_state3"]

    def test_callback_exception_handling(self):
        """Test that exceptions in callbacks don't break transitions"""

        def failing_exit(*args, **kwargs):
            raise RuntimeError("Exit callback failed")

        def failing_enter(*args, **kwargs):
            raise RuntimeError("Enter callback failed")

        # Test exit callback exception
        state1 = State.create("state1", on_exit=failing_exit)
        state2 = State("state2")

        fsm = StateMachine(initial_state=state1, name="callback_exception_test")
        fsm.add_state(state2)
        fsm.add_transition("go", "state1", "state2")

        # Transition should succeed even with exit callback exception
        result = fsm.trigger("go")
        assert result.success  # Transition still completes
        assert fsm.current_state.name == "state2"

        # Test enter callback exception
        state3 = State.create("state3", on_enter=failing_enter)
        fsm.add_state(state3)
        fsm.add_transition("go_again", "state2", "state3")

        # Transition should succeed even with enter callback exception
        result = fsm.trigger("go_again")
        assert result.success  # Transition still completes
        assert fsm.current_state.name == "state3"

    def test_callback_with_args_and_kwargs(self):
        """Test that callbacks receive correct arguments"""
        received_args = {}

        def capture_exit_args(*args, **kwargs):
            received_args["exit_args"] = args
            received_args["exit_kwargs"] = kwargs

        def capture_enter_args(*args, **kwargs):
            received_args["enter_args"] = args
            received_args["enter_kwargs"] = kwargs

        state1 = State.create("state1", on_exit=capture_exit_args)
        state2 = State.create("state2", on_enter=capture_enter_args)

        fsm = StateMachine(initial_state=state1, name="callback_args_test")
        fsm.add_state(state2)
        fsm.add_transition("transfer", "state1", "state2")

        received_args.clear()

        # Trigger with arguments
        result = fsm.trigger("transfer", "arg1", "arg2", key1="value1", key2="value2")
        assert result.success

        # Check that callbacks received the arguments
        assert "exit_args" in received_args
        assert "enter_args" in received_args

        # on_exit receives (to_state, trigger, *user_args)
        exit_args = received_args["exit_args"]
        assert exit_args[0].name == "state2"  # to_state
        assert exit_args[1] == "transfer"  # trigger
        assert exit_args[2:] == ("arg1", "arg2")

        # on_enter receives (from_state, trigger, *user_args)
        enter_args = received_args["enter_args"]
        assert enter_args[0].name == "state1"  # from_state
        assert enter_args[1] == "transfer"  # trigger
        assert enter_args[2:] == ("arg1", "arg2")

        # Both callbacks receive the kwargs
        assert received_args["exit_kwargs"] == {"key1": "value1", "key2": "value2"}
        assert received_args["enter_kwargs"] == {"key1": "value1", "key2": "value2"}


class TestBatchOperations:
    """Test batch transition operations"""

    def test_add_transitions_batch(self):
        """Test adding multiple transitions at once"""
        idle = State("idle")
        running = State("running")
        paused = State("paused")
        stopped = State("stopped")

        fsm = StateMachine(idle, name="batch_test")
        for state in [running, paused, stopped]:
            fsm.add_state(state)

        # Add multiple transitions at once
        transitions = [
            ("start", "idle", "running"),
            ("pause", "running", "paused"),
            ("resume", "paused", "running"),
            ("stop", ["running", "paused"], "stopped"),  # Multiple source states
            ("reset", "stopped", "idle"),
        ]

        fsm.add_transitions(transitions)

        # Test the transitions work
        assert fsm.trigger("start").success
        assert fsm.current_state.name == "running"

        assert fsm.trigger("pause").success
        assert fsm.current_state.name == "paused"

        assert fsm.trigger("stop").success
        assert fsm.current_state.name == "stopped"

        assert fsm.trigger("reset").success
        assert fsm.current_state.name == "idle"

        # Test stop from running state
        fsm.trigger("start")  # idle -> running
        assert fsm.trigger("stop").success
        assert fsm.current_state.name == "stopped"

        # Verify all transitions exist
        assert fsm.transition_exists("start", "idle", "running")
        assert fsm.transition_exists("pause", "running", "paused")
        assert fsm.transition_exists("resume", "paused", "running")
        assert fsm.transition_exists("stop", "running", "stopped")
        assert fsm.transition_exists("stop", "paused", "stopped")
        assert fsm.transition_exists("reset", "stopped", "idle")

    def test_add_transitions_with_state_objects(self):
        """Test batch transitions using State objects instead of strings"""
        idle = State("idle")
        active = State("active")

        fsm = StateMachine(idle, name="batch_objects_test")
        fsm.add_state(active)

        # Use actual State objects in transitions list
        from typing import List, Tuple, Union

        transitions: List[
            Tuple[str, Union[str, State, List[Union[str, State]]], Union[str, State]]
        ] = [("activate", idle, active), ("deactivate", active, idle)]

        fsm.add_transitions(transitions)

        # Test transitions work
        assert fsm.trigger("activate").success
        assert fsm.current_state.name == "active"

        assert fsm.trigger("deactivate").success
        assert fsm.current_state.name == "idle"


class TestForceStateAndReset:
    """Tests for force_state(), reset(), and initial_state_name."""

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _make_fsm(self):
        """idle -> running -> done, no guards."""
        idle = State("idle")
        running = State("running")
        done = State("done")
        fsm = StateMachine(idle, name="test_fsm")
        fsm.add_state(running)
        fsm.add_state(done)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("finish", "running", "done")
        return fsm

    # ------------------------------------------------------------------
    # initial_state_name property
    # ------------------------------------------------------------------

    def test_initial_state_name(self):
        """initial_state_name always reflects the constructor argument."""
        fsm = self._make_fsm()
        assert fsm.initial_state_name == "idle"

    def test_initial_state_name_unchanged_after_transitions(self):
        fsm = self._make_fsm()
        fsm.trigger("start")
        fsm.trigger("finish")
        assert fsm.initial_state_name == "idle"

    # ------------------------------------------------------------------
    # force_state() — basic behaviour
    # ------------------------------------------------------------------

    def test_force_state_changes_current_state(self):
        fsm = self._make_fsm()
        fsm.force_state("done")
        assert fsm.current_state_name == "done"

    def test_force_state_bypasses_guard(self):
        """force_state sets state even when no transition path exists."""
        from fast_fsm import Condition

        class AlwaysFail(Condition):
            def __init__(self):
                super().__init__("never", "always blocks")

            def check(self, **kwargs):
                return False

        idle = State("idle")
        locked = State("locked")
        fsm = StateMachine(idle, name="guarded")
        fsm.add_state(locked)
        fsm.add_transition("go", "idle", "locked", condition=AlwaysFail())

        # Normal trigger fails due to guard
        assert not fsm.trigger("go").success
        assert fsm.current_state_name == "idle"

        # force_state bypasses the guard entirely
        fsm.force_state("locked")
        assert fsm.current_state_name == "locked"

    def test_force_state_self(self):
        """Forcing into the current state is a no-op for state but still
        fires callbacks."""
        fsm = self._make_fsm()
        exits = []
        enters = []

        class L:
            def on_exit_state(self, old, new, t, **kw):
                exits.append(old.name)

            def on_enter_state(self, new, old, t, **kw):
                enters.append(new.name)

        fsm.add_listener(L())
        fsm.force_state("idle")  # already in idle
        assert fsm.current_state_name == "idle"
        assert exits == ["idle"]
        assert enters == ["idle"]

    def test_force_state_unknown_raises_key_error(self):
        import pytest

        fsm = self._make_fsm()
        with pytest.raises(KeyError, match="nonexistent"):
            fsm.force_state("nonexistent")

    # ------------------------------------------------------------------
    # force_state() — listener / callback firing
    # ------------------------------------------------------------------

    def test_force_state_fires_on_exit_listener(self):
        fsm = self._make_fsm()
        events = []

        class L:
            def on_exit_state(self, old, new, t, **kw):
                events.append(("exit", old.name, new.name, t))

        fsm.add_listener(L())
        fsm.force_state("running")
        assert events == [("exit", "idle", "running", "__force__")]

    def test_force_state_fires_on_enter_listener(self):
        fsm = self._make_fsm()
        events = []

        class L:
            def on_enter_state(self, new, old, t, **kw):
                events.append(("enter", new.name, old.name, t))

        fsm.add_listener(L())
        fsm.force_state("running")
        assert events == [("enter", "running", "idle", "__force__")]

    def test_force_state_fires_after_transition_listener(self):
        fsm = self._make_fsm()
        events = []

        class L:
            def after_transition(self, old, new, t, **kw):
                events.append(("after", old.name, new.name, t))

        fsm.add_listener(L())
        fsm.force_state("done")
        assert events == [("after", "idle", "done", "__force__")]

    def test_force_state_fires_callback_state_callbacks(self):
        """CallbackState on_exit / on_enter fire via _execute_transition."""
        from fast_fsm import CallbackState

        exits = []
        enters = []
        idle = CallbackState("idle", on_exit=lambda to, t, **kw: exits.append(to.name))
        running = CallbackState(
            "running", on_enter=lambda frm, t, **kw: enters.append(frm.name)
        )

        fsm = StateMachine(idle, name="cb_test")
        fsm.add_state(running)

        fsm.force_state("running")
        assert exits == ["running"]
        assert enters == ["idle"]

    def test_force_state_all_listeners_order(self):
        """on_exit fires before on_enter, after_transition fires last."""
        from fast_fsm import CallbackState

        order = []
        idle = CallbackState(
            "idle",
            on_exit=lambda to, t, **kw: order.append("state.on_exit"),
        )
        done = CallbackState(
            "done",
            on_enter=lambda frm, t, **kw: order.append("state.on_enter"),
        )
        fsm = StateMachine(idle, name="order_test")
        fsm.add_state(done)

        class L:
            def on_exit_state(self, *a, **kw):
                order.append("listener.on_exit")

            def on_enter_state(self, *a, **kw):
                order.append("listener.on_enter")

            def after_transition(self, *a, **kw):
                order.append("listener.after")

        fsm.add_listener(L())

        fsm.force_state("done")
        assert order == [
            "state.on_exit",
            "listener.on_exit",
            "state.on_enter",
            "listener.on_enter",
            "listener.after",
        ]

    # ------------------------------------------------------------------
    # reset()
    # ------------------------------------------------------------------

    def test_reset_returns_to_initial(self):
        fsm = self._make_fsm()
        fsm.trigger("start")
        fsm.trigger("finish")
        assert fsm.current_state_name == "done"

        fsm.reset()
        assert fsm.current_state_name == "idle"

    def test_reset_fires_callbacks(self):
        fsm = self._make_fsm()
        fsm.trigger("start")

        events = []

        class L:
            def on_enter_state(self, new, old, t, **kw):
                events.append(new.name)

        fsm.add_listener(L())
        fsm.reset()

        assert events == ["idle"]

    def test_reset_when_already_initial(self):
        """reset() is safe when already in the initial state."""
        fsm = self._make_fsm()
        enters = []

        class L:
            def on_enter_state(self, new, old, t, **kw):
                enters.append(new.name)

        fsm.add_listener(L())
        fsm.reset()  # already at idle
        assert fsm.current_state_name == "idle"
        assert enters == ["idle"]  # callbacks still fire

    def test_reset_then_transition_works(self):
        """After reset(), normal transition path is usable again."""
        fsm = self._make_fsm()
        fsm.trigger("start")
        fsm.trigger("finish")
        fsm.reset()

        result = fsm.trigger("start")
        assert result.success
        assert fsm.current_state_name == "running"
