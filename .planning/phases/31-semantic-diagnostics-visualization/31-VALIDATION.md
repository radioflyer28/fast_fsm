---
phase: 31
slug: semantic-diagnostics-visualization
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-19
---

# Phase 31 — Validation Strategy

> Post-execution Nyquist audit: all mapped tasks have automated, passing evidence in pure source and the focused native matrix.

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
| 31-01-01 | 01 | 1 | DIAG-01, DIAG-03 | T-31-01, T-31-03 | One snapshot captures final/mode scalars and JSON projects explicit facts without changing legacy topology | unit + integration | `uv run pytest tests/test_diagnostic_contracts.py -x -q -k "snapshot or json"` | ✅ existing module | ✅ green |
| 31-01-02 | 01 | 1 | DIAG-01, DIAG-03 | T-31-01, T-31-03 | Late mutation, ordering, and exact new-field budgets cannot yield mixed or partial output | unit + structural | `uv run pytest tests/test_diagnostic_contracts.py -x -q` | ✅ existing module | ✅ green |
| 31-02-01 | 02 | 2 | DIAG-01, DIAG-03 | T-31-01, T-31-03 | Explicit final and non-final sink reports preserve topology-only dead-state compatibility | unit | `uv run pytest tests/test_validation.py -x -q -k "dead or complete or report or export"` | ✅ existing module | ✅ green |
| 31-02-02 | 02 | 2 | DIAG-01, DIAG-03 | T-31-01 | Intentional finals no longer incur dead-end findings or scoring penalties | unit + integration | `uv run pytest tests/test_validation.py tests/test_diagnostic_contracts.py -x -q` | ✅ existing modules | ✅ green |
| 31-03-01 | 03 | 2 | DIAG-02, DIAG-03 | T-31-02, T-31-03 | Mermaid and PlantUML mark only explicit finals and distinguish self-transition modes | unit | `uv run pytest tests/test_visualization.py -x -q -k "mermaid or plantuml or final or terminal"` | ✅ existing module | ✅ green |
| 31-03-02 | 03 | 2 | DIAG-02, DIAG-03 | T-31-02, T-31-03 | Hostile text is escaped and every new diagram line is budgeted before output | unit + safety | `uv run pytest tests/test_visualization.py tests/test_output_safety.py -x -q` | ✅ existing modules | ✅ green |
| 31-04-01 | 04 | 2 | DIAG-01, DIAG-03 | T-31-04 | Sync and async trace finalizers emit the same bounded semantic fields | unit + async | `uv run pytest tests/test_logging_config.py tests/test_expected_rejection.py -x -q -k "trace or rejection"` | ✅ existing modules | ✅ green |
| 31-04-02 | 04 | 2 | DIAG-01, DIAG-03 | T-31-04 | Disabled trace stays cheap and redactor failure remains metadata-only | unit + safety | `uv run pytest tests/test_logging_config.py tests/test_expected_rejection.py -x -q` | ✅ existing modules | ✅ green |
| 31-05-01 | 05 | 3 | DIAG-01, DIAG-02, DIAG-03 | T-31-01–T-31-04 | Cross-surface runtime facts and source structure agree | structural + integration | `uv run pytest tests/test_mypyc_guard.py tests/test_final_states.py tests/test_transition_modes.py tests/test_expected_rejection.py -x -q -k "final or mode or rejection or diagnostic or trace or hot_path or snapshot"` | ✅ existing modules | ✅ green |
| 31-05-02 | 05 | 3 | DIAG-01, DIAG-02, DIAG-03 | T-31-01–T-31-04 | Pure/native oracle, origin restoration, docs, typing, slots, and full suite agree | release closure | `uv run pytest tests/ -x -q` plus Plan 31-05 native/origin gate | ✅ harness exists | ✅ green |

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

- [x] Extend existing focused test modules with Phase 31 semantic projections.
- [x] Update old PlantUML sink-arrow expectations to explicit-final semantics and add corresponding Mermaid expectations.
- [x] Add exact budget and hostile-text cases for every new output row/field.
- [x] Add pure/native oracle coverage for copied snapshot final flags and edge mode.

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

- [x] Every final PLAN task has an automated verify route or an explicit Wave 0 dependency.
- [x] Sampling continuity has no three consecutive tasks without automated verification.
- [x] Wave 0 covers every missing test reference.
- [x] No watch-mode flags.
- [x] Ordinary-task feedback latency is proportionate to the change.
- [x] Pure/native closure restores and reasserts the pure source origin.
- [x] `nyquist_compliant: true` is set only after the post-execution gap audit.

**Approval:** validated by the 2026-09-19 post-execution audit.

## Validation Audit 2026-09-19

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

DIAG-01 through DIAG-03 each have direct green tests in the mapped modules. The nine-module focused matrix passed under asserted pure and fresh native origins; the full sequential suite passed after review closure, including the installed compiled throughput floor. `31-VERIFICATION.md` independently reports 18/18 must-haves, no behavior-unverified items, and no human checks.
