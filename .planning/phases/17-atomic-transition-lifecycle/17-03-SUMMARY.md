---
phase: 17-atomic-transition-lifecycle
plan: "03"
subsystem: runtime
tags: [lifecycle, state-machine, callbacks, history, declarative, mypyc]
requires:
  - phase: 17-atomic-transition-lifecycle
    provides: TransitionResult failure metadata and finalization from Plan 17-02
provides:
  - Synchronous trigger lifecycle with locked ordering, staged failures, and atomic commit boundary
  - Direct control-transition compatibility for force_state, reset, and restore
affects: [core-runtime, listeners, builder, declarative-handlers, lifecycle-tests]
tech-stack:
  added: []
  patterns: [fail-fast lifecycle runner, pre-commit versus post-commit failure classification, direct-control compatibility runner]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_transition_lifecycle.py
    - tests/test_advanced_functionality.py
    - tests/test_listeners.py
    - tests/test_builder.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - Ordinary synchronous transitions use one fail-fast runner with a non-user-code commit boundary before destination-side work.
  - Declarative handlers execute post-commit before trigger callbacks, while direct handle_event compatibility remains separate.
  - force_state, reset, and restore use a best-effort direct-control runner rather than the ordinary trigger transaction.
requirements-completed: [LIFE-01, LIFE-02, LIFE-03, LIFE-04, LIFE-05]
metrics:
  duration: 13 min
  completed: 2026-09-01
actuals:
  tokens: 12499.5
  tasks: 2
  commits: 4
status: complete
---

# Phase 17 Plan 03: Synchronous Lifecycle Transaction Summary

Implemented a fail-fast synchronous lifecycle transaction that records precise failure stage and commit state while preserving direct-control and declarative compatibility.

## What Changed

### Task 1: Lock the synchronous lifecycle transaction

- Added RED lifecycle-contract tests for the complete success order, failures at every synchronous stage, commit/history behavior, and declarative-handler failures.
- Reworked `StateMachine._execute_transition()` into one ordered, fail-fast runner: pre listeners; source exit hooks/callbacks/listeners; internal commit/history; destination enter hooks/callbacks/listeners; declarative handler; trigger callbacks; post listeners.
- Added staged lifecycle-failure construction so results retain the original exception, `stage`, `committed`, and the correct pre- or post-commit state without rollback.
- Moved ordinary declarative handler execution into the transaction runner and retained direct `handle_event()` handling unchanged.
- Updated the core API memory with the exact synchronous order, failure policy, and declarative semantics.

### Task 2: Preserve legacy direct-control compatibility

- Added RED compatibility tests for direct force/reset/restore behavior, legacy listener expectations, builder policies, and ordinary declarative outcomes.
- Added a separate `_execute_control_transition()` path used by `force_state()` (and therefore `reset()`/`restore()`) to preserve best-effort direct callbacks without a trigger transaction or finalizer.
- Reconciled listener and builder coverage with the Phase 17 failure-result policy while retaining raising behavior for preflight `can_trigger()` policy checks.
- Documented the direct-control contract beside the synchronous lifecycle API.

## Verification

- Fresh isolated pure build: lifecycle and compatibility matrix — 419 passed.
- Fresh isolated compiled build: lifecycle and compatibility matrix — 419 passed.
- Fresh isolated pure build: direct force/reset/restore compatibility selection — 10 passed.
- `uv run ruff format --check` and `uv run ruff check` passed for all modified Python files.
- `uv run task typecheck-mypy` passed.
- SPR lifecycle and direct-control token assertions passed.

## Task Commits

1. `f278f1d` — `test(17-03): add failing sync lifecycle contract`
2. `af7aef8` — `feat(17-03): implement sync lifecycle transaction`
3. `b54b987` — `test(17-03): define sync lifecycle compatibility regressions`
4. `e6c78cb` — `feat(17-03): preserve direct control compatibility`

## Decisions Made

- The commit boundary remains internal non-user code; all user callbacks before it produce uncommitted failures, and all destination-side callbacks after it produce committed failures.
- A failed ordinary declarative handler is a post-commit lifecycle outcome, but direct event handling retains its existing local compatibility path.
- Direct control operations intentionally remain best-effort and do not receive ordinary trigger lifecycle finalization.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Compatibility regression] Aligned stale safe-trigger error assertions with the Phase 17 redacted, stage-aware failure result.
   - **Found during:** Task 2
   - **Fix:** Assert the guard-stage result and retained cause instead of the old raw raised-exception message.
   - **Files modified:** `tests/test_advanced_functionality.py`
   - **Commit:** `e6c78cb`

2. [Rule 1 - Compatibility regression] Aligned builder policy trigger expectations with the Phase 17 `TransitionResult` failure contract.
   - **Found during:** Task 2
   - **Fix:** Kept `can_trigger()` policy exceptions while asserting a failed trigger result for the ordinary trigger path.
   - **Files modified:** `tests/test_builder.py`
   - **Commit:** `e6c78cb`

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed the summary exists at the required phase path.
- Confirmed all four RED/GREEN task commits are present in git history.
