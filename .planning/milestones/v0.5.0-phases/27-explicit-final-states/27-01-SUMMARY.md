---
phase: 27-explicit-final-states
plan: 01
phase_bead_id: fast_fsm-7xh
subsystem: core-runtime
tags: [state-machine, final-state, slots, mypyc, sphinx]
requires:
  - phase: 26-canonical-construction-evidence-contract
    provides: canonical slotted State model and atomic construction boundary
provides:
  - immutable exact-bool State.final metadata
  - inherited O(1) StateMachine.is_terminated query
  - final propagation through state construction surfaces
affects: [27-02-final-source-invariant, 27-03-control-persistence, phase-32-documentation]
actuals:
  tokens: 2974
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - immutable state metadata in private slots with getter-only public access
    - derived runtime truth from the canonical current State
key-files:
  created:
    - tests/test_final_states.py
  modified:
    - src/fast_fsm/core.py
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Finality lives only on State._final and is validated as an exact built-in bool."
  - "Termination is one inherited current-state marker read, with no machine cache or graph inference."
  - "Callback and declarative construction add keyword-only final forwarding while AsyncDeclarativeState inherits the same path."
patterns-established:
  - "Use AST guards to preserve slots, getter-only metadata, and a single runtime truth source across mypyc changes."
requirements-completed: [FINAL-01, FINAL-02, FINAL-04]
coverage:
  - id: D1
    description: "Exact immutable final-state metadata is available through public State construction surfaces."
    requirement: FINAL-01
    verification:
      - kind: unit
        ref: "tests/test_final_states.py#TestStateFinalMetadata and TestFinalConstructionSurfaces"
        status: pass
      - kind: other
        ref: "uv run python tools/release_evidence.py slots-policy --json"
        status: pass
    human_judgment: false
  - id: D2
    description: "Termination is a direct inherited current-State read for initial and transitioned final states."
    requirement: FINAL-02
    verification:
      - kind: unit
        ref: "tests/test_final_states.py#TestTerminationQuery"
        status: pass
      - kind: other
        ref: "tests/test_mypyc_guard.py#test_final_state_metadata_and_termination_query_keep_one_truth_source"
        status: pass
    human_judgment: false
  - id: D3
    description: "A non-final sink remains distinct from an explicitly terminated final state."
    requirement: FINAL-04
    verification:
      - kind: unit
        ref: "tests/test_final_states.py#test_non_final_sink_is_not_terminated"
        status: pass
    human_judgment: false
duration: 5min
completed: 2026-09-15
status: complete
---

# Phase 27 Plan 01: Explicit Final-State Metadata Summary

**Slotted, immutable explicit final-state intent with a single O(1) termination query across direct, callback, and declarative state construction.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-15T22:19:43Z
- **Completed:** 2026-09-15T22:24:12Z
- **Tasks:** 2/2
- **Files modified:** 4
- **Phase Beads item:** `fast_fsm-7xh` (claimed and intentionally left open for phase verification)

## Accomplishments

- Added `State(name, *, final=False)` with an exact built-in-bool check, private slotted storage, and a read-only `final` property.
- Added inherited `StateMachine.is_terminated`, directly derived from `self._current_state.final`, preserving ordinary missing-transition behavior for final states.
- Propagated the keyword-only marker through `State.create`, `CallbackState`, and `DeclarativeState`; `AsyncDeclarativeState` inherits the declarative path.
- Added behavioral and AST regressions for slots, immutability, callback compatibility, interpreted subclasses, and the absence of a machine-side termination latch.
- Updated the living core API SPR and verified the generated API documentation with warnings treated as errors.

## Verification

- `bd ready --json` — passed with the configured local Dolt service.
- `uv run pytest tests/test_final_states.py -x -q -k "state or initial or sink or transition or missing"` — 11 passed.
- `uv run pytest tests/test_final_states.py tests/test_mypyc_guard.py -x -q` — 153 passed, 6 skipped.
- `uv run ruff format ...` and `uv run ruff check ...` — passed.
- `task typecheck-mypy` and `task typecheck-ty` — passed.
- `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` — passed.
- `uv run python tools/release_evidence.py slots-policy --json` — passed.

## Task Commits

1. **Task 1: Trace explicit final declaration through initialization, transition, and termination query**
   - `ffb03da` — `test(27-01): add failing final-state contract`
   - `0e21bf8` — `feat(27-01): add explicit final-state metadata`
2. **Task 2: Propagate final metadata through every State construction surface and structural boundary**
   - `69035ea` — `test(27-01): cover final construction surfaces`
   - `93a8248` — `feat(27-01): propagate final metadata across states`

## Files Created/Modified

- `tests/test_final_states.py` — central behavioral oracle for explicit final intent, termination, and construction surfaces.
- `src/fast_fsm/core.py` — slotted final metadata, derived termination query, and constructor forwarding.
- `tests/test_mypyc_guard.py` — structural proof of the slot, getter, direct query chain, and inherited async implementation.
- `.specify/memory/spr-core-api.md` — living explicit-final and construction contract.

## Decisions Made

- Keep finality as immutable state identity metadata rather than a `StateMachine` field, registry, or graph-shape inference.
- Preserve callback and logger positional compatibility by making `final` keyword-only on every explicit construction surface.
- Keep termination query behavior inherited by both synchronous and asynchronous machines rather than duplicating an async implementation.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The repository Beads store is reachable only outside the workspace sandbox. The required read-only `bd ready --json` check passed against the configured local Dolt service before implementation.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 27-02 can add the final-source construction invariant at the existing canonical normalization seam without altering dispatch.
- The Phase 27 Beads item remains open until the later lifecycle, persistence, native-parity, and phase-verification work is complete.

## Self-Check: PASSED

---
*Phase: 27-explicit-final-states*
*Completed: 2026-09-15*
