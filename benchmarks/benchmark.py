#!/usr/bin/env python3

# =============================================================================
# BENCHMARK SETUP
# =============================================================================

import time
import gc
import sys
import os
from typing import Dict, Any, Callable
import io
import contextlib

# Add parent directory to path to import fast_fsm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import benchmark_my_fsm as my_fsm
import benchmark_py_fsm as py_fsm
import benchmark_transitions_fsm as transitions_fsm
import benchmark_fast_fsm as bench_fast_fsm


class BenchmarkSuite:
    """Comprehensive benchmark suite for comparing FSM implementations"""

    def __init__(self):
        self.results = {}
        self.output_buffer = io.StringIO()

    def time_function(self, func: Callable, iterations: int = 1000) -> float:
        """Time a function execution with warmup and garbage collection"""
        # Warmup
        for _ in range(min(10, iterations // 10)):
            func()

        # Clear garbage before timing
        gc.collect()

        start_time = time.perf_counter()
        for _ in range(iterations):
            func()
        end_time = time.perf_counter()

        # Return time in milliseconds per iteration
        return ((end_time - start_time) / iterations) * 1000

    def memory_profile(self, func: Callable) -> tuple:
        """Profile memory usage of a function"""
        import tracemalloc

        tracemalloc.start()

        # Clear existing memory
        gc.collect()

        func()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return current, peak

    @contextlib.contextmanager
    def suppress_output(self):
        """Context manager to suppress print output during benchmarking"""
        old_stdout = sys.stdout
        sys.stdout = self.output_buffer
        try:
            yield
        finally:
            sys.stdout = old_stdout


def benchmark_my_fsm(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark the custom FSM implementation (my_fsm.py)"""

    suite = BenchmarkSuite()

    def create_aircraft():
        """Test aircraft creation"""
        with suite.suppress_output():
            aircraft = my_fsm.Aircraft("TEST", 10000)
            return aircraft

    def basic_transitions():
        """Test basic state transitions"""
        with suite.suppress_output():
            aircraft = my_fsm.Aircraft("TEST", 10000)
            aircraft.request_climb(1000)
            aircraft.complete_maneuver()
            aircraft.request_descend(1000)
            aircraft.complete_maneuver()

    def tcas_scenario():
        """Test TCAS collision avoidance scenario"""
        with suite.suppress_output():
            aircraft = my_fsm.Aircraft("TEST", 10000)
            tcas = my_fsm.CollisionAvoidanceSystem(aircraft)

            # Create traffic scenario
            traffic = my_fsm.TrafficData(
                distance=2.0,
                altitude_difference=500,
                closing_rate=150,
                bearing=45,
                time_to_closest_approach=10,
            )

            # Simulate TCAS response
            tcas.update_traffic(traffic)
            tcas.maneuver_complete()
            tcas.clear_traffic()

    def emergency_maneuvers():
        """Test emergency maneuver sequences"""
        with suite.suppress_output():
            aircraft = my_fsm.Aircraft("TEST", 10000)
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver()
            aircraft.request_emergency_descend(2500)
            aircraft.complete_maneuver()

    def complex_scenario():
        """Test complex multi-step scenario"""
        with suite.suppress_output():
            aircraft = my_fsm.Aircraft("TEST", 10000)
            tcas = my_fsm.CollisionAvoidanceSystem(aircraft)

            # Normal flight operations
            aircraft.request_climb(1000)
            aircraft.complete_maneuver()

            # TCAS activation
            traffic = my_fsm.TrafficData(1.5, 200, 200, 90, 8)
            tcas.update_traffic(traffic)

            # Emergency response
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver()

            # Recovery
            tcas.maneuver_complete()
            tcas.clear_traffic()

    # Run benchmarks
    results = {
        "implementation": "my_fsm",
        "aircraft_creation_time": suite.time_function(create_aircraft, iterations),
        "basic_transitions_time": suite.time_function(basic_transitions, iterations),
        "tcas_scenario_time": suite.time_function(tcas_scenario, iterations),
        "emergency_maneuvers_time": suite.time_function(
            emergency_maneuvers, iterations
        ),
        "complex_scenario_time": suite.time_function(complex_scenario, iterations),
    }

    # Memory profiling
    results["aircraft_creation_memory"] = suite.memory_profile(create_aircraft)
    results["basic_transitions_memory"] = suite.memory_profile(basic_transitions)
    results["tcas_scenario_memory"] = suite.memory_profile(tcas_scenario)
    results["complex_scenario_memory"] = suite.memory_profile(complex_scenario)

    return results


def benchmark_py_fsm(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark the python-statemachine implementation (py_fsm.py)"""

    suite = BenchmarkSuite()

    def create_aircraft():
        """Test aircraft creation"""
        with suite.suppress_output():
            aircraft = py_fsm.Aircraft("TEST", 10000)
            return aircraft

    def basic_transitions():
        """Test basic state transitions"""
        with suite.suppress_output():
            aircraft = py_fsm.Aircraft("TEST", 10000)
            aircraft.request_climb(1000)
            aircraft.complete_maneuver()
            aircraft.request_descend(1000)
            aircraft.complete_maneuver()

    def tcas_scenario():
        """Test TCAS collision avoidance scenario"""
        with suite.suppress_output():
            aircraft = py_fsm.Aircraft("TEST", 10000)
            tcas = py_fsm.CollisionAvoidanceSystem(aircraft)

            # Create traffic scenario
            traffic = py_fsm.TrafficData(
                distance=2.0,
                altitude_difference=500,
                closing_rate=150,
                bearing=45,
                time_to_closest_approach=10,
            )

            # Simulate TCAS response
            tcas.update_traffic(traffic)
            tcas.maneuver_complete()
            tcas.clear_traffic()

    def emergency_maneuvers():
        """Test emergency maneuver sequences"""
        with suite.suppress_output():
            aircraft = py_fsm.Aircraft("TEST", 10000)
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver()
            aircraft.request_emergency_descend(2500)
            aircraft.complete_maneuver()

    def complex_scenario():
        """Test complex multi-step scenario"""
        with suite.suppress_output():
            aircraft = py_fsm.Aircraft("TEST", 10000)
            tcas = py_fsm.CollisionAvoidanceSystem(aircraft)

            # Normal flight operations
            aircraft.request_climb(1000)
            aircraft.complete_maneuver()

            # TCAS activation
            traffic = py_fsm.TrafficData(1.5, 200, 200, 90, 8)
            tcas.update_traffic(traffic)

            # Emergency response
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver()

            # Recovery
            tcas.maneuver_complete()
            tcas.clear_traffic()

    # Run benchmarks
    results = {
        "implementation": "py_fsm",
        "aircraft_creation_time": suite.time_function(create_aircraft, iterations),
        "basic_transitions_time": suite.time_function(basic_transitions, iterations),
        "tcas_scenario_time": suite.time_function(tcas_scenario, iterations),
        "emergency_maneuvers_time": suite.time_function(
            emergency_maneuvers, iterations
        ),
        "complex_scenario_time": suite.time_function(complex_scenario, iterations),
    }

    # Memory profiling
    results["aircraft_creation_memory"] = suite.memory_profile(create_aircraft)
    results["basic_transitions_memory"] = suite.memory_profile(basic_transitions)
    results["tcas_scenario_memory"] = suite.memory_profile(tcas_scenario)
    results["complex_scenario_memory"] = suite.memory_profile(complex_scenario)

    return results


def benchmark_fast_fsm(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark the fast_fsm implementation (fast_fsm_aircraft.py)"""

    suite = BenchmarkSuite()

    def create_aircraft():
        """Test aircraft creation"""
        with suite.suppress_output():
            aircraft = bench_fast_fsm.Aircraft("TEST", 10000)
            return aircraft

    def basic_transitions():
        """Test basic state transitions"""
        with suite.suppress_output():
            aircraft = bench_fast_fsm.Aircraft("TEST", 10000)
            aircraft.request_climb(1000)
            aircraft.complete_maneuver()
            aircraft.request_descend(1000)
            aircraft.complete_maneuver()

    def tcas_scenario():
        """Test TCAS collision avoidance scenario"""
        with suite.suppress_output():
            aircraft = bench_fast_fsm.Aircraft("TEST", 10000)
            tcas = bench_fast_fsm.CollisionAvoidanceSystem(aircraft)

            # Create traffic scenario
            traffic = bench_fast_fsm.TrafficData(
                distance=2.0,
                altitude_difference=500,
                closing_rate=150,
                bearing=45,
                time_to_closest_approach=10,
            )

            # Simulate TCAS response
            tcas.update_traffic(traffic)
            tcas.maneuver_complete()
            tcas.clear_traffic()

    def emergency_maneuvers():
        """Test emergency maneuver sequences"""
        with suite.suppress_output():
            aircraft = bench_fast_fsm.Aircraft("TEST", 10000)
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver()
            aircraft.request_emergency_descend(2500)
            aircraft.complete_maneuver()

    def complex_scenario():
        """Test complex multi-step scenario"""
        with suite.suppress_output():
            aircraft = bench_fast_fsm.Aircraft("TEST", 10000)
            tcas = bench_fast_fsm.CollisionAvoidanceSystem(aircraft)

            # Normal flight operations
            aircraft.request_climb(1000)
            aircraft.complete_maneuver()

            # TCAS activation
            traffic = bench_fast_fsm.TrafficData(1.5, 200, 200, 90, 8)
            tcas.update_traffic(traffic)

            # Emergency response
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver()

            # Recovery
            tcas.maneuver_complete()
            tcas.clear_traffic()

    # Run benchmarks
    results = {
        "implementation": "fast_fsm",
        "aircraft_creation_time": suite.time_function(create_aircraft, iterations),
        "basic_transitions_time": suite.time_function(basic_transitions, iterations),
        "tcas_scenario_time": suite.time_function(tcas_scenario, iterations),
        "emergency_maneuvers_time": suite.time_function(
            emergency_maneuvers, iterations
        ),
        "complex_scenario_time": suite.time_function(complex_scenario, iterations),
    }

    # Memory profiling
    results["aircraft_creation_memory"] = suite.memory_profile(create_aircraft)
    results["basic_transitions_memory"] = suite.memory_profile(basic_transitions)
    results["tcas_scenario_memory"] = suite.memory_profile(tcas_scenario)
    results["complex_scenario_memory"] = suite.memory_profile(complex_scenario)

    return results


def benchmark_transitions_fsm(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark the transitions library implementation (transitions_fsm.py)"""

    suite = BenchmarkSuite()

    def create_aircraft():
        """Test aircraft creation"""
        with suite.suppress_output():
            aircraft = transitions_fsm.Aircraft("TEST", 10000)
            return aircraft

    def basic_transitions():
        """Test basic state transitions"""
        with suite.suppress_output():
            aircraft = transitions_fsm.Aircraft("TEST", 10000)
            aircraft.request_climb(1000)
            aircraft.complete_maneuver_request()
            aircraft.request_descend(1000)
            aircraft.complete_maneuver_request()

    def tcas_scenario():
        """Test TCAS collision avoidance scenario"""
        with suite.suppress_output():
            aircraft = transitions_fsm.Aircraft("TEST", 10000)
            tcas = transitions_fsm.CollisionAvoidanceSystem(aircraft)

            # Create traffic scenario
            traffic = transitions_fsm.TrafficData(
                distance=2.0,
                altitude_difference=500,
                closing_rate=150,
                bearing=45,
                time_to_closest_approach=10,
            )

            # Simulate TCAS response
            tcas.update_traffic(traffic)
            tcas.maneuver_complete()
            tcas.clear_traffic()

    def emergency_maneuvers():
        """Test emergency maneuver sequences"""
        with suite.suppress_output():
            aircraft = transitions_fsm.Aircraft("TEST", 10000)
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver_request()
            aircraft.request_emergency_descend(2500)
            aircraft.complete_maneuver_request()

    def complex_scenario():
        """Test complex multi-step scenario"""
        with suite.suppress_output():
            aircraft = transitions_fsm.Aircraft("TEST", 10000)
            tcas = transitions_fsm.CollisionAvoidanceSystem(aircraft)

            # Normal flight operations
            aircraft.request_climb(1000)
            aircraft.complete_maneuver_request()

            # TCAS activation
            traffic = transitions_fsm.TrafficData(1.5, 200, 200, 90, 8)
            tcas.update_traffic(traffic)

            # Emergency response
            aircraft.request_emergency_climb(2500)
            aircraft.complete_maneuver_request()

            # Recovery
            tcas.maneuver_complete()
            tcas.clear_traffic()

    # Run benchmarks
    results = {
        "implementation": "transitions_fsm",
        "aircraft_creation_time": suite.time_function(create_aircraft, iterations),
        "basic_transitions_time": suite.time_function(basic_transitions, iterations),
        "tcas_scenario_time": suite.time_function(tcas_scenario, iterations),
        "emergency_maneuvers_time": suite.time_function(
            emergency_maneuvers, iterations
        ),
        "complex_scenario_time": suite.time_function(complex_scenario, iterations),
    }

    # Memory profiling
    results["aircraft_creation_memory"] = suite.memory_profile(create_aircraft)
    results["basic_transitions_memory"] = suite.memory_profile(basic_transitions)
    results["tcas_scenario_memory"] = suite.memory_profile(tcas_scenario)
    results["complex_scenario_memory"] = suite.memory_profile(complex_scenario)

    return results


def run_comparison_benchmark(iterations: int = 1000) -> Dict[str, Any]:
    """Run comprehensive comparison between all four FSM implementations"""

    print("🚀 Starting FSM Performance Benchmark...")
    print(f"Running {iterations} iterations for each test...")
    print("Times reported in milliseconds (ms) per operation")
    print("=" * 60)

    # Run benchmarks for all implementations
    print("\n📊 Benchmarking my_fsm.py (custom implementation)...")
    my_fsm_results = benchmark_my_fsm(iterations)

    print("📊 Benchmarking py_fsm.py (python-statemachine library)...")
    py_fsm_results = benchmark_py_fsm(iterations)

    print("📊 Benchmarking transitions_fsm.py (transitions library)...")
    transitions_fsm_results = benchmark_transitions_fsm(iterations)

    print("📊 Benchmarking fast_fsm.py (optimized implementation with logging)...")
    fast_fsm_results = benchmark_fast_fsm(iterations)

    # Compare results
    comparison = {
        "my_fsm": my_fsm_results,
        "py_fsm": py_fsm_results,
        "transitions_fsm": transitions_fsm_results,
        "fast_fsm": fast_fsm_results,
        "comparison": {},
    }

    # Calculate performance ratios
    time_metrics = [
        "aircraft_creation_time",
        "basic_transitions_time",
        "tcas_scenario_time",
        "emergency_maneuvers_time",
        "complex_scenario_time",
    ]

    print("\n🏆 Performance Comparison Results:")
    print("=" * 60)

    for metric in time_metrics:
        my_time = my_fsm_results[metric]
        py_time = py_fsm_results[metric]
        transitions_time = transitions_fsm_results[metric]
        fast_fsm_time = fast_fsm_results[metric]

        # Find the fastest implementation
        times = {
            "my_fsm": my_time,
            "py_fsm": py_time,
            "transitions_fsm": transitions_time,
            "fast_fsm": fast_fsm_results[metric],
        }

        fastest = min(times.keys(), key=lambda k: times[k])

        print(f"{metric.replace('_', ' ').title()}:")
        for impl_name, impl_time in times.items():
            print(f"  {impl_name}:  {impl_time:.3f}ms")
        print(
            f"  Winner:  {fastest} (py_fsm: {py_time / my_time:.2f}x, transitions: {transitions_time / my_time:.2f}x, fast_fsm: {fast_fsm_time / my_time:.2f}x vs my_fsm)"
        )
        print()

        comparison["comparison"][metric] = {
            "my_fsm": my_time,
            "py_fsm": py_time,
            "transitions_fsm": transitions_time,
            "fast_fsm": fast_fsm_time,
            "fastest": fastest,
            "py_fsm_vs_my_fsm_ratio": py_time / my_time,
            "transitions_vs_my_fsm_ratio": transitions_time / my_time,
            "fast_fsm_vs_my_fsm_ratio": fast_fsm_time / my_time,
            "transitions_vs_py_fsm_ratio": transitions_time / py_time,
            "fast_fsm_vs_py_fsm_ratio": fast_fsm_time / py_time,
            "fast_fsm_vs_transitions_ratio": fast_fsm_time / transitions_time,
        }

    # Memory comparison
    print("💾 Memory Usage Comparison:")
    print("=" * 60)

    memory_metrics = [
        "aircraft_creation_memory",
        "basic_transitions_memory",
        "tcas_scenario_memory",
        "complex_scenario_memory",
    ]

    for metric in memory_metrics:
        my_current, my_peak = my_fsm_results[metric]
        py_current, py_peak = py_fsm_results[metric]
        transitions_current, transitions_peak = transitions_fsm_results[metric]
        fast_fsm_current, fast_fsm_peak = fast_fsm_results[metric]

        comparison["comparison"][metric] = {
            "my_fsm_current": my_current,
            "my_fsm_peak": my_peak,
            "py_fsm_current": py_current,
            "py_fsm_peak": py_peak,
            "transitions_current": transitions_current,
            "transitions_peak": transitions_peak,
            "fast_fsm_current": fast_fsm_current,
            "fast_fsm_peak": fast_fsm_peak,
        }

        print(f"{metric.replace('_memory', '').replace('_', ' ').title()}:")
        print(
            f"  my_fsm:  {my_current / 1024:.1f}KB current, {my_peak / 1024:.1f}KB peak"
        )
        print(
            f"  py_fsm:  {py_current / 1024:.1f}KB current, {py_peak / 1024:.1f}KB peak"
        )
        print(
            f"  transitions_fsm:  {transitions_current / 1024:.1f}KB current, {transitions_peak / 1024:.1f}KB peak"
        )
        print(
            f"  fast_fsm:  {fast_fsm_current / 1024:.1f}KB current, {fast_fsm_peak / 1024:.1f}KB peak"
        )
        print()

    # Overall summary
    fastest_counts = {}
    for metric in time_metrics:
        fastest = comparison["comparison"][metric]["fastest"]
        fastest_counts[fastest] = fastest_counts.get(fastest, 0) + 1

    print("🎯 Overall Performance Summary:")
    print("=" * 60)
    for impl, count in fastest_counts.items():
        print(f"{impl} wins: {count}/{len(time_metrics)} benchmarks")

    winner = max(fastest_counts.keys(), key=lambda k: fastest_counts[k])
    print(f"🏆 Overall Winner: {winner}")

    return comparison


if __name__ == "__main__":
    # Run the comprehensive comparison
    results = run_comparison_benchmark(iterations=1000)

    # Optional: Save results to file
    import json

    with open("benchmark_results.json", "w") as f:
        # Convert memory tuples to lists for JSON serialization
        serializable_results = results.copy()
        for impl in ["my_fsm", "py_fsm", "transitions_fsm", "fast_fsm"]:
            for key, value in serializable_results[impl].items():
                if isinstance(value, tuple):
                    serializable_results[impl][key] = list(value)

        json.dump(serializable_results, f, indent=2)

    print("\n💾 Results saved to benchmark_results.json")
