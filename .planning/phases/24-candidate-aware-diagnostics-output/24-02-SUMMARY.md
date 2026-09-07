---
phase: 24-candidate-aware-diagnostics-output
plan: 02
subsystem: diagnostics and visualization
tags: [python, diagnostics, validation, visualization, priority, budgets]
requires:
  - phase: 24-candidate-aware-diagnostics-output
    provides: frozen candidate-complete diagnostic edges with scalar priority and guard metadata
  - phase: 23-construction-declarative-serialization-parity
    provides: immutable candidate-complete graph snapshots in canonical priority order
provides:
  - priority-bearing sparse and dense adjacency records, transition-matrix rows, and generated path steps
  - candidate-complete JSON, Mermaid, PlantUML, validation Markdown, and visualization Markdown output
  - exact candidate-level result reservations and priority-sensitive adjacency validation
affects: [24-03, 25-artifacts-performance-and-guidance, diagnostics, visualization]
actuals:
  tokens: 7166
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - preserve snapshot candidate order through shared scalar diagnostic adapters
    - reserve output capacity before each candidate representation is exposed
key-files:
  created:
    - .planning/phases/24-candidate-aware-diagnostics-output/24-02-SUMMARY.md
  modified:
    - src/fast_fsm/_diagnostics.py
    - src/fast_fsm/validation.py
    - src/fast_fsm/visualization.py
    - tests/test_diagnostic_contracts.py
    - tests/test_validation.py
    - tests/test_visualization.py
key-decisions:
  - "Transition-matrix cells deliberately evolve to ordered {to_state, priority} records so same-target candidates cannot collapse."
  - "Generated priority stays outside caller-text encoders while caller labels retain their existing final-sink escaping."
  - "Candidate rows reserve the existing shared ledger before output rather than introducing sink-local counters."
patterns-established:
  - "Diagnostic adapters carry one canonical numeric priority field across adjacency, paths, JSON, diagrams, and Markdown."
  - "Caller-provided dense matrices are exact only when every candidate index and priority matches the captured graph."
requirements-completed: [DIAG-02]
coverage:
  - id: D1
    description: "Sparse/dense adjacency, transition matrices, counts, and paths retain every same-target candidate in priority order."
    requirement: DIAG-02
    verification:
      - kind: integration
        ref: "tests/test_diagnostic_contracts.py::test_candidate_adapters_preserve_same_target_priority_and_path_identity"
        status: pass
      - kind: integration
        ref: "tests/test_validation.py::TestFSMValidator::test_candidate_transition_matrix_and_counts_keep_same_target_priorities"
        status: pass
    human_judgment: false
  - id: D2
    description: "JSON, Mermaid, PlantUML, and both Markdown formats emit escaped, priority-complete candidate records and reject stale priority matrices."
    requirement: DIAG-02
    verification:
      - kind: integration
        ref: "tests/test_visualization.py::TestPriorityCandidateOutput::test_all_visualization_sinks_keep_priority_and_escape_hostile_labels"
        status: pass
      - kind: integration
        ref: "tests/test_visualization.py::TestPriorityCandidateOutput::test_tampered_adjacency_priority_fails_the_fixed_contract"
        status: pass
      - kind: integration
        ref: "tests/test_validation.py::TestEnhancedFSMValidator::test_candidate_reports_keep_numeric_priority_in_json_and_markdown"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each JSON candidate record consumes a result reservation and one-less limits return the existing incomplete budget failure."
    requirement: DIAG-02
    verification:
      - kind: boundary
        ref: "tests/test_diagnostic_contracts.py::test_json_reserves_each_candidate_record_before_returning_output"
        status: pass
    human_judgment: false
duration: 1h 10m
completed: 2026-09-07
status: complete
---

# Phase 24 Plan 02: Candidate-Complete Diagnostics Summary

**Every diagnostic representation now exposes each finite transition candidate with its numeric priority, while preserving one-snapshot escaping and fail-explicit budget semantics.**

## Performance

- **Duration:** 1h 10m
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Evolved sparse/dense adjacency and transition-matrix records to carry priority without collapsing same-target candidate rows, and extended generated path steps with their fourth priority scalar.
- Made transition totals and enhanced validation metrics candidate-counted instead of deriving cardinality from target-name sets.
- Rendered candidate priority in JSON, Mermaid, PlantUML, and both Markdown report families; condition visibility only controls condition text.
- Tightened caller-supplied adjacency validation to reject priority tampering and reserved the existing shared ledger before candidate output records.

## Task Commits

1. **Task 1: Preserve candidate identity in adjacency and generated paths with exact accounting** — `ed60be8` (RED tests), `234c2fa` (implementation)
2. **Task 2: Render every candidate safely across JSON, diagrams, and Markdown** — `56edff3` (RED tests), `d25d341` (implementation)

## Files Created/Modified

- `src/fast_fsm/_diagnostics.py` — emits priority-bearing candidate adjacency records, matrix records, and path steps.
- `src/fast_fsm/validation.py` — reports candidate totals and renders priority in validation Markdown.
- `src/fast_fsm/visualization.py` — renders priority in JSON/diagrams/documents and validates exact matrix precedence.
- `tests/test_diagnostic_contracts.py` — proves same-target cardinality, priority paths, and result-budget boundaries.
- `tests/test_validation.py` — proves matrix/count and validation report candidate parity.
- `tests/test_visualization.py` — proves escaping, diagram/JSON/Markdown output, and stale-priority rejection.

## Decisions Made

- Dense transition-matrix cells are ordered candidate dictionaries with exactly `to_state` and `priority`; target strings could not faithfully represent same-target candidates.
- Priority is generated numeric metadata, not caller-controlled text, so only caller labels flow through grammar-specific encoders.
- Output work remains on the one existing diagnostic ledger; no renderer-specific budget type or partial-return mode was introduced.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test fixture correctness] Restored actual hostile newline input in renderer coverage.**
- **Found during:** Task 2 focused green run.
- **Issue:** The initial fixture contained the two literal characters `\\n`, testing backslash escaping rather than the newline injection boundary required by the plan.
- **Fix:** Used actual newline characters in the source, guard, title, and trigger fixture values.
- **Files modified:** `tests/test_visualization.py`, `tests/test_validation.py`
- **Verification:** Focused renderer/report tests and the full owned diagnostic suite passed.
- **Committed in:** `d25d341`

**Total deviations:** 1 Rule 1 test-correctness fix. The output contract, public API, and runtime selector scope remain unchanged.

## Issues Encountered

- The default user UV cache is inaccessible in this sandbox. All planned commands passed with the phase's offline cache at `/private/tmp/fast-fsm-phase23-uv-cache`.
- The local Beads Dolt service was unavailable during scoped commits. Git commits completed; no tracker or remote mutation was attempted.

## User Setup Required

None - no external service configuration required.

## Verification

- `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache task pure-source-check`: passed.
- Focused Plan 02 suites and the full owned diagnostic/validation/visualization suite in pure mode: passed.
- Ruff format/check, `task typecheck-mypy`, `task typecheck-ty`, and `tools/release_evidence.py slots-policy --json`: passed.

## Next Phase Readiness

Plan 24-03 can assert this priority-complete snapshot-to-output behavior against pure and freshly compiled core without changing the direct runtime selector. No integration blockers were found.

## Self-Check: PASSED

- Verified all six scoped source/test files and this summary exist.
- Verified task commits `ed60be8`, `234c2fa`, `56edff3`, and `d25d341` exist in local history.

---
*Phase: 24-candidate-aware-diagnostics-output*
*Completed: 2026-09-07*
