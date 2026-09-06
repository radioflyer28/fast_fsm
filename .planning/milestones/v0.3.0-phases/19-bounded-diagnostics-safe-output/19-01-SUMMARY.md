---
phase: 19-bounded-diagnostics-safe-output
plan: "01"
subsystem: diagnostics
tags: [diagnostics, validation, graph-snapshot, budgets, mypyc, slots]
requires:
  - phase: 18-safe-ownership-concurrency
    provides: ownership-safe core topology mutation and callback boundaries
provides:
  - one-capture scalar graph snapshots with declared-initial reachability
  - finite reserve-before-work diagnostic limits, status, and redacted exhaustion errors
  - strict-RED ownership matrix for remaining graph, comparison, and renderer contracts
affects: [19-03, 19-04, 19-06, validation, visualization]
actuals:
  tokens: 9056
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - interpreted tuple-backed diagnostics behind the compiled core snapshot seam
    - reserve-before-work budget ledger with scalar-only failure metadata
    - strict-XFAIL contract staging for later implementation owners
key-files:
  created:
    - src/fast_fsm/_diagnostics.py
    - tests/test_diagnostic_contracts.py
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/validation.py
    - src/fast_fsm/__init__.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Capture scalar labels under the core ownership boundary while retaining identity-bearing snapshot fields."
  - "Keep diagnostics interpreted and prohibit imports back into compiled core hot paths."
  - "Legacy reachability fails closed with a fixed-message budget exception rather than returning partial data."
  - "Expose only DiagnosticLimits, DiagnosticStatus, and DiagnosticBudgetExceeded at package root."
requirements-completed: [DIAG-01, DIAG-04, DIAG-05, DIAG-06, DIAG-07, DIAG-08]
coverage:
  - id: D1
    description: "Declared-initial, one-snapshot reachability with exact redacted work exhaustion"
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: "tests/test_diagnostic_contracts.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Strict-RED matrix assigning remaining diagnostic/output contracts to one later owner"
    requirement: DIAG-07
    verification:
      - kind: unit
        ref: "tests/test_diagnostic_contracts.py"
        status: pass
    human_judgment: false
duration: 11min
completed: 2026-09-02
status: complete
---

# Phase 19 Plan 01: Bounded Diagnostics Tracer Summary

**A one-capture declared-initial reachability tracer with finite deterministic budgets, scalar snapshot labels, and strict future diagnostic contracts.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-02T23:00:47Z
- **Completed:** 2026-09-02T23:11:20Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Captured immutable scalar state and condition labels inside the core ownership boundary without importing diagnostics into compiled `core.py`.
- Added tuple-backed interpreted diagnostics, explicit finite limits/status, and a fixed redacted budget-exhaustion boundary for legacy reachability.
- Added root exports and a real-machine strict-XFAIL matrix for the next graph, report, and renderer implementations.

## Task Commits

1. **Task 1 RED: diagnostic tracer contracts** — `337f4ce` (test)
2. **Task 1: snapshot-backed diagnostic tracer** — `37a9b8a` (feat)
3. **Task 2: diagnostic strict-RED matrix** — `c9f2b6c` (test)

## Files Created/Modified

- `src/fast_fsm/_diagnostics.py` — private scalar graph projection and shared deterministic budget ledger.
- `src/fast_fsm/core.py` — ownership-synchronized snapshot capture plus scalar snapshot fields.
- `src/fast_fsm/validation.py` — single-capture validator reachability adapter.
- `tests/test_diagnostic_contracts.py` — tracer contracts, fixture inventory, hash-seed proof, and strict-RED rows.
- `src/fast_fsm/__init__.py` — three intentional diagnostic root exports.
- `.specify/memory/spr-core-api.md` — current snapshot, budget, import-boundary, and export contract.
- `tools/release_evidence.py` and `tests/test_release_evidence.py` — registered-exception slots-policy evidence for the public status-carrying error.
- `tests/test_mypyc_guard.py` — additive compiled snapshot-field structural guard.

## Decisions Made

- Snapshot labels are copied as strings under the ownership read boundary, while Phase 16 identity fields remain available.
- `FSMValidator` owns one captured graph and one budget ledger; it does not reread live topology for reachability.
- Future SCC/depth, sparse/dense/path, comparison/report, and JSON contracts remain strict RED until their designated implementation plans.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Registered the public budget exception with the slots-policy audit**
- **Found during:** Task 1
- **Issue:** Python exception subclasses retain an instance dictionary even with `__slots__`; the mandatory slots audit rejected `DiagnosticBudgetExceeded`.
- **Fix:** Added its reviewed registry entry, runtime representative, and regression expectation.
- **Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`
- **Verification:** `uv run python tools/release_evidence.py slots-policy --json`
- **Committed in:** `37a9b8a`

**2. [Rule 3 - Blocking] Updated the compiled snapshot structural guard additively**
- **Found during:** Task 2
- **Issue:** The mypyc guard required the old exact field sets and rejected the plan-mandated scalar additions.
- **Fix:** Extended the frozen-slot field assertions for both graph records.
- **Files modified:** `tests/test_mypyc_guard.py`
- **Verification:** `uv run pytest tests/test_mypyc_guard.py -x -q`
- **Committed in:** `c9f2b6c`

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 3).

## Known Stubs

The following private helpers deliberately remain strict-RED seams for Plan 19-03; their callers are covered by strict XFAIL tests and they are not exposed at package root.

| File | Line | Stub | Resolution owner |
|---|---:|---|---|
| `src/fast_fsm/_diagnostics.py` | 212 | `_strongly_connected_components()` | Plan 19-03 |
| `src/fast_fsm/_diagnostics.py` | 217 | `_structural_depth()` | Plan 19-03 |
| `src/fast_fsm/_diagnostics.py` | 222 | `_sparse_adjacency()` | Plan 19-03 |
| `src/fast_fsm/_diagnostics.py` | 227 | `_dense_adjacency()` | Plan 19-03 |
| `src/fast_fsm/_diagnostics.py` | 232 | `_generate_paths()` | Plan 19-03 |

## Issues Encountered

The isolated pure-tree verifier initially lacked a locked development dependency in the sandbox cache; after the approved locked download, the required isolated verification passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 19-03 can remove only its strict XFAIL rows and implement SCC, structural-depth, sparse/dense, and bounded-path behavior against the shared graph/budget seam. Plans 19-04 and 19-06 retain their owned strict-XFAIL rows.

## Self-Check: PASSED

- Created tracer, contract-test, and summary files exist.
- TDD RED, tracer, and strict-RED matrix commits (`337f4ce`, `37a9b8a`, `c9f2b6c`) exist in history.
