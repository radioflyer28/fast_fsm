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


class TestSnapshot:
    """Tests for snapshot() and restore()."""

    def _make_fsm(self):
        idle = State("idle")
        running = State("running")
        done = State("done")
        fsm = StateMachine(idle, name="snap_fsm")
        fsm.add_state(running)
        fsm.add_state(done)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("finish", "running", "done")
        return fsm

    # ------------------------------------------------------------------
    # snapshot()
    # ------------------------------------------------------------------

    def test_snapshot_initial_state(self):
        fsm = self._make_fsm()
        snap = fsm.snapshot()
        assert snap == {"state": "idle", "version": 1}

    def test_snapshot_after_transition(self):
        fsm = self._make_fsm()
        fsm.trigger("start")
        snap = fsm.snapshot()
        assert snap["state"] == "running"
        assert snap["version"] == 1

    def test_snapshot_returns_new_dict_each_call(self):
        fsm = self._make_fsm()
        s1 = fsm.snapshot()
        s2 = fsm.snapshot()
        assert s1 is not s2

    def test_snapshot_is_json_serialisable(self):
        import json

        fsm = self._make_fsm()
        fsm.trigger("start")
        assert json.dumps(fsm.snapshot())  # must not raise

    # ------------------------------------------------------------------
    # restore()
    # ------------------------------------------------------------------

    def test_restore_sets_state(self):
        fsm = self._make_fsm()
        snap = fsm.snapshot()  # idle
        fsm.trigger("start")
        fsm.restore(snap)
        assert fsm.current_state_name == "idle"

    def test_restore_fires_callbacks(self):
        fsm = self._make_fsm()
        fsm.trigger("start")
        snap = fsm.snapshot()  # running

        enters = []

        class L:
            def on_enter_state(self, new, old, t, **kw):
                enters.append(new.name)

        fsm.trigger("finish")  # now at done
        fsm.add_listener(L())
        fsm.restore(snap)  # back to running
        assert enters == ["running"]

    def test_restore_unknown_state_raises_key_error(self):
        import pytest

        fsm = self._make_fsm()
        with pytest.raises(KeyError):
            fsm.restore({"state": "nonexistent", "version": 1})

    def test_restore_bad_version_raises_value_error(self):
        import pytest

        fsm = self._make_fsm()
        with pytest.raises(ValueError, match="Unsupported snapshot version"):
            fsm.restore({"state": "idle", "version": 99})

    def test_restore_bad_state_type_raises_value_error(self):
        import pytest

        fsm = self._make_fsm()
        with pytest.raises(ValueError, match="must be a string"):
            fsm.restore({"state": 42, "version": 1})

    def test_snapshot_restore_roundtrip(self):
        """Full round-trip: advance, snapshot, advance more, restore."""
        fsm = self._make_fsm()
        fsm.trigger("start")
        snap = fsm.snapshot()

        fsm.trigger("finish")
        assert fsm.current_state_name == "done"

        fsm.restore(snap)
        assert fsm.current_state_name == "running"

        # machine is functional after restore
        assert fsm.trigger("finish").success
        assert fsm.current_state_name == "done"


class TestClone:
    """Tests for clone()."""

    def _make_fsm(self):
        idle = State("idle")
        running = State("running")
        done = State("done")
        fsm = StateMachine(idle, name="template")
        fsm.add_state(running)
        fsm.add_state(done)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("finish", "running", "done")
        fsm.add_transition("reset_t", "done", "idle")
        return fsm

    # ------------------------------------------------------------------
    # Topology fidelity
    # ------------------------------------------------------------------

    def test_clone_starts_at_initial_state(self):
        fsm = self._make_fsm()
        fsm.trigger("start")
        clone = fsm.clone()
        assert clone.current_state_name == "idle"

    def test_clone_has_same_states(self):
        fsm = self._make_fsm()
        clone = fsm.clone()
        assert set(clone.states) == set(fsm.states)

    def test_clone_has_same_transitions(self):
        fsm = self._make_fsm()
        clone = fsm.clone()
        assert clone.trigger("start").success
        assert clone.trigger("finish").success
        assert clone.trigger("reset_t").success
        assert clone.current_state_name == "idle"

    def test_clone_preserves_guard_conditions(self):
        from fast_fsm import Condition

        allow = True

        class Toggle(Condition):
            def __init__(self):
                super().__init__("toggle", "toggleable guard")

            def check(self, **kwargs):
                return allow

        idle = State("idle")
        active = State("active")
        fsm = StateMachine(idle, name="guarded")
        fsm.add_state(active)
        fsm.add_transition("go", "idle", "active", condition=Toggle())

        clone = fsm.clone()

        # Guard passes
        assert clone.trigger("go").success

        # Disable guard — both FSMs share the same Condition object
        allow = False
        clone2 = fsm.clone()
        result = clone2.trigger("go")
        assert not result.success

    # ------------------------------------------------------------------
    # Independence
    # ------------------------------------------------------------------

    def test_clone_state_is_independent(self):
        """Advancing original does not affect clone and vice versa."""
        fsm = self._make_fsm()
        clone = fsm.clone()

        fsm.trigger("start")
        assert clone.current_state_name == "idle"

        clone.trigger("start")
        clone.trigger("finish")
        assert fsm.current_state_name == "running"

    def test_clone_adding_transition_does_not_affect_original(self):
        """Adding a transition to the clone doesn't appear in the original."""
        fsm = self._make_fsm()
        clone = fsm.clone()

        extra = State("extra")
        clone.add_state(extra)
        clone.add_transition("side", "idle", "extra")

        assert "extra" not in fsm.states
        assert not fsm.transition_exists("side", "idle", "extra")

    def test_clone_listeners_are_empty(self):
        """Listeners attached to the original are NOT copied to the clone."""
        fsm = self._make_fsm()
        events = []

        class L:
            def after_transition(self, old, new, t, **kw):
                events.append("original")

        fsm.add_listener(L())

        clone = fsm.clone()
        clone.trigger("start")  # should not fire original's listener
        assert events == []

    # ------------------------------------------------------------------
    # Multiple clones
    # ------------------------------------------------------------------

    def test_multiple_clones_are_independent(self):
        fsm = self._make_fsm()
        c1 = fsm.clone()
        c2 = fsm.clone()

        c1.trigger("start")
        assert c2.current_state_name == "idle"
        assert fsm.current_state_name == "idle"

    def test_clone_name_preserved(self):
        fsm = self._make_fsm()
        clone = fsm.clone()
        assert clone.name == fsm.name


class TestMachineCallbacks:
    """Tests for on_enter() and on_exit() per-state callback registration."""

    def _make_fsm(self):
        idle = State("idle")
        running = State("running")
        done = State("done")
        fsm = StateMachine(idle, name="cb_fsm")
        fsm.add_state(running)
        fsm.add_state(done)
        fsm.add_transition("start", "idle", "running")
        fsm.add_transition("finish", "running", "done")
        fsm.add_transition("reset_t", "done", "idle")
        return fsm

    # ------------------------------------------------------------------
    # on_enter() — basic firing
    # ------------------------------------------------------------------

    def test_on_enter_fires_when_entering_state(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_enter("running", lambda from_s, t, **kw: calls.append((from_s.name, t)))

        fsm.trigger("start")
        assert calls == [("idle", "start")]

    def test_on_enter_receives_correct_args(self):
        fsm = self._make_fsm()
        args_seen = []
        fsm.on_enter(
            "running", lambda from_s, t, **kw: args_seen.append((from_s.name, t, kw))
        )

        fsm.trigger("start", extra="hello")
        assert args_seen == [("idle", "start", {"extra": "hello"})]

    def test_on_enter_does_not_fire_for_other_states(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_enter("done", lambda from_s, t, **kw: calls.append(t))

        fsm.trigger("start")  # enters running — should NOT fire
        assert calls == []

        fsm.trigger("finish")  # enters done — should fire
        assert calls == ["finish"]

    def test_on_enter_multiple_callbacks_same_state(self):
        fsm = self._make_fsm()
        order = []
        fsm.on_enter("running", lambda *a, **kw: order.append(1))
        fsm.on_enter("running", lambda *a, **kw: order.append(2))
        fsm.on_enter("running", lambda *a, **kw: order.append(3))

        fsm.trigger("start")
        assert order == [1, 2, 3]

    def test_on_enter_multiple_callbacks_different_states(self):
        fsm = self._make_fsm()
        log = []
        fsm.on_enter("running", lambda *a, **kw: log.append("running"))
        fsm.on_enter("done", lambda *a, **kw: log.append("done"))

        fsm.trigger("start")
        fsm.trigger("finish")
        assert log == ["running", "done"]

    def test_on_enter_fires_on_force_state(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_enter("done", lambda from_s, t, **kw: calls.append(t))

        fsm.force_state("done")
        assert calls == ["__force__"]

    # ------------------------------------------------------------------
    # on_exit() — basic firing
    # ------------------------------------------------------------------

    def test_on_exit_fires_when_leaving_state(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_exit("idle", lambda to_s, t, **kw: calls.append((to_s.name, t)))

        fsm.trigger("start")
        assert calls == [("running", "start")]

    def test_on_exit_receives_correct_args(self):
        fsm = self._make_fsm()
        args_seen = []
        fsm.on_exit("idle", lambda to_s, t, **kw: args_seen.append((to_s.name, t, kw)))

        fsm.trigger("start", tag="x")
        assert args_seen == [("running", "start", {"tag": "x"})]

    def test_on_exit_does_not_fire_for_other_states(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_exit("running", lambda *a, **kw: calls.append("running"))

        fsm.trigger("start")  # exits idle — should NOT fire
        assert calls == []

        fsm.trigger("finish")  # exits running — should fire
        assert calls == ["running"]

    def test_on_exit_fires_on_force_state(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_exit("idle", lambda to_s, t, **kw: calls.append(t))

        fsm.force_state("running")
        assert calls == ["__force__"]

    # ------------------------------------------------------------------
    # Callback ordering relative to other hooks
    # ------------------------------------------------------------------

    def test_callback_order_relative_to_state_method_and_listener(self):
        """Order within a full transition:
        1. State.on_exit
        2. machine on_exit callback   ← new
        3. on_exit_state listener
        4. [state change]
        5. State.on_enter
        6. machine on_enter callback  ← new
        7. on_enter_state listener
        8. after_transition listener
        """
        from fast_fsm import CallbackState

        order = []
        idle = CallbackState(
            "idle",
            on_exit=lambda to, t, **kw: order.append("state.on_exit"),
        )
        running = CallbackState(
            "running",
            on_enter=lambda frm, t, **kw: order.append("state.on_enter"),
        )
        fsm = StateMachine(idle, name="order_test")
        fsm.add_state(running)
        fsm.add_transition("start", "idle", "running")

        fsm.on_exit("idle", lambda *a, **kw: order.append("machine.on_exit"))
        fsm.on_enter("running", lambda *a, **kw: order.append("machine.on_enter"))

        class L:
            def on_exit_state(self, *a, **kw):
                order.append("listener.on_exit")

            def on_enter_state(self, *a, **kw):
                order.append("listener.on_enter")

            def after_transition(self, *a, **kw):
                order.append("listener.after")

        fsm.add_listener(L())
        fsm.trigger("start")

        assert order == [
            "state.on_exit",
            "machine.on_exit",
            "listener.on_exit",
            "state.on_enter",
            "machine.on_enter",
            "listener.on_enter",
            "listener.after",
        ]

    # ------------------------------------------------------------------
    # Exception safety
    # ------------------------------------------------------------------

    def test_on_enter_exception_does_not_abort_transition(self):
        """A raising on_enter callback must not stop the transition."""
        fsm = self._make_fsm()

        def boom(*a, **kw):
            raise RuntimeError("on_enter boom")

        fsm.on_enter("running", boom)

        result = fsm.trigger("start")
        assert result.success
        assert fsm.current_state_name == "running"

    def test_on_exit_exception_does_not_abort_transition(self):
        """A raising on_exit callback must not stop the transition."""
        fsm = self._make_fsm()

        def boom(*a, **kw):
            raise RuntimeError("on_exit boom")

        fsm.on_exit("idle", boom)

        result = fsm.trigger("start")
        assert result.success
        assert fsm.current_state_name == "running"

    # ------------------------------------------------------------------
    # clone() copies callbacks
    # ------------------------------------------------------------------

    def test_clone_copies_on_enter_callbacks(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_enter("running", lambda *a, **kw: calls.append("enter"))

        clone = fsm.clone()
        clone.trigger("start")
        assert calls == ["enter"]

    def test_clone_copies_on_exit_callbacks(self):
        fsm = self._make_fsm()
        calls = []
        fsm.on_exit("idle", lambda *a, **kw: calls.append("exit"))

        clone = fsm.clone()
        clone.trigger("start")
        assert calls == ["exit"]

    def test_clone_callback_independence(self):
        """Adding a callback to origin after clone does not affect clone."""
        fsm = self._make_fsm()
        fsm.on_enter("running", lambda *a, **kw: None)  # pre-existing

        clone = fsm.clone()

        extra_calls = []
        fsm.on_enter("running", lambda *a, **kw: extra_calls.append(1))

        clone.trigger("start")
        assert extra_calls == []  # extra callback not on clone


class TestFromDict:
    """Tests for StateMachine.from_dict()."""

    # ------------------------------------------------------------------
    # Basic construction
    # ------------------------------------------------------------------

    def test_basic_construction(self):
        config = {
            "initial": "idle",
            "transitions": [
                {"trigger": "start", "from": "idle", "to": "running"},
                {"trigger": "finish", "from": "running", "to": "done"},
            ],
        }
        fsm = StateMachine.from_dict(config)
        assert fsm.current_state_name == "idle"
        assert set(fsm.states) == {"idle", "running", "done"}

    def test_transitions_work(self):
        config = {
            "initial": "idle",
            "transitions": [
                {"trigger": "start", "from": "idle", "to": "running"},
                {"trigger": "finish", "from": "running", "to": "done"},
            ],
        }
        fsm = StateMachine.from_dict(config)
        assert fsm.trigger("start").success
        assert fsm.current_state_name == "running"
        assert fsm.trigger("finish").success
        assert fsm.current_state_name == "done"

    # ------------------------------------------------------------------
    # Name resolution
    # ------------------------------------------------------------------

    def test_default_name(self):
        fsm = StateMachine.from_dict({"initial": "a", "transitions": []})
        assert fsm.name == "FSM"

    def test_name_from_config(self):
        config = {"name": "TrafficLight", "initial": "red", "transitions": []}
        fsm = StateMachine.from_dict(config)
        assert fsm.name == "TrafficLight"

    def test_name_kwarg_overrides_config(self):
        config = {"name": "TrafficLight", "initial": "red", "transitions": []}
        fsm = StateMachine.from_dict(config, name="Override")
        assert fsm.name == "Override"

    # ------------------------------------------------------------------
    # Fan-out ("from" as list)
    # ------------------------------------------------------------------

    def test_fanout_from_as_list(self):
        config = {
            "initial": "idle",
            "transitions": [
                {"trigger": "start", "from": "idle", "to": "running"},
                {"trigger": "error", "from": ["idle", "running"], "to": "failed"},
            ],
        }
        fsm = StateMachine.from_dict(config)
        # error trigger should work from both states
        fsm2 = StateMachine.from_dict(config)
        fsm2.trigger("start")
        assert fsm2.trigger("error").success
        assert fsm2.current_state_name == "failed"

        assert fsm.trigger("error").success
        assert fsm.current_state_name == "failed"

    # ------------------------------------------------------------------
    # Explicit states list
    # ------------------------------------------------------------------

    def test_explicit_states_includes_isolated_state(self):
        """States listed in 'states' but not in transitions are still registered."""
        config = {
            "initial": "idle",
            "states": ["idle", "running", "terminal"],
            "transitions": [
                {"trigger": "start", "from": "idle", "to": "running"},
            ],
        }
        fsm = StateMachine.from_dict(config)
        assert "terminal" in fsm.states

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_missing_initial_raises(self):
        import pytest

        with pytest.raises(ValueError, match="initial"):
            StateMachine.from_dict({"transitions": []})

    def test_transition_missing_trigger_raises(self):
        import pytest

        config = {
            "initial": "a",
            "transitions": [{"from": "a", "to": "b"}],
        }
        with pytest.raises(ValueError, match="trigger"):
            StateMachine.from_dict(config)

    def test_transition_missing_from_raises(self):
        import pytest

        config = {
            "initial": "a",
            "transitions": [{"trigger": "go", "to": "b"}],
        }
        with pytest.raises(ValueError, match="from"):
            StateMachine.from_dict(config)

    def test_transition_missing_to_raises(self):
        import pytest

        config = {
            "initial": "a",
            "transitions": [{"trigger": "go", "from": "a"}],
        }
        with pytest.raises(ValueError, match="to"):
            StateMachine.from_dict(config)

    # ------------------------------------------------------------------
    # Round-trip: JSON -> FSM -> snapshot -> dict comparison
    # ------------------------------------------------------------------

    def test_json_roundtrip(self):
        import json

        config = {
            "name": "Lifecycle",
            "initial": "pending",
            "transitions": [
                {"trigger": "activate", "from": "pending", "to": "active"},
                {"trigger": "deactivate", "from": "active", "to": "inactive"},
                {"trigger": "reactivate", "from": "inactive", "to": "active"},
            ],
        }
        json_str = json.dumps(config)
        fsm = StateMachine.from_dict(json.loads(json_str))
        fsm.trigger("activate")
        assert fsm.snapshot()["state"] == "active"
