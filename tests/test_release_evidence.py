"""Regression coverage for the maintainer-only release evidence CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable
from zipfile import ZipFile

import pytest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release_evidence import (  # noqa: E402
    REGISTERED_SLOTS_EXCEPTIONS,
    EvidenceError,
    collect_class_declarations,
    validate_slots_inventory,
)


PACKAGE_SOURCE = ROOT / "src" / "fast_fsm"
TOOL = ROOT / "tools" / "release_evidence.py"


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
    registered = {entry["qualified_name"]: entry for entry in evidence["registered_exceptions"]}
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
