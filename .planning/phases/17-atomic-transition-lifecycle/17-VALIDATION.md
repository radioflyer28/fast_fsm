---
phase: 17
slug: atomic-transition-lifecycle
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-01
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_transition_lifecycle.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Pure/native command** | `uv run python tools/phase16_isolated_verify.py --suite phase17` |
| **Estimated runtime** | Targeted lifecycle suite under 30 seconds; isolated/full gate several minutes |

---

## Sampling Rate

- **After every task commit:** Run the focused lifecycle module plus the exact touched legacy module.
- **After every core/result shape change:** Run `task typecheck-mypy` and `uv run pytest tests/test_mypyc_guard.py -x -q`.
- **After every implementation wave:** Run the lifecycle/advanced/listener/builder/async/boundary selection.
- **Before `$gsd-verify-work`:** Run the Phase 17 fresh pure/compiled suite, compiled performance floor, full sequential suite, Ruff, mypy, docs, doctests, and read-only release-baseline freshness.
- **Max feedback latency:** 30 seconds for the targeted lifecycle loop.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 0 | LIFE-01–06 | T-17-01–08 | Executable scenario matrix defines order, stage, state, history, cause, observer, cancellation, and parity outcomes | unit/integration | `uv run pytest tests/test_transition_lifecycle.py -x -q` | ❌ W0 | ⬜ pending |
| 17-02-01 | 02 | 1 | LIFE-02, LIFE-04 | T-17-03, T-17-04 | Additive result contract preserves cause without disclosure and finalizes failures once | unit/API | `uv run pytest tests/test_transition_lifecycle.py tests/test_boundary_negative.py tests/test_mypyc_guard.py -x -q` | mixed | ⬜ pending |
| 17-03-01 | 03 | 2 | LIFE-01–05 | T-17-01–04 | Sync runner fails fast and commits state/history atomically | integration | `uv run pytest tests/test_transition_lifecycle.py tests/test_advanced_functionality.py tests/test_listeners.py tests/test_builder.py -x -q` | mixed | ⬜ pending |
| 17-04-01 | 04 | 3 | LIFE-01, LIFE-03–06 | T-17-02, T-17-05, T-17-06 | Async runner awaits work at matching slots and re-raises cancellation unchanged | async integration | `uv run pytest tests/test_transition_lifecycle.py tests/test_async.py -x -q` | mixed | ⬜ pending |
| 17-05-01 | 05 | 4 | LIFE-01–06 | T-17-06–08 | Fresh pure/native semantics, documentation, slots, types, and compiled throughput agree | conformance/performance | `uv run python tools/phase16_isolated_verify.py --suite phase17` | ❌ W0 | ⬜ pending |

Task identifiers are provisional until the planner writes executable plans; the planner must preserve equivalent coverage when assigning final IDs.

---

## Wave 0 Requirements

- [ ] `tests/test_transition_lifecycle.py` — authoritative sync/async stage, order, failure, cancellation, observer, history, and cause matrix for LIFE-01–06.
- [ ] `tools/phase16_isolated_verify.py` — backward-compatible Phase 17 suite and explicit overlay inventory for fresh pure/native proof.
- [ ] `tests/test_performance_benchmarks.py` — lifecycle-success selection retaining the compiled `trigger()` floor of 200,000 operations/second.
- [ ] `tests/test_mypyc_guard.py` and `tests/test_boundary_negative.py` — additive slotted result/API compatibility and hidden-cause guards.
- [ ] Rewrite contradictory expectations in `tests/test_advanced_functionality.py`, `tests/test_listeners.py`, and `tests/test_async.py` as implementation lands.

No new test framework or shared fixture module is required.

---

## Required Scenario Families

- Exact successful callback order with two registrations per collection in sync and async machines.
- Every pre- and post-commit injection point with expected stage, committed flag, current state, history cardinality, original-cause identity, later-call suppression, and one observer pass.
- Missing resolution, guard false/raise, state-permission false/raise, and declarative false/failed/invalid/raise outcomes through the same finalizer.
- Observer registration order and continuation when observers raise ordinary or cancellation exceptions, without recursion or original-cause replacement.
- Event-synchronized cancellation at async guard, source-exit callback, destination-enter callback, and declarative handler; no sleeps, shielding, or rollback.
- Legacy five-field positional `TransitionResult` construction, `raise_if_failed()` chaining, cause redaction in repr/error/logs, and unchanged force/reset/restore/direct-handler behavior.
- One scenario table executed in asserted pure and freshly compiled origins, with guard-context and callback kwargs parity.

---

## Manual-Only Verifications

All Phase 17 behaviors have automated verification. Documentation review is enforced through Sphinx warnings-as-errors, doctests, contract-memory checks, and independent goal verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or Wave 0 dependencies.
- [ ] Sampling continuity: no three consecutive tasks without automated verification.
- [ ] Wave 0 covers every missing test/harness reference.
- [ ] No watch-mode flags or timing sleeps.
- [ ] Pure and compiled origins are asserted before semantic tests.
- [ ] Compiled `trigger()` remains at or above 200,000 operations/second.
- [ ] `nyquist_compliant: true` is set only after validation audit.

**Approval:** pending
