---
phase: 16-canonical-graph-dispatch-invariants
reviewed: 2026-08-30T15:36:12Z
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
  critical: 3
  warning: 1
  info: 0
  total: 4
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-08-30T15:36:12Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

The three iteration-two findings are repaired on their covered ordinary-dispatch and builder-preflight paths: all 30 focused cases passed in both asserted-pure and freshly compiled contexts. The final pass nevertheless found two uncovered runtime correctness defects and one release-evidence policy regression. Direct `AsyncDeclarativeState` policy calls still use the old synchronous wrapper path, builder publication still uses value equality despite the locked identity contract, and the regenerated manifest lowers the committed coverage floor in a way that makes the read-only regression gate accept the regression. Contributor documentation also contradicts the compiled subclassing behavior the phase itself relies on.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Direct async declarative policy still executes wrapped async guards synchronously

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:2904-2912`

**Issue:** Ordinary `AsyncStateMachine.can_trigger_async()` and `trigger_async()` now use the machine-owned iterative evaluator, but the public `AsyncDeclarativeState.can_transition_async()` method still handles every non-direct `AsyncCondition` through `condition.check()`. A supported `NotCondition(AsyncCondition(...))`, `NegatedCondition`, `AndCondition`, `OrCondition`, or `FuncCondition` wrapping an async callable therefore reaches `asyncio.run()` from an active loop or returns an un-awaited coroutine. In an asserted-pure reproduction, `NotCondition` around an async leaf that returned `False` should have allowed the transition, but the method returned `False`, logged `asyncio.run() cannot be called from a running event loop`, and emitted `RuntimeWarning: coroutine ... was never awaited`. This contradicts the method's async-condition contract and leaves direct state policy behavior inconsistent with ordinary dispatch.

**Fix:** Extract the iterative wrapper evaluator into a private helper that both machine dispatch and `AsyncDeclarativeState.can_transition_async()` can call, rather than invoking `Condition.check()` directly. Preserve short-circuiting and await any awaitable leaf result. Add direct-call pure and compiled regressions for all supported wrapper shapes plus `FuncCondition(async_callable)`, asserting correct results and no runtime warnings.

### CR-02: Builder publication silently drops valid states whose objects compare equal

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:3345-3348`

**Issue:** Phase 16 locks canonical registration to exact object identity, but `FSMBuilder.build()` skips the initial state with `state != self._initial_state`. `State` is intentionally subclassable, so a valid state subclass may define equality independently of identity. An asserted-pure reproduction added two distinct-name state objects whose subclass returns `True` from `__eq__`; `build()` succeeded but returned a machine whose state list contained only the initial state, silently omitting the staged target. This violates D-01/GRAF-02 and the builder's publish-complete-or-fail contract.

**Fix:** Use identity at publication:

```python
for state in self._states.values():
    if state is not self._initial_state:
        candidate.add_state(state)
```

Add pure and compiled tests with a `State` subclass whose distinct instances compare equal, proving both differently named objects are registered and same-name identity conflicts retain the existing rejection semantics.

### CR-03: Baseline refresh lowers and thereby bypasses the locked coverage regression floor

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/evidence/release-baseline.json:58-63`

**Issue:** The iteration-two refresh changed total coverage from 96.08% to 95.68% and `core.py` coverage from 94.27% to 93.75%. Coverage is not an environment-only observation: inherited Phase 15 decision D-06 explicitly requires regressions to be blocked from the measured baseline, `validate_manifest_regressions()` treats both percentages as strict non-decreasing fields, and `docs/dev/testing.md` calls the check a regression gate. The Phase 16 helper's `baseline-write` path (`tools/phase16_isolated_verify.py:265-286`) regenerates and atomically replaces the manifest without comparing it to the prior committed floor; the subsequent check therefore compares against the newly lowered values and passes. This converts a real regression into a new accepted threshold and weakens the release gate rather than merely recording an allowed source/environment observation.

**Fix:** Restore coverage to at least 96.08% total and 94.27% for `core.py` with tests for the new declarative/builder branches, then regenerate the manifest. Also make the intentional Phase 16 baseline-export path validate the generated manifest against the existing tracked manifest before replacement, with an explicit separately reviewed migration mechanism if a future milestone deliberately changes a floor. Add a regression test proving `baseline-write` cannot silently lower either coverage field.

## Warnings

### WR-01: Contributor guidance falsely prohibits supported `State` subclass tests

**Classification:** WARNING

**File:** `/Users/akriz/code/fast_fsm/docs/dev/architecture.md:200-205`

**Issue:** The guide says tests must not inherit from `State` because compiled classes cannot be subclassed from interpreted Python; `docs/dev/testing.md:68-71` repeats the rule. That is false for `State`, `CallbackState`, `DeclarativeState`, and `AsyncDeclarativeState`, which deliberately use `@mypyc_attr(allow_interpreted_subclasses=True)`. The iteration-two compatibility regressions themselves subclass `DeclarativeState`/`AsyncDeclarativeState` and pass against the freshly compiled extension. The blanket prohibition discourages the exact compiled compatibility coverage needed to catch CR-01 and CR-02 and contradicts the architecture guard.

**Fix:** Distinguish the supported state subclass surfaces from closed compiled classes such as `StateMachine`. Require pure/compiled parity tests for public subclass hooks, while retaining composition guidance where inheritance is not part of the public contract.

---

_Reviewed: 2026-08-30T15:36:12Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
