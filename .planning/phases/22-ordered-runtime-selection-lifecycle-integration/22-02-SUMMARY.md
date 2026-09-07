---
phase: 22-ordered-runtime-selection-lifecycle-integration
plan: 02
subsystem: core-transition-selection
tags: [python, asyncio, mypyc, fsm, priority, guarded-transitions, lifecycle]
requires:
  - phase: 22-01
    provides: Synchronous prepared-winner selection over direct singleton entries and frozen priority groups.
provides:
  - Sequential asynchronous candidate selection with one eligibility stage awaited at a time.
  - Terminal async exception, cancellation, and exhaustion finalization before one lifecycle handoff.
affects: [phase-22-03-runtime-metadata, phase-23-construction-parity]
actuals:
  tokens: 9423
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - Capture source/slot identity, await one candidate stage at a time, then hand one prepared winner to the existing lifecycle runner.
    - Use task-local cancellation-stage bookkeeping only on owned trigger paths; observer-free queries retain no lifecycle finalization.
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_priority_selection.py
    - tests/test_async.py
    - tests/test_transition_lifecycle.py
key-decisions:
  - "Async candidate selection mirrors the synchronous prepared-dispatch union and scans only the stored frozen tuple when a slot has competitors."
  - "Cancellation records the latest awaited selection stage through a task-local marker, then reaches the existing owned trigger finalizer once and bare re-raises."
patterns-established:
  - "Normal false is local candidate-scan control; ordinary exceptions and cancellation never activate a lower-priority candidate."
  - "Async queries use the same selector but are observer-free, lifecycle-free, history-free, and trace-finalization-free."
requirements-completed: [SEL-02, SEL-03, SEL-04]
coverage:
  - id: D1
    description: "Async priority groups await guards sequentially in ascending stored order and stop at the first eligible winner."
    requirement: SEL-02
    verification:
      - kind: integration
        ref: "tests/test_priority_selection.py#test_async_group_awaits_one_candidate_at_a_time_in_priority_order"
        status: pass
      - kind: integration
        ref: "tests/test_priority_selection.py#test_async_group_does_not_speculate_beyond_the_current_candidate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Async exceptions, cancellation, and selection exhaustion finalize truthfully without a lower-candidate fallback."
    requirement: SEL-02
    verification:
      - kind: integration
        ref: "tests/test_priority_selection.py#test_async_candidate_cancellation_finalizes_once_and_releases_ownership"
        status: pass
      - kind: integration
        ref: "tests/test_priority_selection.py#test_async_permission_cancellation_uses_permission_stage_without_fallback"
        status: pass
    human_judgment: false
  - id: D3
    description: "Only one prepared async winner crosses into lifecycle, while queries remain side-effect free."
    requirement: SEL-03
    verification:
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_async_group_selection_completes_before_one_lifecycle_failure"
        status: pass
      - kind: integration
        ref: "tests/test_priority_selection.py#test_can_trigger_async_scans_the_same_order_without_lifecycle"
        status: pass
    human_judgment: false
  - id: D4
    description: "Async group exhaustion reports one redacted selection-stage failure while missing trigger and singleton failures retain their established boundaries."
    requirement: SEL-04
    verification:
      - kind: integration
        ref: "tests/test_priority_selection.py#test_async_group_terminal_exception_and_exhaustion_finalize_once"
        status: pass
    human_judgment: false
duration: 6m
completed: 2026-09-07
status: complete
---

# Phase 22 Plan 02: Async Priority Selection Summary

**Async priority groups now await exactly one candidate stage at a time, select one prepared winner before lifecycle, and fail closed on exception, cancellation, or exhaustion.**

## Performance

- **Duration:** 6m
- **Started:** 2026-09-07T00:51:34Z
- **Completed:** 2026-09-07T00:57:05Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added a direct-singleton/local-group asynchronous selector shared by `trigger_async()` and `can_trigger_async()`.
- Preserved captured source and target handler identity through awaits, while awaiting transition guard, declarative guard, then state permission in order.
- Added event-handshake proof for non-speculation, terminal exception/cancellation, single observer finalization, query isolation, and no lower-candidate lifecycle fallback.

## Task Commits

1. **Task 1: Select one async winner with strictly sequential awaits** - `5a23f9e` (`feat`)
2. **Task 2: Preserve terminal exceptions, cancellation, exhaustion, and one async lifecycle** - `aec0731` (`feat`)

## Files Created/Modified

- `src/fast_fsm/core.py` - Implements async prepared-winner selection and cancellation-stage reporting while retaining the existing lifecycle seam.
- `tests/test_priority_selection.py` - Covers priority order, async handshakes, terminal failures, cancellation, exhaustion, query isolation, and ownership recovery.
- `tests/test_async.py` - Confirms grouped query exceptions remain terminal and observer-free.
- `tests/test_transition_lifecycle.py` - Proves all async eligibility work precedes the one lifecycle attempt and later candidates remain untouched on lifecycle failure.

## Decisions Made

- Used a task-local `ContextVar` solely for owned-trigger cancellation-stage truth; it avoids mutable machine state and leaves queries observer-free.
- Retained the exact `_PreparedDispatch | TransitionResult` selector boundary, rather than adding a parallel async outcome type or another lifecycle runner.

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

Focused tests were added and observed failing before the corresponding implementation, then passed after it. The red tests and implementation were committed together in each task feature commit rather than as standalone `test(22-02)` commits.

## Issues Encountered

- Beads' local Dolt server was unavailable at commit time. Its pre-commit export warning did not prevent the scoped Git commits.
- The advisory `ty` check initially identified dynamically overridden async policy calls as non-callable. Replacing `hasattr` with a guarded callable cast preserved the dynamic extension seam and cleared both type checks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 22-03 can add selected/evaluated priority metadata to results, history, and trace without changing async selection or lifecycle ownership.
- No Phase 22 Plan 02 blockers remain.

## Self-Check: PASSED

- Both task commits resolve in Git, all four scoped files exist, and the latest pure/offline targeted tests, Ruff checks, mypy, and ty checks passed.
