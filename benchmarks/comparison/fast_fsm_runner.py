#!/usr/bin/env python3
"""Collect semantic-first Fast FSM observations for isolated comparison."""

from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import platform
import sys
from typing import Callable

import fast_fsm.core as core
from fast_fsm import FuncCondition, State, StateMachine

try:
    from .common import (
        COMPARISON_SCHEMA_VERSION,
        EXPECTED_PREFLIGHTS,
        ComparisonContractError,
        canonical_json,
        measure_scenario,
        supported_record,
        unsupported_record,
        validate_child_record,
    )
except ImportError:  # Direct script execution keeps the adjacent helper importable.
    from common import (  # type: ignore[no-redef]
        COMPARISON_SCHEMA_VERSION,
        EXPECTED_PREFLIGHTS,
        ComparisonContractError,
        canonical_json,
        measure_scenario,
        supported_record,
        unsupported_record,
        validate_child_record,
    )


def _preflight_flat_cycle() -> tuple[dict[str, object], Callable[[], None]]:
    idle = State("idle")
    active = State("active")
    machine = StateMachine(idle, name="comparison-flat-cycle")
    machine.add_state(active)
    machine.add_transition("activate", idle, active)
    machine.add_transition("deactivate", active, idle)
    initial = machine.current_state_name
    first = machine.trigger("activate")
    after_first = machine.current_state_name
    second = machine.trigger("deactivate")
    after_second = machine.current_state_name
    if not first.success or not second.success:
        raise ComparisonContractError("flat-alternating-cycle preflight failed")

    def operation() -> None:
        if not machine.trigger("activate").success:
            raise ComparisonContractError("flat-alternating-cycle operation failed")
        if not machine.trigger("deactivate").success:
            raise ComparisonContractError("flat-alternating-cycle operation failed")

    return {
        "initial": initial,
        "after_first": after_first,
        "after_second": after_second,
    }, operation


def _preflight_false_guard() -> tuple[dict[str, object], Callable[[], None]]:
    idle = State("idle")
    active = State("active")
    machine = StateMachine(idle, name="comparison-false-guard")
    machine.add_state(active)
    guard_calls = 0
    transition_callbacks = 0

    def deny(**_: object) -> bool:
        nonlocal guard_calls
        guard_calls += 1
        return False

    def after(*_: object, **__: object) -> None:
        nonlocal transition_callbacks
        transition_callbacks += 1

    machine.add_transition("advance", idle, active, FuncCondition(deny))
    machine.after_transition(after)
    result = machine.trigger("advance")
    if result.success:
        raise ComparisonContractError("false-guard-no-transition preflight failed")
    preflight = {
        "guard_calls": guard_calls,
        "state": machine.current_state_name,
        "transition_callbacks": transition_callbacks,
    }

    def operation() -> None:
        if machine.trigger("advance").success or machine.current_state is not idle:
            raise ComparisonContractError("false-guard-no-transition operation failed")

    return preflight, operation


def build_record(args: argparse.Namespace) -> dict[str, object]:
    """Build one record only after both required semantic preflights pass."""
    flat_preflight, flat_operation = _preflight_flat_cycle()
    false_preflight, false_operation = _preflight_false_guard()
    for scenario_id, preflight in (
        ("flat-alternating-cycle", flat_preflight),
        ("false-guard-no-transition", false_preflight),
    ):
        if preflight != EXPECTED_PREFLIGHTS[scenario_id]:
            raise ComparisonContractError(
                f"required scenario {scenario_id} preflight contradicted"
            )

    scenarios = [
        supported_record(
            "flat-alternating-cycle",
            flat_preflight,
            measure_scenario(
                flat_operation,
                warmup=args.warmup,
                operations=args.operations,
                samples=args.samples,
            ),
        ),
        supported_record(
            "false-guard-no-transition",
            false_preflight,
            measure_scenario(
                false_operation,
                warmup=args.warmup,
                operations=args.operations,
                samples=args.samples,
            ),
        ),
        unsupported_record("final-state-rejection"),
    ]
    origin = Path(core.__file__ or "").resolve()
    record: dict[str, object] = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "implementation_id": "fast-fsm",
        "requested_distribution": "fast-fsm",
        "requested_version": metadata.version("fast-fsm"),
        "resolved_version": metadata.version("fast-fsm"),
        "module_origin": str(origin),
        "module_loader": type(core.__loader__).__name__,
        "python_implementation": sys.implementation.name,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "command": [str(Path(__file__).resolve()), *sys.argv[1:]],
        "observation_only": True,
        "scenarios": scenarios,
    }
    return validate_child_record(record)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--operations", type=int, default=1_000)
    parser.add_argument("--samples", type=int, default=5)
    return parser


def main() -> None:
    try:
        print(canonical_json(build_record(_parser().parse_args())))
    except (ComparisonContractError, ValueError) as error:
        message = str(error)[:200]
        print(json.dumps({"error": message}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
