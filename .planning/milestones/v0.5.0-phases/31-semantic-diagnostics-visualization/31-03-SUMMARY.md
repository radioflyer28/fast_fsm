---
phase: 31-semantic-diagnostics-visualization
plan: 03
subsystem: visualization
tags: [mermaid, plantuml, final-state, self-transition, escaping, budget]
requires:
  - phase: 31-semantic-diagnostics-visualization
    provides: Plan 31-01 copied final flags and internal edge mode
provides:
  - final-aware Mermaid and PlantUML completion markers
  - distinct internal and external self-edge labels
  - hostile-text and exact-budget renderer evidence
affects: [31-05, phase-32]
actuals:
  tokens: 3600
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [opaque positional diagram IDs, reserve marker visits and physical lines before append]
key-files:
  created: []
  modified: [src/fast_fsm/visualization.py, tests/test_visualization.py, tests/test_output_safety.py, docs/api/visualization.md, .specify/memory/spr-visualization.md]
key-decisions:
  - "Draw completion arrows only from copied explicit final flags, never from no-outgoing topology."
  - "Place fixed self-mode wording before the existing priority label; preserve ordinary external edge notation."
patterns-established:
  - "A single captured scalar graph and one budget drive raw and composed diagrams."
requirements-completed: [DIAG-02, DIAG-03]
coverage:
  - id: D1
    description: Both diagram languages mark only explicit finals, including initial-only final, and distinguish self-transition modes.
    requirement: DIAG-02
    verification:
      - kind: integration
        ref: tests/test_visualization.py#test_diagram_marks_only_explicit_finals_and_labels_self_modes
        status: pass
      - kind: unit
        ref: tests/test_visualization.py#test_initial_only_final_has_start_and_completion_markers
        status: pass
    human_judgment: false
  - id: D2
    description: Marker and label output stays inert under hostile caller text and uses exact reserve-before-output work/result limits.
    requirement: DIAG-03
    verification:
      - kind: unit
        ref: tests/test_output_safety.py#test_final_markers_and_self_modes_keep_hostile_text_inert
        status: pass
      - kind: unit
        ref: tests/test_output_safety.py#test_explicit_final_rows_have_exact_result_budget
        status: pass
      - kind: unit
        ref: tests/test_output_safety.py#test_explicit_final_marker_visit_has_exact_work_budget
        status: pass
    human_judgment: false
duration: 10min
completed: 2026-09-19
status: complete
---

# Phase 31 Plan 03: Semantic Diagram Summary

**Mermaid and PlantUML now expose declared completion and self-transition intent through safe, deterministic, bounded diagrams.**

## Performance

- **Duration:** approximately 10 minutes
- **Completed:** 2026-09-19T18:23:59Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Removed PlantUML's no-outgoing completion inference; both renderers now use explicit final flags from one graph capture.
- Added fixed internal/external-self labels while retaining escaped trigger, optional guard name, and priority.
- Verified hostile text containment and exact/one-less limits for raw Mermaid, PlantUML, fenced Mermaid, and Markdown document rendering; updated reference and maintainer docs.

## Task Commits

The two related tasks were committed together as `b3f0e51` after the focused renderer suite passed.

## Verification

- `uv run pytest tests/test_visualization.py tests/test_output_safety.py -x -q --disable-warnings` — passed.
- Ruff check and `task typecheck-mypy` — passed.

## Decisions Made

Completion markers use only copied explicit final flags. Ordinary non-self external labels are unchanged; self mode is appended before the priority bracket.

## Deviations from Plan

The two tasks landed in one cohesive commit rather than separate task commits. No scope expansion.

## Issues Encountered

None beyond the previously noted sandbox uv-cache restriction; approved escalated checks used the normal project environment.

## User Setup Required

None.

## Next Phase Readiness

The diagrams are ready for cross-surface closure in Plan 31-05. Plan 31-04 still owns trace semantics.

---
*Phase: 31-semantic-diagnostics-visualization*
*Completed: 2026-09-19*
