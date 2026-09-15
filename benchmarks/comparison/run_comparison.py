#!/usr/bin/env python3
"""Run exact isolated FSM comparison children and assemble observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    from .common import (
        COMPARISON_SCHEMA_VERSION,
        REQUIRED_SCENARIO_IDS,
        ComparisonContractError,
        canonical_json,
        validate_child_record,
    )
except ImportError:  # Direct script execution.
    from common import (  # type: ignore[no-redef]
        COMPARISON_SCHEMA_VERSION,
        REQUIRED_SCENARIO_IDS,
        ComparisonContractError,
        canonical_json,
        validate_child_record,
    )


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPARISON_ROOT = Path(__file__).resolve().parent
MAX_CHILD_OUTPUT_BYTES = 256 * 1024
CHILD_TIMEOUT_SECONDS = 120


def _scenario(record: dict[str, object], scenario_id: str) -> dict[str, object]:
    scenarios = record["scenarios"]
    assert isinstance(scenarios, list)
    return next(
        scenario
        for scenario in scenarios
        if isinstance(scenario, dict) and scenario["scenario_id"] == scenario_id
    )


def build_child_commands(args: argparse.Namespace) -> dict[str, list[str]]:
    """Return absolute, isolated commands without importing any child library."""
    common_args = [
        "--warmup",
        str(args.warmup),
        "--operations",
        str(args.operations),
        "--samples",
        str(args.samples),
    ]
    return {
        "fast-fsm": [
            "uv",
            "run",
            "--project",
            str(REPOSITORY_ROOT),
            "python",
            str(COMPARISON_ROOT / "fast_fsm_runner.py"),
            *common_args,
        ],
        "python-statemachine-2.5.0": [
            "uv",
            "run",
            "--locked",
            "--script",
            str(COMPARISON_ROOT / "python_statemachine_2_5.py"),
            *common_args,
        ],
        "python-statemachine-3.2.1": [
            "uv",
            "run",
            "--locked",
            "--script",
            str(COMPARISON_ROOT / "python_statemachine_3_2.py"),
            *common_args,
        ],
    }


def run_child(command: list[str]) -> dict[str, object]:
    """Run one child from a neutral directory and accept one bounded JSON object."""
    if (
        not command
        or len(command) > 32
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise ComparisonContractError("child command is invalid")
    try:
        with tempfile.TemporaryDirectory(prefix="fast-fsm-comparison-") as temporary:
            completed = subprocess.run(
                command,
                cwd=temporary,
                text=True,
                capture_output=True,
                check=False,
                timeout=CHILD_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired:
        raise ComparisonContractError("child process timed out") from None
    if completed.returncode != 0:
        raise ComparisonContractError("child process failed")
    stdout = completed.stdout
    stderr = completed.stderr
    if (
        not stdout
        or len(stdout.encode("utf-8")) > MAX_CHILD_OUTPUT_BYTES
        or len(stderr.encode("utf-8")) > MAX_CHILD_OUTPUT_BYTES
    ):
        raise ComparisonContractError("child stdout is invalid")
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        raise ComparisonContractError("child stdout is invalid") from None
    return validate_child_record(payload)


def build_comparison_report(records: list[dict[str, object]]) -> dict[str, object]:
    """Validate identity/semantics before calculating descriptive ratios."""
    checked = [validate_child_record(record) for record in records]
    by_id = {str(record["implementation_id"]): record for record in checked}
    expected_ids = {
        "fast-fsm",
        "python-statemachine-2.5.0",
        "python-statemachine-3.2.1",
    }
    if set(by_id) != expected_ids or len(by_id) != len(checked):
        raise ComparisonContractError("implementation inventory is invalid")
    origins = [str(record["module_origin"]) for record in checked]
    if len(set(origins)) != len(origins):
        raise ComparisonContractError("implementations require distinct origins")

    fast = by_id["fast-fsm"]
    ratios: list[dict[str, object]] = []
    for competitor_id in (
        "python-statemachine-2.5.0",
        "python-statemachine-3.2.1",
    ):
        competitor = by_id[competitor_id]
        for scenario_id in sorted(REQUIRED_SCENARIO_IDS):
            fast_scenario = _scenario(fast, scenario_id)
            competitor_scenario = _scenario(competitor, scenario_id)
            if (
                fast_scenario["status"] != "supported"
                or competitor_scenario["status"] != "supported"
                or fast_scenario["preflight"] != competitor_scenario["preflight"]
            ):
                raise ComparisonContractError(
                    f"required scenario {scenario_id} cannot be compared"
                )
            fast_rate = float(fast_scenario["operations_per_second"])
            competitor_rate = float(competitor_scenario["operations_per_second"])
            ratios.append(
                {
                    "scenario_id": scenario_id,
                    "competitor_id": competitor_id,
                    "fast_over_competitor": fast_rate / competitor_rate,
                }
            )

    unsupported: list[dict[str, object]] = []
    for record in checked:
        implementation_id = str(record["implementation_id"])
        scenarios = record["scenarios"]
        assert isinstance(scenarios, list)
        for scenario in scenarios:
            assert isinstance(scenario, dict)
            if scenario["status"] == "unsupported":
                unsupported.append(
                    {
                        "implementation_id": implementation_id,
                        "scenario_id": scenario["scenario_id"],
                        "reason": scenario["unsupported_reason"],
                    }
                )
    report: dict[str, object] = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "observation_only": True,
        "implementations": checked,
        "ratios": ratios,
        "unsupported": unsupported,
    }
    canonical_json(report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--operations", type=int, default=1_000)
    parser.add_argument("--samples", type=int, default=5)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        commands = build_child_commands(args)
        records = [run_child(command) for command in commands.values()]
        print(canonical_json(build_comparison_report(records)))
    except ComparisonContractError as error:
        print(json.dumps({"error": str(error)[:200]}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
