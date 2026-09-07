---
phase: 23
slug: construction-declarative-serialization-parity
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-07
---

# Phase 23 — Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 8.4.1 with pytest-asyncio |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/test_builder.py tests/test_graph_invariants.py tests/test_state_machine_utils.py tests/test_advanced_functionality.py::TestFromDict tests/test_advanced_functionality.py::TestToDict tests/test_advanced_functionality.py::TestFromDictConditions tests/test_priority_selection.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |
| Estimated runtime | under 30 seconds for focused checks |

## Sampling Rate

- **After every task commit:** Run the directly modified focused tests.
- **After every plan wave:** Run the focused construction/parity suite.
- **Before verification:** Run pure full suite, Ruff, mypy, ty, slots policy, compiled build/import, and focused compiled parity suite.
- **Max feedback latency:** 30 seconds for task-scoped tests.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|---|
| 23-01-01 | 01 | 1 | PAR-03 | T-23-01, T-23-02, T-23-03 | Explicit references round-trip without ambiguous attachment, callable leakage, or partial publication | integration | `uv run pytest tests/test_advanced_functionality.py tests/test_graph_invariants.py -k 'FromDict or ToDict or condition_ref or priority or candidate' -x -q` | ✅ | ✅ green |
| 23-01-02 | 01 | 1 | PAR-02 | T-23-04 | Queries, snapshots, and clones preserve every candidate without entering dispatch | integration | `uv run pytest tests/test_graph_invariants.py tests/test_state_machine_utils.py tests/test_async.py tests/test_priority_selection.py -k 'priority or candidate or clone or snapshot or reachable or transition_exists or selection' -x -q` | ✅ | ✅ green |
| 23-02-01 | 02 | 2 | PAR-01, PAR-02 | T-23-05, T-23-07 | Sync declarative discovery retains every candidate and invokes only the exact selected handler | integration | `uv run pytest tests/test_builder.py tests/test_transition_lifecycle.py tests/test_priority_selection.py -k 'declarative and (priority or candidate or handler or lifecycle or ambiguous)' -x -q` | ✅ | ✅ green |
| 23-02-02 | 02 | 2 | PAR-01, PAR-02 | T-23-06, T-23-08 | Async declarative identity and plural preflight remain sequential, atomic, and retryable | integration | `uv run pytest tests/test_builder.py tests/test_async.py tests/test_transition_lifecycle.py tests/test_priority_selection.py -k 'declarative or preflight or priority or candidate or cancellation' -x -q` | ✅ | ✅ green |
| 23-03-01 | 03 | 3 | PAR-01 | T-23-09, T-23-10 | Quick/factory rows use one canonical batch and failed construction publishes no prefix | integration | `uv run pytest tests/test_builder.py tests/test_graph_invariants.py tests/test_advanced_functionality.py -k 'quick or factory or builder or priority or candidate or atomic or retry' -x -q` | ✅ | ✅ green |
| 23-03-02 | 03 | 3 | PAR-01, PAR-02, PAR-03 | T-23-11, T-23-12 | Pure/native representation, callback, serialization, declarative, and selector contracts agree | build/integration | `uv run pytest tests/test_mypyc_guard.py tests/test_builder.py tests/test_advanced_functionality.py tests/test_graph_invariants.py tests/test_state_machine_utils.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_priority_selection.py -k 'priority or candidate or declarative or condition_ref or quick or clone or snapshot or reachable or transition_exists' -x -q` | ✅ | ✅ green |

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Add focused cases in the
existing builder, async, graph, utility, lifecycle, serialization, priority,
and mypyc test modules before their corresponding implementation turns green.

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Sign-Off

- [x] All tasks have automated verification.
- [x] Sampling continuity: no three consecutive tasks without focused checks.
- [x] Wave 0 additions cover every parity seam.
- [x] No watch-mode flags.
- [x] Feedback latency is under 30 seconds.
- [x] `nyquist_compliant: true` set after execution validation.

**Approval:** reconciled 2026-09-07

## Validation Audit 2026-09-07

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Phase verification proves all PAR requirements, including native parity. The
later full release suite remained green, so every planned construction,
declarative, query, clone, and serialization seam has active automated coverage.
