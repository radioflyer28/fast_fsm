---
phase: 16
fixed_at: 2026-08-30T17:10:00Z
review_path: .planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md
iteration: 2
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-08-30T17:10:00Z
**Source review:** `.planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md`
**Iteration:** cycle 2, iteration 2

**Summary:**

- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: Async evaluation bypasses `FuncCondition` subclass overrides

**Status:** Fixed: requires human verification
**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`, `tests/test_async.py`
**Commit:** `0b92c25`
**Applied fix:** Retained the direct wrapped-callable path only for the exact
built-in `FuncCondition`. Public subclasses now invoke their effective
`check()` override through the dynamic boundary and await an awaitable result.
The pure and compiled regressions cover direct `AsyncDeclarativeState` policy
and ordinary machine dispatch where the override rejects, raises, or returns
an awaitable while the stored callable would otherwise accept.

### CR-02: Predictable atomic-write temporary follows symlinks and overwrites targets

**Status:** Fixed: requires human verification
**Files modified:** `tools/phase16_isolated_verify.py`, `tests/test_mypyc_guard.py`
**Commit:** `cdc8974`
**Applied fix:** Replaced the predictable sibling filename with an
unpredictable exclusive same-directory `NamedTemporaryFile`, copied through
the opened descriptor, flushed and fsynced it, atomically replaced the
destination, and cleaned the fresh temporary file on every failure path. The
adversarial regression leaves the legacy symlink and its outside victim
untouched; a replace-failure regression proves no temporary remains.

### CR-03: Non-finite coverage values bypass the regression floor

**Status:** Fixed: requires human verification
**Files modified:** `tools/phase16_isolated_verify.py`, `tests/test_mypyc_guard.py`
**Commit:** `c68bab2`
**Applied fix:** Coverage parsing now rejects booleans, non-numbers,
`NaN`, both infinities, and raw values below 0 or above 100 before rounding or
comparison. The exact validation is shared by existing, generated, and
explicit migration manifests. Parameterized regressions preserve destination
bytes for every rejected value in each path.

## Verification

Verification began in the isolated review-fix worktree and all import-bearing
checks then ran from fresh temporary `HEAD` exports through
`tools/phase16_isolated_verify.py`. Pure contexts asserted
`src/fast_fsm/core.py`; compiled contexts built and asserted a native
`fast_fsm.core` extension. No developer-checkout native shadow was imported,
deleted, or used as evidence.

- Tier 1 rereads, `git diff --check`, Ruff format/lint, and Python AST parsing
  passed for every modified Python file.
- CR-01 focused pure and compiled contexts each passed 7 regressions.
- CR-02 focused pure and compiled contexts each passed 4 regressions,
  including the pre-positioned-symlink victim and failure cleanup checks.
- CR-03 focused pure and compiled contexts each passed 59 regressions covering
  `NaN`, positive/negative infinity, booleans, non-numbers, and out-of-range
  existing/generated/migration percentages with destination-byte preservation.
- The pre-refresh full Phase 16 semantic suite passed in asserted pure and
  compiled contexts; the compiled trigger/history performance selection passed
  3 tests and retained its existing 200,000 ops/s floor. Its first release
  check stopped only because the previous manifest was stale after the new
  tests increased observations to 1,129 passing tests and 96.21% / 94.57%
  total / `core.py` coverage.
- After the semantic and type gates passed, the isolated baseline write and
  independent baseline check passed with 1,129/1,129 tests, 96.21% total
  coverage, and 94.57% `core.py` coverage. The evidence commit is `9f4c096`.
- The final isolated pure release gate passed source-origin preflight, Ruff,
  mypy, all tests, Sphinx HTML/doctests, and read-only baseline freshness.
  `task typecheck-mypy` passed; advisory `task typecheck-ty` exited 0 with two
  non-blocking redundant-`Any`-cast diagnostics at dynamic mypyc boundaries.

---

_Fixed: 2026-08-30T17:10:00Z_
_Fixer: gsd-code-fixer_
_Iteration: cycle 2, iteration 2_
