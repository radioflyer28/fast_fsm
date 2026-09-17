---
phase: 28-same-state-transition-modes
plan: 02
subsystem: fsm-runtime
tags: [python, fsm, internal-transition, lifecycle, timing, priority, failure]
requires:
  - phase: 28-01
    provides: immutable selected-entry mode metadata and the synchronous internal lifecycle seam
provides:
  - Deterministic synchronous lifecycle and residency evidence for external and internal self-transitions
  - Mode-neutral priority-selection and staged internal failure evidence
affects: [28-03, 29-expected-domain-rejection, 30-construction-and-persistence-parity, 32-docs-and-release]
actuals:
  tokens: 3142
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - Internal events retain transition-level work but suppress every state lifecycle family together.
    - A selected immutable entry alone determines lifecycle mode after ordinary priority selection.
key-files:
  created: []
  modified:
    - tests/test_transition_modes.py
    - tests/test_transition_timing.py
    - tests/test_priority_selection.py
key-decisions:
  - "Expand the Phase 01 lifecycle seam with deterministic local fake-clock and sentinel coverage instead of duplicating runtime branching."
  - "Keep MODE-06 incomplete until Plan 03 proves the async and cancellation half."
patterns-established:
  - "Use local sentinel state callbacks and FakeClock instances to prove suppressed surfaces and residency timing without sleeps."
  - "Assert selected-mode failure truth from result, history, state identity, suffix behavior, and exactly-one failure observer pass."
requirements-completed: [MODE-05]
coverage:
  - id: D1
    description: External self-transitions preserve complete re-entry while direct controls remain external-only.
    requirement: MODE-03
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py tests/test_transition_timing.py -x -q"
        status: pass
    human_judgment: false
  - id: D2
    description: Internal logical commits suppress all state lifecycle surfaces, retain transition surfaces, and preserve residency timing.
    requirement: MODE-05
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_transition_modes.py tests/test_transition_lifecycle.py tests/test_transition_timing.py -x -q"
        status: pass
    human_judgment: false
  - id: D3
    description: Synchronous mixed-mode priority and retained internal failure paths keep selected candidate, priority, commit, mode, history, and observer truth aligned.
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_transition_modes.py tests/test_priority_selection.py tests/test_transition_lifecycle.py tests/test_graph_invariants.py -x -q -k 'internal or external or priority or failure or lifecycle'"
        status: pass
    human_judgment: false
duration: 4min
completed: 2026-09-17
status: complete
---

# Phase 28 Plan 02: Synchronous Lifecycle, Timing, Priority, and Failure Summary

**External re-entry and internal logical commits now have deterministic synchronous evidence for callback ownership, timing, priority selection, and staged failure truth.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-17T00:43:44Z
- **Completed:** 2026-09-17T00:47:00Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Proved the full retained/suppressed lifecycle matrix, direct-control boundary, history-dependent clock reads, and external versus internal residency behavior without sleeps.
- Proved pre- and post-commit internal failures retain stage, priority, mode, history, suffix, and exactly-once observer truth.
- Proved priority remains mode-neutral until selection; only the selected immutable candidate controls whether state lifecycle work runs.

## Task Commits

1. **Task 1: Prove the complete lifecycle and residency matrix** — `9cfaf9d` (test)
2. **Task 2: Preserve selected-mode priority and staged failure truth** — `93abc08` (test)

## Files Created/Modified

- `tests/test_transition_modes.py` — retained/suppressed sync lifecycle, direct-control, and staged-failure oracle.
- `tests/test_transition_timing.py` — local fake-clock checks for event timestamps, entry epochs, and residency deadlines.
- `tests/test_priority_selection.py` — mixed external/internal candidate ordering, selected-mode, and terminal guard-failure coverage.

## Decisions Made

- The Plan 01 runtime seam already met the expanded Plan 02 contract; this plan adds the intended deterministic regression evidence without duplicating or widening runtime logic.
- MODE-05 is complete. MODE-06 remains pending until Plan 03 proves its async and cancellation requirements.

## Deviations from Plan

None - plan executed exactly as written. The prior Plan 01 implementation satisfied the new focused tests, so no additional runtime edit was necessary.

## Issues Encountered

- `task typecheck-ty` remains advisory and reports the existing relative-import diagnostic for `src/fast_fsm/core.py`; blocking mypy and the slots-policy audit passed.

## TDD Gate Compliance

- The planned behavior was already implemented by Plan 01's lifecycle seam. The expanded tests passed on their first valid run after correcting the declarative test fixture to use the library's actual declarative-state contract, so no separate RED/GREEN production commit was appropriate. The two task commits add the full regression oracle.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

Plan 03 can now focus exclusively on async lifecycle/cancellation ownership and pure/native validation. The synchronous lifecycle, timing, selection, and failure contract is locked by deterministic tests.

## Self-Check: PASSED

- All three modified test files exist and task commits `9cfaf9d` and `93abc08` are present in Git history.
- The task-level, wave-close, Ruff, blocking mypy, and slots-policy checks passed; advisory `ty` retains its pre-existing relative-import diagnostic.

---
*Phase: 28-same-state-transition-modes*
*Completed: 2026-09-17*
