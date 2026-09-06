---
phase: 17-atomic-transition-lifecycle
plan: 01
subsystem: runtime
tags: [lifecycle, transition-result, callbacks, mypyc, verification]
requires:
  - phase: 16-canonical-graph-dispatch-invariants
    provides: canonical dispatch preparation, bounded history, and origin-safe evidence tooling
provides:
  - committed destination-enter failure tracer with one observer finalizer
  - additive TransitionResult lifecycle fields and compiled cause chaining
  - explicit Phase 17 clean-export suite and lifecycle throughput selection
affects: [phase-17-plans-02-05, core-runtime, release-evidence]
actuals:
  tokens: 9193
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - stage-aware result finalization with a no-callback commit helper
    - explicit clean-export overlays for lifecycle semantics
key-files:
  created:
    - tests/test_transition_lifecycle.py
    - .planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md
  modified:
    - src/fast_fsm/core.py
    - tools/phase16_isolated_verify.py
    - tests/test_boundary_negative.py
    - tests/test_mypyc_guard.py
    - tests/test_performance_benchmarks.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Destination State.on_enter failures return a committed destination-enter result, preserving the original exception only as hidden cause data."
  - "Phase 17 semantic evidence runs only in fresh pure or freshly compiled exports; checkout native shadows remain untouched."
patterns-established:
  - "Failure observers run through one non-recursive finalizer and preserve the caller callback signature."
  - "Lifecycle performance claims remain floor-based and environment-labelled rather than reporting an unrepeatable exact rate."
requirements-completed: [LIFE-01, LIFE-02, LIFE-03, LIFE-04, LIFE-05, LIFE-06]
coverage:
  - id: D1
    description: "Committed destination-enter failure returns truthful state, history, stage, and cause data."
    requirement: LIFE-03
    verification:
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_tracer_destination_enter_failure_commits_and_finalizes_once"
        status: pass
    human_judgment: false
  - id: D2
    description: "TransitionResult remains additive, redacts causes, and chains its opt-in error boundary in pure and compiled modes."
    requirement: LIFE-04
    verification:
      - kind: unit
        ref: "tests/test_boundary_negative.py#TestTransitionResult.test_additive_lifecycle_fields_preserve_legacy_constructor_and_equality"
        status: pass
    human_judgment: false
  - id: D3
    description: "The Wave 0 lifecycle contract and compiled success path execute from asserted clean exports."
    requirement: LIFE-06
    verification:
      - kind: integration
        ref: "uv run python tools/phase16_isolated_verify.py --suite phase17"
        status: pass
    human_judgment: false
duration: 16 min
completed: 2026-09-01
status: complete
---

# Phase 17 Plan 01: Wave 0 Lifecycle Tracer Summary

**A committed destination-enter failure now returns truthful lifecycle state, preserves its hidden cause, notifies observers once, and is proven in fresh pure and compiled exports.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-01T16:29:23Z
- **Completed:** 2026-09-01T16:45:38Z
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments

- Added the first production lifecycle slice: a destination `State.on_enter` exception commits the destination and its history entry, stops the suffix, returns `committed=True`/`stage="destination-enter"`, and retains cause identity without exposing payload text.
- Added one ordered, non-recursive failure observer finalizer and additive `TransitionResult` fields without breaking five-field positional construction or opt-in `TransitionError` use.
- Established the eight-family lifecycle probe inventory, fresh Phase 17 pure/compiled isolation suite, and compiled lifecycle-success performance selection.

## Task Commits

1. **Task 1 RED: destination-enter tracer** — `8ff9ef4` (test)
2. **Task 1 GREEN: committed destination-enter failure** — `ad2ac06` (feat)
3. **Task 2 RED: Wave 0 compatibility guards** — `3573ce4` (test)
4. **Task 2 GREEN: fresh lifecycle evidence suite** — `0408c18` (feat)

## Files Created/Modified

- `src/fast_fsm/core.py` — result fields, commit seam, observer finalizer, and post-commit tracer.
- `tests/test_transition_lifecycle.py` — real-object tracer and eight-family probe inventory.
- `tools/phase16_isolated_verify.py` — backwards-compatible `phase17` clean-export suite.
- `tests/test_boundary_negative.py`, `tests/test_mypyc_guard.py`, and `tests/test_performance_benchmarks.py` — compatibility, source-boundary, and fixed-floor guards.
- `.specify/memory/spr-core-api.md` and `17-PERFORMANCE-EVIDENCE.md` — synchronized lifecycle and evidence contract.

## Decisions Made

- Kept ordinary triggers value-returning; stored causes are visible only on `TransitionResult` and explicitly chained when `raise_if_failed()` is requested.
- Committed state and history through one no-callback helper before the destination hook, making post-commit failure observable without a rollback policy.
- Used asserted clean exports for every lifecycle claim because local native shadows intentionally do not represent edited source.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Compiled behavior] Preserved `TransitionError.__cause__` under mypyc**

- **Found during:** Task 1
- **Issue:** `raise error from result.cause` preserved chaining in pure Python but not the freshly compiled extension.
- **Fix:** Assign `error.__cause__` before raising, then prove cause identity in both artifact modes.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_transition_lifecycle.py`
- **Verification:** Fresh compiled tracer test passed.
- **Committed in:** `ad2ac06`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** The repair preserves the plan's public opt-in error contract in both supported artifact modes without expanding lifecycle scope.

## Issues Encountered

The developer checkout contains intentional stale native shadows, so direct source tests imported an older extension. The isolated harness asserted clean `.py` and freshly built native origins instead; no checkout artifact was removed or accepted as evidence.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plans 17-02 through 17-04 can expand the same result/finalizer/commit seams across the remaining failure stages and async cancellation. Plan 17-05 can use the established Phase 17 suite for final documentation and release evidence.

## Self-Check: PASSED

- `17-01-SUMMARY.md` exists on disk.
- All four RED/GREEN task commits are present in git history.
- The fresh pure/compiled `phase17` suite and compiled throughput selection passed.
