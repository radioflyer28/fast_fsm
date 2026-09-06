---
phase: 21-priority-contract-atomic-registration
plan: 01
subsystem: core-fsm
tags: [python, mypyc, priority, atomic-registration]
requires:
  - phase: 20-installed-artifact-proof
    provides: canonical graph/version invariants and the compiled-core boundary
provides:
  - Exact keyword-only priority registration through `add_transition`
  - Direct singleton slots and immutable ascending-priority candidate groups
  - Atomic staged merge with duplicate identity and one-version publication
affects: [22-ordered-runtime-selection, 23-construction-parity, 24-diagnostics-output, 25-performance-artifact-proof]
actuals:
  tokens: 7189
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - Exact built-in type validation on an object-typed mypyc boundary
    - Replacement-only singleton-or-group slot transactions
key-files:
  created:
    - .specify/decisions/ADR-007-priority-topology.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_graph_invariants.py
    - tests/test_hypothesis.py
    - tests/test_mypyc_guard.py
    - .specify/memory/constitution.md
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Validate priority as an exact built-in int while the public implementation boundary is object-typed."
  - "Represent one candidate directly and promote competing priorities into a private frozen tuple-backed group."
  - "Stage every slot replacement before publishing, incrementing graph version once only for identity-changing topology."
patterns-established:
  - "Singleton fast path: preserve direct slot lookup and dispatch; defer grouped winner selection to Phase 22."
  - "Atomic group merge: merge repeated keys against their staged replacement, never a last-write map."
requirements-completed: [PRIO-01, PRIO-02]
coverage:
  - id: D1
    description: "Priority-aware add_transition stores direct singletons or immutable ordered candidate groups."
    requirement: PRIO-01
    verification:
      - kind: unit
        ref: "tests/test_graph_invariants.py#test_priority_registration_keeps_singletons_direct_and_groups_immutable"
        status: pass
      - kind: other
        ref: "uv run pytest tests/ -x -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exact priority validation and duplicate-safe atomic registration preserve graph identity and version."
    requirement: PRIO-02
    verification:
      - kind: unit
        ref: "tests/test_graph_invariants.py#test_equal_priority_conflict_rolls_back_all_staged_replacements"
        status: pass
      - kind: unit
        ref: "tests/test_hypothesis.py#TestPriorityRegistrationOrder.test_priority_candidate_permutations_have_one_ascending_topology"
        status: pass
      - kind: other
        ref: "task typecheck-mypy; task typecheck-ty; uv run python tools/release_evidence.py slots-policy --json"
        status: pass
    human_judgment: false
duration: 21 min
completed: 2026-09-06
status: complete
---

# Phase 21 Plan 01: Priority Contract and Atomic Registration Summary

**`add_transition(..., priority=...)` now constructs exact-validated singleton or immutable ordered candidate topology with atomic duplicate-safe publication.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-09-06T21:23:47Z
- **Completed:** 2026-09-06T21:44:37Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added the keyword-only `priority` registration contract with exact built-in integer validation before mypyc narrowing.
- Preserved direct singleton storage and promoted competing candidates into frozen, slotted, tuple-backed ascending groups.
- Replaced last-write plan publication with staged duplicate-safe merging, late-conflict rollback, and one-version commits.
- Documented the local O(k) candidate-group contract in the constitution, SPR, and ADR-007 without introducing runtime winner selection or projection parity.

## Task Commits

1. **Task 1: Trace one competing candidate through the public API into immutable topology**
   - `3a950cd` — failing priority topology tests
   - `fad5505` — singleton/group implementation and contract documentation
2. **Task 2: Generalize candidate merging to duplicate-safe atomic registration plans**
   - `9fb45c6` — rollback, identity, staged-merge, and permutation coverage

Additional verification fixes:

- `3e27a00` — compiled-boundary AST guard and analyzer-compatible exact narrowing
- `e392553` — cached live slots to restore the singleton constant-work bound

## Files Created/Modified

- `.specify/decisions/ADR-007-priority-topology.md` — D-01 through D-08 topology decision record.
- `.specify/memory/constitution.md` and `.specify/memory/spr-core-api.md` — truthful singleton O(1) and finite-group O(k) policy.
- `src/fast_fsm/core.py` — exact priority validation, typed slot union, immutable groups, and atomic merge/publish logic.
- `tests/test_graph_invariants.py`, `tests/test_hypothesis.py`, and `tests/test_mypyc_guard.py` — topology, rollback, permutation, and compiled-layout coverage.

## Decisions Made

- Priority stays `object` until `type(priority) is int` succeeds, preventing mypyc from erasing the exact-type contract.
- Grouped runtime and projection consumers return fixed fail-closed errors; Phase 22 owns selection and Phases 23–24 own parity.
- Atomic merge retains the singleton performance bound by caching each live slot while applying replacement-only staged values.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical verification] Extended the compiled-core guard for the new group and priority fields.**
- **Found during:** Plan-wide compiled-boundary verification
- **Issue:** The existing AST guard rejected the intentionally added `_PreparedTransition.priority` field and did not assert `_TransitionGroup` layout, public hiding, or object-typed validation.
- **Fix:** Updated `tests/test_mypyc_guard.py` with frozen/slotted group, `TransitionEntry` slot, private-export, and exact-boundary assertions.
- **Files modified:** `tests/test_mypyc_guard.py`, `src/fast_fsm/core.py`
- **Verification:** mypyc guard tests, mypy, ty, and slots-policy all passed.
- **Committed in:** `3e27a00`

**2. [Rule 1 - Performance regression] Restored the singleton registration operation-count bound.**
- **Found during:** Full-suite verification
- **Issue:** Re-reading each live slot while evaluating and publishing replacements raised `add_transition` mapping operations from 6 to 10.
- **Fix:** Cached original live slots during staging, then published only identity-changing replacements.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** focused performance invariant and the complete suite passed.
- **Committed in:** `e392553`

---

**Total deviations:** 2 auto-fixed (1 Rule 2 verification, 1 Rule 1 performance regression).
**Impact on plan:** Both changes preserve the explicit compiled and singleton-performance contracts without expanding the Phase 21 boundary.

## TDD Gate Compliance

Task 1 completed the red/green commits. Task 2's added regression/property tests passed immediately because the sole commit seam had already been generalized in Task 1 to prevent last-write loss; the tests are non-vacuous and fail against the pre-plan singleton implementation.

## Issues Encountered

- The local beads Dolt server was unavailable, so each Git pre-commit hook emitted an export warning; all Git commits completed normally and no issue-tracker state was changed.
- The full suite emitted one existing test-generated duplicate-zip-name warning and otherwise passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 22 can introduce ordered sync/async winner selection on the frozen slot union. Grouped runtime dispatch currently fails closed by design; construction, clone/query/serialization parity remains explicitly deferred to Phase 23.

## Self-Check: PASSED

Verified all seven implementation/spec/test artifacts exist and all five implementation commits are present in Git history.
