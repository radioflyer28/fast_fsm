"""Installed-wheel proof uses concrete archives outside the source checkout."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import artifact_conformance, release_evidence  # noqa: E402


_SDIST_PACKAGE_SOURCES = (
    "src/fast_fsm/__init__.py",
    "src/fast_fsm/_diagnostics.py",
    "src/fast_fsm/condition_templates.py",
    "src/fast_fsm/conditions.py",
    "src/fast_fsm/core.py",
    "src/fast_fsm/py.typed",
    "src/fast_fsm/validation.py",
    "src/fast_fsm/visualization.py",
)
_SDIST_REQUIRED_FILES = (
    "pyproject.toml",
    "setup.py",
    "MANIFEST.in",
    "tools/__init__.py",
    "tools/build_modes.py",
    "tools/artifact_conformance.py",
    *_SDIST_PACKAGE_SOURCES,
)


def _write_sdist(
    tmp_path: Path,
    entries: list[tuple[str, bytes, bytes | None]],
) -> Path:
    """Write a compact synthetic source archive for archive-boundary tests."""
    sdist = tmp_path / "fast_fsm-0.2.2.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        for name, contents, member_type in entries:
            member = tarfile.TarInfo(name)
            member.type = member_type or tarfile.REGTYPE
            member.size = len(contents)
            if member_type in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
                member.linkname = "target"
                archive.addfile(member)
            elif member_type is not None and member_type != tarfile.REGTYPE:
                archive.addfile(member)
            else:
                archive.addfile(member, io.BytesIO(contents))
    return sdist


def _valid_sdist_entries() -> list[tuple[str, bytes, bytes | None]]:
    """Return all fixed build/probe inputs under one expected source root."""
    root = "fast_fsm-0.2.2"
    return [(f"{root}/{path}", b"fixture", None) for path in _SDIST_REQUIRED_FILES]


def test_sdist_archive_requires_all_build_and_probe_inputs(tmp_path: Path) -> None:
    """Archive validation exposes its bounded deterministic contract before build."""
    sdist = _write_sdist(tmp_path, _valid_sdist_entries())

    record = release_evidence.inspect_sdist(sdist)

    assert record["filename"] == sdist.name
    assert record["project_root"] == "fast_fsm-0.2.2"
    assert record["member_count"] == len(_SDIST_REQUIRED_FILES)
    assert record["required_members"] == list(_SDIST_REQUIRED_FILES)


def test_sdist_archive_rejects_unsafe_members_before_extraction(tmp_path: Path) -> None:
    """Traversal, links, duplicate paths, and native residue fail archive inspection."""
    unsafe_entries = (
        ("fast_fsm-0.2.2/../escaped.py", b"", None),
        ("/absolute.py", b"", None),
        ("C:/drive.py", b"", None),
        ("fast_fsm-0.2.2/link", b"", tarfile.SYMTYPE),
        ("fast_fsm-0.2.2/hard-link", b"", tarfile.LNKTYPE),
        ("fast_fsm-0.2.2/device", b"", tarfile.CHRTYPE),
        ("fast_fsm-0.2.2/src/fast_fsm/core.abi3.so", b"native", None),
    )
    for entry in unsafe_entries:
        sdist = _write_sdist(tmp_path, [*_valid_sdist_entries(), entry])
        with pytest.raises(release_evidence.EvidenceError):
            release_evidence.inspect_sdist(sdist)

    duplicate = _valid_sdist_entries()
    duplicate.append(duplicate[-1])
    with pytest.raises(release_evidence.EvidenceError, match="duplicate"):
        release_evidence.inspect_sdist(_write_sdist(tmp_path, duplicate))

    missing = _valid_sdist_entries()
    missing = [entry for entry in missing if not entry[0].endswith("setup.py")]
    with pytest.raises(release_evidence.EvidenceError, match="missing"):
        release_evidence.inspect_sdist(_write_sdist(tmp_path, missing))


def test_sdist_archive_enforces_member_and_uncompressed_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixed limits stop oversized archives before any extraction or build work."""
    entries = _valid_sdist_entries()

    with monkeypatch.context() as patched:
        patched.setattr(release_evidence, "_MAX_SDIST_MEMBERS", len(entries) - 1)
        with pytest.raises(release_evidence.EvidenceError, match="member-count"):
            release_evidence.inspect_sdist(_write_sdist(tmp_path, entries))

    with monkeypatch.context() as patched:
        patched.setattr(release_evidence, "_MAX_SDIST_MEMBER_BYTES", 1)
        with pytest.raises(release_evidence.EvidenceError, match="oversized member"):
            release_evidence.inspect_sdist(_write_sdist(tmp_path, entries))

    with monkeypatch.context() as patched:
        patched.setattr(release_evidence, "_MAX_SDIST_MEMBER_BYTES", 10)
        patched.setattr(release_evidence, "_MAX_SDIST_TOTAL_UNCOMPRESSED_BYTES", 1)
        with pytest.raises(release_evidence.EvidenceError, match="uncompressed-size"):
            release_evidence.inspect_sdist(_write_sdist(tmp_path, entries))


def test_sdist_child_lineage_rejects_auto_missing_and_duplicate_records() -> None:
    """The accepted lineage has one exact pure and compiled child, never AUTO."""
    parent = {"filename": "fast_fsm-0.2.2.tar.gz", "sha256": "0" * 64}

    def child(intent: str, *, build_intent: str | None = None) -> dict[str, object]:
        return {
            "requested_build_intent": intent,
            "parent_sdist": parent,
            "artifact": {
                "expected_mode": intent,
                "build_intent": build_intent or intent,
            },
        }

    with pytest.raises(release_evidence.EvidenceError, match="missing or duplicate"):
        release_evidence._validate_sdist_child_lineage(
            [child("pure")], parent_sdist=parent
        )
    with pytest.raises(release_evidence.EvidenceError, match="missing or duplicate"):
        release_evidence._validate_sdist_child_lineage(
            [child("pure"), child("pure")], parent_sdist=parent
        )
    with pytest.raises(release_evidence.EvidenceError, match="invalid build intent"):
        release_evidence._validate_sdist_child_lineage(
            [child("pure", build_intent="auto"), child("compiled")],
            parent_sdist=parent,
        )


def _build_wheel(output: Path, mode: str) -> Path:
    """Build one intentional local wheel under the requested release intent."""
    environment = dict(os.environ)
    environment["FAST_FSM_BUILD_MODE"] = mode
    environment.pop("FAST_FSM_PURE_PYTHON", None)
    completed = subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(output)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    wheels = sorted(output.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0].resolve()


@pytest.fixture(scope="module")
def tracer_wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Build concrete pure and compiled archives once for the tracer proof."""
    root = tmp_path_factory.mktemp("artifact-tracer")
    return {mode: _build_wheel(root / mode, mode) for mode in ("pure", "compiled")}


@pytest.mark.integration
@pytest.mark.parametrize("mode", ("pure", "compiled"))
def test_tracer_installs_exact_artifact_and_matches_source_lifecycle(
    tracer_wheels: dict[str, Path], mode: str
) -> None:
    """An absolute artifact path proves the same real lifecycle record in isolation."""
    wheel = tracer_wheels[mode]
    record = release_evidence.verify_installed_wheel(
        wheel,
        expected_mode=mode,
        build_intent=mode,
    )

    assert (
        record["artifact"]["sha256"] == hashlib.sha256(wheel.read_bytes()).hexdigest()
    )
    assert record["runtime"]["expected_mode"] == mode
    assert record["conformance"]["payload_leak_free"] is True
    assert (
        artifact_conformance.compare_conformance(
            artifact_conformance.collect_conformance(), record["conformance"]
        )
        == []
    )
    if mode == "compiled":
        performance = record["performance"]
        assert performance["core_loader"] == "ExtensionFileLoader"
        assert performance["median_ops_per_second"] >= 200_000
        assert len(performance["samples_ops_per_second"]) >= 3
    else:
        assert record["performance"] is None


def _runtime_probe(
    environment: Path, *, direct_url: object | None = None
) -> dict[str, object]:
    """Build one parent-side runtime fixture without importing a real checkout."""
    package = environment / "site-packages" / "fast_fsm" / "__init__.py"
    core = environment / "site-packages" / "fast_fsm" / "core.py"
    interpreter = environment / "bin" / "python"
    return {
        "distribution_version": "0.2.2",
        "package_version": "0.2.2",
        "package_origin": str(package),
        "core_origin": str(core),
        "core_loader": "SourceFileLoader",
        "interpreter": str(interpreter),
        "python_implementation": "cpython",
        "python_version": "3.12.10",
        "platform": "Darwin",
        "machine": "arm64",
        "direct_url": direct_url,
        "extension_suffixes": [".so", ".pyd"],
    }


def test_runtime_provenance_rejects_checkout_and_symlink_escapes(
    tmp_path: Path,
) -> None:
    """Fresh-env evidence never accepts editable or checkout-backed origins."""
    environment = tmp_path / "environment"
    checkout_direct_url = {"url": ROOT.as_uri(), "dir_info": {"editable": False}}
    with pytest.raises(release_evidence.EvidenceError, match="provenance"):
        release_evidence._validate_runtime_probe(
            _runtime_probe(environment, direct_url=checkout_direct_url),
            environment_root=environment,
            expected_mode="pure",
            version="0.2.2",
        )

    escaped = _runtime_probe(environment)
    escaped["core_origin"] = str(ROOT / "src" / "fast_fsm" / "core.py")
    with pytest.raises(release_evidence.EvidenceError, match="origin"):
        release_evidence._validate_runtime_probe(
            escaped,
            environment_root=environment,
            expected_mode="pure",
            version="0.2.2",
        )


def test_child_probe_rejects_payloads_resource_abuse_and_parent_identity_drift() -> (
    None
):
    """Child output is untrusted even when its top-level JSON is well formed."""
    conformance = artifact_conformance.collect_conformance()
    conformance["scenarios"][0]["state"] = "caller-secret"
    conformance["semantic_sha256"] = "0" * 64
    child = {
        "artifact_sha256": "0" * 64,
        "conformance": conformance,
        "runtime": _runtime_probe(Path("/environment")),
    }

    with pytest.raises(release_evidence.EvidenceError, match="artifact identity"):
        release_evidence._validate_child_probe(
            child,
            expected_artifact_sha256="f" * 64,
        )

    with pytest.raises(release_evidence.EvidenceError, match="malformed"):
        release_evidence._strict_json_object(
            '{"value": 1, "value": 2}', field="child probe"
        )
    with pytest.raises(release_evidence.EvidenceError, match="malformed"):
        release_evidence._strict_json_object('{"value": NaN}', field="child probe")

    oversized = json.dumps(
        {"value": "x" * (release_evidence._MAX_CHILD_OUTPUT_BYTES + 1)}
    )
    with pytest.raises(release_evidence.EvidenceError, match="size limit"):
        release_evidence._strict_json_object(oversized, field="child probe")


def test_compiled_archive_tags_must_match_the_installed_runtime_architecture() -> None:
    """A cross-platform archive cannot be accepted as native local proof."""
    with pytest.raises(release_evidence.EvidenceError, match="architecture"):
        release_evidence._validate_archive_runtime_architecture(
            ["cp312-cp312-manylinux_2_17_x86_64"],
            {"platform": "Darwin", "machine": "arm64"},
            expected_mode="compiled",
        )


def _installed_compiled_performance_record() -> dict[str, object]:
    """Return one complete installed-native sample set with a slow outlier."""
    return {
        "evidence_kind": "installed_compiled_performance",
        "artifact_sha256": "a" * 64,
        "asserted_mode": "compiled",
        "build_intent": "compiled",
        "core_origin": "/isolated/environment/site-packages/fast_fsm/core.so",
        "core_loader": "ExtensionFileLoader",
        "exact_command": "release_evidence.py installed-benchmark-child",
        "execution_commit": "b" * 40,
        "executed_at": "2026-09-05T02:36:33Z",
        "warmup_operations": 2_000,
        "iterations": 20_000,
        "samples_ops_per_second": [275_000.0, 250_000.0, 1.0],
        "statistic": "median",
        "median_ops_per_second": 250_000.0,
        "python_implementation": "cpython",
        "python_version": "3.12.10",
        "platform": "Darwin",
        "machine": "arm64",
        "environment_label": "installed-compiled-native",
    }


def test_installed_compiled_performance_requires_native_median_samples() -> None:
    """Only three finite installed-native samples can pass the 200k median gate."""
    record = _installed_compiled_performance_record()

    validated = release_evidence.validate_installed_compiled_performance(record)

    assert validated["median_ops_per_second"] == 250_000.0
    assert validated["samples_ops_per_second"] == [275_000.0, 250_000.0, 1.0]
    assert validated["statistic"] == "median"


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("samples_ops_per_second", [275_000.0, 250_000.0], "three"),
        ("samples_ops_per_second", [275_000.0, float("nan"), 250_000.0], "finite"),
        ("samples_ops_per_second", [275_000.0, float("inf"), 250_000.0], "finite"),
        ("median_ops_per_second", 199_999.99, "median"),
        ("statistic", "mean", "median"),
        ("asserted_mode", "pure", "compiled"),
        ("core_loader", "SourceFileLoader", "native"),
        ("artifact_sha256", "short", "sha256"),
        ("execution_commit", "short", "commit"),
        ("executed_at", "not-a-utc-time", "time"),
    ],
)
def test_installed_compiled_performance_rejects_nonblocking_or_malformed_records(
    field: str, value: object, match: str
) -> None:
    """Pure, detached, malformed, and below-floor records cannot satisfy TEST-06."""
    record = _installed_compiled_performance_record()
    record[field] = value

    with pytest.raises(release_evidence.EvidenceError, match=match):
        release_evidence.validate_installed_compiled_performance(record)


def test_installed_performance_evidence_validates_history_before_new_native_run() -> (
    None
):
    """Historical records remain categorical prerequisites, never performance substitutes."""
    installed = _installed_compiled_performance_record()
    historical = release_evidence.historical_evidence()["entries"]

    validated = release_evidence.validate_installed_performance_evidence(
        historical=historical,
        installed=[installed],
    )

    assert validated["historical_phases"] == ["16", "17", "18", "19"]
    assert validated["compiled"][0]["artifact_sha256"] == "a" * 64

    with pytest.raises(release_evidence.EvidenceError, match="historical"):
        release_evidence.validate_installed_performance_evidence(
            historical=historical[:-1],
            installed=[installed],
        )

    substituted = dict(installed)
    substituted["evidence_kind"] = "historical_phase_performance"
    with pytest.raises(release_evidence.EvidenceError, match="evidence kind"):
        release_evidence.validate_installed_performance_evidence(
            historical=historical,
            installed=[substituted],
        )
