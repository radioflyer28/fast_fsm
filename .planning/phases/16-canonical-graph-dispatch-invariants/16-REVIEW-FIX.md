---
phase: 16
fixed_at: 2026-09-01T14:59:44Z
review_path: .planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md
cycle: 5
iteration: 2
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-09-01T14:59:44Z
**Source review:** `.planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md`
**Cycle / iteration:** 5 / 2

**Summary:**

- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: Awaitable guard results omit generator protocol and resource ownership

**Status:** Fixed: requires human verification
**Files modified:** `src/fast_fsm/conditions.py`,
`src/fast_fsm/core.py`, `tests/test_condition_templates.py`
**Commits:** `ffc57ff`, `f949f25`, `2e9453e`
**Applied fix:** Centralized protocol-complete awaitable detection, including
generator-based coroutine awaitables created with `types.coroutine`. Deferred
composite and negated results now own their already-created child until they
begin execution, so closing or finalizing an unstarted parent closes that child
exactly once. The direct check boundary remains synchronous when every child is
synchronous, retains left-to-right short-circuiting and exactly-once execution,
and continues to expose the public `GuardResult` contract without moving guard
evaluation into the compiled machine evaluator.

### CR-02: Coverage-floor migration authorization follows attacker-controlled paths

**Status:** Fixed: requires human verification
**Files modified:** `tools/phase16_isolated_verify.py`,
`tests/test_mypyc_guard.py`
**Commit:** `e4040ff`
**Applied fix:** Replaced migration reads through an untrusted `Path` with a
repository-anchored, no-follow descriptor walk. Both symlinked parents and a
symlinked manifest leaf are rejected before content is parsed. Regression tests
exercise each escape route and prove the in-repository manifest and external
target remain untouched.

### WR-01: Forced-sync async entry documentation contradicts builder behavior

**Status:** Fixed
**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`
**Commit:** `9415a21`
**Applied fix:** Aligned `on_enter_async` documentation with the forced-sync
fail-before-publication contract and removed the unreachable warning branch.
The regression test confirms the documented contract and that the builder does
not publish a machine after the forced-sync preflight failure.

## Verification

Source and test changes were made in an isolated review-fix worktree, then
fast-forwarded into the main checkout before final verification. Origin-sensitive
gates ran in fresh temporary exports: pure mode asserted
`src/fast_fsm/core.py`; compiled mode rebuilt and asserted a fresh native core
extension. No developer-checkout native shadow was imported or removed.

- Focused pure and fresh-compiled condition-template, migration, and builder
  regressions: exit 0.
- Ruff format and lint: exit 0. Strict mypy: exit 0. Pure slots-policy check:
  exit 0.
- `uv run python tools/phase16_isolated_verify.py --suite phase16`: exit 0.
  It passed fresh pure and compiled semantic matrices, compiled
  trigger/history performance selection, the full 1,221-test pure suite,
  Ruff format/lint, mypy, Sphinx HTML, three doctests, and read-only release
  baseline verification.
- `uv run python tools/phase16_isolated_verify.py --suite baseline-check`:
  exit 0.
- The baseline was truthfully regenerated through
  `--suite baseline-write` after coverage and test count improved. Commit
  `d75f185` records 1,221/1,221 pure tests, 96.64% total source coverage, and
  95.13% `core.py` coverage; no durable floor was lowered.

This report is intentionally uncommitted; the review workflow owns its
documentation commit.

---

_Fixed: 2026-09-01T14:59:44Z_
_Fixer: gsd-code-fixer_
_Cycle / iteration: 5 / 2_
