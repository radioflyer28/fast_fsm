#!/usr/bin/env python3
"""Environment-labelled observations for Fast FSM dispatch semantics.

This reporter is intentionally descriptive. The deterministic benchmark tests
enforce the O(1) source/trigger lookup and local O(k) group-work contract;
these timing rows show representative runtime observations only.
"""

from __future__ import annotations

import argparse
import importlib.machinery
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
from collections.abc import Callable

import fast_fsm
import fast_fsm.core as core
from fast_fsm import State, StateMachine, TransitionRejected
from fast_fsm.conditions import Condition


TOPOLOGY_SIZES = (4, 64, 512)
GROUP_DEPTHS = (2, 8, 32)
WINNER_POSITIONS = ("first", "middle", "last", "exhausted")
DEFAULT_SAMPLE_COUNT = 5
DEFAULT_ITERATIONS = 1_000
SEMANTIC_SCENARIOS = (
    "final_entry",
    "internal_self",
    "external_self",
    "expected_rejection",
)


class _PriorityCondition(Condition):
    """Count one candidate's actual evaluation during a descriptive sample."""

    __slots__ = ("calls", "rank", "winner_rank")

    def __init__(self, rank: int, winner_rank: int | None) -> None:
        super().__init__(f"rank-{rank}", "priority-group benchmark guard")
        self.calls = 0
        self.rank = rank
        self.winner_rank = winner_rank

    def check(self, *args: object, **kwargs: object) -> bool:
        self.calls += 1
        return self.rank == self.winner_rank


def performance_header(title: str) -> None:
    """Print a formatted benchmark header."""
    print(f"\n{'=' * 60}")
    print(f"🚀 {title}")
    print(f"{'=' * 60}")


def measure_time(operation: Callable[[], None], iterations: int) -> float:
    """Measure a fixed number of operations with a high-resolution clock."""
    started = time.perf_counter_ns()
    for _ in range(iterations):
        operation()
    return (time.perf_counter_ns() - started) / 1_000_000_000


def _winner_rank(group_depth: int, winner_position: str) -> int | None:
    """Return the rank represented by a descriptive position label."""
    if winner_position == "first":
        return 0
    if winner_position == "middle":
        return group_depth // 2
    if winner_position == "last":
        return group_depth - 1
    if winner_position == "exhausted":
        return None
    raise ValueError(f"unknown winner position: {winner_position}")


def _build_priority_group_machine(
    *, group_depth: int, topology_size: int, winner_rank: int | None
) -> tuple[StateMachine, tuple[_PriorityCondition, ...]]:
    """Build repeatable group-dispatch sources plus unrelated topology."""
    source = State("source")
    targets = tuple(State(f"target-{rank}") for rank in range(group_depth))
    machine = StateMachine(source, name=f"priority-group-{group_depth}-{topology_size}")
    for state in targets:
        machine.add_state(state)
    conditions = tuple(
        _PriorityCondition(rank, winner_rank) for rank in range(group_depth)
    )

    # Every reachable result state gets the same finite group so a sample can
    # repeatedly measure priority dispatch without private state mutation.
    for candidate_source in (source, *targets):
        for rank, target in enumerate(targets):
            machine.add_transition(
                "priority_tick",
                candidate_source,
                target,
                conditions[rank],
                priority=rank,
            )
    for index in range(topology_size):
        machine.add_state(State(f"unrelated-{index}"))
    return machine, conditions


def _uv_version() -> str:
    """Return the invoking uv version when available without timing it."""
    try:
        completed = subprocess.run(
            ["uv", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    if completed.returncode != 0:
        return "unavailable"
    version = completed.stdout.strip()
    return version or "unavailable"


def _runtime_labels() -> dict[str, str]:
    """Describe the interpreter and actual core loader origin for each row."""
    origin = Path(core.__file__ or "<unknown>").resolve()
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    mode = "compiled-native" if str(origin).endswith(suffixes) else "pure-python"
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "core_mode": mode,
        "core_origin": str(origin),
        "distribution_version": fast_fsm.__version__,
        "platform": platform.platform(),
        "uv_version": _uv_version(),
    }


def collect_priority_group_observations(
    *,
    topology_sizes: tuple[int, ...] = TOPOLOGY_SIZES,
    group_depths: tuple[int, ...] = GROUP_DEPTHS,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
    iterations: int = DEFAULT_ITERATIONS,
) -> list[dict[str, object]]:
    """Return representative labelled group timings without enforcing rate policy."""
    if sample_count < 1 or iterations < 1:
        raise ValueError("sample_count and iterations must be positive")

    labels = _runtime_labels()
    observations: list[dict[str, object]] = []
    for topology_size in topology_sizes:
        for group_depth in group_depths:
            for winner_position in WINNER_POSITIONS:
                winner_rank = _winner_rank(group_depth, winner_position)
                machine, conditions = _build_priority_group_machine(
                    group_depth=group_depth,
                    topology_size=topology_size,
                    winner_rank=winner_rank,
                )
                expected_guard_evaluations = (
                    group_depth if winner_rank is None else winner_rank + 1
                )
                expected_success = winner_rank is not None

                def operation() -> None:
                    result = machine.trigger("priority_tick")
                    if result.success is not expected_success:
                        raise RuntimeError(
                            "priority-group observation changed result shape"
                        )

                elapsed_samples = [
                    measure_time(operation, iterations) for _ in range(sample_count)
                ]
                observed_guard_evaluations = sum(
                    condition.calls for condition in conditions
                )
                if observed_guard_evaluations != (
                    expected_guard_evaluations * iterations * sample_count
                ):
                    raise RuntimeError("priority-group observation changed guard work")
                median_elapsed = statistics.median(elapsed_samples)
                observations.append(
                    {
                        **labels,
                        "topology_size": topology_size,
                        "group_depth": group_depth,
                        "winner_position": winner_position,
                        "guard_evaluations": expected_guard_evaluations,
                        "sample_count": sample_count,
                        "iterations": iterations,
                        "operations_per_second": iterations / median_elapsed,
                    }
                )
    return observations


def _build_final_entry_operation(
    iterations: int,
) -> tuple[Callable[[], None], Callable[[], int]]:
    """Prepare one prebuilt final-entry batch outside the timed sample."""
    machines: list[tuple[StateMachine, State]] = []
    for index in range(iterations):
        source = State(f"final-source-{index}")
        destination = State(f"final-destination-{index}", final=True)
        machine = StateMachine(source, name=f"final-entry-{index}")
        machine.add_state(destination)
        machine.add_transition("finish", source, destination)
        machines.append((machine, destination))
    next_machine = 0

    def operation() -> None:
        nonlocal next_machine
        machine, destination = machines[next_machine]
        next_machine += 1
        result = machine.trigger("finish")
        if not result.success or not machine.is_terminated:
            raise RuntimeError("final-entry observation changed result shape")
        if machine.current_state is not destination:
            raise RuntimeError("final-entry observation changed destination")

    return operation, lambda: 0


def _build_self_operation(
    *, internal: bool
) -> tuple[Callable[[], None], Callable[[], int]]:
    """Prepare a repeatedly reachable internal or external self transition."""
    state = State("self")
    machine = StateMachine(state, name="internal-self" if internal else "external-self")
    machine.add_transition("tick", state, state, internal=internal)

    def operation() -> None:
        result = machine.trigger("tick")
        if not result.success or result.internal is not internal:
            raise RuntimeError("self-transition observation changed result shape")
        if machine.current_state is not state:
            raise RuntimeError("self-transition observation left its state")

    return operation, lambda: 0


def _build_expected_rejection_operation() -> tuple[Callable[[], None], Callable[[], int]]:
    """Prepare a repeated pre-commit expected-rejection eligibility attempt."""
    source = State("rejection-source")
    destination = State("rejection-destination")
    machine = StateMachine(source, name="expected-rejection")
    machine.add_state(destination)
    guard_calls = 0

    def reject() -> bool:
        nonlocal guard_calls
        guard_calls += 1
        raise TransitionRejected("benchmark.rejected")

    machine.add_transition("check", source, destination, reject)

    def operation() -> None:
        result = machine.trigger("check")
        if result.success or result.committed:
            raise RuntimeError("expected-rejection observation committed unexpectedly")
        if result.rejection_code != "benchmark.rejected":
            raise RuntimeError("expected-rejection observation changed rejection code")
        if machine.current_state is not source:
            raise RuntimeError("expected-rejection observation changed source state")

    return operation, lambda: guard_calls


def collect_semantic_observations(
    *,
    environment_label: str,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
    iterations: int = DEFAULT_ITERATIONS,
) -> list[dict[str, object]]:
    """Collect non-gating optional-semantic costs beside the singleton floor.

    The installed native singleton floor belongs to the release-evidence tool.
    This reporter only records environment-specific observations, with setup
    (including final-entry batches) completed before each timed sample.
    """
    if not isinstance(environment_label, str) or not environment_label.strip():
        raise ValueError("environment_label must be a nonempty string")
    if sample_count < 1 or iterations < 1:
        raise ValueError("sample_count and iterations must be positive")

    builders: tuple[
        tuple[str, int, Callable[[], tuple[Callable[[], None], Callable[[], int]]]],
        ...,
    ] = (
        (
            "final_entry",
            0,
            lambda: _build_final_entry_operation(iterations),
        ),
        ("internal_self", 0, lambda: _build_self_operation(internal=True)),
        ("external_self", 0, lambda: _build_self_operation(internal=False)),
        ("expected_rejection", 1, _build_expected_rejection_operation),
    )
    labels = _runtime_labels()
    observations: list[dict[str, object]] = []
    for scenario, expected_guard_work, build_operation in builders:
        elapsed_samples: list[float] = []
        for _ in range(sample_count):
            operation, guard_calls = build_operation()
            elapsed = measure_time(operation, iterations)
            if not math.isfinite(elapsed) or elapsed <= 0:
                raise RuntimeError("semantic observation elapsed time is invalid")
            if guard_calls() != expected_guard_work * iterations:
                raise RuntimeError("semantic observation changed guard work")
            elapsed_samples.append(elapsed)
        median_elapsed = statistics.median(elapsed_samples)
        operations_per_second = iterations / median_elapsed
        if not math.isfinite(operations_per_second) or operations_per_second <= 0:
            raise RuntimeError("semantic observation rate is invalid")
        observations.append(
            {
                **labels,
                "scenario": scenario,
                "environment_label": environment_label,
                "clock": "perf_counter_ns",
                "statistic": "median",
                "sample_count": sample_count,
                "iterations": iterations,
                "operation_count": sample_count * iterations,
                "guard_evaluations_per_operation": expected_guard_work,
                "operations_per_second": operations_per_second,
            }
        )
    return observations


def _parse_args() -> argparse.Namespace:
    """Parse explicit provenance controls for a descriptive benchmark run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--environment-label",
        required=True,
        type=str,
        help="Explicit label for this runtime/build environment.",
    )
    parser.add_argument(
        "--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT, metavar="COUNT"
    )
    parser.add_argument(
        "--iterations", type=int, default=DEFAULT_ITERATIONS, metavar="COUNT"
    )
    parser.add_argument(
        "--expected-core-mode",
        choices=("pure-python", "compiled-native"),
        help="Fail before timing unless the observed core loader mode matches.",
    )
    return parser.parse_args()


def main() -> None:
    """Print descriptive priority and semantic observations for the active runtime."""
    args = _parse_args()
    if not args.environment_label.strip():
        raise SystemExit("--environment-label must be nonempty")
    observed_mode = _runtime_labels()["core_mode"]
    if args.expected_core_mode is not None and observed_mode != args.expected_core_mode:
        raise SystemExit(
            "expected core mode "
            f"{args.expected_core_mode!r}, observed {observed_mode!r}"
        )
    performance_header("Fast FSM Performance Observations")
    print("Source/trigger lookup and singleton dispatch are O(1).")
    print("Finite group selection and immutable group mutation are local O(k).")
    print("Rows below are environment-labelled observations, not release thresholds.")
    for observation in collect_priority_group_observations(
        sample_count=args.sample_count, iterations=args.iterations
    ):
        print("PRIORITY_GROUP_OBSERVATION " + json.dumps(observation, sort_keys=True))
    for observation in collect_semantic_observations(
        environment_label=args.environment_label,
        sample_count=args.sample_count,
        iterations=args.iterations,
    ):
        print("SEMANTIC_OBSERVATION " + json.dumps(observation, sort_keys=True))


if __name__ == "__main__":
    main()
