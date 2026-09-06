---
phase: 17-atomic-transition-lifecycle
plan: "04"
subsystem: runtime
tags: [asyncio, lifecycle, cancellation, callbacks, mypyc]
requires:
  - phase: 17-atomic-transition-lifecycle
    provides: Synchronous lifecycle stages, failure result metadata, and one failure-observer finalizer
provides:
  - Explicit same-slot asynchronous lifecycle execution
  - Native cancellation finalization with commit/history coherence
  - Event-synchronized async lifecycle and builder regressions
affects: [core-runtime, async-dispatch, callback-contract, phase-17-verification]
tech-stack:
  added: []
  patterns: [explicit async lifecycle runner, event-synchronized cancellation tests, fresh pure-native parity]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_transition_lifecycle.py
    - tests/test_async.py
    - tests/test_builder.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - Async callbacks share their synchronous source-exit and destination-enter semantic slots rather than running as a tail.
  - Native cancellation is observed once, then bare re-raised without shielding, rollback, or suffix continuation.
requirements-completed: [LIFE-01, LIFE-03, LIFE-04, LIFE-05, LIFE-06]
coverage:
  - id: D1
    description: Async transition callbacks, failure results, guard context, and declarative dispatch follow the synchronous lifecycle contract.
    requirement: LIFE-06
    verification:
      - kind: integration
        ref: tests/test_transition_lifecycle.py#test_async_lifecycle_awaits_callbacks_at_their_matching_slots
        status: pass
      - kind: integration
        ref: tests/test_async.py#TestAsyncPerStateCallbacks
        status: pass
    human_judgment: false
  - id: D2
    description: Async cancellation finalizes ordered failure observers once, preserves the reached commit/history boundary, and re-raises the same cancellation object.
    requirement: LIFE-05
    verification:
      - kind: integration
        ref: tests/test_transition_lifecycle.py#test_async_cancellation_finalizes_once_at_the_reached_boundary
        status: pass
      - kind: integration
        ref: fresh compiled core origin plus cancellation/parity pytest selection
        status: pass
    human_judgment: false
actuals:
  tokens: 10906.75
  tasks: 2
  commits: 4
metrics:
  duration: 11 min
  completed: 2026-09-01
status: complete
---

# Phase 17 Plan 04: Async Lifecycle and Cancellation Summary

Async transition execution now awaits callbacks at their matching lifecycle slots and preserves native cancellation identity, observer behavior, and commit/history truth.

## What Changed

### Task 1: Run the async lifecycle at the matching semantic slots

- Replaced the sync-runner-plus-tail approach with an explicit async lifecycle runner.
- Kept synchronous callbacks inline; awaited source exit and destination enter callbacks immediately after their synchronous registries.
- Aligned async ordinary failures, declarative dispatch, callback order, and builder wiring with the staged synchronous outcome contract.
- Updated the core API memory with the same-slot and exactly-once declarative invariants.

### Task 2: Preserve cancellation identity at every awaited boundary

- Added `asyncio.Event`-synchronized guard, source-exit, destination-enter, and declarative cancellation cases without timing sleeps.
- Finalized failure observers once with a redacted `Transition cancelled at <stage>` result and then bare re-raised the original `CancelledError`.
- Verified pre-commit cancellation leaves source/history empty while post-commit cancellation retains destination/one history record.
- Documented native propagation, suffix suppression, and no-shield/no-rollback behavior.

## Verification

- Ruff format and lint passed for `core.py` and all touched lifecycle suites.
- Blocking `task typecheck-mypy` passed.
- Fresh isolated pure-source lifecycle/cancellation/declarative selection passed.
- Fresh compiled `core` origin was asserted and its cancellation/parity lifecycle selection passed.
- SPR token assertions for same-slot and cancellation contracts passed.

## Task Commits

1. `192a490` — `test(17-04): define async same-slot lifecycle contract`
2. `e2e6bc2` — `feat(17-04): run async lifecycle at matching slots`
3. `d114702` — `test(17-04): define cancellation lifecycle contract`
4. `de5e983` — `feat(17-04): preserve native cancellation lifecycle`

## Decisions Made

- The stable lifecycle stage remains shared between sync and async callbacks at the same semantic slot.
- Cancellation uses a distinct redacted observer message while retaining the original exception only as hidden cause and preserving its identity when re-raised.

## Deviations from Plan

None - plan executed as specified. The task runner’s fresh compiled build exceeded its response window after producing the native extension, so the exact compiled test selection was completed directly in that freshly created harness tree after asserting the `.so` origin.

## Known Stubs

None.

## Issues Encountered

- Fresh compiled cancellation tests emit a CPython 3.12 `throw(type, exc, tb)` deprecation warning from the mypyc-generated path. Behavior passed; follow-up is tracked as linked bead `fast_fsm-2fh` and is out of Phase 17 scope.

## Next Phase Readiness

Plan 17-05 can use the same event-synchronized lifecycle matrix for full fresh-origin conformance, documentation, and throughput evidence.

## Self-Check: PASSED

- Confirmed all five modified runtime, test, and API-memory files plus this summary exist.
- Confirmed all four Task 1/Task 2 RED-GREEN commits are present in history.
- Confirmed the structured coverage block classifies both deliverables as automated and passing.
