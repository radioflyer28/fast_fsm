---
phase: 18-safe-ownership-concurrency
plan: 05
subsystem: ownership-concurrency
tags: [safe-trigger, declarative-guards, contextvars, concurrency, mypyc]
requires:
  - phase: 18-04
    provides: complete public-writer ownership envelopes and D-14 structural admission guards
provides:
  - safe_trigger ownership admission outside ordinary result conversion
  - context-local machine-qualified declarative guard marker with token restoration
  - fresh pure/native coverage for safe-trigger and declarative compatibility seams
affects: [18-06, 18-07, phase18-verification, phase19]
tech-stack:
  added: []
  patterns: [one-entry-safe-writer, contextvar-token-reset, fresh-origin-native-verification]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_ownership_concurrency.py
    - tests/test_transition_lifecycle.py
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "safe_trigger owns once before its ordinary Exception barrier, so ownership admission RuntimeError values remain observable and redacted."
  - "Declarative preparation is one ContextVar marker containing machine/source/trigger/target identity and is restored only with the returned token."
requirements-completed: [OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07]
coverage:
  - id: D1
    description: "safe_trigger rejects ownership misuse before compatibility conversion while ordinary post-admission faults still return a stable result."
    requirement: OWN-01
    verification:
      - kind: unit
        ref: "tests/test_ownership_concurrency.py#safe_trigger ownership and conversion tests"
        status: pass
      - kind: other
        ref: "fresh pure and compiled ownership selection"
        status: pass
    human_judgment: false
  - id: D2
    description: "Declarative guard preparation is context-local, machine-qualified, and token-restored across nesting, threads, tasks, and cancellation."
    requirement: OWN-05
    verification:
      - kind: unit
        ref: "tests/test_ownership_concurrency.py#declarative marker isolation tests"
        status: pass
      - kind: unit
        ref: "tests/test_mypyc_guard.py#test_prepared_declarative_marker_is_one_contextvar_with_machine_identity"
        status: pass
      - kind: other
        ref: "fresh pure and compiled declarative/ownership selection"
        status: pass
    human_judgment: false
metrics:
  duration: 17m
  completed: 2026-09-02
  tasks: 2
  files: 5
actuals:
  tokens: 6913
  tasks: 2
  commits: 5
status: complete
---

# Phase 18 Plan 05: Safe-Trigger and Declarative Context Isolation Summary

**safe_trigger now exposes ownership misuse instead of downgrading it, and declarative guard preparation is context-local across machines, threads, tasks, and native builds.**

## Accomplishments

- Moved safe-trigger ownership admission outside its ordinary `Exception` conversion barrier, with one private `_trigger_owned()` call and unconditional release.
- Retained ordinary post-admission value conversion with a stable redacted result and log message; nested ownership errors instead reach their outer Phase 17 lifecycle stage.
- Replaced the mutable prepared-guard registry with one token-reset `ContextVar` containing exact machine/source/trigger/target identity.
- Added deterministic safe-trigger admission/redaction/reuse and declarative nesting/thread/task/cancellation regression coverage, plus structural mypyc guards.

## Task Commits

1. **Task 1: Move safe-trigger ownership admission outside its compatibility catch** — `753ffdc` (RED), `1d1c2d5` (GREEN), `4739833` (native-compatible regression fixture repair)
2. **Task 2: Replace the shared declarative marker with context-local machine-qualified state** — `249ca43` (RED), `4d620ce` (GREEN)

## Verification

- Ruff format and lint checks passed for all touched source and test files.
- `task typecheck-mypy` passed.
- Fresh pure-source selected safe-trigger, declarative, ownership, lifecycle, boundary, and AST suites passed.
- Freshly compiled selected safe-trigger, declarative, ownership, lifecycle, boundary, and AST suites passed.

## Decisions Made

- Ownership admission is a public precondition, not a safe-trigger compatibility result; its redacted `RuntimeError` is intentionally outside the broad catch.
- The prepared guard is represented by a single `ContextVar` marker and restored only with its token, preserving nested context exactly on Python 3.10 through 3.14.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Native test compatibility] Replaced an interpreted test subclass of compiled StateMachine**
- **Found during:** Task 2 compiled fresh-origin verification
- **Issue:** mypyc prohibits an interpreted test subclass of the compiled `StateMachine`, preventing the safe-trigger regression from running against native origin.
- **Fix:** Injected a malformed private transition entry to exercise the same post-admission compatibility barrier without subclassing the native class.
- **Files modified:** `tests/test_ownership_concurrency.py`
- **Verification:** Fresh compiled ownership selection passed.
- **Committed in:** `4739833`

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** The test now proves the intended boundary in both asserted origins without changing runtime scope.

## Known Stubs

None.

## Self-Check: PASSED

All five modified source/test/contract files and task commits `753ffdc`, `1d1c2d5`, `249ca43`, `4739833`, and `4d620ce` exist in the repository.

## Next Phase Readiness

Plan 18-06 can measure the completed ownership representation and complete end-to-end concurrency evidence without a safe-trigger downgrade or shared declarative marker seam.
