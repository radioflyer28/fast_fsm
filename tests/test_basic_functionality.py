"""
Pytest-based tests for fast_fsm examples and basic functionality.

This module contains tests that verify the examples from the README
and other basic functionality work correctly.
"""

import pytest

from fast_fsm.core import StateMachine, State
from fast_fsm.conditions import Condition


class TestBasicFunctionality:
    """Test basic FSM functionality"""

    def test_state_creation(self):
        """Test creating basic states"""
        state = State("test_state")
        assert state.name == "test_state"

    def test_state_machine_creation(self):
        """Test creating a state machine"""
        initial_state = State("initial")
        fsm = StateMachine(initial_state, name="test_fsm")

        assert fsm.current_state == initial_state
        assert fsm.current_state.name == "initial"

    def test_add_state(self):
        """Test adding states to FSM"""
        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)

        # Should have both states
        assert "initial" in fsm.states
        assert "target" in fsm.states

    def test_simple_transition(self):
        """Test a simple transition without conditions"""
        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)
        fsm.add_transition("go", "initial", "target")

        # Should start in initial state
        assert fsm.current_state.name == "initial"

        # Trigger transition
        result = fsm.trigger("go")

        # Should succeed and be in target state
        assert result.success
        assert fsm.current_state.name == "target"

    def test_transition_with_args(self):
        """Test transitions with arguments"""
        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)
        fsm.add_transition("go", "initial", "target")

        # Trigger with arguments
        result = fsm.trigger("go", arg1="value1", arg2=42)

        assert result.success
        assert fsm.current_state.name == "target"


class TestConditionalTransitions:
    """Test transitions with conditions"""

    def test_condition_success(self):
        """Test transition with successful condition"""

        class AlwaysTrueCondition(Condition):
            def __init__(self):
                super().__init__("always_true", "Always returns true")

            def check(self, **kwargs):
                return True

        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)
        fsm.add_transition("go", "initial", "target", AlwaysTrueCondition())

        result = fsm.trigger("go")

        assert result.success
        assert fsm.current_state.name == "target"

    def test_condition_failure(self):
        """Test transition with failing condition"""

        class AlwaysFalseCondition(Condition):
            def __init__(self):
                super().__init__("always_false", "Always returns false")

            def check(self, **kwargs):
                return False

        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)
        fsm.add_transition("go", "initial", "target", AlwaysFalseCondition())

        result = fsm.trigger("go")

        assert not result.success
        assert fsm.current_state.name == "initial"  # Should stay in initial
        assert result.error and "failed" in result.error.lower()

    def test_condition_with_context(self):
        """Test condition that uses context data"""

        class ValueCheckCondition(Condition):
            def __init__(self, expected_value):
                super().__init__(
                    "value_check", f"Checks if value equals {expected_value}"
                )
                self.expected_value = expected_value

            def check(self, **kwargs):
                return kwargs.get("value") == self.expected_value

        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)
        fsm.add_transition("go", "initial", "target", ValueCheckCondition(42))

        # Should fail with wrong value
        result = fsm.trigger("go", value=99)
        assert not result.success
        assert fsm.current_state.name == "initial"

        # Should succeed with correct value
        result = fsm.trigger("go", value=42)
        assert result.success
        assert fsm.current_state.name == "target"


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_trigger(self):
        """Test triggering non-existent transition"""
        initial_state = State("initial")
        fsm = StateMachine(initial_state, name="test_fsm")

        result = fsm.trigger("nonexistent")

        assert not result.success
        assert result.error and "No transition" in result.error
        assert fsm.current_state.name == "initial"

    def test_invalid_source_state(self):
        """Test trigger from wrong state"""
        state1 = State("state1")
        state2 = State("state2")
        state3 = State("state3")

        fsm = StateMachine(state1, name="test_fsm")
        fsm.add_state(state2)
        fsm.add_state(state3)

        # Add transition from state2 to state3
        fsm.add_transition("go", "state2", "state3")

        # Try to trigger from state1 (should fail)
        result = fsm.trigger("go")

        assert not result.success
        assert fsm.current_state.name == "state1"

    def test_can_trigger_method(self):
        """Test the can_trigger method"""
        initial_state = State("initial")
        target_state = State("target")

        fsm = StateMachine(initial_state, name="test_fsm")
        fsm.add_state(target_state)
        fsm.add_transition("go", "initial", "target")

        # Should be able to trigger from initial state
        assert fsm.can_trigger("go")

        # Move to target state
        fsm.trigger("go")

        # Should not be able to trigger from target state
        assert not fsm.can_trigger("go")


class TestComplexScenarios:
    """Test more complex FSM scenarios"""

    def test_traffic_light_example(self):
        """Test a traffic light state machine"""

        class TimerCondition(Condition):
            def __init__(self, duration):
                super().__init__(f"timer_{duration}", f"Timer for {duration} seconds")
                self.duration = duration

            def check(self, **kwargs):
                # In real scenario, this would check actual timer
                # For test, we'll use a passed 'timer_expired' flag
                return kwargs.get("timer_expired", False)

        # Create states
        red = State("red")
        yellow = State("yellow")
        green = State("green")

        # Create FSM
        traffic_light = StateMachine(red, name="traffic_light")
        traffic_light.add_state(yellow)
        traffic_light.add_state(green)

        # Add transitions
        timer_condition = TimerCondition(30)
        traffic_light.add_transition("timer", "red", "green", timer_condition)
        traffic_light.add_transition("timer", "green", "yellow", timer_condition)
        traffic_light.add_transition("timer", "yellow", "red", timer_condition)

        # Test cycle
        assert traffic_light.current_state.name == "red"

        # Timer expires -> should go to green
        result = traffic_light.trigger("timer", timer_expired=True)
        assert result.success
        assert traffic_light.current_state.name == "green"

        # Timer expires -> should go to yellow
        result = traffic_light.trigger("timer", timer_expired=True)
        assert result.success
        assert traffic_light.current_state.name == "yellow"

        # Timer expires -> should go back to red
        result = traffic_light.trigger("timer", timer_expired=True)
        assert result.success
        assert traffic_light.current_state.name == "red"

    def test_order_processing_example(self):
        """Test an order processing state machine"""

        class PaymentCondition(Condition):
            def __init__(self):
                super().__init__("payment_valid", "Check if payment is valid")

            def check(self, **kwargs) -> bool:
                order = kwargs.get("order")
                return bool(
                    order and order.get("payment_method") and order.get("amount", 0) > 0
                )

        class InventoryCondition(Condition):
            def __init__(self):
                super().__init__("inventory_available", "Check if items are in stock")

            def check(self, **kwargs) -> bool:
                order = kwargs.get("order")
                return bool(order and order.get("in_stock", False))

        # Create states
        pending = State("pending")
        payment_processing = State("payment_processing")
        confirmed = State("confirmed")
        shipped = State("shipped")
        cancelled = State("cancelled")

        # Create FSM
        order_fsm = StateMachine(pending, name="order_processor")
        for state in [payment_processing, confirmed, shipped, cancelled]:
            order_fsm.add_state(state)

        # Add transitions
        payment_condition = PaymentCondition()
        inventory_condition = InventoryCondition()

        order_fsm.add_transition(
            "process_payment", "pending", "payment_processing", payment_condition
        )
        order_fsm.add_transition(
            "confirm", "payment_processing", "confirmed", inventory_condition
        )
        order_fsm.add_transition("ship", "confirmed", "shipped")
        order_fsm.add_transition(
            "cancel", ["pending", "payment_processing", "confirmed"], "cancelled"
        )

        # Test valid order flow
        valid_order = {
            "payment_method": "credit_card",
            "amount": 99.99,
            "in_stock": True,
        }

        assert order_fsm.current_state.name == "pending"

        # Process payment
        result = order_fsm.trigger("process_payment", order=valid_order)
        assert result.success
        assert order_fsm.current_state.name == "payment_processing"

        # Confirm order
        result = order_fsm.trigger("confirm", order=valid_order)
        assert result.success
        assert order_fsm.current_state.name == "confirmed"

        # Ship order
        result = order_fsm.trigger("ship", order=valid_order)
        assert result.success
        assert order_fsm.current_state.name == "shipped"

    def test_multiple_target_states(self):
        """Test transitions with multiple possible target states"""
        state1 = State("state1")
        state2 = State("state2")
        state3 = State("state3")

        fsm = StateMachine(state1, name="test_fsm")
        fsm.add_state(state2)
        fsm.add_state(state3)

        # Add transitions with different target states
        fsm.add_transition("go_to_2", "state1", "state2")
        fsm.add_transition("go_to_3", "state1", "state3")

        # Test first transition
        result = fsm.trigger("go_to_2")
        assert result.success
        assert fsm.current_state.name == "state2"

        # Reset and test second transition
        fsm._current_state = state1
        result = fsm.trigger("go_to_3")
        assert result.success
        assert fsm.current_state.name == "state3"


@pytest.mark.integration
class TestPerformance:
    """Integration tests for performance characteristics"""

    def test_many_states_performance(self):
        """Test FSM with many states"""
        import time

        # Create FSM with many states
        initial = State("state_0")
        fsm = StateMachine(initial, name="large_fsm")

        # Add 100 states
        for i in range(1, 101):
            state = State(f"state_{i}")
            fsm.add_state(state)
            fsm.add_transition(f"go_{i}", f"state_{i - 1}", f"state_{i}")

        # Time transitions
        start = time.time()
        for i in range(1, 101):
            result = fsm.trigger(f"go_{i}")
            assert result.success

        elapsed = time.time() - start

        # Should complete 100 transitions quickly
        assert elapsed < 1.0
        assert fsm.current_state.name == "state_100"

    def test_repeated_transitions_performance(self):
        """Test performance of repeated transitions"""
        import time

        state1 = State("state1")
        state2 = State("state2")

        fsm = StateMachine(state1, name="perf_fsm")
        fsm.add_state(state2)
        fsm.add_transition("go", "state1", "state2")
        fsm.add_transition("back", "state2", "state1")

        # Time many transitions
        start = time.time()
        for i in range(1000):
            if i % 2 == 0:
                fsm.trigger("go")
            else:
                fsm.trigger("back")

        elapsed = time.time() - start

        # Should complete 1000 transitions quickly
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
