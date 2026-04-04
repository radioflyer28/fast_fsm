---
phase: 260404-exx
plan: 01
subsystem: core
tags: [callbacks, listeners, hooks, async]
dependency_graph:
  requires: []
  provides: [before_transition hook, on_failed callback, on_trigger callback, after_transition convenience]
  affects: [StateMachine, AsyncStateMachine, clone, add_listener]
tech_stack:
  added: []
  patterns: [observer, callback registry]
key_files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_listeners.py
    - tests/test_advanced_functionality.py
decisions:
  - "_before_listeners and _on_failed_callbacks intentionally NOT copied in clone() — consistent with existing listener list behaviour"
  - "after_transition(fn) added as convenience method appending to _after_listeners (no new slot needed)"
  - "_trigger_callbacks IS copied in clone() — per-trigger watches are part of machine topology config, not per-session observation"
metrics:
  duration: "~15 minutes"
  completed: "2026-04-04"
  tasks: 3
  files_changed: 3
---

# Phase 260404-exx Plan 01: Fill Callback Hook Gaps Summary

**One-liner:** Four new callback hooks on StateMachine — `before_transition` listener protocol, `after_transition(fn)` convenience, `on_failed(fn)` for all failure paths, `on_trigger(name, fn)` per-trigger watch — plus async and clone wiring.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement four hooks in core.py | 0ee0c0e | src/fast_fsm/core.py |
| 2 | Write tests for all four hooks | dd8b607 | tests/test_listeners.py, tests/test_advanced_functionality.py |
| 3 | Full regression suite | (no files) | — |

## Changes Made

### src/fast_fsm/core.py

- **StateMachine.__slots__**: added `_before_listeners`, `_on_failed_callbacks`, `_trigger_callbacks`
- **StateMachine.__init__**: initialized all three new slots (`list`, `list`, `dict`)
- **add_listener()**: extracts `before_transition` protocol method from listener objects
- **New methods**: `after_transition(fn)`, `on_failed(fn)`, `on_trigger(name, fn)`
- **_execute_transition()**: fires `_before_listeners` before on_exit; fires `_trigger_callbacks[trigger]` after `_after_listeners`
- **trigger()**: fires `_on_failed_callbacks` at all 4 early-return failure paths
- **AsyncStateMachine.trigger_async()**: same `_on_failed_callbacks` wiring at all 4 failure paths
- **StateMachine.clone()**: copies `_trigger_callbacks` (deep copy inner lists); skips `_before_listeners` and `_on_failed_callbacks`

### Callback execution order (updated)

1. `_before_listeners` — before on_exit
2. `old_state.on_exit()` + `_state_exit_callbacks`
3. `_on_exit_listeners`
4. *(state change)*
5. `to_state.on_enter()` + `_state_enter_callbacks`
6. `_on_enter_listeners`
7. `_after_listeners`
8. `_trigger_callbacks[trigger]`

## Tests Added

**test_listeners.py — TestBeforeTransitionListener (4 tests):**
- `test_before_transition_fires_before_on_exit_state` — order assertion: before < exit < after
- `test_before_transition_not_called_on_blocked_trigger` — no fire when trigger blocked
- `test_before_transition_receives_correct_args` — source/target are State objects
- `test_before_transition_state_values_correct` — correct state names

**test_advanced_functionality.py — 4 new test classes (13 tests total):**
- `TestAfterTransitionMethod` (2): fires on success, not on failure
- `TestOnFailedMethod` (4): fires on no-match, condition fail; not on success; forwards kwargs
- `TestOnTriggerMethod` (4): fires for matching trigger, not for different, not on fail, correct args
- `TestCloneCallbackBehavior` (3): copies trigger_callbacks; drops before_listeners; drops on_failed

## Verification

- `uv run python setup.py build_ext --inplace -q` — exits 0
- Import check: all 4 methods callable, slots accessible
- `uv run pytest tests/test_listeners.py tests/test_advanced_functionality.py` — 150 passed
- `uv run pytest tests/` — **653 passed, 0 failures**

## Deviations from Plan

None — plan executed exactly as written (with critical_notes guidance applied precisely).

## Self-Check: PASSED

- src/fast_fsm/core.py exists with all new slots/methods ✓
- Commits 0ee0c0e and dd8b607 exist ✓
- 653 tests pass ✓
