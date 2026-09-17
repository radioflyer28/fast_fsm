---
phase: 30-builder-first-construction-persistence-parity
plan: 04
subsystem: core-persistence
tags: [serialization, clone, snapshot, final-states, internal-transitions, construction-parity]
requires:
  - phase: 30-03
    provides: retained construction adapters with warning-contained canonical parity
provides:
  - True-only JSON topology emission and exact, atomic internal-mode reconstruction
  - Clone identity/isolation proof and unchanged receiver-owned snapshot-v1 semantics
  - Deserialization and clone cells in the construction parity oracle
affects: [30-05, 30-06, 31-semantic-diagnostics, 32-artifact-proof]
actuals:
  tokens: 5953
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - Parse untrusted serialized topology into complete local request rows before one canonical apply
    - Share immutable state/callable collaborators across clones while rebuilding mutable ownership containers
    - Treat snapshot v1 as state-only; receiving topology owns finality and transition mode
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_advanced_functionality.py
    - tests/test_final_states.py
    - tests/test_transition_modes.py
    - tests/test_construction_parity.py
key-decisions:
  - Dictionary `internal` is additive and emitted only as JSON `true`; absent and exact false remain external for directional legacy compatibility.
  - `from_dict()` accepts only exact built-in serialized containers/scalars for its topology shape and reports bounded transition-index context without inspecting payload representations.
  - Clone remains a canonical-request replay with shared immutable collaborators, independent mutable registries, and reset history; snapshot v1 remains unchanged and receiver-owned.
requirements-completed: [BUILD-06, BUILD-07, BUILD-08]
coverage:
  - id: D1
    description: Topology dictionaries preserve final/internal metadata, true-only output, opaque guard references, timing, and legacy external defaults while rejecting malformed exact types before canonical publication.
    requirement: BUILD-07
    verification:
      - kind: integration
        ref: tests/test_advanced_functionality.py#TestPrioritySerialization
        status: pass
      - kind: integration
        ref: tests/test_final_states.py#TestFinalControlCloneAndPersistence
        status: pass
      - kind: integration
        ref: tests/test_transition_modes.py#test_dictionary_reconstructed_internal_transition_retains_lifecycle_mode
        status: pass
    human_judgment: false
  - id: D2
    description: Sync and async clones preserve concrete type and immutable collaborators while rebuilding all mutable topology/callback/ownership containers and resetting current/history; snapshot v1 derives finality and mode from its receiver.
    requirement: BUILD-08
    verification:
      - kind: integration
        ref: tests/test_advanced_functionality.py#TestPrioritySerialization.test_clone_retains_state_and_callable_identity_without_aliasing_tables
        status: pass
      - kind: integration
        ref: tests/test_final_states.py#TestFinalControlCloneAndPersistence
        status: pass
    human_judgment: false
  - id: D3
    description: Direct, batch, builder, declarative, callback, clone, and deserialization construction paths have matching final/internal observable behavior.
    requirement: BUILD-06
    verification:
      - kind: integration
        ref: tests/test_construction_parity.py#test_construction_parity_covers_final_destination_and_internal_batch_row
        status: pass
      - kind: integration
        ref: tests/test_graph_invariants.py#test_retained_transition_adapters_use_the_canonical_request_transaction
        status: pass
    human_judgment: false
duration: 14 min
completed: 2026-09-17
status: complete
---

# Phase 30 Plan 04: Persistence, Clone, and Snapshot Parity Summary

**Topology dictionaries now preserve explicit final states and internal self-transition mode through exact, atomic reconstruction, while clones and state-only snapshots retain their established ownership semantics.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-17T19:56:00Z
- **Completed:** 2026-09-17T20:10:02Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added true-only `internal: true` topology emission; external rows retain their previous shape, and omitted or exact `false` input remains external.
- Tightened dictionary parsing to exact built-in serialized shape checks, bounded indexed errors, and one request tuple submitted to the canonical transaction.
- Extended persistence tests through JSON, final-state, guard-reference, priority, timing, sync/async, and reconstructed lifecycle behavior.
- Proved clone state/callable identity, fresh mutable registries and async ownership primitives, reset current/history state, and snapshot-v1 receiver-owned finality/mode.
- Completed the construction parity oracle with deserialization and clone adapter cells.

## Task Commits

1. **Task 1: Implement exact true-only dictionary mode round trips and atomic validation** — `8163597` (RED coverage), `dabf51c` (implementation)
2. **Task 2: Prove clone isolation, snapshot-v1 ownership, and complete adapter parity** — `7cefe90` (verification coverage)

## Files Created/Modified

- `src/fast_fsm/core.py` — exact serialized topology validation plus true-only internal transition emission.
- `tests/test_advanced_functionality.py` — dictionary type/round-trip and clone identity/isolation coverage.
- `tests/test_final_states.py` — asynchronous dictionary/clone and receiver-owned restore coverage.
- `tests/test_transition_modes.py` — reconstructed internal lifecycle coverage.
- `tests/test_construction_parity.py` — clone and deserialization cells in the observable construction oracle.

## Decisions Made

- Keep dictionary compatibility directional: older payloads use omitted/false defaults, but no schema version or old-reader semantic claim is introduced.
- Preserve the existing clone/snapshot implementation after the stronger tests confirmed canonical replay, independent containers, reset behavior, and receiver-owned topology truth.
- Keep persistence, clone, and snapshot validation outside dispatch; no transition selection or lifecycle policy moved into hot paths.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Style] Replaced a test callback lambda rejected by Ruff**

- **Found during:** Task 2 quality checks.
- **Issue:** Ruff's `E731` rule rejects assigning a lambda to a test callback variable.
- **Fix:** Replaced it with a local named callback function without changing test behavior.
- **Files modified:** `tests/test_advanced_functionality.py`
- **Verification:** Plan-wide Ruff format/lint and focused clone/snapshot matrix pass.
- **Committed in:** `7cefe90`

**Total deviations:** 1 auto-fixed (1 Rule 1 style correction).
**Impact on plan:** No scope expansion or runtime behavior change.

## Issues Encountered

- `task typecheck-ty` reports the existing advisory unresolved relative import `.conditions` in `src/fast_fsm/core.py`. Blocking `task typecheck-mypy` passes; the same advisory is documented by Plans 29-01/02/04 and 30-01/02/03 and is unrelated to this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 05 can document the settled builder-first and directional persistence contracts without changing their runtime semantics.
- Plan 06 can synchronize the project API memory and complete the broader release/artifact closure.

## Self-Check: PASSED

- Required modified files and task commits `8163597`, `dabf51c`, and `7cefe90` exist.
- The plan-wide focused pure-source suite, Ruff format/lint, and blocking mypy all pass.
- `ty` was run and retains only its documented pre-existing advisory diagnostic.

---
*Phase: 30-builder-first-construction-persistence-parity*
*Completed: 2026-09-17*
