---
phase: 16-canonical-graph-dispatch-invariants
reviewed: 2026-08-30T19:10:01Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - .specify/memory/spr-core-api.md
  - docs/dev/architecture.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/condition_templates.py
  - src/fast_fsm/conditions.py
  - src/fast_fsm/core.py
  - tests/test_advanced_functionality.py
  - tests/test_async.py
  - tests/test_boundary_negative.py
  - tests/test_builder.py
  - tests/test_condition_templates.py
  - tests/test_graph_invariants.py
  - tests/test_mypyc_guard.py
  - tests/test_performance_benchmarks.py
  - tests/test_safety_kwargs.py
  - tools/phase16_isolated_verify.py
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-08-30T19:10:01Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

The four findings from the preceding review are fixed on their named paths.
The exact `CompiledFuncCondition`, inherited `FuncCondition`, and overridden
`check()` cases now select or reject the correct machine type; failed auto
builds publish neither their candidate nor its transient type; manifest
publication stays on a no-follow descriptor after parent/leaf swaps and fails
closed without the required platform primitives; and the new-file mode probe
does not mutate process-global `umask`. The focused 14-test asserted-pure
selection passed, and an independent asserted-pure baseline check reproduced
1,175/1,175 tests with 96.37% total coverage and 94.85% `core.py` coverage.
The component-level release evidence is internally consistent and does not
claim an unobserved monolithic-wrapper exit.

The review is not clean. The async classifier still misses inspectable async
callable objects, so both auto and explicit-sync builders choose invalid modes
in fresh pure and compiled reproductions. The review also reproduced a separate
pure/compiled contract split: `CompiledFuncCondition` is documented as an
interpreted-subclass surface, works that way in pure mode, but crashes at
construction under the compiled artifact.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Async callable objects still bypass builder mode classification

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:1735-1750,3175-3189,3403-3417`

**Issue:** The repaired classifier calls `asyncio.iscoroutinefunction()` on
the stored callable object itself. Python returns `False` for an instance whose
`__call__` method is declared with `async def`, even though invoking that object
returns a coroutine. This affects exact `FuncCondition(AsyncCallable())`, exact
`CompiledFuncCondition(AsyncCallable())`, and a callable object supplied
directly as a builder guard. In fresh asserted-pure and freshly compiled
reproductions, auto mode reported and built `StateMachine`; explicit-sync mode
also accepted the condition. Async runtime evaluation is already capable of
awaiting the resulting coroutine, so detection and execution disagree and
GRAF-05/D-11 remain unsatisfied for a documented “any callable” guard shape.

**Fix:** Centralize callable-hook classification and test both the callable and
its effective `__call__` method without executing user code, for example:

```python
def _is_async_callable(value: object) -> bool:
    return asyncio.iscoroutinefunction(value) or asyncio.iscoroutinefunction(
        getattr(value, "__call__", None)
    )
```

Use that helper for stored `.func` leaves and direct/declarative callable
guards in both incremental detection and build preflight. Add pure and compiled
auto-mode, explicit-sync, and awaited-dispatch regressions for callable
instances wrapped by both public function-condition types and supplied
directly.

### CR-02: `CompiledFuncCondition`'s documented subclass contract crashes when compiled

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:329-386`
**Related contract:** `/Users/akriz/code/fast_fsm/.specify/memory/spr-core-api.md:45`

**Issue:** Both the class docstring and the current SPR state that
`CompiledFuncCondition` can be subclassed from interpreted Python. A minimal
inherited subclass constructs and runs in asserted-pure mode, but the same
class against a freshly built native extension fails in the inherited
constructor with `TypeError: fast_fsm.core.CompiledFuncCondition object
expected; got __main__.InheritedCompiled`. This is a public artifact-mode crash,
and it also means the new classifier's pure-mode inherited-compiled leaf falls
outside the promised compiled/pure equivalence.

**Fix:** Make the contract explicit and identical in both artifacts. If this is
an intended subclass surface, use a mypyc-supported interpreted-subclass
boundary and add a pure/compiled construction, auto-detection, explicit-sync,
and dispatch matrix. If it is intentionally sealed, remove the subclassability
claims from the class documentation and SPR, reject subclass creation
consistently in pure mode, and direct users to the already supported
interpreted `FuncCondition` subclass surface. Do not leave the current
pure-only behavior.

---

_Reviewed: 2026-08-30T19:10:01Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
