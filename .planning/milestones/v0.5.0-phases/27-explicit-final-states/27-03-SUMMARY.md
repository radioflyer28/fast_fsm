---
phase: 27-explicit-final-states
plan: 03
phase_bead_id: fast_fsm-7xh
subsystem: core-lifecycle-persistence
tags: [state-machine, final-state, lifecycle, serialization, mypyc, async]
requires:
  - phase: 27-02
    provides: canonical atomic rejection of final-state sources
  - phase: 27-01
    provides: immutable State.final metadata and derived termination query
provides:
  - deterministic backward-compatible final_states topology persistence
  - lifecycle, control, clone, and async finality continuity
  - compiled and pure-source parity evidence for final-state behavior
affects: [phase-28-transition-modes, phase-30-persistence-parity, phase-32-artifact-proof]
actuals:
  tokens: 6646
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - strict additive topology metadata validated before canonical candidate construction
    - current-state-derived termination remains authoritative after post-commit failures
    - native parity keeps exact runtime validation at object-typed input boundaries
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_final_states.py
    - tests/test_graph_invariants.py
    - tests/test_transition_lifecycle.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Persist only explicit final-state names as a sorted top-level final_states list; legacy omission remains all non-final."
  - "Keep termination derived from current State at the existing commit/control seam, including sync and async post-commit failure paths."
  - "Use object-typed compiled entry boundaries for exact runtime validation rather than accepting mypyc coercion."
patterns-established:
  - "Native behavior suites may exclude only private monkeypatch-injection probes; the same probes run in the pure-source full suite."
requirements-completed: [FINAL-03, FINAL-05, FINAL-06]
coverage:
  - id: D1
    description: "Control operations, clone, async clone, and snapshot-v1 restore derive termination only from canonical State.final."
    requirement: FINAL-06
    verification:
      - kind: integration
        ref: "tests/test_final_states.py#TestFinalControlCloneAndPersistence"
        status: pass
    human_judgment: false
  - id: D2
    description: "Deterministic final_states persistence accepts valid final targets, defaults legacy data, and rejects malformed or final-source topology before publication."
    requirement: FINAL-03
    verification:
      - kind: unit
        ref: "tests/test_final_states.py#TestFinalControlCloneAndPersistence"
        status: pass
      - kind: integration
        ref: "tests/test_graph_invariants.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Committed finality is visible during destination entry and remains true after sync failures or post-commit async cancellation."
    requirement: FINAL-05
    verification:
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_sync_lifecycle_callback_failure_stops_the_suffix_at_its_stage"
        status: pass
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_async_cancellation_finalizes_once_at_the_reached_boundary"
        status: pass
    human_judgment: false
  - id: D4
    description: "Exact final validation, construction atomicity, lifecycle truth, and persistence agree in compiled and restored pure-source core modes."
    requirement: FINAL-06
    verification:
      - kind: other
        ref: "task build-check; compiled focused Phase 27 suite; task pure-source-check; uv run pytest tests/ -x -q"
        status: pass
    human_judgment: false
duration: 18min
completed: 2026-09-15
status: complete
---

# Phase 27 Plan 03: Final Lifecycle and Persistence Summary

**Explicit finality now survives direct control, cloning, strict topology persistence, lifecycle failures, and compiled/pure-source execution without adding a second termination truth source.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-09-15T22:35:00Z
- **Completed:** 2026-09-15T22:53:06Z
- **Tasks:** 2/2
- **Files modified:** 5
- **Phase Beads item:** `fast_fsm-7xh` remains in progress until the Phase 27 verifier closes it.

## Accomplishments

- Added sorted JSON-native `final_states` metadata to `to_dict()` and strict backward-compatible `from_dict()` validation before any candidate can escape; snapshot v1 remains unchanged.
- Proved reset, force-state, restore, clone, and async construction derive termination from the reached canonical State marker and preserve shared State identity with independent topology.
- Extended synchronous failure and async cancellation matrices so destination entry observes committed termination and every post-commit path retains finality, history, result stage, cause, and observer behavior.
- Closed two compiled-core parity gaps: exact `final` validation now happens before mypyc coercion, and raw list-subclass iteration remains dynamic at the public construction boundary.
- Ran the ordered native/pure gate: compiled build and focused suite, exact preflight-reported shadow relocation, pure-source origin proof, and final complete source suite.

## Verification

- `uv run pytest tests/test_final_states.py tests/test_transition_lifecycle.py tests/test_graph_invariants.py tests/test_builder.py tests/test_async.py tests/test_hypothesis.py tests/test_mypyc_guard.py -x -q` — passed in both compiled and pure-source modes (two compiled-only skips are private monkeypatch-injection probes, both exercised by the pure-source suite).
- `uv run pytest tests/ -x -q` — passed after final pure-source restoration.
- `uv run ruff format`, `uv run ruff check --fix`, and `uv run ruff check` — passed.
- `task typecheck-mypy`, `task typecheck-ty`, `uv run python tools/release_evidence.py slots-policy --json`, and `uv lock --check` — passed.
- `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` — passed.
- `task build-check` and compiled-origin assertion — passed.
- `task pure-source-check` and exact `src/fast_fsm/core.py` origin assertion — passed; no native shadow remains under `src/fast_fsm`.

## Task Commits

1. **Task 1: Preserve finality through control, clone, and strict additive dictionary persistence**
   - `aa0e5b4` — `test(27-03): add final persistence regressions`
   - `2b53963` — `feat(27-03): persist explicit final states`
2. **Task 2: Prove post-commit termination and close interpreted/native/pure-source validation**
   - `ed515a6` — `fix(27-03): preserve finality across native lifecycle parity`

## Files Created/Modified

- `src/fast_fsm/core.py` — validates and serializes explicit final markers, and preserves exact public input behavior in compiled mode.
- `tests/test_final_states.py` — control, clone, persistence, legacy, invalid-input, and async parity oracle.
- `tests/test_graph_invariants.py` — additive schema proof plus native-safe private-injection handling.
- `tests/test_transition_lifecycle.py` — committed sync/async finality failure and cancellation matrices.
- `.specify/memory/spr-core-api.md` — normative control, clone, snapshot, and persistence contract.

## Decisions Made

- Serialize a deterministic explicit-name list rather than infer completion from topology; legacy dictionaries reconstruct every State as non-final.
- Preserve the established commit boundary: state assignment and optional history happen before destination-side callbacks, so termination remains an O(1) current-State read after later failures.
- Keep native-focused tests behavioral. Two tests that intentionally replace private compiled method dispatch are scoped to pure source, where their injection mechanism is valid; their state-safety properties remain covered by the final pure-source suite.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Native compatibility] Preserved exact final-value validation in the compiled core.**
- **Found during:** Task 2
- **Issue:** mypyc coerced a `bool`-annotated constructor argument before the required exact-value validator could reject it with the public bounded error.
- **Fix:** Kept final-constructor boundaries object-typed until the exact `type(final) is bool` guard completes.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** Compiled final-state oracle passed.
- **Committed in:** `ed515a6`

**2. [Rule 1 - Native compatibility] Restored dynamic list-subclass iteration at the construction boundary.**
- **Found during:** Task 2
- **Issue:** mypyc optimized tuple conversion of a typed list and bypassed a caller-supplied list subclass iterator, weakening the all-or-nothing interruption contract.
- **Fix:** Routed the raw list copy through an object-typed iterator before freezing it.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** Compiled interruption regression and full compiled suite passed.
- **Committed in:** `ed515a6`

**Total deviations:** 2 auto-fixed Rule 1 compatibility corrections.
**Impact on plan:** Both corrections preserve already-promised public semantics across source and compiled cores; no scope expanded.

## Issues Encountered

- The compiled suite cannot monkeypatch two private static method dispatch calls. Those probes now skip only when the native extension is loaded and execute in the final pure-source full suite; public semantic coverage remains compiled and pure.
- Exact generated native shadows were moved only after preflight reporting to recoverable temporary backups. The final backup is `/tmp/fast-fsm-phase27-native-backup.fDeBuZ`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 27 implementation is ready for phase-level verification and its Beads closure gate.
- Phase 28 may rely on finality as immutable State metadata, a derived current-State query, and additive `final_states` topology persistence.

## Self-Check: PASSED

- All required source, test, and SPR files exist on the branch.
- Task commits `aa0e5b4`, `2b53963`, and `ed515a6` exist in history.
- `task pure-source-check` reports `src/fast_fsm/core.py`; no `core*.so` or `core*.pyd` file remains in the source package.

---
*Phase: 27-explicit-final-states*
*Completed: 2026-09-15*
