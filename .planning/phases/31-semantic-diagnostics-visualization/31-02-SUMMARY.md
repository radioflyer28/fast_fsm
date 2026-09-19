---
phase: 31-semantic-diagnostics-visualization
plan: 02
subsystem: validation
tags: [final-state, dead-state, scoring, diagnostic-budget]
requires:
  - phase: 31-semantic-diagnostics-visualization
    provides: Plan 31-01 scalar final flags in the captured diagnostic graph
provides:
  - additive final-state and non-final-sink validation reports
  - final-aware enhanced findings and quality scores
  - documented topology-versus-completion distinction
affects: [31-05, phase-32]
actuals:
  tokens: 4200
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [classify findings from captured final flags, preserve legacy dead-state meaning]
key-files:
  created: []
  modified: [src/fast_fsm/validation.py, tests/test_validation.py, docs/api/validation.md, .specify/memory/spr-validation.md]
key-decisions:
  - "Keep dead_states, has_dead_states, missing_transitions, and is_complete topological; add separately named final_states and non_final_sinks."
  - "Exempt finals from missing-exit and no-return issues, but retain genuine unreachable-state findings."
patterns-established:
  - "Validation outputs and scores consume copied graph flags and the shared diagnostic budget."
requirements-completed: [DIAG-01, DIAG-03]
coverage:
  - id: D1
    description: Validation reports and exports distinguish explicit finals from topological sinks while retaining legacy dead-state fields.
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: tests/test_validation.py#test_completeness_report_separates_finals_from_topological_dead_states
        status: pass
      - kind: unit
        ref: tests/test_validation.py#test_completeness_final_flags_are_captured_and_exactly_budgeted
        status: pass
    human_judgment: false
  - id: D2
    description: Enhanced findings and dense blended scores do not penalize an intentional final merely for lacking exits.
    requirement: DIAG-01
    verification:
      - kind: unit
        ref: tests/test_validation.py#test_initial_final_has_no_missing_exit_issue_or_score_penalty
        status: pass
      - kind: integration
        ref: tests/test_validation.py#test_final_destination_avoids_sink_and_return_findings
        status: pass
    human_judgment: false
  - id: D3
    description: New validation scans and emitted final/sink lists respect the shared work and result budgets.
    requirement: DIAG-03
    verification:
      - kind: unit
        ref: tests/test_validation.py#test_completeness_final_flags_are_captured_and_exactly_budgeted
        status: pass
    human_judgment: false
duration: 15min
completed: 2026-09-19
status: complete
---

# Phase 31 Plan 02: Final-Aware Validation Summary

**Validation now identifies intentional completion without calling it a design defect, while preserving the old topological dead-state contract.**

## Performance

- **Duration:** approximately 15 minutes
- **Completed:** 2026-09-19T18:20:09Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added ordered `final_states` and `non_final_sinks` to completeness and enhanced export views; legacy dead-state fields still describe no-outgoing topology.
- Suppressed only final-specific dead-end, no-event, missing-transition, and no-return findings. Unreachable finals remain reported.
- Covered initial-only final, final versus non-final destination, immutable capture, exact budget limits, and score/export behavior; updated public and maintainer docs.

## Task Commits

The two related tasks were committed together as `e8d4edb` after both focused tests passed.

## Verification

- `uv run pytest tests/test_validation.py tests/test_diagnostic_contracts.py -x -q --disable-warnings` — passed.
- `uv run ruff check src/fast_fsm/validation.py tests/test_validation.py` — passed.
- `task typecheck-mypy` — passed.

## Decisions Made

New list fields are snapshot ordered; old set and boolean fields are unchanged. The enhanced validator uses copied final flags for issue classification, not a live machine read.

## Deviations from Plan

The two task changes landed in one cohesive commit rather than separate task commits. No scope expansion.

## Issues Encountered

The normal uv cache was intermittently inaccessible within the workspace sandbox; checks used approved escalated execution without changing project configuration.

## User Setup Required

None.

## Next Phase Readiness

The diagnostic graph and validator are ready for Plan 31-03 diagrams and Plan 31-04 trace work. Shared DIAG requirements remain open until all declaring plans finish.

---
*Phase: 31-semantic-diagnostics-visualization*
*Completed: 2026-09-19*
