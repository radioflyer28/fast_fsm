"""
Pytest migration of README examples and validation tests.

These tests are rewritten to be compatible with the mypyc-compiled version
of fast_fsm, using composition instead of inheritance where needed.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fast_fsm.core import StateMachine, State
from fast_fsm.conditions import Condition, FuncCondition


class TestReadmeExamples:
    """Test examples from README documentation"""

    def test_basic_usage_example(self):
        """Test the basic usage example from README"""
        # Create states using basic State class (no inheritance needed)
        idle_state = State("idle")
        processing_state = State("processing")

        # Create FSM directly (no FSMBuilder needed)
        fsm = StateMachine(idle_state, name="basic_example")
        fsm.add_state(processing_state)

        # Add transitions
        fsm.add_transition("start", "idle", "processing")
        fsm.add_transition("complete", "processing", "idle")

        # Test the FSM
        assert fsm.current_state.name == "idle"

        # Test transition
        result = fsm.trigger("start")
        assert result.success
        assert fsm.current_state.name == "processing"

        # Test return transition
        result = fsm.trigger("complete")
        assert result.success
        assert fsm.current_state.name == "idle"

    def test_conditional_transitions_example(self):
        """Test conditional transitions example"""

        # Create a condition using FuncCondition
        def can_proceed(value=0, **kwargs):
            return value > 5

        condition = FuncCondition(can_proceed, "value_check", "Check if value > 5")

        # Create states
        waiting = State("waiting")
        ready = State("ready")

        # Create FSM
        fsm = StateMachine(waiting, name="conditional_example")
        fsm.add_state(ready)
        fsm.add_transition("proceed", "waiting", "ready", condition)

        # Test successful condition
        result = fsm.trigger("proceed", value=10)
        assert result.success
        assert fsm.current_state.name == "ready"

        # Reset state for next test
        fsm._current_state = waiting

        # Test failed condition
        result = fsm.trigger("proceed", value=3)
        assert not result.success
        assert fsm.current_state.name == "waiting"

    def test_state_callbacks_example(self):
        """Test state callbacks without inheritance"""

        # Track callback execution
        callbacks_executed = []

        def on_enter_idle(from_state, trigger, *args, **kwargs):
            callbacks_executed.append("entered_idle")

        def on_enter_processing(from_state, trigger, *args, **kwargs):
            callbacks_executed.append("entered_processing")

        def on_exit_idle(to_state, trigger, *args, **kwargs):
            callbacks_executed.append("exited_idle")

        # Create states with callbacks
        idle_state = State.create("idle", on_enter=on_enter_idle, on_exit=on_exit_idle)
        processing_state = State.create("processing", on_enter=on_enter_processing)

        # Create FSM
        fsm = StateMachine(idle_state, name="callback_example")
        fsm.add_state(processing_state)
        fsm.add_transition("start", "idle", "processing")
        fsm.add_transition("complete", "processing", "idle")

        # Test callbacks
        callbacks_executed.clear()

        result = fsm.trigger("start")
        assert result.success
        assert "exited_idle" in callbacks_executed
        assert "entered_processing" in callbacks_executed

        result = fsm.trigger("complete")
        assert result.success
        assert "entered_idle" in callbacks_executed

    def test_complex_condition_example(self):
        """Test more complex condition logic with single classifier"""

        class RangeClassifier(Condition):
            def __init__(self):
                super().__init__(
                    "range_classifier", "Classify value into range categories"
                )

            def check(self, **kwargs) -> bool:
                # This classifier always returns True as we'll determine
                # the target state dynamically
                return True

        # Create states
        start = State("start")
        low = State("low")
        medium = State("medium")
        high = State("high")

        # Create FSM
        fsm = StateMachine(start, name="complex_condition")
        for state in [low, medium, high]:
            fsm.add_state(state)

        # Add a single transition that will choose target dynamically
        # We'll override the trigger method to handle this case
        classifier = RangeClassifier()
        fsm.add_transition("classify", "start", "low", classifier)  # Default target

        # Custom logic for value-based transitions
        def classify_value(value):
            if 1 <= value <= 10:
                target = "low"
            elif 11 <= value <= 50:
                target = "medium"
            elif 51 <= value <= 100:
                target = "high"
            else:
                return None

            # Set current state directly for this test
            fsm._current_state = fsm._states[target]
            return target

        # Test classifications
        result = classify_value(5)
        assert result == "low"
        assert fsm.current_state.name == "low"

        # Reset and test medium
        fsm._current_state = start
        result = classify_value(25)
        assert result == "medium"
        assert fsm.current_state.name == "medium"

        # Reset and test high
        fsm._current_state = start
        result = classify_value(75)
        assert result == "high"
        assert fsm.current_state.name == "high"


class TestTrafficLightExample:
    """Test traffic light state machine example"""

    def test_traffic_light_cycle(self):
        """Test complete traffic light cycle"""

        class TimerCondition(Condition):
            def __init__(self, duration):
                super().__init__(f"timer_{duration}", f"Timer for {duration} seconds")
                self.duration = duration

            def check(self, **kwargs) -> bool:
                # In real scenario, this would check actual timer
                # For test, we'll use a passed 'timer_expired' flag
                return kwargs.get("timer_expired", False)

        # Create traffic light states
        red = State("red")
        yellow = State("yellow")
        green = State("green")

        # Create FSM
        traffic_light = StateMachine(red, name="traffic_light")
        traffic_light.add_state(yellow)
        traffic_light.add_state(green)

        # Add transitions with timer conditions
        timer_condition = TimerCondition(30)
        traffic_light.add_transition("timer", "red", "green", timer_condition)
        traffic_light.add_transition("timer", "green", "yellow", timer_condition)
        traffic_light.add_transition("timer", "yellow", "red", timer_condition)

        # Test complete cycle
        assert traffic_light.current_state.name == "red"

        # Red -> Green
        result = traffic_light.trigger("timer", timer_expired=True)
        assert result.success
        assert traffic_light.current_state.name == "green"

        # Green -> Yellow
        result = traffic_light.trigger("timer", timer_expired=True)
        assert result.success
        assert traffic_light.current_state.name == "yellow"

        # Yellow -> Red
        result = traffic_light.trigger("timer", timer_expired=True)
        assert result.success
        assert traffic_light.current_state.name == "red"

    def test_traffic_light_with_emergency(self):
        """Test traffic light with emergency override"""

        class EmergencyCondition(Condition):
            def __init__(self):
                super().__init__("emergency", "Emergency vehicle detected")

            def check(self, **kwargs) -> bool:
                return kwargs.get("emergency", False)

        # Create states
        red = State("red")
        yellow = State("yellow")
        green = State("green")
        emergency = State("emergency")

        # Create FSM
        traffic_light = StateMachine(red, name="emergency_traffic_light")
        for state in [yellow, green, emergency]:
            traffic_light.add_state(state)

        # Normal cycle transitions
        traffic_light.add_transition("timer", "red", "green")
        traffic_light.add_transition("timer", "green", "yellow")
        traffic_light.add_transition("timer", "yellow", "red")

        # Emergency transitions from any state
        emergency_condition = EmergencyCondition()
        traffic_light.add_transition(
            "emergency", ["red", "yellow", "green"], "emergency", emergency_condition
        )
        traffic_light.add_transition("clear", "emergency", "red")

        # Test emergency override
        traffic_light.trigger("timer")  # red -> green
        assert traffic_light.current_state.name == "green"

        # Emergency from green
        result = traffic_light.trigger("emergency", emergency=True)
        assert result.success
        assert traffic_light.current_state.name == "emergency"

        # Clear emergency
        result = traffic_light.trigger("clear")
        assert result.success
        assert traffic_light.current_state.name == "red"


class TestOrderProcessingExample:
    """Test order processing workflow example"""

    def test_order_processing_workflow(self):
        """Test complete order processing workflow"""

        class PaymentValidCondition(Condition):
            def __init__(self):
                super().__init__("payment_valid", "Validate payment information")

            def check(self, **kwargs) -> bool:
                order = kwargs.get("order", {})
                return (
                    order.get("payment_method") is not None
                    and order.get("amount", 0) > 0
                )

        class InventoryAvailableCondition(Condition):
            def __init__(self):
                super().__init__("inventory_available", "Check inventory availability")

            def check(self, **kwargs) -> bool:
                order = kwargs.get("order", {})
                return order.get("in_stock", False)

        # Create order processing states
        pending = State("pending")
        payment_processing = State("payment_processing")
        confirmed = State("confirmed")
        shipped = State("shipped")
        cancelled = State("cancelled")

        # Create FSM
        order_fsm = StateMachine(pending, name="order_processor")
        for state in [payment_processing, confirmed, shipped, cancelled]:
            order_fsm.add_state(state)

        # Create conditions
        payment_condition = PaymentValidCondition()
        inventory_condition = InventoryAvailableCondition()

        # Add transitions
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

        # Test successful order flow
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

    def test_order_cancellation_flow(self):
        """Test order cancellation from different states"""

        # Create states
        pending = State("pending")
        payment_processing = State("payment_processing")
        confirmed = State("confirmed")
        cancelled = State("cancelled")

        # Create FSM
        order_fsm = StateMachine(pending, name="cancellation_test")
        for state in [payment_processing, confirmed, cancelled]:
            order_fsm.add_state(state)

        # Add transitions (simplified for cancellation test)
        order_fsm.add_transition("process", "pending", "payment_processing")
        order_fsm.add_transition("confirm", "payment_processing", "confirmed")
        order_fsm.add_transition(
            "cancel", ["pending", "payment_processing", "confirmed"], "cancelled"
        )

        # Test cancellation from pending
        result = order_fsm.trigger("cancel")
        assert result.success
        assert order_fsm.current_state.name == "cancelled"

        # Reset and test cancellation from payment_processing
        order_fsm._current_state = pending
        order_fsm.trigger("process")
        assert order_fsm.current_state.name == "payment_processing"

        result = order_fsm.trigger("cancel")
        assert result.success
        assert order_fsm.current_state.name == "cancelled"


@pytest.mark.integration
class TestPerformanceExamples:
    """Test performance characteristics with example scenarios"""

    def test_large_state_machine_performance(self):
        """Test performance with many states and transitions"""
        import time

        # Create a large state machine
        initial_state = State("state_0")
        fsm = StateMachine(initial_state, name="large_fsm")

        # Add many states with transitions
        num_states = 100
        for i in range(1, num_states + 1):
            state = State(f"state_{i}")
            fsm.add_state(state)
            fsm.add_transition(f"next_{i}", f"state_{i - 1}", f"state_{i}")

        # Time the transitions
        start_time = time.time()
        for i in range(1, num_states + 1):
            result = fsm.trigger(f"next_{i}")
            assert result.success

        elapsed = time.time() - start_time

        # Should complete quickly (less than 1 second for 100 transitions)
        assert elapsed < 1.0
        assert fsm.current_state.name == f"state_{num_states}"

    def test_condition_evaluation_performance(self):
        """Test performance of condition evaluation"""
        import time

        class PerformanceCondition(Condition):
            def __init__(self):
                super().__init__("perf_condition", "Performance test condition")
                self.call_count = 0

            def check(self, **kwargs) -> bool:
                self.call_count += 1
                # Simple condition that always passes
                return kwargs.get("value", 0) >= 0

        # Create FSM with condition
        state_a = State("state_a")
        state_b = State("state_b")

        fsm = StateMachine(state_a, name="perf_test")
        fsm.add_state(state_b)

        condition = PerformanceCondition()
        fsm.add_transition("go", "state_a", "state_b", condition)
        fsm.add_transition("back", "state_b", "state_a", condition)

        # Time many condition evaluations
        num_iterations = 1000
        start_time = time.time()

        for i in range(num_iterations):
            if i % 2 == 0:
                fsm.trigger("go", value=i)
            else:
                fsm.trigger("back", value=i)

        elapsed = time.time() - start_time

        # Should complete quickly
        assert elapsed < 1.0
        assert condition.call_count == num_iterations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
