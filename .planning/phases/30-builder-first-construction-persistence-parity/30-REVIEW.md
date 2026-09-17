---
phase: 30-builder-first-construction-persistence-parity
reviewed: 2026-09-17T21:41:01Z
depth: deep
files_reviewed: 21
files_reviewed_list:
  - .specify/memory/spr-core-api.md
  - README.md
  - docs/QUICK_START.md
  - docs/TUTORIAL.md
  - docs/api/core.md
  - docs/api/validation.md
  - docs/api/visualization.md
  - docs/dev/architecture.md
  - examples/cross_fsm_demo.py
  - src/fast_fsm/_construction_compat.py
  - src/fast_fsm/core.py
  - src/fast_fsm/core.pyi
  - tests/test_advanced_functionality.py
  - tests/test_builder.py
  - tests/test_construction_parity.py
  - tests/test_final_states.py
  - tests/test_graph_invariants.py
  - tests/test_installed_artifacts.py
  - tests/test_mypyc_guard.py
  - tests/test_readme_examples.py
  - tests/test_transition_modes.py
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 30: Code Review Report

**Reviewed:** 2026-09-17T21:41:01Z
**Depth:** deep
**Files Reviewed:** 21
**Status:** issues_found

## Summary

The Phase 30 implementation needs fixes before it ships. The canonical
construction and persistence paths pass the committed focused suite, but an
uncovered legacy builder shape now creates an additional declarative candidate
and silently changes priority/mode selection. The interpreted compatibility
wrappers also no longer behave like top-level public functions for runtime
introspection and pickling.

Verification performed:

- The 193-test focused Phase 30 selection passed.
- A direct regression probe produced two candidates, `(priority=0,
  internal=False)` and `(priority=5, internal=True)`, from one legacy decorated
  handler plus one explicit builder row; a stateful guard ran twice and the
  selected transition changed.
- Pure and already-built native probes both showed unresolved runtime type
  hints for the installed wrappers. `simple_fsm` and `quick_fsm` also failed
  `pickle.dumps()` because their qualified names identify local functions.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Declarative auto-import duplicates legacy explicit builder topology

**Classification:** BLOCKER

**File:** `src/fast_fsm/core.py:6780-6801`

**Issue:** `FSMBuilder.build()` unconditionally derives every applicable,
topology-complete handler after it has already bound all explicitly staged
requests. Existing code previously had to pair a decorated handler with
`builder.add_transition(...)`. When that explicit row intentionally carries a
non-default priority, timing window, or internal mode, Phase 30 now publishes
both rows instead of preserving the explicit topology. This is not a harmless
duplicate: the derived default candidate can win first, change an internal
transition into an external one, and cause the same state-owned guard to run
again during fallthrough.

The focused probe used an external-default declaration plus an explicit
`priority=5, internal=True` row. The built slot contained priorities `0` and
`5`; the first probe selected the new external priority-0 candidate. With a
stateful false-then-true guard, one trigger evaluated the same declaration
twice before committing the priority-5 internal row. That contradicts the
project's retained constructor behavior and exactly-once guard objective.

**Fix:** Define and implement a compatibility rule before appending derived
requests. When an explicit staged request already owns the same canonical
source/trigger/target declaration, do not silently derive an additional
candidate. Preserve the explicit row as the topology authority (with the
state-owned declaration still supplying its guard/handler), or fail with an
actionable migration error if a genuinely ambiguous combination cannot be
preserved. Add pure/native tests for legacy explicit rows whose priority,
timing, and internal mode differ from decorator defaults, including a stateful
guard assertion proving one evaluation per trigger attempt.

## Warnings

### WR-01: Interpreted warning wrappers lose public-function provenance

**Classification:** WARNING

**File:** `src/fast_fsm/_construction_compat.py:47-107`

**Issue:** The four installed warning boundaries are nested local functions.
Only the classmethod wrappers conditionally copy metadata, and that condition
does not fire for the compiled methods. The module-level wrappers never copy
metadata at all. Consequently, `simple_fsm` and `quick_fsm` report
`fast_fsm._construction_compat.install_construction_compat.<locals>...` rather
than their public `fast_fsm.core` identity and cannot be pickled. In both pure
and native modes, `typing.get_type_hints()` raises `NameError` because runtime
annotations refer to `StateMachine`, `State`, and `_TransitionRow`, which exist
only under `TYPE_CHECKING` in the wrapper module. The native classmethod
wrappers have the same type-hint/provenance failure. This breaks runtime typing
tools, API discovery, multiprocessing/serialization use of the top-level
functions, and the claimed pure/native compatibility surface.

**Fix:** Capture all four original public callables before replacement and
apply `functools.wraps`/`update_wrapper` consistently in pure and compiled
modes, or explicitly assign public `__module__`, `__name__`, `__qualname__`,
`__doc__`, `__annotations__`, and `__wrapped__` metadata whose referenced names
resolve at runtime. Add pure/native assertions for `typing.get_type_hints()`,
public module/qualified names, docstrings/signatures, and pickle round trips of
`simple_fsm` and `quick_fsm`.

---

_Reviewed: 2026-09-17T21:41:01Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
