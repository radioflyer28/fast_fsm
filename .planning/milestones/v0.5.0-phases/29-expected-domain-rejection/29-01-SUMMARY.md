---
phase: 29-expected-domain-rejection
plan: "01"
subsystem: core-runtime
tags: [expected-rejection, priority-selection, mypyc, slots-policy]
requires:
  - phase: 28-same-state-transition-modes
    provides: selected-entry priority/internal metadata and single failure finalization
provides:
  - bounded public TransitionRejected control signal
  - comparison-neutral TransitionResult rejection metadata
  - terminal synchronous conversion at all three eligibility seams
affects:
  - 29-02 query, composition, and async parity
  - 29-03 lifecycle-boundary and public documentation closure
  - 29-04 native, performance, and full-suite closure
actuals:
  tokens: 10656
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - terminal TransitionResult conversion at an approved eligibility boundary
    - cold-path revalidation of public metadata before result construction
key-files:
  created:
    - tests/test_expected_rejection.py
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/core.pyi
    - src/fast_fsm/__init__.py
    - tools/release_evidence.py
    - tests/test_mypyc_guard.py
    - tests/test_release_evidence.py
key-decisions:
  - "TransitionRejected accepts only exact bounded ASCII strings and is revalidated only on the rejection path."
  - "Expected rejection remains a terminal TransitionResult; None remains reserved for ordinary group fallthrough."
  - "Failure observers remain owned by existing trigger finalization, with no rejection listener family."
requirements-completed: [REJECT-01, REJECT-02, REJECT-03, REJECT-04, REJECT-05, REJECT-07]
coverage:
  - id: D1
    description: Bounded public signal and additive structured result contract.
    requirement: REJECT-01
    verification:
      - kind: unit
        ref: tests/test_expected_rejection.py#test_reject_01_public_signal_constructs_valid_exact_codes
        status: pass
      - kind: unit
        ref: tests/test_expected_rejection.py#test_reject_05_result_tail_is_read_only_and_preserves_error_boundary
        status: pass
    human_judgment: false
  - id: D2
    description: Synchronous guard, declarative guard, and permission rejection stop priority selection and retain one observer finalization path.
    requirement: REJECT-03
    verification:
      - kind: integration
        ref: tests/test_expected_rejection.py#test_reject_03_approved_boundaries_abort_priority_groups
        status: pass
      - kind: integration
        ref: tests/test_expected_rejection.py#test_reject_07_observers_finalize_once_and_reentry_stays_isolated
        status: pass
      - kind: other
        ref: uv run pytest tests/test_expected_rejection.py tests/test_priority_selection.py tests/test_condition_interface.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_logging_config.py tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q
        status: pass
    human_judgment: false
duration: 16min
completed: 2026-09-17
status: complete
---

# Phase 29 Plan 01: Expected Domain Rejection Summary

**Fast FSM now turns one bounded, public expected-domain signal into a terminal synchronous transition result without lower-priority fallthrough or a new observer API.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-17T16:10:00Z
- **Completed:** 2026-09-17T16:25:34Z
- **Tasks:** 2/2
- **Files modified:** 9

## Accomplishments

- Added package-root `TransitionRejected(code)` with exact built-in-string, bounded ASCII validation and cold-path conversion revalidation.
- Extended `TransitionResult` with comparison-neutral, repr-visible `rejection_code` and a derived read-only `rejected` property while retaining `TransitionError` as the failed-result boundary.
- Converted synchronous transition guards, declarative guards, and state-permission checks into terminal rejection results that preserve selected priority/internal metadata, avoid lifecycle/history work, finalize existing observers once, and emit only bounded debug code metadata.
- Registered the new non-native exception consistently across stubs, package exports, structural tests, release evidence, maintainer instructions, and the living core API contract.

## Task Commits

1. **Task 1: Trace the bounded public signal into one structured synchronous result** — `cfbcbce` (test), `0ac3e43` (feat)
2. **Task 2: Complete synchronous three-seam terminality, observation, and safe logging** — `93ef76c` (test), `67ae57d` (feat)

## Files Created/Modified

- `src/fast_fsm/core.py` — public signal/result contract, cold-path validation, synchronous three-seam conversion, and bounded debug logging.
- `src/fast_fsm/core.pyi` and `src/fast_fsm/__init__.py` — typed/package-root API exposure.
- `tests/test_expected_rejection.py` — central REJECT-01 through REJECT-07 synchronous semantic oracle.
- `tests/test_mypyc_guard.py`, `tests/test_release_evidence.py`, and `tools/release_evidence.py` — synchronized fourth measured exception authority.
- `.github/copilot-instructions.md` and `.specify/memory/spr-core-api.md` — maintained slots and selection contracts.

## Decisions Made

- Kept rejection inside the existing selector outcome algebra: `None` remains ordinary false fallthrough, while a rejected `TransitionResult` is terminal.
- Performed signal revalidation only after a signal is caught, so untouched singleton dispatch carries no rejection validation or allocation cost.
- Used the established trigger finalizer and observer signature, avoiding a parallel rejection callback family.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `task typecheck-ty` continues to report the pre-existing `src/fast_fsm/core.py` relative-import diagnostic. Blocking mypy passed; the advisory result does not originate from this plan's change.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 29-02 can extend the established terminal result and three-seam boundary into observer-free queries, condition composition, async parity, and cancellation proof. The current implementation intentionally does not convert signals outside those eligibility seams.

## Self-Check: PASSED

- The summary, public core/stub/export artifacts, and central oracle exist.
- Task commits `cfbcbce`, `0ac3e43`, `93ef76c`, and `67ae57d` exist in repository history.
- The complete Plan 29-01 adjacent regression command and slots-policy audit passed after the implementation commits.

---
*Phase: 29-expected-domain-rejection*
*Completed: 2026-09-17*
