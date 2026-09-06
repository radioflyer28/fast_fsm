---
phase: 19-bounded-diagnostics-safe-output
plan: "03"
subsystem: diagnostics
tags: [diagnostics, graph-algorithms, scc, sparse, dense, bounded-paths]
requires:
  - phase: 19-01
    provides: immutable diagnostic graph snapshots and reserve-before-work ledgers
provides:
  - deterministic iterative SCC membership and condensation-DAG structural depth
  - sparse-first validation reports with preflighted dense compatibility adapters
  - iterative path generation with independent length, result, and expansion bounds
affects: [19-04, 19-06, validation, visualization, release-verification]
actuals:
  tokens: 35691
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - iterative Kosaraju over immutable snapshot-indexed adjacency
    - reserve-before-allocation dense preflight
    - explicit iterative DFS frames for bounded path enumeration
key-files:
  created: []
  modified:
    - src/fast_fsm/_diagnostics.py
    - src/fast_fsm/validation.py
    - tests/test_diagnostic_contracts.py
    - tests/test_validation.py
    - .specify/memory/spr-validation.md
key-decisions:
  - "Cyclic membership is the canonical SCC result; legacy find_cycles derives deterministic closed representatives from it."
  - "Cyclic depth is the longest edge depth of the condensation DAG, never a longest-simple-path claim inside an SCC."
  - "Sparse rows are the default report shape; dense V×events and V² forms are explicit compatibility outputs preflighted before outer allocation."
  - "max_length and max_paths remain requested path caps while any diagnostic budget exhaustion raises the redacted exception."
patterns-established:
  - "Graph diagnostics use snapshot order, not hash/set iteration, for externally visible order and exact counters."
  - "Legacy list/dict/scalar APIs do not return a partial value when a shared diagnostic budget is exhausted."
requirements-completed: [DIAG-04, DIAG-05, DIAG-06, DIAG-07, DIAG-08]
coverage:
  - id: D1
    description: Deterministic cyclic SCC membership, self-loop handling, and iterative DAG/condensation structural depth.
    requirement: DIAG-04
    verification:
      - kind: unit
        ref: uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py -x -q -k 'cycle or scc or depth or longest or budget'
        status: pass
    human_judgment: false
  - id: D2
    description: Sparse-first graph rows, exact dense-cell preflight, and bounded iterative path generation.
    requirement: DIAG-06
    verification:
      - kind: unit
        ref: uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py -x -q -k 'sparse or dense or matrix or path or budget'
        status: pass
    human_judgment: false
  - id: D3
    description: Shared diagnostic status, finite calibrated defaults, and redacted budget-exhaustion behavior across adapters.
    requirement: DIAG-07
    verification:
      - kind: integration
        ref: uv run pytest tests/ -x -q
        status: pass
    human_judgment: false
metrics:
  duration: 15 min
  completed: 2026-09-03
  tasks: 2
  files: 5
status: complete
---

# Phase 19 Plan 03: Bounded Graph Diagnostics Summary

**Iterative SCC and condensation-depth analysis with sparse-first validation, dense allocation preflight, and deterministic bounded path enumeration.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-03T23:31:00Z
- **Completed:** 2026-09-03T23:45:39Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Replaced recursive cycle and longest-path traversal with snapshot-ordered iterative SCC and condensation-DAG algorithms.
- Made sparse state/event/edge rows the normal validation output while retaining preflighted dense matrix compatibility adapters.
- Replaced recursive test-path generation with iterative frames that independently charge path expansion, work, and result budgets.
- Pinned finite diagnostic defaults and documented exact exhaustion and compatibility semantics in the validation SPR.

## Task Commits

1. **Task 1 RED: SCC and structural-depth contracts** — `129f254` (test)
2. **Task 1: Report complete cyclic membership and condensation structural depth** — `9abf284` (feat)
3. **Task 2 RED: sparse, dense, and path contracts** — `e45044c` (test)
4. **Task 2: Make sparse output default and bound dense allocation and path expansion** — `d069e4e` (feat)

## Files Created/Modified

- `src/fast_fsm/_diagnostics.py` — iterative graph primitives, shared counters, sparse rows, dense preflight, and bounded path frames.
- `src/fast_fsm/validation.py` — snapshot-backed public sparse/dense/path, cycle, depth, and report adapters.
- `tests/test_diagnostic_contracts.py` — exact SCC, depth, matrix allocation, path-budget, and default-limit contracts.
- `tests/test_validation.py` — public sparse-report and cyclic-depth compatibility coverage.
- `.specify/memory/spr-validation.md` — shipped SCC/depth/sparse/dense/path/default-budget contract.

## Decisions Made

- SCC membership remains the canonical cycle fact; the legacy list-shaped `find_cycles()` output is a deterministic compatibility representation.
- A cyclic machine's depth is explicitly `condensation_dag_depth`, rather than an unsafe or exponential search for a simple longest path.
- Dense compatibility output spends its complete V×events or V² cell budget before it can allocate the outer structure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Resolved new mypy inference conflicts in graph helper locals**
- **Found during:** Task 2
- **Issue:** Reusing differently typed iterative-stack and dense-matrix locals caused the mandatory mypy compatibility gate to fail.
- **Fix:** Split the reverse traversal stack and dense branch locals into accurately typed variables without changing runtime semantics.
- **Files modified:** `src/fast_fsm/_diagnostics.py`
- **Verification:** `task typecheck-mypy`
- **Committed in:** `d069e4e`

**Total deviations:** 1 auto-fixed (1 Rule 3).

## Known Stubs

None. All Plan 19-03 strict-RED markers were removed; later-plan strict-RED contracts remain owned by their assigned plans.

## Verification

- `uv run pytest tests/test_diagnostic_contracts.py tests/test_validation.py -x -q` — passed.
- `uv run pytest tests/ -x -q` — passed.
- `uv run ruff check src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py tests/test_diagnostic_contracts.py tests/test_validation.py` — passed.
- `task typecheck-mypy` and `task typecheck-ty` — passed.
- `uv run python tools/release_evidence.py slots-policy --json` — passed.
- Confirmed `core.py` is unchanged and does not import `_diagnostics`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plans 19-04 and 19-06 can use the shared deterministic graph and budget seam without recreating SCC, dense-allocation, or path traversal behavior.

## Self-Check: PASSED

- All five declared implementation, test, and SPR files exist.
- TDD RED/GREEN commits `129f254`, `9abf284`, `e45044c`, and `d069e4e` exist in history.

---
*Phase: 19-bounded-diagnostics-safe-output*
*Completed: 2026-09-03*
