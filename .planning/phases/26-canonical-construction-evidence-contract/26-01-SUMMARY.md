---
phase: 26-canonical-construction-evidence-contract
plan: 01
subsystem: core
tags: [construction, atomicity, topology, ownership, mypyc]
requires:
  - phase: 22-priority-aware-runtime-selection
    provides: immutable priority candidate groups and atomic off-table publication
provides:
  - One immutable private raw transition-request carrier and canonical owned apply transaction
  - Atomic direct/batch construction proofs for failure, no-op, duplicate, and multi-slot cases
  - Interruption, concurrency, and runtime-path isolation proofs
affects: [phase-27, phase-28, phase-29, phase-30, builder, persistence]
actuals:
  tokens: 4744
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - immutable raw request to normalized off-table plan to single publication
    - adapter-owned source-shape freezing before machine-owned normalization
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_graph_invariants.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Copy mutable public source lists at the adapter edge so _TransitionRequest can remain an ordinary frozen/slotted dataclass compatible with the runtime audit."
  - "Keep construction ownership on existing public envelopes and keep selectors and lifecycle runners structurally unaware of the cold request carrier."
patterns-established:
  - "Canonical construction: retained adapters emit immutable raw requests; one owned method normalizes the complete tuple and publishes once."
  - "Atomic observation: machine snapshot readers share the writer ownership primitive; tests inspect raw tables only when deliberately proving an in-progress writer has not published."
requirements-completed: [BUILD-04, BUILD-05]
phase_bead_id: fast_fsm-qj4
coverage:
  - id: D1
    description: Direct and batch transition registration share one immutable normalize/merge/publish transaction.
    requirement: BUILD-04
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_construction_request_direct_and_batch_share_canonical_transaction
        status: pass
      - kind: unit
        ref: tests/test_graph_invariants.py#test_construction_request_adapters_delegate_only_to_canonical_apply
        status: pass
    human_judgment: false
  - id: D2
    description: Construction is atomic, idempotent, interruption-safe, serialized, and absent from runtime selection/lifecycle regions.
    requirement: BUILD-05
    verification:
      - kind: unit
        ref: tests/test_graph_invariants.py#test_construction_request_collection_rejects_before_publication
        status: pass
      - kind: unit
        ref: tests/test_graph_invariants.py#test_construction_request_interruption_releases_ownership_without_publication
        status: pass
      - kind: unit
        ref: tests/test_graph_invariants.py#test_concurrent_construction_requests_are_serialized_as_whole_transactions
        status: pass
      - kind: unit
        ref: tests/test_graph_invariants.py#test_construction_hot_path_symbols_are_absent_from_runtime_regions
        status: pass
    human_judgment: false
duration: 12min
completed: 2026-09-15
status: complete
---

# Phase 26 Plan 01: Canonical Construction Tracer Summary

**Direct and batch registrations now enter one immutable, atomic construction transaction without touching runtime dispatch.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-15T17:46:00Z
- **Completed:** 2026-09-15T17:58:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added frozen/slotted `_TransitionRequest` values that retain raw endpoint identity while copying mutable source lists at adapter entry.
- Routed direct and batch registration through `_apply_transition_requests_owned()`, which validates and normalizes the complete request tuple before the existing single publication boundary.
- Proved exact idempotence, failure and `BaseException` atomicity, serialized concurrent machine construction, and structural isolation from sync/async selection and lifecycle code.

## Task Commits

1. **RED: Define canonical request behavior** — `e9344f7` (test)
2. **GREEN: Implement the request transaction** — `f1c3f28` (feat)
3. **Task 2: Prove construction invariants and update the SPR** — `37d00c4` (test)

**Plan metadata:** this summary commit

## Files Created/Modified

- `src/fast_fsm/core.py` — Adds the raw carrier, adapter source freezing, and canonical apply seam.
- `tests/test_graph_invariants.py` — Covers adapter equivalence, atomicity, idempotence, interruption, concurrency, and hot-path isolation.
- `.specify/memory/spr-core-api.md` — Records the cold construction transaction and unchanged runtime boundary.

## Decisions Made

- Source-shape copying belongs at the adapter edge. This avoids forbidden dynamic attribute assignment while preserving a genuinely frozen/slotted carrier.
- The private apply method accepts only a finite tuple of valid `_TransitionRequest` objects, so `None` and malformed elements fail before normalization or publication.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed a runtime-audit-incompatible frozen initializer**

- **Found during:** Task 2 slots-policy verification
- **Issue:** A custom frozen dataclass initializer required `object.__setattr__`, which the production source audit prohibits.
- **Fix:** Moved mutable-list copying to `_freeze_transition_sources()` at the adapter boundary and restored a generated frozen/slotted dataclass initializer.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_graph_invariants.py`
- **Verification:** `uv run python tools/release_evidence.py slots-policy --json` passes and reports `_TransitionRequest` as slot-protected.
- **Committed in:** `37d00c4`

---

**Total deviations:** 1 auto-fixed (1 blocking runtime-audit constraint).
**Impact on plan:** The corrected implementation matches the research-prescribed adapter boundary and preserves all requested semantics without scope expansion.

## Issues Encountered

- The initial concurrency assertion attempted to take the public snapshot ownership lock while intentionally pausing a writer. The test was corrected to inspect the private table/version directly at that synchronization point, which is precisely the non-blocking observation the proof requires.
- Stale local compiled extensions initially shadowed `core.py`; the six reviewed untracked build artifacts were moved to `/private/tmp/fast-fsm-phase26-native.hUNbbb` before source verification.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- The canonical direct/batch seam is ready for the retained adapter, builder, clone, and persistence propagation in plan 26-03.
- Exact isolated competitor evidence remains in plan 26-02 and is still gated by the plan 26-04 human provenance checkpoint.

## Self-Check: PASSED

- All 39 graph invariant tests pass.
- Ruff formatting/checking, mypy, ty, and the recursive slots-policy audit pass.
- Beads item `fast_fsm-qj4` remains claimed and in progress.

---
*Phase: 26-canonical-construction-evidence-contract*
*Completed: 2026-09-15*
