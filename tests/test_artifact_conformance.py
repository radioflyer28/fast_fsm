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

_OWNERSHIP_OBSERVATIONS = (
    ("ownership.sync-thread-serialization", "first_success"),
    ("ownership.sync-thread-serialization", "second_success"),
    ("ownership.sync-thread-serialization", "second_blocked_while_owned"),
    ("ownership.async-task-serialization", "owner_success"),
    ("ownership.async-task-serialization", "waiter_success"),
    ("ownership.async-task-serialization", "waiter_blocked_while_owned"),
    ("ownership.async-task-serialization", "heartbeat_ran"),
    ("ownership.cross-loop-rejection", "foreign_loop_rejected"),
    ("ownership.cross-loop-rejection", "bound_loop_preserved"),
    ("ownership.cross-loop-rejection", "foreign_guard_not_evaluated"),
    ("ownership.mutator-baseexception-release", "mutator_rejected_while_owned"),
    ("ownership.mutator-baseexception-release", "topology_unchanged"),
    ("ownership.mutator-baseexception-release", "baseexception_propagated"),
    ("ownership.mutator-baseexception-release", "mutator_admitted_after_release"),
)
_DIAGNOSTIC_DIMENSIONS = (
    ("diagnostic.work-boundary", "max_work"),
    ("diagnostic.results-boundary", "max_results"),
    ("diagnostic.dense_cells-boundary", "max_dense_cells"),
    ("diagnostic.path_expansions-boundary", "max_path_expansions"),
)


def _rehash(payload: dict[str, object]) -> None:
    """Keep mutation tests focused on contract validation, not stale digest bytes."""
    payload["semantic_sha256"] = artifact_conformance._sha256(
        {
            "schema_version": artifact_conformance.SCHEMA_VERSION,
            "suite_sha256": payload["suite_sha256"],
            "scenarios": payload["scenarios"],
        }
    )


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


@pytest.mark.parametrize(
    "needle",
    (
        "def collect_conformance(",
        "def validate_conformance(",
        "def canonical_json(",
    ),
)
def test_suite_digest_binds_all_collector_implementation_bytes(
    tmp_path: Path, needle: str
) -> None:
    """Collector, validation, and serialization mutations change suite identity."""
    source = Path(artifact_conformance.__file__)
    mutated = tmp_path / "artifact_conformance.py"
    original = source.read_text(encoding="utf-8")
    mutated.write_text(original, encoding="utf-8")
    baseline = artifact_conformance._suite_sha256(mutated)

    mutated.write_text(
        original.replace(needle, f"{needle}  # reviewed mutation", 1),
        encoding="utf-8",
    )

    assert artifact_conformance._suite_sha256(mutated) != baseline


def test_hardened_oracle_observes_each_phase_contract() -> None:
    """Every hardened behavior has a concrete, payload-safe oracle assertion."""
    records = {
        record["id"]: record
        for record in artifact_conformance.collect_conformance()["scenarios"]
    }

    graph = records["graph.guard-rejection"]
    assert graph["canonical_endpoints"] is True
    assert graph["duplicate_state_rejected"] is True
    assert graph["snapshot_immutable"] is True
    assert graph["snapshot_facts_exact"] is True
    assert graph["guard_context_observed"] is True
    assert graph["rejected_topology_unchanged"] is True

    precommit = records["lifecycle.precommit-failure-observation"]
    assert precommit["success"] is False
    assert precommit["committed"] is False
    assert precommit["stage"] == "source-exit"
    assert precommit["state"] == "source"
    assert precommit["callback_order"] == [
        "source-exit",
        "observer-one",
        "observer-two",
    ]
    assert precommit["history"] == []

    builder = records["builder-declarative.dispatch"]
    assert builder["builder_sealed"] is True
    assert builder["async_detected"] is True

    ownership = records["ownership.reentry-independent-machine"]
    assert ownership["outer_success"] is True
    assert ownership["nested_rejected"] is True
    assert ownership["independent_success"] is True

    for identifier, field in _OWNERSHIP_OBSERVATIONS:
        assert records[identifier][field] is True

    for identifier, dimension in _DIAGNOSTIC_DIMENSIONS:
        diagnostic = records[identifier]
        assert diagnostic["exact_complete"] is True
        assert diagnostic["exact_limit"] == diagnostic["exact_count"]
        assert diagnostic["one_less_limit"] == diagnostic["exact_limit"] - 1
        assert diagnostic["one_less_exhausted"] is True
        assert diagnostic["exhausted_dimension"] == dimension
        assert diagnostic["error_redacted"] is True

    equivalence = records["sync-async.equivalence"]
    for field in (
        "success",
        "committed",
        "stage",
        "state",
        "callback_order",
        "history",
    ):
        assert equivalence[f"sync_{field}"] == equivalence[f"async_{field}"]

    logging_record = records["logging.metadata-redaction"]
    assert logging_record["custom_redactor_called"] is True
    assert logging_record["custom_redactor_safe"] is True
    assert logging_record["custom_failure_safe"] is True

    output = records["output.grammar-containment"]
    assert output["mermaid_safe"] is True
    assert output["plantuml_safe"] is True
    assert output["json_safe"] is True
    assert output["redacted"] is True


@pytest.mark.parametrize(
    "identifier",
    (
        "graph.guard-rejection",
        "lifecycle.precommit-failure-observation",
        "builder-declarative.dispatch",
        "ownership.reentry-independent-machine",
        "sync-async.equivalence",
        "logging.metadata-redaction",
    ),
)
def test_each_hardened_contract_record_is_required(identifier: str) -> None:
    """Removing one contract-specific scenario makes the installed oracle invalid."""
    payload = artifact_conformance.collect_conformance()
    payload["scenarios"] = [
        record for record in payload["scenarios"] if record["id"] != identifier
    ]

    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(payload)


@pytest.mark.parametrize(("identifier", "field"), _OWNERSHIP_OBSERVATIONS)
def test_each_ownership_observation_is_immutable_and_fail_closed(
    identifier: str, field: str
) -> None:
    """Removing or falsifying any ownership proof invalidates installed evidence."""
    payload = copy.deepcopy(artifact_conformance.collect_conformance())
    records = {record["id"]: record for record in payload["scenarios"]}
    records[identifier][field] = False
    _rehash(payload)

    with pytest.raises(
        artifact_conformance.ConformanceError,
        match=rf"{identifier} contradicted {field}",
    ):
        artifact_conformance.validate_conformance(payload)


@pytest.mark.parametrize(("identifier", "dimension"), _DIAGNOSTIC_DIMENSIONS)
def test_each_diagnostic_boundary_is_immutable_and_fail_closed(
    identifier: str, dimension: str
) -> None:
    """Every limit's exact and one-less outcome is a semantic, not count-only, proof."""
    for field, replacement in (
        ("exact_complete", False),
        ("one_less_exhausted", False),
        ("exhausted_dimension", "max_wrong_dimension"),
        ("error_redacted", False),
    ):
        payload = copy.deepcopy(artifact_conformance.collect_conformance())
        records = {record["id"]: record for record in payload["scenarios"]}
        records[identifier][field] = replacement
        _rehash(payload)
        with pytest.raises(artifact_conformance.ConformanceError):
            artifact_conformance.validate_conformance(payload)

    payload = copy.deepcopy(artifact_conformance.collect_conformance())
    records = {record["id"]: record for record in payload["scenarios"]}
    records[identifier]["exact_limit"] += 1
    _rehash(payload)
    with pytest.raises(
        artifact_conformance.ConformanceError, match="invalid budget boundary"
    ):
        artifact_conformance.validate_conformance(payload)

    assert dimension == records[identifier]["exhausted_dimension"]
