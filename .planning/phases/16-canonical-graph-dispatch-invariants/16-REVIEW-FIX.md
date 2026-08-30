---
phase: 16
fixed_at: 2026-08-30T15:25:00Z
review_path: .planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md
iteration: 2
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-08-30T15:25:00Z  
**Source review:** `.planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md`  
**Iteration:** 2

**Summary:**

- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: Shared declarative dispatch bypasses subclass transition policy

**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`  
**Commit:** `d63e6c5`  
**Applied fix:** Routed sync and async machine dispatch through the effective
state policy hook after one prepared decorator-guard evaluation. The private,
task-scoped marker suppresses only the base declarative duplicate guard, so
rejecting, raising, and `super()` overrides run exactly once.

### CR-02: Builder cycle validation is still non-atomic and can be skipped

**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`  
**Commit:** `8c804ce`  
**Applied fix:** Separated complete graph validation from async classification.
All auto and explicit builder modes now validate before state/transition staging,
and preflight scans every handler/guard rather than returning after the first
async requirement.

### CR-03: Async callable decorator guards are never awaited and fail open

**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`  
**Commit:** `c2d0c22`  
**Applied fix:** Classified coroutine-function decorator guards, awaited
callable results in async dispatch, and deterministically rejected them in
sync dispatch without leaking an unawaited coroutine. Native-compatible
condition-result typing keeps the same semantics in mypyc builds.

## Verification

All verification ran in the isolated review-fix worktree. Origin-sensitive
commands exported fresh temporary repositories and asserted `src/fast_fsm/core.py`
for pure mode or a newly built native `fast_fsm.core` extension for compiled
mode; developer native shadows were neither imported nor removed.

- Focused combined CR-01/CR-03 regressions: 16 passed in both pure and compiled
  contexts, covering rejecting, raising, and `super()` policy overrides plus
  false/true/raising async callable guards with exactly-once/no-warning
  assertions.
- CR-02 regressions: 30 pure mode/shape cases passed, covering all explicit and
  auto modes, four cycle shapes, unchanged staging, mixed ordering, and build
  preflight.
- `uv run python tools/phase16_isolated_verify.py --suite baseline-write --manifest-output evidence/release-baseline.json`
  and a separate `--suite baseline-check` both passed: 1,053/1,053 pure tests,
  95.68% total coverage, and 93.75% `core.py` coverage.
- `uv run python tools/phase16_isolated_verify.py --suite phase16` passed the
  pure and compiled semantic matrices, compiled performance/history checks,
  and the asserted-pure release gate (source-origin check, Ruff, mypy, tests,
  Sphinx HTML/doctests, and baseline freshness).
- `task typecheck-mypy` and advisory `task typecheck-ty` both passed.

---

_Fixed: 2026-08-30T15:25:00Z_  
_Fixer: gsd-code-fixer_  
_Iteration: 2_
