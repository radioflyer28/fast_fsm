---
phase: 19-bounded-diagnostics-safe-output
plan: "04"
subsystem: diagnostics
tags: [validation, diagnostics, snapshot, budgets, ordered-schema, sparse-graph]
requires:
  - phase: 19-01
    provides: immutable scalar graph snapshots and bounded diagnostic ledgers
  - phase: 19-03
    provides: deterministic SCC, structural-depth, sparse, and dense adapters
provides:
  - ordered duplicate-safe batch and comparison result schemas
  - exact zero-comparison aggregate semantics with explicit undefined values
  - snapshot-backed structured validation reports with SCC, depth, sparse, and status metadata
affects: [19-06, 19-08, validation, public-api, release-verification]
actuals:
  tokens: 9219
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - positional records instead of display-name-keyed diagnostic aggregation
    - one captured snapshot and one shared ledger per validator input
    - sparse-first structural reports with JSON-ready scalar status conversion
key-files:
  created: []
  modified:
    - src/fast_fsm/validation.py
    - tests/test_diagnostic_contracts.py
    - tests/test_validation.py
    - .specify/memory/spr-validation.md
key-decisions:
  - "Comparison and batch identity is the zero-based input position; names remain display labels."
  - "Empty comparisons use None for undefined average and range rather than invented zero metrics."
  - "Structured reports combine declared-initial reachability, cyclic SCC membership, condensation depth, sparse rows, and one status ledger."
patterns-established:
  - "Public helper limit overrides are keyword-only and preserve positional FSM arguments."
  - "Legacy scalar, list, string, and printing boundaries complete analysis before returning or emitting output, so budget exhaustion fails closed."
requirements-completed: [DIAG-01, DIAG-02, DIAG-03, DIAG-04, DIAG-05, DIAG-06, DIAG-07, DIAG-08]
coverage:
  - id: D1
    description: Duplicate-name batch and comparison inputs retain ordered positional identity, stable ties, one snapshot per input, and exact empty comparison values.
    requirement: DIAG-02
    verification:
      - kind: integration
        ref: uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py -x -q -k 'compare or batch or duplicate or empty or snapshot'
        status: pass
    human_judgment: false
  - id: D2
    description: Snapshot-backed validation reports expose declared initial/current state separation, SCC membership, condensation depth, sparse rows, and deterministic completion counters.
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py tests/test_mypyc_guard.py -x -q -k 'report or status or exhaust or sparse or initial or snapshot or export'
        status: pass
    human_judgment: false
  - id: D3
    description: Full regression, formatting, type, and slots gates preserve public compatibility and slotted diagnostic types.
    requirement: DIAG-08
    verification:
      - kind: integration
        ref: uv run pytest tests/ -x -q
        status: pass
      - kind: other
        ref: FAST_FSM_BUILD_MODE=pure uv run mypy src/fast_fsm/; FAST_FSM_BUILD_MODE=pure uv run ty check src/fast_fsm/; uv run python tools/release_evidence.py slots-policy --json
        status: pass
    human_judgment: false
metrics:
  duration: 11min
  completed: 2026-09-04
  tasks: 2
  files: 4
status: complete
---

# Phase 19 Plan 04: Position-Safe Validation Diagnostics Summary

**Duplicate-safe comparison and batch schemas now preserve input position, while snapshot-backed validation reports publish bounded SCC, depth, sparse, and completion status.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-04T00:12:13Z
- **Completed:** 2026-09-04T00:23:13Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Replaced name-keyed comparison and batch accumulation with ordered positional records, stable score ties, and an unambiguous `{position, name}` winner.
- Defined the exact zero-machine comparison response: empty entries/rankings, no best machine, zero count/issues, and `None` average/range.
- Extended one-snapshot validation reports with declared-initial reachability, complete SCC membership, condensation depth interpretation, sparse adjacency, and aggregate completion counters.
- Added keyword-only limits across validation helpers, JSON-ready scalar status output, source guards against live topology reads, and same-commit SPR contracts.

## Task Commits

1. **Task 1 RED: position-safe comparison contracts** — `8881eac` (test)
2. **Task 1: Preserve duplicate inputs and define the zero-comparison schema** — `771308c` (feat)
3. **Task 2 RED: structured validation status contracts** — `d21bc46` (test)
4. **Task 2: Unify validator, score, report, and JSON-ready analysis status** — `e5db963` (feat)

## Files Created/Modified

- `src/fast_fsm/validation.py` — position-safe batch/comparison assembly, snapshot/ledger initialization, bounded structural adapters, report fields, helper limits, and JSON-safe status records.
- `tests/test_diagnostic_contracts.py` — duplicate/empty/tie/snapshot tests, structured report status coverage, exact aggregate-budget boundary, exports, and live-topology source guards.
- `tests/test_validation.py` — legacy expectation migrations for ordered result schemas and structured report/status assertions.
- `.specify/memory/spr-validation.md` — published batch/comparison identity, zero-result, report/status, sparse/dense, and fail-closed contracts.

## Decisions Made

- Use position as the only result identity across multi-FSM operations; labels never index a public diagnostic map.
- Aggregate per-input diagnostic statuses deterministically, preserving the first exhausted boundary and summed counters without recapturing a graph.
- Keep `DiagnosticStatus` as the structured Python contract while converting it to scalar fields inside JSON export paths.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test contract] Removed an incidental tied-score value from the duplicate-name test**
- **Found during:** Task 1
- **Issue:** The duplicate fixture correctly proves tie ordering, but its one-state/no-event score is `0`, not the test's unrelated expected `66.7`.
- **Fix:** Asserted equal tied scores and ascending positional order instead of coupling the identity contract to a scoring heuristic.
- **Files modified:** `tests/test_diagnostic_contracts.py`
- **Verification:** Focused comparison/batch tests and the full suite passed.
- **Committed in:** `771308c`

**Total deviations:** 1 auto-fixed (1 Rule 1).

## Issues Encountered

- The sandbox blocks the shared `uv` cache by default; approved runs used the existing project environment for all required checks.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 19-06 can document these finalized positional schemas, structural report fields, limits, and export boundaries.
- Plan 19-08 can include the new validation behavior in the final isolated Phase 19 regression evidence.

## Self-Check: PASSED

- All four implementation, test, and SPR files plus this summary exist in the worktree.
- TDD RED/GREEN commits `8881eac`, `771308c`, `d21bc46`, and `e5db963` exist in history.

---
*Phase: 19-bounded-diagnostics-safe-output*
*Completed: 2026-09-04*
