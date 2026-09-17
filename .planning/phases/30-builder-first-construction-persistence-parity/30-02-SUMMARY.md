---
phase: 30-builder-first-construction-persistence-parity
plan: 02
subsystem: core-construction
tags: [fsm-builder, declarative-state, batch-adapter, transition-mode, parity]
requires:
  - phase: 30-01
    provides: build-time declarative request derivation and the central parity tracer
provides:
  - Source-applicable declarative async preflight that cannot reject foreign metadata
  - Internal transition mode in batch, quick-build, and quick_fsm transition rows
  - Observable parity coverage across direct, batch, builder, declarative, and callback construction
affects: [30-03, 30-04, 30-06, construction-parity, helper-compatibility, persistence]
actuals:
  tokens: 5274
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Declarative preflight follows the exact state-owner applicability rule used by build-time derivation
    - Positional adapters append new transition scalars after retained timing fields and delegate to one request transaction
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/core.pyi
    - tests/test_builder.py
    - tests/test_construction_parity.py
    - tests/test_final_states.py
    - tests/test_transition_modes.py
    - tests/test_graph_invariants.py
key-decisions:
  - Inapplicable declarative handler metadata is direct-compatibility data and cannot influence a staged owner's async classification or validation.
  - Batch transition rows carry internal mode as their eighth trailing field after condition, priority, after, and within.
requirements-completed: [BUILD-02, BUILD-06]
coverage:
  - id: D1
    description: Builder imports only source-applicable state-owned declarations while retaining immutable plural metadata, collision atomicity, repair, cache, and exactly-once async execution.
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: tests/test_builder.py#test_builder_ignores_nonapplicable_declarative_guards_during_preflight
        status: pass
      - kind: integration
        ref: tests/test_builder.py#test_builder_declarative_async_topology_owns_each_runtime_seam_once
        status: pass
    human_judgment: false
  - id: D2
    description: Direct, batch, builder, declarative, and callback construction preserve internal lifecycle, priority, history, finality, and final-source failure semantics through the canonical transaction.
    requirement: BUILD-06
    verification:
      - kind: integration
        ref: tests/test_construction_parity.py#test_construction_parity_covers_final_destination_and_internal_batch_row
        status: pass
      - kind: unit
        ref: tests/test_graph_invariants.py#test_batch_transition_mode_rows_remain_one_canonical_request_transaction
        status: pass
    human_judgment: false
duration: 43 min
completed: 2026-09-17
status: complete
---

# Phase 30 Plan 02: Declarative Builder and Adapter Parity Summary

**Builder declaration ownership now governs async preflight, while batch construction can express the same internal-transition topology as every other supported adapter.**

## Performance

- **Duration:** 43 min
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Aligned declarative async detection and preflight with build-time source applicability, so a foreign constrained handler cannot reject or reclassify an unrelated staged state.
- Completed the builder matrix for initial/later declarative owners, defensive source-list copies, exact duplicates, priority collisions, repairable failure, cache identity, and async lifecycle ownership.
- Extended retained batch rows with an exact-boolean eighth `internal` field, preserving one `_TransitionRequest` publication path for direct, batch, builder, declarative, and callback-state construction.
- Added an observable central parity oracle covering priority, internal lifecycle omission, history, state identity/finality, and atomic final-source rejection.

## Task Commits

1. **Task 1: Complete declarative applicability, async detection, conflicts, and builder repair** — `922962d` (RED tests), `6dcf33f` (implementation)
2. **Task 2: Expand construction parity through direct, batch, builder, declarative, and callback paths** — `bbfae6d` (RED tests), `1110fcf` (implementation)

## Files Created/Modified

- `src/fast_fsm/core.py` — aligns declarative preflight with exact owner applicability and accepts internal batch rows.
- `src/fast_fsm/core.pyi` — makes the public batch-row shape match the runtime parser.
- `tests/test_builder.py` — covers full declarative builder applicability, repair, caching, conflicts, and async exactly-once behavior.
- `tests/test_construction_parity.py` — central direct/batch/builder/declarative/callback observable-semantics oracle.
- `tests/test_final_states.py`, `tests/test_transition_modes.py`, and `tests/test_graph_invariants.py` — focused finality, mode, and canonical-transaction regression checks.

## Decisions Made

- Only a decorator whose `from_state` applies to its exact staged owner can affect that owner's builder import and async preflight; nonmatching metadata remains available for direct state compatibility without becoming topology.
- The batch row contract remains positional and backward-compatible: `internal` is optional, exact-boolean, and follows `within` as the eighth field.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Added internal mode to the retained batch adapter**
- **Found during:** Task 2
- **Issue:** `add_transitions()` accepted priority and timing but had no public row position for `internal=True`, so the required batch parity topology could not be authored.
- **Fix:** Added the optional eighth row field, synchronized the runtime/stub aliases and quick-factory validation, and retained canonical validation/publication.
- **Files modified:** `src/fast_fsm/core.py`, `src/fast_fsm/core.pyi`, parity and boundary tests.
- **Verification:** Focused adapter suite, Ruff, and blocking mypy pass.
- **Committed in:** `1110fcf`

**Total deviations:** 1 auto-fixed (1 Rule 2 correctness gap).
**Impact on plan:** The extension is additive, preserves all 3–7-field rows, and is required for BUILD-06 mode parity rather than a second construction path.

## Issues Encountered

- `task typecheck-ty` still reports its pre-existing advisory unresolved relative import for `.conditions`. It is not a Plan 02 regression; blocking `task typecheck-mypy` passes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The declarative builder and covered direct/batch/callback adapters now share final/internal semantics. Plan 03 can add the retained helper deprecation cycle without duplicating topology rules.

## Self-Check: PASSED

- All seven declared implementation and test files exist.
- Task commits `922962d`, `6dcf33f`, `bbfae6d`, and `1110fcf` exist in git history.
- Plan-targeted tests, Ruff format/lint, and blocking mypy pass; ty remains the documented advisory only.

---
*Phase: 30-builder-first-construction-persistence-parity*
*Completed: 2026-09-17*
