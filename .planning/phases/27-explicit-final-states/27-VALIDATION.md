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
- **Before `$gsd-verify-work`:** Run the Sphinx warnings-as-errors API build and full sequential suite, then execute the ordered native parity gate from Plan 27-03 Task 2: build, native-origin assertion, focused compiled tests, constrained recoverable relocation of only exact preflight-reported shadows, pure-source check, exact `.py` origin assertion, and the full pure-source suite.
- **Max feedback latency:** 30 seconds for task-level checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 27-01-01 | 01 | 1 | FINAL-01, FINAL-02, FINAL-04 | T-27-01, T-27-04, T-27-09 | Exact bool validation, immutable slotted metadata, direct termination truth, and phase-item ownership | unit + structural | `bd ready --json`; `uv run pytest tests/test_final_states.py -x -q -k "state or initial or sink or transition or missing"`; slots policy | ❌ W0: `tests/test_final_states.py` | ⬜ pending |
| 27-01-02 | 01 | 1 | FINAL-01, FINAL-02 | T-27-01, T-27-04 | Construction-surface propagation, source-shape guards, public docstrings, and rendered API documentation | unit + structural + docs | `uv run pytest tests/test_final_states.py tests/test_mypyc_guard.py -x -q`; Ruff format/fix/check on task files; `task typecheck-mypy`; `task typecheck-ty`; `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` | ❌ W0: `tests/test_final_states.py` | ⬜ pending |
| 27-02-01 | 02 | 2 | FINAL-03 | T-27-02, T-27-05, T-27-06 | Canonical final-source validation rejects before publication | unit + invariant | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py -x -q -k "final_source or canonical or atomic or mixed or multi_source"`; slots policy | ❌ W0: `tests/test_final_states.py` | ⬜ pending |
| 27-02-02 | 02 | 2 | FINAL-03 | T-27-02, T-27-05, T-27-08 | Every retained adapter, builder, clone, generated, and async path inherits atomic rejection | integration + property | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_builder.py tests/test_hypothesis.py tests/test_async.py -x -q -k "final or canonical or builder or clone or emergency or bidirectional"`; Ruff format/fix/check on task files | ❌ W0: `tests/test_final_states.py` | ⬜ pending |
| 27-03-01 | 03 | 3 | FINAL-03, FINAL-06 | T-27-03, T-27-10, T-27-11 | Strict additive persistence plus derived control, clone, and async truth | integration + unit | `uv run pytest tests/test_final_states.py tests/test_graph_invariants.py tests/test_async.py -x -q -k "reset or restore or force or clone or dict or legacy or final"`; Ruff format/fix/check; mypy; ty | ❌ W0: `tests/test_final_states.py` | ⬜ pending |
| 27-03-02 | 03 | 3 | FINAL-01–FINAL-06 | T-27-12, T-27-13 | Post-commit termination and ordered pure/native/pure-source parity with recoverable exact-path cleanup | lifecycle + native + full regression | Focused Phase 27 tests; Ruff; mypy; ty; slots; lock; Sphinx `-W`; full source suite; `task build-check`; native-origin assertion; focused compiled suite; exact reported-shadow relocation; `task pure-source-check`; exact `.py` origin assertion; final `uv run pytest tests/ -x -q` | ❌ W0: `tests/test_final_states.py` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_final_states.py` — central FINAL-01 through FINAL-06 behavioral oracle.
- [ ] Extend exact dictionary-schema assertions for deterministic `final_states` output and legacy omission.
- [ ] Extend lifecycle matrices with committed termination assertions.
- [ ] Extend source/native guards for the `_final` slot and derived query shape.
- [ ] Add Google-style docstrings for the new public constructor parameter/properties and render them through the existing Sphinx API pages.

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
