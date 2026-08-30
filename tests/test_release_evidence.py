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
    collect_runtime_class_layouts,
    serialize_manifest,
    validate_runtime_slots_layouts,
    validate_slots_inventory,
    validate_manifest_regressions,
    validate_performance_observation,
)


PACKAGE_SOURCE = ROOT / "src" / "fast_fsm"
TOOL = ROOT / "tools" / "release_evidence.py"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
DOCS_WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
TASKFILE = ROOT / "Taskfile.yml"

TASK_SETUP_ACTION = "arduino/setup-task@c0bc642852239c2689f73f4ea6459c29405f3c52"
TASK_VERSION = "3.53.1"
SETUP_UV_ACTION = "astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86"
THIRD_PARTY_ACTION_PINS = {
    "actions/checkout": ("11d5960a326750d5838078e36cf38b85af677262", "v4"),
    "actions/configure-pages": ("983d7736d9b0ae728b81ab479565c72886d7745b", "v5"),
    "actions/deploy-pages": ("d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", "v4"),
    "actions/download-artifact": ("d3f86a106a0bac45b974a628896c90dbdf5c8093", "v4"),
    "actions/upload-artifact": ("ea165f8d65b6e75b540449e92b4886f43607fa02", "v4"),
    "actions/upload-pages-artifact": (
        "56afc609e74202658d3ffba0e8f6dda462b719fa",
        "v3",
    ),
    "arduino/setup-task": ("c0bc642852239c2689f73f4ea6459c29405f3c52", "v3.0.0"),
    "astral-sh/setup-uv": ("d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86", "v5"),
    "docker/setup-qemu-action": ("c7c53464625b32c7a7e944ae62b3e17d2b600130", "v3"),
    "pypa/cibuildwheel": ("ee63bf16da6cddfb925f542f2c7b59ad50e93969", "v2.22.0"),
    "pypa/gh-action-pypi-publish": (
        "ec4db0b4ddc65acdf4bff5fa45ac92d78b56bdf0",
        "v1.9.0",
    ),
    "softprops/action-gh-release": (
        "3bb12739c298aeb8a4eeaf626c5b8d85266b0e65",
        "v2",
    ),
}
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
    filename_name: str = "fast_fsm",
    dist_info_name: str = "fast_fsm",
    dist_info_version: str | None = None,
    metadata_name: str = "fast-fsm",
    metadata_version: str | None = None,
) -> Path:
    """Create a minimal wheel archive with independently controllable evidence."""
    wheel = directory / f"{filename_name}-{version}-{filename_tag}.whl"
    dist_info = f"{dist_info_name}-{dist_info_version or version}.dist-info"
    with ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: release-evidence-test\n"
            + "".join(f"Tag: {tag}\n" for tag in wheel_tags),
        )
        archive.writestr(
            f"{dist_info}/METADATA",
            "Metadata-Version: 2.1\n"
            f"Name: {metadata_name}\n"
            f"Version: {metadata_version or version}\n",
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


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"filename_name": "evil"}, "filename package name"),
        ({"dist_info_name": "evil"}, "dist-info package name"),
        ({"metadata_name": "evil"}, "metadata name"),
        ({"dist_info_version": "9.9"}, "dist-info version"),
        ({"metadata_version": "9.9"}, "metadata version"),
        ({"version": "0.2.3"}, "version contradicts release identity"),
    ],
)
def test_verify_wheel_rejects_every_contradictory_identity_surface(
    tmp_path: Path, overrides: dict[str, str], expected: str
) -> None:
    """Filename, dist-info, METADATA, and release identity must agree exactly."""
    wheel = _write_wheel(
        tmp_path,
        filename_tag="py3-none-any",
        wheel_tags=["py3-none-any"],
        **overrides,
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


@pytest.mark.parametrize(
    "source",
    [
        "class Base:\n    __slots__ = ()\n\nclass Child(Base):\n    pass\n",
        "class Base:\n    __slots__ = ('__dict__',)\n\nclass Child(Base):\n    __slots__ = ()\n",
        "class Child:\n    __slots__ = ('__dict__',)\n",
    ],
)
def test_slots_policy_fails_closed_for_inherited_or_declared_instance_dict(
    tmp_path: Path, source: str
) -> None:
    """A local subclass cannot inherit or declare an instance dictionary."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "slot_regression.py"
    target.write_text(source, encoding="utf-8")

    with pytest.raises(EvidenceError, match="fast_fsm.slot_regression.Child"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


@pytest.mark.parametrize(
    ("source", "class_name"),
    [
        ("class Child(ExternalBase):\n    __slots__ = ()\n", "Child"),
        (
            "SLOTS = ('__dict__',)\n\nclass DynamicSlots:\n    __slots__ = SLOTS\n",
            "DynamicSlots",
        ),
    ],
)
def test_slots_policy_rejects_unresolved_bases_and_dynamic_slot_aliases(
    tmp_path: Path, source: str, class_name: str
) -> None:
    """Unprovable inheritance and slots declarations cannot be certified."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "slot_regression.py"
    target.write_text(source, encoding="utf-8")

    with pytest.raises(EvidenceError, match=f"fast_fsm.slot_regression.{class_name}"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


def test_slots_policy_uses_qualified_imported_base_identities(tmp_path: Path) -> None:
    """An imported local base is not confused with a same-named reviewed class."""
    source_root = _copy_clean_source(tmp_path)
    package_root = source_root / "fast_fsm"
    (package_root / "safe_base.py").write_text(
        "class Shared:\n    __slots__ = ()\n", encoding="utf-8"
    )
    (package_root / "reviewed_shadow.py").write_text(
        "class Shared:\n    pass\n", encoding="utf-8"
    )
    (package_root / "slot_regression.py").write_text(
        "from .safe_base import Shared\n\nclass Child(Shared):\n    __slots__ = ()\n",
        encoding="utf-8",
    )

    inventory = validate_slots_inventory(
        collect_class_declarations(source_root),
        {
            **REGISTERED_SLOTS_EXCEPTIONS,
            "fast_fsm.reviewed_shadow.Shared": "reviewed fixture exception",
        },
    )

    child = next(
        item
        for item in inventory
        if item["qualified_name"] == "fast_fsm.slot_regression.Child"
    )
    assert child["classification"] == "slot-protected"


@pytest.mark.parametrize(
    ("source", "class_names"),
    [
        ("if True:\n    class Conditional:\n        pass\n", ("Conditional",)),
        (
            "if sys.version_info >= (3, 12):\n"
            "    class VersionConditional:\n"
            "        pass\n"
            "else:\n"
            "    class PlatformConditional:\n"
            "        pass\n",
            ("VersionConditional", "PlatformConditional"),
        ),
        (
            "try:\n"
            "    class TryConditional:\n"
            "        pass\n"
            "except ImportError:\n"
            "    class ExceptConditional:\n"
            "        pass\n",
            ("TryConditional", "ExceptConditional"),
        ),
        (
            "with context_manager:\n"
            "    class WithConditional:\n"
            "        pass\n"
            "match selector:\n"
            "    case _:\n"
            "        class MatchConditional:\n"
            "            pass\n",
            ("WithConditional", "MatchConditional"),
        ),
    ],
)
def test_slots_policy_recurses_through_module_control_flow(
    tmp_path: Path, source: str, class_names: tuple[str, ...]
) -> None:
    """Runtime-relevant module branches cannot hide un-slotted classes."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "conditional_policy.py"
    target.write_text(source, encoding="utf-8")

    with pytest.raises(EvidenceError) as error:
        validate_slots_inventory(collect_class_declarations(source_root), {})

    message = str(error.value)
    for class_name in class_names:
        assert f"fast_fsm.conditional_policy.{class_name}" in message


def test_slots_policy_rejects_ambiguous_conditional_class_definitions(
    tmp_path: Path,
) -> None:
    """Mutually exclusive branches cannot silently collapse one class identity."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "conditional_policy.py"
    target.write_text(
        "if selector:\n"
        "    class Ambiguous:\n"
        "        __slots__ = ()\n"
        "else:\n"
        "    class Ambiguous:\n"
        "        __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvidenceError, match="Ambiguous duplicate class definition.*Ambiguous"
    ):
        collect_class_declarations(source_root)


def test_slots_policy_excludes_only_main_and_type_checking_bodies(
    tmp_path: Path,
) -> None:
    """Demo/type-only classes stay out of the runtime inventory, not other scopes."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "conditional_policy.py"
    target.write_text(
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    class TypeOnly:\n"
        "        pass\n\n"
        "if __name__ == '__main__':\n"
        "    class DemoOnly:\n"
        "        pass\n\n"
        "class RuntimeProtected:\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )

    declarations = collect_class_declarations(source_root)
    names = {declaration.qualified_name for declaration in declarations}

    assert "fast_fsm.conditional_policy.TypeOnly" not in names
    assert "fast_fsm.conditional_policy.DemoOnly" not in names
    assert "fast_fsm.conditional_policy.RuntimeProtected" in names
    validate_slots_inventory(declarations, REGISTERED_SLOTS_EXCEPTIONS)


@pytest.mark.parametrize(
    ("source", "class_name"),
    [
        (
            "for value in values:\n    class LoopConditional:\n        pass\n",
            "LoopConditional",
        ),
        (
            "while enabled:\n"
            "    class WhileConditional:\n"
            "        pass\n"
            "else:\n"
            "    class WhileElseConditional:\n"
            "        pass\n",
            "WhileConditional",
        ),
        (
            "try:\n"
            "    class TryStarConditional:\n"
            "        pass\n"
            "except* ImportError:\n"
            "    class ExceptStarConditional:\n"
            "        pass\n",
            "TryStarConditional",
        ),
    ],
)
def test_slots_policy_recurses_through_module_loops_and_try_star(
    tmp_path: Path, source: str, class_name: str
) -> None:
    """Loop and exception-group bodies cannot hide runtime production classes."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "loop_policy.py"
    target.write_text(source, encoding="utf-8")

    with pytest.raises(EvidenceError, match=f"fast_fsm.loop_policy.{class_name}"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


def test_slots_policy_keeps_branch_local_imports_for_base_resolution(
    tmp_path: Path,
) -> None:
    """An alternate safe alias cannot certify a runtime branch's unsafe base."""
    source_root = _copy_clean_source(tmp_path)
    package_root = source_root / "fast_fsm"
    (package_root / "unsafe_base.py").write_text(
        "class Ordinary:\n    pass\n", encoding="utf-8"
    )
    (package_root / "branch_policy.py").write_text(
        "if runtime_selector:\n"
        "    from .unsafe_base import Ordinary as ABC\n\n"
        "    class RuntimeChild(ABC):\n"
        "        __slots__ = ()\n"
        "else:\n"
        "    from abc import ABC\n\n"
        "    class AlternateChild(ABC):\n"
        "        __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="fast_fsm.branch_policy.RuntimeChild"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


def test_slots_policy_rejects_ambiguous_reaching_base_bindings(tmp_path: Path) -> None:
    """A class after divergent aliases fails unless every possible base is safe."""
    source_root = _copy_clean_source(tmp_path)
    package_root = source_root / "fast_fsm"
    (package_root / "unsafe_base.py").write_text(
        "class Ordinary:\n    pass\n", encoding="utf-8"
    )
    (package_root / "branch_policy.py").write_text(
        "if runtime_selector:\n"
        "    from .unsafe_base import Ordinary as Base\n"
        "else:\n"
        "    from abc import ABC as Base\n\n"
        "class AmbiguousChild(Base):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="fast_fsm.branch_policy.AmbiguousChild"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


@pytest.mark.parametrize(
    "source",
    [
        "from abc import ABC as Base\n"
        "Base = type('Ordinary', (), {})\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
        "from abc import ABC as Base\n"
        "del Base\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
        "from abc import ABC as Base\n\n"
        "def Base():\n"
        "    return object\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
        "from abc import ABC as Base\n\n"
        "for Base in values:\n"
        "    pass\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
    ],
)
def test_slots_policy_invalidates_rebound_or_deleted_base_names(
    tmp_path: Path, source: str
) -> None:
    """Every ordinary module binding replaces a previously safe base identity."""
    source_root = _copy_clean_source(tmp_path)
    (source_root / "fast_fsm" / "binding_policy.py").write_text(
        source, encoding="utf-8"
    )

    with pytest.raises(EvidenceError, match="fast_fsm.binding_policy.Child"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


def test_slots_policy_invalidates_try_body_bindings_for_handlers(
    tmp_path: Path,
) -> None:
    """A handler sees unsafe imports made before a later exception in its try body."""
    source_root = _copy_clean_source(tmp_path)
    package_root = source_root / "fast_fsm"
    (package_root / "unsafe_base.py").write_text(
        "class Ordinary:\n    pass\n", encoding="utf-8"
    )
    (package_root / "handler_policy.py").write_text(
        "from abc import ABC as Base\n\n"
        "try:\n"
        "    from .unsafe_base import Ordinary as Base\n"
        "    raise RuntimeError\n"
        "except RuntimeError:\n"
        "    class Child(Base):\n"
        "        __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="fast_fsm.handler_policy.Child"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


def test_slots_policy_rejects_wildcard_imports_before_base_resolution(
    tmp_path: Path,
) -> None:
    """A wildcard may overwrite a safe alias through an imported module's __all__."""
    source_root = _copy_clean_source(tmp_path)
    package_root = source_root / "fast_fsm"
    (package_root / "wildcard_base.py").write_text(
        "class Ordinary:\n    pass\n\n__all__ = ['Base']\nBase = Ordinary\n",
        encoding="utf-8",
    )
    (package_root / "wildcard_policy.py").write_text(
        "from abc import ABC as Base\n"
        "from .wildcard_base import *\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="Wildcard import"):
        collect_class_declarations(source_root)


def test_slots_policy_keeps_nonmatching_match_environment(tmp_path: Path) -> None:
    """A non-exhaustive match may leave an unsafe incoming base unchanged."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "match_policy.py"
    target.write_text(
        "from .unsafe_base import Ordinary as Base\n\n"
        "match selector:\n"
        "    case 'safe':\n"
        "        from abc import ABC as Base\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )
    (source_root / "fast_fsm" / "unsafe_base.py").write_text(
        "class Ordinary:\n    pass\n", encoding="utf-8"
    )

    with pytest.raises(EvidenceError, match="fast_fsm.match_policy.Child"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


def test_slots_policy_rejects_imported_base_attribute_mutation(tmp_path: Path) -> None:
    """Mutating a qualified imported base cannot retain its safe certificate."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "attribute_mutation_policy.py"
    target.write_text(
        "import abc\n\n"
        "abc.ABC = type('Ordinary', (), {})\n\n"
        "class Child(abc.ABC):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="Imported binding mutation"):
        collect_class_declarations(source_root)


def test_slots_policy_rejects_setattr_of_imported_base(tmp_path: Path) -> None:
    """Built-in attribute mutation cannot hide behind an imported module alias."""
    source_root = _copy_clean_source(tmp_path)
    target = source_root / "fast_fsm" / "setattr_mutation_policy.py"
    target.write_text(
        "import abc\n\n"
        "setattr(abc, 'ABC', type('Ordinary', (), {}))\n\n"
        "class Child(abc.ABC):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="Imported binding mutation"):
        collect_class_declarations(source_root)


def test_slots_policy_invalidates_loop_bindings_after_break(tmp_path: Path) -> None:
    """An unreachable safe import after break cannot recertify an unsafe base."""
    source_root = _copy_clean_source(tmp_path)
    package_root = source_root / "fast_fsm"
    (package_root / "unsafe_base.py").write_text(
        "class Ordinary:\n    pass\n", encoding="utf-8"
    )
    (package_root / "loop_break_policy.py").write_text(
        "from abc import ABC as Base\n\n"
        "for _ in (1,):\n"
        "    from .unsafe_base import Ordinary as Base\n"
        "    break\n"
        "    from abc import ABC as Base\n\n"
        "class Child(Base):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="fast_fsm.loop_break_policy.Child"):
        validate_slots_inventory(collect_class_declarations(source_root), {})


@pytest.mark.parametrize(
    ("filename", "mutation"),
    [
        (
            "qualified_mutator_policy.py",
            "import builtins\nbuiltins.setattr(abc, 'ABC', type('Ordinary', (), {}))\n",
        ),
        (
            "vars_mutator_policy.py",
            "vars(abc)['ABC'] = type('Ordinary', (), {})\n",
        ),
        (
            "aliased_mutator_policy.py",
            "from builtins import setattr as mutate\n"
            "mutate(abc, 'ABC', type('Ordinary', (), {}))\n",
        ),
        (
            "dict_view_mutator_policy.py",
            "abc.__dict__['ABC'] = type('Ordinary', (), {})\n",
        ),
    ],
)
def test_slots_policy_rejects_indirect_imported_base_mutators(
    tmp_path: Path, filename: str, mutation: str
) -> None:
    """Qualified, mapped, and aliased standard mutators all invalidate abc."""
    source_root = _copy_clean_source(tmp_path)
    (source_root / "fast_fsm" / filename).write_text(
        "import abc\n" + mutation + "\nclass Child(abc.ABC):\n    __slots__ = ()\n",
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="Imported binding mutation"):
        collect_class_declarations(source_root)


@pytest.mark.parametrize(
    "mutation",
    [
        "import builtins\nbuiltins.setattr(abc, 'ABC', type('Ordinary', (), {}))\n",
        "vars(abc)['ABC'] = type('Ordinary', (), {})\n",
        "from builtins import setattr as mutate\n"
        "mutate(abc, 'ABC', type('Ordinary', (), {}))\n",
    ],
)
def test_runtime_slots_layout_audit_catches_indirect_mutators_without_static_help(
    tmp_path: Path, mutation: str
) -> None:
    """Actual layout detects every indirect mutation if static analysis is incomplete."""
    source_root = _copy_clean_source(tmp_path)
    declarations = collect_class_declarations(source_root)
    (source_root / "fast_fsm" / "runtime_indirect_policy.py").write_text(
        "import abc\n" + mutation + "\nclass Child(abc.ABC):\n    __slots__ = ()\n",
        encoding="utf-8",
    )
    declarations.append(
        release_evidence.ClassDeclaration(
            qualified_name="fast_fsm.runtime_indirect_policy.Child",
            source_path="src/fast_fsm/runtime_indirect_policy.py",
            line=4,
            base_references=("abc.ABC",),
            has_own_slots=True,
            slots_are_literal=True,
            declares_instance_dict=False,
        )
    )

    with pytest.raises(EvidenceError, match="fast_fsm.runtime_indirect_policy.Child"):
        validate_runtime_slots_layouts(declarations, source_root)


def test_runtime_slots_layout_audit_catches_dynamic_base_mutation(
    tmp_path: Path,
) -> None:
    """Runtime layout checks catch a dict-bearing base static syntax cannot resolve."""
    source_root = _copy_clean_source(tmp_path)
    (source_root / "fast_fsm" / "runtime_escape_policy.py").write_text(
        "import abc\n"
        "exec(\"abc.ABC = type('Ordinary', (), {})\")\n\n"
        "class Child(abc.ABC):\n"
        "    __slots__ = ()\n",
        encoding="utf-8",
    )
    declarations = collect_class_declarations(source_root)
    static_inventory = validate_slots_inventory(declarations)

    assert any(
        entry["qualified_name"] == "fast_fsm.runtime_escape_policy.Child"
        and entry["classification"] == "slot-protected"
        for entry in static_inventory
    )
    with pytest.raises(EvidenceError, match="fast_fsm.runtime_escape_policy.Child"):
        validate_runtime_slots_layouts(declarations, source_root)


def test_runtime_slots_layout_audit_preserves_registered_exceptions(
    tmp_path: Path,
) -> None:
    """Only the explicitly reviewed exception registry may retain dictionaries."""
    source_root = _copy_clean_source(tmp_path)
    declarations = collect_class_declarations(source_root)
    layouts = validate_runtime_slots_layouts(declarations, source_root)
    layouts_by_name = {entry["qualified_name"]: entry for entry in layouts}

    assert set(REGISTERED_SLOTS_EXCEPTIONS) <= set(layouts_by_name)
    assert all(
        layouts_by_name[name]["has_instance_dict"]
        for name in REGISTERED_SLOTS_EXCEPTIONS
    )
    assert all(
        not entry["has_instance_dict"]
        for name, entry in layouts_by_name.items()
        if name not in REGISTERED_SLOTS_EXCEPTIONS
    )


def test_runtime_layout_inventory_uses_selected_pure_source(tmp_path: Path) -> None:
    """The isolated layout loader reports classes from the passed source root."""
    source_root = _copy_clean_source(tmp_path)
    (source_root / "fast_fsm" / "runtime_layout_policy.py").write_text(
        "class RuntimeOnly:\n    __slots__ = ()\n",
        encoding="utf-8",
    )

    layouts = collect_runtime_class_layouts(source_root)

    assert any(
        entry["qualified_name"] == "fast_fsm.runtime_layout_policy.RuntimeOnly"
        and entry["has_instance_dict"] is False
        for entry in layouts
    )


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
        "toolchain": {"python": "3.12.10", "uv": "0.12.6"},
        "artifact_evidence": {"wheels": []},
        "slots_policy": {
            "inventory": [{"qualified_name": "fast_fsm.core.State"}],
            "registered_exceptions": [
                {"qualified_name": "fast_fsm.core.CompiledFuncCondition"},
                {"qualified_name": "fast_fsm.core.TransitionError"},
            ],
            "measurements": [],
        },
        "performance_contract": {
            "compiled_trigger_ops_per_sec_min": 200000,
            "observation": {
                "command": "tools/release_evidence.py evidence (fixture)",
                "mode": "pure",
                "metric": "StateMachine.trigger operations per second",
                "operations": 2000,
                "warmup_operations": 200,
                "elapsed_seconds": 0.02,
                "ops_per_second": 100000.0,
                "environment": {
                    "implementation": "cpython",
                    "python_version": "3.12.10",
                    "platform": "fixture-platform",
                    "machine": "fixture-machine",
                },
            },
        },
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


def test_manifest_freshness_accepts_same_minor_python_patches_without_mutation() -> (
    None
):
    """Comparison treats only Python's major.minor as portable evidence."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["toolchain"]["python"] = "3.12.3"
    expected_before = serialize_manifest(expected)
    observed_before = serialize_manifest(observed)

    assert compare_manifests(expected, observed) == []
    assert serialize_manifest(expected) == expected_before
    assert serialize_manifest(observed) == observed_before
    assert '"python": "3.12.10"' in expected_before
    assert '"python": "3.12.3"' in observed_before


@pytest.mark.parametrize("observed_python", ["3.11.9", "3.13.0"])
def test_manifest_freshness_rejects_different_python_minors(
    observed_python: str,
) -> None:
    """Python minor drift remains an actionable stable-field difference."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["toolchain"]["python"] = observed_python

    differences = compare_manifests(expected, observed)

    assert differences
    assert "toolchain.python" in "\n".join(differences)


@pytest.mark.parametrize("observed_python", ["3", "3.12", "3.x.1", "python"])
def test_manifest_freshness_fails_closed_for_malformed_python_identity(
    observed_python: str,
) -> None:
    """Missing or nonnumeric Python minor identities cannot be normalized away."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["toolchain"]["python"] = observed_python

    with pytest.raises(EvidenceError, match="toolchain.python"):
        compare_manifests(expected, observed)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("collected", 782),
        ("passed", 782),
        ("failed", 1),
    ],
)
def test_manifest_freshness_keeps_exact_test_inventory_strict(
    field: str, replacement: int
) -> None:
    """Test outcomes and counts stay stale even when Python patches agree."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["toolchain"]["python"] = "3.12.3"
    observed["quality_baseline"]["tests"][field] = replacement

    differences = compare_manifests(expected, observed)

    assert differences
    rendered = "\n".join(differences)
    assert f"quality_baseline.tests.{field}" in rendered
    assert "toolchain.python" not in rendered


def test_manifest_freshness_keeps_non_python_toolchain_pins_strict() -> None:
    """Exact uv pins remain stable fields while Python patch drift is portable."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["toolchain"]["python"] = "3.12.3"
    observed["toolchain"]["uv"] = "0.12.5"

    differences = compare_manifests(expected, observed)

    rendered = "\n".join(differences)
    assert "toolchain.uv" in rendered
    assert "toolchain.python" not in rendered


def test_manifest_coverage_regression_stays_blocking_across_python_patches() -> None:
    """Portable Python patch comparison cannot bypass coverage regression checks."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observed["toolchain"]["python"] = "3.12.3"
    observed["quality_baseline"]["coverage"]["total_percent"] = 90.11

    with pytest.raises(EvidenceError, match="coverage regression"):
        validate_manifest_regressions(expected, observed)


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


def test_manifest_requires_a_valid_environment_labeled_benchmark_observation() -> None:
    """Volatile timing may vary, but complete positive evidence cannot disappear."""
    manifest = _manifest_fixture()
    validate_performance_observation(manifest)

    missing = json.loads(serialize_manifest(manifest))
    del missing["performance_contract"]["observation"]
    with pytest.raises(EvidenceError, match="performance_contract.observation"):
        validate_performance_observation(missing)

    malformed = json.loads(serialize_manifest(manifest))
    malformed["performance_contract"]["observation"]["ops_per_second"] = 0
    with pytest.raises(EvidenceError, match="positive measurements"):
        validate_performance_observation(malformed)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("elapsed_seconds", float("nan")),
        ("elapsed_seconds", float("inf")),
        ("ops_per_second", float("-inf")),
    ],
)
def test_manifest_rejects_non_finite_benchmark_measurements(
    field: str, value: float
) -> None:
    """Volatile measurements still have to be finite JSON-compatible numbers."""
    manifest = _manifest_fixture()
    observation = manifest["performance_contract"]["observation"]
    assert isinstance(observation, dict)
    observation[field] = value

    with pytest.raises(EvidenceError, match="finite positive measurements"):
        validate_performance_observation(manifest)
    with pytest.raises(ValueError, match="Out of range float values"):
        serialize_manifest(manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("operations", True),
        ("warmup_operations", False),
        ("operations", 1.5),
        ("warmup_operations", 2.0),
        ("operations", "2000"),
    ],
)
def test_manifest_rejects_non_integer_benchmark_operation_counts(
    field: str, value: object
) -> None:
    """Operation counts are integral evidence, not truthy or coercible values."""
    manifest = _manifest_fixture()
    observation = manifest["performance_contract"]["observation"]
    assert isinstance(observation, dict)
    observation[field] = value

    with pytest.raises(EvidenceError, match="integer operation counts"):
        validate_performance_observation(manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("operations", 10**10000, id="huge-integer"),
        ("elapsed_seconds", 5e-324),
        ("operations", 10**308),
    ],
)
def test_manifest_rejects_overflowing_benchmark_rate_calculations(
    field: str, value: object
) -> None:
    """Extreme finite JSON values cannot crash or bypass rate consistency."""
    manifest = _manifest_fixture()
    observation = manifest["performance_contract"]["observation"]
    assert isinstance(observation, dict)
    observation[field] = value
    observation["ops_per_second"] = 1.0

    with pytest.raises(EvidenceError, match="finite positive measurements"):
        validate_performance_observation(manifest)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_manifest_reader_rejects_non_standard_json_numbers(
    tmp_path: Path, token: str
) -> None:
    """Tracked evidence cannot use Python's permissive non-standard constants."""
    manifest_path = tmp_path / "release-baseline.json"
    malformed = serialize_manifest(_manifest_fixture()).replace(
        '"elapsed_seconds": 0.02', f'"elapsed_seconds": {token}'
    )
    manifest_path.write_text(malformed, encoding="utf-8")

    with pytest.raises(EvidenceError, match="Could not read manifest"):
        release_evidence.write_or_check_manifest(
            _manifest_fixture(), manifest_path=manifest_path, write=False
        )


def test_manifest_freshness_excludes_only_volatile_benchmark_measurements() -> None:
    """A valid benchmark measurement may change without weakening its presence contract."""
    expected = _manifest_fixture()
    observed = json.loads(serialize_manifest(expected))
    observation = observed["performance_contract"]["observation"]
    observation["elapsed_seconds"] = 0.04
    observation["ops_per_second"] = 50000.0
    observation["environment"]["machine"] = "another-machine"

    validate_performance_observation(observed)
    assert compare_manifests(expected, observed) == []


def test_trigger_benchmark_collects_structured_environment_labeled_evidence() -> None:
    """The manifest collector runs a concrete benchmark rather than recording prose."""
    observation = release_evidence._collect_trigger_benchmark(
        iterations=100, warmup_iterations=10
    )

    assert observation["operations"] == 200
    assert observation["mode"] == "pure"
    assert "release_evidence.py evidence" in observation["command"]
    validate_performance_observation(
        {"performance_contract": {"observation": observation}}
    )


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


def test_collect_manifest_builds_one_temporary_wheel_after_preflight_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The canonical wheel path is Python-managed and cannot leak a Taskfile temp dir."""
    calls: list[str] = []
    observed_wheel: list[Path] = []

    def preflight(**_kwargs: object) -> dict[str, str]:
        calls.append("preflight")
        return {
            "core_origin": "src/fast_fsm/core.py",
            "distribution_version": "0.2.2",
        }

    def build(arguments: Iterable[str], **_kwargs: object) -> str:
        calls.append("build")
        arguments = list(arguments)
        assert arguments[:3] == ["uv", "build", "--wheel"]
        _write_wheel(
            Path(arguments[-1]),
            filename_tag="py3-none-any",
            wheel_tags=["py3-none-any"],
        )
        return ""

    def collect(**kwargs: object) -> dict[str, object]:
        calls.append("collect")
        wheel_paths = tuple(kwargs["wheel_paths"])
        assert len(wheel_paths) == 1
        observed_wheel.extend(wheel_paths)
        assert wheel_paths[0].is_file()
        return {"status": "collected"}

    monkeypatch.setattr(release_evidence, "_source_preflight", preflight)
    monkeypatch.setattr(release_evidence, "_run_checked", build)
    monkeypatch.setattr(release_evidence, "_collect_manifest_after_preflight", collect)

    assert release_evidence.collect_manifest(build_wheel=True) == {
        "status": "collected"
    }
    assert calls == ["preflight", "build", "collect"]
    assert observed_wheel and not observed_wheel[0].parent.exists()


@pytest.mark.parametrize("count", [0, 2])
def test_temporary_wheel_selection_requires_exactly_one_archive(
    tmp_path: Path, count: int
) -> None:
    """Canonical evidence has the same one-wheel semantics on every platform."""
    for index in range(count):
        _write_wheel(
            tmp_path,
            filename_tag=f"py3-none-any.{index}",
            wheel_tags=["py3-none-any"],
        )

    with pytest.raises(EvidenceError, match="exactly one temporary wheel"):
        release_evidence._exactly_one_wheel(tmp_path)


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


def _taskfile_data() -> dict[str, object]:
    """Load the task contract so ordering checks do not rely on prose layout."""
    data = yaml.safe_load(_workflow_text(TASKFILE))
    assert isinstance(data, dict)
    assert isinstance(data.get("tasks"), dict)
    return data


def _task_definitions(taskfile: dict[str, object]) -> dict[str, dict[str, object]]:
    """Return validated Taskfile task mappings."""
    tasks = taskfile["tasks"]
    assert isinstance(tasks, dict)
    assert all(
        isinstance(name, str) and isinstance(task, dict) for name, task in tasks.items()
    )
    return tasks


PURE_IMPORT_TASKS = frozenset(
    {
        "test",
        "test-verbose",
        "test-fast",
        "test-coverage",
        "docs",
        "docs-check",
        "docs-test",
    }
)


def _validate_taskfile_pure_source_order(taskfile: dict[str, object]) -> None:
    """Require source preflight before every independently runnable pure import task."""
    tasks = _task_definitions(taskfile)
    for task_name in PURE_IMPORT_TASKS:
        task = tasks[task_name]
        assert task.get("env", {}).get("FAST_FSM_BUILD_MODE") == "pure", task_name
        dependencies = task.get("deps", [])
        assert {"task": "pure-source-check"} in dependencies, (
            f"{task_name}: pure-source-check must run before package import"
        )
    release_commands = tasks["release-gate"].get("cmds", [])
    assert release_commands and release_commands[0] == {"task": "pure-source-check"}, (
        "release-gate must run pure-source-check before every aggregate component"
    )


def test_taskfile_pure_source_preflight_precedes_local_test_and_docs_tasks() -> None:
    """Taskfile gates cannot label native imports as pure-mode proof."""
    _validate_taskfile_pure_source_order(_taskfile_data())

    mutated = deepcopy(_taskfile_data())
    tasks = _task_definitions(mutated)
    tasks["docs-check"].pop("deps")
    with pytest.raises(AssertionError, match="docs-check: pure-source-check"):
        _validate_taskfile_pure_source_order(mutated)


def test_taskfile_baseline_tasks_delegate_temp_wheel_lifecycle_to_python() -> None:
    """Windows and POSIX use one Python cleanup path instead of shell utilities."""
    taskfile = _taskfile_data()
    tasks = _task_definitions(taskfile)
    for task_name, mode in (
        ("release-baseline-write", "--write"),
        ("release-baseline-check", "--check"),
    ):
        commands = tasks[task_name]["cmds"]
        assert isinstance(commands, list)
        rendered = "\n".join(str(command) for command in commands)
        assert "mktemp" not in rendered
        assert "find " not in rendered
        assert f"evidence {mode}" in rendered
        assert "--build-wheel" in rendered


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
    assert all(
        isinstance(job_id, str) and isinstance(job, dict)
        for job_id, job in jobs.items()
    )
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
        uv_indices = [
            index
            for index, step in enumerate(steps)
            if isinstance(step, dict) and step.get("uses") == SETUP_UV_ACTION
        ]
        assert len(uv_indices) == 1, f"{job_id}: expected exactly one uv setup"
        assert setup_index == uv_indices[0] + 1, (
            f"{job_id}: Task setup must immediately follow uv setup"
        )
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
        rf"(?m)^\s*uses: {re.escape(TASK_SETUP_ACTION)} # v3\.0\.0$",
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
        steps[:] = [
            step
            for step in steps
            if not (
                isinstance(step, dict)
                and isinstance(step.get("uses"), str)
                and step["uses"].startswith("arduino/setup-task@")
            )
        ]
        uv_index = next(
            index
            for index, step in enumerate(steps)
            if isinstance(step, dict) and step.get("uses") == SETUP_UV_ACTION
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
    with pytest.raises(
        AssertionError, match="lint: Task setup must immediately follow"
    ):
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
    """Return each pinned setup-uv step through its following configuration boundary."""
    return re.findall(
        rf"- uses: {re.escape(SETUP_UV_ACTION)} # v5(?P<block>.*?)(?=\n\s*- uses:|\n\s*- name:|\Z)",
        workflow,
        flags=re.DOTALL,
    )


def test_setup_uv_actions_pin_the_exact_release_version() -> None:
    """Every repository-owned setup-uv use shares the manifest's exact version."""
    for workflow_path in (CI_WORKFLOW, DOCS_WORKFLOW, RELEASE_WORKFLOW):
        blocks = _setup_uv_blocks(_workflow_text(workflow_path))
        assert blocks, workflow_path
        assert all('version: "0.12.6"' in block for block in blocks), workflow_path


def _third_party_action_uses(workflow: dict[str, object]) -> set[str]:
    """Return executable non-local actions from parsed workflow job steps."""
    actions: set[str] = set()
    for job in _workflow_jobs(workflow).values():
        steps = job.get("steps", [])
        assert isinstance(steps, list)
        for step in steps:
            if not isinstance(step, dict):
                continue
            action = step.get("uses")
            if isinstance(action, str) and not action.startswith("./"):
                actions.add(action)
    return actions


def _validate_action_pins(workflow_path: Path) -> None:
    """Require every executable third-party action to be pinned and documented."""
    parsed_uses = _third_party_action_uses(_workflow_data(workflow_path))
    expected_uses = {
        f"{repository}@{sha}"
        for repository, (sha, _version) in THIRD_PARTY_ACTION_PINS.items()
    }
    assert parsed_uses <= expected_uses, (
        f"{workflow_path}: unpinned or unknown executable action(s): "
        f"{sorted(parsed_uses - expected_uses)}"
    )
    text = _workflow_text(workflow_path)
    for action in parsed_uses:
        repository, sha = action.split("@", 1)
        assert re.fullmatch(r"[0-9a-f]{40}", sha), action
        expected_sha, version = THIRD_PARTY_ACTION_PINS[repository]
        assert sha == expected_sha
        assert f"uses: {action} # {version}" in text


def test_workflow_actions_use_reviewed_immutable_pins() -> None:
    """Tags cannot regain execution authority through a future workflow edit."""
    for workflow_path in (CI_WORKFLOW, DOCS_WORKFLOW, RELEASE_WORKFLOW):
        _validate_action_pins(workflow_path)
        for action in re.findall(
            r"(?m)^\s*(?:#\s*)?(?:-\s*)?uses:\s+([^\s#]+)",
            _workflow_text(workflow_path),
        ):
            if action.startswith("./"):
                continue
            repository, sha = action.split("@", 1)
            assert re.fullmatch(r"[0-9a-f]{40}", sha), action
            expected_sha, version = THIRD_PARTY_ACTION_PINS[repository]
            assert sha == expected_sha
            assert f"uses: {action} # {version}" in _workflow_text(workflow_path)

    mutated = _workflow_data(CI_WORKFLOW)
    steps = _workflow_jobs(mutated)["format"]["steps"]
    assert isinstance(steps, list)
    next(
        step
        for step in steps
        if isinstance(step, dict) and step.get("uses") == SETUP_UV_ACTION
    )["uses"] = "astral-sh/setup-uv@v5"
    with pytest.raises(AssertionError, match="unpinned or unknown"):
        parsed_uses = _third_party_action_uses(mutated)
        expected_uses = {
            f"{repository}@{sha}"
            for repository, (sha, _version) in THIRD_PARTY_ACTION_PINS.items()
        }
        assert parsed_uses <= expected_uses, (
            "unpinned or unknown executable action(s): "
            f"{sorted(parsed_uses - expected_uses)}"
        )


def test_workflow_permissions_follow_least_privilege_boundaries() -> None:
    """Only the two publication jobs receive their distinct write privileges."""
    ci = _workflow_data(CI_WORKFLOW)
    docs = _workflow_data(DOCS_WORKFLOW)
    release = _workflow_data(RELEASE_WORKFLOW)

    assert ci.get("permissions") == {"contents": "read"}
    assert docs.get("permissions") == {"contents": "read"}
    assert release.get("permissions") == {"contents": "read"}
    assert "permissions" not in _workflow_jobs(docs)["build_docs"]
    assert _workflow_jobs(docs)["deploy_docs"]["permissions"] == {
        "pages": "write",
        "id-token": "write",
    }
    assert _workflow_jobs(release)["github_release"]["permissions"] == {
        "contents": "write"
    }
    for job_id, job in _workflow_jobs(release).items():
        if job_id != "github_release":
            assert "permissions" not in job, job_id


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
