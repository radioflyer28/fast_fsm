"""Offline contract tests for isolated competitor comparison evidence."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Any

import pytest

BENCHMARK_ROOT = Path(__file__).parents[1] / "benchmarks"
sys.path.insert(0, str(BENCHMARK_ROOT))

from comparison import common  # noqa: E402
from comparison import fast_fsm_runner  # noqa: E402


def supported_scenario(
    scenario_id: str,
    preflight: dict[str, object],
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "status": "supported",
        "preflight": preflight,
        "unsupported_reason": None,
        "warmup_operations": 1,
        "operations": 2,
        "samples_ns": [100.0, 120.0, 110.0],
        "median_ns": 110.0,
        "operations_per_second": 2_000_000_000 / 110.0,
    }


def unsupported_scenario(scenario_id: str) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "status": "unsupported",
        "preflight": {},
        "unsupported_reason": "api-unavailable",
        "warmup_operations": None,
        "operations": None,
        "samples_ns": None,
        "median_ns": None,
        "operations_per_second": None,
    }


def fixture_record(
    implementation_id: str = "python-statemachine-2.5.0",
) -> dict[str, object]:
    if implementation_id == "fast-fsm":
        distribution = "fast-fsm"
        version = "0.4.0"
        origin = "/tmp/fast_fsm/core.py"
    else:
        distribution = "python-statemachine"
        version = implementation_id.rsplit("-", 1)[1]
        origin = f"/tmp/{implementation_id}/statemachine/__init__.py"
    return {
        "schema_version": common.COMPARISON_SCHEMA_VERSION,
        "implementation_id": implementation_id,
        "requested_distribution": distribution,
        "requested_version": version,
        "resolved_version": version,
        "module_origin": origin,
        "module_loader": "SourceFileLoader",
        "python_implementation": "cpython",
        "python_version": "3.12.10",
        "platform": "Darwin",
        "machine": "arm64",
        "command": ["fixture-child"],
        "observation_only": True,
        "scenarios": [
            supported_scenario(
                "flat-alternating-cycle",
                {"initial": "idle", "after_first": "active", "after_second": "idle"},
            ),
            supported_scenario(
                "false-guard-no-transition",
                {"guard_calls": 1, "state": "idle", "transition_callbacks": 0},
            ),
            unsupported_scenario("final-state-rejection"),
        ],
    }


def test_schema_accepts_exact_supported_and_unsupported_cells() -> None:
    record = fixture_record()
    assert common.validate_child_record(record) == record


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda record: record.update(extra=True), "record fields"),
        (
            lambda record: record.update(resolved_version="3.2.1"),
            "resolved version",
        ),
        (
            lambda record: record.update(module_origin="relative.py"),
            "module origin",
        ),
        (
            lambda record: record["scenarios"][0].update(operations=True),
            "operation count",
        ),
        (
            lambda record: record["scenarios"][0].update(samples_ns=[math.nan]),
            "samples",
        ),
        (
            lambda record: record["scenarios"][0].update(status="unsupported"),
            "required scenario",
        ),
        (
            lambda record: record["scenarios"][2].update(
                samples_ns=[1.0], median_ns=1.0
            ),
            "unsupported scenario",
        ),
    ],
)
def test_schema_rejects_malformed_or_contradictory_records(
    mutate: Any,
    match: str,
) -> None:
    record = fixture_record()
    mutate(record)
    with pytest.raises(common.ComparisonContractError, match=match):
        common.validate_child_record(record)


def test_canonical_json_is_deterministic_and_finite() -> None:
    assert common.canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    with pytest.raises(ValueError):
        common.canonical_json({"sample": math.inf})


def test_measure_scenario_validates_counts_and_returns_finite_samples() -> None:
    calls = 0

    def operation() -> None:
        nonlocal calls
        calls += 1

    measured = common.measure_scenario(operation, warmup=1, operations=2, samples=3)
    assert calls == 7
    assert len(measured["samples_ns"]) == 3
    assert measured["median_ns"] > 0
    assert measured["operations_per_second"] > 0
    with pytest.raises(common.ComparisonContractError, match="operation count"):
        common.measure_scenario(operation, warmup=True, operations=2, samples=3)


def test_fast_fsm_preflight_contradiction_prevents_sampling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sampled: list[bool] = []
    monkeypatch.setattr(
        fast_fsm_runner,
        "_preflight_false_guard",
        lambda: (
            {"guard_calls": 2, "state": "idle", "transition_callbacks": 0},
            lambda: None,
        ),
    )
    monkeypatch.setattr(
        fast_fsm_runner,
        "measure_scenario",
        lambda *args, **kwargs: sampled.append(True),
    )

    with pytest.raises(common.ComparisonContractError, match="preflight"):
        fast_fsm_runner.build_record(
            argparse.Namespace(warmup=1, operations=2, samples=3)
        )
    assert sampled == []


def test_fast_fsm_record_proves_false_guard_before_measurement() -> None:
    record = fast_fsm_runner.build_record(
        argparse.Namespace(warmup=1, operations=2, samples=3)
    )
    checked = common.validate_child_record(record)
    false_guard = next(
        scenario
        for scenario in checked["scenarios"]
        if scenario["scenario_id"] == "false-guard-no-transition"
    )
    assert false_guard["preflight"] == {
        "guard_calls": 1,
        "state": "idle",
        "transition_callbacks": 0,
    }
    assert Path(str(checked["module_origin"])).is_absolute()
