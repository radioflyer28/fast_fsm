---
phase: 29-expected-domain-rejection
plan: "03"
subsystem: runtime-contract-and-documentation
tags: [expected-rejection, lifecycle, logging, sphinx]
requires:
  - phase: 29-02
    provides: selector-only sync/async expected-rejection conversion and condition parity
provides:
  - lifecycle-boundary classification evidence for TransitionRejected
  - payload-confidential expected-rejection logging evidence
  - focused public core and condition API reference
affects:
  - 29-04 native and full-suite closure
  - 30-builder-first-construction-and-persistence-parity
actuals:
  tokens: 4002.75
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns:
    - selector-only expected-rejection conversion
    - ordinary lifecycle failure preservation outside eligibility
key-files:
  created: []
  modified:
    - tests/test_expected_rejection.py
    - tests/test_transition_lifecycle.py
    - tests/test_logging_config.py
    - docs/api/core.md
    - docs/api/conditions.md
key-decisions:
  - "Only transition guards, declarative guards, and state permission hooks convert TransitionRejected into rejection metadata."
  - "Lifecycle and observer signals retain their original cause, stage, commit, history, priority, and internal-mode truth."
  - "The public reference documents bounded debug metadata without extending Phase 32 tutorial scope."
requirements-completed: [REJECT-02, REJECT-03, REJECT-07, REJECT-09]
coverage:
  - id: D1
    description: Lifecycle, timing, declarative-action, and observer-raised signals remain ordinary staged failures.
    requirement: REJECT-09
    verification:
      - kind: integration
        ref: tests/test_expected_rejection.py#test_reject_09_outside_boundary_lifecycle_signal_stays_an_ordinary_failure
        status: pass
      - kind: integration
        ref: tests/test_transition_lifecycle.py#test_sync_lifecycle_callback_failure_stops_the_suffix_at_its_stage
        status: pass
    human_judgment: false
  - id: D2
    description: Expected-rejection logs contain only validated debug metadata and never signal or payload representations.
    requirement: REJECT-02
    verification:
      - kind: unit
        ref: tests/test_logging_config.py#test_expected_rejection_logs_only_validated_debug_metadata
        status: pass
    human_judgment: false
  - id: D3
    description: The core and conditions API pages distinguish false eligibility, expected rejection, ordinary failures, and cancellation.
    requirement: REJECT-03
    verification:
      - kind: other
        ref: uv run sphinx-build -b html docs docs/_build/html -W --keep-going
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-09-17
status: complete
---

# Phase 29 Plan 03: Lifecycle Boundary and API Contract Summary

**Expected domain rejection is now proven selector-only: the same signal at lifecycle, timing, observer, or control boundaries remains an ordinary failure without exposing payloads.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-17T16:36:43Z
- **Completed:** 2026-09-17T16:44:46Z
- **Tasks:** 1/1
- **Files modified:** 5

## Accomplishments

- Added an outside-boundary matrix for timing plus every synchronous pre- and post-commit lifecycle stage, including declarative handlers, trigger callbacks, after listeners, and observer isolation.
- Proved rejected-selector logging emits only the validated debug code and never calls a hostile signal or caller payload representation.
- Documented the exact `TransitionRejected` grammar, result/escalation/query behavior, selector-only conversion sites, condition propagation, and ordinary failure/cancellation boundaries.

## Task Commits

1. **Task 1: Prove outside-boundary classification, logging safety, and API truth** — `368f6e8` (test)

## Files Created/Modified

- `tests/test_expected_rejection.py` — central expected-rejection oracle for timing, lifecycle, and observer boundaries.
- `tests/test_transition_lifecycle.py` — full callback-stage and declarative-handler coverage for ordinary signal handling.
- `tests/test_logging_config.py` — hostile-representation logging confidentiality evidence.
- `docs/api/core.md` — public signal, result, query, logging, and selector-boundary reference.
- `docs/api/conditions.md` — direct and composed-condition propagation reference.

## Decisions Made

- Kept all non-eligibility handling catch-free: no lifecycle, observer, timing, trace, or callback path reclassifies `TransitionRejected` as an expected result.
- Kept documentation reference-focused; examples and broader guidance remain Phase 32 work.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - no unresolved implementation or environment issues remain.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 29-04 can close structural, pure/native, performance, restoration, and full-suite evidence on an explicit lifecycle and documentation contract.

## Self-Check: PASSED

- Summary, central oracle, lifecycle suite, logging suite, and both API pages exist.
- Task commit `368f6e8` exists in repository history.
- Focused lifecycle/logging tests, the Phase 29 adjacent regression suite, Ruff, and warnings-as-errors Sphinx build passed.

---
*Phase: 29-expected-domain-rejection*
*Completed: 2026-09-17*
