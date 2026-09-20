---
phase: 28-same-state-transition-modes
plan: 03
subsystem: fsm-runtime
tags: [python, fsm, async, cancellation, mypyc, native-parity]
requires:
  - phase: 28-02
    provides: synchronous lifecycle, timing, priority, and failure truth for both transition modes
provides:
  - Async internal self-transition lifecycle parity with the synchronous selected-entry seam
  - Cancellation-safe selected-mode metadata and reusable async ownership
  - Structural, pure-source, and fresh compiled-native proof of transition-mode behavior
affects: [29-expected-domain-rejection, 30-construction-and-persistence-parity, 31-diagnostics, 32-docs-and-release]
actuals:
  tokens: 14727
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - Async cancellation retains only task-local selected priority and internal-mode scalars until dispatch is prepared.
    - Native verification builds from an asserted pure origin and relocates only validated source-tree core shadows before final pure tests.
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_transition_modes.py
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Async execution branches only on prepared.entry.internal, matching the synchronous selected-entry seam."
  - "Cancellation result mode is retained in a task-local ContextVar before a prepared dispatch exists; no callback payload or machine map is added."
  - "The compiled oracle uses public behavior only, because interpreted test subclasses cannot inherit from the compiled machine type."
patterns-established:
  - "Internal async events skip every state lifecycle hook, callback, and listener together while retaining before, logical commit, declarative, trigger, and after work."
  - "Native/pure parity tests assert source origin both before and after a fresh in-place mypyc build."
requirements-completed: [MODE-01, MODE-02, MODE-03, MODE-04, MODE-05, MODE-06]
coverage:
  - id: D1
    description: "Async internal and external self-transitions select the same mode/priority truth as synchronous dispatch and retain or suppress matching lifecycle surfaces."
    requirement: MODE-04
    verification:
      - kind: integration
        ref: "tests/test_transition_modes.py#test_async_internal_transition_retains_transition_work_and_skips_all_state_surfaces"
        status: pass
      - kind: integration
        ref: "tests/test_mypyc_guard.py#test_priority_selector_semantic_probe_matches_pure_and_native_core"
        status: pass
    human_judgment: false
  - id: D2
    description: "Async guard and retained declarative cancellation preserve pre/post-commit truth, finalization cardinality, released ownership, and successful reuse."
    requirement: MODE-06
    verification:
      - kind: integration
        ref: "tests/test_transition_modes.py#test_async_internal_guard_cancellation_is_uncommitted_mode_true_and_reusable"
        status: pass
      - kind: integration
        ref: "tests/test_transition_modes.py#test_async_internal_postcommit_cancellation_is_mode_true_and_reusable"
        status: pass
    human_judgment: false
  - id: D3
    description: "Canonical carrier and stub layouts, exact validation, selected-entry dispatch, fresh compiled semantics, and restored pure-source origin remain locked."
    requirement: MODE-01
    verification:
      - kind: integration
        ref: "tests/test_mypyc_guard.py#test_phase28_mode_carriers_and_async_selection_keep_one_exact_contract"
        status: pass
      - kind: integration
        ref: "task pure-source-check; task build-check; FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_transition_modes.py tests/test_mypyc_guard.py -x -q -k 'internal or mode or transition_mode'; FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q"
        status: pass
    human_judgment: false
duration: 48min
completed: 2026-09-17
status: complete
---

# Phase 28 Plan 03: Async, Cancellation, and Native Parity Summary

**Async internal self-transitions now have the same committed lifecycle, cancellation, ownership, and pure/native truth as their synchronous counterparts.**

## Performance

- **Duration:** 48 min
- **Started:** 2026-09-17T00:18:00Z
- **Completed:** 2026-09-17T01:06:25Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Routed async execution through the selected immutable entry, so internal events retain transition work but skip all synchronous and asynchronous state lifecycle surfaces.
- Kept selected internal-mode truth beside priority in task-local cancellation bookkeeping; guard-time cancellation is uncommitted, retained declarative cancellation is committed, and both release ownership for immediate reuse.
- Locked runtime/stub carrier order and direct dispatch structure, documented the settled core contract, and proved the same oracle from an asserted pure source and a freshly compiled mypyc extension.

## Task Commits

1. **Task 1: Match async lifecycle, cancellation, ownership, and reuse truth** — `7570604` (feat)
2. **Task 2: Lock structural, typing, pure/native, and full-suite parity** — `df26a3f` (test)

## Files Created/Modified

- `src/fast_fsm/core.py` — adds selected internal-mode task-local cancellation truth and an async internal lifecycle runner.
- `tests/test_transition_modes.py` — adds deterministic event-handshake lifecycle, cancellation, priority, ownership, and reuse coverage, plus a portable direct-control rejection assertion.
- `tests/test_mypyc_guard.py` — locks runtime/stub field order, exact validation ordering, selected-entry dispatch, and a direct/builder/sync/async pure-native semantic probe.
- `.specify/memory/spr-core-api.md` — records per-transition authoring, lifecycle, timing, cancellation, and deferred Phase 30 persistence truth.

## Decisions Made

- The async runner receives `_PreparedDispatch` rather than a separately supplied target/mode, keeping `prepared.entry.internal` as its only post-selection source of truth.
- A task-local `ContextVar[bool]` complements existing priority tracking only while candidate selection awaits; callback kwargs and per-machine dispatch maps remain unchanged.
- Native parity tests do not subclass `AsyncStateMachine`, since mypyc correctly rejects interpreted subclasses of the compiled type; they assert public cancellation, ownership, history, and lifecycle effects instead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test portability] Removed a CPython-specific TypeError message assertion from direct-control rejection coverage**
- **Found during:** Task 2 fresh compiled semantic probe
- **Issue:** Both runtimes reject an unsupported `internal=` direct-control argument, but mypyc emits an equivalent positional-argument TypeError rather than CPython's keyword-oriented wording.
- **Fix:** Assert the stable exception type rather than undocumented interpreter-specific error text.
- **Files modified:** `tests/test_transition_modes.py`
- **Verification:** Fresh compiled semantic probe and the restored pure-source full suite passed.
- **Committed in:** `df26a3f`

---

**Total deviations:** 1 auto-fixed (1 test portability regression)
**Impact on plan:** The correction strengthens cross-artifact parity without changing the public direct-control boundary.

## Issues Encountered

- `task typecheck-mypy` passed. Advisory `task typecheck-ty` retains its pre-existing `src/fast_fsm/core.py` relative-import resolution diagnostic; no Phase 28 typing regression was introduced.
- The fresh compiled cancellation cases emit Python 3.12 deprecation warnings from the mypyc/asyncio bridge, but their semantics passed and the warnings do not originate from application callbacks or a new Fast FSM API surface.

## TDD Gate Compliance

- Task 1's async lifecycle test was demonstrated red before the selected-entry async implementation was added, then passed with the focused matrix.
- Task 2 expands structural and native parity evidence over the Task 1 implementation; its added contract tests passed after correcting their fixture path and native-safe public observation strategy.

## User Setup Required

None — no external service configuration is required.

## Next Phase Readiness

Phase 28 now proves all six MODE requirements across direct/builder construction, sync/async lifecycle, timing, priority, failure, cancellation, clone, and pure/native execution. Phase 29 can add expected domain rejection at the established pre-commit selection seam; dictionary and retained-adapter propagation remain deliberately reserved for Phase 30.

## Self-Check: PASSED

- Task commits `7570604` and `df26a3f` exist, and all four modified artifacts exist.
- Blocking mypy, final Ruff format/check-with-fixes/clean-check, slots policy, focused pure and fresh-native probes, restored pure-origin assertions, and the full sequential pure suite passed.
- No `core*.so` or `core*.pyd` shadow remains in `src/fast_fsm`.

---
*Phase: 28-same-state-transition-modes*
*Completed: 2026-09-17*
