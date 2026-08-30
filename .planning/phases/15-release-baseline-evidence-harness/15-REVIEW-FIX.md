---
phase: 15
fixed_at: 2026-08-30T01:34:00Z
review_path: .planning/phases/15-release-baseline-evidence-harness/15-REVIEW.md
iteration: 13
cycle: staged-source-audit-boundary
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 15: Code Review Fix Report

**Fixed at:** 2026-08-30T01:34:00Z  
**Source review:** `.planning/phases/15-release-baseline-evidence-harness/15-REVIEW.md`  
**Cycle:** staged-source-audit-boundary (iteration 13)

**Summary:**

- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### CR-01: Selected source can mutate the authoritative finder before a denied artifact executes

**Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`  
**Commits:** `730094d`, `1c1d092`

**Applied fix:** The runtime auditor now copies only selected `fast_fsm/**/*.py`
files into a fresh temporary source root before launching the child process. The
original root is never supplied to that child or added to its import path, so
legacy bytecode and native siblings cannot be selected. The authoritative finder
holds its mapping-proxy policy and loader references in closure state, has no
instance dictionary, rejects instance mutation, and has a frozen finder class.
The regression attempts to read/mutate/restore finder policy before importing a
marker-writing sibling `.pyc`; it fails before the marker can execute.

### CR-02: Captured audit references remain mutable through selected-code caller frames

**Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`  
**Commit:** `730094d`

**Applied fix:** Trusted builtins, import machinery, paths, serializer, and raw
type access are now captured as `run_audit` function defaults and locals before
selected imports; no module-global `_AUDIT_*` references remain. A documented
pre-execution AST auditability contract fails closed for dynamic execution,
`sys._getframe`, `inspect` frame APIs, `ctypes`, and direct type/object mutation
primitives that could bypass the audit boundary. The caller-frame `_AUDIT_VARS`
attack is rejected before its dynamic dictionary-bearing class can run.

### Evidence refresh

**Files modified:** `evidence/release-baseline.json`  
**Commit:** `3ef4e69`

**Applied fix:** Regenerated from a clean committed pure-source worktree. The
baseline records 879/879 tests; only the expected test inventory and volatile,
environment-labelled benchmark observation changed.

## Verification

Focused finder-policy/legacy-bytecode/caller-frame regressions and the full
`tests/test_release_evidence.py` suite passed, as did Ruff formatting and lint,
mypy for `tools/release_evidence.py`, and generated-script parse checks in the
isolated review worktree.

The final authoritative gate ran in a second fresh detached clean worktree after
`FAST_FSM_BUILD_MODE=pure uv sync --locked --all-groups` and immediate source
preflight:

- `FAST_FSM_BUILD_MODE=pure task release-gate` — passed
- `pytest tests/ -x -q` — 879 passed
- Ruff, mypy, strict Sphinx HTML, and doctests — passed
- `task release-baseline-check` — passed without rewriting evidence (879/879,
  95.75% total coverage)

This report is intentionally uncommitted for the review workflow to own.

---

_Fixed: 2026-08-30T01:34:00Z_  
_Fixer: gsd-code-fixer_  
_Cycle: staged-source-audit-boundary / iteration 13_
