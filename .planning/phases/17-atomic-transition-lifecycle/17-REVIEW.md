---
phase: 17-atomic-transition-lifecycle
reviewed: 2026-09-01T18:16:05Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - .specify/decisions/ADR-004-atomic-transition-lifecycle.md
  - .specify/memory/spr-core-api.md
  - README.md
  - docs/QUICK_START.md
  - docs/dev/architecture.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/core.py
  - tests/test_advanced_functionality.py
  - tests/test_async.py
  - tests/test_basic_functionality.py
  - tests/test_boundary_negative.py
  - tests/test_builder.py
  - tests/test_listeners.py
  - tests/test_mypyc_guard.py
  - tests/test_performance_benchmarks.py
  - tests/test_safety_kwargs.py
  - tests/test_transition_lifecycle.py
  - tools/phase16_isolated_verify.py
findings:
  critical: 3
  warning: 2
  info: 0
  total: 5
status: issues_found
---

# Phase 17: Code Review Report

**Reviewed:** 2026-09-01T18:16:05Z  
**Depth:** standard  
**Files Reviewed:** 20  
**Status:** issues_found

## Summary

The staged sync/async lifecycle is substantially implemented, but three defects violate Phase 17's compatibility, atomic-commit, and exactly-once guarantees. Fresh pure-source reproductions confirmed that successful trigger results no longer compare equal to legacy five-field `TransitionResult` values, an ordinary commit-time exception leaves state and history divergent, and a failure observer can extend the live registry while it is being iterated and receive multiple calls from one failed transition. The advertised single stage catalog is also unused, and one new README example fails when executed sequentially.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Additive fields break legacy `TransitionResult` equality

**Classification:** BLOCKER  
**File:** `src/fast_fsm/core.py:277`  
**Issue:** `committed` and `stage` participate in generated dataclass equality, while real successful triggers now set `committed=True`. Before Phase 17, callers could compare a returned result with `TransitionResult(True, "a", "b", "go", "")`; that same five-field value now defaults `committed=False` and compares unequal. This contradicts Plan 17-01's explicit promise that legacy five-field construction and equality remain valid. A fresh pure-source reproduction printed `legacy_equal False`. The added compatibility test only compares two eight-field values and therefore misses the regression.

**Fix:** Preserve equality over the established five-field surface, either by excluding all appended metadata from comparison or by defining an explicit compatibility-preserving `__eq__`. Add a regression that compares actual sync and async trigger results against five-field expected values.

```python
committed: bool = field(default=False, compare=False)
stage: Optional[str] = field(default=None, compare=False)
cause: Optional[BaseException] = field(default=None, repr=False, compare=False)
```

### CR-02: Commit failure can change state without recording history or returning a staged failure

**Classification:** BLOCKER  
**File:** `src/fast_fsm/core.py:2039`  
**Issue:** `_commit_transition()` assigns `_current_state` before constructing and appending the history record. If record construction or append raises, the destination is current but history remains empty. Neither sync call site at line 2204 nor async call site at line 2863 catches that exception, so no `TransitionResult(stage="commit")` is produced and failure observers are not notified. A fresh pure-source fault injection that made `time.monotonic()` raise `OSError` produced `state b history 0` and propagated the exception. This directly violates LIFE-05/D-12 and makes the documented `commit` stage unreachable.

**Fix:** Prepare the record before mutating either committed field, order the remaining non-user operations so ordinary exceptions cannot leave a partial commit, and convert ordinary commit failure through the shared staged result/finalizer in both runners. Add sync/async fault-injection tests asserting source state, empty history, `stage="commit"`, `committed=False`, original cause identity, and one observer pass.

```python
record = None
if self._history is not None:
    record = TransitionRecord(old_state.name, trigger, to_state.name, time.monotonic())
if record is not None:
    self._history.append(record)
self._current_state = to_state
```

### CR-03: Failure observers iterate a live registry and can defeat exactly-once delivery

**Classification:** BLOCKER  
**File:** `src/fast_fsm/core.py:2100`  
**Issue:** `_finalize_failure()` iterates `self._on_failed_callbacks` directly. Python list iteration observes appended entries, so an observer that calls `machine.on_failed(...)` while handling a failure extends the current pass. A bounded reproduction registered one observer, had it append itself until five calls, and one missing-trigger attempt invoked it five times. If it appends unconditionally, finalization never terminates. This violates LIFE-04/D-09's exactly-once contract and creates a denial-of-service path on every sync failure and async cancellation.

**Fix:** Snapshot the registry at finalization entry and iterate the snapshot. Add sync and async/cancellation regressions where an observer registers another observer; the new registration must begin with the next failed transition, not the current pass.

```python
observers = tuple(self._on_failed_callbacks)
for observer_index, observer in enumerate(observers):
    ...
```

## Warnings

### WR-01: The documented authoritative lifecycle stage catalog is dead code

**Classification:** WARNING  
**File:** `src/fast_fsm/core.py:57`  
**Issue:** `_LIFECYCLE_STAGES` and `_DESTINATION_ENTER_STAGE` are never read. Every producer hard-codes stage strings independently across preparation, sync execution, async execution, and cancellation. `docs/dev/architecture.md:163` nevertheless says both runners share this catalog. The current shape provides no protection against sync/async spelling drift and already advertises the unreachable `commit` stage.

**Fix:** Make stage producers consume one authoritative set of constants (and validate public `TransitionResult.stage` values), or remove the unused catalog and correct the architecture documentation. Add a contract test that enumerates every produced stage in both artifact modes.

### WR-02: README's new one-liner example triggers `start` twice from incompatible states

**Classification:** WARNING  
**File:** `README.md:204`  
**Issue:** The example first runs `result = fsm.trigger("start")` at line 185, which normally commits the destination, then demonstrates chaining by firing `start` again. In the Quick Start machine, `start` is not registered from the destination, so the advertised one-liner raises `TransitionError` when the snippet is followed sequentially. This escaped the README example tests because the block is not executed as one scenario.

**Fix:** Reuse the existing result (`target = result.raise_if_failed().to_state`), reset the machine before the second trigger, or use the valid return trigger as `docs/QUICK_START.md` does. Convert this block to an executable documentation test.

---

_Reviewed: 2026-09-01T18:16:05Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
