---
phase: 31-semantic-diagnostics-visualization
plan: 01
subsystem: diagnostics
tags: [snapshot, json, final-state, transition-mode, budget]
requires:
  - phase: 27-explicit-final-states
    provides: immutable explicit State.final metadata
  - phase: 28-same-state-transition-modes
    provides: internal transition selection metadata
provides:
  - single-capture scalar finality and edge mode projection
  - additive, bounded diagnostic JSON completion and mode fields
affects: [31-02, 31-03, 31-05]
actuals:
  tokens: 2700
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [capture canonical scalar facts once, reserve before diagnostic output]
key-files:
  created: []
  modified: [src/fast_fsm/core.py, src/fast_fsm/core.pyi, src/fast_fsm/_diagnostics.py, src/fast_fsm/visualization.py, tests/test_diagnostic_contracts.py]
key-decisions:
  - "Carry final flags parallel to snapshot state names and internal mode on diagnostic edges; do not recalculate from live topology."
  - "Keep topology-only terminal semantics while adding final_states and non_final_sinks."
patterns-established:
  - "JSON semantic additions use one captured graph and one reserve-before-output budget ledger."
requirements-completed: [DIAG-01, DIAG-03]
coverage:
  - id: D1
    description: Explicit finals, non-final sinks, and internal/external transition modes are distinguished in public JSON.
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: tests/test_diagnostic_contracts.py#test_json_distinguishes_explicit_final_sink_and_transition_modes
        status: pass
    human_judgment: false
  - id: D2
    description: JSON semantic fields are single-capture, deterministic, and reject exact-limit budget overflow without partial output.
    requirement: DIAG-03
    verification:
      - kind: unit
        ref: tests/test_diagnostic_contracts.py#test_json_semantics_have_stable_order_and_exact_budget_boundaries
        status: pass
      - kind: integration
        ref: tests/test_diagnostic_contracts.py#test_json_semantics_use_one_capture_after_live_graph_mutation
        status: pass
    human_judgment: false
duration: 20min
completed: 2026-09-19
status: complete
---

# Phase 31 Plan 01: Semantic Snapshot and JSON Summary

**One immutable capture now carries explicit finality and transition mode into bounded, deterministic JSON without changing legacy topology meaning.**

## Performance

- **Duration:** approximately 20 minutes
- **Completed:** 2026-09-19T18:14:42Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added scalar final flags and internal mode to the shared diagnostic graph from one owned snapshot.
- Added `topology.final_states`, `analysis.reachability.non_final_sinks`, and per-transition `mode` while retaining the original `terminal` and adjacency contracts.
- Proved initial-only finals, late mutation isolation, stable serialization, and exact/one-less work and result budgets.

## Task Commits

The two tightly coupled tasks were committed together as `1bcbab5` after both focused tests passed.

## Verification

- `uv run pytest tests/test_diagnostic_contracts.py -x -q` — 33 passed.
- `uv run pytest tests/test_diagnostic_contracts.py tests/test_visualization.py tests/test_validation.py tests/test_output_safety.py -x -q` — passed.
- `task typecheck-mypy` and Ruff checks — passed after test formatting.
- `task typecheck-ty` — reports two unresolved imports in `core.py` (`._construction_compat`, `.conditions`); this is a nonblocking checker-resolution issue, not a changed import.

## Decisions Made

Preserved `terminal` as a topological no-outgoing list and emitted explicit completion separately. The `mode` field is directly readable for internal, external-self, and ordinary external edges.

## Deviations from Plan

The two task changes landed in one cohesive commit rather than separate task commits. Scope and verification were otherwise as planned.

## Issues Encountered

The sandbox cannot initialize the standard uv cache for type and Ruff tools, so those checks used approved escalated execution. The secondary `ty` checker still reports unresolved imports and is documented above.

## User Setup Required

None.

## Next Phase Readiness

The scalar graph is ready for validator and diagram projections in Plans 31-02 and 31-03. Shared DIAG requirements must remain open until all declaring plans complete.

---
*Phase: 31-semantic-diagnostics-visualization*
*Completed: 2026-09-19*
