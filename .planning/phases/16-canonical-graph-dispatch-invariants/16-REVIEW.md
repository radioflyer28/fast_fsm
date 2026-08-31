---
phase: 16-canonical-graph-dispatch-invariants
reviewed: 2026-08-31T12:37:03Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - .specify/decisions/ADR-003-mypyc-compilation-boundary.md
  - .specify/memory/spr-core-api.md
  - docs/dev/architecture.md
  - docs/dev/contributing.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/__init__.py
  - src/fast_fsm/condition_templates.py
  - src/fast_fsm/conditions.py
  - src/fast_fsm/core.py
  - tests/test_advanced_functionality.py
  - tests/test_async.py
  - tests/test_boundary_negative.py
  - tests/test_builder.py
  - tests/test_condition_templates.py
  - tests/test_graph_invariants.py
  - tests/test_mypyc_guard.py
  - tests/test_performance_benchmarks.py
  - tests/test_release_evidence.py
  - tests/test_safety_kwargs.py
  - tools/phase16_isolated_verify.py
  - tools/release_evidence.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-08-31T12:37:03Z
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

The three findings from the preceding review are resolved: the public guard aliases
are consistently exported and accepted by the guard APIs, the slots documentation
matches the measured exceptions, and ADR-003/SPR describe the interpreted wrapper
and compiled invocation bridge consistently. Public alias and wrapper identities were
also verified in isolated pure and freshly compiled installations.

The authoritative Phase 16 isolated suite and an independent baseline check both
passed with 1,191/1,191 tests, 96.53% total coverage, and 95.06% core coverage.
Those green gates do not exercise direct composite `Condition.check()` calls with
awaitable children. Such calls remain observably incorrect in both pure and compiled
builds, so the phase is not clean.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Composite condition checks coerce awaitable children instead of preserving the guard channel

**Classification:** BLOCKER

**Files:** `src/fast_fsm/condition_templates.py:130-160`,
`src/fast_fsm/conditions.py:179-181`

**Issue:** `Condition.check()` now truthfully permits `GuardResult` (`bool |
Awaitable[bool]`), but the public composite implementations still apply `all()`,
`any()`, or `not` directly to child results and still annotate their own return as
`bool`. A fresh isolated pure reproduction and a fresh mypyc build both showed
`AndCondition(FuncCondition(async_false)).check()` returning `True` and emitting
`RuntimeWarning: coroutine ... was never awaited`. `OrCondition` likewise treats an
awaitable as true, while `NegatedCondition` and `NotCondition` invert the awaitable
object's truthiness rather than its awaited boolean. Awaitables can therefore leak
unclosed, exceptions raised by them are lost, and the direct public API returns the
wrong result. The machine-owned iterative evaluators are correct, which explains why
the full suite remains green, but it does not repair direct calls to the standardized
`Condition.check()` interface. This also contradicts the explicit compatibility claim
in `.specify/memory/spr-core-api.md:20`.

**Fix:** Change all four composite `check()` methods to return `GuardResult` and add
an interpreted composition helper that preserves the current immediate `bool` result
for all-synchronous children but returns a coroutine as soon as an awaitable child is
encountered. That coroutine must await each produced value exactly once and continue
left-to-right with the same short-circuit or inversion rule. Keep the helper outside
compiled `core.py` (or inject it without reversing the `conditions -> core` dependency)
so the documented compilation boundary remains intact. For example, the shape should
be equivalent to:

```python
def check(self, *args: Any, **kwargs: Any) -> GuardResult:
    result = self.condition.check(*args, **kwargs)
    if inspect.isawaitable(result):
        async def invert() -> bool:
            return not await result
        return invert()
    return not result
```

Use a shared implementation for `AndCondition` and `OrCondition` that retains their
short-circuit behavior without evaluating later children early. Add direct-call tests
in asserted-pure and freshly compiled environments for async true, false, and raising
leaves under `NegatedCondition`, `AndCondition`, `OrCondition`, and `NotCondition`,
including a warnings-as-errors assertion that no coroutine is left unawaited.

---

_Reviewed: 2026-08-31T12:37:03Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
