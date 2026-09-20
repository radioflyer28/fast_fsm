---
phase: 28
fixed_at: 2026-09-17T01:52:12Z
review_path: /Users/akriz/code/fast_fsm/.planning/phases/28-same-state-transition-modes/28-REVIEW.md
iteration: 3
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 28: Code Review Fix Report

**Fixed at:** 2026-09-17T01:52:12Z
**Source review:** `/Users/akriz/code/fast_fsm/.planning/phases/28-same-state-transition-modes/28-REVIEW.md`
**Iteration:** 3

**Summary:**

- Findings in scope: 1
- Fixed: 1
- Skipped: 0

## Fixed Issues

### CR-01: Pre-commit candidate failures discard internal-mode truth

**Files modified:** `src/fast_fsm/core.py`, `tests/test_transition_modes.py`
**Commit:** 5454eef
**Applied fix:** Propagated `entry.internal` into every singleton terminal
timing, direct/declarative guard, and state-permission failure result in both
sync and async candidate selectors. Kept group fallthrough and group-exhaustion
results mode-neutral. Added focused parity tests for timing, direct and
declarative guard rejection/exception, and state-permission rejection/exception
paths in both dispatch modes.

## Verification

Verification ran in the isolated review-fix worktree
`/Users/akriz/code/fast_fsm/.claude/worktrees/rf-28-74929-1789609627` before
it was removed after the commit fast-forwarded to the milestone branch.

- `uv run python -c "import ast; ..."` — passed syntax parsing.
- `uv run ruff format src/fast_fsm/core.py tests/test_transition_modes.py`,
  `uv run ruff check --fix ...`, and clean `uv run ruff check ...` — passed.
- `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_transition_modes.py tests/test_priority_selection.py -x -q` — passed: 35 tests.
- `task typecheck-mypy` — passed for the package and explicit `core.py` check.
- `git diff --check` — passed.

---

_Fixed: 2026-09-17T01:52:12Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 3_
