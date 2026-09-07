#!/usr/bin/env python3
"""Environment-labelled observations for Fast FSM priority candidate groups.

This reporter is intentionally descriptive. The deterministic benchmark tests
enforce the O(1) source/trigger lookup and local O(k) group-work contract;
these timing rows show representative runtime observations only.
"""

from __future__ import annotations

import importlib.machinery
import json
from pathlib import Path
import platform
import statistics
import time
from collections.abc import Callable

import fast_fsm.core as core
from fast_fsm import State, StateMachine
from fast_fsm.conditions import Condition


TOPOLOGY_SIZES = (4, 64, 512)
GROUP_DEPTHS = (2, 8, 32)
WINNER_POSITIONS = ("first", "middle", "last", "exhausted")
DEFAULT_SAMPLE_COUNT = 5
DEFAULT_ITERATIONS = 1_000


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
        "platform": platform.platform(),
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


def main() -> None:
    """Print descriptive priority-group observations for the active runtime."""
    performance_header("Priority Group Performance Observations")
    print("Source/trigger lookup and singleton dispatch are O(1).")
    print("Finite group selection and immutable group mutation are local O(k).")
    print("Rows below are environment-labelled observations, not release thresholds.")
    for observation in collect_priority_group_observations():
        print("PRIORITY_GROUP_OBSERVATION " + json.dumps(observation, sort_keys=True))


if __name__ == "__main__":
    main()
