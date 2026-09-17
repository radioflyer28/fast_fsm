---
phase: 28-same-state-transition-modes
reviewed: 2026-09-17T01:52:12Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - .github/copilot-instructions.md
  - .gitignore
  - .specify/memory/spr-core-api.md
  - .vscode/mcp.json
  - AGENTS.md
  - src/fast_fsm/core.py
  - src/fast_fsm/core.pyi
  - tests/test_builder.py
  - tests/test_graph_invariants.py
  - tests/test_hypothesis.py
  - tests/test_mypyc_guard.py
  - tests/test_priority_selection.py
  - tests/test_transition_modes.py
  - tests/test_transition_timing.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 28: Code Review Report

**Reviewed:** 2026-09-17T01:52:12Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** clean

## Summary

All Phase 28 review findings are resolved. Candidate-specific terminal
selection failures now preserve the selected immutable entry's `internal` mode
in both synchronous and asynchronous dispatch, while group fallthrough and
group-exhaustion results remain mode-neutral. Focused pure-mode regressions
cover timing, direct and declarative guard rejection/exception, and state
permission rejection/exception seams in both dispatch modes.

## Narrative Findings (AI reviewer)

## Resolved Issues

### CR-01: Pre-commit candidate failures discarded internal-mode truth

**Classification:** RESOLVED

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:2873-3042` and `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:5083-5193`

**Issue:** Both candidate evaluators attached `entry.priority` to terminal timing,
guard, declarative-guard, and state-permission failures but omit
`internal=entry.internal`. Consequently, a registered internal self-transition
whose guard raises returns `TransitionResult(success=False, stage="guard",
priority=7, internal=False)`. The same transition reports `internal=True` when
cancelled during that guard and when it reaches lifecycle execution. This makes
ordinary failure results disagree with the immutable candidate that caused
them, breaks the Phase 28 sync/async failure-parity contract, and gives callers
contradictory mode metadata depending only on whether an async guard raises or
is cancelled. Normal group fallthrough and group exhaustion should remain
mode-neutral; the defect is in terminal results for the currently evaluated
entry.

The existing `test_internal_priority_guard_error_is_terminal_before_lifecycle`
asserts priority, stage, commit, and cause but never asserts `result.internal`,
so the scoped suite passes despite the contract violation. A direct pure-mode
probe produced:

```text
sync False guard 7 False
async False guard 7 False
```

**Fix:** The candidate scalar is now propagated on every terminal result produced by
`_select_sync_candidate()` and `_select_async_candidate()`, while leaving
`None` fallthrough and group-exhaustion results unchanged. Add paired sync and
async regressions for guard exceptions and at least one non-exception singleton
rejection seam (timing or permission).

```python
return self._build_failure_result(
    current_name,
    trigger,
    "Transition guard raised an exception",
    stage=_LIFECYCLE_STAGE_GUARD,
    cause=cause,
    priority=entry.priority,
    internal=entry.internal,
)
```

All terminal candidate-specific failure branches in both evaluators now pass
`internal=entry.internal`. The regression suite covers direct and declarative
guard rejection and exceptions, state-permission rejection and exceptions, and
timing rejection in both dispatch modes.

## Resolution Evidence

- Fix commit `5454eef` adds `internal=entry.internal` to each terminal timing,
  guard, declarative-guard, and state-permission result built by
  `_select_sync_candidate()` and `_select_async_candidate()`.
- `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_transition_modes.py tests/test_priority_selection.py -x -q` — passed: 35 tests.
- `uv run ruff format src/fast_fsm/core.py tests/test_transition_modes.py`,
  `uv run ruff check --fix ...`, and clean `uv run ruff check ...` — passed.
- `task typecheck-mypy` — passed for the package and explicit `core.py` check.
- `uv run python -c "import ast; ..."` and `git diff --check` — passed.

---

_Reviewed: 2026-09-17T01:52:12Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
