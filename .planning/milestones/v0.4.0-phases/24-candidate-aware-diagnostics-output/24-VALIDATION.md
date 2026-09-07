---
phase: 24
slug: candidate-aware-diagnostics-output
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-07
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `FAST_FSM_BUILD_MODE=pure uv run --offline pytest tests/test_graph_invariants.py tests/test_validation.py tests/test_visualization.py tests/test_diagnostic_contracts.py tests/test_mypyc_guard.py -k 'priority or candidate or diagnostic or validation or visualization or adjacency or path or shadow' -x -q` |
| **Full suite command** | `FAST_FSM_BUILD_MODE=pure task test` |
| **Estimated runtime** | ~90 seconds (environment/cache dependent) |

---

## Sampling Rate

- **After every task commit:** Run the quick command above.
- **After every plan wave:** Run the full pure source suite, preserving the
  native-shadow cleanup/preflight boundary.
- **Before `$gsd-verify-work`:** Run pure-source preflight, Ruff, mypy, ty,
  slots policy, focused pure diagnostics, and fresh compiled core smoke/probes.
- **Max feedback latency:** 120 seconds for focused verification.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | DIAG-01 | T-24-01, T-24-02, T-24-03 | Snapshot carries scalar priority, guard presence, and only the narrow static-unconditional proof; candidate groups are never inferred by running guards. | unit/integration | focused graph-invariant and validation command from Plan 24-01 | ✅ | ⬜ pending |
| 24-01-02 | 01 | 1 | DIAG-01 | T-24-02, T-24-03, T-24-04 | Strictly increasing priorities are deterministic; malformed priorities and proved/possible shadowing remain distinct budgeted report categories. | unit/boundary | focused validation command from Plan 24-01 | ✅ | ⬜ pending |
| 24-02-01 | 02 | 2 | DIAG-02 | T-24-06, T-24-08 | Sparse/dense adjacency, transition matrices, counts, and generated paths retain one priority-bearing record/step per candidate. | unit/boundary | focused diagnostic-contract and validation command from Plan 24-02 | ✅ | ⬜ pending |
| 24-02-02 | 02 | 2 | DIAG-02 | T-24-05, T-24-06, T-24-07, T-24-08 | JSON, diagrams, and both Markdown families preserve candidate identity under existing escaping, one-capture, and budget contracts. | integration/golden | focused visualization, validation, and diagnostic-contract command from Plan 24-02 | ✅ | ⬜ pending |
| 24-03-01 | 03 | 3 | DIAG-01, DIAG-02 | T-24-09, T-24-10, T-24-11, T-24-12 | Structural and real-behavior probes prove the snapshot-to-output contract in pure and freshly compiled core. | static/pure/native | pure-source preflight plus focused pure/native command from Plan 24-03 | ✅ | ⬜ pending |
| 24-03-02 | 03 | 3 | DIAG-01, DIAG-02 | T-24-09, T-24-11, T-24-12 | Full quality gates and recoverable native-shadow handling finish with a documented clean pure-source origin. | full regression | Ruff, mypy, ty, slots, full pure suite, fresh compiled probe, cleanup, and final preflight from Plan 24-03 | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Add focused cases to the
active graph-invariant, validation, visualization, diagnostic-contract, and
mypyc-guard suites; do not create a duplicate budget suite.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verification.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 is unnecessary; existing infrastructure covers DIAG-01 and DIAG-02.
- [x] No watch-mode flags.
- [x] Feedback latency < 120 seconds for focused checks.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved — final task IDs, threats, waves, and pure/native commands reconciled with the PLAN.md files
