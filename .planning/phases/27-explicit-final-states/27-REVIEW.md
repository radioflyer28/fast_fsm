---
phase: 27-explicit-final-states
reviewed: 2026-09-15T23:02:21Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - src/fast_fsm/core.py
  - tests/test_final_states.py
  - tests/test_mypyc_guard.py
  - tests/test_graph_invariants.py
  - tests/test_builder.py
  - tests/test_hypothesis.py
  - tests/test_async.py
  - tests/test_transition_lifecycle.py
  - .specify/memory/spr-core-api.md
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 27: Code Review Report

**Reviewed:** 2026-09-15T23:02:21Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The explicit final-state runtime behavior, canonical source rejection, lifecycle commit truth, persistence validation, and sync/async tests are internally consistent, and the focused 456-test review suite passed. One public API contract defect remains: every new `final` parameter is typed as `object`, so typed callers receive no protection from values that the runtime immediately rejects. A direct strict-mypy probe confirmed that `State("done", final=object())` passes type checking and then fails at runtime.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01 [BLOCKER]: Public final-state parameters discard the promised boolean type

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:852`

**Issue:** Phase decision D-01 and FINAL-01 define `final` as a boolean public constructor parameter, but `State.__init__`, `State.create`, `CallbackState.__init__`, and `DeclarativeState.__init__` annotate it as `object` (lines 852, 876, 945, and 5342). This makes the package's PEP 561 interface claim that every object is valid even though runtime validation rejects every non-exact `bool`. Consequently, strict mypy accepts invalid client code such as `State("done", final=object())`, which then raises `TypeError` at runtime. The broad annotation also renders misleading Sphinx/API signatures for the milestone's central public feature.

**Fix:** Keep the exact runtime check for `bool` subclasses/coercible values, but expose the actual public type on all four construction surfaces and add a downstream strict-mypy regression test:

```python
def __init__(self, name: str, *, final: bool = False) -> None:
    if type(final) is not bool:
        raise TypeError("final must be an exact built-in bool")
    self.name = name
    self._final = final
```

Apply `final: bool = False` likewise to `State.create`, `CallbackState.__init__`, and `DeclarativeState.__init__`. Runtime negative tests can continue using `# type: ignore[arg-type]` to exercise fail-closed validation.

---

_Reviewed: 2026-09-15T23:02:21Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
