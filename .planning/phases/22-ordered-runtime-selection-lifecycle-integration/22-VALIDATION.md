---
phase: 22
slug: ordered-runtime-selection-lifecycle-integration
status: draft
nyquist_compliant: false
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
| **Quick run command** | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_graph_invariants.py tests/test_transition_lifecycle.py tests/test_async.py -k 'priority or candidate or selection or lifecycle' -x -q` |
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
| 22-01-01 | 01 | 1 | SEL-01, SEL-03 | T-22-01 | Ordered candidate scan stops at first fully eligible sync winner before lifecycle | unit/property | `uv run pytest tests/test_graph_invariants.py tests/test_transition_lifecycle.py -k 'priority or candidate or selection or lifecycle' -x -q` | ✅ | ⬜ pending |
| 22-01-02 | 01 | 1 | SEL-02 | T-22-02 | Async guard evaluation is sequential; exception/cancellation never evaluates a lower priority | async unit | `uv run pytest tests/test_async.py -k 'priority or candidate or selection or cancellation' -x -q` | ✅ | ⬜ pending |
| 22-02-01 | 02 | 2 | SEL-03, SEL-04 | T-22-03 | One selected priority reaches result/history/trace; exhaustion sends one truthful failure | lifecycle/unit | `uv run pytest tests/test_transition_lifecycle.py tests/test_listeners.py -k 'selection or priority or failure' -x -q` | ✅ | ⬜ pending |
| 22-02-02 | 02 | 2 | SEL-01..04 | T-22-04 | Typed singleton/group dispatch remains native-safe and preserves O(1) singleton lookup | native/performance | `FAST_FSM_BUILD_MODE=compiled uv run pytest tests/test_mypyc_guard.py tests/test_performance_benchmarks.py -k 'priority or candidate or selection or constant_lookup' -x -q` | ✅ | ⬜ pending |

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test framework, fixture, or service setup is required.

## Manual-Only Verifications

All Phase 22 behaviors have automated verification. The Phase 25 drone example remains the later human-facing integration check.

## Validation Sign-Off

- [x] Existing infrastructure covers the required sync, async, lifecycle, native, and performance seams.
- [ ] Planner task IDs and commands reconciled against the final PLAN.md files.
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify.
- [ ] No watch-mode flags.
- [x] Feedback latency target is under 60 seconds for focused checks.
- [ ] `nyquist_compliant: true` set after plan validation.

**Approval:** draft — awaiting plan-checker reconciliation
