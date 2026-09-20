#!/usr/bin/env python3
"""Run exact isolated FSM comparison children and assemble observations."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import BinaryIO

try:
    from .common import (
        COMPARISON_SCHEMA_VERSION,
        EXPECTED_PREFLIGHTS,
        MAX_COUNT,
        MAX_SAMPLES,
        REQUIRED_SCENARIO_IDS,
        SCENARIO_IDS,
        ComparisonContractError,
        canonical_json,
        validate_child_record,
    )
except ImportError:  # Direct script execution.
    from common import (  # type: ignore[no-redef]
        COMPARISON_SCHEMA_VERSION,
        EXPECTED_PREFLIGHTS,
        MAX_COUNT,
        MAX_SAMPLES,
        REQUIRED_SCENARIO_IDS,
        SCENARIO_IDS,
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
            "--locked",
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


def _run_bounded_process(command: list[str], cwd: str) -> tuple[int, bytes, bytes]:
    """Run one process with hard time and incremental per-stream byte limits."""
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
            creationflags=creationflags,
        )
    except (OSError, ValueError):
        raise ComparisonContractError("child process could not start") from None
    assert process.stdout is not None and process.stderr is not None
    output = {"stdout": bytearray(), "stderr": bytearray()}
    exceeded = threading.Event()
    stopped = threading.Event()

    def stop_process_tree() -> None:
        if stopped.is_set():
            return
        stopped.set()
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    timeout=1,
                )
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except (OSError, subprocess.SubprocessError):
            try:
                process.kill()
            except OSError:
                pass

    def close_stream_descriptors() -> None:
        """Wake readers without waiting on a BufferedReader lock they may hold."""
        for stream in (process.stdout, process.stderr):
            try:
                descriptor = stream.fileno()
            except (OSError, ValueError):
                continue
            try:
                os.close(descriptor)
            except OSError:
                pass

    def read_capped(stream: BinaryIO, target: bytearray) -> None:
        try:
            read_available = getattr(stream, "read1", stream.read)
            while chunk := read_available(64 * 1024):
                if len(target) + len(chunk) > MAX_CHILD_OUTPUT_BYTES:
                    exceeded.set()
                    stop_process_tree()
                    return
                target.extend(chunk)
        except (OSError, ValueError):
            return

    readers = (
        threading.Thread(
            target=read_capped,
            args=(process.stdout, output["stdout"]),
            daemon=True,
        ),
        threading.Thread(
            target=read_capped,
            args=(process.stderr, output["stderr"]),
            daemon=True,
        ),
    )
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + CHILD_TIMEOUT_SECONDS
    timed_out = False
    try:
        process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        timed_out = True
        stop_process_tree()
    finally:
        for reader in readers:
            reader.join(timeout=max(0.0, deadline - time.monotonic()))
        if any(reader.is_alive() for reader in readers):
            timed_out = True
            stop_process_tree()
            close_stream_descriptors()
            for reader in readers:
                reader.join(timeout=0.1)
        for stream, reader in zip((process.stdout, process.stderr), readers):
            # A detached descendant can retain a pipe while its reader is
            # blocked. The descriptor is already closed above; BufferedReader
            # .close() would wait for that reader's lock past our deadline.
            if reader.is_alive():
                continue
            try:
                stream.close()
            except (OSError, ValueError):
                pass
        if process.poll() is None:
            stop_process_tree()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
    if exceeded.is_set():
        raise ComparisonContractError("child stdout is invalid")
    if timed_out:
        raise ComparisonContractError("child process timed out")
    return process.returncode, bytes(output["stdout"]), bytes(output["stderr"])


def run_child(command: list[str]) -> dict[str, object]:
    """Run one child from a neutral directory and accept one bounded JSON object."""
    if (
        not command
        or len(command) > 32
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise ComparisonContractError("child command is invalid")
    with tempfile.TemporaryDirectory(prefix="fast-fsm-comparison-") as temporary:
        returncode, stdout_bytes, _stderr_bytes = _run_bounded_process(
            command, temporary
        )
    if returncode != 0:
        raise ComparisonContractError("child process failed")
    if not stdout_bytes:
        raise ComparisonContractError("child stdout is invalid")
    try:
        payload = json.loads(stdout_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ComparisonContractError("child stdout is invalid") from None
    return validate_child_record(payload)


def build_comparison_report(
    records: list[dict[str, object]],
    *,
    generated_at_utc: str | None = None,
    command: list[str] | None = None,
) -> dict[str, object]:
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

    implementation_order = (
        "fast-fsm",
        "python-statemachine-2.5.0",
        "python-statemachine-3.2.1",
    )
    scenario_comparisons: list[dict[str, object]] = []
    for scenario_id in SCENARIO_IDS:
        scenarios = {
            implementation_id: _scenario(by_id[implementation_id], scenario_id)
            for implementation_id in implementation_order
        }
        unsupported_reason = {
            implementation_id: scenario["unsupported_reason"]
            for implementation_id, scenario in scenarios.items()
            if scenario["status"] == "unsupported"
        }
        required_values: dict[str, object] | None = None
        if scenario_id in REQUIRED_SCENARIO_IDS:
            required_values = EXPECTED_PREFLIGHTS[scenario_id]
            if unsupported_reason or any(
                scenario["preflight"] != required_values
                for scenario in scenarios.values()
            ):
                raise ComparisonContractError(
                    f"required scenario {scenario_id} cannot be compared"
                )

        if unsupported_reason:
            scenario_comparisons.append(
                {
                    "scenario_id": scenario_id,
                    "status": "unsupported",
                    "unsupported_reason": unsupported_reason,
                    "required_values": required_values,
                    "medians_ns": {},
                    "operations_per_second": {},
                    "ratios": {},
                }
            )
            continue

        medians_ns = {
            implementation_id: scenario["median_ns"]
            for implementation_id, scenario in scenarios.items()
        }
        rates = {
            implementation_id: scenario["operations_per_second"]
            for implementation_id, scenario in scenarios.items()
        }
        fast_rate = float(rates["fast-fsm"])
        ratios = {
            competitor_id: fast_rate / float(rates[competitor_id])
            for competitor_id in implementation_order[1:]
        }
        scenario_comparisons.append(
            {
                "scenario_id": scenario_id,
                "status": "supported",
                "unsupported_reason": None,
                "required_values": required_values,
                "medians_ns": medians_ns,
                "operations_per_second": rates,
                "ratios": ratios,
            }
        )

    timestamp = generated_at_utc or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    report: dict[str, object] = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "observation_only": True,
        "generated_at_utc": timestamp,
        "command": command or ["fixture-comparison"],
        "implementations": [by_id[item] for item in implementation_order],
        "scenario_comparisons": scenario_comparisons,
    }
    canonical_json(report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--operations", type=int, default=1_000)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--output", type=Path)
    return parser


def _validate_cli_counts(args: argparse.Namespace) -> None:
    """Reject unbounded manual work before any child process starts."""
    for field in ("warmup", "operations"):
        value = getattr(args, field)
        if type(value) is not int or not 0 < value <= MAX_COUNT:
            raise ComparisonContractError(f"{field} count is invalid")
    if type(args.samples) is not int or not 0 < args.samples <= MAX_SAMPLES:
        raise ComparisonContractError("sample count is invalid")


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        _validate_cli_counts(args)
        commands = build_child_commands(args)
        records = [run_child(command) for command in commands.values()]
        report_command = [
            "benchmark-compare",
            "--warmup",
            str(args.warmup),
            "--operations",
            str(args.operations),
            "--samples",
            str(args.samples),
        ]
        payload = canonical_json(
            build_comparison_report(records, command=report_command)
        )
        print(payload)
        if args.output is not None:
            args.output.write_text(payload + "\n", encoding="utf-8")
    except ComparisonContractError as error:
        print(json.dumps({"error": str(error)[:200]}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
