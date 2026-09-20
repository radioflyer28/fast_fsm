"""Installed-wheel proof uses concrete archives outside the source checkout."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest
from fast_fsm import StateMachine, quick_fsm, simple_fsm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import artifact_conformance, release_evidence  # noqa: E402


_SDIST_PACKAGE_SOURCES = (
    "src/fast_fsm/__init__.py",
    "src/fast_fsm/_construction_compat.py",
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


def _copy_native_build_project(destination: Path) -> None:
    """Stage the minimum locked project needed for a disposable native build."""
    for relative in ("README.md", "pyproject.toml", "setup.py", "uv.lock"):
        shutil.copy2(ROOT / relative, destination / relative)
    shutil.copytree(
        ROOT / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("core*.so", "core*.pyd", "__pycache__"),
    )
    tools = destination / "tools"
    tools.mkdir()
    for relative in ("__init__.py", "build_modes.py"):
        shutil.copy2(ROOT / "tools" / relative, tools / relative)


def _native_probe_environment() -> dict[str, str]:
    """Keep the disposable build/probe outside pytest-cov's parent data file."""
    environment = dict(os.environ)
    for key in tuple(environment):
        if key.startswith("COV_CORE_") or key in {
            "COVERAGE_FILE",
            "COVERAGE_PROCESS_START",
            "COVERAGE_RCFILE",
        }:
            environment.pop(key)
    return environment


def _collect_source_probe(
    source_project: Path, neutral_directory: Path
) -> dict[str, object]:
    """Collect a strict record in a child that imports only the staged source."""
    neutral_directory.mkdir()
    probe = neutral_directory / "artifact_conformance.py"
    shutil.copy2(ROOT / "tools" / "artifact_conformance.py", probe)
    environment = _native_probe_environment()
    environment["PYTHONPATH"] = str((source_project / "src").resolve())
    completed = subprocess.run(
        [
            sys.executable,
            str(probe),
            "--installed-probe",
            "--artifact-sha256",
            "0" * 64,
        ],
        cwd=neutral_directory,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    record = json.loads(completed.stdout)
    assert isinstance(record, dict)
    return record


def _assert_staged_source_origin(
    record: dict[str, object], *, source_project: Path, expected_mode: str
) -> None:
    """Require the child loader and exact core location before comparing semantics."""
    runtime = record["runtime"]
    assert isinstance(runtime, dict)
    package_root = (source_project / "src" / "fast_fsm").resolve()
    core_origin = Path(str(runtime["core_origin"])).resolve()
    assert core_origin.parent == package_root
    if expected_mode == "compiled":
        assert core_origin.suffix in set(runtime["extension_suffixes"])
        assert runtime["core_loader"] == "ExtensionFileLoader"
    else:
        assert core_origin == package_root / "core.py"
        assert runtime["core_loader"] == "SourceFileLoader"
    runtime["expected_mode"] = expected_mode


@pytest.fixture(scope="module")
def fresh_native_source_conformance(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, object]:
    """Build a native core in a disposable source copy and restore its pure shadow."""
    project = tmp_path_factory.mktemp("fresh-native-source")
    _copy_native_build_project(project)
    environment = _native_probe_environment()
    environment["FAST_FSM_BUILD_MODE"] = "compiled"
    environment.pop("FAST_FSM_PURE_PYTHON", None)
    built = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--inplace", "-q"],
        cwd=project,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr

    package_root = (project / "src" / "fast_fsm").resolve()
    shadows = release_evidence.find_native_core_shadows(package_root)
    assert shadows
    assert all(shadow.parent == package_root for shadow in shadows)
    native_probe = _collect_source_probe(project, project / "native-probe")
    _assert_staged_source_origin(
        native_probe, source_project=project, expected_mode="compiled"
    )

    backup = (project / "recoverable-native-shadow-backup").resolve()
    backup.mkdir()
    moved: list[tuple[Path, Path]] = []
    try:
        for shadow in shadows:
            destination = (backup / shadow.name).resolve()
            assert destination.parent == backup
            shutil.move(str(shadow), destination)
            moved.append((shadow, destination))
        assert not release_evidence.find_native_core_shadows(package_root)
        pure_probe = _collect_source_probe(project, project / "pure-probe")
        _assert_staged_source_origin(
            pure_probe, source_project=project, expected_mode="pure"
        )
    finally:
        for original, relocated in moved:
            assert relocated.parent == backup
            assert original.parent == package_root
            if relocated.is_file():
                shutil.move(str(relocated), original)
    assert release_evidence.find_native_core_shadows(package_root) == shadows
    return {
        "runtime": native_probe["runtime"],
        "conformance": native_probe["conformance"],
        "pure_after_shadow_relocation": pure_probe,
    }


def test_phase32_native_probe_environment_does_not_replace_parent_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Child builds cannot write pytest-cov's parent coverage data file."""
    monkeypatch.setenv("COV_CORE_DATAFILE", "parent-coverage-data")
    monkeypatch.setenv("COV_CORE_SOURCE", "src/fast_fsm")
    monkeypatch.setenv("COVERAGE_PROCESS_START", "pyproject.toml")
    monkeypatch.setenv("FAST_FSM_BUILD_MODE", "pure")

    environment = _native_probe_environment()

    assert environment["FAST_FSM_BUILD_MODE"] == "pure"
    assert not any(
        key.startswith("COV_CORE_") or key.startswith("COVERAGE_")
        for key in environment
    )


def test_phase32_compatibility_wrappers_execute_the_documented_builder_window() -> None:
    """Retained v0.5.x wrappers still warn once while constructing real machines."""
    with pytest.warns(DeprecationWarning):
        from_states = StateMachine.from_states("idle", "active", initial="idle")
    with pytest.warns(DeprecationWarning):
        quick_build = StateMachine.quick_build("idle", [("advance", "idle", "active")])
    with pytest.warns(DeprecationWarning):
        simple = simple_fsm("idle", "active", initial="idle")
    with pytest.warns(DeprecationWarning):
        quick = quick_fsm("idle", [("advance", "idle", "active")])

    assert from_states.trigger("missing").success is False
    assert quick_build.trigger("advance").to_state == "active"
    assert simple.current_state.name == "idle"
    assert quick.trigger("advance").to_state == "active"


@pytest.fixture(scope="module")
def tracer_wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Build concrete pure and compiled archives once for the tracer proof."""
    root = tmp_path_factory.mktemp("artifact-tracer")
    return {mode: _build_wheel(root / mode, mode) for mode in ("pure", "compiled")}


@pytest.fixture(scope="module")
def clean_source_conformance() -> dict[str, object]:
    """Capture the one clean-source record only after its pure-origin preflight."""
    source = release_evidence.verify_source()
    assert source["core_origin"] == "src/fast_fsm/core.py"
    return artifact_conformance.collect_conformance()


@pytest.mark.integration
@pytest.mark.parametrize("mode", ("pure", "compiled"))
def test_tracer_installs_exact_artifact_and_matches_clean_source_record(
    tracer_wheels: dict[str, Path],
    clean_source_conformance: dict[str, object],
    mode: str,
) -> None:
    """Both exact archives match one source record captured after pure preflight."""
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
            clean_source_conformance, record["conformance"]
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


@pytest.mark.integration
def test_phase32_final_pure_wheel_preserves_exact_origin_finality_oracle(
    tracer_wheels: dict[str, Path],
    clean_source_conformance: dict[str, object],
) -> None:
    """The pure installed tracer is accepted only after provenance checks pass."""
    wheel = tracer_wheels["pure"]
    installed = release_evidence.verify_installed_wheel(
        wheel,
        expected_mode="pure",
        build_intent="pure",
        collect_performance=False,
    )

    assert installed["artifact"]["expected_mode"] == "pure"
    assert installed["artifact"]["build_intent"] == "pure"
    assert installed["runtime"]["expected_mode"] == "pure"
    assert installed["runtime"]["core_loader"] == "SourceFileLoader"
    assert (
        artifact_conformance.compare_conformance(
            clean_source_conformance, installed["conformance"]
        )
        == []
    )
    records = {record["id"]: record for record in installed["conformance"]["scenarios"]}
    assert records["final.explicit-versus-sink"]["final_terminated"] is True
    assert records["final.explicit-versus-sink"]["sink_terminated"] is False


@pytest.mark.integration
def test_phase32_fresh_native_copy_matches_clean_source_oracle(
    clean_source_conformance: dict[str, object],
    fresh_native_source_conformance: dict[str, object],
) -> None:
    """A fresh isolated native core matches the same strict source oracle."""
    assert fresh_native_source_conformance["runtime"]["expected_mode"] == "compiled"
    assert fresh_native_source_conformance["runtime"]["core_loader"] == (
        "ExtensionFileLoader"
    )
    assert (
        artifact_conformance.compare_conformance(
            clean_source_conformance,
            fresh_native_source_conformance["conformance"],
        )
        == []
    )
    restored_pure = fresh_native_source_conformance["pure_after_shadow_relocation"]
    assert isinstance(restored_pure, dict)
    assert (
        artifact_conformance.compare_conformance(
            clean_source_conformance,
            restored_pure["conformance"],
        )
        == []
    )


def test_direct_artifact_task_captures_one_clean_source_record_for_both_wheels() -> (
    None
):
    """The runnable task keeps source/pure/compiled proof in one shared flow."""
    taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    target = taskfile.split("  release-installed-artifacts-check:\n", 1)[1].split(
        "\n  release-sdist-check:", 1
    )[0]

    assert "- task: pure-source-check" in target
    assert "source_conformance = artifact_conformance.collect_conformance()" in target
    assert "release_evidence.verify_source()" in target
    assert 'for intent in ("pure", "compiled"):' in target
    assert "record = release_evidence.verify_installed_wheel(" in target
    assert "artifact_conformance.compare_conformance(" in target
    assert "release-installed-performance-check" in taskfile


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


def test_parent_rejects_digest_valid_priority_contract_drift() -> None:
    """Child hashes cannot substitute for parent validation of required values."""
    conformance = artifact_conformance.collect_conformance()
    priority = next(
        record
        for record in conformance["scenarios"]
        if record["id"] == "priority.sync.winner"
    )
    priority["target"] = "wrong-target"
    conformance["semantic_sha256"] = artifact_conformance._sha256(
        {
            "schema_version": artifact_conformance.SCHEMA_VERSION,
            "suite_sha256": conformance["suite_sha256"],
            "scenarios": conformance["scenarios"],
        }
    )
    child = {
        "artifact_sha256": "0" * 64,
        "conformance": conformance,
        "runtime": _runtime_probe(Path("/environment")),
    }

    with pytest.raises(release_evidence.EvidenceError, match="required contract"):
        release_evidence._validate_child_probe(
            child,
            expected_artifact_sha256="0" * 64,
        )


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
