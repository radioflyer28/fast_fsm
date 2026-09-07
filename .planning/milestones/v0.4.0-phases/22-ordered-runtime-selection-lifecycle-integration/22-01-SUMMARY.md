---
phase: 22-ordered-runtime-selection-lifecycle-integration
plan: 01
subsystem: core-transition-selection
tags: [python, mypyc, fsm, priority, guarded-transitions, lifecycle]
requires:
  - phase: 21-priority-contract-atomic-registration
    provides: Direct singleton entries and frozen ascending-priority candidate groups.
provides:
  - Deterministic synchronous selection of one fully eligible priority candidate before lifecycle work.
  - Distinct group-rejection, terminal-exception, selection-exhaustion, and observer-free query behavior.
affects: [phase-22-02-async-selection, phase-22-03-runtime-metadata, phase-23-construction-parity]
actuals:
  tokens: 10950
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - Direct singleton dispatch with local immutable-group scanning only when competing candidates exist.
    - Prepared winner handoff captures source identity, sanitized guard context, and target-specific declarative metadata before lifecycle execution.
key-files:
  created:
    - tests/test_priority_selection.py
  modified:
    - src/fast_fsm/core.py
    - tests/test_graph_invariants.py
    - tests/test_transition_lifecycle.py
key-decisions:
  - "Synchronous candidate selection uses one direct singleton branch or a local frozen-group scan, and sends only a fully eligible prepared winner into lifecycle execution."
  - "Normal rejections are local group-scan control; exceptions are terminal and exhausted groups return one fixed, redacted selection-stage result."
patterns-established:
  - "The selected entry carries source state, caller-safe guard context, and exact declarative handler as a slotted private handoff."
  - "Projection consumers retain _require_singleton_entry() fail-closed behavior while runtime dispatch handles groups."
requirements-completed: [SEL-01, SEL-03, SEL-04]
coverage:
  - id: D1
    description: Synchronous grouped dispatch resolves the first fully eligible stored-priority candidate before one existing lifecycle.
    requirement: SEL-01
    verification:
      - kind: integration
        ref: tests/test_priority_selection.py#test_sync_group_selects_the_first_fully_eligible_candidate_before_lifecycle
        status: pass
    human_judgment: false
  - id: D2
    description: Rejection, exception, exhaustion, lifecycle-failure, and query boundaries remain distinct and truthful.
    requirement: SEL-03
    verification:
      - kind: integration
        ref: "FAST_FSM_BUILD_MODE=pure uv run --offline pytest tests/test_priority_selection.py tests/test_graph_invariants.py tests/test_transition_lifecycle.py tests/test_async.py -x -q"
        status: pass
    human_judgment: false
  - id: D3
    description: Exhausted groups notify failure observers once while grouped runtime support does not unlock projections.
    requirement: SEL-04
    verification:
      - kind: unit
        ref: tests/test_priority_selection.py#test_sync_group_exhaustion_is_one_redacted_selection_failure
        status: pass
    human_judgment: false
duration: 6m
completed: 2026-09-07
status: complete
---

# Phase 22 Plan 01: Ordered Synchronous Selection Summary

**Synchronous priority groups now select the first fully eligible candidate before a single existing lifecycle, while query, failure, and projection boundaries remain explicit.**

## Performance

- **Duration:** 6m
- **Started:** 2026-09-07T00:40:12Z
- **Completed:** 2026-09-07T00:46:11Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added a direct singleton branch and ascending immutable-group scan that evaluates transition guard, target-specific declarative guard, and captured-source permission before lifecycle callbacks.
- Captured the winning entry, source state, sanitized guard mapping, and exact declarative handler in one frozen prepared dispatch passed once into the existing lifecycle.
- Added redacted selection exhaustion, terminal eligibility-exception, observer-free `can_trigger()`, lifecycle non-retry, and fail-closed projection coverage.

## Task Commits

1. **Task 1: Trace one ordered synchronous winner through one lifecycle** - `45fb0c7` (`feat`)
2. **Task 2: Close synchronous rejection, exception, exhaustion, and query boundaries** - `25717fe` (`feat`)

## Files Created/Modified

- `src/fast_fsm/core.py` - Selects sync singleton/group candidates and invokes the existing lifecycle once for the prepared winner.
- `tests/test_priority_selection.py` - Exercises ordered guards, target-specific declarative behavior, exhaustion, exceptions, query semantics, and lifecycle non-retry.
- `tests/test_graph_invariants.py` - Confirms runtime group selection works without relaxing the later Phase 23 projection guard.
- `tests/test_transition_lifecycle.py` - Adds `selection` to the stable lifecycle catalog and proves selection precedes lifecycle work.

## Decisions Made

- Kept singleton lookup and dispatch direct; only a real `_TransitionGroup` scans its already sorted local tuple.
- Kept normal false results private to group scanning; only terminal failure, exhaustion, and lifecycle results cross the existing failure-finalization seam.
- Preserved async grouped dispatch as Phase 22 Plan 02 work and projection/public topology support as later-phase work.

## Deviations from Plan

None - plan scope and behavior executed as specified.

## TDD Gate Compliance

Focused tests were written and observed failing before implementation, then passed after the implementation. The red tests were not committed separately before the two feature commits, so the Git history does not contain the ideal standalone `test(22-01)` RED commit; this is a process-record gap only.

## Issues Encountered

- Beads' local Dolt server was unavailable during both commits; its pre-commit export warning did not prevent the scoped Git commits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 22 Plan 02 can mirror this prepared-winner boundary through sequential async awaiting and cancellation finalization.
- Runtime metadata, trace/history propagation, compiled structure checks, and broader performance evidence remain deliberately scoped to Phase 22 Plan 03.

## Self-Check: PASSED

- The summary, four scoped implementation/test files, and both task commits resolve on disk and in Git history.
