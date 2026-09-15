---
phase: 27-explicit-final-states
plan: 02
phase_bead_id: fast_fsm-7xh
subsystem: core-construction
tags: [state-machine, final-state, atomicity, builders, async, hypothesis]
requires:
  - phase: 27-01
    provides: immutable State.final metadata and derived termination truth
  - phase: 26-canonical-construction-evidence-contract
    provides: canonical immutable transition-request transaction
provides:
  - one canonical final-source construction invariant
  - atomic final-source rejection across every retained construction adapter
  - generated and identity-sensitive rollback coverage
affects: [27-03-control-persistence, phase-32-documentation]
actuals:
  tokens: 4688
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - canonical source validation before prepared topology publication
    - adapter coverage proves delegation rather than duplicating validation
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_final_states.py
    - tests/test_graph_invariants.py
    - tests/test_builder.py
    - tests/test_hypothesis.py
    - tests/test_async.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Reject an outgoing final source immediately after canonical endpoint resolution, with fixed bounded text."
  - "Keep final-source validation construction-only; selectors and lifecycle runners remain unaware of it."
  - "Use the existing immutable request transaction so mixed helpers, builders, clones, and async machines get all-or-nothing behavior without local checks."
patterns-established:
  - "Use graph and builder fingerprints to prove that a failed construction transaction publishes no prefix and remains retryable."
requirements-completed: [FINAL-03]
coverage:
  - id: D1
    description: "Outgoing transitions from a canonical final State are rejected before prepared topology can publish, while incoming final targets remain legal."
    requirement: FINAL-03
    verification:
      - kind: unit
        ref: "tests/test_final_states.py#TestFinalSourceConstructionInvariant and tests/test_graph_invariants.py#test_final_source_mixed_batch_and_multi_source_fail_before_publication"
        status: pass
      - kind: other
        ref: "uv run python tools/release_evidence.py slots-policy --json"
        status: pass
    human_judgment: false
  - id: D2
    description: "Direct, grouped, helper, factory, builder, declarative, clone, generated, and async construction paths inherit one atomic final-source invariant."
    requirement: FINAL-03
    verification:
      - kind: integration
        ref: "tests/test_graph_invariants.py#test_final_source_helpers_and_priority_reject_without_a_prefix; tests/test_builder.py#test_builder_final_source_failure_preserves_staging_and_can_be_repaired; tests/test_async.py#test_async_registration_rejects_final_sources_without_graph_mutation"
        status: pass
      - kind: unit
        ref: "tests/test_hypothesis.py#TestFinalSourceTransactionInvariant"
        status: pass
    human_judgment: false
duration: 9min
completed: 2026-09-15
status: complete
---

# Phase 27 Plan 02: Final-Source Construction Invariant Summary

**One canonical construction branch now rejects any outgoing final-state edge atomically, while all retained adapters continue to delegate to the same fast dispatch-free transaction.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-15T22:25:00Z
- **Completed:** 2026-09-15T22:33:42Z
- **Tasks:** 2/2
- **Files modified:** 7
- **Phase Beads item:** `fast_fsm-7xh` remains claimed until Phase 27 verification closes the phase.

## Accomplishments

- Added the one fixed `ValueError("final state cannot be a transition source")` branch immediately after each source resolves to its registered canonical State.
- Preserved Phase 26 all-or-nothing semantics: final self-edges, late mixed rows, multi-source fanout, helpers, priority registrations, factories, builders, declarative sources, corrupted clone reconstruction, and async registration leave no graph/version prefix.
- Proved builder staging remains un-cached and repairable after a final-source candidate failure, while valid final destinations and normal final-preserving clones remain supported.
- Added bounded Hypothesis coverage for reordered invalid batches and direct termination-to-current-marker consistency.
- Updated the living core API SPR with the construction-only invariant and fixed public error contract.

## Verification

- `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py -x -q -k "final_source or canonical or atomic or mixed or multi_source"` — 11 passed.
- `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_builder.py tests/test_hypothesis.py tests/test_async.py -x -q -k "final or canonical or builder or clone or emergency or bidirectional"` — passed.
- `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_builder.py tests/test_hypothesis.py tests/test_async.py -q --disable-warnings` — passed.
- `uv run ruff format`, `uv run ruff check --fix`, and `uv run ruff check` on Plan files — passed.
- `task typecheck-mypy` — passed.
- `task typecheck-ty` — passed.
- `uv run python tools/release_evidence.py slots-policy --json` — passed.

## Task Commits

1. **Task 1: Reject canonical final sources before any topology publication**
   - `0e74815` — `test(27-02): add final-source transaction regressions`
   - `a0b5ee0` — `feat(27-02): reject outgoing final-state topology`
2. **Task 2: Prove adapter, builder, clone, generated, and async invariant coverage**
   - `9bd31e3` — `test(27-02): cover final-source construction adapters`

## Files Created/Modified

- `src/fast_fsm/core.py` — validates the registered final source exactly once during request normalization.
- `tests/test_final_states.py` — final-source and quick-factory behavioral coverage.
- `tests/test_graph_invariants.py` — identity-sensitive atomicity, helper, declarative, and clone proofs.
- `tests/test_builder.py` — failed final-source build staging/cache/retry contract.
- `tests/test_hypothesis.py` — reordered mixed-batch and termination-marker property coverage.
- `tests/test_async.py` — inherited async registration rollback proof.
- `.specify/memory/spr-core-api.md` — living construction-invariant contract.

## Decisions Made

- Read finality only from the registered canonical source after endpoint resolution; a foreign same-name object remains rejected by the established identity boundary and cannot spoof the marker.
- Keep final targets legal and do not add a finality branch to runtime selection, `trigger`, `can_trigger`, or lifecycle code.
- Preserve the fixed error wording so caller-controlled State names do not enter the final-source rejection.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test assertion] Corrected an assertion to use the existing public result/current-state contract.**
- **Found during:** Task 1
- **Issue:** The new red test referred to a non-existent `StateMachine.get_transition()` helper.
- **Fix:** Asserted against the established private topology table used by this invariant suite.
- **Files modified:** `tests/test_final_states.py`
- **Verification:** Focused final-source regression suite passed.
- **Committed in:** `a0b5ee0`

**Total deviations:** 1 auto-fixed (Rule 1 test assertion).
**Impact on plan:** No production scope changed; the correction keeps the intended no-publication proof aligned with existing suite conventions.

## Issues Encountered

- The restricted shell could not initialize the shared uv cache or write the Git index; the same locked commands ran successfully with the project-authorized environment.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 27-03 can add additive dictionary persistence and control/lifecycle continuity while relying on the canonical final-source transaction already enforced here.
- The Phase 27 Beads item remains open for the later persistence, native-parity, verifier, and phase-close gates.

## Self-Check: PASSED

- Required source and regression files exist and were committed in `a0b5ee0` and `9bd31e3`.
- All three task commits are present in the branch history.

---
*Phase: 27-explicit-final-states*
*Completed: 2026-09-15*
