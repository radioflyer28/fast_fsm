"""Deterministic, payload-safe evidence from the shared artifact oracle."""

from __future__ import annotations

from pathlib import Path
import sys
import copy
import json
import os
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import artifact_conformance  # noqa: E402


REQUIRED_FAMILIES = {
    "graph-guard",
    "lifecycle-result-history",
    "sync-async",
    "builder-declarative",
    "ownership-cancellation",
    "diagnostic-budget",
    "output-containment",
    "logging-redaction",
}


def test_tracer_lifecycle_record_is_stable_and_payload_safe() -> None:
    """The initial oracle scenario is real lifecycle behavior, not a smoke import."""
    first = artifact_conformance.collect_conformance()
    second = artifact_conformance.collect_conformance()

    assert first == second
    assert first["schema_version"] == artifact_conformance.SCHEMA_VERSION
    assert first["payload_leak_free"] is True
    assert len(first["suite_sha256"]) == 64
    assert len(first["semantic_sha256"]) == 64

    assert next(
        record
        for record in first["scenarios"]
        if record["id"] == "lifecycle.destination-enter-failure"
    ) == {
        "id": "lifecycle.destination-enter-failure",
        "family": "lifecycle-result-history",
        "success": False,
        "committed": True,
        "stage": "destination-enter",
        "state": "destination",
        "callback_order": [
            "source-exit",
            "destination-enter",
            "observer-one",
            "observer-two",
        ],
        "history": [["source", "advance", "destination"]],
        "redacted": True,
    }

    rendered = artifact_conformance.canonical_json(first)
    for secret in ("caller-secret", "destination-secret", "observer-secret"):
        assert secret not in rendered


def test_parity_mismatch_reports_only_scenario_and_field_names() -> None:
    """Parity diagnostics name the contract drift without rendering record payloads."""
    expected = artifact_conformance.collect_conformance()
    actual = artifact_conformance.collect_conformance()
    next(
        record
        for record in actual["scenarios"]
        if record["id"] == "lifecycle.destination-enter-failure"
    )["stage"] = "guard"

    assert artifact_conformance.compare_conformance(expected, actual) == [
        "lifecycle.destination-enter-failure: stage"
    ]


def test_required_hardened_inventory_is_complete_and_stably_ordered() -> None:
    """The one oracle includes every Phase 16–19 hardened behavior family."""
    payload = artifact_conformance.collect_conformance()

    assert set(artifact_conformance.REQUIRED_FAMILIES) == REQUIRED_FAMILIES
    assert {record["family"] for record in payload["scenarios"]} == REQUIRED_FAMILIES
    assert [record["id"] for record in payload["scenarios"]] == sorted(
        record["id"] for record in payload["scenarios"]
    )


def test_inventory_and_schema_drift_fail_closed() -> None:
    """Missing, duplicate, extra, unsorted, and payload-bearing records are rejected."""
    payload = artifact_conformance.collect_conformance()

    missing = copy.deepcopy(payload)
    missing["scenarios"].pop()
    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(missing)

    duplicate = copy.deepcopy(payload)
    duplicate["scenarios"].append(copy.deepcopy(duplicate["scenarios"][0]))
    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(duplicate)

    extra = copy.deepcopy(payload)
    extra["scenarios"][0]["unallowlisted"] = "value"
    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(extra)

    unsorted = copy.deepcopy(payload)
    unsorted["scenarios"].reverse()
    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(unsorted)

    payload_bearing = copy.deepcopy(payload)
    payload_bearing["scenarios"][0]["state"] = "caller-secret"
    payload_bearing["semantic_sha256"] = "0" * 64
    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(payload_bearing)


def test_hash_seed_does_not_change_canonical_semantics() -> None:
    """Independent processes cannot reorder the shared oracle through hash randomization."""
    outputs: list[dict[str, object]] = []
    for seed in ("1", "777"):
        environment = dict(os.environ)
        environment["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            [sys.executable, str(Path(artifact_conformance.__file__)), "--json"],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        outputs.append(json.loads(completed.stdout))
    assert outputs[0] == outputs[1]
