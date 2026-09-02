---
phase: 18-safe-ownership-concurrency
reviewed: 2026-09-02T05:18:02Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - .github/workflows/ci.yml
  - .specify/decisions/ADR-005-safe-ownership-concurrency.md
  - .specify/memory/spr-core-api.md
  - README.md
  - docs/QUICK_START.md
  - docs/dev/architecture.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/core.py
  - tests/test_advanced_functionality.py
  - tests/test_async.py
  - tests/test_builder.py
  - tests/test_listeners.py
  - tests/test_mypyc_guard.py
  - tests/test_ownership_concurrency.py
  - tests/test_performance_benchmarks.py
  - tests/test_transition_lifecycle.py
  - tools/phase16_isolated_verify.py
  - tools/phase18_native_probe.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-09-02T05:18:02Z
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

The ownership implementation was reviewed for per-instance primitive creation,
sync/async admission, causal reentry, cancellation, exception cleanup, native
compatibility, and evidence integrity. No proven lock-release or state/history
corruption defect was found in the production ownership paths. Three verification
defects remain: concurrent regressions can hang the suite indefinitely, the CI
contract check can be satisfied by inert text, and exact-SHA evidence rejects valid
commits that have more than one CI run.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Concurrency tests have unbounded coordination waits

**Classification:** WARNING
**File:** `tests/test_ownership_concurrency.py:1078-1091`
**Issue:** Several tests await handshake events and owner tasks without a timeout
(`owner_entered.wait()`, `waiter_attempted.wait()`, `heartbeat_ran.wait()`, and
later equivalents at lines 1119-1147 and 1229). The cancellation tests in
`tests/test_transition_lifecycle.py:980`, `tests/test_transition_lifecycle.py:1066`,
and `tests/test_transition_lifecycle.py:1075` have the same pattern. If admission,
callback dispatch, or cancellation regresses before setting an event, pytest never
reaches an assertion and the sequential CI job hangs until the external Actions
timeout. That makes the tests unreliable precisely for the deadlock class they are
intended to diagnose.
**Fix:** Bound every coordination edge and task completion with `asyncio.wait_for`
(or `asyncio.timeout` where the minimum Python allows it), and cancel/gather spawned
tasks in `finally` so timeout failures do not leave pending tasks:

```python
owner = asyncio.create_task(machine.trigger_async("advance"))
try:
    await asyncio.wait_for(owner_entered.wait(), timeout=5)
    # ... assertions ...
finally:
    if not owner.done():
        owner.cancel()
    await asyncio.gather(owner, return_exceptions=True)
```

### WR-02: CI contract validation accepts comments or unrelated scalar text

**Classification:** WARNING
**File:** `tools/phase18_native_probe.py:144-168`
**Issue:** `_check_ci()` validates the ownership job by splitting raw YAML text and
checking whether required substrings occur anywhere in that slice. A required command
can be commented out, moved into an environment value, or embedded in a step name and
the validator still reports success even though Actions will never execute it. This
undermines the claimed fail-closed evidence check and allows a broken native matrix to
pass the local contract gate.
**Fix:** Parse the workflow as YAML, locate `jobs.ownership_native_probe`, and inspect
the structured `strategy.matrix.python-version` and each step's actual `run` scalar.
Require the commands in executable `run` steps and validate the native-origin and test
steps separately. If adding a YAML parser is intentionally avoided, use an existing
workflow-schema checker rather than treating raw text as executable structure.

### WR-03: Exact-SHA evidence rejects valid push-plus-PR or rerun histories

**Classification:** WARNING
**File:** `tools/phase18_native_probe.py:198-213`
**Issue:** `_assert_hosted_ci_sha()` requires `len(matching_runs) == 1`. The workflow
now runs on every branch push as well as `pull_request`, so an open PR commonly produces
two CI runs for the same head SHA. Manual dispatches and replacement runs can also add
another exact-SHA run. Even when one of those runs is a completed success with all five
required native jobs, the evidence command fails solely because another matching run
exists. This makes the final gate depend on trigger history rather than the candidate's
verified result.
**Fix:** Filter exact-SHA runs to completed successful candidates, inspect each
candidate's jobs, and accept when at least one run contains exactly one successful
ownership job for every supported Python version. If policy requires a specific event,
request the `event` field and select it explicitly instead of requiring global
uniqueness for the SHA.

---

_Reviewed: 2026-09-02T05:18:02Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
