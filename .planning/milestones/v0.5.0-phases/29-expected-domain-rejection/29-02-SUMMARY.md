---
phase: 29-expected-domain-rejection
plan: "02"
subsystem: core-runtime
tags: [expected-rejection, async, queries, conditions, cancellation]
requires:
  - phase: 29-01
    provides: bounded TransitionRejected signal and synchronous terminal selector conversion
provides:
  - terminal async rejection conversion at the three approved eligibility seams
  - observer-free rejection projection for synchronous and asynchronous queries
  - direct and composed condition propagation evidence without combinator changes
affects:
  - 29-03 lifecycle-boundary and documentation closure
  - 29-04 native, performance, and full-suite closure
actuals:
  tokens: 4432
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - async selector catches the validated control signal only at existing eligibility seams
    - condition combinators retain exception propagation by deliberate non-interference
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_expected_rejection.py
    - tests/test_condition_interface.py
key-decisions:
  - "Async selector conversion mirrors synchronous conversion at transition-guard, declarative-guard, and state-permission seams only."
  - "can_trigger and can_trigger_async consume terminal rejection as False without lifecycle, observer, history, trace, or lower-candidate work."
  - "Condition composition remains catch-free; tests prove identity propagation, ordering, and deferred await ownership."
requirements-completed: [REJECT-03, REJECT-04, REJECT-06, REJECT-07, REJECT-08, REJECT-09]
coverage:
  - id: D1
    description: Async transition selection returns the same terminal rejection metadata as synchronous selection at all three approved seams.
    requirement: REJECT-03
    verification:
      - kind: integration
        ref: tests/test_expected_rejection.py#test_reject_06_async_query_stops_at_every_approved_boundary
        status: pass
      - kind: other
        ref: uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_async.py tests/test_transition_lifecycle.py -x -q -k "query or async or cancellation or priority or rejection"
        status: pass
    human_judgment: false
  - id: D2
    description: Queries return False without mutation or observers, while triggers finalize the existing observer family once.
    requirement: REJECT-06
    verification:
      - kind: integration
        ref: tests/test_expected_rejection.py#test_reject_06_sync_query_stops_at_every_approved_boundary
        status: pass
      - kind: integration
        ref: tests/test_expected_rejection.py#test_reject_06_async_query_stops_at_every_approved_boundary
        status: pass
    human_judgment: false
  - id: D3
    description: Direct, nested, deferred, negated, synchronous, and asynchronous condition shapes propagate the exact signal without evaluating a later child.
    requirement: REJECT-08
    verification:
      - kind: unit
        ref: tests/test_condition_interface.py#test_reject_08_direct_and_synchronous_composition_preserve_signal_identity
        status: pass
      - kind: integration
        ref: tests/test_condition_interface.py#test_reject_08_deferred_composition_keeps_signal_and_cancellation_terminal
        status: pass
      - kind: integration
        ref: tests/test_condition_interface.py#test_reject_08_direct_async_leaf_and_fsm_boundary_have_distinct_owners
        status: pass
    human_judgment: false
  - id: D4
    description: Async cancellation stays a cancellation, finalizes once through existing ownership, and never falls through to a later candidate or child.
    requirement: REJECT-09
    verification:
      - kind: integration
        ref: tests/test_priority_selection.py#test_async_candidate_cancellation_finalizes_once_and_releases_ownership
        status: pass
      - kind: integration
        ref: tests/test_transition_lifecycle.py#test_async_cancellation_finalizes_once_at_the_reached_boundary
        status: pass
    human_judgment: false
duration: 4 min
completed: 2026-09-17
status: complete
---

# Phase 29 Plan 02: Query, Async, and Condition Composition Summary

**Expected domain rejection now has the same terminal, priority-aware meaning for asynchronous dispatch and observer-free queries, while condition composition preserves the original signal unchanged.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-17T16:31:15Z
- **Completed:** 2026-09-17T16:35:08Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Added the three approved `TransitionRejected` conversion catches to sequential async candidate selection, retaining the established corrupt-signal and ordinary-exception compatibility paths.
- Proved sync and async queries terminate rejection as `False` without lifecycle, observer, history, state, or lower-priority side effects; triggers retain structured metadata and exactly one failure-observer pass.
- Added direct, nested, deferred, negated, sync, and async composition evidence showing rejection and cancellation identity propagate without later-child evaluation or production combinator catches.

## Task Commits

1. **Task 1: Match query, async selection, observer, and cancellation behavior** — `1a45672` (test), `32eeb70` (feat)
2. **Task 2: Prove direct, nested, deferred, and negated composition propagation** — `ccb48cd` (test)

## Files Created/Modified

- `src/fast_fsm/core.py` — specific, cold-path async conversion for validated expected rejection at guard, declarative guard, and state-permission selection seams.
- `tests/test_expected_rejection.py` — singleton/grouped, internal/external, sync/async query and trigger oracle matrix.
- `tests/test_condition_interface.py` — condition signal identity, short-circuit, deferred ownership, cancellation, and selector-boundary tests.

## Decisions Made

- Async conversion reuses the synchronous result construction path and remains inside the existing single sequential selector.
- Query behavior is a projection from terminal selector results rather than a separate rejection protocol.
- No production `conditions.py` change was appropriate: its existing lack of catch/return logic is exactly the desired propagation behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `task typecheck-ty` continues to report the pre-existing relative-import diagnostic for `src/fast_fsm/core.py`. Blocking mypy passed; the advisory diagnostic is unrelated to this plan's selector changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 29-03 can now concentrate on lifecycle-boundary classification and public documentation, with async selector, query, composition, cancellation, and observer semantics covered by focused regression evidence.

## Self-Check: PASSED

- The three modified runtime/test artifacts and this summary exist.
- Task commits `1a45672`, `32eeb70`, and `ccb48cd` exist in repository history.
- The Plan 29 adjacent regression suite, Ruff, blocking mypy, and slots-policy audit passed; ty remains the documented pre-existing advisory diagnostic.

---
*Phase: 29-expected-domain-rejection*
*Completed: 2026-09-17*
