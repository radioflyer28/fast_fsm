"""Strict, stdlib-only contracts for isolated FSM comparison children."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any


COMPARISON_SCHEMA_VERSION = 1
IMPLEMENTATION_IDS = frozenset(
    {
        "fast-fsm",
        "python-statemachine-2.5.0",
        "python-statemachine-3.2.1",
    }
)
REQUIRED_SCENARIO_IDS = frozenset(
    {"flat-alternating-cycle", "false-guard-no-transition"}
)
SCENARIO_IDS = (
    "flat-alternating-cycle",
    "false-guard-no-transition",
    "final-state-rejection",
)
UNSUPPORTED_REASON_CODES = frozenset({"api-unavailable", "not-comparable"})
EXPECTED_PREFLIGHTS: dict[str, dict[str, object]] = {
    "flat-alternating-cycle": {
        "initial": "idle",
        "after_first": "active",
        "after_second": "idle",
    },
    "false-guard-no-transition": {
        "guard_calls": 1,
        "state": "idle",
        "transition_callbacks": 0,
    },
}

MAX_STRING_LENGTH = 4096
MAX_COMMAND_PARTS = 32
MAX_COUNT = 10_000_000
MAX_SAMPLES = 20

_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "implementation_id",
        "requested_distribution",
        "requested_version",
        "resolved_version",
        "module_origin",
        "module_loader",
        "python_implementation",
        "python_version",
        "platform",
        "machine",
        "command",
        "observation_only",
        "scenarios",
    }
)
_SCENARIO_FIELDS = frozenset(
    {
        "scenario_id",
        "status",
        "preflight",
        "unsupported_reason",
        "warmup_operations",
        "operations",
        "samples_ns",
        "median_ns",
        "operations_per_second",
    }
)


class ComparisonContractError(RuntimeError):
    """Raised when comparison identity, semantics, or measurements contradict."""


def canonical_json(value: Mapping[str, Any]) -> str:
    """Return deterministic JSON and reject non-finite numeric values."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_STRING_LENGTH:
        raise ComparisonContractError(f"{field} is invalid")
    return value


def _require_count(value: object, field: str) -> int:
    if type(value) is not int or not 0 < value <= MAX_COUNT:
        raise ComparisonContractError(f"{field} is invalid")
    return value


def _require_finite_positive(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComparisonContractError(f"{field} is invalid")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ComparisonContractError(f"{field} is invalid")
    return numeric


def _validate_preflight(scenario_id: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ComparisonContractError(f"scenario {scenario_id} preflight is invalid")
    if scenario_id in REQUIRED_SCENARIO_IDS:
        expected = EXPECTED_PREFLIGHTS[scenario_id]
        if value != expected:
            raise ComparisonContractError(
                f"required scenario {scenario_id} preflight contradicted"
            )
    elif value:
        raise ComparisonContractError(
            f"optional scenario {scenario_id} preflight is invalid"
        )
    return value


def _validate_scenario(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _SCENARIO_FIELDS:
        raise ComparisonContractError("scenario fields are invalid")
    scenario_id = _require_string(value["scenario_id"], "scenario id")
    if scenario_id not in SCENARIO_IDS:
        raise ComparisonContractError("scenario id is unknown")
    status = value["status"]
    if status not in {"supported", "unsupported"}:
        raise ComparisonContractError(f"scenario {scenario_id} status is invalid")
    if status == "unsupported":
        if scenario_id in REQUIRED_SCENARIO_IDS:
            raise ComparisonContractError(
                f"required scenario {scenario_id} cannot be unsupported"
            )
        _validate_preflight(scenario_id, value["preflight"])
        if value["unsupported_reason"] not in UNSUPPORTED_REASON_CODES:
            raise ComparisonContractError(
                f"unsupported scenario {scenario_id} reason is invalid"
            )
        for field in (
            "warmup_operations",
            "operations",
            "samples_ns",
            "median_ns",
            "operations_per_second",
        ):
            if value[field] is not None:
                raise ComparisonContractError(
                    f"unsupported scenario {scenario_id} has measurements"
                )
        return value

    if value["unsupported_reason"] is not None:
        raise ComparisonContractError(f"supported scenario {scenario_id} has a reason")
    _validate_preflight(scenario_id, value["preflight"])
    warmup = _require_count(value["warmup_operations"], "operation count")
    operations = _require_count(value["operations"], "operation count")
    samples = value["samples_ns"]
    if not isinstance(samples, list) or not samples or len(samples) > MAX_SAMPLES:
        raise ComparisonContractError(f"scenario {scenario_id} samples are invalid")
    numeric_samples = [
        _require_finite_positive(sample, "samples") for sample in samples
    ]
    median_ns = _require_finite_positive(value["median_ns"], "median")
    rate = _require_finite_positive(
        value["operations_per_second"], "operations per second"
    )
    expected_median = float(statistics.median(numeric_samples))
    expected_rate = operations * 1_000_000_000 / expected_median
    if median_ns != expected_median or rate != expected_rate or warmup > MAX_COUNT:
        raise ComparisonContractError(
            f"scenario {scenario_id} measurement summary contradicted"
        )
    return value


def validate_child_record(value: object) -> dict[str, object]:
    """Validate one complete child record before parent comparison."""
    if not isinstance(value, dict) or set(value) != _RECORD_FIELDS:
        raise ComparisonContractError("record fields are invalid")
    if value["schema_version"] != COMPARISON_SCHEMA_VERSION:
        raise ComparisonContractError("record schema version is invalid")
    implementation_id = _require_string(value["implementation_id"], "implementation id")
    if implementation_id not in IMPLEMENTATION_IDS:
        raise ComparisonContractError("implementation id is invalid")
    distribution = _require_string(
        value["requested_distribution"], "requested distribution"
    )
    requested_version = _require_string(value["requested_version"], "requested version")
    resolved_version = _require_string(value["resolved_version"], "resolved version")
    if requested_version != resolved_version:
        raise ComparisonContractError("resolved version contradicts requested version")
    if implementation_id.startswith("python-statemachine-"):
        exact = implementation_id.removeprefix("python-statemachine-")
        if distribution != "python-statemachine" or requested_version != exact:
            raise ComparisonContractError("implementation identity is contradictory")
    elif distribution != "fast-fsm":
        raise ComparisonContractError("implementation identity is contradictory")
    origin = Path(_require_string(value["module_origin"], "module origin"))
    if not origin.is_absolute() or origin.name in {"", ".", ".."}:
        raise ComparisonContractError("module origin is implausible")
    for field in (
        "module_loader",
        "python_implementation",
        "python_version",
        "platform",
        "machine",
    ):
        _require_string(value[field], field.replace("_", " "))
    command = value["command"]
    if (
        not isinstance(command, list)
        or not command
        or len(command) > MAX_COMMAND_PARTS
        or any(
            not isinstance(part, str) or not part or len(part) > MAX_STRING_LENGTH
            for part in command
        )
    ):
        raise ComparisonContractError("command is invalid")
    if value["observation_only"] is not True:
        raise ComparisonContractError("observation marker is invalid")
    scenarios = value["scenarios"]
    if not isinstance(scenarios, list):
        raise ComparisonContractError("scenario collection is invalid")
    checked = [_validate_scenario(scenario) for scenario in scenarios]
    if [scenario["scenario_id"] for scenario in checked] != list(SCENARIO_IDS):
        raise ComparisonContractError("scenario inventory is invalid")
    canonical_json(value)
    return value


def measure_scenario(
    operation: Callable[[], None],
    *,
    warmup: int,
    operations: int,
    samples: int,
) -> dict[str, object]:
    """Collect bounded nanosecond samples for one preflighted operation."""
    warmup_count = _require_count(warmup, "operation count")
    operation_count = _require_count(operations, "operation count")
    sample_count = _require_count(samples, "sample count")
    if sample_count > MAX_SAMPLES:
        raise ComparisonContractError("sample count is invalid")
    for _ in range(warmup_count):
        operation()
    timings: list[float] = []
    for _ in range(sample_count):
        started = time.perf_counter_ns()
        for _ in range(operation_count):
            operation()
        elapsed = time.perf_counter_ns() - started
        timings.append(float(max(1, elapsed)))
    median_ns = float(statistics.median(timings))
    return {
        "warmup_operations": warmup_count,
        "operations": operation_count,
        "samples_ns": timings,
        "median_ns": median_ns,
        "operations_per_second": operation_count * 1_000_000_000 / median_ns,
    }


def supported_record(
    scenario_id: str,
    preflight: dict[str, object],
    measurement: Mapping[str, object],
) -> dict[str, object]:
    """Assemble one supported scenario using only canonical fields."""
    return {
        "scenario_id": scenario_id,
        "status": "supported",
        "preflight": preflight,
        "unsupported_reason": None,
        **measurement,
    }


def unsupported_record(
    scenario_id: str, reason: str = "api-unavailable"
) -> dict[str, object]:
    """Assemble one explicit optional unsupported scenario."""
    return {
        "scenario_id": scenario_id,
        "status": "unsupported",
        "preflight": {},
        "unsupported_reason": reason,
        "warmup_operations": None,
        "operations": None,
        "samples_ns": None,
        "median_ns": None,
        "operations_per_second": None,
    }
