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
from pathlib import Path

CORE_PY = Path(__file__).parent.parent / "src" / "fast_fsm" / "core.py"

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
