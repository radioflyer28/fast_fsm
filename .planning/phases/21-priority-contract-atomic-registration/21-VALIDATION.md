---
phase: 21
slug: priority-contract-atomic-registration
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-09-06
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio and Hypothesis |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_mypyc_guard.py -x -q` |
| **Full suite command** | `FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~35 seconds quick; environment-dependent full suite |

---

## Sampling Rate

- **After every task commit:** Run the quick run command.
- **After every plan wave:** Run the full suite command.
- **Before `$gsd-verify-work`:** Full suite, Ruff, type checks, slots policy,
  and the compiled targeted suite must be green.
- **Max feedback latency:** 60 seconds for focused tests.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | PRIO-01, PRIO-02 | T-21-01 | Reject non-exact priority values before native coercion; singleton and immutable group shapes are explicit. | unit/type | `uv run pytest tests/test_graph_invariants.py tests/test_mypyc_guard.py -x -q` | ✅ | ⬜ pending |
| 21-01-02 | 01 | 1 | PRIO-01, PRIO-02 | T-21-02 | Conflicting ties and invalid candidates never partially publish. | unit/property | `uv run pytest tests/test_graph_invariants.py tests/test_hypothesis.py -x -q` | ✅ | ⬜ pending |
| 21-02-01 | 02 | 2 | PRIO-03 | T-21-03 | Batch, helper, builder, clone, and concurrent registration preserve all-or-nothing graph state. | unit/concurrency | `uv run pytest tests/test_builder.py tests/test_advanced_functionality.py tests/test_ownership_concurrency.py -x -q` | ✅ | ⬜ pending |
| 21-02-02 | 02 | 2 | PRIO-01..03 | T-21-04 | The slotted union compiles in `core.py` without widening to `Any`; existing singleton lookup evidence remains green. | static/native | `task typecheck-mypy && task typecheck-ty && uv run python tools/release_evidence.py slots-policy --json` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. The phase adds focused
coverage to existing graph-invariant, builder, ownership/concurrency, Hypothesis,
and mypyc-guard modules rather than creating a new test harness.

---

## Manual-Only Verifications

All phase behaviors have automated verification. The compiled targeted suite
must run from a freshly built compiled mode after source validation.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Focused feedback latency target is < 60 seconds
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
