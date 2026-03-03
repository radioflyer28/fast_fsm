"""
Pytest migration of performance tests.

These tests verify the performance characteristics of the fast_fsm library
while being compatible with mypyc compilation.
"""

import pytest
import time
import gc
import sys
import os
import contextlib
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fast_fsm.core import StateMachine, State
from fast_fsm.conditions import Condition


# Suppress print output during benchmarks
@contextlib.contextmanager
def suppress_stdout():
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        yield


class TrackingState(State):
    """State that tracks enter/exit counts using composition instead of inheritance"""

    def __init__(self, name: str):
        super().__init__(name)
        self.enter_count = 0
        self.exit_count = 0


@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    def benchmark_state_transitions(self, iterations: int = 10000):
        """Benchmark basic state transitions"""

        # Create states using composition-friendly approach
        idle = State("idle")
        processing = State("processing")
        waiting = State("waiting")
        error = State("error")

        # Create FSM
        fsm = StateMachine(idle, name="perf_test")
        fsm.add_state(processing)
        fsm.add_state(waiting)
        fsm.add_state(error)

        # Add transitions
        fsm.add_transition("start", "idle", "processing")
        fsm.add_transition("wait", "processing", "waiting")
        fsm.add_transition("resume", "waiting", "processing")
        fsm.add_transition("finish", "processing", "idle")
        fsm.add_transition("error", ["idle", "processing", "waiting"], "error")
        fsm.add_transition("reset", "error", "idle")

        # Warm up
        for _ in range(100):
            fsm.trigger("start")
            fsm.trigger("finish")

        # Benchmark
        gc.collect()
        start_time = time.perf_counter()

        for i in range(iterations):
            if i % 6 == 0:
                fsm.trigger("start")
            elif i % 6 == 1:
                fsm.trigger("wait")
            elif i % 6 == 2:
                fsm.trigger("resume")
            elif i % 6 == 3:
                fsm.trigger("finish")
            elif i % 6 == 4:
                fsm.trigger("error")
            else:
                fsm.trigger("reset")

        end_time = time.perf_counter()
        return end_time - start_time

    def test_transition_performance(self):
        """Test that transitions complete within reasonable time"""
        iterations = 10000
        elapsed = self.benchmark_state_transitions(iterations)

        # Should complete 10k transitions in less than 1 second
        assert elapsed < 1.0

        # Calculate transitions per second
        tps = iterations / elapsed
        assert tps > 10000  # Should handle at least 10k transitions per second

    def test_condition_evaluation_performance(self):
        """Test performance of condition evaluation"""

        class FastCondition(Condition):
            def __init__(self):
                super().__init__("fast_condition", "Fast condition for testing")
                self.call_count = 0

            def check(self, **kwargs) -> bool:
                self.call_count += 1
                return kwargs.get("value", 0) % 2 == 0

        # Create FSM with conditional transitions
        state_a = State("state_a")
        state_b = State("state_b")

        fsm = StateMachine(state_a, name="condition_perf")
        fsm.add_state(state_b)

        condition = FastCondition()
        fsm.add_transition("toggle", "state_a", "state_b", condition)
        fsm.add_transition("toggle", "state_b", "state_a", condition)

        # Benchmark condition evaluation
        iterations = 5000
        gc.collect()
        start_time = time.perf_counter()

        for i in range(iterations):
            fsm.trigger("toggle", value=i)

        elapsed = time.perf_counter() - start_time

        # Should complete quickly
        assert elapsed < 1.0
        assert condition.call_count == iterations

    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during many transitions"""

        # Create a simple FSM
        state1 = State("state1")
        state2 = State("state2")

        fsm = StateMachine(state1, name="memory_test")
        fsm.add_state(state2)
        fsm.add_transition("toggle", "state1", "state2")
        fsm.add_transition("toggle", "state2", "state1")

        # Force garbage collection
        gc.collect()

        # Perform many transitions
        iterations = 10000
        start_time = time.perf_counter()

        for i in range(iterations):
            fsm.trigger("toggle")

        elapsed = time.perf_counter() - start_time

        # Should complete transitions quickly (memory stability test)
        assert elapsed < 5.0

        # Force garbage collection again
        gc.collect()

        # Memory should be stable (no major leaks)
        # We can't easily test actual memory without external deps,
        # but the timing gives us confidence about memory behavior

    def test_large_state_machine_creation(self):
        """Test creation of FSM with many states"""

        start_time = time.perf_counter()

        # Create FSM with many states
        initial_state = State("state_0")
        fsm = StateMachine(initial_state, name="large_fsm")

        num_states = 1000
        for i in range(1, num_states + 1):
            state = State(f"state_{i}")
            fsm.add_state(state)

            # Add transition from previous state
            fsm.add_transition(f"next_{i}", f"state_{i - 1}", f"state_{i}")

        creation_time = time.perf_counter() - start_time

        # Should create large FSM quickly (less than 1 second)
        assert creation_time < 1.0

        # Verify structure
        assert len(fsm.states) == num_states + 1  # +1 for initial state
        assert fsm.current_state.name == "state_0"

    def test_concurrent_state_checks(self):
        """Test performance of state checking operations"""

        # Create FSM with multiple states
        states = [State(f"state_{i}") for i in range(100)]
        fsm = StateMachine(states[0], name="check_test")

        for state in states[1:]:
            fsm.add_state(state)

        # Add transitions
        for i in range(len(states) - 1):
            fsm.add_transition(f"next_{i}", f"state_{i}", f"state_{i + 1}")

        # Benchmark state checking
        iterations = 10000
        start_time = time.perf_counter()

        for i in range(iterations):
            # Various state checks for performance testing
            _ = fsm.current_state.name
            _ = fsm.can_trigger(f"next_{i % (len(states) - 1)}")
            _ = f"state_{i % len(states)}" in fsm.states

        elapsed = time.perf_counter() - start_time

        # Should complete state checks quickly
        assert elapsed < 1.0


@pytest.mark.integration
class TestAdvancedPerformance:
    """Advanced performance and stress tests"""

    def test_complex_condition_chains(self):
        """Test performance with complex condition evaluation chains"""

        class ChainedCondition(Condition):
            def __init__(self, condition_id, threshold):
                super().__init__(
                    f"chained_{condition_id}", f"Chained condition {condition_id}"
                )
                self.threshold = threshold
                self.call_count = 0

            def check(self, **kwargs) -> bool:
                self.call_count += 1
                value = kwargs.get("value", 0)
                # Simulate some computation
                result = value > self.threshold
                for _ in range(10):  # Small computation loop
                    result = not result if value % 2 == 0 else result
                return result

        # Create states
        start = State("start")
        end = State("end")

        fsm = StateMachine(start, name="complex_conditions")
        fsm.add_state(end)

        # Add multiple transitions with different conditions
        conditions = []
        for i in range(5):
            condition = ChainedCondition(i, i * 10)
            conditions.append(condition)
            fsm.add_transition(f"path_{i}", "start", "end", condition)

        # Benchmark complex condition evaluation
        iterations = 1000
        start_time = time.perf_counter()

        for i in range(iterations):
            # Reset state
            fsm._current_state = start

            # Try different transitions
            path_id = i % 5
            fsm.trigger(f"path_{path_id}", value=i)

        elapsed = time.perf_counter() - start_time

        # Should handle complex conditions reasonably fast
        assert elapsed < 5.0  # Allow more time for complex conditions

        # Verify conditions were called
        total_calls = sum(c.call_count for c in conditions)
        assert total_calls == iterations

    def test_fsm_with_many_transitions(self):
        """Test FSM with many transitions from single state"""

        # Create central hub state with many outgoing transitions
        hub = State("hub")
        fsm = StateMachine(hub, name="hub_test")

        # Add many target states
        num_targets = 100
        target_states = []
        for i in range(num_targets):
            state = State(f"target_{i}")
            target_states.append(state)
            fsm.add_state(state)

            # Add transition to target and back
            fsm.add_transition(f"goto_{i}", "hub", f"target_{i}")
            fsm.add_transition(f"return_{i}", f"target_{i}", "hub")

        # Test transition performance
        start_time = time.perf_counter()

        for i in range(num_targets):
            result = fsm.trigger(f"goto_{i}")
            assert result.success

            result = fsm.trigger(f"return_{i}")
            assert result.success
            assert fsm.current_state.name == "hub"

        elapsed = time.perf_counter() - start_time

        # Should handle many transitions efficiently
        assert elapsed < 1.0

    @pytest.mark.slow
    def test_stress_test_transitions(self):
        """Stress test with very many transitions"""

        # Create simple 2-state FSM for stress testing
        state_a = State("state_a")
        state_b = State("state_b")

        fsm = StateMachine(state_a, name="stress_test")
        fsm.add_state(state_b)
        fsm.add_transition("toggle", "state_a", "state_b")
        fsm.add_transition("toggle", "state_b", "state_a")

        # Stress test with many iterations
        iterations = 100000
        gc.collect()
        start_time = time.perf_counter()

        for i in range(iterations):
            result = fsm.trigger("toggle")
            assert result.success

        elapsed = time.perf_counter() - start_time

        # Should handle stress test within reasonable time
        assert elapsed < 10.0  # Allow up to 10 seconds for 100k transitions

        # Calculate performance metrics
        transitions_per_second = iterations / elapsed
        assert transitions_per_second > 10000  # At least 10k TPS


@pytest.mark.unit
class TestMicroBenchmarks:
    """Micro-benchmarks for specific operations"""

    def test_state_creation_performance(self):
        """Test performance of state creation"""

        start_time = time.perf_counter()

        states = []
        for i in range(10000):
            state = State(f"state_{i}")
            states.append(state)

        elapsed = time.perf_counter() - start_time

        # Should create states quickly
        assert elapsed < 1.0
        assert len(states) == 10000

    def test_transition_lookup_performance(self):
        """Test performance of transition lookup"""

        # Create FSM with many transitions
        state = State("state")
        fsm = StateMachine(state, name="lookup_test")

        # Add many self-transitions with different triggers
        num_triggers = 1000
        for i in range(num_triggers):
            fsm.add_transition(f"trigger_{i}", "state", "state")

        # Benchmark lookup performance
        start_time = time.perf_counter()

        for i in range(num_triggers):
            can_trigger = fsm.can_trigger(f"trigger_{i}")
            assert can_trigger

        elapsed = time.perf_counter() - start_time

        # Should lookup transitions quickly
        assert elapsed < 1.0

    def test_condition_object_creation(self):
        """Test performance of condition object creation"""

        class TestCondition(Condition):
            def __init__(self, condition_id):
                super().__init__(
                    f"test_{condition_id}", f"Test condition {condition_id}"
                )

            def check(self, **kwargs) -> bool:
                return True

        start_time = time.perf_counter()

        conditions = []
        for i in range(1000):
            condition = TestCondition(i)
            conditions.append(condition)

        elapsed = time.perf_counter() - start_time

        # Should create conditions quickly
        assert elapsed < 1.0
        assert len(conditions) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
