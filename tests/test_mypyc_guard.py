"""
ADR-003 compliance guard: mypyc subclassing safety.

``core.py`` is compiled by mypyc.  Any class that users subclass from
interpreted Python must carry ``@mypyc_attr(allow_interpreted_subclasses=True)``
or it will silently work in pure-Python mode and crash at import time when the
compiled extension is loaded.

This module performs a static AST analysis of ``core.py`` source so the
check is independent of whether the module is currently compiled or not.

When to add entries to INTERNAL_CLOSED
---------------------------------------
Only if a new class:
  - inherits (directly or transitively) from ``State`` or ``ABC``, AND
  - is intentionally sealed / not designed for user subclassing.

Otherwise just add ``@mypyc_attr(allow_interpreted_subclasses=True)`` to the
new class — that is the correct fix.

See ADR-003 (.specify/decisions/ADR-003-mypyc-compilation-boundary.md)
for full rationale.
"""

import ast
import importlib.util
import json
import os
from pathlib import Path
import stat
import threading

import pytest

CORE_PY = Path(__file__).parent.parent / "src" / "fast_fsm" / "core.py"
PACKAGE_INIT = Path(__file__).parent.parent / "src" / "fast_fsm" / "__init__.py"
SETUP_PY = Path(__file__).parent.parent / "setup.py"
PHASE16_RUNNER = Path(__file__).parent.parent / "tools" / "phase16_isolated_verify.py"

# Classes that inherit (transitively) from State or ABC but are intentionally
# sealed — not designed for user subclassing.  Exempt from the decorator
# requirement.  Add new entries here with a short justification comment.
INTERNAL_CLOSED: frozenset[str] = frozenset(
    # (empty — all current State-hierarchy classes are open for subclassing)
)


def _has_allow_interpreted(class_node: ast.ClassDef) -> bool:
    """Return True iff the class is decorated with
    ``@mypyc_attr(allow_interpreted_subclasses=True)``."""
    for decorator in class_node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "mypyc_attr"
        ):
            for kw in decorator.keywords:
                if kw.arg == "allow_interpreted_subclasses" and (
                    isinstance(kw.value, ast.Constant) and kw.value.value is True
                ):
                    return True
    return False


def _direct_base_names(class_node: ast.ClassDef) -> set[str]:
    """Return the set of simple name strings for a class's direct bases."""
    names: set[str] = set()
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def _collect_subclassable(classes: dict[str, ast.ClassDef]) -> set[str]:
    """
    Return the set of class names that are in the ``State`` or ``ABC``
    inheritance graph (direct and transitive).
    """
    seed_bases = {"State", "ABC"}
    subclassable: set[str] = set()

    # Seed: classes whose direct bases include State or ABC
    for name, node in classes.items():
        if _direct_base_names(node) & seed_bases or name in seed_bases:
            subclassable.add(name)

    # Propagate transitively
    changed = True
    while changed:
        changed = False
        for name, node in classes.items():
            if name not in subclassable and _direct_base_names(node) & subclassable:
                subclassable.add(name)
                changed = True

    return subclassable


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_all_user_subclassable_state_classes_have_mypyc_attr() -> None:
    """Every class in core.py that inherits (directly or transitively) from
    ``State`` or ``ABC`` must carry
    ``@mypyc_attr(allow_interpreted_subclasses=True)``.

    If your new class IS user-subclassable: add the decorator.
    If your new class is intentionally sealed: add it to INTERNAL_CLOSED.
    """
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))

    classes: dict[str, ast.ClassDef] = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }

    subclassable = _collect_subclassable(classes)
    candidates = subclassable - INTERNAL_CLOSED

    missing = [
        f"  {name} (line {classes[name].lineno})"
        for name in sorted(candidates)
        if not _has_allow_interpreted(classes[name])
    ]

    assert not missing, (
        "The following classes in core.py inherit from State or ABC but are "
        "missing @mypyc_attr(allow_interpreted_subclasses=True).\n\n"
        "Fix: add the decorator, or add the class name to INTERNAL_CLOSED in\n"
        "tests/test_mypyc_guard.py if the class is intentionally sealed.\n\n"
        "Missing:\n" + "\n".join(missing)
    )


def test_no_unexpected_classes_exempted() -> None:
    """INTERNAL_CLOSED should only name classes that actually exist in core.py
    and are members of the subclassable set.  Stale entries indicate a class
    was removed or renamed without updating the exemption list."""
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))

    classes: dict[str, ast.ClassDef] = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }

    subclassable = _collect_subclassable(classes)

    stale = sorted(INTERNAL_CLOSED - subclassable)
    assert not stale, (
        "INTERNAL_CLOSED in tests/test_mypyc_guard.py contains names that are "
        "not in core.py's State/ABC hierarchy (stale or mistyped):\n"
        + "\n".join(f"  {n}" for n in stale)
    )


def test_known_classes_have_decorator() -> None:
    """Explicit regression test for the four currently-decorated classes.
    If one of them loses the decorator during a refactor, this test catches it
    with a more specific failure message than the general guard above."""
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))

    classes: dict[str, ast.ClassDef] = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }

    expected = ["State", "CallbackState", "DeclarativeState", "AsyncDeclarativeState"]
    for name in expected:
        assert name in classes, f"{name} not found in core.py — was it renamed?"
        assert _has_allow_interpreted(classes[name]), (
            f"{name} is missing @mypyc_attr(allow_interpreted_subclasses=True). "
            f"This decorator is required for mypyc-compiled classes that users "
            f"subclass from interpreted Python. See ADR-003."
        )


def test_private_graph_records_are_frozen_slot_dataclasses() -> None:
    """The private graph records must keep the compiled core's slot boundary."""
    tree = ast.parse(CORE_PY.read_text(encoding="utf-8"), filename=str(CORE_PY))
    classes = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    for name, fields in {
        "_GraphTransition": {"from_state", "trigger", "to_state", "condition"},
        "_GraphSnapshot": {
            "name",
            "initial_state",
            "graph_version",
            "states",
            "transitions",
        },
        "_PreparedTransition": {"trigger", "sources", "target", "condition"},
    }.items():
        node = classes.get(name)
        assert node is not None, f"{name} must remain in the compiled core unit"
        decorator = next(
            (
                item
                for item in node.decorator_list
                if isinstance(item, ast.Call)
                and isinstance(item.func, ast.Name)
                and item.func.id == "dataclass"
            ),
            None,
        )
        assert decorator is not None, f"{name} must be a dataclass"
        keywords = {
            keyword.arg: keyword.value.value
            for keyword in decorator.keywords
            if isinstance(keyword.value, ast.Constant)
        }
        assert keywords.get("frozen") is True
        assert keywords.get("slots") is True
        assert {
            item.target.id
            for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        } == fields


def test_state_machine_graph_version_remains_in_slots() -> None:
    """Graph topology versioning must not add a dynamic instance dictionary."""
    tree = ast.parse(CORE_PY.read_text(encoding="utf-8"), filename=str(CORE_PY))
    state_machine = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "StateMachine"
    )
    slots = next(
        node.value
        for node in state_machine.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__slots__"
            for target in node.targets
        )
    )
    assert isinstance(slots, ast.Tuple)
    assert "_graph_version" in {
        item.value for item in slots.elts if isinstance(item, ast.Constant)
    }


def test_private_graph_records_are_not_public_exports() -> None:
    """The Phase 16 internal graph contract must not widen ``fast_fsm.__all__``."""
    tree = ast.parse(
        PACKAGE_INIT.read_text(encoding="utf-8"), filename=str(PACKAGE_INIT)
    )
    exported = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        )
    )
    assert isinstance(exported, ast.List)
    names = {item.value for item in exported.elts if isinstance(item, ast.Constant)}
    assert not {"_GraphTransition", "_GraphSnapshot", "_PreparedTransition"} & names


def test_setup_keeps_core_as_the_only_mypyc_source() -> None:
    """Selective compilation remains core.py-only even as private seams grow."""
    tree = ast.parse(SETUP_PY.read_text(encoding="utf-8"), filename=str(SETUP_PY))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "mypycify"
    ]
    assert len(calls) == 1
    assert isinstance(calls[0].args[0], ast.List)
    assert [item.value for item in calls[0].args[0].elts] == ["src/fast_fsm/core.py"]


def test_phase16_runner_has_fail_closed_isolation_guards() -> None:
    """The helper keeps its explicit-overlay and asserted-origin safety seams."""
    source = PHASE16_RUNNER.read_text(encoding="utf-8")
    for required in (
        "git",
        "archive",
        "_assert_relative_include",
        "_overlay",
        "_assert_origin",
        "FAST_FSM_BUILD_MODE",
        "_native_artifacts",
        "_validate_child_command",
        "_coverage_percentage",
        "isfinite",
        "baseline-write",
        "manifest-output",
        "NamedTemporaryFile",
        "copyfileobj",
        "fsync",
        "os.replace",
    ):
        assert required in source


def test_phase16_runner_treats_task_commands_as_trusted(tmp_path: Path) -> None:
    """Task mode selects an initial cwd but deliberately is not a sandbox."""
    spec = importlib.util.spec_from_file_location("phase16_runner", PHASE16_RUNNER)
    assert spec is not None
    assert spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    runner._validate_child_command(("sh", "-c", "cd /tmp && true"), tmp_path)


def test_phase16_runner_covers_boundary_negative_in_both_modes() -> None:
    """Changed boundary behavior belongs in the canonical parity command."""
    source = PHASE16_RUNNER.read_text(encoding="utf-8")

    assert source.count('"tests/test_boundary_negative.py"') == 2


def _load_phase16_runner():
    """Load the standalone Phase 16 runner without importing Fast FSM."""
    spec = importlib.util.spec_from_file_location("phase16_runner", PHASE16_RUNNER)
    assert spec is not None
    assert spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def _write_coverage_manifest(
    path: Path,
    total: object,
    core: object,
    *,
    collected: object = 1129,
    passed: object = 1129,
    failed: object = 0,
    errors: object = 0,
) -> None:
    path.write_text(
        json.dumps(
            {
                "quality_baseline": {
                    "coverage": {
                        "total_percent": total,
                        "core_percent": core,
                    },
                    "tests": {
                        "collected": collected,
                        "passed": passed,
                        "failed": failed,
                        "errors": errors,
                    },
                }
            }
        ),
        encoding="utf-8",
    )


def _manifest_destination(
    runner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Path:
    """Create a real repository-relative manifest destination for the runner."""
    source_root = tmp_path / "repo"
    destination = source_root / "evidence" / "release-baseline.json"
    destination.parent.mkdir(parents=True)
    monkeypatch.setattr(runner, "ROOT", source_root)
    return destination


def test_phase16_baseline_write_refuses_lower_coverage_before_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An isolated write cannot redefine an existing coverage floor downward."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(destination, 96.08, 94.27)
    _write_coverage_manifest(generated, 96.07, 94.26)
    original = destination.read_bytes()

    with pytest.raises(runner.VerificationError, match="coverage floor regression"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert destination.read_bytes() == original


def test_phase16_baseline_write_does_not_follow_legacy_temp_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale predictable temp symlink cannot write outside the destination."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    victim = tmp_path / "victim.json"
    _write_coverage_manifest(generated, 96.16, 94.50)
    victim.write_bytes(b"do not overwrite")
    legacy_temporary = destination.with_name(f".{destination.name}.phase16-tmp")
    legacy_temporary.symlink_to(victim)

    runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert destination.read_bytes() == generated.read_bytes()
    assert victim.read_bytes() == b"do not overwrite"
    assert legacy_temporary.is_symlink()
    assert legacy_temporary.resolve() == victim


@pytest.mark.parametrize("victim_location", ("inside", "outside"))
def test_phase16_baseline_write_rejects_destination_symlinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, victim_location: str
) -> None:
    """A requested output link is rejected without touching either victim."""
    runner = _load_phase16_runner()
    source_root = tmp_path / "repo"
    evidence_dir = source_root / "evidence"
    evidence_dir.mkdir(parents=True)
    destination = evidence_dir / "release-baseline.json"
    victim = (
        source_root / "victim.json"
        if victim_location == "inside"
        else tmp_path / "outside-victim.json"
    )
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(generated, 96.16, 94.50)
    victim.write_bytes(b"do not overwrite")
    destination.symlink_to(victim)
    monkeypatch.setattr(runner, "ROOT", source_root)

    with pytest.raises(runner.VerificationError, match="must not be a symlink"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert destination.is_symlink()
    assert victim.read_bytes() == b"do not overwrite"


def test_phase16_baseline_write_replaces_a_raced_destination_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A link swapped in after lstat is replaced, never followed to its victim."""
    runner = _load_phase16_runner()
    source_root = tmp_path / "repo"
    evidence_dir = source_root / "evidence"
    evidence_dir.mkdir(parents=True)
    destination = evidence_dir / "release-baseline.json"
    victim = source_root / "victim.json"
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.16, 94.50)
    victim.write_bytes(b"do not overwrite")
    monkeypatch.setattr(runner, "ROOT", source_root)
    original_rename = runner.os.rename

    def rename_after_leaf_swap(source, target, **kwargs) -> None:
        destination.unlink()
        destination.symlink_to(victim)
        original_rename(source, target, **kwargs)

    monkeypatch.setattr(runner.os, "rename", rename_after_leaf_swap)

    runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert not destination.is_symlink()
    assert destination.read_bytes() == generated.read_bytes()
    assert victim.read_bytes() == b"do not overwrite"


def test_phase16_baseline_write_anchors_parent_after_lexical_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A renamed parent cannot redirect descriptor-relative publication outside ROOT."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    source_root = runner.ROOT
    generated = tmp_path / "generated.json"
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_destination = outside_dir / "release-baseline.json"
    anchored_parent = source_root / "anchored-evidence"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.17, 94.51)
    destination.chmod(0o640)
    outside_destination.write_bytes(b"outside directory must not change")
    outside_before = {path.name: path.read_bytes() for path in outside_dir.iterdir()}
    original_open = runner.os.open
    swapped = False

    def open_then_swap(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        opened = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == "evidence" and dir_fd is not None and not swapped:
            swapped = True
            destination.parent.rename(anchored_parent)
            destination.parent.symlink_to(outside_dir, target_is_directory=True)
        return opened

    monkeypatch.setattr(runner.os, "open", open_then_swap)

    runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    anchored_destination = anchored_parent / destination.name
    assert swapped
    assert anchored_destination.read_bytes() == generated.read_bytes()
    assert stat.S_IMODE(anchored_destination.stat().st_mode) == 0o640
    assert {
        path.name: path.read_bytes() for path in outside_dir.iterdir()
    } == outside_before
    assert not any(
        path.name.startswith(".release-baseline.json.")
        for path in anchored_parent.iterdir()
    )

    # Cleanup restores the lexical repository layout without touching outside.
    destination.parent.unlink()
    anchored_parent.rename(destination.parent)
    assert destination.read_bytes() == generated.read_bytes()
    assert {
        path.name: path.read_bytes() for path in outside_dir.iterdir()
    } == outside_before


def test_phase16_baseline_write_fails_closed_without_descriptor_support(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Publication refuses a platform that cannot anchor its target directory."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(generated, 96.16, 94.50)
    monkeypatch.setattr(runner, "MANIFEST_DESCRIPTOR_SUPPORT", False)

    with pytest.raises(runner.VerificationError, match="directory-descriptor"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert not destination.exists()


def test_phase16_baseline_write_preserves_existing_regular_file_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Atomic publication retains the repository mode of an existing manifest."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.17, 94.51)
    destination.chmod(0o640)

    runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert stat.S_IMODE(destination.stat().st_mode) == 0o640
    assert destination.read_bytes() == generated.read_bytes()


def test_phase16_first_baseline_write_uses_default_mode_without_mutating_umask(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """New manifests use the ambient mode without changing process umask."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(generated, 96.16, 94.50)
    mode_probe = destination.parent / "default-mode-probe"
    mode_probe_fd = os.open(mode_probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    os.close(mode_probe_fd)
    expected_mode = stat.S_IMODE(mode_probe.stat().st_mode)
    mode_probe.unlink()

    def forbid_umask(*_args: object, **_kwargs: object) -> None:
        pytest.fail("manifest publication must not mutate process umask")

    monkeypatch.setattr(runner.os, "umask", forbid_umask)

    runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert stat.S_IMODE(destination.stat().st_mode) == expected_mode
    assert destination.read_bytes() == generated.read_bytes()


def test_phase16_baseline_write_does_not_weaken_concurrent_file_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Concurrent file creation keeps the ambient mode while a manifest publishes."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(generated, 96.16, 94.50)

    mode_probe = destination.parent / "default-mode-probe"
    mode_probe_fd = os.open(mode_probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    os.close(mode_probe_fd)
    expected_mode = stat.S_IMODE(mode_probe.stat().st_mode)
    mode_probe.unlink()

    concurrent_file = destination.parent / "concurrent-file"
    start_concurrent_creation = threading.Event()

    def create_concurrent_file() -> None:
        assert start_concurrent_creation.wait(timeout=5)
        concurrent_fd = os.open(
            concurrent_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666
        )
        os.close(concurrent_fd)

    worker = threading.Thread(target=create_concurrent_file)
    worker.start()
    original_new_manifest_temporary = runner._new_manifest_temporary

    def create_then_reserve(parent_fd: int, destination_name: str) -> tuple[str, int]:
        start_concurrent_creation.set()
        worker.join(timeout=5)
        assert not worker.is_alive()
        return original_new_manifest_temporary(parent_fd, destination_name)

    def forbid_umask(*_args: object, **_kwargs: object) -> None:
        pytest.fail("manifest publication must not mutate process umask")

    monkeypatch.setattr(runner, "_new_manifest_temporary", create_then_reserve)
    monkeypatch.setattr(runner.os, "umask", forbid_umask)

    runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert stat.S_IMODE(destination.stat().st_mode) == expected_mode
    assert stat.S_IMODE(concurrent_file.stat().st_mode) == expected_mode


def test_phase16_baseline_write_cleans_fresh_temp_after_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed replace leaves neither a partial destination nor a temp file."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.16, 94.50)
    original = destination.read_bytes()
    before = {path.name for path in destination.parent.iterdir()}

    def fail_rename(source, target, **kwargs) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(runner.os, "rename", fail_rename)

    with pytest.raises(OSError, match="simulated rename failure"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert destination.read_bytes() == original
    assert {path.name for path in destination.parent.iterdir()} == before


@pytest.mark.parametrize(
    "invalid",
    (
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
        "96.16",
        None,
        -0.01,
        100.01,
    ),
)
@pytest.mark.parametrize("invalid_role", ("existing", "generated"))
def test_phase16_baseline_write_rejects_invalid_coverage_without_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: object, invalid_role: str
) -> None:
    """Invalid existing or generated percentages never replace destination bytes."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    if invalid_role == "existing":
        _write_coverage_manifest(destination, invalid, 94.50)
        _write_coverage_manifest(generated, 96.16, 94.50)
    else:
        _write_coverage_manifest(destination, 96.16, 94.50)
        _write_coverage_manifest(generated, invalid, 94.50)
    original = destination.read_bytes()

    with pytest.raises(runner.VerificationError, match="invalid coverage baseline"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert destination.read_bytes() == original


@pytest.mark.parametrize(
    "generated_contents",
    (
        "{}",
        '{"quality_baseline": {"coverage": {"total_percent": 96.16}}}',
        '{"quality_baseline": {"coverage": {"total_percent": NaN, "core_percent": 94.50}}}',
        '{"quality_baseline": {"coverage": {"total_percent": Infinity, "core_percent": 94.50}}}',
        '{"quality_baseline": {"coverage": {"total_percent": -Infinity, "core_percent": 94.50}}}',
        '{"quality_baseline": {"coverage": {"total_percent": true, "core_percent": 94.50}}}',
        '{"quality_baseline": {"coverage": {"total_percent": "96.16", "core_percent": 94.50}}}',
        '{"quality_baseline": {"coverage": {"total_percent": -0.01, "core_percent": 94.50}}}',
        '{"quality_baseline": {"coverage": {"total_percent": 100.01, "core_percent": 94.50}}}',
    ),
)
def test_phase16_first_baseline_write_rejects_invalid_generated_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, generated_contents: str
) -> None:
    """A first write validates generated evidence and leaves no destination."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    generated.write_text(generated_contents, encoding="utf-8")

    with pytest.raises(runner.VerificationError, match="invalid coverage baseline"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert not destination.exists()


def test_phase16_first_baseline_write_catches_json_overflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An oversized JSON number cannot establish a first durable baseline."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(generated, 96.16, 94.50)

    def raise_overflow(*args, **kwargs):
        raise OverflowError("integer string conversion limit exceeded")

    monkeypatch.setattr(runner.json, "loads", raise_overflow)

    with pytest.raises(runner.VerificationError, match="invalid coverage baseline"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert not destination.exists()


@pytest.mark.parametrize(
    "invalid",
    (
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
        "96.16",
        None,
        -0.01,
        100.01,
    ),
)
@pytest.mark.parametrize("section", ("previous", "replacement"))
@pytest.mark.parametrize("field", ("total_percent", "core_percent"))
def test_phase16_baseline_write_rejects_invalid_migration_coverage_without_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid: object,
    section: str,
    field: str,
) -> None:
    """Migration coverage uses the same strict validation before replacement."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    migration = tmp_path / "coverage-floor-migration.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.15, 94.49)
    record = {
        "schema_version": 2,
        "quality_floor_migration": {
            "previous": {
                "coverage": {"total_percent": 96.16, "core_percent": 94.50},
                "tests": {"collected": 1129, "passed": 1129, "failed": 0, "errors": 0},
            },
            "replacement": {
                "coverage": {"total_percent": 96.15, "core_percent": 94.49},
                "tests": {"collected": 1129, "passed": 1129, "failed": 0, "errors": 0},
            },
            "reason": "intentional future coverage migration",
            "reviewed_by": "maintainer",
            "reviewed_at": "2026-08-30T00:00:00Z",
        },
    }
    record["quality_floor_migration"][section]["coverage"][field] = invalid
    migration.write_text(json.dumps(record), encoding="utf-8")
    original = destination.read_bytes()

    with pytest.raises(
        runner.VerificationError, match="invalid quality-floor migration"
    ):
        runner._export_manifest_atomically(
            generated, "evidence/release-baseline.json", migration
        )

    assert destination.read_bytes() == original


def test_phase16_coverage_floor_migration_requires_explicit_review_data(
    tmp_path: Path,
) -> None:
    """A future deliberate lower floor needs a separately reviewed record."""
    runner = _load_phase16_runner()
    baseline = tmp_path / "baseline.json"
    generated = tmp_path / "generated.json"
    migration = tmp_path / "coverage-floor-migration.json"
    _write_coverage_manifest(baseline, 96.08, 94.27)
    _write_coverage_manifest(generated, 96.07, 94.26)

    with pytest.raises(runner.VerificationError, match="coverage floor regression"):
        runner._validate_coverage_floor(baseline, generated)

    migration.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "quality_floor_migration": {
                    "previous": {
                        "coverage": {"total_percent": 96.08, "core_percent": 94.27},
                        "tests": {
                            "collected": 1129,
                            "passed": 1129,
                            "failed": 0,
                            "errors": 0,
                        },
                    },
                    "replacement": {
                        "coverage": {"total_percent": 96.07, "core_percent": 94.26},
                        "tests": {
                            "collected": 1129,
                            "passed": 1129,
                            "failed": 0,
                            "errors": 0,
                        },
                    },
                    "reason": "intentional future coverage migration",
                    "reviewed_by": "maintainer",
                    "reviewed_at": "2026-08-30T00:00:00Z",
                },
            }
        ),
        encoding="utf-8",
    )

    runner._validate_coverage_floor(baseline, generated, migration)


@pytest.mark.parametrize(
    "generated_counts",
    (
        {"collected": 1128, "passed": 1128},
        {"collected": -1, "passed": -1},
        {"collected": True, "passed": True},
        {"collected": 1129, "passed": 1128},
        {"failed": 1},
        {"errors": 1},
    ),
)
def test_phase16_baseline_write_rejects_invalid_or_lower_test_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, generated_counts: dict[str, object]
) -> None:
    """A malformed or reduced test inventory never replaces durable bytes."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.16, 94.50, **generated_counts)
    original = destination.read_bytes()

    with pytest.raises(runner.VerificationError):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert destination.read_bytes() == original


def test_phase16_first_baseline_write_rejects_invalid_test_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A first write cannot establish a malformed zero-test baseline."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(generated, 96.16, 94.50, collected=0, passed=0)

    with pytest.raises(runner.VerificationError, match="invalid test baseline"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

    assert not destination.exists()


def test_phase16_quality_floor_migration_allows_reviewed_test_reduction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An intentional lower test floor requires an exact reviewed migration."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    migration = tmp_path / "quality-floor-migration.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.16, 94.50, collected=1128, passed=1128)
    migration.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "quality_floor_migration": {
                    "previous": {
                        "coverage": {"total_percent": 96.16, "core_percent": 94.50},
                        "tests": {
                            "collected": 1129,
                            "passed": 1129,
                            "failed": 0,
                            "errors": 0,
                        },
                    },
                    "replacement": {
                        "coverage": {"total_percent": 96.16, "core_percent": 94.50},
                        "tests": {
                            "collected": 1128,
                            "passed": 1128,
                            "failed": 0,
                            "errors": 0,
                        },
                    },
                    "reason": "intentional reviewed test-suite migration",
                    "reviewed_by": "maintainer",
                    "reviewed_at": "2026-08-30T00:00:00Z",
                },
            }
        ),
        encoding="utf-8",
    )
    runner._export_manifest_atomically(
        generated, "evidence/release-baseline.json", migration
    )

    assert destination.read_bytes() == generated.read_bytes()
