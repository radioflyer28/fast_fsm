# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "python-statemachine==3.2.1",
# ]
# ///
"""Isolated python-statemachine 3.2.1 comparison child."""

from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import platform
import sys
from typing import Callable

import statemachine as statemachine_module
from statemachine import State, StateMachine
from statemachine.exceptions import TransitionNotAllowed

from common import (
    COMPARISON_SCHEMA_VERSION,
    EXPECTED_PREFLIGHTS,
    ComparisonContractError,
    canonical_json,
    measure_scenario,
    supported_record,
    unsupported_record,
    validate_child_record,
)


REQUESTED_VERSION = "3.2.1"
IMPLEMENTATION_ID = "python-statemachine-3.2.1"


def _preflight_flat_cycle() -> tuple[dict[str, object], Callable[[], None]]:
    class AlternatingMachine(StateMachine):
        idle = State(initial=True)
        active = State()
        toggle = idle.to(active) | active.to(idle)

    machine = AlternatingMachine()
    initial = machine.current_state.id
    machine.toggle()
    after_first = machine.current_state.id
    machine.toggle()
    after_second = machine.current_state.id

    def operation() -> None:
        machine.toggle()
        machine.toggle()
        if machine.current_state.id != "idle":
            raise ComparisonContractError("flat-alternating-cycle operation failed")

    return {
        "initial": initial,
        "after_first": after_first,
        "after_second": after_second,
    }, operation


def _preflight_false_guard() -> tuple[dict[str, object], Callable[[], None]]:
    class GuardedMachine(StateMachine):
        idle = State(initial=True)
        active = State()
        advance = idle.to(active, cond="deny")
        reset = active.to(idle)

        def __init__(self) -> None:
            self.guard_calls = 0
            self.transition_callbacks = 0
            super().__init__()

        def deny(self) -> bool:
            self.guard_calls += 1
            return False

        def on_enter_active(self) -> None:
            self.transition_callbacks += 1

    machine = GuardedMachine()
    try:
        machine.advance()
    except TransitionNotAllowed:
        pass
    else:
        raise ComparisonContractError("false-guard-no-transition preflight failed")
    preflight = {
        "guard_calls": machine.guard_calls,
        "state": machine.current_state.id,
        "transition_callbacks": machine.transition_callbacks,
    }

    def operation() -> None:
        try:
            machine.advance()
        except TransitionNotAllowed:
            pass
        else:
            raise ComparisonContractError("false-guard-no-transition operation failed")
        if machine.current_state.id != "idle":
            raise ComparisonContractError("false-guard-no-transition operation failed")

    return preflight, operation


def build_record(args: argparse.Namespace) -> dict[str, object]:
    resolved_version = metadata.version("python-statemachine")
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

    record: dict[str, object] = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "implementation_id": IMPLEMENTATION_ID,
        "requested_distribution": "python-statemachine",
        "requested_version": REQUESTED_VERSION,
        "resolved_version": resolved_version,
        "module_origin": str(Path(statemachine_module.__file__ or "").resolve()),
        "module_loader": type(statemachine_module.__loader__).__name__,
        "python_implementation": sys.implementation.name,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "command": [str(Path(__file__).resolve()), *sys.argv[1:]],
        "observation_only": True,
        "scenarios": [
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
        ],
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
        print(json.dumps({"error": str(error)[:200]}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
