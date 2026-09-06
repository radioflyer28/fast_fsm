---
phase: 18-safe-ownership-concurrency
plan: 02
subsystem: runtime-concurrency
tags: [threading, ownership, lifecycle, direct-control, mypyc]
requires:
  - phase: 18-01
    provides: per-machine synchronous lock, owner marker, and private trigger body
provides:
  - Complete synchronous trigger ownership coverage through callbacks and failure finalization
  - Single-admission force, reset, and restore control operations
  - Deterministic sync reentry, contention, cleanup, and clone-isolation regressions
affects: [18-03, 18-04, 18-05, async-ownership, writer-admission]
tech-stack:
  added: []
  patterns: [one-public-admission, private-already-owned-body, finally-release]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_ownership_concurrency.py
    - tests/test_transition_lifecycle.py
    - tests/test_advanced_functionality.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Keep ordinary trigger ownership through every Phase 17 callback and failure observer."
  - "Give force_state, reset, and restore distinct public labels but one private _force_state_owned body."
  - "Retain direct-control best-effort Exception behavior while finally releasing after BaseException."
patterns-established:
  - "A public synchronous writer acquires once, calls a private owned body, and releases in finally."
  - "Callback reentry is tested with Event handshakes rather than scheduling assumptions."
requirements-completed: [OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07]
actuals:
  tokens: 8071
  tasks: 2
  commits: 2
coverage:
  - id: D1
    description: "Synchronous trigger ownership rejects callback reentry and retains the envelope through failure finalization."
    requirement: OWN-01
    verification:
      - kind: integration
        ref: "tests/test_ownership_concurrency.py#test_sync_uncaught_reentry_preserves_the_outer_lifecycle_stage"
        status: pass
      - kind: integration
        ref: "tests/test_transition_lifecycle.py#test_sync_failure_observer_reentry_is_rejected_inside_the_outer_finalizer"
        status: pass
    human_judgment: false
  - id: D2
    description: "force_state, reset, and restore use one ownership admission and an already-owned control body."
    requirement: OWN-02
    verification:
      - kind: integration
        ref: "tests/test_ownership_concurrency.py#test_sync_direct_control_reentry_precedes_nested_validation"
        status: pass
      - kind: integration
        ref: "tests/test_ownership_concurrency.py#test_sync_direct_control_serializes_threads_and_releases_after_validation"
        status: pass
    human_judgment: false
  - id: D3
    description: "Direct-control BaseException and clone paths leave ownership isolated and reusable."
    requirement: OWN-06
    verification:
      - kind: integration
        ref: "tests/test_ownership_concurrency.py#test_sync_direct_control_releases_after_baseexception"
        status: pass
      - kind: integration
        ref: "tests/test_advanced_functionality.py#TestClone.test_clone_has_independent_sync_ownership_primitives"
        status: pass
    human_judgment: false
duration: 15m
completed: 2026-09-01
status: complete
---

# Phase 18 Plan 02: Synchronous Ownership and Direct Control Summary

**Synchronous transitions and direct control now serialize per machine, reject callback reentry before nested work, and release cleanly after every tested exit.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-01T20:51:00Z
- **Completed:** 2026-09-01T21:06:20Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Covered the full synchronous Phase 17 lifecycle matrix for caught and uncaught callback-triggered reentry, including observer finalization and `BaseException` isolation.
- Routed `force_state`, `reset`, and `restore` through one admission each and the private `_force_state_owned()` body, avoiding false public-to-public reentry.
- Proved direct-control thread serialization, validation and `BaseException` cleanup, and independent clone lock/owner state.

## Task Commits

1. **Task 1: Finish the synchronous trigger envelope and callback-originated reentry matrix** — `6614faa` (`test`)
2. **Task 2: Give force, reset, and restore one direct-control ownership entry** — `81baea2` (`feat`)

## Files Created/Modified

- `src/fast_fsm/core.py` — adds private owned direct-control execution and wraps every public control entry in ownership cleanup.
- `tests/test_ownership_concurrency.py` — adds lifecycle-stage, finalizer, control, contention, validation, and `BaseException` matrices.
- `tests/test_transition_lifecycle.py` — proves failure observers cannot reenter during finalization.
- `tests/test_advanced_functionality.py` — asserts cloned machines own independent lock and marker primitives.
- `.specify/memory/spr-core-api.md` — records the completed sync trigger and direct-control contracts.

## Decisions Made

- Retained the Phase 17 fail-fast ordinary trigger lifecycle unchanged inside the ownership envelope.
- Preserved direct-control’s legacy best-effort behavior for ordinary callback exceptions; only ownership admission is fail-fast.
- Used the project’s isolated pure-source harness because the intentionally retained native shadow cannot represent newly added private source symbols.

## Deviations from Plan

None - plan behavior executed as specified. The source verification commands ran through `tools/phase16_isolated_verify.py` in asserted pure mode because the working checkout intentionally retains a stale compiled shadow; no native artifact was modified.

## Verification

- `uv run ruff format` and `uv run ruff check` passed for all task files.
- `task typecheck-mypy` passed with no issues.
- `uv run python tools/release_evidence.py slots-policy --json` passed.
- Asserted-pure focused and full regressions passed; future-plan ownership rows remain strict xfails.

## Self-Check: PASSED

- Required source, test, and SPR files exist.
- Task commits `6614faa` and `81baea2` exist in git history.

## Next Phase Readiness

Plan 18-03 can build the paired async ownership contract on the established per-machine synchronous primitive. Future strict RED rows for Plans 18-03 through 18-05 remain intact.

---
*Phase: 18-safe-ownership-concurrency*
*Completed: 2026-09-01*
