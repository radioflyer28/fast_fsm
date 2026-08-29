"""Regression coverage for the maintainer-only release evidence CLI."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable
from zipfile import ZipFile

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.release_evidence as release_evidence  # noqa: E402
from tools.release_evidence import (  # noqa: E402
    REGISTERED_SLOTS_EXCEPTIONS,
    EvidenceError,
    compare_manifests,
    collect_class_declarations,
    serialize_manifest,
    validate_slots_inventory,
    validate_manifest_regressions,
)


PACKAGE_SOURCE = ROOT / "src" / "fast_fsm"
TOOL = ROOT / "tools" / "release_evidence.py"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
DOCS_WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"

TASK_SETUP_ACTION = "arduino/setup-task@c0bc642852239c2689f73f4ea6459c29405f3c52"
TASK_VERSION = "3.53.1"
TASK_CONSUMING_CI_JOBS = frozenset(
    {
        "format",
        "lint",
        "typecheck_mypy",
        "typecheck_ty",
        "test",
        "supported_python_build",
        "evidence",
        "docs_html",
        "docs_doctest",
    }
)
_TASK_COMMAND = re.compile(
    r"""(?mx)
    (?:^|[;&|])\s*
    (?:
        [A-Za-z_][A-Za-z0-9_]*=
        (?:\"[^\"\n]*\"|'[^'\n]*'|[^\s;&|\n]+)\s+
    )*
    task(?:\s|$)
    """
)


def _run_evidence(
    *arguments: str, environ: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the evidence CLI in an isolated subprocess."""
    return subprocess.run(
        [sys.executable, str(TOOL), *arguments],
        cwd=ROOT,
        env={**os.environ, **(environ or {})},
        text=True,
        capture_output=True,
        check=False,
    )


def _copy_clean_source(tmp_path: Path) -> Path:
    """Copy package source without native build leftovers into a temp source root."""
    source_root = tmp_path / "src"
    shutil.copytree(
        PACKAGE_SOURCE,
        source_root / "fast_fsm",
        ignore=shutil.ignore_patterns("core*.so", "core*.pyd", "__pycache__"),
    )
    return source_root


def _write_wheel(
    directory: Path,
    *,
    filename_tag: str,
    wheel_tags: Iterable[str],
    native_members: Iterable[str] = (),
    version: str = "0.2.2",
) -> Path:
    """Create a minimal wheel archive with independently controllable evidence."""
    wheel = directory / f"fast_fsm-{version}-{filename_tag}.whl"
    dist_info = f"fast_fsm-{version}.dist-info"
    with ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: release-evidence-test\n"
            + "".join(f"Tag: {tag}\n" for tag in wheel_tags),
        )
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.1\nName: fast-fsm\nVersion: {version}\n",
        )
        archive.writestr("fast_fsm/__init__.py", "")
        archive.writestr("fast_fsm/core.py", "")
        for member in native_members:
            archive.writestr(member, b"native-fixture")
    return wheel


CANONICAL_V023_CORRECTION = (
    "Version 0.2.3 was shipped with defective 0.2.2 package metadata. "
    "It remains a shipped release: the existing v0.2.3 tag and published "
    "artifacts are immutable and unchanged. Corrected metadata will be "
    "published in v0.3.0."
)


def _run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a local fixture Git command without touching repository refs."""
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )


def _write_history_fixture(
    tmp_path: Path,
    *,
    changelog: str | None = None,
    correction: str = CANONICAL_V023_CORRECTION,
) -> tuple[Path, Path]:
    """Create an isolated immutable-tag fixture and its correction record."""
    repository = tmp_path / "history"
    repository.mkdir()
    _run_git(repository, "init", "--quiet")
    _run_git(repository, "config", "user.email", "release-evidence@example.test")
    _run_git(repository, "config", "user.name", "Release Evidence")
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "fast_fsm"\nversion = "0.2.2"\n', encoding="utf-8"
    )
    (repository / "CHANGELOG.md").write_text(
        changelog
        or "\n".join(
            [
                "# Changelog",
                "",
                "## [0.2.3] — 2026-04-05",
                "",
                CANONICAL_V023_CORRECTION,
                "",
                "## [0.2.2] — 2026-04-04",
                "",
                "The preceding release record remains available for audit.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _run_git(repository, "add", "pyproject.toml", "CHANGELOG.md")
    _run_git(repository, "commit", "--quiet", "-m", "fixture release")
    _run_git(repository, "tag", "-a", "v0.2.3", "-m", "fixture v0.2.3")
    correction_path = repository / "docs" / "release-corrections" / "v0.2.3.md"
    correction_path.parent.mkdir(parents=True)
    correction_path.write_text(correction + "\n", encoding="utf-8")
    return repository, correction_path


def test_release_history_audits_immutable_v023_metadata_and_correction(
    tmp_path: Path,
) -> None:
    """A v0.2.3 tag with 0.2.2 metadata needs an additive correction, not a retag."""
    repository, correction_path = _write_history_fixture(tmp_path)
    tag_before = _run_git(repository, "rev-parse", "v0.2.3").stdout.strip()

    evidence = release_evidence.verify_history(
        tag="v0.2.3", correction_path=correction_path, repository_root=repository
    )

    assert evidence["tag"] == "v0.2.3"
    assert evidence["tag_pyproject_version"] == "0.2.2"
    assert evidence["correction_path"] == "docs/release-corrections/v0.2.3.md"
    assert _run_git(repository, "rev-parse", "v0.2.3").stdout.strip() == tag_before


def test_release_history_accepts_wrapped_canonical_correction(tmp_path: Path) -> None:
    """Canonical Markdown wrapping must not change immutable-history facts."""
    correction = CANONICAL_V023_CORRECTION.replace(
        " It remains", "\nIt remains"
    ).replace(" published", "\npublished")
    repository, correction_path = _write_history_fixture(
        tmp_path, correction=correction
    )

    evidence = release_evidence.verify_history(
        tag="v0.2.3", correction_path=correction_path, repository_root=repository
    )

    assert evidence["tag_pyproject_version"] == "0.2.2"


@pytest.mark.parametrize(
    ("changelog", "correction", "expected"),
    [
        (
            "# Changelog\n\n## [0.2.3] — 2026-04-05\n\n"
            + CANONICAL_V023_CORRECTION
            + "\n",
            CANONICAL_V023_CORRECTION,
            "0.2.2",
        ),
        (
            None,
            "Version 0.2.3 metadata is correct and its tag was moved.",
            "defective 0.2.2 package metadata",
        ),
        (
            "# Changelog\n\n## [0.2.3] — 2026-04-05\n\n"
            "Version 0.2.3 was shipped with defective 0.2.2 package metadata.\n\n"
            "## [0.2.2] — 2026-04-04\n",
            CANONICAL_V023_CORRECTION,
            "immutable and unchanged",
        ),
    ],
)
def test_release_history_rejects_missing_or_divergent_correction_facts(
    tmp_path: Path, changelog: str | None, correction: str, expected: str
) -> None:
    """Missing dated history, changed facts, and retag wording fail audibly."""
    repository, correction_path = _write_history_fixture(
        tmp_path, changelog=changelog, correction=correction
    )

    with pytest.raises(EvidenceError, match=re.escape(expected)):
        release_evidence.verify_history(
            tag="v0.2.3", correction_path=correction_path, repository_root=repository
        )


def test_verify_source_reports_native_shadow_before_import_without_mutation(
    tmp_path: Path,
) -> None:
    """A native core sibling fails preflight and remains byte-for-byte intact."""
    source_root = _copy_clean_source(tmp_path)
    shadow = source_root / "fast_fsm" / "core.fixture.so"
    original = b"do not delete or rewrite this fixture"
    shadow.write_bytes(original)

    completed = _run_evidence(
        "verify-source", "--source-root", str(source_root), "--json"
    )

    assert completed.returncode != 0
    assert str(shadow) in completed.stderr
    assert "Remove or relocate" in completed.stderr
    assert shadow.read_bytes() == original


def test_verify_source_records_clean_python_origin_and_distribution_metadata(
    tmp_path: Path,
) -> None:
    """A clean copied source tree imports core.py and produces normalized evidence."""
    source_root = _copy_clean_source(tmp_path)

    completed = _run_evidence(
        "verify-source", "--source-root", str(source_root), "--json"
    )

    assert completed.returncode == 0, completed.stderr
    evidence = json.loads(completed.stdout)
    assert evidence["core_origin"] == "src/fast_fsm/core.py"
    assert evidence["core_origin"].endswith(".py")
    assert evidence["distribution_version"]


def test_verify_wheel_classifies_universal_wheel_without_native_members(
    tmp_path: Path,
) -> None:
    """Universal tags plus no native archive members are the pure-wheel identity."""
    wheel = _write_wheel(
        tmp_path, filename_tag="py3-none-any", wheel_tags=["py3-none-any"]
    )

    completed = _run_evidence("verify-wheel", "--wheel", str(wheel), "--json")

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(completed.stdout)["artifacts"][0]
    assert artifact["mode"] == "pure"
    assert artifact["filename_tags"] == ["py3-none-any"]
    assert artifact["wheel_tags"] == ["py3-none-any"]
    assert artifact["native_members"] == []
    assert artifact["metadata_version"] == "0.2.2"


@pytest.mark.parametrize(
    ("filename_tag", "wheel_tags", "native_members", "expected"),
    [
        (
            "py3-none-any",
            ["py3-none-any"],
            ["fast_fsm/core.cpython-310-x86_64-linux-gnu.so"],
            "universal pure wheel",
        ),
        ("py3-none-any", ["cp310-cp310-manylinux_2_17_x86_64"], [], "tag mismatch"),
    ],
)
def test_verify_wheel_rejects_contradictory_pure_evidence(
    tmp_path: Path,
    filename_tag: str,
    wheel_tags: list[str],
    native_members: list[str],
    expected: str,
) -> None:
    """A claimed universal pure artifact must agree across all evidence sources."""
    wheel = _write_wheel(
        tmp_path,
        filename_tag=filename_tag,
        wheel_tags=wheel_tags,
        native_members=native_members,
    )

    completed = _run_evidence("verify-wheel", "--wheel", str(wheel), "--json")

    assert completed.returncode != 0
    assert expected in completed.stderr.lower()


def test_verify_wheel_keeps_one_pure_and_multiple_compiled_records_sorted(
    tmp_path: Path,
) -> None:
    """Every repeated wheel input retains independent deterministic evidence."""
    pure = _write_wheel(
        tmp_path, filename_tag="py3-none-any", wheel_tags=["py3-none-any"]
    )
    linux = _write_wheel(
        tmp_path,
        filename_tag="cp310-cp310-manylinux_2_17_x86_64",
        wheel_tags=["cp310-cp310-manylinux_2_17_x86_64"],
        native_members=["fast_fsm/core.cpython-310-x86_64-linux-gnu.so"],
    )
    windows = _write_wheel(
        tmp_path,
        filename_tag="cp310-cp310-win_amd64",
        wheel_tags=["cp310-cp310-win_amd64"],
        native_members=["fast_fsm/core.cp310-win_amd64.pyd"],
    )

    first = _run_evidence(
        "verify-wheel",
        "--wheel",
        str(windows),
        "--wheel",
        str(pure),
        "--wheel",
        str(linux),
        "--json",
    )
    second = _run_evidence(
        "verify-wheel",
        "--wheel",
        str(linux),
        "--wheel",
        str(windows),
        "--wheel",
        str(pure),
        "--json",
    )

    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout) == json.loads(second.stdout)
    artifacts = json.loads(first.stdout)["artifacts"]
    assert [artifact["mode"] for artifact in artifacts] == [
        "compiled",
        "compiled",
        "pure",
    ]
    assert all(
        {
            "normalized_basename",
            "filename_tags",
            "wheel_tags",
            "metadata_version",
            "native_members",
        }
        <= artifact.keys()
        for artifact in artifacts
    )


def _write_nested_class(source_root: Path, name: str, base: str = "object") -> None:
    """Add a future production class to a nested source module fixture."""
    nested = source_root / "fast_fsm" / "nested"
    nested.mkdir()
    (nested / "__init__.py").write_text("", encoding="utf-8")
    (nested / "future_policy.py").write_text(
        f"class {name}({base}):\n    pass\n", encoding="utf-8"
    )


def test_slots_policy_recursively_classifies_every_production_class() -> None:
    """All top-level production classes are either slotted or deliberately registered."""
    completed = _run_evidence("slots-policy", "--json")

    assert completed.returncode == 0, completed.stderr
    evidence = json.loads(completed.stdout)
    inventory = evidence["inventory"]
    assert inventory
    assert all(entry["classification"] for entry in inventory)
    registered = {
        entry["qualified_name"]: entry for entry in evidence["registered_exceptions"]
    }
    assert set(registered) == {
        "fast_fsm.core.CompiledFuncCondition",
        "fast_fsm.core.TransitionError",
    }
    for name, entry in registered.items():
        assert entry["has_instance_dict"] is True, name
        assert isinstance(entry["instance_size_bytes"], int)
        assert entry["exception_reason"]


@pytest.mark.parametrize(
    ("name", "base"),
    [
        ("FuturePolicyClass", "object"),
        ("FuturePolicyError", "Exception"),
    ],
)
def test_slots_policy_rejects_nested_unregistered_instance_dict_classes(
    tmp_path: Path, name: str, base: str
) -> None:
    """A future nested class without slots cannot disappear from the policy audit."""
    source_root = _copy_clean_source(tmp_path)
    _write_nested_class(source_root, name, base)
    declarations = collect_class_declarations(source_root)

    with pytest.raises(EvidenceError) as error:
        validate_slots_inventory(declarations, REGISTERED_SLOTS_EXCEPTIONS)

    message = str(error.value)
    assert f"fast_fsm.nested.future_policy.{name}" in message
    assert "src/fast_fsm/nested/future_policy.py:1" in message


def test_slots_policy_rejects_stale_exception_registry_entries(tmp_path: Path) -> None:
    """Renamed or removed exceptions cannot remain silently allowlisted."""
    declarations = collect_class_declarations(_copy_clean_source(tmp_path))
    stale_registry = {
        **REGISTERED_SLOTS_EXCEPTIONS,
        "fast_fsm.core.RemovedException": "stale test fixture",
    }

    with pytest.raises(EvidenceError) as error:
        validate_slots_inventory(declarations, stale_registry)

    assert "fast_fsm.core.RemovedException" in str(error.value)


def _manifest_fixture() -> dict[str, object]:
    """Return a complete minimal stable manifest for comparison coverage."""
    return {
        "schema_version": 1,
        "release_identity": {"package": "fast_fsm", "version": "0.2.2"},
        "quality_baseline": {
            "build_mode": "pure",
            "tests": {"collected": 722, "passed": 722, "failed": 0},
            "coverage": {"total_percent": 90.12, "core_percent": 95.34},
            "source": {"core_origin": "src/fast_fsm/core.py"},
        },
        "toolchain": {"uv": "0.12.6"},
        "artifact_evidence": {"wheels": []},
        "slots_policy": {
            "inventory": [{"qualified_name": "fast_fsm.core.State"}],
            "registered_exceptions": [
                {"qualified_name": "fast_fsm.core.CompiledFuncCondition"},
                {"qualified_name": "fast_fsm.core.TransitionError"},
            ],
            "measurements": [],
        },
        "performance_contract": {"compiled_trigger_ops_per_sec_min": 200000},
        "measurement_environment": {"stable_fields": ["schema_version"]},
    }


def test_manifest_serialization_is_byte_stable_and_ends_with_one_newline() -> None:
    """Equivalent evidence has deterministic sorted JSON representation."""
    fixture = _manifest_fixture()
    first = serialize_manifest(fixture)
    second = serialize_manifest(dict(reversed(list(fixture.items()))))

    assert first == second
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    assert list(json.loads(first)) == sorted(fixture)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("schema_version",), 2),
        (("quality_baseline", "tests", "passed"), 721),
        (("toolchain", "uv"), "0.12.5"),
        (("quality_baseline", "source", "core_origin"), "src/fast_fsm/core.so"),
        (("slots_policy", "inventory"), []),
    ],
)
def test_manifest_comparison_reports_field_level_staleness(
    path: tuple[str, ...], replacement: object
) -> None:
    """Stable evidence drift has an actionable JSON-path diff."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    target: dict[str, object] = observed
    for part in path[:-1]:
        target = target[part]  # type: ignore[assignment,index]
    target[path[-1]] = replacement

    differences = compare_manifests(expected, observed)

    assert differences
    assert ".".join(path) in "\n".join(differences)


@pytest.mark.parametrize(
    ("field", "observed_value"),
    [
        ("total_percent", 90.11),
        ("core_percent", 95.33),
    ],
)
def test_manifest_rejects_two_decimal_source_coverage_regressions(
    field: str, observed_value: float
) -> None:
    """A lower total or core source percentage cannot silently refresh a baseline."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["quality_baseline"]["coverage"][field] = observed_value

    with pytest.raises(EvidenceError, match="coverage regression"):
        validate_manifest_regressions(expected, observed)


def test_manifest_write_then_check_is_read_only_and_renders_summary(
    tmp_path: Path,
) -> None:
    """Only an explicit write updates bytes; a succeeding check leaves them alone."""
    manifest_path = tmp_path / "release-baseline.json"
    fixture = _manifest_fixture()

    written = release_evidence.write_or_check_manifest(
        fixture, manifest_path=manifest_path, write=True
    )
    before_check = manifest_path.read_bytes()
    checked = release_evidence.write_or_check_manifest(
        fixture, manifest_path=manifest_path, write=False
    )

    assert written == checked
    assert before_check == manifest_path.read_bytes()
    assert "Pure tests: 722/722 passed" in release_evidence._render_summary(fixture)


def test_manifest_check_reports_staleness_without_rewriting(tmp_path: Path) -> None:
    """A changed exact test count fails check mode with a field-level diff."""
    manifest_path = tmp_path / "release-baseline.json"
    fixture = _manifest_fixture()
    release_evidence.write_or_check_manifest(
        fixture, manifest_path=manifest_path, write=True
    )
    original = manifest_path.read_bytes()
    observed = json.loads(serialize_manifest(fixture))
    observed["quality_baseline"]["tests"]["passed"] = 721

    with pytest.raises(EvidenceError, match="quality_baseline.tests.passed"):
        release_evidence.write_or_check_manifest(
            observed, manifest_path=manifest_path, write=False
        )

    assert manifest_path.read_bytes() == original


def test_collect_manifest_preflights_before_any_test_or_coverage_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed native-origin preflight prevents test and coverage collection."""
    calls: list[str] = []

    def fail_preflight(**_kwargs: object) -> dict[str, str]:
        calls.append("preflight")
        raise EvidenceError("native shadow")

    def collect_after_preflight(
        **_kwargs: object,
    ) -> tuple[dict[str, int], dict[str, float]]:
        calls.append("test-and-coverage")
        return (
            {"collected": 1, "passed": 1},
            {"total_percent": 100, "core_percent": 100},
        )

    monkeypatch.setattr(release_evidence, "_source_preflight", fail_preflight)
    monkeypatch.setattr(
        release_evidence, "_collect_test_and_coverage", collect_after_preflight
    )

    with pytest.raises(EvidenceError, match="native shadow"):
        release_evidence.collect_manifest()

    assert calls == ["preflight"]


def test_resolved_uv_must_match_the_phase_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An ambient uv executable cannot silently change release evidence."""
    monkeypatch.setattr(
        release_evidence,
        "_run_checked",
        lambda *_args, **_kwargs: "uv 0.12.5 (unexpected)\n",
    )

    with pytest.raises(EvidenceError, match="requires uv 0.12.6"):
        release_evidence._resolved_uv_version(environment={})


def test_build_tool_versions_are_read_from_the_reviewed_lock_not_runtime_imports(
    tmp_path: Path,
) -> None:
    """A PEP 517-only build input remains evidence without becoming a project dependency."""
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        "\n".join(
            [
                "version = 1",
                "",
                "[[package]]",
                'name = "wheel"',
                'version = "0.45.1"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert release_evidence._locked_package_version("wheel", lock_path) == "0.45.1"


def test_repository_lock_records_each_exact_release_build_tool() -> None:
    """The manifest can audit all exact PEP 517 inputs from uv.lock."""
    assert release_evidence._locked_package_version("setuptools") == "80.9.0"
    assert release_evidence._locked_package_version("wheel") == "0.45.1"
    assert release_evidence._locked_package_version("mypy") == "1.17.1"


def _workflow_text(path: Path) -> str:
    """Read a repository-owned GitHub workflow for contract assertions."""
    return path.read_text(encoding="utf-8")


def _workflow_data(path: Path = CI_WORKFLOW) -> dict[str, object]:
    """Load a workflow as YAML so step discovery cannot be fooled by prose."""
    data = yaml.safe_load(_workflow_text(path))
    assert isinstance(data, dict), path
    assert isinstance(data.get("jobs"), dict), path
    return data


def _workflow_jobs(workflow: dict[str, object]) -> dict[str, dict[str, object]]:
    """Return verified job mappings from a parsed workflow."""
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert all(isinstance(job_id, str) and isinstance(job, dict) for job_id, job in jobs.items())
    return jobs


def _task_invocation_steps(job: dict[str, object]) -> list[int]:
    """Find every shell step that executes Task, including multiline forms."""
    steps = job.get("steps")
    assert isinstance(steps, list)
    return [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict)
        and isinstance(step.get("run"), str)
        and _TASK_COMMAND.search(step["run"])
    ]


def _task_consuming_jobs(workflow: dict[str, object]) -> dict[str, list[int]]:
    """Return each Taskfile-consuming job and all of its invocation indices."""
    return {
        job_id: invocation_indices
        for job_id, job in _workflow_jobs(workflow).items()
        if (invocation_indices := _task_invocation_steps(job))
    }


def _validate_task_runner_steps(workflow: dict[str, object]) -> None:
    """Require one exact, earlier Task setup in every consuming CI job."""
    consumers = _task_consuming_jobs(workflow)
    assert set(consumers) == TASK_CONSUMING_CI_JOBS, (
        "Taskfile-consuming job set changed: "
        f"expected {sorted(TASK_CONSUMING_CI_JOBS)}, got {sorted(consumers)}"
    )

    for job_id, invocation_indices in consumers.items():
        job = _workflow_jobs(workflow)[job_id]
        steps = job["steps"]
        assert isinstance(steps, list)
        setup_steps = [
            (index, step)
            for index, step in enumerate(steps)
            if isinstance(step, dict)
            and isinstance(step.get("uses"), str)
            and step["uses"].startswith("arduino/setup-task@")
        ]
        assert setup_steps, f"{job_id}: missing pinned Task setup"
        assert len(setup_steps) == 1, f"{job_id}: expected exactly one Task setup"
        setup_index, setup_step = setup_steps[0]
        assert setup_step["uses"] == TASK_SETUP_ACTION, (
            f"{job_id}: Task setup must use the full verified action SHA"
        )
        inputs = setup_step.get("with")
        assert isinstance(inputs, dict), f"{job_id}: Task setup must provide inputs"
        assert inputs.get("version") == TASK_VERSION, (
            f"{job_id}: Task setup must pin version {TASK_VERSION}"
        )
        assert all(setup_index < index for index in invocation_indices), (
            f"{job_id}: Task setup must precede every Taskfile invocation"
        )


def _validate_task_runner_comments(workflow_text: str) -> None:
    """Keep the human-readable v3.0.0 provenance beside every exact SHA pin."""
    pinned_uses = re.findall(
        rf"(?m)^\s*- uses: {re.escape(TASK_SETUP_ACTION)} # v3\.0\.0$",
        workflow_text,
    )
    assert len(pinned_uses) == len(TASK_CONSUMING_CI_JOBS), (
        "Every exact Task action pin must retain its adjacent # v3.0.0 comment"
    )


def _workflow_with_pinned_task_setup(workflow: dict[str, object]) -> dict[str, object]:
    """Create a valid parsed-workflow fixture for negative mutation tests."""
    fixture = deepcopy(workflow)
    for job_id in TASK_CONSUMING_CI_JOBS:
        job = _workflow_jobs(fixture)[job_id]
        steps = job["steps"]
        assert isinstance(steps, list)
        uv_index = next(
            index
            for index, step in enumerate(steps)
            if isinstance(step, dict) and step.get("uses") == "astral-sh/setup-uv@v5"
        )
        steps.insert(
            uv_index + 1,
            {
                "name": "Install pinned Task runner",
                "uses": TASK_SETUP_ACTION,
                "with": {"version": TASK_VERSION},
            },
        )
    return fixture


def test_task_runner_contract_covers_every_taskfile_consuming_ci_job() -> None:
    """All current Taskfile jobs need an exact, earlier cross-platform setup."""
    _validate_task_runner_steps(_workflow_data())
    _validate_task_runner_comments(_workflow_text(CI_WORKFLOW))


def test_task_runner_contract_rejects_missing_late_or_mispinned_setup() -> None:
    """A sibling setup, late setup, action tag, or version drift cannot satisfy CI."""
    fixture = _workflow_with_pinned_task_setup(_workflow_data())

    missing = deepcopy(fixture)
    missing_steps = _workflow_jobs(missing)["format"]["steps"]
    assert isinstance(missing_steps, list)
    missing_steps[:] = [
        step
        for step in missing_steps
        if not isinstance(step, dict) or step.get("uses") != TASK_SETUP_ACTION
    ]
    with pytest.raises(AssertionError, match="format: missing pinned Task setup"):
        _validate_task_runner_steps(missing)

    late = deepcopy(fixture)
    late_steps = _workflow_jobs(late)["lint"]["steps"]
    assert isinstance(late_steps, list)
    setup = next(
        step
        for step in late_steps
        if isinstance(step, dict) and step.get("uses") == TASK_SETUP_ACTION
    )
    late_steps.remove(setup)
    late_steps.append(setup)
    with pytest.raises(AssertionError, match="lint: Task setup must precede"):
        _validate_task_runner_steps(late)

    wrong_sha = deepcopy(fixture)
    wrong_sha_steps = _workflow_jobs(wrong_sha)["typecheck_mypy"]["steps"]
    assert isinstance(wrong_sha_steps, list)
    next(
        step
        for step in wrong_sha_steps
        if isinstance(step, dict) and step.get("uses") == TASK_SETUP_ACTION
    )["uses"] = "arduino/setup-task@v3"
    with pytest.raises(AssertionError, match="typecheck_mypy: Task setup must use"):
        _validate_task_runner_steps(wrong_sha)

    wrong_version = deepcopy(fixture)
    wrong_version_steps = _workflow_jobs(wrong_version)["typecheck_ty"]["steps"]
    assert isinstance(wrong_version_steps, list)
    next(
        step
        for step in wrong_version_steps
        if isinstance(step, dict) and step.get("uses") == TASK_SETUP_ACTION
    )["with"]["version"] = "3.53.2"
    with pytest.raises(AssertionError, match="typecheck_ty: Task setup must pin"):
        _validate_task_runner_steps(wrong_version)


@pytest.mark.parametrize(
    "run",
    [
        "task format-check",
        "task first\ntask second",
        "echo ready && task lint",
        "FAST_FSM_BUILD_MODE=pure task test",
    ],
)
def test_task_runner_contract_detects_all_shell_invocation_forms(run: str) -> None:
    """Plain, block, multiline, and environment-prefixed Task runs cannot evade setup."""
    fixture = _workflow_with_pinned_task_setup(_workflow_data())
    job = _workflow_jobs(fixture)["build_check"]
    steps = job["steps"]
    assert isinstance(steps, list)
    steps.append({"name": "Unprovisioned Task variant", "run": run})

    with pytest.raises(AssertionError, match="Taskfile-consuming job set changed"):
        _validate_task_runner_steps(fixture)


def test_task_runner_detector_ignores_nonexecuting_prose() -> None:
    """A mention of Task in an echo command is not a Taskfile invocation."""
    assert not _TASK_COMMAND.search("echo task format-check")


def _setup_uv_blocks(workflow: str) -> list[str]:
    """Return each setup-uv step through its following configuration boundary."""
    return re.findall(
        r"- uses: astral-sh/setup-uv@v5(?P<block>.*?)(?=\n\s*- uses:|\n\s*- name:|\Z)",
        workflow,
        flags=re.DOTALL,
    )


def test_setup_uv_actions_pin_the_exact_release_version() -> None:
    """Every repository-owned setup-uv use shares the manifest's exact version."""
    for workflow_path in (CI_WORKFLOW, DOCS_WORKFLOW, RELEASE_WORKFLOW):
        blocks = _setup_uv_blocks(_workflow_text(workflow_path))
        assert blocks, workflow_path
        assert all('version: "0.12.6"' in block for block in blocks), workflow_path


def test_workflow_contract_has_dispatch_reusable_and_independent_gate_jobs() -> None:
    """Pull requests and releases expose every quality verdict independently."""
    workflow = _workflow_text(CI_WORKFLOW)
    for trigger in ("push:", "pull_request:", "workflow_dispatch:", "workflow_call:"):
        assert trigger in workflow
    for job in (
        "format",
        "lint",
        "typecheck_mypy",
        "typecheck_ty",
        "test",
        "supported_python_build",
        "evidence",
        "docs_html",
        "docs_doctest",
        "build_check",
        "benchmark",
    ):
        assert re.search(rf"^  {job}:$", workflow, flags=re.MULTILINE), job
    assert re.search(
        r"^  typecheck_ty:.*?^    continue-on-error: true$",
        workflow,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert "fail-fast: false" in workflow
    for version in ('"3.10"', '"3.11"', '"3.12"', '"3.13"', '"3.14"'):
        assert version in workflow


def test_clean_workflow_jobs_sync_then_immediately_preflight_in_pure_mode() -> None:
    """No test, coverage, documentation, or build collection precedes source proof."""
    required = {
        CI_WORKFLOW: (
            "test",
            "supported_python_build",
            "evidence",
            "docs_html",
            "docs_doctest",
        ),
        DOCS_WORKFLOW: ("build_docs",),
        RELEASE_WORKFLOW: ("build_sdist",),
    }
    preflight = "uv run python tools/release_evidence.py verify-source --json"
    for workflow_path, jobs in required.items():
        workflow = _workflow_text(workflow_path)
        for job in jobs:
            job_match = re.search(
                rf"^  {job}:$(.*?)(?=^  [A-Za-z_][A-Za-z0-9_]*:$|\Z)",
                workflow,
                flags=re.MULTILINE | re.DOTALL,
            )
            assert job_match, f"Missing {job} in {workflow_path}"
            body = job_match.group(1)
            assert "FAST_FSM_BUILD_MODE: pure" in body
            sync_index = body.index("uv sync --locked")
            preflight_index = body.index(preflight)
            assert sync_index < preflight_index
            between = body[sync_index:preflight_index]
            assert "uv run " not in between
            assert "uv build" not in between
            assert "pytest" not in between


def test_release_workflow_gates_artifacts_without_publishing_a_pure_wheel() -> None:
    """The reusable complete gate precedes existing artifacts; Phase 20 owns pure publication."""
    workflow = _workflow_text(RELEASE_WORKFLOW)
    assert "uses: ./.github/workflows/ci.yml" in workflow
    for job in ("build_wheels", "build_sdist"):
        job_match = re.search(
            rf"^  {job}:$(.*?)(?=^  [A-Za-z_][A-Za-z0-9_]*:$|\Z)",
            workflow,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert job_match
        assert "needs: quality_gate" in job_match.group(1)
    assert "FAST_FSM_BUILD_MODE: pure" in workflow
    assert "uv sync --locked" in workflow
    assert "py3-none-any" not in workflow
