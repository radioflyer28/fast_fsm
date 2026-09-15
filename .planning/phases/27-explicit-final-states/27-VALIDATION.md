---
phase: 27
slug: explicit-final-states
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-15
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio and Hypothesis |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_transition_lifecycle.py tests/test_builder.py tests/test_async.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | Quick: <30 seconds; full: project-dependent |

---

## Sampling Rate

- **After every task commit:** Run the smallest affected Phase 27 test file plus one adjacent existing suite.
- **After every plan wave:** Run the quick command, Ruff, mypy, advisory ty, and the slots policy.
- **Before `$gsd-verify-work`:** Run the full sequential suite, `task build-check`, focused compiled tests, remove generated native shadows, then run `task pure-source-check` and the full pure-source suite.
- **Max feedback latency:** 30 seconds for task-level checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-01-01 | 01 | 1 | FINAL-01, FINAL-02, FINAL-04 | T-27-01 | Exact bool validation and immutable slotted metadata | unit + structural | `uv run pytest tests/test_final_states.py tests/test_mypyc_guard.py -x -q` | ❌ W0 | ⬜ pending |
| 27-01-02 | 01 | 1 | FINAL-03 | T-27-02 | Canonical final-source validation rejects before publication | unit + property | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_builder.py tests/test_hypothesis.py -x -q` | ❌ W0 | ⬜ pending |
| 27-02-01 | 02 | 2 | FINAL-05 | T-27-03 | Post-commit failures cannot falsify committed termination | lifecycle + async | `uv run pytest tests/test_transition_lifecycle.py tests/test_final_states.py -x -q` | ❌ W0 | ⬜ pending |
| 27-02-02 | 02 | 2 | FINAL-06 | T-27-02 | Strict additive persistence and derived control-operation truth | integration + unit | `uv run pytest tests/test_final_states.py tests/test_advanced_functionality.py tests/test_graph_invariants.py tests/test_async.py -x -q` | ❌ W0 | ⬜ pending |
| 27-03-01 | 03 | 3 | FINAL-01–FINAL-06 | T-27-01, T-27-02, T-27-03 | Pure/native parity and no hot-path regression | native + full regression | `task build-check` then focused compiled tests, cleanup, `task pure-source-check`, and `uv run pytest tests/ -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_final_states.py` — central FINAL-01 through FINAL-06 behavioral oracle.
- [ ] Extend exact dictionary-schema assertions for deterministic `final_states` output and legacy omission.
- [ ] Extend lifecycle matrices with committed termination assertions.
- [ ] Extend source/native guards for the `_final` slot and derived query shape.

No new test framework, configuration, or dependency is required.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All planned tasks have an automated verification route or Wave 0 dependency.
- [x] Sampling continuity has no three consecutive tasks without automated verification.
- [x] Wave 0 identifies every missing test artifact.
- [x] Commands use no watch-mode flags.
- [x] Task-level feedback latency target is below 30 seconds.
- [x] `nyquist_compliant: true` is set in frontmatter.

**Approval:** approved 2026-09-15
