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
from pathlib import Path

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
        "baseline-write",
        "manifest-output",
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


def _write_coverage_manifest(path: Path, total: float, core: float) -> None:
    path.write_text(
        json.dumps(
            {
                "quality_baseline": {
                    "coverage": {
                        "total_percent": total,
                        "core_percent": core,
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_phase16_baseline_write_refuses_lower_coverage_before_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An isolated write cannot redefine an existing coverage floor downward."""
    runner = _load_phase16_runner()
    destination = tmp_path / "release-baseline.json"
    generated = tmp_path / "generated.json"
    _write_coverage_manifest(destination, 96.08, 94.27)
    _write_coverage_manifest(generated, 96.07, 94.26)
    original = destination.read_bytes()
    monkeypatch.setattr(runner, "_manifest_output", lambda _output: destination)

    with pytest.raises(runner.VerificationError, match="coverage floor regression"):
        runner._export_manifest_atomically(generated, "evidence/release-baseline.json")

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
                "schema_version": 1,
                "coverage_floor_migration": {
                    "previous": {"total_percent": 96.08, "core_percent": 94.27},
                    "replacement": {"total_percent": 96.07, "core_percent": 94.26},
                    "reason": "intentional future coverage migration",
                    "reviewed_by": "maintainer",
                    "reviewed_at": "2026-08-30T00:00:00Z",
                },
            }
        ),
        encoding="utf-8",
    )

    runner._validate_coverage_floor(baseline, generated, migration)
