"""Non-destructive maintainer checks for source and wheel release evidence."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from email.message import Message
from email.parser import Parser
import gc
import hashlib
import importlib
from importlib import machinery, metadata, util
import json
import math
import os
from packaging.utils import (
    InvalidWheelFilename,
    canonicalize_name,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence, cast
from urllib.parse import unquote, urlparse
from zipfile import ZipFile
from xml.etree import ElementTree


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "fast_fsm"
CORE_MODULE_NAME = f"{PACKAGE_NAME}.core"
REQUIRED_UV_VERSION = "0.12.6"
MANIFEST_SCHEMA_VERSION = 2

_RELEASE_VERSION = "0.3.0"
_SUPPORTED_CPYTHON_MINORS = ("3.10", "3.11", "3.12", "3.13", "3.14")
_DIRECT_NATIVE_TARGETS = (
    ("linux", "x86_64"),
    ("linux", "aarch64"),
    ("windows", "amd64"),
    ("macos", "x86_64"),
    ("macos", "arm64"),
)

_RELEASE_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
_RELEASE_HISTORY_FACTS = (
    "defective 0.2.2 package metadata",
    "remains a shipped release",
    "existing v0.2.3 tag and published artifacts are immutable and unchanged",
    "v0.3.0",
)

REGISTERED_SLOTS_EXCEPTIONS: Mapping[str, str] = {
    "fast_fsm.conditions.CompiledFuncCondition": (
        "The interpreted public subclass boundary delegates evaluation to a "
        "compiled core helper."
    ),
    "fast_fsm.core.TransitionError": (
        "@mypyc_attr(native_class=False) preserves normal Python exception behavior."
    ),
    "fast_fsm._diagnostics.DiagnosticBudgetExceeded": (
        "Public bounded-diagnostic failures carry a scalar DiagnosticStatus."
    ),
}


class EvidenceError(RuntimeError):
    """Raised when local release evidence is incomplete or contradictory."""

    def __init__(
        self, message: str, *, diagnostics: tuple[str, str] | None = None
    ) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


@dataclass(frozen=True, order=True)
class MatrixCell:
    """One immutable required artifact/runtime evidence cell."""

    identifier: str
    cpython_minor: str
    os: str
    machine: str
    asserted_mode: str
    sdist_parent: str | None = None
    requires_parity: bool = True
    requires_origin: bool = True
    requires_performance: bool = False


@dataclass(frozen=True)
class MatrixProfile:
    """A complete expected-evidence view derived from the release contract."""

    profile: str
    cells: tuple[MatrixCell, ...]
    authorizes_release: bool


def _canonical_release_cells() -> tuple[MatrixCell, ...]:
    """Return the one authoritative hosted release contract in stable order."""
    cells: list[MatrixCell] = []
    for minor in _SUPPORTED_CPYTHON_MINORS:
        cells.append(
            MatrixCell(
                identifier=f"pure-wheel-cp{minor.replace('.', '')}",
                cpython_minor=minor,
                os="universal",
                machine="universal",
                asserted_mode="pure",
            )
        )
        for os_name, machine in _DIRECT_NATIVE_TARGETS:
            cells.append(
                MatrixCell(
                    identifier=(
                        f"compiled-wheel-cp{minor.replace('.', '')}-{os_name}-{machine}"
                    ),
                    cpython_minor=minor,
                    os=os_name,
                    machine=machine,
                    asserted_mode="compiled",
                    requires_performance=True,
                )
            )
        for machine in ("x86_64", "arm64"):
            cells.append(
                MatrixCell(
                    identifier=(
                        f"compiled-wheel-cp{minor.replace('.', '')}-macos-universal2-{machine}"
                    ),
                    cpython_minor=minor,
                    os="macos",
                    machine=machine,
                    asserted_mode="compiled",
                    requires_performance=True,
                )
            )

    cells.append(
        MatrixCell(
            identifier="sdist-archive",
            cpython_minor="archive",
            os="archive",
            machine="archive",
            asserted_mode="sdist",
            requires_parity=False,
            requires_origin=False,
        )
    )
    for minor in _SUPPORTED_CPYTHON_MINORS:
        for os_name, machine in _DIRECT_NATIVE_TARGETS:
            for mode in ("pure", "compiled"):
                cells.append(
                    MatrixCell(
                        identifier=(
                            f"sdist-{mode}-cp{minor.replace('.', '')}-{os_name}-{machine}"
                        ),
                        cpython_minor=minor,
                        os=os_name,
                        machine=machine,
                        asserted_mode=mode,
                        sdist_parent="sdist-archive",
                        requires_performance=mode == "compiled",
                    )
                )
    return tuple(sorted(cells))


def _normalize_matrix_runtime(runtime: Mapping[str, object]) -> tuple[str, str, str]:
    """Normalize the current interpreter/platform target without guessing values."""
    implementation = runtime.get("implementation")
    minor = runtime.get("python_minor")
    os_name = runtime.get("platform")
    machine = runtime.get("machine")
    aliases = {
        "darwin": "macos",
        "macos": "macos",
        "linux": "linux",
        "win32": "windows",
        "windows": "windows",
        "amd64": "amd64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "aarch64",
    }
    if implementation != "cpython" or not isinstance(minor, str):
        raise EvidenceError("Matrix runtime requires a CPython minor version.")
    if minor not in _SUPPORTED_CPYTHON_MINORS:
        raise EvidenceError(f"Matrix runtime CPython {minor!r} is unsupported.")
    if not isinstance(os_name, str) or not isinstance(machine, str):
        raise EvidenceError("Matrix runtime platform and machine must be strings.")
    normalized_os = aliases.get(os_name.casefold())
    normalized_machine = aliases.get(machine.casefold())
    if normalized_os not in {"linux", "windows", "macos"} or normalized_machine not in {
        "x86_64",
        "amd64",
        "arm64",
        "aarch64",
    }:
        raise EvidenceError("Matrix runtime platform or machine is unsupported.")
    return minor, normalized_os, normalized_machine


def expected_matrix(profile: str, runtime: Mapping[str, object]) -> MatrixProfile:
    """Return the release contract or its deterministic local proof projection."""
    release_cells = _canonical_release_cells()
    if profile == "release":
        return MatrixProfile("release", release_cells, True)
    if profile != "local":
        raise EvidenceError("Matrix profile must be 'release' or 'local'.")

    minor, os_name, machine = _normalize_matrix_runtime(runtime)
    compatible_machines = {machine}
    if machine == "arm64":
        compatible_machines.add("aarch64")
    elif machine == "aarch64":
        compatible_machines.add("arm64")
    elif machine == "amd64":
        compatible_machines.add("x86_64")
    elif machine == "x86_64":
        compatible_machines.add("amd64")
    local_cells = tuple(
        cell
        for cell in release_cells
        if cell.identifier == "sdist-archive"
        or (
            cell.cpython_minor == minor
            and (
                (cell.os == "universal" and cell.machine == "universal")
                or (cell.os == os_name and cell.machine in compatible_machines)
            )
        )
    )
    if not local_cells:
        raise EvidenceError("Matrix runtime has no local release proof projection.")
    return MatrixProfile("local", local_cells, False)


def build_release_authorization(aggregate: Mapping[str, object]) -> dict[str, str]:
    """Construct an authorization marker only for a complete hosted profile."""
    if aggregate.get("profile") != "release":
        raise EvidenceError("Only the complete release profile can authorize release.")
    if aggregate.get("authorizes_release") is not True:
        raise EvidenceError("Release profile aggregate is not authorizing.")
    return {"profile": "release", "authorization": "release-evidence-complete"}


_MATRIX_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_id",
        "matrix",
        "artifact",
        "runtime",
        "conformance",
        "provenance",
        "origin_verified",
        "performance",
        "parent_sdist",
    }
)


def _matrix_cell_payload(cell: MatrixCell) -> dict[str, object]:
    """Serialize an expected cell without exposing mutable implementation state."""
    return {
        "identifier": cell.identifier,
        "cpython_minor": cell.cpython_minor,
        "os": cell.os,
        "machine": cell.machine,
        "asserted_mode": cell.asserted_mode,
        "sdist_parent": cell.sdist_parent,
        "requires_parity": cell.requires_parity,
        "requires_origin": cell.requires_origin,
        "requires_performance": cell.requires_performance,
    }


def _exact_mapping(
    value: object, *, fields: frozenset[str], field: str
) -> Mapping[str, object]:
    """Require an untrusted evidence object to have no omitted or extra fields."""
    if not isinstance(value, Mapping) or set(value) != fields:
        raise EvidenceError(f"matrix evidence {field} has an invalid field set.")
    return cast(Mapping[str, object], value)


def _matrix_filename(value: object, *, field: str) -> str:
    """Normalize one archive filename while rejecting path-bearing evidence."""
    if not isinstance(value, str) or not value or len(value) > 255:
        raise EvidenceError(f"matrix evidence {field} filename is malformed.")
    if "/" in value or "\\" in value or Path(value).name != value:
        raise EvidenceError(f"matrix evidence {field} filename is malformed.")
    return value.casefold()


def _matrix_artifact_group(cell: MatrixCell) -> str:
    """Return the only cell families allowed to share one artifact digest."""
    if cell.identifier.startswith("pure-wheel-"):
        return "pure-wheel"
    if "universal2" in cell.identifier:
        return f"universal2-cp{cell.cpython_minor}"
    return cell.identifier


def _matrix_runtime_matches(cell: MatrixCell, runtime: Mapping[str, object]) -> None:
    """Bind installed runtime facts to the expected cell before parity is accepted."""
    fields = frozenset(
        {
            "python_implementation",
            "python_version",
            "platform",
            "machine",
            "distribution_version",
            "package_version",
        }
    )
    checked = _exact_mapping(runtime, fields=fields, field="runtime")
    implementation = checked["python_implementation"]
    python_version = checked["python_version"]
    platform_name = checked["platform"]
    machine = checked["machine"]
    if (
        implementation != "cpython"
        or not isinstance(python_version, str)
        or not isinstance(platform_name, str)
        or not isinstance(machine, str)
    ):
        raise EvidenceError("matrix evidence runtime is malformed.")
    pieces = python_version.split(".")
    if len(pieces) != 3 or not all(piece.isdigit() for piece in pieces):
        raise EvidenceError("matrix evidence runtime.python_version is malformed.")
    if f"{int(pieces[0])}.{int(pieces[1])}" != cell.cpython_minor:
        raise EvidenceError(
            "matrix evidence runtime.python_version contradicts matrix."
        )
    platform_aliases = {
        "darwin": "macos",
        "macos": "macos",
        "linux": "linux",
        "windows": "windows",
        "win32": "windows",
    }
    machine_aliases = {
        "x86_64": "x86_64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "aarch64",
    }
    normalized_platform = platform_aliases.get(platform_name.casefold())
    normalized_machine = machine_aliases.get(machine.casefold())
    compatible_machines = {cell.machine}
    if cell.machine == "arm64":
        compatible_machines.add("aarch64")
    elif cell.machine == "aarch64":
        compatible_machines.add("arm64")
    elif cell.machine == "amd64":
        compatible_machines.add("x86_64")
    elif cell.machine == "x86_64":
        compatible_machines.add("amd64")
    if cell.os != "universal" and (
        normalized_platform != cell.os or normalized_machine not in compatible_machines
    ):
        raise EvidenceError("matrix evidence runtime architecture contradicts matrix.")
    for field in ("distribution_version", "package_version"):
        if checked[field] != _RELEASE_VERSION:
            raise EvidenceError(
                f"matrix evidence runtime.{field} is not {_RELEASE_VERSION}."
            )


def _matrix_conformance_matches(
    conformance: object, *, suite_sha256: str | None
) -> tuple[dict[str, Any], str]:
    """Validate semantic records and retain only a declared suite identity."""
    if not isinstance(conformance, Mapping):
        raise EvidenceError("matrix evidence conformance is malformed.")
    expected_suite = suite_sha256 or _expected_conformance_suite_sha256()
    if conformance.get("suite_sha256") != expected_suite:
        raise EvidenceError("matrix evidence conformance.suite_sha256 is invalid.")
    try:
        record = _validate_child_conformance(
            conformance, expected_suite_sha256=expected_suite
        )
    except EvidenceError as error:
        raise EvidenceError("matrix evidence conformance is invalid.") from error
    actual_suite = record["suite_sha256"]
    if not isinstance(actual_suite, str):  # defensive; child validation guarantees it.
        raise EvidenceError("matrix evidence conformance is invalid.")
    return record, actual_suite


def _matrix_scenario_differences(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any]
) -> list[str]:
    """Return bounded scenario/field deltas without rendering evidence payloads."""
    baseline_scenarios = {
        str(item["id"]): item
        for item in cast(list[Mapping[str, Any]], baseline["scenarios"])
    }
    candidate_scenarios = {
        str(item["id"]): item
        for item in cast(list[Mapping[str, Any]], candidate["scenarios"])
    }
    differences: list[str] = []
    for identifier in sorted(set(baseline_scenarios) | set(candidate_scenarios)):
        expected = baseline_scenarios.get(identifier)
        observed = candidate_scenarios.get(identifier)
        if expected is None or observed is None:
            differences.append(f"{identifier}: scenario")
        else:
            changed = [
                field
                for field in sorted(set(expected) | set(observed))
                if field != "id" and expected.get(field) != observed.get(field)
            ]
            if changed:
                differences.append(f"{identifier}: {', '.join(changed[:4])}")
        if len(differences) == 8:
            break
    return differences


def _validate_matrix_record(
    record: object,
    *,
    expected_cells: Mapping[str, MatrixCell],
    record_ids: set[str],
    artifact_groups: dict[tuple[str, str], str],
    suite_sha256: str | None,
) -> tuple[MatrixCell, dict[str, Any], str]:
    """Validate one untrusted record and return its expected cell and semantics."""
    checked = _exact_mapping(record, fields=_MATRIX_RECORD_FIELDS, field="record")
    if checked["schema_version"] != 1:
        raise EvidenceError("matrix evidence record schema_version is unsupported.")
    record_id = checked["record_id"]
    if not isinstance(record_id, str) or not record_id or len(record_id) > 255:
        raise EvidenceError("matrix evidence record_id is malformed.")
    if record_id in record_ids:
        raise EvidenceError("matrix evidence has duplicate record_id values.")
    record_ids.add(record_id)

    matrix_fields = frozenset(
        {
            "cell",
            "cpython_minor",
            "os",
            "machine",
            "asserted_mode",
            "sdist_parent",
            "artifact_filename",
            "artifact_sha256",
        }
    )
    matrix = _exact_mapping(checked["matrix"], fields=matrix_fields, field="matrix")
    identifier = matrix["cell"]
    if not isinstance(identifier, str) or identifier not in expected_cells:
        raise EvidenceError("matrix evidence has an unexpected matrix cell.")
    cell = expected_cells[identifier]
    for field, expected in (
        ("cpython_minor", cell.cpython_minor),
        ("os", cell.os),
        ("machine", cell.machine),
        ("asserted_mode", cell.asserted_mode),
        ("sdist_parent", cell.sdist_parent),
    ):
        if matrix[field] != expected:
            raise EvidenceError(f"matrix evidence matrix.{field} contradicts cell.")
    matrix_filename = _matrix_filename(matrix["artifact_filename"], field="matrix")
    matrix_sha = matrix["artifact_sha256"]
    if not _is_sha256(matrix_sha):
        raise EvidenceError("matrix evidence matrix.artifact_sha256 is malformed.")

    artifact_fields = frozenset(
        {"filename", "sha256", "classified_mode", "build_intent"}
    )
    artifact = _exact_mapping(
        checked["artifact"], fields=artifact_fields, field="artifact"
    )
    artifact_filename = _matrix_filename(artifact["filename"], field="artifact")
    artifact_sha = artifact["sha256"]
    if not _is_sha256(artifact_sha):
        raise EvidenceError("matrix evidence artifact.sha256 is malformed.")
    if matrix_filename != artifact_filename or matrix_sha != artifact_sha:
        raise EvidenceError("matrix evidence artifact digest is detached from matrix.")
    if (
        artifact["classified_mode"] != cell.asserted_mode
        or artifact["build_intent"] != cell.asserted_mode
    ):
        raise EvidenceError("matrix evidence artifact mode contradicts matrix.")
    artifact_key = (artifact_filename, cast(str, artifact_sha))
    artifact_group = _matrix_artifact_group(cell)
    existing_group = artifact_groups.setdefault(artifact_key, artifact_group)
    if existing_group != artifact_group:
        raise EvidenceError(
            "matrix evidence reuses an artifact across incompatible cells."
        )

    provenance_fields = frozenset({"release_version", "commit", "tag"})
    provenance = _exact_mapping(
        checked["provenance"], fields=provenance_fields, field="provenance"
    )
    version = provenance["release_version"]
    commit = provenance["commit"]
    tag = provenance["tag"]
    if version != _RELEASE_VERSION:
        raise EvidenceError("matrix evidence provenance.release_version is invalid.")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceError("matrix evidence provenance.commit is malformed.")
    if tag not in {"unreleased", f"v{_RELEASE_VERSION}"}:
        raise EvidenceError("matrix evidence provenance.tag is invalid.")

    if cell.identifier == "sdist-archive":
        if (
            checked["runtime"] is not None
            or checked["conformance"] is not None
            or checked["origin_verified"] is not False
            or checked["performance"] is not None
            or checked["parent_sdist"] is not None
        ):
            raise EvidenceError(
                "matrix evidence sdist archive has runtime-only fields."
            )
        return cell, {}, cast(str, commit)

    if not isinstance(checked["runtime"], Mapping):
        raise EvidenceError("matrix evidence runtime is required.")
    _matrix_runtime_matches(cell, cast(Mapping[str, object], checked["runtime"]))
    if checked["origin_verified"] is not cell.requires_origin:
        raise EvidenceError("matrix evidence origin proof contradicts matrix.")
    if cell.requires_performance:
        performance = _exact_mapping(
            checked["performance"], fields=frozenset({"status"}), field="performance"
        )
        if performance["status"] != "passed":
            raise EvidenceError("matrix evidence installed performance is invalid.")
    elif checked["performance"] is not None:
        raise EvidenceError("matrix evidence has unexpected installed performance.")

    if cell.sdist_parent is None:
        if checked["parent_sdist"] is not None:
            raise EvidenceError("matrix evidence has unexpected sdist lineage.")
    else:
        parent = _exact_mapping(
            checked["parent_sdist"],
            fields=frozenset({"filename", "sha256"}),
            field="parent_sdist",
        )
        if _matrix_filename(
            parent["filename"], field="parent_sdist"
        ) != "fast_fsm-0.3.0.tar.gz" or not _is_sha256(parent["sha256"]):
            raise EvidenceError("matrix evidence sdist lineage is malformed.")

    conformance, _suite = _matrix_conformance_matches(
        checked["conformance"], suite_sha256=suite_sha256
    )
    return cell, conformance, cast(str, commit)


def aggregate_matrix_records(
    records: Sequence[object], *, profile: str, runtime: Mapping[str, object]
) -> dict[str, Any]:
    """Reconcile a complete exact evidence profile into deterministic aggregate JSON."""
    if len(records) > 256:
        raise EvidenceError("matrix evidence has too many records.")
    expected = expected_matrix(profile, runtime)
    expected_cells = {cell.identifier: cell for cell in expected.cells}
    actual_cells: dict[str, MatrixCell] = {}
    accepted_records: list[dict[str, Any]] = []
    record_ids: set[str] = set()
    artifact_groups: dict[tuple[str, str], str] = {}
    baseline_conformance: dict[str, Any] | None = None
    suite_sha256: str | None = None
    commits: set[str] = set()
    tags: set[object] = set()

    for record in records:
        cell, conformance, commit = _validate_matrix_record(
            record,
            expected_cells=expected_cells,
            record_ids=record_ids,
            artifact_groups=artifact_groups,
            suite_sha256=suite_sha256,
        )
        if cell.identifier in actual_cells:
            raise EvidenceError("matrix evidence has duplicate matrix cells.")
        actual_cells[cell.identifier] = cell
        checked = cast(Mapping[str, Any], record)
        provenance = cast(Mapping[str, Any], checked["provenance"])
        commits.add(commit)
        tags.add(provenance["tag"])
        if conformance:
            record_suite = conformance["suite_sha256"]
            if not isinstance(record_suite, str):
                raise EvidenceError("matrix evidence conformance is invalid.")
            if suite_sha256 is None:
                suite_sha256 = record_suite
            elif suite_sha256 != record_suite:
                raise EvidenceError("matrix evidence has mixed suite_sha256 values.")
            if baseline_conformance is None:
                baseline_conformance = conformance
            else:
                differences = _matrix_scenario_differences(
                    baseline_conformance, conformance
                )
                if differences:
                    raise EvidenceError(
                        "matrix evidence semantic parity differs: "
                        + "; ".join(differences)
                    )
        accepted_records.append(json.loads(serialize_manifest(checked)))

    missing = sorted(set(expected_cells) - set(actual_cells))
    unexpected = sorted(set(actual_cells) - set(expected_cells))
    if missing or unexpected:
        parts: list[str] = []
        if missing:
            parts.append("missing " + ", ".join(missing[:8]))
        if unexpected:
            parts.append("unexpected " + ", ".join(unexpected[:8]))
        raise EvidenceError("matrix evidence exact set mismatch: " + "; ".join(parts))
    if len(commits) != 1:
        raise EvidenceError("matrix evidence has mixed provenance.commit values.")
    if len(tags) != 1:
        raise EvidenceError("matrix evidence has mixed provenance.tag values.")
    if suite_sha256 is None or baseline_conformance is None:
        raise EvidenceError("matrix evidence is missing installed conformance.")

    archive = next(
        record
        for record in accepted_records
        if cast(Mapping[str, Any], record["matrix"])["cell"] == "sdist-archive"
    )
    archive_artifact = cast(Mapping[str, Any], archive["artifact"])
    for record in accepted_records:
        matrix = cast(Mapping[str, Any], record["matrix"])
        if matrix["sdist_parent"] is None:
            continue
        parent = cast(Mapping[str, Any], record["parent_sdist"])
        if (
            parent["filename"] != archive_artifact["filename"]
            or parent["sha256"] != archive_artifact["sha256"]
        ):
            raise EvidenceError(
                "matrix evidence sdist lineage is detached from archive."
            )

    accepted_records.sort(
        key=lambda item: str(cast(Mapping[str, Any], item["matrix"])["cell"])
    )
    commit = next(iter(commits))
    tag = next(iter(tags))
    return {
        "schema_version": 2,
        "profile": expected.profile,
        "scope": "hosted-release-authorizing"
        if expected.authorizes_release
        else "local-non-authorizing",
        "authorizes_release": expected.authorizes_release,
        "expected_matrix": [_matrix_cell_payload(cell) for cell in expected.cells],
        "artifact_records": accepted_records,
        "release_identity": {
            "package": PACKAGE_NAME,
            "distribution_version": _RELEASE_VERSION,
            "commit": commit,
            "tag": tag,
            "suite_sha256": suite_sha256,
        },
        "historical_evidence": [],
        "installed_performance": [
            {
                "cell": cast(Mapping[str, Any], record["matrix"])["cell"],
                "status": "passed",
            }
            for record in accepted_records
            if record["performance"] is not None
        ],
    }


def read_matrix_record(path: Path) -> dict[str, Any]:
    """Read one uploaded evidence record with strict JSON and bounded resources."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise EvidenceError("matrix evidence could not be read.") from error
    if len(raw.encode("utf-8")) > _MAX_CHILD_OUTPUT_BYTES:
        raise EvidenceError("matrix evidence exceeds the size limit.")
    try:
        record = _strict_json_object(raw, field="matrix evidence")
        _validate_json_bounds(record)
    except EvidenceError as error:
        raise EvidenceError("matrix evidence is malformed.") from error
    return record


def render_aggregate_summary(aggregate: Mapping[str, object]) -> str:
    """Render concise stable text solely from an already validated aggregate."""
    profile = aggregate.get("profile")
    scope = aggregate.get("scope")
    records = aggregate.get("artifact_records")
    identity = aggregate.get("release_identity")
    if (
        not isinstance(profile, str)
        or not isinstance(scope, str)
        or not isinstance(records, list)
        or not isinstance(identity, Mapping)
    ):
        raise EvidenceError("matrix aggregate summary input is malformed.")
    version = identity.get("distribution_version")
    commit = identity.get("commit")
    if not isinstance(version, str) or not isinstance(commit, str):
        raise EvidenceError("matrix aggregate summary identity is malformed.")
    return "\n".join(
        (
            f"Release evidence profile: {profile}",
            f"Scope: {scope}",
            f"Artifacts verified: {len(records)}",
            f"Version: {version}",
            f"Commit: {commit}",
            "",
        )
    )


def _current_matrix_runtime() -> dict[str, object]:
    """Collect the runtime selector used only for the local matrix projection."""
    return {
        "implementation": sys.implementation.name,
        "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        "platform": platform.system(),
        "machine": platform.machine(),
    }


_HISTORICAL_EVIDENCE_SCHEMA_VERSION = 1
_HISTORICAL_BLOCK_START = "<!-- fast-fsm-historical-evidence:start -->"
_HISTORICAL_BLOCK_END = "<!-- fast-fsm-historical-evidence:end -->"
_HISTORICAL_CATEGORICAL_FIELDS = (
    "phase",
    "source_path",
    "command",
    "build_mode",
    "threshold_outcome",
    "measurement_outcome",
    "environment",
    "original_evidence_commit",
)
_HISTORICAL_RECORDED_FIELDS = frozenset({"status", "value", "citation"})
_HISTORICAL_UNAVAILABLE_FIELDS = frozenset({"status", "reason", "searched_sources"})
_RETROSPECTIVE_RERUN_FIELDS = frozenset(
    {"execution_commit", "command", "environment", "executed_at", "observations"}
)
_RETROSPECTIVE_ENVIRONMENT_FIELDS = frozenset(
    {"interpreter", "os", "architecture", "build_mode"}
)


def _historical_block(text: str, *, relative_path: str) -> tuple[dict[str, Any], str]:
    """Return one strict categorical block and its pre-block source narrative."""
    start = text.find(_HISTORICAL_BLOCK_START)
    end = text.find(_HISTORICAL_BLOCK_END, start + len(_HISTORICAL_BLOCK_START))
    if start < 0 or end < 0 or text.find(_HISTORICAL_BLOCK_START, start + 1) >= 0:
        raise EvidenceError(
            f"Historical evidence {relative_path} requires exactly one categorical block."
        )
    encoded = text[start + len(_HISTORICAL_BLOCK_START) : end].strip()
    matched = re.fullmatch(r"```json\s*(.*?)\s*```", encoded, flags=re.DOTALL)
    if matched is None:
        raise EvidenceError(
            f"Historical evidence {relative_path} categorical block is malformed."
        )
    try:
        record = _strict_json_object(
            matched.group(1), field=f"historical evidence {relative_path}"
        )
        _validate_json_bounds(record)
    except EvidenceError as error:
        raise EvidenceError(
            f"Historical evidence {relative_path} categorical block is malformed."
        ) from error
    return record, text[:start]


def _historical_recorded_value(
    value: object, *, phase: str, field: str, original_text: str
) -> None:
    """Require the original material, never the new block, to support precision."""
    if field == "phase":
        if value == phase:
            return
    elif field == "source_path":
        if value == HISTORICAL_EVIDENCE_PATHS[int(phase) - 16]:
            return
    elif isinstance(value, str) and value and value in original_text:
        return
    raise EvidenceError(
        f"Phase {phase} field {field} contains an unsupported recorded value."
    )


def _validate_historical_field(
    value: object, *, phase: str, field: str, original_text: str
) -> dict[str, Any]:
    """Validate one closed recorded/unavailable historical fact shape."""
    prefix = f"Phase {phase} field {field}"
    if not isinstance(value, Mapping):
        raise EvidenceError(f"{prefix} must declare a recorded or unavailable status.")
    status = value.get("status")
    if status == "recorded":
        if set(value) != _HISTORICAL_RECORDED_FIELDS:
            raise EvidenceError(f"{prefix} recorded provenance is malformed.")
        citation = value.get("citation")
        if not isinstance(citation, str) or not citation.strip():
            raise EvidenceError(f"{prefix} recorded provenance has no citation.")
        _historical_recorded_value(
            value.get("value"), phase=phase, field=field, original_text=original_text
        )
    elif status == "unavailable":
        if set(value) != _HISTORICAL_UNAVAILABLE_FIELDS:
            raise EvidenceError(f"{prefix} unavailable provenance is malformed.")
        reason = value.get("reason")
        searched_sources = value.get("searched_sources")
        if (
            not isinstance(reason, str)
            or not reason.strip()
            or not isinstance(searched_sources, list)
            or not searched_sources
            or not all(
                isinstance(item, str) and item.strip() for item in searched_sources
            )
        ):
            raise EvidenceError(f"{prefix} unavailable provenance is incomplete.")
    else:
        raise EvidenceError(f"{prefix} must declare a recorded or unavailable status.")
    return dict(value)


def _validate_retrospective_rerun(value: object, *, phase: str) -> dict[str, Any]:
    """Validate an optional later observation without letting it rewrite history."""
    if not isinstance(value, Mapping) or set(value) != _RETROSPECTIVE_RERUN_FIELDS:
        raise EvidenceError(f"Phase {phase} retrospective_rerun is incomplete.")
    execution_commit = value.get("execution_commit")
    command = value.get("command")
    environment = value.get("environment")
    executed_at = value.get("executed_at")
    observations = value.get("observations")
    if (
        not isinstance(execution_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", execution_commit) is None
        or not isinstance(command, str)
        or not command.strip()
        or not isinstance(environment, Mapping)
        or set(environment) != _RETROSPECTIVE_ENVIRONMENT_FIELDS
        or not all(
            isinstance(item, str) and item.strip() for item in environment.values()
        )
        or not isinstance(executed_at, str)
        or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", executed_at) is None
        or not isinstance(observations, Mapping)
        or not observations
    ):
        raise EvidenceError(f"Phase {phase} retrospective_rerun is incomplete.")
    return dict(value)


def historical_evidence(*, repository_root: Path | None = None) -> dict[str, Any]:
    """Generate the exact non-gating Phase 16–19 provenance inventory."""
    root = (repository_root or REPOSITORY_ROOT).resolve()
    entries: list[dict[str, Any]] = []
    observed_phases: set[str] = set()
    for expected_phase, relative_path in zip(
        ("16", "17", "18", "19"), HISTORICAL_EVIDENCE_PATHS
    ):
        path = root / relative_path
        try:
            content = path.read_bytes()
        except OSError as error:
            raise EvidenceError(
                f"Historical release evidence is unavailable: {relative_path}."
            ) from error
        if not content or len(content) > _MAX_CHILD_OUTPUT_BYTES:
            raise EvidenceError(
                f"Historical release evidence violates size limits: {relative_path}."
            )
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise EvidenceError(
                f"Historical release evidence is not UTF-8: {relative_path}."
            ) from error
        record, original_text = _historical_block(text, relative_path=relative_path)
        allowed_fields = {"schema_version", "kind", "fields", "retrospective_rerun"}
        if set(record) - allowed_fields:
            raise EvidenceError(
                f"Historical evidence {relative_path} has extra fields."
            )
        if (
            record.get("schema_version") != _HISTORICAL_EVIDENCE_SCHEMA_VERSION
            or record.get("kind") != "historical_phase_performance"
            or not isinstance(record.get("fields"), Mapping)
            or set(cast(Mapping[str, object], record["fields"]))
            != set(_HISTORICAL_CATEGORICAL_FIELDS)
        ):
            raise EvidenceError(
                f"Historical evidence {relative_path} has an invalid schema."
            )
        fields = {
            field: _validate_historical_field(
                cast(Mapping[str, object], record["fields"])[field],
                phase=expected_phase,
                field=field,
                original_text=original_text,
            )
            for field in _HISTORICAL_CATEGORICAL_FIELDS
        }
        if fields["phase"].get("value") != expected_phase:
            raise EvidenceError(
                f"Historical evidence {relative_path} phase contradicts the allowlist."
            )
        if fields["source_path"].get("value") != relative_path:
            raise EvidenceError(
                f"Historical evidence {relative_path} path contradicts the allowlist."
            )
        if expected_phase in observed_phases:
            raise EvidenceError(
                f"Historical evidence duplicates Phase {expected_phase}."
            )
        observed_phases.add(expected_phase)
        entry: dict[str, Any] = {
            "phase": expected_phase,
            "source_path": relative_path,
            "source_sha256": hashlib.sha256(content).hexdigest(),
            "fields": fields,
        }
        if "retrospective_rerun" in record:
            entry["retrospective_rerun"] = _validate_retrospective_rerun(
                record["retrospective_rerun"], phase=expected_phase
            )
        entries.append(entry)
    if observed_phases != {"16", "17", "18", "19"}:
        raise EvidenceError("Historical evidence allowlist is incomplete.")
    return {
        "schema_version": _HISTORICAL_EVIDENCE_SCHEMA_VERSION,
        "scope": "historical-non-gating",
        "entries": entries,
    }


def _historical_evidence() -> list[dict[str, Any]]:
    """Embed generated historical facts without allowing them to satisfy release gates."""
    return cast(list[dict[str, Any]], historical_evidence()["entries"])


def _single_text_match(text: str, pattern: re.Pattern[str], *, field: str) -> str:
    """Extract exactly one non-empty static identity value from trusted source text."""
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise EvidenceError(f"release identity {field} is missing or ambiguous.")
    value = matches[0].strip()
    if not value or value.casefold() == "unknown":
        raise EvidenceError(f"release identity {field} is blank or unknown.")
    return value


def _static_docs_identity(path: Path) -> dict[str, str]:
    """Read literal Sphinx version assignments without importing configuration code."""
    try:
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as error:
        raise EvidenceError("release identity docs.conf is unreadable.") from error
    values: dict[str, list[str]] = {"version": [], "release": []}
    for statement in module.body:
        if not isinstance(statement, ast.Assign) or not isinstance(
            statement.value, ast.Constant
        ):
            continue
        if not isinstance(statement.value.value, str):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id in values:
                values[target.id].append(statement.value.value)
    result: dict[str, str] = {}
    for field, candidates in values.items():
        if len(candidates) != 1 or not candidates[0] or candidates[0] == "unknown":
            raise EvidenceError(
                f"release identity docs.{field} is missing or ambiguous."
            )
        result[field] = candidates[0]
    return result


def _strict_identity_json(path: Path) -> Mapping[str, object]:
    """Read one static JSON identity source with duplicate-key rejection."""
    try:
        raw = path.read_text(encoding="utf-8")
        payload = _strict_json_object(raw, field="release identity")
    except (OSError, EvidenceError) as error:
        raise EvidenceError(
            "release identity evidence is unreadable or malformed."
        ) from error
    return payload


def _validate_identity_mapping(
    value: Mapping[str, object], *, field: str, expected_fields: frozenset[str]
) -> Mapping[str, object]:
    """Require exact identity fields so blank additions cannot hide stale values."""
    if set(value) != expected_fields:
        raise EvidenceError(f"release identity {field} is missing or ambiguous.")
    for key, item in value.items():
        if not isinstance(item, str) or not item or item.casefold() == "unknown":
            raise EvidenceError(f"release identity {field}.{key} is blank or unknown.")
    return value


def _peeled_release_tag_commit(tag_ref: str, *, repository_root: Path) -> str:
    """Read an existing lightweight or annotated tag commit without mutating Git."""
    if tag_ref != f"v{_RELEASE_VERSION}":
        raise EvidenceError("release identity tag ref is invalid.")
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "rev-parse",
            "--verify",
            f"{tag_ref}^{{commit}}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    commit = completed.stdout.strip()
    if completed.returncode or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceError("release identity tag could not be peeled to a commit.")
    return commit


def _checked_out_commit(*, repository_root: Path) -> str:
    """Read the current commit for identity comparison without changing Git state."""
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    commit = completed.stdout.strip()
    if completed.returncode or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceError("release identity checkout commit is unavailable.")
    return commit


def validate_release_identity(
    *,
    repository_root: Path,
    installed_identity: Mapping[str, object],
    aggregate_identity: Mapping[str, object],
    checked_out_commit: str,
    tag_ref: str | None = None,
) -> dict[str, str]:
    """Validate static v0.3.0 identity, with optional non-mutating tag equality."""
    root = repository_root.resolve()
    try:
        pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
    except OSError as error:
        raise EvidenceError("release identity static source is unreadable.") from error

    project_version = _single_text_match(
        pyproject_text,
        re.compile(r'^version\s*=\s*"([^"]+)"\s*$', re.MULTILINE),
        field="pyproject.version",
    )
    docs_identity = _static_docs_identity(root / "docs" / "conf.py")
    baseline = _strict_identity_json(root / "evidence" / "release-baseline.json")
    evidence_identity = baseline.get("release_identity")
    if baseline.get("schema_version") != 2 or not isinstance(
        evidence_identity, Mapping
    ):
        raise EvidenceError("release identity evidence.schema_version is invalid.")
    evidence_checked = _validate_identity_mapping(
        cast(Mapping[str, object], evidence_identity),
        field="evidence.release_identity",
        expected_fields=frozenset({"package", "distribution_version"}),
    )
    installed_checked = _validate_identity_mapping(
        installed_identity,
        field="installed",
        expected_fields=frozenset({"distribution_version", "package_version"}),
    )
    aggregate_checked = _validate_identity_mapping(
        aggregate_identity,
        field="aggregate",
        expected_fields=frozenset(
            {"package", "distribution_version", "commit", "tag", "suite_sha256"}
        ),
    )
    if not re.fullmatch(r"[0-9a-f]{40}", checked_out_commit):
        raise EvidenceError("release identity checked_out_commit is malformed.")
    expected_values = (
        ("pyproject.version", project_version),
        ("docs.version", docs_identity["version"]),
        ("docs.release", docs_identity["release"]),
        ("evidence.release_identity.package", evidence_checked["package"]),
        (
            "evidence.release_identity.distribution_version",
            evidence_checked["distribution_version"],
        ),
        ("installed.distribution_version", installed_checked["distribution_version"]),
        ("installed.package_version", installed_checked["package_version"]),
        ("aggregate.package", aggregate_checked["package"]),
        ("aggregate.distribution_version", aggregate_checked["distribution_version"]),
    )
    for field, value in expected_values:
        if value not in {_RELEASE_VERSION, "0.3", PACKAGE_NAME}:
            raise EvidenceError(f"release identity {field} is not {_RELEASE_VERSION}.")
    if docs_identity["version"] != "0.3" or any(
        value != _RELEASE_VERSION
        for field, value in expected_values
        if field
        not in {
            "docs.version",
            "evidence.release_identity.package",
            "aggregate.package",
        }
    ):
        raise EvidenceError("release identity static values are contradictory.")
    if aggregate_checked["commit"] != checked_out_commit:
        raise EvidenceError("release identity aggregate.commit differs from checkout.")
    suite_sha256 = aggregate_checked["suite_sha256"]
    if not _is_sha256(suite_sha256):
        raise EvidenceError("release identity aggregate.suite_sha256 is malformed.")
    changelog_matches = re.findall(
        rf"^## \[{re.escape(_RELEASE_VERSION)}\] — (UNRELEASED|\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        flags=re.MULTILINE,
    )
    if len(changelog_matches) != 1:
        raise EvidenceError(
            "release identity changelog section is missing or ambiguous."
        )
    required_claims = (
        "v0.3.0",
        "installed-artifact",
        "SHA-256 binds exact bytes",
        "not publisher authenticity",
    )
    normalized_readme = re.sub(r"\s+", " ", readme)
    if any(claim not in normalized_readme for claim in required_claims):
        raise EvidenceError("release identity README durable claims are incomplete.")

    if tag_ref is None:
        if (
            aggregate_checked["tag"] != "unreleased"
            or changelog_matches[0] != "UNRELEASED"
        ):
            raise EvidenceError(
                "release identity static mode requires unreleased tag state."
            )
        tag_status = "not-required"
        changelog_status = "unreleased"
    else:
        if aggregate_checked["tag"] != tag_ref:
            raise EvidenceError(
                "release identity aggregate.tag differs from requested tag."
            )
        if changelog_matches[0] == "UNRELEASED":
            raise EvidenceError(
                "release identity tag mode requires a dated changelog section."
            )
        peeled_commit = _peeled_release_tag_commit(tag_ref, repository_root=root)
        if (
            peeled_commit != checked_out_commit
            or peeled_commit != aggregate_checked["commit"]
        ):
            raise EvidenceError(
                "release identity peeled tag commit differs from checkout."
            )
        tag_status = "verified"
        changelog_status = "dated"
    return {
        "version": _RELEASE_VERSION,
        "commit": checked_out_commit,
        "tag_status": tag_status,
        "changelog_status": changelog_status,
    }


_INSTALLED_ARTIFACT_SCHEMA_VERSION = 1
_SDIST_ARCHIVE_SCHEMA_VERSION = 1
_MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
_MAX_SDIST_MEMBERS = 512
_MAX_SDIST_MEMBER_BYTES = 32 * 1024 * 1024
_MAX_SDIST_TOTAL_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
_MAX_CHILD_OUTPUT_BYTES = 1024 * 1024
_MAX_CHILD_STRING_LENGTH = 4096
_MAX_CHILD_NESTING = 12
_MAX_CHILD_COLLECTION_LENGTH = 128
_MAX_SAFE_JSON_INTEGER = (1 << 53) - 1
_FORBIDDEN_CONFORMANCE_FIELDS = frozenset(
    {"args", "kwargs", "exception", "error", "repr", "path", "timing", "duration"}
)
_FORBIDDEN_CONFORMANCE_TOKENS = (
    "caller-secret",
    "destination-secret",
    "observer-secret",
)
_SDIST_BUILD_REQUIREMENTS = (
    "setuptools==80.9.0",
    "wheel==0.45.1",
    "mypy[mypyc]==1.17.1",
)
_SDIST_REQUIRED_ROOT_FILES = (
    "pyproject.toml",
    "setup.py",
    "MANIFEST.in",
    "tools/__init__.py",
    "tools/build_modes.py",
    "tools/artifact_conformance.py",
)
HISTORICAL_EVIDENCE_PATHS = (
    ".planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md",
    ".planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md",
    ".planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md",
    ".planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md",
)


@dataclass(frozen=True)
class ClassDeclaration:
    """A top-level class declaration discovered by the static slots inventory."""

    qualified_name: str
    source_path: str
    line: int
    base_references: tuple[str, ...]
    has_own_slots: bool
    slots_are_literal: bool
    declares_instance_dict: bool


def _native_suffixes() -> tuple[str, ...]:
    """Return normalized import-extension suffixes with portable fallbacks."""
    suffixes = {suffix.lower() for suffix in machinery.EXTENSION_SUFFIXES}
    suffixes.update({".so", ".pyd"})
    return tuple(sorted(suffixes, key=lambda suffix: (-len(suffix), suffix)))


def _is_native_member(name: str) -> bool:
    """Return whether a path/member name ends with a native-extension suffix."""
    normalized = name.lower()
    return any(normalized.endswith(suffix) for suffix in _native_suffixes())


def _native_core_members(member_names: Iterable[str]) -> tuple[str, ...]:
    """Return native archive members that can satisfy the core compilation seam."""
    core_prefix = f"{PACKAGE_NAME}/core"
    return tuple(
        sorted(
            name
            for name in member_names
            if name.startswith(core_prefix) and _is_native_member(name)
        )
    )


def find_native_core_shadows(package_root: Path) -> list[Path]:
    """Find native siblings that would outrank ``core.py`` during import."""
    if not package_root.is_dir():
        raise EvidenceError(f"Package directory does not exist: {package_root}")
    return sorted(
        (
            candidate.resolve()
            for candidate in package_root.iterdir()
            if candidate.is_file()
            and candidate.name.startswith("core")
            and _is_native_member(candidate.name)
        ),
        key=lambda path: path.as_posix(),
    )


def _normalized_relative_path(path: Path, root: Path) -> str:
    """Return an evidence-safe path relative to a trusted repository root."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise EvidenceError(
            f"Expected {path} to remain inside the inspected source tree {root}."
        ) from error


def verify_source(source_root: Path | None = None) -> dict[str, str]:
    """Verify that ``fast_fsm.core`` resolves to clean Python source.

    Native siblings are checked before importing the package, so this function
    cannot accidentally certify a native module that shadowed ``core.py``.
    It deliberately performs no cleanup or mutation.
    """
    resolved_source_root = (source_root or REPOSITORY_ROOT / "src").resolve()
    package_root = resolved_source_root / PACKAGE_NAME
    shadows = find_native_core_shadows(package_root)
    if shadows:
        rendered_paths = "\n".join(f"  - {path}" for path in shadows)
        raise EvidenceError(
            "Native core shadow(s) found before importing fast_fsm.core:\n"
            f"{rendered_paths}\n"
            "Remove or relocate these generated artifacts explicitly, then rerun "
            "verify-source. This command never deletes developer files."
        )

    source_root_text = str(resolved_source_root)
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)
    importlib.invalidate_caches()
    core_module = importlib.import_module(CORE_MODULE_NAME)
    origin_text = getattr(core_module, "__file__", None)
    if not origin_text:
        raise EvidenceError(f"{CORE_MODULE_NAME} did not expose a module origin.")
    origin = Path(origin_text).resolve()
    if origin.suffix != ".py":
        raise EvidenceError(
            f"Expected a pure Python {CORE_MODULE_NAME} origin ending in '.py', "
            f"got {origin}."
        )

    return {
        "core_origin": _normalized_relative_path(origin, resolved_source_root.parent),
        "distribution_version": metadata.version("fast-fsm"),
    }


def _run_git_history_command(arguments: Sequence[str], *, repository_root: Path) -> str:
    """Read historical Git evidence with argument-array subprocess safety."""
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        rendered = " ".join(arguments)
        raise EvidenceError(
            f"Release-history Git command failed ({completed.returncode}): {rendered}\n"
            f"{completed.stderr.strip()}"
        )
    return completed.stdout


def _require_release_history_facts(text: str, *, artifact_name: str) -> None:
    """Require canonical immutable-history facts in a mutable correction artifact."""
    normalized = re.sub(r"\s+", " ", text.casefold())
    missing = [fact for fact in _RELEASE_HISTORY_FACTS if fact not in normalized]
    if missing:
        rendered = "\n".join(f"  - {fact}" for fact in missing)
        raise EvidenceError(
            f"{artifact_name} is missing required immutable-history facts:\n{rendered}"
        )


def _require_dated_release_section(changelog: str, version: str) -> None:
    """Require a dated Keep-a-Changelog section for a shipped release."""
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\] — \d{{4}}-\d{{2}}-\d{{2}}$",
        flags=re.MULTILINE,
    )
    if not pattern.search(changelog):
        raise EvidenceError(
            f"CHANGELOG.md is missing dated {version} section; expected "
            f"'## [{version}] — YYYY-MM-DD'."
        )


def _tag_pyproject_version(tag: str, *, repository_root: Path) -> str:
    """Read the immutable tagged package version without changing Git state."""
    pyproject = _run_git_history_command(
        ["show", f"{tag}:pyproject.toml"], repository_root=repository_root
    )
    version_match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject, re.MULTILINE)
    if not version_match:
        raise EvidenceError(f"{tag}:pyproject.toml does not declare [project] version.")
    return version_match.group(1)


def verify_history(
    *, tag: str, correction_path: Path, repository_root: Path | None = None
) -> dict[str, str]:
    """Audit the immutable v0.2.3 metadata mismatch and additive correction.

    This command only reads Git objects and repository text. It deliberately
    refuses to retag, rewrite artifacts, or infer correction facts from mutable
    prose that does not state the complete immutable-history policy.
    """
    if not _RELEASE_TAG_PATTERN.fullmatch(tag):
        raise EvidenceError(f"Expected a version tag such as 'v0.2.3', got {tag!r}.")

    root = (repository_root or REPOSITORY_ROOT).resolve()
    resolved_correction = correction_path.resolve()
    correction_relative = _normalized_relative_path(resolved_correction, root)
    try:
        correction = resolved_correction.read_text(encoding="utf-8")
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError as error:
        raise EvidenceError(
            f"Could not read release-history artifact: {error}"
        ) from error

    _require_dated_release_section(changelog, "0.2.2")
    _require_dated_release_section(changelog, tag.removeprefix("v"))
    _require_release_history_facts(correction, artifact_name=correction_relative)
    _require_release_history_facts(changelog, artifact_name="CHANGELOG.md")

    tag_object = _run_git_history_command(
        ["rev-parse", "--verify", f"{tag}^{{}}"], repository_root=root
    ).strip()
    tagged_version = _tag_pyproject_version(tag, repository_root=root)
    if tagged_version != "0.2.2":
        raise EvidenceError(
            f"Expected {tag}:pyproject.toml to declare defective 0.2.2 metadata, "
            f"observed {tagged_version!r}."
        )

    return {
        "tag": tag,
        "tag_target": tag_object,
        "tag_pyproject_version": tagged_version,
        "correction_path": correction_relative,
    }


def _wheel_filename_identity(wheel_path: Path) -> tuple[str, Version, tuple[str, ...]]:
    """Parse normalized distribution, version, and tags from a wheel filename."""
    if wheel_path.suffix.lower() != ".whl":
        raise EvidenceError(f"Expected a .whl archive, got {wheel_path.name!r}.")
    try:
        distribution, version, _build_tag, tags = parse_wheel_filename(wheel_path.name)
    except (InvalidWheelFilename, InvalidVersion) as error:
        raise EvidenceError(f"Invalid wheel filename: {wheel_path.name!r}.") from error
    return str(distribution), version, tuple(sorted(str(tag) for tag in tags))


def _archive_dist_info_directory(archive: ZipFile) -> str:
    """Return the one top-level ``.dist-info`` directory in an archive."""
    directories = sorted(
        {
            name.split("/", 1)[0]
            for name in archive.namelist()
            if "/" in name and name.split("/", 1)[0].endswith(".dist-info")
        }
    )
    if len(directories) != 1:
        raise EvidenceError(
            f"Expected exactly one .dist-info directory, found {directories!r}."
        )
    return directories[0]


def _archive_metadata(archive: ZipFile, dist_info_directory: str, filename: str) -> str:
    """Read one required metadata file from the verified dist-info directory."""
    target = f"{dist_info_directory}/{filename}"
    matches = [name for name in archive.namelist() if name == target]
    if len(matches) != 1:
        raise EvidenceError(f"Expected exactly one {target} file, found {matches!r}.")
    return archive.read(matches[0]).decode("utf-8")


def _dist_info_identity(directory: str) -> tuple[str, Version]:
    """Parse normalized identity from a wheel's ``.dist-info`` directory."""
    if not directory.endswith(".dist-info"):
        raise EvidenceError(f"Invalid dist-info directory: {directory!r}.")
    stem = directory.removesuffix(".dist-info")
    try:
        distribution, version = stem.rsplit("-", 1)
        return canonicalize_name(distribution), Version(version)
    except (ValueError, InvalidVersion) as error:
        raise EvidenceError(f"Invalid dist-info directory: {directory!r}.") from error


def _metadata_identity(headers: Message, wheel_name: str) -> tuple[str, Version]:
    """Parse normalized package identity from one METADATA header block."""
    package_name = headers.get("Name")
    package_version = headers.get("Version")
    if not package_name:
        raise EvidenceError(f"Wheel METADATA has no Name header: {wheel_name}")
    if not package_version:
        raise EvidenceError(f"Wheel METADATA has no Version header: {wheel_name}")
    try:
        return canonicalize_name(package_name), Version(package_version)
    except InvalidVersion as error:
        raise EvidenceError(
            f"Wheel METADATA has an invalid Version header: {wheel_name}"
        ) from error


def inspect_wheel(
    wheel_path: Path,
    *,
    expected_package: str = PACKAGE_NAME,
    expected_version: str | None = None,
) -> dict[str, Any]:
    """Inspect one wheel and reject contradictory release identity evidence."""
    resolved_wheel = wheel_path.resolve()
    if not resolved_wheel.is_file():
        raise EvidenceError(f"Wheel does not exist: {resolved_wheel}")

    filename_name, filename_version, filename_tags = _wheel_filename_identity(
        resolved_wheel
    )
    with ZipFile(resolved_wheel) as archive:
        dist_info_directory = _archive_dist_info_directory(archive)
        wheel_headers = Parser().parsestr(
            _archive_metadata(archive, dist_info_directory, "WHEEL")
        )
        package_headers = Parser().parsestr(
            _archive_metadata(archive, dist_info_directory, "METADATA")
        )
        wheel_tags = tuple(sorted(wheel_headers.get_all("Tag", [])))
        native_members = tuple(
            sorted(name for name in archive.namelist() if _is_native_member(name))
        )
        native_core_members = _native_core_members(archive.namelist())

    dist_info_name, dist_info_version = _dist_info_identity(dist_info_directory)
    metadata_name, metadata_version = _metadata_identity(
        package_headers, resolved_wheel.name
    )
    normalized_expected_package = canonicalize_name(expected_package)
    if filename_name != normalized_expected_package:
        raise EvidenceError(
            "Wheel filename package name contradicts release identity: "
            f"expected {normalized_expected_package!r}, got {filename_name!r}."
        )
    if dist_info_name != filename_name:
        raise EvidenceError(
            "Wheel dist-info package name contradicts filename: "
            f"expected {filename_name!r}, got {dist_info_name!r}."
        )
    if metadata_name != filename_name:
        raise EvidenceError(
            "Wheel METADATA Name contradicts filename: "
            f"expected {filename_name!r}, got {metadata_name!r}."
        )
    if dist_info_version != filename_version:
        raise EvidenceError(
            "Wheel dist-info version contradicts filename: "
            f"expected {filename_version!s}, got {dist_info_version!s}."
        )
    if metadata_version != filename_version:
        raise EvidenceError(
            "Wheel METADATA Version contradicts filename: "
            f"expected {filename_version!s}, got {metadata_version!s}."
        )
    if expected_version is not None:
        try:
            normalized_expected_version = Version(expected_version)
        except InvalidVersion as error:
            raise EvidenceError(
                f"Invalid expected release version: {expected_version!r}."
            ) from error
        if filename_version != normalized_expected_version:
            raise EvidenceError(
                "Wheel version contradicts release identity: "
                f"expected {normalized_expected_version!s}, got {filename_version!s}."
            )

    if not wheel_tags:
        raise EvidenceError(f"Wheel metadata has no Tag header: {resolved_wheel.name}")
    if filename_tags != wheel_tags:
        raise EvidenceError(
            f"Wheel tag mismatch for {resolved_wheel.name}: filename tags "
            f"{list(filename_tags)!r} disagree with WHEEL tags {list(wheel_tags)!r}."
        )

    universal_tags = ("py3-none-any",)
    if filename_tags == universal_tags:
        if native_members:
            raise EvidenceError(
                f"Universal pure wheel {resolved_wheel.name} contains native member(s): "
                f"{list(native_members)!r}."
            )
        mode = "pure"
    else:
        if not native_core_members:
            raise EvidenceError(
                f"Platform wheel {resolved_wheel.name} has no native {CORE_MODULE_NAME} "
                "member and cannot be classified as compiled evidence."
            )
        mode = "compiled"

    return {
        "filename": resolved_wheel.name,
        "normalized_basename": resolved_wheel.name.lower(),
        "filename_package": filename_name,
        "filename_version": str(filename_version),
        "dist_info_directory": dist_info_directory,
        "dist_info_package": dist_info_name,
        "dist_info_version": str(dist_info_version),
        "filename_tags": list(filename_tags),
        "archive_tags": list(wheel_tags),
        "wheel_tags": list(wheel_tags),
        "metadata_name": metadata_name,
        "metadata_version": str(metadata_version),
        "native_members": list(native_members),
        "native_core_members": list(native_core_members),
        "classified_mode": mode,
        "mode": mode,
    }


def _required_sdist_members() -> tuple[str, ...]:
    """Return the source and probe files an isolated sdist child must retain."""
    package_root = REPOSITORY_ROOT / "src" / PACKAGE_NAME
    if not package_root.is_dir():
        raise EvidenceError("Source archive contract cannot locate package sources.")
    package_members = sorted(
        source.relative_to(REPOSITORY_ROOT).as_posix()
        for source in package_root.rglob("*")
        if source.is_file() and (source.suffix == ".py" or source.name == "py.typed")
    )
    if not package_members:
        raise EvidenceError("Source archive contract has no package sources.")
    return (*_SDIST_REQUIRED_ROOT_FILES, *package_members)


def _sdist_project_root(path: Path) -> str:
    """Derive the single permitted top-level root from a canonical sdist name."""
    suffix = ".tar.gz"
    if not path.name.endswith(suffix):
        raise EvidenceError(f"Expected a .tar.gz source archive, got {path.name!r}.")
    root = path.name.removesuffix(suffix)
    if not root or "/" in root or "\\" in root:
        raise EvidenceError("Source archive filename has an invalid project root.")
    return root


def _normalized_sdist_member_name(member: tarfile.TarInfo, *, root: str) -> str:
    """Normalize one tar member only after rejecting paths unsafe for extraction."""
    name = member.name
    if not isinstance(name, str) or not name or "\x00" in name or "\\" in name:
        raise EvidenceError("Source archive contains an unsafe member destination.")
    candidate = name.rstrip("/") if member.isdir() else name
    if (
        not candidate
        or candidate.startswith("/")
        or re.match(r"^[A-Za-z]:", candidate)
        or candidate.split("/")[0] != root
    ):
        raise EvidenceError("Source archive contains an unsafe member destination.")
    normalized = "/".join(part for part in candidate.split("/") if part not in {""})
    if normalized != candidate or any(
        part in {".", ".."} for part in normalized.split("/")
    ):
        raise EvidenceError("Source archive contains an unsafe member destination.")
    return normalized


def _inspect_sdist_archive(
    archive: tarfile.TarFile, *, path: Path, artifact_sha256: str
) -> tuple[dict[str, Any], tuple[tarfile.TarInfo, ...]]:
    """Inspect every sdist member before extraction or a downstream build starts."""
    root = _sdist_project_root(path)
    members: list[tarfile.TarInfo] = []
    normalized_members: set[str] = set()
    relative_members: set[str] = set()
    total_uncompressed_bytes = 0

    for member in archive:
        members.append(member)
        if len(members) > _MAX_SDIST_MEMBERS:
            raise EvidenceError("Source archive exceeds the member-count limit.")
        if not (member.isdir() or member.isfile()):
            raise EvidenceError("Source archive contains an unsafe member type.")
        normalized = _normalized_sdist_member_name(member, root=root)
        if normalized in normalized_members:
            raise EvidenceError(
                "Source archive contains a duplicate normalized member."
            )
        normalized_members.add(normalized)
        if member.isfile():
            if member.size < 0 or member.size > _MAX_SDIST_MEMBER_BYTES:
                raise EvidenceError("Source archive contains an oversized member.")
            total_uncompressed_bytes += member.size
            if total_uncompressed_bytes > _MAX_SDIST_TOTAL_UNCOMPRESSED_BYTES:
                raise EvidenceError(
                    "Source archive exceeds the uncompressed-size limit."
                )
        if normalized != root:
            relative = normalized.removeprefix(f"{root}/")
            relative_members.add(relative)

    if not members:
        raise EvidenceError("Source archive contains no members.")
    required_members = _required_sdist_members()
    missing = [member for member in required_members if member not in relative_members]
    if missing:
        raise EvidenceError(
            "Source archive is missing required build or probe input(s): "
            + ", ".join(missing)
        )
    native_members = sorted(
        member for member in relative_members if _is_native_member(member)
    )
    if native_members:
        raise EvidenceError(
            "Source archive contains unexpected native member(s): "
            + ", ".join(native_members)
        )
    return (
        {
            "schema_version": _SDIST_ARCHIVE_SCHEMA_VERSION,
            "filename": path.name,
            "sha256": artifact_sha256,
            "project_root": root,
            "member_count": len(members),
            "total_uncompressed_bytes": total_uncompressed_bytes,
            "members": sorted(relative_members),
            "required_members": list(required_members),
        },
        tuple(members),
    )


def inspect_sdist(sdist_path: Path) -> dict[str, Any]:
    """Inspect one bounded source archive without extracting it."""
    sdist = sdist_path.resolve(strict=True)
    artifact_sha256 = _artifact_sha256(sdist)
    try:
        with tarfile.open(sdist, mode="r:gz") as archive:
            record, _members = _inspect_sdist_archive(
                archive, path=sdist, artifact_sha256=artifact_sha256
            )
    except (OSError, tarfile.TarError) as error:
        raise EvidenceError("Source archive could not be inspected safely.") from error
    return record


def _extract_validated_sdist(sdist: Path, destination: Path) -> dict[str, Any]:
    """Extract an sdist only after its complete member inventory is accepted."""
    artifact_sha256 = _artifact_sha256(sdist)
    try:
        with tarfile.open(sdist, mode="r:gz") as archive:
            record, members = _inspect_sdist_archive(
                archive, path=sdist, artifact_sha256=artifact_sha256
            )
            destination.mkdir()
            if sys.version_info >= (3, 12):
                archive.extractall(destination, members=members, filter="data")
            else:
                archive.extractall(destination, members=members)
    except (OSError, tarfile.TarError) as error:
        raise EvidenceError("Source archive could not be extracted safely.") from error
    return record


def _write_sdist_build_constraints(path: Path) -> None:
    """Write the reviewed PEP 517 pins used by every derived child build."""
    path.write_text("\n".join(_SDIST_BUILD_REQUIREMENTS) + "\n", encoding="utf-8")


def _validate_sdist_child_lineage(
    children: Sequence[Mapping[str, Any]], *, parent_sdist: Mapping[str, str]
) -> None:
    """Require exactly one pure and compiled installed record bound to one parent."""
    expected_intents = {"pure", "compiled"}
    seen_intents: set[str] = set()
    if len(children) != len(expected_intents):
        raise EvidenceError(
            "Source archive derivation has missing or duplicate children."
        )
    for child in children:
        intent = child.get("requested_build_intent")
        if intent not in expected_intents or intent in seen_intents:
            raise EvidenceError(
                "Source archive derivation has missing or duplicate intents."
            )
        seen_intents.add(cast(str, intent))
        if child.get("parent_sdist") != dict(parent_sdist):
            raise EvidenceError("Source archive child lineage contradicts its parent.")
        artifact = child.get("artifact")
        if not isinstance(artifact, Mapping) or (
            artifact.get("expected_mode") != intent
            or artifact.get("build_intent") != intent
        ):
            raise EvidenceError(
                "Source archive child lineage has an invalid build intent."
            )
    if seen_intents != expected_intents:
        raise EvidenceError("Source archive derivation has missing required children.")


def verify_sdist_derivations(sdist_path: Path) -> dict[str, Any]:
    """Build and prove explicit pure and compiled wheels from one safe sdist."""
    source_archive = sdist_path.resolve(strict=True)
    _artifact_sha256(source_archive)
    with tempfile.TemporaryDirectory(prefix="fast-fsm-sdist-proof-") as temporary:
        temporary_root = Path(temporary).resolve()
        staged_archive = temporary_root / source_archive.name
        shutil.copyfile(source_archive, staged_archive)
        extraction_root = temporary_root / "extracted"
        archive_record = _extract_validated_sdist(staged_archive, extraction_root)
        source_root = extraction_root / str(archive_record["project_root"])
        if not source_root.is_dir():
            raise EvidenceError("Source archive project root was not extracted.")
        constraints = temporary_root / "build-constraints.txt"
        _write_sdist_build_constraints(constraints)
        children: list[dict[str, Any]] = []
        for intent in ("compiled", "pure"):
            wheel_directory = temporary_root / f"{intent}-wheel"
            environment = _installed_environment()
            environment["FAST_FSM_BUILD_MODE"] = intent
            environment.pop("FAST_FSM_PURE_PYTHON", None)
            _run_installed_command(
                [
                    "uv",
                    "build",
                    "--offline",
                    "--python",
                    sys.executable,
                    "--build-constraints",
                    str(constraints),
                    "--wheel",
                    "--out-dir",
                    str(wheel_directory),
                ],
                cwd=source_root,
                environment=environment,
                stage=f"sdist {intent} child build",
            )
            wheel = _exactly_one_wheel(wheel_directory)
            child = verify_installed_wheel(
                wheel, expected_mode=intent, build_intent=intent
            )
            children.append(
                {
                    **child,
                    "parent_sdist": {
                        "filename": archive_record["filename"],
                        "sha256": archive_record["sha256"],
                    },
                    "requested_build_intent": intent,
                }
            )

    parent_sdist = {
        "filename": cast(str, archive_record["filename"]),
        "sha256": cast(str, archive_record["sha256"]),
    }
    _validate_sdist_child_lineage(children, parent_sdist=parent_sdist)
    return {
        "schema_version": _SDIST_ARCHIVE_SCHEMA_VERSION,
        "archive": archive_record,
        "children": children,
    }


def verify_wheels(
    wheel_paths: Iterable[Path], *, expected_version: str | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Collect deterministic independent evidence for a repeated wheel input."""
    release_version = expected_version or metadata.version("fast-fsm")
    artifacts = [
        inspect_wheel(path, expected_version=release_version) for path in wheel_paths
    ]
    artifacts.sort(
        key=lambda artifact: (
            artifact["normalized_basename"],
            tuple(artifact["filename_tags"]),
        )
    )
    normalized_basenames = [artifact["normalized_basename"] for artifact in artifacts]
    duplicates = sorted(
        name
        for name in set(normalized_basenames)
        if normalized_basenames.count(name) > 1
    )
    if duplicates:
        raise EvidenceError(
            "Duplicate normalized wheel artifact identities: " + ", ".join(duplicates)
        )
    return {"artifacts": artifacts}


def _artifact_sha256(path: Path) -> str:
    """Hash one bounded archive before any isolated-environment work begins."""
    try:
        size = path.stat().st_size
    except OSError as error:
        raise EvidenceError("Artifact identity could not be read.") from error
    if size <= 0 or size > _MAX_ARTIFACT_BYTES:
        raise EvidenceError("Artifact identity violates the archive size limit.")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise EvidenceError("Artifact identity could not be hashed.") from error
    return digest.hexdigest()


def _strict_json_object(value: str, *, field: str) -> dict[str, Any]:
    """Parse one child object without accepting duplicate keys or NaN values."""
    if len(value.encode("utf-8")) > _MAX_CHILD_OUTPUT_BYTES:
        raise EvidenceError(f"Installed artifact {field} exceeds the size limit.")

    def reject_constant(_value: str) -> None:
        raise ValueError("non-standard JSON number")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = item
        return result

    try:
        parsed = json.loads(
            value,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise EvidenceError(f"Installed artifact {field} is malformed.") from error
    if not isinstance(parsed, dict):
        raise EvidenceError(f"Installed artifact {field} must be a JSON object.")
    return parsed


def _validate_json_bounds(value: Any, *, depth: int = 0) -> None:
    """Reject child values that exceed finite evidence resource budgets."""
    if depth > _MAX_CHILD_NESTING:
        raise EvidenceError("Installed artifact child evidence exceeds nesting limits.")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > _MAX_SAFE_JSON_INTEGER:
            raise EvidenceError(
                "Installed artifact child evidence has an unsafe number."
            )
        return
    if isinstance(value, str):
        if len(value) > _MAX_CHILD_STRING_LENGTH:
            raise EvidenceError(
                "Installed artifact child evidence has an oversized string."
            )
        return
    if isinstance(value, list):
        if len(value) > _MAX_CHILD_COLLECTION_LENGTH:
            raise EvidenceError(
                "Installed artifact child evidence has too many values."
            )
        for item in value:
            _validate_json_bounds(item, depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > _MAX_CHILD_COLLECTION_LENGTH:
            raise EvidenceError(
                "Installed artifact child evidence has too many fields."
            )
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > _MAX_CHILD_STRING_LENGTH:
                raise EvidenceError(
                    "Installed artifact child evidence has an invalid field."
                )
            _validate_json_bounds(item, depth=depth + 1)
        return
    raise EvidenceError("Installed artifact child evidence has an invalid value.")


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _expected_conformance_suite_sha256() -> str:
    """Load only the copied-probe definition seam and bind child suite identity."""
    probe_path = Path(__file__).with_name("artifact_conformance.py")
    spec = util.spec_from_file_location("_artifact_conformance_contract", probe_path)
    if spec is None or spec.loader is None:
        raise EvidenceError(
            "Installed artifact conformance contract could not be loaded."
        )
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite = getattr(module, "_suite_sha256", None)
    if not callable(suite):
        raise EvidenceError("Installed artifact conformance contract is incomplete.")
    value = suite()
    if not _is_sha256(value):
        raise EvidenceError("Installed artifact conformance contract is malformed.")
    return value


def _path_is_contained(path: Path, root: Path) -> bool:
    """Return whether a resolved artifact-runtime path is inside its fresh env."""
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _lexically_contained(path: Path, root: Path) -> bool:
    """Check a venv entrypoint without resolving its intentional interpreter symlink."""
    try:
        path.absolute().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _direct_url_references_checkout(direct_url: Mapping[str, Any]) -> bool:
    """Return whether untrusted PEP 610 metadata points back into this checkout."""
    value = direct_url.get("url")
    if not isinstance(value, str) or not value:
        raise EvidenceError("Installed artifact direct-url provenance is malformed.")
    parsed = urlparse(value)
    if parsed.scheme != "file":
        return False
    return _path_is_contained(Path(unquote(parsed.path)), REPOSITORY_ROOT)


def _installed_environment() -> dict[str, str]:
    """Remove checkout and project discovery from an installed-artifact child."""
    environment = dict(os.environ)
    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "UV_PROJECT",
        "UV_WORKING_DIR",
        "UV_CONFIG_FILE",
        "UV_RUN_RECURSION_DEPTH",
        "FAST_FSM_PURE_PYTHON",
    ):
        environment.pop(key, None)
    for key in tuple(environment):
        if key.startswith("COV_CORE_") or key == "COVERAGE_PROCESS_START":
            environment.pop(key)
    environment["UV_NO_PROJECT"] = "1"
    environment["UV_NO_CONFIG"] = "1"
    return environment


def _environment_python(environment_root: Path) -> Path:
    """Resolve the absolute interpreter path for a fresh virtual environment."""
    candidates = (
        environment_root / "bin" / "python",
        environment_root / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            # Preserve the venv entrypoint rather than resolving its interpreter
            # symlink to uv's externally managed base Python.
            return candidate.absolute()
    raise EvidenceError("Installed artifact environment has no interpreter.")


def _run_installed_command(
    arguments: Sequence[str], *, cwd: Path, environment: Mapping[str, str], stage: str
) -> str:
    """Run an isolated child while retaining only bounded, non-manifest diagnostics."""
    completed = subprocess.run(
        list(arguments),
        cwd=cwd,
        env=dict(environment),
        text=True,
        capture_output=True,
        check=False,
    )
    if (
        len(completed.stdout.encode("utf-8")) > _MAX_CHILD_OUTPUT_BYTES
        or len(completed.stderr.encode("utf-8")) > _MAX_CHILD_OUTPUT_BYTES
    ):
        raise EvidenceError(f"Installed artifact {stage} exceeded the output limit.")
    if completed.returncode:
        raise EvidenceError(
            f"Installed artifact {stage} failed.",
            diagnostics=(completed.stdout, completed.stderr),
        )
    return completed.stdout


def _validate_runtime_probe(
    runtime: Mapping[str, Any],
    *,
    environment_root: Path,
    expected_mode: str,
    version: str,
) -> dict[str, Any]:
    """Check runtime provenance and mode before semantic evidence is accepted."""
    required = {
        "distribution_version",
        "package_version",
        "package_origin",
        "core_origin",
        "core_loader",
        "interpreter",
        "python_implementation",
        "python_version",
        "platform",
        "machine",
        "direct_url",
        "extension_suffixes",
    }
    if set(runtime) != required:
        raise EvidenceError("Installed artifact runtime identity is incomplete.")
    string_fields = required - {"direct_url", "extension_suffixes"}
    if any(
        not isinstance(runtime[field], str) or not runtime[field]
        for field in string_fields
    ):
        raise EvidenceError("Installed artifact runtime identity is malformed.")
    if (
        runtime["distribution_version"] != version
        or runtime["package_version"] != version
    ):
        raise EvidenceError(
            "Installed artifact runtime version contradicts archive identity."
        )
    for field in ("package_origin", "core_origin"):
        if not _path_is_contained(Path(runtime[field]), environment_root):
            raise EvidenceError(
                "Installed artifact runtime origin escapes its environment."
            )
    if not _lexically_contained(Path(runtime["interpreter"]), environment_root):
        raise EvidenceError("Installed artifact interpreter escapes its environment.")
    direct_url = runtime["direct_url"]
    if direct_url is not None and not isinstance(direct_url, dict):
        raise EvidenceError("Installed artifact direct-url provenance is malformed.")
    if isinstance(direct_url, dict) and bool(
        cast(Mapping[str, Any], direct_url).get("dir_info", {}).get("editable", False)
    ):
        raise EvidenceError("Installed artifact provenance is editable.")
    if isinstance(direct_url, dict) and _direct_url_references_checkout(
        cast(Mapping[str, Any], direct_url)
    ):
        raise EvidenceError("Installed artifact provenance references the checkout.")
    suffixes = runtime["extension_suffixes"]
    if (
        not isinstance(suffixes, list)
        or not suffixes
        or not all(isinstance(suffix, str) and suffix for suffix in suffixes)
    ):
        raise EvidenceError("Installed artifact extension classification is malformed.")
    core_origin = Path(runtime["core_origin"])
    is_extension = core_origin.suffix in set(suffixes)
    if expected_mode == "pure":
        if core_origin.suffix != ".py" or is_extension:
            raise EvidenceError(
                "Installed artifact pure mode has a native core origin."
            )
        if find_native_core_shadows(Path(runtime["package_origin"]).parent):
            raise EvidenceError("Installed artifact pure mode has a native shadow.")
    elif expected_mode == "compiled":
        if not is_extension or runtime["core_loader"] != "ExtensionFileLoader":
            raise EvidenceError(
                "Installed artifact compiled mode lacks an extension core origin."
            )
    else:
        raise EvidenceError("Installed artifact expected mode is invalid.")
    return {
        field: runtime[field]
        for field in (
            "distribution_version",
            "package_version",
            "package_origin",
            "core_origin",
            "core_loader",
            "interpreter",
            "python_implementation",
            "python_version",
            "platform",
            "machine",
        )
    }


def _validate_archive_runtime_architecture(
    archive_tags: Sequence[object],
    runtime: Mapping[str, Any],
    *,
    expected_mode: str,
) -> None:
    """Require a compiled archive tag to match the native runtime that ran it."""
    if expected_mode == "pure":
        return
    platform_name = runtime.get("platform")
    machine = runtime.get("machine")
    if not isinstance(platform_name, str) or not isinstance(machine, str):
        raise EvidenceError("Installed artifact runtime architecture is malformed.")
    platform_markers = {
        "darwin": ("macosx",),
        "windows": ("win",),
        "linux": ("linux",),
    }
    architecture_markers = {
        "arm64": ("arm64", "aarch64", "universal2"),
        "aarch64": ("arm64", "aarch64", "universal2"),
        "x86_64": ("x86_64", "amd64", "universal2"),
        "amd64": ("x86_64", "amd64", "universal2"),
    }
    expected_platforms = platform_markers.get(platform_name.casefold())
    expected_architectures = architecture_markers.get(machine.casefold())
    if expected_platforms is None or expected_architectures is None:
        raise EvidenceError("Installed artifact runtime architecture is unsupported.")
    normalized_tags = [tag.casefold() for tag in archive_tags if isinstance(tag, str)]
    if not normalized_tags or not any(
        any(platform_marker in tag for platform_marker in expected_platforms)
        and any(
            architecture_marker in tag for architecture_marker in expected_architectures
        )
        for tag in normalized_tags
    ):
        raise EvidenceError(
            "Installed artifact archive architecture does not match the runtime."
        )


def _validate_child_conformance(
    value: Mapping[str, Any], *, expected_suite_sha256: str
) -> dict[str, Any]:
    """Accept only the strict semantic contract emitted by the copied probe."""
    expected = {
        "schema_version",
        "suite_sha256",
        "scenarios",
        "semantic_sha256",
        "payload_leak_free",
    }
    if set(value) != expected:
        raise EvidenceError("Installed artifact conformance schema is incomplete.")
    if value["schema_version"] != 1 or value["payload_leak_free"] is not True:
        raise EvidenceError("Installed artifact conformance verdict is invalid.")
    if not all(
        _is_sha256(value[field]) for field in ("suite_sha256", "semantic_sha256")
    ):
        raise EvidenceError("Installed artifact conformance digest is malformed.")
    if value["suite_sha256"] != expected_suite_sha256:
        raise EvidenceError("Installed artifact conformance suite digest is invalid.")
    if not isinstance(value["scenarios"], list) or not value["scenarios"]:
        raise EvidenceError("Installed artifact conformance scenario set is invalid.")
    _validate_json_bounds(value)
    for scenario in value["scenarios"]:
        if not isinstance(scenario, dict):
            raise EvidenceError("Installed artifact conformance scenario is malformed.")
        if not isinstance(scenario.get("id"), str) or not isinstance(
            scenario.get("family"), str
        ):
            raise EvidenceError("Installed artifact conformance scenario is malformed.")
        if _FORBIDDEN_CONFORMANCE_FIELDS.intersection(scenario):
            raise EvidenceError(
                "Installed artifact conformance scenario has forbidden fields."
            )
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if any(token in rendered for token in _FORBIDDEN_CONFORMANCE_TOKENS):
        raise EvidenceError(
            "Installed artifact conformance scenario contains payload data."
        )
    semantic_input = {
        "schema_version": value["schema_version"],
        "suite_sha256": value["suite_sha256"],
        "scenarios": value["scenarios"],
    }
    expected_semantic = hashlib.sha256(
        json.dumps(
            semantic_input, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()
    if value["semantic_sha256"] != expected_semantic:
        raise EvidenceError(
            "Installed artifact conformance semantic digest is invalid."
        )
    return dict(value)


def _extract_child_probe(
    value: Mapping[str, Any],
    *,
    expected_artifact_sha256: str,
    expected_suite_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate child shape and parent-bound identity before provenance checks."""
    _validate_json_bounds(value)
    if set(value) != {"artifact_sha256", "conformance", "runtime"}:
        raise EvidenceError("Installed artifact child probe has an invalid schema.")
    if value["artifact_sha256"] != expected_artifact_sha256:
        raise EvidenceError("Installed artifact child artifact identity is invalid.")
    conformance = value["conformance"]
    runtime = value["runtime"]
    if not isinstance(conformance, dict) or not isinstance(runtime, dict):
        raise EvidenceError("Installed artifact child probe is malformed.")
    return dict(conformance), dict(runtime)


def _validate_child_probe(
    value: Mapping[str, Any],
    *,
    expected_artifact_sha256: str,
    expected_suite_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate all untrusted child evidence for direct unit-test use."""
    conformance, runtime = _extract_child_probe(
        value,
        expected_artifact_sha256=expected_artifact_sha256,
        expected_suite_sha256=expected_suite_sha256,
    )
    suite_sha256 = expected_suite_sha256 or _expected_conformance_suite_sha256()
    return (
        _validate_child_conformance(conformance, expected_suite_sha256=suite_sha256),
        runtime,
    )


def verify_installed_wheel(
    wheel_path: Path, *, expected_mode: str, build_intent: str
) -> dict[str, Any]:
    """Prove one exact wheel in a neutral fresh environment before accepting semantics."""
    if expected_mode not in {"pure", "compiled"} or build_intent not in {
        "pure",
        "compiled",
    }:
        raise EvidenceError(
            "Installed artifact mode and build intent must be explicit."
        )
    if expected_mode != build_intent:
        raise EvidenceError("Installed artifact mode contradicts build intent.")
    artifact = wheel_path.resolve(strict=True)
    artifact_sha256 = _artifact_sha256(artifact)
    archive = inspect_wheel(artifact)
    if archive["classified_mode"] != expected_mode:
        raise EvidenceError(
            "Installed artifact archive mode contradicts expected mode."
        )
    expected_suite_sha256 = _expected_conformance_suite_sha256()

    with tempfile.TemporaryDirectory(
        prefix="fast-fsm-installed-artifact-"
    ) as temporary:
        temporary_root = Path(temporary).resolve()
        environment_root = temporary_root / "environment"
        neutral_directory = temporary_root / "neutral"
        neutral_directory.mkdir()
        environment = _installed_environment()
        _run_installed_command(
            [
                "uv",
                "venv",
                "--no-project",
                "--no-config",
                "--python",
                sys.executable,
                str(environment_root),
            ],
            cwd=neutral_directory,
            environment=environment,
            stage="environment creation",
        )
        interpreter = _environment_python(environment_root)
        _run_installed_command(
            [
                "uv",
                "pip",
                "install",
                "--offline",
                "--no-config",
                "--python",
                str(interpreter),
                str(artifact),
            ],
            cwd=neutral_directory,
            environment=environment,
            stage="artifact installation",
        )
        probe = neutral_directory / "artifact_conformance.py"
        shutil.copyfile(Path(__file__).with_name("artifact_conformance.py"), probe)
        child = _strict_json_object(
            _run_installed_command(
                [
                    str(interpreter),
                    str(probe),
                    "--installed-probe",
                    "--artifact-sha256",
                    artifact_sha256,
                ],
                cwd=neutral_directory,
                environment=environment,
                stage="conformance probe",
            ),
            field="child probe",
        )
        conformance, runtime = _extract_child_probe(
            child,
            expected_artifact_sha256=artifact_sha256,
            expected_suite_sha256=expected_suite_sha256,
        )
        runtime_record = _validate_runtime_probe(
            runtime,
            environment_root=environment_root,
            expected_mode=expected_mode,
            version=str(archive["metadata_version"]),
        )
        _validate_archive_runtime_architecture(
            cast(Sequence[object], archive["wheel_tags"]),
            runtime,
            expected_mode=expected_mode,
        )
        conformance_record = _validate_child_conformance(
            conformance,
            expected_suite_sha256=expected_suite_sha256,
        )

    return {
        "schema_version": _INSTALLED_ARTIFACT_SCHEMA_VERSION,
        "artifact": {
            "filename": archive["filename"],
            "sha256": artifact_sha256,
            "wheel_tags": archive["wheel_tags"],
            "native_members": archive["native_members"],
            "classified_mode": archive["classified_mode"],
            "expected_mode": expected_mode,
            "build_intent": build_intent,
        },
        "runtime": {**runtime_record, "expected_mode": expected_mode},
        "conformance": conformance_record,
    }


def _module_name_for_path(source_root: Path, source_file: Path) -> str:
    """Map an importable package path to its module name."""
    relative = source_file.relative_to(source_root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[0] == PACKAGE_NAME:
        parts.pop(0)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join([PACKAGE_NAME, *parts])


PROVEN_SAFE_SLOT_BASES = frozenset({"builtins.object", "abc.ABC"})


def _resolve_from_import_module(module_name: str, statement: ast.ImportFrom) -> str:
    """Resolve one ``from`` statement to its absolute module identity."""
    if not statement.level:
        return statement.module or ""
    package_parts = module_name.rsplit(".", 1)[0].split(".")
    if statement.level > 1:
        package_parts = package_parts[: 1 - statement.level]
    if statement.module:
        package_parts.extend(statement.module.split("."))
    return ".".join(package_parts)


BindingEnvironment = dict[str, frozenset[str]]
ClassOccurrence = tuple[ast.ClassDef, BindingEnvironment]


def _merge_binding_environments(
    environments: Iterable[Mapping[str, frozenset[str]]],
) -> BindingEnvironment:
    """Join possible reaching environments without choosing one branch."""
    merged: dict[str, set[str]] = {}
    for environment in environments:
        for name, references in environment.items():
            merged.setdefault(name, set()).update(references)
    return {name: frozenset(references) for name, references in merged.items()}


def _apply_import_binding(
    statement: ast.stmt,
    environment: Mapping[str, frozenset[str]],
    module_name: str,
) -> BindingEnvironment:
    """Return one sequential environment after a statically known import."""
    updated = dict(environment)
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            local_name = alias.asname or alias.name.split(".", 1)[0]
            reference = alias.name if alias.asname else local_name
            updated[local_name] = frozenset({reference})
    elif isinstance(statement, ast.ImportFrom):
        imported_module = _resolve_from_import_module(module_name, statement)
        for alias in statement.names:
            if alias.name == "*":
                raise EvidenceError(
                    "Wildcard import blocks fail-closed slots-policy analysis: "
                    f"{imported_module or '<relative>'}"
                )
            local_name = alias.asname or alias.name
            updated[local_name] = frozenset(
                {".".join(part for part in (imported_module, alias.name) if part)}
            )
    return updated


def _target_names(target: ast.expr) -> set[str]:
    """Return names directly rebound by one assignment-like target."""
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_target_names(item) for item in target.elts))
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return set()


def _mutation_root_names(target: ast.expr) -> set[str]:
    """Return imported-name roots mutated through an attribute or subscript."""
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_mutation_root_names(item) for item in target.elts))
    if isinstance(target, ast.Starred):
        return _mutation_root_names(target.value)
    if not isinstance(target, (ast.Attribute, ast.Subscript)):
        return set()
    return _reference_root_names(target.value)


def _reference_root_names(expression: ast.expr) -> set[str]:
    """Return names whose objects are reached by a qualified runtime expression."""
    if isinstance(expression, ast.Name):
        return {expression.id}
    if isinstance(expression, (ast.Attribute, ast.Subscript)):
        return _reference_root_names(expression.value)
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "vars"
        and len(expression.args) == 1
        and not expression.keywords
    ):
        return _reference_root_names(expression.args[0])
    return set()


def _target_mutation_roots(targets: Iterable[ast.expr]) -> set[str]:
    """Return roots mutated by one statement's assignment-like targets."""
    return set().union(*(_mutation_root_names(target) for target in targets))


def _is_imported_binding(references: frozenset[str], module_name: str) -> bool:
    """Return whether a reaching name still identifies an imported object."""
    local_prefix = f"{module_name}."
    return any(
        not reference.startswith("<unresolved:")
        and reference != module_name
        and not reference.startswith(local_prefix)
        for reference in references
    )


_BUILTIN_MUTATOR_REFERENCES = frozenset({"builtins.setattr", "builtins.delattr"})


def _expression_references(
    expression: ast.expr,
    environment: Mapping[str, frozenset[str]],
) -> frozenset[str]:
    """Resolve a dotted runtime expression through its reaching bindings."""
    parts = _dotted_expression_parts(expression)
    if not parts:
        return frozenset()
    bindings = environment.get(parts[0])
    if bindings is not None:
        return frozenset(".".join([binding, *parts[1:]]) for binding in bindings)
    if len(parts) == 1 and parts[0] in {"setattr", "delattr"}:
        return frozenset({f"builtins.{parts[0]}"})
    return frozenset()


def _mutator_references(
    expression: ast.expr,
    environment: Mapping[str, frozenset[str]],
) -> frozenset[str]:
    """Return every reaching standard attribute-mutator identity."""
    return _expression_references(expression, environment) & _BUILTIN_MUTATOR_REFERENCES


def _reject_imported_binding_mutation(
    roots: Iterable[str],
    environment: Mapping[str, frozenset[str]],
    module_name: str,
) -> None:
    """Fail closed when code mutates an object reached from an import binding."""
    for root in roots:
        references = environment.get(root)
        if references is not None and _is_imported_binding(references, module_name):
            raise EvidenceError(
                "Imported binding mutation blocks fail-closed slots-policy analysis: "
                f"{module_name}.{root}"
            )


def _expression_mutation_roots(
    expression: ast.expr,
    environment: Mapping[str, frozenset[str]],
) -> set[str]:
    """Return roots passed to a statically resolved standard attribute mutator."""
    roots: set[str] = set()
    for node in ast.walk(expression):
        if (
            isinstance(node, ast.Call)
            and _mutator_references(node.func, environment)
            and node.args
        ):
            roots.update(_reference_root_names(node.args[0]))
    return roots


def _statement_mutation_roots(
    statement: ast.stmt,
    environment: Mapping[str, frozenset[str]],
) -> set[str]:
    """Return imported roots mutated by this statement without descending scopes."""
    if isinstance(statement, ast.Assign):
        return _target_mutation_roots(statement.targets) | _expression_mutation_roots(
            statement.value, environment
        )
    if isinstance(statement, ast.AnnAssign):
        roots = _mutation_root_names(statement.target)
        return roots | (
            _expression_mutation_roots(statement.value, environment)
            if statement.value is not None
            else set()
        )
    if isinstance(statement, ast.AugAssign):
        return _mutation_root_names(statement.target) | _expression_mutation_roots(
            statement.value, environment
        )
    if isinstance(statement, ast.Delete):
        return _target_mutation_roots(statement.targets)
    if isinstance(statement, ast.Expr):
        return _expression_mutation_roots(statement.value, environment)
    if isinstance(statement, ast.If):
        return _expression_mutation_roots(statement.test, environment)
    if isinstance(statement, ast.While):
        return _expression_mutation_roots(statement.test, environment)
    if isinstance(statement, (ast.For, ast.AsyncFor)):
        return _expression_mutation_roots(statement.iter, environment)
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        return set().union(
            *(
                _expression_mutation_roots(item.context_expr, environment)
                for item in statement.items
            )
        )
    if isinstance(statement, ast.Match):
        return _expression_mutation_roots(statement.subject, environment)
    return set()


def _mutation_roots_in_statements(statements: Iterable[ast.stmt]) -> set[str]:
    """Collect attribute/subscript mutation roots without entering child scopes."""
    roots: set[str] = set()
    for statement in statements:
        if isinstance(statement, ast.Assign):
            roots.update(_target_mutation_roots(statement.targets))
        elif isinstance(statement, ast.AnnAssign):
            roots.update(_mutation_root_names(statement.target))
        elif isinstance(statement, ast.AugAssign):
            roots.update(_mutation_root_names(statement.target))
        elif isinstance(statement, ast.Delete):
            roots.update(_target_mutation_roots(statement.targets))
        if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            roots.update(_mutation_roots_in_statements(statement.body))
            roots.update(_mutation_roots_in_statements(statement.orelse))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            roots.update(_mutation_roots_in_statements(statement.body))
        elif isinstance(statement, ast.If):
            roots.update(_mutation_roots_in_statements(statement.body))
            roots.update(_mutation_roots_in_statements(statement.orelse))
        elif isinstance(statement, ast.Match):
            for case in statement.cases:
                roots.update(_mutation_roots_in_statements(case.body))
        elif (
            isinstance(statement, ast.Try) or statement.__class__.__name__ == "TryStar"
        ):
            try_statement = cast(ast.Try, statement)
            roots.update(_mutation_roots_in_statements(try_statement.body))
            roots.update(_mutation_roots_in_statements(try_statement.orelse))
            roots.update(_mutation_roots_in_statements(try_statement.finalbody))
            for handler in try_statement.handlers:
                roots.update(_mutation_roots_in_statements(handler.body))
    return roots


def _pattern_names(pattern: ast.pattern) -> set[str]:
    """Return capture names from one module-level match pattern."""
    names: set[str] = set()
    for node in ast.walk(pattern):
        if isinstance(node, ast.MatchAs) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
    return names


def _unresolved_environment(
    environment: Mapping[str, frozenset[str]], names: Iterable[str]
) -> BindingEnvironment:
    """Invalidate bindings that an arbitrary runtime value could replace."""
    updated = dict(environment)
    for name in names:
        updated[name] = frozenset({f"<unresolved:{name}>"})
    return updated


def _bound_names_in_statements(statements: Iterable[ast.stmt]) -> set[str]:
    """Collect every binding in a control-flow tree without entering scopes."""
    names: set[str] = set()
    for statement in statements:
        if isinstance(statement, ast.Import):
            names.update(
                alias.asname or alias.name.split(".", 1)[0] for alias in statement.names
            )
        elif isinstance(statement, ast.ImportFrom):
            names.update(
                alias.asname or alias.name
                for alias in statement.names
                if alias.name != "*"
            )
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                names.update(_target_names(target))
        elif isinstance(statement, ast.AnnAssign):
            names.update(_target_names(statement.target))
        elif isinstance(statement, ast.AugAssign):
            names.update(_target_names(statement.target))
        elif isinstance(statement, ast.Delete):
            for target in statement.targets:
                names.update(_target_names(target))
        elif isinstance(
            statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            names.add(statement.name)
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            names.update(_target_names(statement.target))
            names.update(_bound_names_in_statements(statement.body))
            names.update(_bound_names_in_statements(statement.orelse))
        elif isinstance(statement, ast.While):
            names.update(_bound_names_in_statements(statement.body))
            names.update(_bound_names_in_statements(statement.orelse))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                if item.optional_vars:
                    names.update(_target_names(item.optional_vars))
            names.update(_bound_names_in_statements(statement.body))
        elif isinstance(statement, ast.If):
            names.update(_bound_names_in_statements(statement.body))
            names.update(_bound_names_in_statements(statement.orelse))
        elif isinstance(statement, ast.Match):
            for case in statement.cases:
                names.update(_pattern_names(case.pattern))
                names.update(_bound_names_in_statements(case.body))
        elif (
            isinstance(statement, ast.Try) or statement.__class__.__name__ == "TryStar"
        ):
            try_statement = cast(ast.Try, statement)
            names.update(_bound_names_in_statements(try_statement.body))
            names.update(_bound_names_in_statements(try_statement.orelse))
            names.update(_bound_names_in_statements(try_statement.finalbody))
            for handler in try_statement.handlers:
                if handler.name:
                    names.add(handler.name)
                names.update(_bound_names_in_statements(handler.body))
        for node in ast.walk(statement):
            if isinstance(node, ast.NamedExpr):
                names.update(_target_names(node.target))
    return names


def _is_main_demo_condition(condition: ast.expr) -> bool:
    """Return whether an ``if`` body is the conventional script-only boundary."""
    if not isinstance(condition, ast.Compare) or len(condition.ops) != 1:
        return False
    if not isinstance(condition.ops[0], ast.Eq) or len(condition.comparators) != 1:
        return False
    left, right = condition.left, condition.comparators[0]
    return (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    ) or (
        isinstance(right, ast.Name)
        and right.id == "__name__"
        and isinstance(left, ast.Constant)
        and left.value == "__main__"
    )


def _is_type_checking_condition(condition: ast.expr) -> bool:
    """Return whether a direct standard type-only guard has no runtime body."""
    return (isinstance(condition, ast.Name) and condition.id == "TYPE_CHECKING") or (
        isinstance(condition, ast.Attribute)
        and isinstance(condition.value, ast.Name)
        and condition.value.id == "typing"
        and condition.attr == "TYPE_CHECKING"
    )


def _walk_module_statements(
    statements: Iterable[ast.stmt],
    environment: Mapping[str, frozenset[str]],
    module_name: str,
) -> tuple[list[ClassOccurrence], BindingEnvironment]:
    """Walk module control flow in order with branch-local reaching bindings."""
    occurrences: list[ClassOccurrence] = []
    current = dict(environment)
    for statement in statements:
        named_expression_names = {
            name
            for node in ast.walk(statement)
            if isinstance(node, ast.NamedExpr)
            for name in _target_names(node.target)
        }
        if named_expression_names:
            current = _unresolved_environment(current, named_expression_names)
        _reject_imported_binding_mutation(
            _statement_mutation_roots(statement, current), current, module_name
        )
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            current = _apply_import_binding(statement, current, module_name)
        elif isinstance(statement, ast.ClassDef):
            occurrences.append((statement, dict(current)))
            current[statement.name] = frozenset({f"{module_name}.{statement.name}"})
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            current = _unresolved_environment(current, {statement.name})
        elif isinstance(statement, ast.Assign):
            mutator_aliases = _mutator_references(statement.value, current)
            current = _unresolved_environment(
                current,
                set().union(*(_target_names(target) for target in statement.targets)),
            )
            if (
                mutator_aliases
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                current[statement.targets[0].id] = mutator_aliases
        elif isinstance(statement, ast.AnnAssign):
            mutator_aliases = (
                _mutator_references(statement.value, current)
                if statement.value is not None
                else frozenset()
            )
            current = _unresolved_environment(current, _target_names(statement.target))
            if mutator_aliases and isinstance(statement.target, ast.Name):
                current[statement.target.id] = mutator_aliases
        elif isinstance(statement, ast.AugAssign):
            current = _unresolved_environment(current, _target_names(statement.target))
        elif isinstance(statement, ast.Delete):
            current = _unresolved_environment(
                current,
                set().union(*(_target_names(target) for target in statement.targets)),
            )
        elif isinstance(statement, ast.If):
            if _is_main_demo_condition(statement.test) or _is_type_checking_condition(
                statement.test
            ):
                nested, current = _walk_module_statements(
                    statement.orelse, current, module_name
                )
                occurrences.extend(nested)
            else:
                then_occurrences, then_environment = _walk_module_statements(
                    statement.body, current, module_name
                )
                else_occurrences, else_environment = _walk_module_statements(
                    statement.orelse, current, module_name
                )
                occurrences.extend(then_occurrences)
                occurrences.extend(else_occurrences)
                current = _merge_binding_environments(
                    (then_environment, else_environment)
                )
        elif (
            isinstance(statement, ast.Try) or statement.__class__.__name__ == "TryStar"
        ):
            try_statement = cast(ast.Try, statement)
            body_occurrences, body_environment = _walk_module_statements(
                try_statement.body, current, module_name
            )
            else_occurrences, successful_environment = _walk_module_statements(
                try_statement.orelse, body_environment, module_name
            )
            occurrences.extend(body_occurrences)
            occurrences.extend(else_occurrences)
            path_environments = [successful_environment]
            handler_entry = _unresolved_environment(
                current, _bound_names_in_statements(try_statement.body)
            )
            for handler in try_statement.handlers:
                handler_environment_start = _unresolved_environment(
                    handler_entry, {handler.name} if handler.name else set()
                )
                handler_occurrences, handler_environment = _walk_module_statements(
                    handler.body, handler_environment_start, module_name
                )
                occurrences.extend(handler_occurrences)
                path_environments.append(handler_environment)
            final_environment = _merge_binding_environments(path_environments)
            final_occurrences, current = _walk_module_statements(
                try_statement.finalbody, final_environment, module_name
            )
            occurrences.extend(final_occurrences)
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            with_names = {
                name
                for item in statement.items
                if item.optional_vars is not None
                for name in _target_names(item.optional_vars)
            }
            current = _unresolved_environment(current, with_names)
            nested, current = _walk_module_statements(
                statement.body, current, module_name
            )
            occurrences.extend(nested)
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            loop_invalidated_names = _bound_names_in_statements(
                [*statement.body, *statement.orelse]
            ) | _mutation_roots_in_statements([*statement.body, *statement.orelse])
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                current = _unresolved_environment(
                    current, _target_names(statement.target)
                )
            body_occurrences, body_environment = _walk_module_statements(
                statement.body, current, module_name
            )
            occurrences.extend(body_occurrences)
            loop_environment = _merge_binding_environments((current, body_environment))
            else_occurrences, current = _walk_module_statements(
                statement.orelse, loop_environment, module_name
            )
            occurrences.extend(else_occurrences)
            current = _unresolved_environment(current, loop_invalidated_names)
        elif isinstance(statement, ast.Match):
            case_environments: list[BindingEnvironment] = [dict(current)]
            for case in statement.cases:
                case_entry = _unresolved_environment(
                    current, _pattern_names(case.pattern)
                )
                nested, case_environment = _walk_module_statements(
                    case.body, case_entry, module_name
                )
                occurrences.extend(nested)
                case_environments.append(case_environment)
            current = _merge_binding_environments(case_environments)
    return occurrences, current


def _dotted_expression_parts(expression: ast.expr) -> tuple[str, ...] | None:
    """Return dotted source components only for statically resolvable bases."""
    if isinstance(expression, ast.Name):
        return (expression.id,)
    if isinstance(expression, ast.Attribute):
        prefix = _dotted_expression_parts(expression.value)
        return (*prefix, expression.attr) if prefix is not None else None
    return None


def _base_references(
    class_node: ast.ClassDef,
    *,
    module_name: str,
    import_bindings: Mapping[str, frozenset[str]],
) -> tuple[str, ...]:
    """Resolve bases to module-qualified identities or explicit unknown markers."""
    references: list[str] = []
    for base in class_node.bases:
        parts = _dotted_expression_parts(base)
        if not parts:
            references.append(f"<unresolved:{ast.unparse(base)}>")
            continue
        bindings = import_bindings.get(parts[0])
        if bindings is not None:
            references.extend(".".join([binding, *parts[1:]]) for binding in bindings)
        elif parts == ("object",):
            references.append("builtins.object")
        else:
            references.append(f"<unresolved:{'.'.join(parts)}>")
    return tuple(references)


def _slots_declaration(class_node: ast.ClassDef) -> tuple[bool, bool, bool]:
    """Return slots presence, literal inspectability, and ``__dict__`` status.

    Only literal strings and collections of literal strings prove a slots
    declaration safe. Any alias, computed expression, or annotation without a
    value leaves the instance layout unprovable and must fail closed.
    """
    has_own_slots = False
    slots_are_literal = True
    declares_instance_dict = False

    def literal_slot_names(value: ast.expr) -> tuple[str, ...] | None:
        if isinstance(value, ast.Constant):
            return (value.value,) if isinstance(value.value, str) else None
        if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            names: list[str] = []
            for item in value.elts:
                if not isinstance(item, ast.Constant) or not isinstance(
                    item.value, str
                ):
                    return None
                names.append(item.value)
            return tuple(names)
        return None

    for statement in class_node.body:
        if isinstance(statement, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__slots__"
                for target in statement.targets
            ):
                has_own_slots = True
                names = literal_slot_names(statement.value)
                if names is None:
                    slots_are_literal = False
                else:
                    declares_instance_dict = (
                        declares_instance_dict or "__dict__" in names
                    )
        elif isinstance(statement, ast.AnnAssign):
            if (
                isinstance(statement.target, ast.Name)
                and statement.target.id == "__slots__"
            ):
                has_own_slots = True
                if statement.value is None:
                    slots_are_literal = False
                else:
                    names = literal_slot_names(statement.value)
                    if names is None:
                        slots_are_literal = False
                    else:
                        declares_instance_dict = (
                            declares_instance_dict or "__dict__" in names
                        )

    for decorator in class_node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        decorator_name = (
            decorator.func.id
            if isinstance(decorator.func, ast.Name)
            else decorator.func.attr
            if isinstance(decorator.func, ast.Attribute)
            else ""
        )
        if decorator_name != "dataclass":
            continue
        if any(
            keyword.arg == "slots"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in decorator.keywords
        ):
            has_own_slots = True
    return has_own_slots, slots_are_literal, declares_instance_dict


def collect_class_declarations(source_root: Path) -> list[ClassDeclaration]:
    """Recursively collect importable top-level production classes from source."""
    resolved_source_root = source_root.resolve()
    package_root = resolved_source_root / PACKAGE_NAME
    if not package_root.is_dir():
        raise EvidenceError(f"Package directory does not exist: {package_root}")

    declarations: list[ClassDeclaration] = []
    for source_file in sorted(package_root.rglob("*.py")):
        source = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_file))
        module_name = _module_name_for_path(resolved_source_root, source_file)
        occurrences, _ = _walk_module_statements(tree.body, {}, module_name)
        source_path = _normalized_relative_path(
            source_file, resolved_source_root.parent
        )
        for node, import_bindings in occurrences:
            has_own_slots, slots_are_literal, declares_instance_dict = (
                _slots_declaration(node)
            )
            declarations.append(
                ClassDeclaration(
                    qualified_name=f"{module_name}.{node.name}",
                    source_path=source_path,
                    line=node.lineno,
                    base_references=_base_references(
                        node,
                        module_name=module_name,
                        import_bindings=import_bindings,
                    ),
                    has_own_slots=has_own_slots,
                    slots_are_literal=slots_are_literal,
                    declares_instance_dict=declares_instance_dict,
                )
            )
    ordered = sorted(declarations, key=lambda declaration: declaration.qualified_name)
    duplicate_names = sorted(
        {
            declaration.qualified_name
            for declaration in ordered
            if sum(
                item.qualified_name == declaration.qualified_name for item in ordered
            )
            > 1
        }
    )
    if duplicate_names:
        raise EvidenceError(
            "Ambiguous duplicate class definition(s) in slots-policy inventory: "
            + ", ".join(duplicate_names)
        )
    return ordered


def _base_introduces_instance_dict(
    declaration: ClassDeclaration,
    declarations_by_name: Mapping[str, ClassDeclaration],
    visited: set[str] | None = None,
) -> bool:
    """Return whether any base is unsafe or cannot be statically proven safe.

    A subclass must declare its own slots.  Even that is not enough when a
    parent has already introduced an instance dictionary, as the descendant
    cannot remove it. References are resolved against module-qualified
    identities; an external base is unsafe unless it is explicitly proven safe.
    """
    seen = set() if visited is None else visited
    if declaration.qualified_name in seen:
        return True
    next_seen = {*seen, declaration.qualified_name}
    for base_reference in declaration.base_references:
        if base_reference in PROVEN_SAFE_SLOT_BASES:
            continue
        base = declarations_by_name.get(base_reference)
        if base is None:
            return True
        if (
            not base.has_own_slots
            or not base.slots_are_literal
            or base.declares_instance_dict
            or _base_introduces_instance_dict(base, declarations_by_name, next_seen)
        ):
            return True
    return False


def validate_slots_inventory(
    declarations: Iterable[ClassDeclaration],
    registry: Mapping[str, str] = REGISTERED_SLOTS_EXCEPTIONS,
) -> list[dict[str, Any]]:
    """Classify every discovered class or fail on stale/un-slotted entries."""
    ordered_declarations = sorted(declarations, key=lambda item: item.qualified_name)
    declarations_by_name = {
        declaration.qualified_name: declaration for declaration in ordered_declarations
    }
    stale_entries = sorted(set(registry) - set(declarations_by_name))
    if stale_entries:
        raise EvidenceError(
            "Registered slots-policy exception(s) no longer exist in source: "
            + ", ".join(stale_entries)
        )

    inventory: list[dict[str, Any]] = []
    unprotected: list[ClassDeclaration] = []
    for declaration in ordered_declarations:
        entry: dict[str, Any] = {
            "qualified_name": declaration.qualified_name,
            "source_path": declaration.source_path,
            "line": declaration.line,
        }
        exception_reason = registry.get(declaration.qualified_name)
        if exception_reason is not None:
            entry.update(
                classification="registered-exception", exception_reason=exception_reason
            )
        elif not declaration.has_own_slots:
            unprotected.append(declaration)
            continue
        elif not declaration.slots_are_literal:
            unprotected.append(declaration)
            continue
        elif declaration.declares_instance_dict:
            unprotected.append(declaration)
            continue
        elif _base_introduces_instance_dict(declaration, declarations_by_name):
            unprotected.append(declaration)
            continue
        else:
            entry["classification"] = "slot-protected"
        inventory.append(entry)

    if unprotected:
        locations = "\n".join(
            f"  - {item.qualified_name} ({item.source_path}:{item.line})"
            for item in unprotected
        )
        raise EvidenceError(
            "Unregistered instance-__dict__ class(es) in slots-policy inventory:\n"
            + locations
        )
    return inventory


_RUNTIME_AUDIT_DENIED_BUILTINS = frozenset({"exec", "eval", "compile", "__import__"})
_RUNTIME_AUDIT_DENIED_MODULES = frozenset({"ctypes", "inspect"})


def validate_runtime_auditability(source_root: Path) -> None:
    """Reject source that can defeat the isolated runtime-layout audit.

    The layout subprocess deliberately imports selected production source in
    order to inspect CPython class layouts.  That makes dynamic execution and
    frame inspection incompatible with an auditable boundary: they can reach
    the audit runner or manufacture code after the preflight.  Production
    source must therefore remain statically importable while this check is in
    force.  It is intentionally fail-closed rather than trying to sandbox
    Python's reflective execution features.
    """
    package_root = source_root.resolve() / PACKAGE_NAME
    if not package_root.is_dir():
        raise EvidenceError(f"Package directory does not exist: {package_root}")

    for source_path in sorted(package_root.rglob("*.py")):
        try:
            tree = ast.parse(
                source_path.read_text(encoding="utf-8"), filename=str(source_path)
            )
        except (OSError, SyntaxError) as error:
            raise EvidenceError(
                f"Runtime auditability preflight could not parse {source_path}: {error}"
            ) from error
        sys_aliases = {"sys"}
        builtin_aliases = {"builtins"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sys":
                        sys_aliases.add(alias.asname or "sys")
                    elif alias.name == "builtins":
                        builtin_aliases.add(alias.asname or "builtins")
        for node in ast.walk(tree):
            denied: str | None = None
            if isinstance(node, ast.Import):
                if any(
                    alias.name.split(".", 1)[0] in _RUNTIME_AUDIT_DENIED_MODULES
                    for alias in node.names
                ):
                    denied = "frame/native introspection import"
            elif isinstance(node, ast.ImportFrom):
                if (
                    node.module
                    and node.module.split(".", 1)[0] in _RUNTIME_AUDIT_DENIED_MODULES
                ):
                    denied = "frame/native introspection import"
                elif node.module == "sys" and any(
                    alias.name == "_getframe" for alias in node.names
                ):
                    denied = "sys._getframe import"
                elif node.module == "builtins" and any(
                    alias.name in _RUNTIME_AUDIT_DENIED_BUILTINS for alias in node.names
                ):
                    denied = "dynamic execution import"
            elif isinstance(node, ast.Call):
                target = node.func
                if (
                    isinstance(target, ast.Name)
                    and target.id in _RUNTIME_AUDIT_DENIED_BUILTINS
                ):
                    denied = target.id
                elif (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and (
                        (target.value.id in sys_aliases and target.attr == "_getframe")
                        or target.value.id in _RUNTIME_AUDIT_DENIED_MODULES
                        or (
                            target.value.id in builtin_aliases
                            and target.attr in _RUNTIME_AUDIT_DENIED_BUILTINS
                        )
                    )
                ):
                    denied = f"{target.value.id}.{target.attr}"
                elif (
                    isinstance(target, ast.Name)
                    and target.id == "getattr"
                    and len(node.args) >= 2
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in sys_aliases
                    and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value == "_getframe"
                ):
                    denied = "sys._getframe"
                elif (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in {"type", "object"}
                    and target.attr in {"__setattr__", "__delattr__"}
                ):
                    denied = f"{target.value.id}.{target.attr}"
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in sys_aliases
                and node.attr == "_getframe"
            ):
                denied = "sys._getframe"
            if denied is not None:
                relative_path = source_path.relative_to(
                    source_root.resolve()
                ).as_posix()
                line = getattr(node, "lineno", "?")
                raise EvidenceError(
                    "Runtime auditability preflight denied "
                    f"{denied} in {relative_path}:{line}. "
                    "Selected production source may not use dynamic execution or "
                    "audit-state introspection."
                )


_RUNTIME_LAYOUT_AUDIT_SCRIPT = r"""
import abc
import builtins
import collections
import importlib
import importlib.abc
import importlib.metadata
import importlib.util
import json
import sys
import types
import typing
from pathlib import Path


def run_audit(
    source_root_text,
    package_name_text,
    _builtins=builtins,
    _json=json,
    _importlib=importlib,
    _importlib_util=importlib.util,
    _sys=sys,
    _types=types,
    _path=Path,
    _meta_path_finder=importlib.abc.MetaPathFinder,
):
    _AUDIT_BUILTINS = _builtins
    _AUDIT_VARS = _builtins.vars
    _AUDIT_ISINSTANCE = _builtins.isinstance
    _AUDIT_TYPE = _builtins.type
    _AUDIT_GETATTR = _builtins.getattr
    _AUDIT_SORTED = _builtins.sorted
    _AUDIT_TUPLE = _builtins.tuple
    _AUDIT_STR = _builtins.str
    _AUDIT_INT = _builtins.int
    _AUDIT_BOOL = _builtins.bool
    _AUDIT_SET = _builtins.set
    _AUDIT_RUNTIME_ERROR = _builtins.RuntimeError
    _AUDIT_MODULE_NOT_FOUND_ERROR = _builtins.ModuleNotFoundError
    _AUDIT_ATTRIBUTE_ERROR = _builtins.AttributeError
    _AUDIT_TYPE_GETATTRIBUTE = _builtins.type.__getattribute__
    _AUDIT_JSON_DUMPS = _json.dumps
    _AUDIT_IMPORT_MODULE = _importlib.import_module
    _AUDIT_SPEC_FROM_FILE_LOCATION = _importlib_util.spec_from_file_location
    _AUDIT_SYS_MODULES = _sys.modules
    _AUDIT_SYS_META_PATH = _sys.meta_path
    _AUDIT_SYS_PATH = _sys.path
    _AUDIT_SYS_STDOUT_WRITE = _sys.stdout.write
    _AUDIT_MAPPING_PROXY_TYPE = _types.MappingProxyType
    _AUDIT_PATH = _path
    _AUDIT_PATH_RESOLVE = _path.resolve


    def raw_class_attribute(
        cls,
        name,
        _isinstance=_AUDIT_ISINSTANCE,
        _type=_AUDIT_TYPE,
        _type_getattribute=_AUDIT_TYPE_GETATTRIBUTE,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        if not _isinstance(cls, _type):
            raise _runtime_error(f"Runtime layout target is not a class: {cls!r}")
        return _type_getattribute(cls, name)


    def assert_audit_primitive_integrity(
        _vars=_AUDIT_VARS,
        _builtins=_AUDIT_BUILTINS,
        _json=_json,
        _importlib=_importlib,
        _importlib_util=_importlib_util,
        _sys=_sys,
        _types=_types,
        _type=_AUDIT_TYPE,
        _type_getattribute=_AUDIT_TYPE_GETATTRIBUTE,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
        _builtin_bindings=(
            ("vars", _AUDIT_VARS),
            ("isinstance", _AUDIT_ISINSTANCE),
            ("type", _AUDIT_TYPE),
            ("getattr", _AUDIT_GETATTR),
            ("sorted", _AUDIT_SORTED),
            ("tuple", _AUDIT_TUPLE),
            ("str", _AUDIT_STR),
            ("int", _AUDIT_INT),
            ("bool", _AUDIT_BOOL),
            ("set", _AUDIT_SET),
        ),
        _module_bindings=(
            (_json, "dumps", _AUDIT_JSON_DUMPS),
            (_importlib, "import_module", _AUDIT_IMPORT_MODULE),
            (_importlib_util, "spec_from_file_location", _AUDIT_SPEC_FROM_FILE_LOCATION),
            (_sys, "modules", _AUDIT_SYS_MODULES),
            (_sys, "meta_path", _AUDIT_SYS_META_PATH),
            (_sys, "path", _AUDIT_SYS_PATH),
            (_types, "MappingProxyType", _AUDIT_MAPPING_PROXY_TYPE),
        ),
    ):
        builtin_values = _vars(_builtins)
        for name, expected in _builtin_bindings:
            if builtin_values.get(name) is not expected:
                raise _runtime_error(f"Audit primitive integrity changed: builtins.{name}")
        for module, name, expected in _module_bindings:
            if _vars(module).get(name) is not expected:
                raise _runtime_error(
                    f"Audit primitive integrity changed: {module.__name__}.{name}"
                )
        if _type_getattribute(_type, "__getattribute__") is not _type_getattribute:
            raise _runtime_error("Audit primitive integrity changed: type.__getattribute__")


    source_root = _AUDIT_PATH(source_root_text).resolve()
    package_name = package_name_text
    package_root = source_root / package_name
    if not package_root.is_dir():
        raise RuntimeError(f"Package directory does not exist: {package_root}")
    if _sys.implementation.name != "cpython":
        raise RuntimeError("Runtime slots layout audit requires CPython")

    _AUDIT_SYS_PATH.insert(0, _AUDIT_STR(source_root))
    _importlib.invalidate_caches()

    allowed_modules = {}
    for source_file in package_root.rglob("*.py"):
        resolved = source_file.resolve()
        try:
            resolved.relative_to(source_root)
        except ValueError as error:
            raise RuntimeError(f"Selected source escaped source root: {source_file}") from error
        parts = list(resolved.relative_to(source_root).with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        module_name = ".".join(parts)
        if module_name != package_name and not module_name.startswith(package_name + "."):
            raise RuntimeError(f"Selected source is outside project namespace: {resolved}")
        previous = allowed_modules.get(module_name)
        if previous is not None and previous != (resolved, is_package):
            raise RuntimeError(f"Ambiguous selected source module: {module_name}")
        allowed_modules[module_name] = (resolved, is_package)
    if package_name not in allowed_modules or not allowed_modules[package_name][1]:
        raise RuntimeError(f"Selected source is missing package initializer: {package_name}")

    def make_pure_source_finder(
        allowed,
        _mapping_proxy=_AUDIT_MAPPING_PROXY_TYPE,
        _spec_from_file_location=_AUDIT_SPEC_FROM_FILE_LOCATION,
        _module_not_found_error=_AUDIT_MODULE_NOT_FOUND_ERROR,
        _to_str=_AUDIT_STR,
        _base=_meta_path_finder,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        # Policy is a closure-held mapping proxy, not finder state.  Selected
        # code can inspect meta_path but cannot extend the selected source set.
        allowed_snapshot = _mapping_proxy(dict(allowed))

        class FrozenFinderType(_AUDIT_TYPE(_base)):
            __slots__ = ()

            def __new__(metaclass, name, bases, namespace, **kwargs):
                namespace["_audit_finder_frozen"] = False
                cls = super().__new__(metaclass, name, bases, namespace, **kwargs)
                _AUDIT_TYPE.__setattr__(cls, "_audit_finder_frozen", True)
                return cls

            def __setattr__(cls, name, value):
                if _AUDIT_TYPE_GETATTRIBUTE(cls, "__dict__").get(
                    "_audit_finder_frozen", False
                ):
                    raise _runtime_error("Pure source finder class is immutable")
                return super().__setattr__(name, value)

            def __delattr__(cls, name):
                if _AUDIT_TYPE_GETATTRIBUTE(cls, "__dict__").get(
                    "_audit_finder_frozen", False
                ):
                    raise _runtime_error("Pure source finder class is immutable")
                return super().__delattr__(name)

        class PureSourceFinder(_base, metaclass=FrozenFinderType):
            __slots__ = ()

            def __setattr__(self, name, value):
                raise _runtime_error("Pure source finder is immutable")

            def __delattr__(self, name):
                raise _runtime_error("Pure source finder is immutable")

            def find_spec(self, fullname, path=None, target=None):
                if fullname != package_name and not fullname.startswith(package_name + "."):
                    return None
                source = allowed_snapshot.get(fullname)
                if source is None:
                    raise _module_not_found_error(
                        f"Pure source audit denied unselected project import: {fullname}",
                        name=fullname,
                    )
                source_file, is_package = source
                if is_package:
                    return _spec_from_file_location(
                        fullname,
                        source_file,
                        submodule_search_locations=[_to_str(source_file.parent)],
                    )
                return _spec_from_file_location(fullname, source_file)

        return PureSourceFinder(), allowed_snapshot

    finder, allowed_module_snapshot = make_pure_source_finder(allowed_modules)
    _AUDIT_SYS_META_PATH.insert(0, finder)
    _AUDIT_SYS_PATH_ENTRIES = _AUDIT_TUPLE(_AUDIT_SYS_PATH)
    _AUDIT_SYS_META_PATH_ENTRIES = _AUDIT_TUPLE(_AUDIT_SYS_META_PATH)

    for module_key in _AUDIT_TUPLE(_AUDIT_SYS_MODULES):
        if module_key == package_name or module_key.startswith(package_name + "."):
            raise RuntimeError(f"Selected project module was loaded before audit: {module_key}")

    external_module_records = {}
    external_class_records = {}

    def snapshot_external_class(module_key, binding_name, cls):
        claimed_module_name = raw_class_attribute(cls, "__module__")
        qualname = raw_class_attribute(cls, "__qualname__")
        if claimed_module_name != module_key:
            return
        if not _AUDIT_ISINSTANCE(qualname, _AUDIT_STR) or not qualname or "<locals>" in qualname:
            raise RuntimeError(
                f"Pre-execution external class has an uncertain qualified name: "
                f"{module_key}.{qualname!r}"
            )
        identity_key = (module_key, qualname)
        previous = external_class_records.get(identity_key)
        if previous is not None and previous[0] is not cls:
            raise RuntimeError(
                f"Ambiguous pre-execution external class identity: "
                f"{module_key}.{qualname}"
            )
        if previous is None:
            external_class_records[identity_key] = (cls, binding_name)


    for module_key in ("abc", "builtins", "collections", "importlib.metadata", "typing"):
        module = _AUDIT_SYS_MODULES.get(module_key)
        if module is None:
            raise RuntimeError(
                f"Required pre-execution external module is unavailable: {module_key}"
            )
        spec = _AUDIT_GETATTR(module, "__spec__", None)
        if _AUDIT_GETATTR(spec, "name", None) != module_key:
            raise RuntimeError(
                f"Required pre-execution external module has uncertain identity: "
                f"{module_key}"
            )
        external_module_records[module_key] = (module, spec)
        for binding_name, value in _AUDIT_VARS(module).items():
            if _AUDIT_ISINSTANCE(value, _AUDIT_TYPE):
                snapshot_external_class(module_key, binding_name, value)

    external_module_snapshot = _AUDIT_MAPPING_PROXY_TYPE(dict(external_module_records))
    external_class_snapshot = _AUDIT_MAPPING_PROXY_TYPE(dict(external_class_records))


    def assert_external_snapshot_integrity(
        external_modules=external_module_snapshot,
        external_classes=external_class_snapshot,
        _vars=_AUDIT_VARS,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        for (module_key, qualname), (expected, binding_name) in external_classes.items():
            module, _ = external_modules[module_key]
            if _vars(module).get(binding_name) is not expected:
                raise _runtime_error(
                    f"Pre-execution external class binding changed: {module_key}.{qualname}"
                )


    def assert_audit_import_state(
        _assert_primitives=assert_audit_primitive_integrity,
        _tuple=_AUDIT_TUPLE,
        _sys_path=_AUDIT_SYS_PATH,
        _sys_meta_path=_AUDIT_SYS_META_PATH,
        _expected_path_entries=_AUDIT_SYS_PATH_ENTRIES,
        _expected_meta_path_entries=_AUDIT_SYS_META_PATH_ENTRIES,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        _assert_primitives()
        if _tuple(_sys_path) != _expected_path_entries:
            raise _runtime_error("Audit import path changed after selected source execution")
        if _tuple(_sys_meta_path) != _expected_meta_path_entries:
            raise _runtime_error("Audit meta path changed after selected source execution")

    module_names = sorted(
        allowed_modules,
        key=lambda name: (name.count("."), name),
    )
    modules = {}

    def assert_selected_module_identity(
        module_key,
        module,
        _sys_modules=_AUDIT_SYS_MODULES,
        _getattr=_AUDIT_GETATTR,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        if _sys_modules.get(module_key) is not module:
            raise _runtime_error(f"Selected module binding changed: {module_key}")
        if _getattr(module, "__name__", None) != module_key:
            raise _runtime_error(f"Selected module identity changed: {module_key}")
        spec = _getattr(module, "__spec__", None)
        if _getattr(spec, "name", None) != module_key:
            raise _runtime_error(f"Selected module spec identity changed: {module_key}")


    for module_key in module_names:
        assert_audit_import_state()
        module = _AUDIT_IMPORT_MODULE(module_key)
        assert_audit_import_state()
        assert_selected_module_identity(module_key, module)
        origin_text = _AUDIT_GETATTR(module, "__file__", None)
        if not origin_text:
            raise RuntimeError(f"Imported module has no source origin: {module_key}")
        origin = _AUDIT_PATH_RESOLVE(_AUDIT_PATH(origin_text))
        try:
            origin.relative_to(source_root)
        except ValueError as error:
            raise RuntimeError(
                f"Imported module escaped selected source root: {module_key} -> {origin}"
            ) from error
        if origin.suffix != ".py":
            raise RuntimeError(f"Imported module is not pure Python: {module_key} -> {origin}")
        expected_origin, _ = allowed_modules[module_key]
        if origin != expected_origin:
            raise RuntimeError(
                f"Imported module did not use selected source: {module_key} -> {origin}"
            )
        modules[module_key] = module

    for module_key, module in modules.items():
        assert_audit_import_state()
        assert_selected_module_identity(module_key, module)

    assert_external_snapshot_integrity()

    for module_name, module in _AUDIT_SORTED(_AUDIT_TUPLE(_AUDIT_SYS_MODULES.items())):
        if module_name != package_name and not module_name.startswith(package_name + "."):
            continue
        source = allowed_modules.get(module_name)
        if source is None:
            raise RuntimeError(f"Loaded unselected project module: {module_name}")
        origin_text = _AUDIT_GETATTR(module, "__file__", None)
        if not origin_text:
            raise RuntimeError(f"Loaded project module has no source origin: {module_name}")
        origin = _AUDIT_PATH_RESOLVE(_AUDIT_PATH(origin_text))
        expected_origin, _ = source
        if origin != expected_origin or origin.suffix != ".py":
            raise RuntimeError(
                f"Loaded project module did not use allowed selected .py source: "
                f"{module_name} -> {origin}"
            )

    layouts = {}
    seen = _AUDIT_SET()

    def resolve_class_qualname(
        module,
        module_key,
        qualname,
        binding_name,
        _getattr=_AUDIT_GETATTR,
        _attribute_error=_AUDIT_ATTRIBUTE_ERROR,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        resolved = module
        for component in qualname.split("."):
            try:
                resolved = _getattr(resolved, component)
            except _attribute_error as error:
                raise _runtime_error(
                    f"Runtime type has an unresolvable claimed owner: {binding_name} -> "
                    f"{module_key}.{qualname}"
                ) from error
        return resolved


    def verify_external_reexport(
        cls,
        binding_name,
        external_modules=external_module_snapshot,
        external_classes=external_class_snapshot,
        _raw_class_attribute=raw_class_attribute,
        _isinstance=_AUDIT_ISINSTANCE,
        _str=_AUDIT_STR,
        _getattr=_AUDIT_GETATTR,
        _sys_modules=_AUDIT_SYS_MODULES,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        claimed_module_name = _raw_class_attribute(cls, "__module__")
        qualname = _raw_class_attribute(cls, "__qualname__")
        if not _isinstance(claimed_module_name, _str) or not claimed_module_name:
            raise _runtime_error(
                f"Runtime type has an uncertain claimed owner: {binding_name}"
            )
        if not _isinstance(qualname, _str) or not qualname or "<locals>" in qualname:
            raise _runtime_error(
                f"Runtime type has an uncertain qualified name: {binding_name}"
            )
        record = external_modules.get(claimed_module_name)
        if record is None:
            raise _runtime_error(
                f"Runtime type has no pre-execution external module provenance: "
                f"{binding_name} -> "
                f"{claimed_module_name}.{qualname}"
            )
        claimed_module, claimed_spec = record
        if _sys_modules.get(claimed_module_name) is not claimed_module:
            raise _runtime_error(
                f"Runtime type external module binding changed: {binding_name} -> "
                f"{claimed_module_name}.{qualname}"
            )
        if (
            _getattr(claimed_module, "__name__", None) != claimed_module_name
            or _getattr(claimed_module, "__spec__", None) is not claimed_spec
            or _getattr(claimed_spec, "name", None) != claimed_module_name
        ):
            raise _runtime_error(
                f"Runtime type external module identity changed: {binding_name} -> "
                f"{claimed_module_name}.{qualname}"
            )
        expected_record = external_classes.get((claimed_module_name, qualname))
        if expected_record is None:
            raise _runtime_error(
                f"Runtime type has no pre-execution external class provenance: "
                f"{binding_name} -> {claimed_module_name}.{qualname}"
            )
        expected, _ = expected_record
        if expected is not cls:
            raise _runtime_error(
                f"Runtime type has mismatched pre-execution external provenance: "
                f"{binding_name} -> "
                f"{claimed_module_name}.{qualname}"
            )


    def collect_class(
        cls,
        module_key,
        binding_name,
        _raw_class_attribute=raw_class_attribute,
        _isinstance=_AUDIT_ISINSTANCE,
        _str=_AUDIT_STR,
        _bool=_AUDIT_BOOL,
        _int=_AUDIT_INT,
        _vars=_AUDIT_VARS,
        _type=_AUDIT_TYPE,
        _runtime_error=_AUDIT_RUNTIME_ERROR,
    ):
        claimed_module_name = _raw_class_attribute(cls, "__module__")
        if claimed_module_name != module_key:
            if claimed_module_name in allowed_modules:
                claimed_module = modules.get(claimed_module_name)
                if claimed_module is None:
                    raise _runtime_error(
                        f"Runtime type has an unavailable selected owner: {binding_name} -> "
                        f"{claimed_module_name}"
                    )
                assert_selected_module_identity(claimed_module_name, claimed_module)
                qualname = _raw_class_attribute(cls, "__qualname__")
                if not _isinstance(qualname, _str) or not qualname or "<locals>" in qualname:
                    raise _runtime_error(
                        f"Runtime type has an uncertain qualified name: {binding_name}"
                    )
                if (
                    resolve_class_qualname(
                        claimed_module, claimed_module_name, qualname, binding_name
                    )
                    is not cls
                ):
                    raise _runtime_error(
                        f"Runtime type has a mismatched selected owner: {binding_name} -> "
                        f"{claimed_module_name}.{qualname}"
                    )
                return
            verify_external_reexport(cls, binding_name)
            return
        if cls in seen:
            return
        seen.add(cls)
        qualname = _raw_class_attribute(cls, "__qualname__")
        if not _isinstance(qualname, _str) or not qualname or "<locals>" in qualname:
            raise _runtime_error(f"Runtime class has an uncertain qualified name: {cls!r}")
        dictoffset = _raw_class_attribute(cls, "__dictoffset__")
        if _isinstance(dictoffset, _bool) or not _isinstance(dictoffset, _int):
            raise _runtime_error(
                f"Runtime class has an uncertain CPython dictionary layout: "
                f"{module_key}.{qualname}"
            )
        qualified_name = f"{module_key}.{qualname}"
        previous = layouts.get(qualified_name)
        layout = {
            "qualified_name": qualified_name,
            "has_instance_dict": dictoffset != 0,
            "dictoffset": dictoffset,
        }
        if previous is not None and previous != layout:
            raise _runtime_error(f"Ambiguous runtime class layout: {qualified_name}")
        layouts[qualified_name] = layout
        for attribute_name, value in _raw_class_attribute(cls, "__dict__").items():
            if _isinstance(value, _type):
                collect_class(value, module_key, f"{binding_name}.{attribute_name}")

    for module_key, module in modules.items():
        for binding_name, value in _AUDIT_VARS(module).items():
            if _AUDIT_ISINSTANCE(value, _AUDIT_TYPE):
                collect_class(value, module_key, f"{module_key}.{binding_name}")

    _AUDIT_SYS_STDOUT_WRITE(
        _AUDIT_JSON_DUMPS(
            [layouts[name] for name in _AUDIT_SORTED(layouts)], sort_keys=True
        )
        + "\n"
    )


run_audit(sys.argv[1], sys.argv[2])
"""


def _stage_runtime_audit_source(source_root: Path, staged_root: Path) -> None:
    """Copy exactly selected Python source into a fresh subprocess source root."""
    resolved_source_root = source_root.resolve()
    package_root = resolved_source_root / PACKAGE_NAME
    for source_path in sorted(package_root.rglob("*.py")):
        resolved_source_path = source_path.resolve()
        try:
            relative_path = resolved_source_path.relative_to(resolved_source_root)
        except ValueError as error:
            raise EvidenceError(
                f"Selected source escaped source root: {source_path}"
            ) from error
        destination = staged_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resolved_source_path, destination)


def collect_runtime_class_layouts(source_root: Path) -> list[dict[str, Any]]:
    """Load a freshly staged selected ``.py`` tree and report CPython layouts."""
    resolved_source_root = source_root.resolve()
    package_root = resolved_source_root / PACKAGE_NAME
    if not package_root.is_dir():
        raise EvidenceError(f"Package directory does not exist: {package_root}")
    validate_runtime_auditability(resolved_source_root)
    with tempfile.TemporaryDirectory(prefix="fast-fsm-runtime-layout-") as temporary:
        staged_source_root = Path(temporary) / "source"
        _stage_runtime_audit_source(resolved_source_root, staged_source_root)
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                _RUNTIME_LAYOUT_AUDIT_SCRIPT,
                str(staged_source_root),
                PACKAGE_NAME,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    if completed.returncode:
        raise EvidenceError(
            "Isolated runtime slots audit failed:\n" + completed.stderr.strip()
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise EvidenceError("Runtime slots audit did not emit valid JSON.") from error
    if not isinstance(payload, list):
        raise EvidenceError("Runtime slots audit did not emit a class-layout list.")
    layouts: list[dict[str, Any]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise EvidenceError("Runtime slots audit emitted a malformed class layout.")
        qualified_name = entry.get("qualified_name")
        has_instance_dict = entry.get("has_instance_dict")
        dictoffset = entry.get("dictoffset")
        if (
            not isinstance(qualified_name, str)
            or not qualified_name.startswith(f"{PACKAGE_NAME}.")
            or not isinstance(has_instance_dict, bool)
            or isinstance(dictoffset, bool)
            or not isinstance(dictoffset, int)
        ):
            raise EvidenceError(
                "Runtime slots audit emitted an uncertain class layout."
            )
        layouts.append(
            {
                "qualified_name": qualified_name,
                "has_instance_dict": has_instance_dict,
                "dictoffset": dictoffset,
            }
        )
    if [entry["qualified_name"] for entry in layouts] != sorted(
        entry["qualified_name"] for entry in layouts
    ):
        raise EvidenceError(
            "Runtime slots audit emitted a non-deterministic layout order."
        )
    if len({entry["qualified_name"] for entry in layouts}) != len(layouts):
        raise EvidenceError("Runtime slots audit emitted duplicate class layouts.")
    return layouts


def validate_runtime_slots_layouts(
    declarations: Iterable[ClassDeclaration],
    source_root: Path,
    registry: Mapping[str, str] = REGISTERED_SLOTS_EXCEPTIONS,
) -> list[dict[str, Any]]:
    """Reconcile static classes with isolated actual layouts and fail closed."""
    static_names = {declaration.qualified_name for declaration in declarations}
    layouts = collect_runtime_class_layouts(source_root)
    runtime_names = {str(entry["qualified_name"]) for entry in layouts}
    missing_runtime = sorted(static_names - runtime_names)
    extra_runtime = sorted(runtime_names - static_names)
    if missing_runtime or extra_runtime:
        details: list[str] = []
        if missing_runtime:
            details.append("missing runtime: " + ", ".join(missing_runtime))
        if extra_runtime:
            details.append("extra runtime: " + ", ".join(extra_runtime))
        raise EvidenceError(
            "Static and runtime slots-policy inventories do not reconcile: "
            + "; ".join(details)
        )
    unexpected_dict = sorted(
        str(entry["qualified_name"])
        for entry in layouts
        if entry["has_instance_dict"] and entry["qualified_name"] not in registry
    )
    if unexpected_dict:
        raise EvidenceError(
            "Unregistered runtime instance-__dict__ class(es) in slots-policy "
            "inventory: " + ", ".join(unexpected_dict)
        )
    return layouts


def _measure_instance(instance: object) -> dict[str, Any]:
    """Return deliberate, environment-labeled instance memory evidence."""
    return {
        "has_instance_dict": hasattr(instance, "__dict__"),
        "instance_size_bytes": sys.getsizeof(instance),
    }


def _slots_measurements(
    source_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Instantiate registered and representative classes without exposing internals."""
    source_root_text = str(source_root.resolve())
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)
    importlib.invalidate_caches()
    core = importlib.import_module(CORE_MODULE_NAME)
    diagnostics = importlib.import_module("fast_fsm._diagnostics")

    registered_instances = {
        "fast_fsm.conditions.CompiledFuncCondition": core.CompiledFuncCondition(
            lambda **_kwargs: True
        ),
        "fast_fsm.core.TransitionError": core.TransitionError(
            core.TransitionResult(False)
        ),
        "fast_fsm._diagnostics.DiagnosticBudgetExceeded": (
            diagnostics.DiagnosticBudgetExceeded(
                diagnostics.DiagnosticStatus(True, None, None, 0, 0, 0, 0)
            )
        ),
    }
    registered = [
        {
            "qualified_name": qualified_name,
            "exception_reason": REGISTERED_SLOTS_EXCEPTIONS[qualified_name],
            **_measure_instance(instance),
        }
        for qualified_name, instance in sorted(registered_instances.items())
    ]
    representatives = [
        {
            "qualified_name": "fast_fsm.core.State",
            **_measure_instance(core.State("slots-policy")),
        },
        {
            "qualified_name": "fast_fsm.core.TransitionResult",
            **_measure_instance(core.TransitionResult(True)),
        },
    ]
    return registered, representatives


def slots_policy(source_root: Path | None = None) -> dict[str, Any]:
    """Produce a complete static, runtime-verified slots-policy inventory."""
    resolved_source_root = (source_root or REPOSITORY_ROOT / "src").resolve()
    declarations = collect_class_declarations(resolved_source_root)
    inventory = validate_slots_inventory(declarations)
    runtime_layouts = validate_runtime_slots_layouts(declarations, resolved_source_root)
    registered, representatives = _slots_measurements(resolved_source_root)
    return {
        "inventory": inventory,
        "runtime_layouts": runtime_layouts,
        "registered_exceptions": registered,
        "representative_measurements": representatives,
        "measurement_environment": {
            "implementation": sys.implementation.name,
            "python_version": sys.version.split()[0],
        },
    }


def serialize_manifest(manifest: Mapping[str, Any]) -> str:
    """Render evidence as one stable JSON document with exactly one newline."""
    return (
        json.dumps(
            manifest, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False
        )
        + "\n"
    )


def _render_field_value(value: Any) -> str:
    """Make a compact, deterministic field-level diff value."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def _python_major_minor(version: Any) -> str:
    """Return a fail-closed major.minor identity from an exact Python version."""
    if not isinstance(version, str):
        raise EvidenceError("Manifest has malformed toolchain.python identity.")
    components = version.split(".")
    if len(components) != 3 or not all(component.isdigit() for component in components):
        raise EvidenceError("Manifest has malformed toolchain.python identity.")
    return f"{int(components[0])}.{int(components[1])}"


def _ordered_layout_names(entries: Any, *, path: str) -> list[str]:
    """Validate a deterministically ordered qualified-name evidence list."""
    if not isinstance(entries, list):
        raise EvidenceError(f"Manifest {path} must be a list.")
    names: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(
            entry.get("qualified_name"), str
        ):
            raise EvidenceError(
                f"Manifest {path} contains an entry without a qualified_name."
            )
        names.append(str(entry["qualified_name"]))
    if names != sorted(names):
        raise EvidenceError(f"Manifest {path} must be sorted by qualified_name.")
    if len(set(names)) != len(names):
        raise EvidenceError(
            f"Manifest {path} contains duplicate qualified_name entries."
        )
    return names


def _normalize_runtime_layouts_for_comparison(slots: dict[str, Any]) -> None:
    """Validate runtime layout evidence and remove only host-specific offsets."""
    static_names = _ordered_layout_names(
        slots.get("inventory"), path="slots_policy.inventory"
    )
    registry_names = _ordered_layout_names(
        slots.get("registered_exceptions"),
        path="slots_policy.registered_exceptions",
    )
    layouts = slots.get("runtime_layouts")
    runtime_names = _ordered_layout_names(layouts, path="slots_policy.runtime_layouts")
    if static_names != runtime_names:
        missing = sorted(set(static_names) - set(runtime_names))
        extra = sorted(set(runtime_names) - set(static_names))
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra " + ", ".join(extra))
        raise EvidenceError(
            "Manifest slots_policy.runtime_layouts does not reconcile with "
            "slots_policy.inventory: " + "; ".join(details)
        )
    if not set(registry_names) <= set(static_names):
        stale = sorted(set(registry_names) - set(static_names))
        raise EvidenceError(
            "Manifest slots_policy.registered_exceptions has entries absent from "
            "slots_policy.inventory: " + ", ".join(stale)
        )
    normalized_layouts: list[dict[str, Any]] = []
    for entry in cast(list[Mapping[str, Any]], layouts):
        qualified_name = str(entry["qualified_name"])
        has_instance_dict = entry.get("has_instance_dict")
        dictoffset = entry.get("dictoffset")
        if not isinstance(has_instance_dict, bool):
            raise EvidenceError(
                "Manifest slots_policy.runtime_layouts has a non-boolean "
                f"has_instance_dict for {qualified_name}."
            )
        if isinstance(dictoffset, bool) or not isinstance(dictoffset, int):
            raise EvidenceError(
                "Manifest slots_policy.runtime_layouts has an invalid dictoffset for "
                f"{qualified_name}."
            )
        if has_instance_dict != (dictoffset != 0):
            raise EvidenceError(
                "Manifest slots_policy.runtime_layouts has contradictory dictionary "
                f"layout evidence for {qualified_name}."
            )
        if has_instance_dict != (qualified_name in registry_names):
            expectation = "registered" if has_instance_dict else "not registered"
            raise EvidenceError(
                "Manifest slots_policy.runtime_layouts has registry-inconsistent "
                f"dictionary evidence for {qualified_name}: expected {expectation}."
            )
        normalized_layouts.append(
            {
                "qualified_name": qualified_name,
                "has_instance_dict": has_instance_dict,
            }
        )
    slots["runtime_layouts"] = normalized_layouts


def _stable_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return fields whose equality defines evidence freshness.

    Platform/runtime observations are retained for audit context, but a different
    runner must not churn a stable release baseline merely because its host or
    timing characteristics differ.
    """
    stable = json.loads(serialize_manifest(manifest))
    stable.pop("measurement_environment", None)
    toolchain = stable.get("toolchain")
    if isinstance(toolchain, dict) and "python" in toolchain:
        toolchain["python"] = _python_major_minor(toolchain["python"])
    performance_contract = stable.get("performance_contract")
    if isinstance(performance_contract, dict):
        performance_contract.pop("observation", None)
    slots = stable.get("slots_policy")
    if isinstance(slots, dict):
        _normalize_runtime_layouts_for_comparison(slots)
    return stable


def compare_manifests(
    expected: Mapping[str, Any], observed: Mapping[str, Any]
) -> list[str]:
    """Return deterministic, actionable stable-field differences.

    Lists deliberately compare as whole values. Their members are evidence
    collections whose deterministic sort order is part of the release contract.
    """
    differences: list[str] = []

    def compare(expected_value: Any, observed_value: Any, path: str) -> None:
        if isinstance(expected_value, Mapping) and isinstance(observed_value, Mapping):
            for key in sorted(set(expected_value) | set(observed_value)):
                key_path = f"{path}.{key}" if path else str(key)
                if key not in expected_value:
                    differences.append(
                        f"{key_path}: expected <missing>, observed "
                        f"{_render_field_value(observed_value[key])}"
                    )
                elif key not in observed_value:
                    differences.append(
                        f"{key_path}: expected {_render_field_value(expected_value[key])}, "
                        "observed <missing>"
                    )
                else:
                    compare(expected_value[key], observed_value[key], key_path)
            return
        if expected_value != observed_value:
            differences.append(
                f"{path}: expected {_render_field_value(expected_value)}, observed "
                f"{_render_field_value(observed_value)}"
            )

    compare(_stable_manifest(expected), _stable_manifest(observed), "")
    return differences


def validate_manifest_regressions(
    baseline: Mapping[str, Any], observed: Mapping[str, Any]
) -> None:
    """Reject source-coverage regressions before considering baseline freshness."""
    try:
        baseline_coverage = baseline["quality_baseline"]["coverage"]
        observed_coverage = observed["quality_baseline"]["coverage"]
    except (KeyError, TypeError) as error:
        raise EvidenceError("Manifest is missing quality_baseline.coverage.") from error

    for field in ("total_percent", "core_percent"):
        try:
            expected_value = round(float(baseline_coverage[field]), 2)
            observed_value = round(float(observed_coverage[field]), 2)
        except (KeyError, TypeError, ValueError) as error:
            raise EvidenceError(
                f"Manifest is missing numeric quality_baseline.coverage.{field}."
            ) from error
        if observed_value < expected_value:
            raise EvidenceError(
                f"coverage regression at quality_baseline.coverage.{field}: "
                f"expected at least {expected_value:.2f}, observed {observed_value:.2f}"
            )


def validate_performance_observation(manifest: Mapping[str, Any]) -> None:
    """Require one complete, positive, environment-labeled benchmark observation."""
    try:
        observation = manifest["performance_contract"]["observation"]
    except (KeyError, TypeError) as error:
        raise EvidenceError(
            "Manifest is missing performance_contract.observation."
        ) from error
    if not isinstance(observation, Mapping):
        raise EvidenceError("Manifest performance observation must be an object.")
    try:
        command = observation["command"]
        mode = observation["mode"]
        metric = observation["metric"]
        operations = observation["operations"]
        warmup_operations = observation["warmup_operations"]
        elapsed_seconds = observation["elapsed_seconds"]
        ops_per_second = observation["ops_per_second"]
        environment = observation["environment"]
    except KeyError as error:
        raise EvidenceError("Manifest performance observation is malformed.") from error
    if not all(isinstance(value, str) and value for value in (command, mode, metric)):
        raise EvidenceError(
            "Manifest performance observation requires non-empty command, mode, and metric."
        )
    if mode != "pure":
        raise EvidenceError(
            f"Manifest performance observation must record pure mode, got {mode!r}."
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (operations, warmup_operations)
    ):
        raise EvidenceError(
            "Manifest performance observation requires integer operation counts."
        )
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in (elapsed_seconds, ops_per_second)
    ):
        raise EvidenceError(
            "Manifest performance observation requires finite positive measurements."
        )
    try:
        numeric_operations = float(operations)
        numeric_elapsed_seconds = float(elapsed_seconds)
        numeric_ops_per_second = float(ops_per_second)
        expected_rate = numeric_operations / numeric_elapsed_seconds
    except (OverflowError, ValueError, ZeroDivisionError) as error:
        raise EvidenceError(
            "Manifest performance observation requires finite positive measurements."
        ) from error
    if not all(
        math.isfinite(value)
        for value in (
            numeric_operations,
            numeric_elapsed_seconds,
            numeric_ops_per_second,
            expected_rate,
        )
    ):
        raise EvidenceError(
            "Manifest performance observation requires finite positive measurements."
        )
    if (
        operations <= 0
        or warmup_operations < 0
        or elapsed_seconds <= 0
        or ops_per_second <= 0
    ):
        raise EvidenceError(
            "Manifest performance observation requires positive measurements."
        )
    if not math.isclose(numeric_ops_per_second, expected_rate, rel_tol=0.02):
        raise EvidenceError(
            "Manifest performance observation ops_per_second contradicts operations/elapsed_seconds."
        )
    if not isinstance(environment, Mapping) or not all(
        isinstance(environment.get(field), str) and environment[field]
        for field in ("implementation", "python_version", "platform", "machine")
    ):
        raise EvidenceError(
            "Manifest performance observation requires a complete environment label."
        )


def _command_environment() -> dict[str, str]:
    """Force pure mode without leaking ambient environment into evidence."""
    environment = dict(os.environ)
    environment["FAST_FSM_BUILD_MODE"] = "pure"
    environment.pop("FAST_FSM_PURE_PYTHON", None)
    return environment


def _run_checked(
    arguments: Sequence[str], *, cwd: Path, environment: Mapping[str, str]
) -> str:
    """Run one controlled evidence command with argument-array safety."""
    completed = subprocess.run(
        list(arguments),
        cwd=cwd,
        env=dict(environment),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        rendered = " ".join(arguments)
        output = "\n".join(
            part
            for part in (completed.stdout.strip(), completed.stderr.strip())
            if part
        )
        raise EvidenceError(
            f"Evidence subprocess failed ({completed.returncode}): {rendered}\n{output}"
        )
    return completed.stdout


def _parse_junit_results(junit_path: Path) -> dict[str, int]:
    """Parse exact pytest outcomes from JUnit XML rather than console text."""
    try:
        root = ElementTree.parse(junit_path).getroot()
    except (ElementTree.ParseError, OSError) as error:
        raise EvidenceError(
            f"Could not parse pytest JUnit XML: {junit_path}"
        ) from error

    suites = [
        suite
        for suite in root.iter("testsuite")
        if not any(child.tag == "testsuite" for child in suite)
    ]
    if not suites:
        raise EvidenceError("JUnit XML contained no leaf testsuite results.")

    def total(attribute: str) -> int:
        try:
            return sum(int(suite.attrib.get(attribute, "0")) for suite in suites)
        except ValueError as error:
            raise EvidenceError(
                f"JUnit XML has invalid {attribute!r} count."
            ) from error

    collected = total("tests")
    failures = total("failures")
    errors = total("errors")
    skipped = total("skipped")
    passed = collected - failures - errors - skipped
    if collected <= 0 or passed < 0:
        raise EvidenceError("JUnit XML reported inconsistent test outcome counts.")
    return {
        "collected": collected,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
    }


def _coverage_percentages(coverage_path: Path) -> dict[str, float]:
    """Read rounded total and core.py source coverage from pytest-cov JSON."""
    try:
        payload = json.loads(coverage_path.read_text(encoding="utf-8"))
        total_percent = float(payload["totals"]["percent_covered"])
        core_entry = next(
            entry
            for source_path, entry in payload["files"].items()
            if Path(source_path).as_posix().endswith("src/fast_fsm/core.py")
        )
        core_percent = float(core_entry["summary"]["percent_covered"])
    except (KeyError, OSError, StopIteration, TypeError, ValueError) as error:
        raise EvidenceError(
            "Coverage JSON is missing total or src/fast_fsm/core.py source coverage."
        ) from error
    return {
        "total_percent": round(total_percent, 2),
        "core_percent": round(core_percent, 2),
    }


def _distribution_version(distribution: str) -> str:
    """Read one resolved package version with a useful missing-tool error."""
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError as error:
        raise EvidenceError(
            f"Required evidence tool {distribution!r} is not installed in the locked environment."
        ) from error


def _locked_package_version(package_name: str, lock_path: Path | None = None) -> str:
    """Read one resolved package version from uv.lock without a runtime import.

    Build-system requirements are installed in uv's isolated build environment,
    not necessarily in the project environment.  Their evidence must therefore
    come from the reviewed lock instead of turning a build tool into a runtime
    dependency merely to ask it for ``__version__``.
    """
    path = lock_path or REPOSITORY_ROOT / "uv.lock"
    try:
        sections = path.read_text(encoding="utf-8").split("[[package]]")
    except OSError as error:
        raise EvidenceError(f"Could not read resolved lock file {path}.") from error
    name_marker = f'name = "{package_name}"'
    for section in sections[1:]:
        section_lines = [line for line in section.splitlines() if line]
        if not section_lines or section_lines[0] != name_marker:
            continue
        for line in section_lines:
            if line.startswith("version = "):
                return line.split('"', 2)[1]
    raise EvidenceError(f"Resolved package {package_name!r} is missing from {path}.")


def _resolved_uv_version(*, environment: Mapping[str, str]) -> str:
    """Return and validate the exact uv executable version for this phase."""
    stdout = _run_checked(
        ["uv", "--version"], cwd=REPOSITORY_ROOT, environment=environment
    )
    parts = stdout.strip().split()
    if len(parts) < 2 or parts[0] != "uv":
        raise EvidenceError(f"Could not parse uv version output: {stdout!r}")
    version = parts[1]
    if version != REQUIRED_UV_VERSION:
        raise EvidenceError(
            f"Release evidence requires uv {REQUIRED_UV_VERSION}, resolved {version}."
        )
    return version


def _source_preflight(
    *, source_root: Path, environment: Mapping[str, str]
) -> dict[str, str]:
    """Run the native-shadow/source-origin proof before any collection command."""
    output = _run_checked(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "verify-source",
            "--source-root",
            str(source_root),
            "--json",
        ],
        cwd=REPOSITORY_ROOT,
        environment=environment,
    )
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise EvidenceError(
            "Source preflight did not emit valid JSON evidence."
        ) from error
    if not str(payload.get("core_origin", "")).endswith(".py"):
        raise EvidenceError("Source preflight did not prove a core.py module origin.")
    return {str(key): str(value) for key, value in payload.items()}


def _collect_test_and_coverage(
    *, environment: Mapping[str, str]
) -> tuple[dict[str, int], dict[str, float]]:
    """Collect test and coverage facts only after source preflight succeeded."""
    with tempfile.TemporaryDirectory(prefix="fast-fsm-evidence-") as temp_directory:
        temporary_root = Path(temp_directory)
        junit_path = temporary_root / "pytest.xml"
        coverage_path = temporary_root / "coverage.json"
        _run_checked(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-x",
                "-q",
                f"--junitxml={junit_path}",
                "--cov=src/fast_fsm",
                f"--cov-report=json:{coverage_path}",
            ],
            cwd=REPOSITORY_ROOT,
            environment=environment,
        )
        return _parse_junit_results(junit_path), _coverage_percentages(coverage_path)


def _collect_trigger_benchmark(
    *, iterations: int = 20_000, warmup_iterations: int = 1_000
) -> dict[str, Any]:
    """Collect one local pure-source trigger observation for release evidence."""
    if iterations <= 0 or warmup_iterations < 0:
        raise EvidenceError(
            "Benchmark iterations must be positive with nonnegative warmup."
        )

    from fast_fsm.core import State, StateMachine

    idle = State("benchmark-idle")
    active = State("benchmark-active")
    fsm = StateMachine(idle, name="release-evidence-trigger-benchmark")
    fsm.add_state(active)
    fsm.add_transition("start", "benchmark-idle", "benchmark-active")
    fsm.add_transition("finish", "benchmark-active", "benchmark-idle")

    for _ in range(warmup_iterations):
        fsm.trigger("start")
        fsm.trigger("finish")
    gc.collect()
    started = time.perf_counter()
    for _ in range(iterations):
        fsm.trigger("start")
        fsm.trigger("finish")
    elapsed_seconds = time.perf_counter() - started
    if elapsed_seconds <= 0:
        raise EvidenceError(
            "Trigger benchmark did not produce a positive elapsed time."
        )

    operations = iterations * 2
    return {
        "command": (
            "tools/release_evidence.py evidence "
            "(StateMachine.trigger alternating-transition microbenchmark)"
        ),
        "mode": "pure",
        "metric": "StateMachine.trigger operations per second",
        "operations": operations,
        "warmup_operations": warmup_iterations * 2,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "ops_per_second": round(operations / elapsed_seconds, 2),
        "environment": {
            "implementation": sys.implementation.name,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
    }


def _collect_manifest_after_preflight(
    *,
    source_root: Path,
    source: Mapping[str, str],
    environment: Mapping[str, str],
    wheel_paths: Iterable[Path],
) -> dict[str, Any]:
    """Collect release facts after a caller has proved the pure source origin."""
    tests, coverage = _collect_test_and_coverage(environment=environment)
    wheel_artifacts = verify_wheels(
        wheel_paths, expected_version=source["distribution_version"]
    )["artifacts"]
    slots = slots_policy(source_root)
    benchmark = _collect_trigger_benchmark()
    uv_version = _resolved_uv_version(environment=environment)

    toolchain = {
        "python": sys.version.split()[0],
        "uv": uv_version,
        "pytest": _distribution_version("pytest"),
        "pytest_cov": _distribution_version("pytest-cov"),
        "ruff": _distribution_version("ruff"),
        "mypy": _locked_package_version("mypy"),
        "mypyc": _locked_package_version("mypy"),
        "ty": _distribution_version("ty"),
        "sphinx": _distribution_version("sphinx"),
        "setuptools": _locked_package_version("setuptools"),
        "wheel": _locked_package_version("wheel"),
    }
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "release_identity": {
            "package": PACKAGE_NAME,
            "distribution_version": source["distribution_version"],
        },
        "matrix_profile": {
            "profile": "local",
            "scope": "local-non-authorizing",
            "status": "not-collected",
        },
        "expected_matrix": [
            _matrix_cell_payload(cell)
            for cell in expected_matrix("local", _current_matrix_runtime()).cells
        ],
        "artifact_records": [],
        "historical_evidence": _historical_evidence(),
        "installed_performance": [],
        "quality_baseline": {
            "build_mode": "pure",
            "tests": tests,
            "coverage": coverage,
            "source": {"core_origin": source["core_origin"]},
        },
        "toolchain": toolchain,
        "artifact_evidence": {
            "wheels": wheel_artifacts,
            "source": {"core_origin": source["core_origin"]},
        },
        "slots_policy": {
            "inventory": slots["inventory"],
            "runtime_layouts": slots["runtime_layouts"],
            "registered_exceptions": slots["registered_exceptions"],
            "measurements": slots["representative_measurements"],
        },
        "performance_contract": {
            "compiled_trigger_ops_per_sec_min": 200000,
            "measurement": "environment-labeled; exact timing is not a freshness field",
            "observation": benchmark,
        },
        "measurement_environment": {
            "implementation": sys.implementation.name,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "comparison": "stable fields exclude this environment observation",
        },
    }


def _exactly_one_wheel(directory: Path) -> Path:
    """Return the one wheel built into an isolated evidence directory."""
    wheels = sorted(directory.glob("*.whl"), key=lambda path: path.name.casefold())
    if len(wheels) != 1:
        raise EvidenceError(
            "Expected exactly one temporary wheel for release evidence, found "
            f"{[wheel.name for wheel in wheels]!r}."
        )
    return wheels[0]


def collect_manifest(
    *,
    source_root: Path | None = None,
    wheel_paths: Iterable[Path] = (),
    build_wheel: bool = False,
) -> dict[str, Any]:
    """Collect the schema-v1 release baseline in a deterministic shape.

    The source preflight is intentionally the first subprocess action.  All
    later tool, test, coverage, and wheel observations inherit explicit pure
    mode, preventing a native build residue from being certified as source.
    When a caller requests a canonical wheel, its temporary directory is
    created and cleaned in Python so Taskfile behavior is portable.
    """
    supplied_wheels = tuple(wheel_paths)
    if build_wheel and supplied_wheels:
        raise EvidenceError("Use either supplied wheels or --build-wheel, not both.")
    resolved_source_root = (source_root or REPOSITORY_ROOT / "src").resolve()
    environment = _command_environment()
    source = _source_preflight(
        source_root=resolved_source_root, environment=environment
    )
    if not build_wheel:
        return _collect_manifest_after_preflight(
            source_root=resolved_source_root,
            source=source,
            environment=environment,
            wheel_paths=supplied_wheels,
        )

    with tempfile.TemporaryDirectory(prefix="fast-fsm-wheel-evidence-") as temporary:
        wheel_directory = Path(temporary)
        _run_checked(
            ["uv", "build", "--wheel", "--out-dir", str(wheel_directory)],
            cwd=REPOSITORY_ROOT,
            environment=environment,
        )
        wheel = _exactly_one_wheel(wheel_directory)
        return _collect_manifest_after_preflight(
            source_root=resolved_source_root,
            source=source,
            environment=environment,
            wheel_paths=(wheel,),
        )


def _read_manifest(path: Path) -> dict[str, Any]:
    """Load a tracked manifest without normalizing its source bytes."""

    def reject_non_standard_number(value: str) -> None:
        raise ValueError(f"non-standard JSON number {value!r}")

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_non_standard_number,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise EvidenceError(f"Could not read manifest {path}: {error}") from error
    if not isinstance(payload, dict):
        raise EvidenceError(f"Manifest {path} must contain a JSON object.")
    return payload


def _write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    """Write only the explicitly selected baseline path with deterministic bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_manifest(manifest), encoding="utf-8")


def write_or_check_manifest(
    manifest: Mapping[str, Any], *, manifest_path: Path, write: bool
) -> dict[str, Any]:
    """Intentionally write a baseline or compare it without mutating its bytes."""
    validate_performance_observation(manifest)
    if write:
        _write_manifest(manifest_path, manifest)
        return dict(manifest)

    baseline = _read_manifest(manifest_path)
    validate_performance_observation(baseline)
    validate_manifest_regressions(baseline, manifest)
    differences = compare_manifests(baseline, manifest)
    if differences:
        raise EvidenceError(
            "Release evidence manifest is stale:\n"
            + "\n".join(f"  - {difference}" for difference in differences)
        )
    return dict(manifest)


def _render_summary(manifest: Mapping[str, Any]) -> str:
    """Return a compact human-readable evidence summary."""
    baseline = manifest["quality_baseline"]
    tests = baseline["tests"]
    coverage = baseline["coverage"]
    return "\n".join(
        [
            f"Release evidence schema: {manifest['schema_version']}",
            f"Pure tests: {tests['passed']}/{tests['collected']} passed",
            "Source coverage: "
            f"total {coverage['total_percent']:.2f}%, core.py {coverage['core_percent']:.2f}%",
            f"uv: {manifest['toolchain']['uv']}",
            f"core origin: {baseline['source']['core_origin']}",
        ]
    )


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    """Write deterministic CLI output without exposing the caller environment."""
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
        return
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    verify_source_parser = commands.add_parser(
        "verify-source", help="fail closed when core.py is shadowed by native output"
    )
    verify_source_parser.add_argument(
        "--source-root",
        type=Path,
        default=REPOSITORY_ROOT / "src",
        help="source directory containing the fast_fsm package (default: repository src)",
    )
    verify_source_parser.add_argument("--json", action="store_true")

    verify_wheel_parser = commands.add_parser(
        "verify-wheel", help="classify repeated wheel archives without extraction"
    )
    verify_wheel_parser.add_argument(
        "--wheel",
        type=Path,
        action="append",
        required=True,
        help="wheel archive to inspect",
    )
    verify_wheel_parser.add_argument("--json", action="store_true")

    installed_wheel_parser = commands.add_parser(
        "verify-installed-wheel",
        help="install one exact wheel into a fresh neutral environment",
    )
    installed_wheel_parser.add_argument(
        "--wheel", type=Path, required=True, help="exact wheel archive to install"
    )
    installed_wheel_parser.add_argument(
        "--expected-mode", choices=("pure", "compiled"), required=True
    )
    installed_wheel_parser.add_argument(
        "--build-intent", choices=("pure", "compiled"), required=True
    )
    installed_wheel_parser.add_argument("--json", action="store_true")

    sdist_parser = commands.add_parser(
        "verify-sdist",
        help="inspect one bounded sdist and prove explicit installed child wheels",
    )
    sdist_parser.add_argument(
        "--sdist", type=Path, required=True, help="exact source archive to inspect"
    )
    sdist_parser.add_argument("--json", action="store_true")

    aggregate_parser = commands.add_parser(
        "aggregate-matrix",
        help="reconcile exact artifact evidence into a release or local matrix profile",
    )
    aggregate_parser.add_argument(
        "--profile", choices=("release", "local"), required=True
    )
    aggregate_parser.add_argument(
        "--record",
        type=Path,
        action="append",
        required=True,
        help="strict JSON artifact record to aggregate (repeatable)",
    )
    aggregate_parser.add_argument(
        "--summary",
        type=Path,
        help="optional generated human summary output path",
    )
    aggregate_parser.add_argument("--json", action="store_true")

    historical_parser = commands.add_parser(
        "historical-evidence",
        help="validate the exact non-gating Phase 16-19 provenance inventory",
    )
    historical_parser.add_argument(
        "--check", action="store_true", help="validate without changing evidence files"
    )
    historical_parser.add_argument("--json", action="store_true")

    identity_parser = commands.add_parser(
        "verify-release-identity",
        help="validate static v0.3.0 identity and optional tag-to-commit equality",
    )
    identity_parser.add_argument(
        "--installed-identity",
        type=Path,
        required=True,
        help="strict JSON installed distribution and fast_fsm.__version__ values",
    )
    identity_parser.add_argument(
        "--aggregate",
        type=Path,
        required=True,
        help="strict JSON aggregate or adjacent release_identity object",
    )
    identity_parser.add_argument(
        "--tag-ref",
        help="existing v0.3.0 tag to peel and compare (omitted for static mode)",
    )
    identity_parser.add_argument("--json", action="store_true")

    slots_policy_parser = commands.add_parser(
        "slots-policy", help="recursively audit source classes against the slots policy"
    )
    slots_policy_parser.add_argument(
        "--source-root",
        type=Path,
        default=REPOSITORY_ROOT / "src",
        help="source directory containing the fast_fsm package (default: repository src)",
    )
    slots_policy_parser.add_argument("--json", action="store_true")

    history_parser = commands.add_parser(
        "verify-history",
        help="audit an immutable release tag against its additive correction",
    )
    history_parser.add_argument("--tag", required=True, help="immutable release tag")
    history_parser.add_argument(
        "--correction",
        type=Path,
        required=True,
        help="canonical correction record under the repository root",
    )
    history_parser.add_argument("--json", action="store_true")

    evidence_parser = commands.add_parser(
        "evidence", help="write or non-destructively check release baseline evidence"
    )
    evidence_mode = evidence_parser.add_mutually_exclusive_group(required=True)
    evidence_mode.add_argument(
        "--write", action="store_true", help="intentionally regenerate the manifest"
    )
    evidence_mode.add_argument(
        "--check",
        action="store_true",
        help="compare in-memory evidence without writing",
    )
    evidence_parser.add_argument(
        "--manifest",
        type=Path,
        default=REPOSITORY_ROOT / "evidence" / "release-baseline.json",
        help="tracked manifest path (default: evidence/release-baseline.json)",
    )
    evidence_parser.add_argument(
        "--wheel",
        type=Path,
        action="append",
        default=[],
        help="wheel archive to preserve as independent artifact evidence (repeatable)",
    )
    evidence_parser.add_argument(
        "--build-wheel",
        action="store_true",
        help="build one temporary pure wheel with portable Python cleanup",
    )
    evidence_parser.add_argument(
        "--summary",
        type=Path,
        help="optional explicitly requested human-readable summary output path",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run a release-evidence subcommand and convert domain errors to exit 1."""
    parser = _build_parser()
    parsed = parser.parse_args(arguments)
    try:
        if parsed.command == "verify-source":
            _emit(verify_source(parsed.source_root), parsed.json)
        elif parsed.command == "verify-wheel":
            _emit(verify_wheels(parsed.wheel), parsed.json)
        elif parsed.command == "verify-installed-wheel":
            _emit(
                verify_installed_wheel(
                    parsed.wheel,
                    expected_mode=parsed.expected_mode,
                    build_intent=parsed.build_intent,
                ),
                parsed.json,
            )
        elif parsed.command == "verify-sdist":
            _emit(verify_sdist_derivations(parsed.sdist), parsed.json)
        elif parsed.command == "aggregate-matrix":
            aggregate = aggregate_matrix_records(
                [read_matrix_record(path) for path in parsed.record],
                profile=parsed.profile,
                runtime=_current_matrix_runtime(),
            )
            summary = render_aggregate_summary(aggregate)
            if parsed.summary:
                parsed.summary.write_text(summary, encoding="utf-8")
            _emit(aggregate if parsed.json else {"summary": summary}, parsed.json)
        elif parsed.command == "historical-evidence":
            if not parsed.check:
                raise EvidenceError("historical-evidence requires --check.")
            _emit(historical_evidence(), parsed.json)
        elif parsed.command == "verify-release-identity":
            installed = _strict_identity_json(parsed.installed_identity)
            aggregate_payload = _strict_identity_json(parsed.aggregate)
            aggregate_identity = aggregate_payload.get(
                "release_identity", aggregate_payload
            )
            if not isinstance(aggregate_identity, Mapping):
                raise EvidenceError("release identity aggregate is malformed.")
            _emit(
                validate_release_identity(
                    repository_root=REPOSITORY_ROOT,
                    installed_identity=installed,
                    aggregate_identity=cast(Mapping[str, object], aggregate_identity),
                    checked_out_commit=_checked_out_commit(
                        repository_root=REPOSITORY_ROOT
                    ),
                    tag_ref=parsed.tag_ref,
                ),
                parsed.json,
            )
        elif parsed.command == "slots-policy":
            _emit(slots_policy(parsed.source_root), parsed.json)
        elif parsed.command == "verify-history":
            _emit(
                verify_history(tag=parsed.tag, correction_path=parsed.correction),
                parsed.json,
            )
        elif parsed.command == "evidence":
            manifest = collect_manifest(
                wheel_paths=parsed.wheel, build_wheel=parsed.build_wheel
            )
            write_or_check_manifest(
                manifest, manifest_path=parsed.manifest, write=parsed.write
            )
            summary = _render_summary(manifest)
            if parsed.summary:
                parsed.summary.write_text(summary + "\n", encoding="utf-8")
            print(summary)
        else:  # pragma: no cover - argparse constrains this branch.
            parser.error(f"Unknown command: {parsed.command}")
    except EvidenceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
