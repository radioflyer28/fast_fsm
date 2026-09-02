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
import subprocess
import sys
import threading
from types import ModuleType

import pytest

CORE_PY = Path(__file__).parent.parent / "src" / "fast_fsm" / "core.py"
CONDITIONS_PY = Path(__file__).parent.parent / "src" / "fast_fsm" / "conditions.py"
PACKAGE_INIT = Path(__file__).parent.parent / "src" / "fast_fsm" / "__init__.py"
SETUP_PY = Path(__file__).parent.parent / "setup.py"
PHASE16_RUNNER = Path(__file__).parent.parent / "tools" / "phase16_isolated_verify.py"
PHASE18_NATIVE_PROBE = (
    Path(__file__).parent.parent / "tools" / "phase18_native_probe.py"
)
CI_WORKFLOW = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"


def _load_phase18_native_probe() -> ModuleType:
    """Import the standalone native probe without invoking its CLI."""
    specification = importlib.util.spec_from_file_location(
        "phase18_native_probe_for_tests", PHASE18_NATIVE_PROBE
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


PHASE18_WRITER_OWNER_PLANS = {
    "trigger": "18-01",
    "force_state": "18-02",
    "reset": "18-02",
    "restore": "18-02",
    "trigger_async": "18-03",
    "add_state": "18-04",
    "add_transition": "18-04",
    "add_transitions": "18-04",
    "add_bidirectional_transition": "18-04",
    "add_emergency_transition": "18-04",
    "enable_history": "18-04",
    "disable_history": "18-04",
    "add_listener": "18-04",
    "on_enter": "18-04",
    "on_exit": "18-04",
    "after_transition": "18-04",
    "on_failed": "18-04",
    "on_trigger": "18-04",
    "on_enter_async": "18-04",
    "on_exit_async": "18-04",
    "safe_trigger": "18-05",
}

D14_WRITER_ENTRY_POINTS = {
    "StateMachine": {
        "trigger": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "safe_trigger": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "force_state": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "reset": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "restore": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "add_state": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "add_transition": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "add_transitions": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "add_bidirectional_transition": (
            "_acquire_sync_ownership",
            "_release_sync_ownership",
        ),
        "add_emergency_transition": (
            "_acquire_sync_ownership",
            "_release_sync_ownership",
        ),
        "enable_history": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "disable_history": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "add_listener": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "on_enter": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "on_exit": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "after_transition": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "on_failed": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "on_trigger": ("_acquire_sync_ownership", "_release_sync_ownership"),
    },
    "AsyncStateMachine": {
        "trigger_async": ("_acquire_async_ownership", "_release_async_ownership"),
        "on_enter_async": ("_acquire_sync_ownership", "_release_sync_ownership"),
        "on_exit_async": ("_acquire_sync_ownership", "_release_sync_ownership"),
    },
}

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


def test_compiled_func_condition_keeps_its_interpreted_subclass_boundary() -> None:
    """The public wrapper stays interpreted while its evaluator stays in core."""
    tree = ast.parse(
        CONDITIONS_PY.read_text(encoding="utf-8"), filename=str(CONDITIONS_PY)
    )
    compiled_condition = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "CompiledFuncCondition"
    )
    slots = next(
        node.value
        for node in compiled_condition.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__slots__"
            for target in node.targets
        )
    )
    assert isinstance(slots, ast.Tuple)
    assert {item.value for item in slots.elts if isinstance(item, ast.Constant)} == {
        "func",
        "__dict__",
    }
    check = next(
        node
        for node in compiled_condition.body
        if isinstance(node, ast.FunctionDef) and node.name == "check"
    )
    assert any(
        isinstance(node, ast.Name) and node.id == "_compiled_func_condition_check"
        for node in ast.walk(check)
    )
    core_source = CORE_PY.read_text(encoding="utf-8")
    assert "def _compiled_func_condition_check" in core_source
    assert (
        "_bind_compiled_func_condition_check(_compiled_func_condition_check)"
        in core_source
    )


def test_compiled_func_condition_remains_usable_before_core_binds_helper() -> None:
    """The interpreted wrapper has a safe direct-module fallback at import time."""
    spec = importlib.util.spec_from_file_location(
        "fast_fsm_unbound_conditions", CONDITIONS_PY
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    condition = module.CompiledFuncCondition(lambda: True)

    assert condition.check() is True


def test_typed_downstream_async_callable_wrappers_accept_exact_and_inherited_shapes(
    tmp_path: Path,
) -> None:
    """The PEP 561 client contract matches runtime async wrapper support."""
    assert (CONDITIONS_PY.parent / "py.typed").is_file()
    client = tmp_path / "client.py"
    client.write_text(
        "from fast_fsm import (\n"
        "    CompiledFuncCondition,\n"
        "    FuncCondition,\n"
        "    GuardCallable,\n"
        "    GuardResult,\n"
        "    NegatedCondition,\n"
        ")\n"
        "from fast_fsm.condition_templates import AndCondition, NotCondition, OrCondition\n"
        "from fast_fsm.core import (\n"
        "    CompiledFuncCondition as CoreCompiledFuncCondition,\n"
        "    FuncCondition as CoreFuncCondition,\n"
        "    GuardCallable as CoreGuardCallable,\n"
        "    GuardResult as CoreGuardResult,\n"
        ")\n\n"
        "class AsyncCallable:\n"
        "    async def __call__(self, *args: object, **kwargs: object) -> bool:\n"
        "        return True\n\n"
        "class InheritedPackageFunc(FuncCondition):\n"
        "    pass\n\n"
        "class InheritedPackageCompiled(CompiledFuncCondition):\n"
        "    pass\n\n"
        "class InheritedCoreFunc(CoreFuncCondition):\n"
        "    pass\n\n"
        "class InheritedCoreCompiled(CoreCompiledFuncCondition):\n"
        "    pass\n\n"
        "guard = AsyncCallable()\n"
        "package_guard: GuardCallable = guard\n"
        "core_guard: CoreGuardCallable = guard\n"
        "package_exact_func = FuncCondition(package_guard)\n"
        "package_exact_compiled = CompiledFuncCondition(package_guard)\n"
        "package_inherited_func = InheritedPackageFunc(package_guard)\n"
        "package_inherited_compiled = InheritedPackageCompiled(package_guard)\n"
        "core_exact_func = CoreFuncCondition(core_guard)\n"
        "core_exact_compiled = CoreCompiledFuncCondition(core_guard)\n"
        "core_inherited_func = InheritedCoreFunc(core_guard)\n"
        "core_inherited_compiled = InheritedCoreCompiled(core_guard)\n"
        "package_result: GuardResult = package_exact_func.check()\n"
        "package_negated_result: GuardResult = NegatedCondition(package_exact_func).check()\n"
        "package_and_result: GuardResult = AndCondition(package_exact_func).check()\n"
        "package_or_result: GuardResult = OrCondition(package_exact_func).check()\n"
        "package_not_result: GuardResult = NotCondition(package_exact_func).check()\n"
        "core_result: CoreGuardResult = core_exact_compiled.check()\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["FAST_FSM_BUILD_MODE"] = "pure"
    environment.pop("MYPYPATH", None)
    completed = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", str(client)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr


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


def test_staged_writer_inventory_names_every_phase18_public_write() -> None:
    """Wave 0 records the exact writer owner before full entry checks land."""
    tree = ast.parse(CORE_PY.read_text(encoding="utf-8"), filename=str(CORE_PY))
    classes = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    state_machine = classes["StateMachine"]
    async_machine = classes["AsyncStateMachine"]
    state_machine_methods = {
        node.name
        for node in state_machine.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    async_machine_methods = {
        node.name
        for node in async_machine.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected_state_machine = set(PHASE18_WRITER_OWNER_PLANS) - {
        "trigger_async",
        "on_enter_async",
        "on_exit_async",
    }
    assert expected_state_machine <= state_machine_methods
    assert {"trigger_async", "on_enter_async", "on_exit_async"} <= async_machine_methods
    assert set(PHASE18_WRITER_OWNER_PLANS.values()) == {
        "18-01",
        "18-02",
        "18-03",
        "18-04",
        "18-05",
    }


def test_phase18_sync_tracer_keeps_private_per_machine_locks() -> None:
    """Ownership locks are slotted instance fields, never module-global state."""
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))
    state_machine = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "StateMachine"
    )
    async_machine = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "AsyncStateMachine"
    )

    def slot_names(class_node: ast.ClassDef) -> set[str]:
        slots = next(
            node.value
            for node in class_node.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__slots__"
                for target in node.targets
            )
        )
        assert isinstance(slots, ast.Tuple)
        return {item.value for item in slots.elts if isinstance(item, ast.Constant)}

    def self_lock_assignments(class_node: ast.ClassDef, attribute: str) -> int:
        initializer = next(
            node
            for node in class_node.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        )
        return sum(
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr == attribute
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "threading"
            and node.value.func.attr == "Lock"
            for node in ast.walk(initializer)
        )

    module_lock_assignments = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "threading"
        and node.value.func.attr == "Lock"
    ]
    assert module_lock_assignments == []

    assert {"_sync_ownership_lock", "_sync_owner_thread_id"} <= slot_names(
        state_machine
    )
    assert "_async_admission_lock" in slot_names(async_machine)
    assert self_lock_assignments(state_machine, "_sync_ownership_lock") == 1
    assert self_lock_assignments(async_machine, "_async_admission_lock") == 1
    methods = {
        node.name
        for node in state_machine.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert {
        "_acquire_sync_ownership",
        "_release_sync_ownership",
        "_trigger_owned",
        "trigger",
    } <= methods
    assert "_sync_ownership_locks" not in source


def test_d14_writers_enter_and_release_once_without_public_delegation() -> None:
    """Every D-14 write has one auditable entry and private owned body."""
    tree = ast.parse(CORE_PY.read_text(encoding="utf-8"), filename=str(CORE_PY))
    classes = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name in D14_WRITER_ENTRY_POINTS
    }
    public_writers = {
        writer
        for entry_points in D14_WRITER_ENTRY_POINTS.values()
        for writer in entry_points
    }

    for class_name, entry_points in D14_WRITER_ENTRY_POINTS.items():
        methods = {
            node.name: node
            for node in classes[class_name].body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for writer, (acquire, release) in entry_points.items():
            method = methods[writer]
            self_calls = [
                node.func.attr
                for node in ast.walk(method)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
            ]
            assert self_calls.count(acquire) == 1
            assert self_calls.count(release) == 1
            assert not (set(self_calls) & (public_writers - {writer}))


def test_prepared_declarative_marker_is_one_contextvar_with_machine_identity() -> None:
    """Guard preparation must never regress to a mutable shared scope registry."""
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))
    names = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    }
    functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert "_prepared_declarative_guards" not in names
    assert "_prepared_guard_scope_key" not in functions
    assert "_prepared_declarative_guard" in names
    assert "contextvars.ContextVar" in source
    assert "id(machine)" in source

    for name in (
        "_set_prepared_declarative_guard",
        "_reset_prepared_declarative_guard",
        "_has_prepared_declarative_guard",
    ):
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )
        calls = [
            node.func.attr
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "_prepared_declarative_guard"
        ]
        expected_call = (
            "get"
            if name == "_has_prepared_declarative_guard"
            else ("reset" if name == "_reset_prepared_declarative_guard" else "set")
        )
        assert expected_call in calls


def test_prepared_declarative_marker_compares_independent_consumer_identity() -> None:
    """Preparation provenance and active dispatch stay at distinct seams."""
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))
    module_names = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    }
    assert "_declarative_consumer_machine_id" in module_names

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    setter_source = ast.unparse(functions["_set_prepared_declarative_guard"])
    assert "_prepared_declarative_guard.set" in setter_source
    assert "_declarative_consumer_machine_id" not in setter_source

    consumer_source = ast.unparse(functions["_has_prepared_declarative_guard"])
    assert "marker[0]" in consumer_source
    assert "_declarative_consumer_machine_id.get()" in consumer_source

    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    public_dispatch = (
        ("StateMachine", "can_trigger", False),
        ("StateMachine", "trigger", False),
        ("StateMachine", "safe_trigger", False),
        ("AsyncStateMachine", "can_trigger_async", True),
        ("AsyncStateMachine", "trigger_async", True),
    )
    for class_name, method_name, is_async in public_dispatch:
        method = next(
            node
            for node in classes[class_name].body
            if node.name == method_name
            and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        assert isinstance(method, ast.AsyncFunctionDef) is is_async
        calls = [
            node.func.attr
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "_declarative_consumer_machine_id"
        ]
        assert "set" in calls
        assert "reset" in calls
        assert any(isinstance(node, ast.Try) for node in ast.walk(method))

    for class_name in ("State", "DeclarativeState", "AsyncDeclarativeState"):
        method_name = (
            "can_transition_async"
            if class_name == "AsyncDeclarativeState"
            else "can_transition"
        )
        method = next(
            node
            for node in classes[class_name].body
            if node.name == method_name
            and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        assert [argument.arg for argument in method.args.args] == [
            "self",
            "trigger",
            "to_state",
        ]
        assert method.args.vararg is not None
        assert method.args.kwarg is not None
        assert not method.args.kwonlyargs

    mutable_registries = [
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and isinstance(node.value, (ast.Dict, ast.List, ast.Set))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
        and "declarative" in target.id
        and "registry" in target.id
    ]
    assert not mutable_registries


def test_phase18_native_probe_and_supported_matrix_are_present() -> None:
    """The final CI matrix compiles and exercises the actual ownership core."""
    probe_source = PHASE18_NATIVE_PROBE.read_text(encoding="utf-8")
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    for required in (
        "threading.Lock",
        "asyncio.Lock",
        "ContextVar",
        "OwnershipRepresentation",
        "--assert-native",
        "--assert-core-native",
        "--assert-hosted-ci-sha",
        "gh",
        "headSha",
    ):
        assert required in probe_source
    assert "ownership_native_probe:" in workflow
    assert (
        "tools/phase18_native_probe.py --check-ci .github/workflows/ci.yml" in workflow
    )
    assert "tests/test_ownership_concurrency.py" in workflow
    assert (
        "tools/phase18_native_probe.py --build-mode compiled --assert-native"
        in workflow
    )
    assert "tools/phase18_native_probe.py --assert-core-native" in workflow
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert f'"{version}"' in workflow


def test_phase18_native_probe_requires_executable_workflow_commands(
    tmp_path: Path,
) -> None:
    """A command mentioned only in a YAML comment cannot satisfy the contract."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    required_command = (
        "run: uv run python tools/phase18_native_probe.py --check-ci "
        ".github/workflows/ci.yml"
    )
    commented_command = (
        "run: |\n"
        "          # uv run python tools/phase18_native_probe.py --check-ci "
        ".github/workflows/ci.yml"
    )
    assert required_command in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(required_command, commented_command), encoding="utf-8"
    )

    with pytest.raises(SystemExit, match="missing executable command"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_requires_commands_in_their_named_steps(
    tmp_path: Path,
) -> None:
    """Executable commands in an unrelated step cannot satisfy the contract."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_step = "Run native ownership and lifecycle semantics"
    assert f"name: {expected_step}" in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            f"name: {expected_step}",
            "name: Unrelated native ownership command",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="must exactly match the required named step"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_rejects_inert_or_split_pytest_commands(
    tmp_path: Path,
) -> None:
    """The native test step must execute one pytest command with real test args."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_run = """run: >-
          uv run pytest
          tests/test_ownership_concurrency.py
          tests/test_transition_lifecycle.py
          tests/test_async.py
          tests/test_mypyc_guard.py
          -x -q"""
    inert_run = """run: |
          uv run pytest --collect-only -q
          echo tests/test_ownership_concurrency.py
          echo tests/test_transition_lifecycle.py
          echo tests/test_async.py
          echo tests/test_mypyc_guard.py"""
    assert expected_run in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(workflow.replace(expected_run, inert_run), encoding="utf-8")

    with pytest.raises(SystemExit, match="exactly one non-comment shell command"):
        _load_phase18_native_probe()._check_ci(candidate)


@pytest.mark.parametrize(
    "suffix",
    (
        "--collect-only",
        "--help",
        "--version",
        "-o addopts=--collect-only",
        "|& true",
    ),
)
def test_phase18_native_probe_rejects_extra_pytest_options_and_shell_controls(
    tmp_path: Path,
    suffix: str,
) -> None:
    """The native test command accepts only its exact executing argv contract."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_run = """run: >-
          uv run pytest
          tests/test_ownership_concurrency.py
          tests/test_transition_lifecycle.py
          tests/test_async.py
          tests/test_mypyc_guard.py
          -x -q"""
    assert expected_run in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            expected_run, expected_run.replace("-x -q", f"-x -q {suffix}")
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="must exactly match the required pytest argv"):
        _load_phase18_native_probe()._check_ci(candidate)


@pytest.mark.parametrize(
    ("step_name", "command"),
    (
        (
            "Compile actual ownership core",
            "uv run python setup.py build_ext --inplace -q",
        ),
        (
            "Assert native ownership core origin",
            "uv run python tools/phase18_native_probe.py --assert-core-native",
        ),
    ),
)
def test_phase18_native_probe_rejects_shell_controls_in_core_evidence_steps(
    tmp_path: Path,
    step_name: str,
    command: str,
) -> None:
    """Core compilation and native-origin assertion cannot mask failures."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_run = f"name: {step_name}\n        run: {command}"
    assert expected_run in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(expected_run, f"{expected_run} || true"), encoding="utf-8"
    )

    with pytest.raises(SystemExit, match="must exactly match the required"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_rejects_conditional_required_steps(
    tmp_path: Path,
) -> None:
    """Required native evidence cannot be skipped through Actions metadata."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_step = (
        "name: Compile actual ownership core\n"
        "        run: uv run python setup.py build_ext --inplace -q"
    )
    assert expected_step in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            expected_step,
            "name: Compile actual ownership core\n"
            "        if: false\n"
            "        run: uv run python setup.py build_ext --inplace -q",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="must not define an if condition"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_rejects_failure_tolerant_required_steps(
    tmp_path: Path,
) -> None:
    """Required native evidence cannot ignore a compilation failure."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_step = (
        "name: Compile actual ownership core\n"
        "        run: uv run python setup.py build_ext --inplace -q"
    )
    assert expected_step in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            expected_step,
            "name: Compile actual ownership core\n"
            "        continue-on-error: true\n"
            "        run: uv run python setup.py build_ext --inplace -q",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="must not continue after an error"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_rejects_pytest_environment_override(
    tmp_path: Path,
) -> None:
    """The exact pytest argv cannot be changed through PYTEST_ADDOPTS."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    expected_environment = "    env:\n      FAST_FSM_BUILD_MODE: compiled\n    steps:"
    assert expected_environment in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            expected_environment,
            "    env:\n"
            "      FAST_FSM_BUILD_MODE: compiled\n"
            "      PYTEST_ADDOPTS: --collect-only\n"
            "    steps:",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="PYTEST_ADDOPTS"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_rejects_github_env_injection_step(
    tmp_path: Path,
) -> None:
    """No unrecognized step can persist a pytest override through GITHUB_ENV."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    pytest_step = "      - name: Run native ownership and lifecycle semantics"
    assert pytest_step in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            pytest_step,
            "      - name: Inject pytest collection-only override\n"
            "        run: echo PYTEST_ADDOPTS=--collect-only >> $GITHUB_ENV\n"
            + pytest_step,
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="exactly 8 ordered steps"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_rejects_mutated_dependency_install_step(
    tmp_path: Path,
) -> None:
    """The fixed setup command cannot be weakened through a changed argv."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    install_step = (
        "name: Install locked native probe dependencies\n"
        "        run: uv sync --locked --all-groups"
    )
    assert install_step in workflow
    candidate = tmp_path / "ci.yml"
    candidate.write_text(
        workflow.replace(
            install_step,
            "name: Install locked native probe dependencies\n"
            "        run: uv sync --all-groups",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="required dependency install argv"):
        _load_phase18_native_probe()._check_ci(candidate)


def test_phase18_native_probe_accepts_the_real_workflow_contract() -> None:
    """The checked-in folded workflow scalar parses to the allowlisted argv."""
    _load_phase18_native_probe()._check_ci(CI_WORKFLOW)


def test_phase18_native_probe_accepts_one_complete_hosted_run_among_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A push-plus-PR history is valid when one exact-SHA matrix is complete."""
    probe = _load_phase18_native_probe()
    candidate = "a" * 40
    successful_jobs = [
        {
            "name": f"Ownership native probe · Python {version}",
            "conclusion": "success",
        }
        for version in probe._SUPPORTED_PYTHONS
    ]
    incomplete_jobs = successful_jobs[:-1]

    def fake_gh_json(arguments: list[str]) -> object:
        if arguments[:2] == ["run", "list"]:
            return [
                {
                    "databaseId": 10,
                    "headSha": candidate,
                    "workflowName": "CI",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "databaseId": 11,
                    "headSha": candidate,
                    "workflowName": "CI",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "databaseId": 12,
                    "headSha": candidate,
                    "workflowName": "CI",
                    "status": "in_progress",
                    "conclusion": None,
                },
            ]
        if arguments[:3] == ["run", "view", "10"]:
            return {
                "headSha": candidate,
                "status": "completed",
                "conclusion": "success",
                "jobs": incomplete_jobs,
            }
        if arguments[:3] == ["run", "view", "11"]:
            return {
                "headSha": candidate,
                "status": "completed",
                "conclusion": "success",
                "jobs": successful_jobs,
            }
        pytest.fail(f"unexpected GitHub CLI request: {arguments}")

    monkeypatch.setattr(probe, "_resolve_commit", lambda _ref: candidate)
    monkeypatch.setattr(probe, "_gh_json", fake_gh_json)

    probe._assert_hosted_ci_sha("HEAD")


def test_transition_result_keeps_its_additive_slots_and_chained_error_boundary() -> (
    None
):
    """The public result stays compact while its opt-in error keeps the cause."""
    tree = ast.parse(CORE_PY.read_text(encoding="utf-8"), filename=str(CORE_PY))
    classes = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    result = classes["TransitionResult"]
    error = classes["TransitionError"]

    result_decorator = next(
        item
        for item in result.decorator_list
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == "dataclass"
    )
    assert {
        keyword.arg: keyword.value.value
        for keyword in result_decorator.keywords
        if isinstance(keyword.value, ast.Constant)
    }.get("slots") is True
    fields = [
        node.target.id
        for node in result.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]
    assert fields[:5] == ["success", "from_state", "to_state", "trigger", "error"]
    assert fields[5:] == ["committed", "stage", "cause"]

    raise_if_failed = next(
        node
        for node in result.body
        if isinstance(node, ast.FunctionDef) and node.name == "raise_if_failed"
    )
    assert any(
        isinstance(node, ast.Raise)
        and isinstance(node.cause, ast.Attribute)
        and isinstance(node.cause.value, ast.Name)
        and node.cause.value.id == "self"
        and node.cause.attr == "cause"
        for node in ast.walk(raise_if_failed)
    )
    assert isinstance(error.bases[0], ast.Name) and error.bases[0].id == "RuntimeError"
    assert any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == "mypyc_attr"
        and any(
            keyword.arg == "native_class"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in item.keywords
        )
        for item in error.decorator_list
    )


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
        "MANIFEST_DESCRIPTOR_SUPPORT",
        "_open_manifest_parent",
        "O_NOFOLLOW",
        "src_dir_fd",
        "dst_dir_fd",
        "copyfileobj",
        "fsync",
        "os.rename",
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

    assert source.count('"tests/test_boundary_negative.py"') >= 2


def test_phase17_runner_has_explicit_lifecycle_overlay_and_suite() -> None:
    """Lifecycle evidence must not silently inherit checkout artifacts."""
    source = PHASE16_RUNNER.read_text(encoding="utf-8")

    for required in (
        "PHASE17_INVENTORY",
        '"tests/test_transition_lifecycle.py"',
        '".planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md"',
        'args.suite == "phase17"',
        "lifecycle_success",
    ):
        assert required in source


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


@pytest.fixture(autouse=True)
def _skip_descriptor_publication_tests_without_platform_support(
    request: pytest.FixtureRequest,
) -> None:
    """Keep POSIX descriptor-publication tests out of unsupported CI jobs."""
    name = request.node.name
    if name == "test_phase16_baseline_write_fails_closed_without_descriptor_support":
        return
    if not (
        name.startswith("test_phase16_")
        and (
            "baseline" in name
            or "coverage_floor_migration" in name
            or "quality_floor_migration" in name
        )
    ):
        return

    runner = _load_phase16_runner()
    if not runner.MANIFEST_DESCRIPTOR_SUPPORT:
        pytest.skip("secure descriptor publication is unavailable on this platform")


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
    migration = destination.parent / "coverage-floor-migration.json"
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
    secure_migration = runner._coverage_floor_migration(
        "evidence/coverage-floor-migration.json"
    )

    with pytest.raises(
        runner.VerificationError, match="invalid quality-floor migration"
    ):
        runner._export_manifest_atomically(
            generated, "evidence/release-baseline.json", secure_migration
        )

    assert destination.read_bytes() == original


def test_phase16_coverage_floor_migration_requires_explicit_review_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A future deliberate lower floor needs a separately reviewed record."""
    runner = _load_phase16_runner()
    baseline = tmp_path / "baseline.json"
    generated = tmp_path / "generated.json"
    source_root = tmp_path / "repo"
    source_root.mkdir()
    migration = source_root / "coverage-floor-migration.json"
    monkeypatch.setattr(runner, "ROOT", source_root)
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

    runner._validate_coverage_floor(
        baseline,
        generated,
        runner._coverage_floor_migration("coverage-floor-migration.json"),
    )


@pytest.mark.parametrize("link_position", ("leaf", "parent"))
def test_phase16_coverage_floor_migration_rejects_external_symlinks_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    link_position: str,
) -> None:
    """An external record cannot authorize a floor reduction through a symlink."""
    runner = _load_phase16_runner()
    destination = _manifest_destination(runner, monkeypatch, tmp_path)
    generated = tmp_path / "generated.json"
    outside = tmp_path / "outside"
    outside.mkdir()
    external_record = outside / "migration.json"
    _write_coverage_manifest(destination, 96.16, 94.50)
    _write_coverage_manifest(generated, 96.15, 94.49)
    external_record.write_text("external migration must not be read", encoding="utf-8")
    original = destination.read_bytes()

    if link_position == "leaf":
        (runner.ROOT / "migration.json").symlink_to(external_record)
        requested_migration = "migration.json"
    else:
        (runner.ROOT / "migrations").symlink_to(outside, target_is_directory=True)
        requested_migration = "migrations/migration.json"

    with pytest.raises(runner.VerificationError, match="must not.*symlink"):
        migration = runner._coverage_floor_migration(requested_migration)
        runner._export_manifest_atomically(
            generated, "evidence/release-baseline.json", migration
        )

    assert destination.read_bytes() == original
    assert (
        external_record.read_text(encoding="utf-8")
        == "external migration must not be read"
    )


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
    migration = destination.parent / "quality-floor-migration.json"
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
        generated,
        "evidence/release-baseline.json",
        runner._coverage_floor_migration("evidence/quality-floor-migration.json"),
    )

    assert destination.read_bytes() == generated.read_bytes()
