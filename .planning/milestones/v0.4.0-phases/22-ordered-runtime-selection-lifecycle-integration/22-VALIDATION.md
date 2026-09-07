---
phase: 22
slug: ordered-runtime-selection-lifecycle-integration
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-06
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for ordered candidate resolution and lifecycle handoff.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + Hypothesis |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_priority_selection.py tests/test_graph_invariants.py tests/test_transition_lifecycle.py tests/test_async.py -k 'priority or candidate or selection or lifecycle' -x -q` |
| **Full suite command** | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

## Sampling Rate

- **After every task commit:** Run the quick run command for the touched sync, async, lifecycle, or result behavior.
- **After every plan wave:** Run the full pure suite plus the scoped compiled/native selection gate when `core.py` changes.
- **Before `$gsd-verify-work`:** Pure and compiled selection suites must be green and source/native import origins must be explicit.
- **Max feedback latency:** 60 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | SEL-01, SEL-03 | T-22-01, T-22-02 | Ascending sync eligibility resolves one prepared winner before one lifecycle | unit/integration | `uv run pytest tests/test_priority_selection.py tests/test_transition_lifecycle.py -k 'sync and (priority or candidate or selection or lifecycle)' -x -q` | 🆕 planned | ⬜ pending |
| 22-01-02 | 01 | 1 | SEL-01, SEL-03, SEL-04 | T-22-03, T-22-04 | Rejection, terminal exception, exhaustion, singleton, projection, and can-trigger boundaries stay distinct | unit/integration | `uv run pytest tests/test_priority_selection.py tests/test_graph_invariants.py tests/test_transition_lifecycle.py -k 'priority or candidate or selection or exhaust or exception or singleton or projection' -x -q` | 🆕 planned | ⬜ pending |
| 22-02-01 | 02 | 2 | SEL-02 | T-22-05, T-22-08 | Async query/dispatch awaits one candidate stage at a time in stored order | async integration | `uv run pytest tests/test_priority_selection.py tests/test_async.py -k 'async and (priority or candidate or selection or can_trigger)' -x -q` | 🆕 planned | ⬜ pending |
| 22-02-02 | 02 | 2 | SEL-02, SEL-03, SEL-04 | T-22-06, T-22-07 | Exception/cancellation stop lower candidates; trigger finalizes once and query stays observer-free | async/lifecycle | `uv run pytest tests/test_priority_selection.py tests/test_async.py tests/test_transition_lifecycle.py -k 'async and (priority or candidate or selection or exception or cancellation or lifecycle or exhaust)' -x -q` | 🆕 planned | ⬜ pending |
| 22-03-01 | 03 | 3 | SEL-03, SEL-04 | T-22-09, T-22-12 | Selected/evaluated priority reaches one result/history/trace path without payload disclosure | lifecycle/logging | `uv run pytest tests/test_transition_lifecycle.py tests/test_logging_config.py -k 'priority or selection or history or trace or redactor or lifecycle' -x -q` | ✅ | ⬜ pending |
| 22-03-02 | 03 | 3 | SEL-01, SEL-02, SEL-03, SEL-04 | T-22-10, T-22-11 | Slotted pure/native selection preserves O(1) singleton and local O(k) group work | native/performance | `FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_mypyc_guard.py tests/test_priority_selection.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_performance_benchmarks.py -k 'priority or candidate or selection or constant_lookup or group_local_work or lifecycle_success_trigger_throughput' -x -q -s -p no:cov` | ✅ | ⬜ pending |

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test framework, fixture, or service setup is required.

## Manual-Only Verifications

All Phase 22 behaviors have automated verification. The Phase 25 drone example remains the later human-facing integration check.

## Validation Sign-Off

- [x] Existing infrastructure covers the required sync, async, lifecycle, native, and performance seams.
- [x] Planner task IDs and commands reconciled against the final PLAN.md files.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [ ] No watch-mode flags.
- [x] Feedback latency target is under 60 seconds for focused checks.
- [x] `nyquist_compliant: true` set after plan validation.

**Approval:** approved — final plan task IDs, threats, waves, and commands reconciled
