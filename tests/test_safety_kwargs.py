"""
Unit tests for safety improvements in kwargs handling.

Tests the safety mechanisms added to protect against potentially
problematic context data passed through **kwargs in trigger() calls.
"""

import pytest
import logging
from unittest.mock import Mock
from fast_fsm.core import StateMachine, State
from fast_fsm.conditions import Condition


class MockCondition(Condition):
    """Test condition that records the kwargs it receives"""

    def __init__(self, return_value=True):
        super().__init__("mock_condition", "Test condition")
        self.return_value = return_value
        self.received_kwargs = {}

    def check(self, **kwargs):
        self.received_kwargs = kwargs.copy()
        return self.return_value


class ExceptionCondition(Condition):
    """Test condition that raises an exception"""

    def __init__(self, exception=None):
        super().__init__("exception_condition", "Condition that raises exception")
        self.exception = exception or ValueError("test exception")

    def check(self, **kwargs):
        raise self.exception


@pytest.fixture
def basic_fsm():
    """Create a basic FSM for testing"""
    initial_state = State("initial")
    target_state = State("target")

    fsm = StateMachine(initial_state, name="test_fsm")
    fsm.add_state(target_state)

    return fsm, initial_state, target_state


class TestKwargsSanitization:
    """Test kwargs sanitization functionality"""

    def test_normal_kwargs_pass_through(self, basic_fsm):
        """Test that normal kwargs pass through unchanged"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        # Trigger with normal kwargs
        result = fsm.trigger(
            "test_trigger",
            normal_arg="value1",
            another_arg=42,
            object_arg={"key": "value"},
        )

        assert result.success
        assert condition.received_kwargs == {
            "normal_arg": "value1",
            "another_arg": 42,
            "object_arg": {"key": "value"},
        }

    def test_private_attributes_filtered(self, basic_fsm):
        """Test that private attributes are filtered out"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        # Trigger with private attributes
        result = fsm.trigger(
            "test_trigger",
            normal_arg="visible",
            _private_arg="filtered",
            __dunder_arg="filtered",
            another_normal="visible",
        )

        assert result.success
        assert condition.received_kwargs == {
            "normal_arg": "visible",
            "another_normal": "visible",
        }
        # Private args should not be present
        assert "_private_arg" not in condition.received_kwargs
        assert "__dunder_arg" not in condition.received_kwargs

    def test_excessive_kwargs_truncated(self, basic_fsm, caplog):
        """Test that excessive kwargs are truncated"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        # Create 60 kwargs (over the 50 limit)
        large_kwargs = {f"arg_{i}": f"value_{i}" for i in range(60)}

        with caplog.at_level(logging.WARNING):
            fsm.trigger("test_trigger", **large_kwargs)

        # Should log a warning about truncation
        assert "Too many kwargs (60) passed to condition, truncating" in caplog.text

        # Should receive only 50 kwargs
        assert len(condition.received_kwargs) == 50

    def test_invalid_key_length_filtered(self, basic_fsm, caplog):
        """Test that overly long keys are filtered"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        # Create key longer than 100 characters
        long_key = "a" * 150
        kwargs = {long_key: "should_be_filtered", "normal_key": "should_pass"}

        with caplog.at_level(logging.WARNING):
            result = fsm.trigger("test_trigger", **kwargs)

        assert result.success
        assert "Skipping invalid kwarg key" in caplog.text
        assert condition.received_kwargs == {"normal_key": "should_pass"}
        assert long_key not in condition.received_kwargs

    def test_empty_kwargs_handled(self, basic_fsm):
        """Test that empty kwargs are handled correctly"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        result = fsm.trigger("test_trigger")

        assert result.success
        assert condition.received_kwargs == {}


class TestConditionExceptionHandling:
    """Test exception handling in conditions"""

    def test_condition_exception_caught(self, basic_fsm, caplog):
        """Test that condition exceptions are caught and logged"""
        fsm, initial_state, target_state = basic_fsm
        condition = ExceptionCondition(ValueError("test error"))

        fsm.add_transition("test_trigger", "initial", "target", condition)

        with caplog.at_level(logging.WARNING):
            result = fsm.trigger("test_trigger", test_arg="value")

        assert not result.success
        assert (
            result.error
            == "Condition 'exception_condition' raised exception: test error"
        )
        assert (
            "FAILED - Condition 'exception_condition' raised exception" in caplog.text
        )

        # FSM state should not have changed
        assert fsm.current_state.name == "initial"

    def test_different_exception_types(self, basic_fsm):
        """Test handling of different exception types"""
        fsm, initial_state, target_state = basic_fsm

        # Test RuntimeError
        condition = ExceptionCondition(RuntimeError("runtime error"))
        fsm.add_transition("runtime_trigger", "initial", "target", condition)

        result = fsm.trigger("runtime_trigger")
        assert not result.success
        assert "runtime error" in result.error

        # Test AttributeError
        condition2 = ExceptionCondition(AttributeError("attribute error"))
        fsm.add_transition("attr_trigger", "initial", "target", condition2)

        result = fsm.trigger("attr_trigger")
        assert not result.success
        assert "attribute error" in result.error

    def test_condition_exception_with_kwargs(self, basic_fsm):
        """Test exception handling preserves original kwargs context"""
        fsm, initial_state, target_state = basic_fsm
        condition = ExceptionCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        result = fsm.trigger(
            "test_trigger",
            important_context="should_be_preserved",
            _private="should_be_filtered",
        )

        assert not result.success
        assert result.from_state == "initial"
        assert result.trigger == "test_trigger"


class TestSafetyIntegration:
    """Integration tests for safety features"""

    def test_can_trigger_with_safety(self, basic_fsm):
        """Test that can_trigger also uses safety mechanisms"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        # Test can_trigger with private attributes
        can_trigger = fsm.can_trigger(
            "test_trigger", normal_arg="value", _private="filtered"
        )

        assert can_trigger
        # Condition should have received sanitized kwargs
        assert condition.received_kwargs == {"normal_arg": "value"}
        assert "_private" not in condition.received_kwargs

    def test_safety_with_multiple_conditions(self, basic_fsm):
        """Test safety with multiple conditions on same transition"""
        fsm, initial_state, target_state = basic_fsm

        condition = MockCondition(True)

        # Add transition with condition
        fsm.add_transition("test_trigger", "initial", "target", condition)

        # For this test, we'll verify the pattern works with one condition
        # (Multiple conditions per transition would require FSM enhancement)
        result = fsm.trigger("test_trigger", normal_arg="value", _private="filtered")

        assert result.success
        assert condition.received_kwargs == {"normal_arg": "value"}

    def test_safety_performance_impact(self, basic_fsm):
        """Test that safety features don't significantly impact performance"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        import time

        # Measure time for many triggers
        start = time.time()
        for i in range(1000):
            # Reset to initial state for each iteration
            fsm._current_state = initial_state
            fsm.trigger("test_trigger", arg=i)

        elapsed = time.time() - start

        # Should complete 1000 operations in reasonable time (< 1 second)
        assert elapsed < 1.0

    def test_logging_integration(self, basic_fsm, caplog):
        """Test that safety logging integrates properly with FSM logging"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        with caplog.at_level(logging.DEBUG):
            result = fsm.trigger(
                "test_trigger", normal_arg="value", _private="filtered"
            )

        assert result.success

        # Should see both safety and FSM log messages
        log_text = caplog.text
        assert "Skipping private kwarg '_private'" in log_text
        assert "Evaluating condition 'mock_condition'" in log_text


class TestRealWorldScenarios:
    """Test safety with real-world usage patterns"""

    def test_aircraft_scenario_safety(self):
        """Test safety with aircraft-like scenario from benchmarks"""

        class AircraftCondition(Condition):
            def __init__(self):
                super().__init__("aircraft_condition", "Aircraft safety check")
                self.last_kwargs = {}

            def check(self, **kwargs):
                self.last_kwargs = kwargs
                aircraft = kwargs.get("aircraft")
                return aircraft is not None

        # Create FSM
        normal = State("normal")
        maneuvering = State("maneuvering")

        fsm = StateMachine(normal, name="aircraft")
        fsm.add_state(maneuvering)

        condition = AircraftCondition()
        fsm.add_transition("maneuver", "normal", "maneuvering", condition)

        # Mock aircraft object
        aircraft = Mock()
        aircraft.altitude = 10000

        # Trigger with real-world kwargs pattern
        result = fsm.trigger(
            "maneuver",
            aircraft=aircraft,
            traffic_data={"distance": 1.5},
            _internal_state="filtered",
            tcas=Mock(),
        )

        assert result.success

        # Should receive sanitized kwargs
        received = condition.last_kwargs
        assert "aircraft" in received
        assert "traffic_data" in received
        assert "tcas" in received
        assert "_internal_state" not in received

    def test_complex_object_kwargs(self, basic_fsm):
        """Test safety with complex objects in kwargs"""
        fsm, initial_state, target_state = basic_fsm
        condition = MockCondition()

        fsm.add_transition("test_trigger", "initial", "target", condition)

        # Create complex objects
        complex_object = {
            "nested": {"data": [1, 2, 3]},
            "function": lambda x: x + 1,
            "class_instance": Mock(),
        }

        result = fsm.trigger(
            "test_trigger", complex_data=complex_object, simple_data="string"
        )

        assert result.success
        # Complex objects should pass through (individual conditions validate)
        assert condition.received_kwargs["complex_data"] == complex_object
        assert condition.received_kwargs["simple_data"] == "string"


if __name__ == "__main__":
    pytest.main([__file__])
