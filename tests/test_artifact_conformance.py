"""Deterministic, payload-safe evidence from the shared artifact oracle."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import artifact_conformance


def test_tracer_lifecycle_record_is_stable_and_payload_safe() -> None:
    """The initial oracle scenario is real lifecycle behavior, not a smoke import."""
    first = artifact_conformance.collect_conformance()
    second = artifact_conformance.collect_conformance()

    assert first == second
    assert first["schema_version"] == artifact_conformance.SCHEMA_VERSION
    assert first["payload_leak_free"] is True
    assert len(first["suite_sha256"]) == 64
    assert len(first["semantic_sha256"]) == 64

    assert first["scenarios"] == [
        {
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
    ]

    rendered = artifact_conformance.canonical_json(first)
    for secret in ("caller-secret", "destination-secret", "observer-secret"):
        assert secret not in rendered


def test_parity_mismatch_reports_only_scenario_and_field_names() -> None:
    """Parity diagnostics name the contract drift without rendering record payloads."""
    expected = artifact_conformance.collect_conformance()
    actual = artifact_conformance.collect_conformance()
    actual["scenarios"][0]["stage"] = "guard"

    assert artifact_conformance.compare_conformance(expected, actual) == [
        "lifecycle.destination-enter-failure: stage"
    ]
