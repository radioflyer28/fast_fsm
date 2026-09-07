---
phase: 24
slug: candidate-aware-diagnostics-output
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 24-01-01 | 01 | 1 | DIAG-01 | — | Snapshot carries scalar priority and only the narrow static-unconditional proof; candidate groups are never inferred by running guards. | unit/native | quick command plus fresh compiled probe | ✅ | ⬜ pending |
| 24-01-02 | 01 | 1 | DIAG-01 | — | Strictly increasing priorities are deterministic; malformed priorities and proven/possible shadowing remain distinct report categories. | unit | quick command | ✅ | ⬜ pending |
| 24-02-01 | 02 | 2 | DIAG-02 | — | Adjacency, paths, JSON, diagrams, and Markdown retain one priority-bearing record per candidate under existing escaping. | integration | quick command | ✅ | ⬜ pending |
| 24-02-02 | 02 | 2 | DIAG-02 | — | Candidate edges consume existing budget dimensions and exhaustion never masquerades as a complete result. | boundary | quick command | ✅ | ⬜ pending |
| 24-03-01 | 03 | 3 | DIAG-01, DIAG-02 | — | Source and compiled core agree on the snapshot/projection contract; native shadows are recoverably removed before pure verification. | pure/native regression | pure-source preflight, quick command, fresh compiled probe | ✅ | ⬜ pending |

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

- [ ] All tasks have automated verification.
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 is unnecessary; existing infrastructure covers DIAG-01 and DIAG-02.
- [ ] No watch-mode flags.
- [ ] Feedback latency < 120 seconds for focused checks.
- [ ] `nyquist_compliant: true` set in frontmatter.

**Approval:** pending
