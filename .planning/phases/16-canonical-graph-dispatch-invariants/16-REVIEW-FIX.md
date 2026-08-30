---
phase: 16
fixed_at: 2026-08-30T18:59:45Z
review_path: .planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md
iteration: 2
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-08-30T18:59:45Z
**Source review:** `.planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md`
**Iteration:** cycle 3, iteration 2

**Summary:**

- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### CR-01: Callable-backed async conditions are classified from the wrong hook

**Status:** Fixed: requires human verification
**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`, `tests/test_async.py`
**Commits:** `b5910ab`, `fc53c36`
**Applied fix:** Exact `FuncCondition` and exact `CompiledFuncCondition` use
their stored callable, an inheriting `FuncCondition` without a replacement
`check()` is classified from its `.func`, and other subclasses are classified
from their effective `check()`. The sync evaluator now keeps overridden checks
at a dynamic mypyc boundary so it can close and reject an awaitable instead of
raising a native bool-boundary error.

### CR-02: Manifest publication can be redirected by a parent-directory swap

**Status:** Fixed: requires human verification
**Files modified:** `tools/phase16_isolated_verify.py`, `tests/test_mypyc_guard.py`
**Commits:** `26a8f35`, `7ce6c33`
**Applied fix:** Parent traversal, existing-manifest validation, exclusive
temporary creation, rename, and directory fsync now operate relative to one
no-follow descriptor anchored below the repository root. Unsupported descriptor
platforms fail closed. The regression swaps the lexical parent for an outside
symlink after opening the descriptor and proves that the outside victim and
directory remain unchanged.

### CR-03: Failed auto builds publish an incorrect selected machine type

**Status:** Fixed: requires human verification
**Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`
**Commit:** `85eb72e`
**Applied fix:** Every auto build derives a local candidate type from the
current staged graph, wires a candidate machine completely, then publishes
`_machine_type` and `_machine` together. Repair/retry tests cover sync and
async outcomes without changing the staging fingerprint.

### WR-01: Manifest publication temporarily mutates process-global umask

**Status:** Fixed
**Files modified:** `tools/phase16_isolated_verify.py`, `tests/test_mypyc_guard.py`
**Commit:** `449750f`
**Applied fix:** Payload temporaries remain private (`0600`). A no-follow,
exclusive descriptor-anchored empty probe derives the caller's normal output
mode, then `fchmod()` applies it before publication; no process-wide
`os.umask()` call occurs. The synchronized concurrency regression proves a
regular concurrent file retains the same ambient mode.

## Verification

All source changes were made in an isolated review-fix worktree, then every
origin-sensitive command used a fresh temporary archive. Pure contexts asserted
`src/fast_fsm/core.py`; compiled contexts built and asserted a fresh
`fast_fsm.core.cpython-312-darwin.so`. No developer native shadow was imported
or removed.

- Focused CR-01, CR-02, CR-03, and WR-01 regressions passed locally where an
  appropriate origin was available and in fresh pure/compiled exports. CR-02's
  focused baseline-write selection passed 81 tests in each fresh mode.
- Fresh full Phase 16 pure and compiled semantic matrices passed; the compiled
  trigger/history performance selection passed all 3 tests.
- The initial baseline write failed closed at 1,173/1,173 tests and 96.28%
  total coverage against the reviewed 96.29% floor, with no manifest change.
  Additional runtime coverage restored the floor honestly. Final baseline write
  and independent check passed at 1,175/1,175 tests, 96.37% total coverage,
  and 94.85% `core.py` coverage.
- `task typecheck-mypy` passed with no errors. Advisory `task typecheck-ty`
  exited 0 with four redundant-`Any` diagnostics at deliberate dynamic
  awaitability boundaries.
- In a retained fresh pure export, source-origin preflight, Ruff format/lint,
  mypy, the full test suite, Sphinx HTML, three doctests, and direct
  `release_evidence.py evidence --check --build-wheel` each exited 0. The
  command host truncates the monolithic `task release-gate` wrapper at 30
  seconds, so this report records its successful component exits rather than
  claiming an unobserved wrapper exit code.

The refreshed baseline and permanent gate evidence are committed in `1401525`.
This report intentionally remains uncommitted for the review-fix workflow.

---

_Fixed: 2026-08-30T18:59:45Z_
_Fixer: gsd-code-fixer_
_Iteration: cycle 3, iteration 2_
