---
phase: 31
slug: semantic-diagnostics-visualization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-19
---

# Phase 31 — Validation Strategy

> Draft per-phase sampling contract. The planner must replace provisional task IDs and wave labels with its final PLAN.md mapping; `$gsd-validate-phase 31` sets the validated status only after execution evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_diagnostic_contracts.py tests/test_visualization.py tests/test_validation.py tests/test_output_safety.py tests/test_logging_config.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | Focused suite under a few minutes; full and fresh-native gates are heavyweight closure checks |

---

## Sampling Rate

- **After every task commit:** Run the relevant module(s) from the focused command below and the matching semantic oracle.
- **After every plan wave:** Run the focused diagnostic suite; run blocking `task typecheck-mypy`, visible `task typecheck-ty`, and Ruff checks for changed Python files.
- **Before `$gsd-verify-work`:** Run the full sequential suite, pure/native semantic parity checks, slots policy, strict docs build and doctests if public docs changed, and restore/assert pure-source origin after native testing.
- **Max feedback latency:** Aim for 60 seconds on ordinary implementation tasks; full/native closure is the documented heavyweight exception.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 31-TBD-01 | TBD | TBD | DIAG-01, DIAG-03 | T-31-01, T-31-03 | Snapshot copies immutable final/mode scalars once without mixed epochs or budget bypass | unit + structural | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py -x -q` | ✅ existing modules | ⬜ pending |
| 31-TBD-02 | TBD | TBD | DIAG-01, DIAG-03 | T-31-01, T-31-03 | Validators and JSON distinguish explicit finals from non-final sinks while preserving topology legacy fields | unit + integration | `uv run pytest tests/test_validation.py tests/test_diagnostic_contracts.py tests/test_visualization.py -x -q` | ✅ existing modules | ⬜ pending |
| 31-TBD-03 | TBD | TBD | DIAG-02, DIAG-03 | T-31-02, T-31-03 | Both diagrams mark only true finals, label self modes, escape hostile names, and fail on exact budget exhaustion | unit | `uv run pytest tests/test_visualization.py tests/test_output_safety.py -x -q` | ✅ existing modules | ⬜ pending |
| 31-TBD-04 | TBD | TBD | DIAG-01, DIAG-03 | T-31-04 | Trace uses bounded metadata-only code/mode/finality, keeps redactor fail-closed, and matches sync/async paths | unit + async | `uv run pytest tests/test_logging_config.py tests/test_expected_rejection.py -x -q` | ✅ existing modules | ⬜ pending |
| 31-TBD-05 | TBD | TBD | DIAG-01, DIAG-02, DIAG-03 | T-31-01–T-31-04 | Cross-surface pure/native truth, source origin, docs, and full regression suite agree | integration + release closure | `uv run pytest tests/ -x -q` plus fresh-native oracle and source-origin assertion | ✅ harness exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Required Validation Matrices

1. Explicit final, non-final sink, unreachable sink, and initial final with no edge; preserve topology-only `dead_states`/`terminal` while adjusting intentional-final score and warnings.
2. Internal self versus external self, non-self external, prioritized guarded edge, and selected result/history mode.
3. Expected guard/declarative/state-permission rejection, false guard, unexpected exception, pre/post-commit failure, and `can_trigger*()` behavior.
4. Mermaid/PlantUML hostile names, trigger and condition text, exact marker placement, and stable ordering.
5. JSON serializability, additive field shape, one captured graph under late mutation, exact/one-less work and result limits, and no partial payload.
6. Trace enabled/disabled, sync/async, redactor success/failure, validated rejection code, and absence of raw payload or exception text.
7. Pure source and fresh native extension parity for the same semantic graph, with final pure-source origin restored.

---

## Wave 0 Requirements

- [ ] Extend existing focused test modules with failing Phase 31 semantic projections before implementation.
- [ ] Update old PlantUML sink-arrow expectations to explicit-final semantics and add corresponding Mermaid expectations.
- [ ] Add exact budget and hostile-text cases for every new output row/field.
- [ ] Add pure/native oracle coverage for copied snapshot final flags and edge mode.

No new test framework, dependency, or shared fixture module is required.

---

## Threat Register

| ID | Threat | Required control |
|----|--------|------------------|
| T-31-01 | Mixed graph epochs or topology-derived false completion | Copy final/mode scalars at one owned capture; keep current-state finality authoritative. |
| T-31-02 | Diagram/Markdown injection through caller-controlled text | Opaque IDs and output-language-specific escaping for every interpolated value. |
| T-31-03 | Unbounded diagnostic traversal or partial output | Reserve one shared budget before work and every emitted row/line; throw bounded exhaustion. |
| T-31-04 | Sensitive payload or exception leak through trace | Fixed metadata-only defaults, validated bounded code, safe redactor, fail-closed fallback. |

---

## Manual-Only Verifications

All Phase 31 behavior must have automated tests. Optional visual rendering may supplement, not replace, exact text and safety assertions.

---

## Validation Sign-Off

- [ ] Every final PLAN task has an automated verify route or an explicit Wave 0 dependency.
- [ ] Sampling continuity has no three consecutive tasks without automated verification.
- [ ] Wave 0 covers every missing test reference.
- [ ] No watch-mode flags.
- [ ] Ordinary-task feedback latency is proportionate to the change.
- [ ] Pure/native closure restores and reasserts the pure source origin.
- [ ] `nyquist_compliant: true` is set only after the post-execution gap audit.

**Approval:** pending.
