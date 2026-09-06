---
phase: 21-priority-contract-atomic-registration
plan: 02
subsystem: core-transition-topology
tags: [python, mypyc, transition-priority, atomic-registration, clone-ownership]
requires:
  - phase: 21-01
    provides: singleton-or-group priority slots, exact-int normalization, and staged slot commits
provides:
  - Atomic priority transport through batch, bidirectional, emergency, and builder registration
  - Owner-aware clone capture with independent mutable topology tables
  - Native exact-int rollback and singleton direct-lookup regression coverage
affects: [phase-22-runtime-selection, phase-23-construction-parity, phase-25-performance-proof]
actuals:
  tokens: 4516
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Complete helper fan-out is normalized before a single transition-plan publication.
    - Clone capture shares immutable slots while copying mutable registries under the graph read boundary.
key-files:
  created:
    - .planning/phases/21-priority-contract-atomic-registration/21-02-SUMMARY.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_graph_invariants.py
    - tests/test_builder.py
    - tests/test_ownership_concurrency.py
    - tests/test_mypyc_guard.py
    - tests/test_performance_benchmarks.py
key-decisions:
  - "Builder materializes all staged priority rows through one existing add_transitions batch."
  - "Clone captures topology through the owner-aware read boundary while sharing only immutable slots."
patterns-established:
  - "Five-field helper rows retain legacy three- and four-field compatibility while validating priority before publication."
  - "Native priority validation stays object-typed at the API boundary and explicit at the storage union."
requirements-completed: [PRIO-01, PRIO-02, PRIO-03]
coverage:
  - id: D1
    description: Atomic priority fan-out through helpers, builders, and owner-safe clones.
    requirement: PRIO-03
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_ownership_concurrency.py -k 'priority or candidate or atomic or clone or builder' -x -q"
        status: pass
    human_judgment: false
  - id: D2
    description: Explicit singleton-or-group typing, native exact-int rejection, and direct singleton lookup proof.
    requirement: PRIO-02
    verification:
      - kind: unit
        ref: "FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_mypyc_guard.py tests/test_performance_benchmarks.py -k 'priority or transition_entry or candidate_group or constant_lookup' -x -q"
        status: pass
      - kind: other
        ref: "FAST_FSM_BUILD_MODE=compiled task build-check"
        status: pass
    human_judgment: false
duration: 48m
completed: 2026-09-06
status: complete
---

# Phase 21 Plan 02: Priority Helper, Builder, Clone, and Native Proof Summary

**Priority-aware registration now reaches every scoped fan-out path atomically, while cloned machines capture one coherent topology and native singleton dispatch retains its direct fast path.**

## Performance

- **Duration:** 48m
- **Started:** 2026-09-06T21:52:24Z
- **Completed:** 2026-09-06T22:40:31Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added five-field batch rows and keyword-only priority transport for bidirectional and emergency helpers without changing their winner semantics.
- Made `FSMBuilder` validate and retain priority during staging, then publish its complete local topology through one batch commit only after success.
- Made clone capture wait behind active topology writers, while preserving immutable entry/group sharing and separate mutable mappings and ownership primitives.
- Added AST, compiled-native, counted lookup, throughput, rollback, repair, and thread-contention coverage for the priority storage contract.

## Task Commits

1. **Task 1 RED: priority helper, builder, and clone coverage** - `a261269` (`test`)
2. **Task 1 GREEN: helper/builder transport and owner-aware clone capture** - `ffa671e` (`feat`)
3. **Task 2: native priority and singleton guards** - `e9ad038` (`test`)
4. **Task 2 correction: typed five-field batch boundary** - `776a6bb` (`fix`)

## Files Created/Modified

- `src/fast_fsm/core.py` - Transports priorities through all scoped registration paths, batches builder materialization, and captures clones safely.
- `tests/test_graph_invariants.py` - Covers helper fan-out priority, rollback, and graph-version semantics.
- `tests/test_builder.py` - Covers priority staging, one-commit materialization, and repairable builder failure.
- `tests/test_ownership_concurrency.py` - Proves clone capture serializes with a topology writer and copies mutable tables.
- `tests/test_mypyc_guard.py` - Guards explicit slot-union typing and native exact-int rollback.
- `tests/test_performance_benchmarks.py` - Proves priority-0 singleton dispatch retains direct constant lookup.

## Decisions Made

- Reused the existing batch registrar for builder materialization, so priority fan-out has one atomic publication model.
- Used the same owner-aware read boundary as graph snapshots for cloning, preserving reentrant owned callers without exposing torn topology.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored strict mypy compatibility for widened five-field rows**
- **Found during:** Task 2: Prove the typed compiled boundary and singleton fast path
- **Issue:** Adding the priority field caused the batch guard position and builder local-row collection to widen beyond their declared types.
- **Fix:** Narrowed the batch guard before normalization and declared the complete builder batch-row union explicitly.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `task typecheck-mypy`, `task typecheck-ty`, slots audit, pure suite, and native targeted suite passed.
- **Committed in:** `776a6bb`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Required for the declared mypyc boundary; no behavior or scope expansion.

## Issues Encountered

- The generated in-place native extensions were removed after the compiled checks so the final source-origin preflight and pure test suite loaded `core.py`, not a native shadow.
- Beads' local Dolt server was unavailable; its pre-commit export warning did not prevent any Git commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 22 can add ordered candidate selection to the frozen storage representation without changing registration topology.
- Existing grouped dispatch remains intentionally fail-closed until that selection phase.

## Self-Check: PASSED

- All six scoped source/test files exist and their four task commits resolve in Git history.

## PLAN COMPLETE
