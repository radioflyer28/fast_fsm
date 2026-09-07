---
phase: 25
slug: performance-artifact-proof-drone-guidance
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-09-07
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache uv run pytest tests/test_priority_transitions.py tests/test_performance_benchmarks.py tests/test_artifact_conformance.py tests/test_drone_failsafes_example.py -x -q` |
| **Full suite command** | `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~180 seconds for the local suite; installed artifact proof is longer and runs as a dedicated task |

---

## Sampling Rate

- **After every task commit:** Run the task's focused pytest command and Ruff on its changed Python files.
- **After every plan wave:** Run `task typecheck-mypy`; keep `task typecheck-ty` visible as advisory, plus the relevant documentation or installed-artifact task.
- **Before `$gsd-verify-work`:** Run the full sequential suite, `task docs-check`, `task docs-test`, `task pure-source-check`, and installed pure/compiled artifact proof.
- **Max feedback latency:** 120 seconds for focused code/docs feedback; artifact proof runs as a bounded dedicated validation step.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | PERF-01 | T-25-01 | Ordered candidate insertion does one local linear scan, preserves duplicate/conflict atomicity, and never sorts at dispatch. | unit/structural | `uv run pytest tests/test_priority_transitions.py tests/test_performance_benchmarks.py -x -q` | ✅ | ⬜ pending |
| 25-01-02 | 01 | 1 | PERF-01 | T-25-01 | Representative depth/winner/exhaustion records prove local guard work and no unrelated topology scan; observations carry environment metadata. | benchmark characterization | `uv run pytest tests/test_performance_benchmarks.py -x -q && task benchmark` | ✅ | ⬜ pending |
| 25-02-01 | 02 | 2 | PERF-02 | T-25-02, T-25-03 | Source, pure wheel, and compiled wheel share required priority scenario values and reject malformed or incomplete evidence. | unit/integration | `uv run pytest tests/test_artifact_conformance.py tests/test_installed_artifacts.py -x -q -m integration` | ✅ | ⬜ pending |
| 25-02-02 | 02 | 2 | PERF-02 | T-25-02, T-25-03 | Clean source origin is compared to each fresh installed artifact; compiled provenance and three-sample median remain at least 200,000 ops/sec. | installed-artifact | `task pure-source-check && task release-installed-artifacts-check && task release-installed-performance-check` | ✅ | ⬜ pending |
| 25-03-01 | 03 | 2 | DOC-01 | T-25-04 | A controller sends exactly one `telemetry_tick`; priority guards select the winner and bound entry callbacks alone issue the selected aircraft command. | example/unit | `uv run pytest tests/test_drone_failsafes_example.py -x -q` | ✅ | ⬜ pending |
| 25-03-02 | 03 | 2 | PERF-01, DOC-01 | T-25-04 | Public and maintainer guidance describe singleton O(1) versus local grouped O(k), preserve the simulation disclaimer, and render the runnable example. | docs/lint | `task docs-check && task docs-test` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Phase work extends existing priority, performance, artifact-conformance, installed-artifact, and drone-example test seams; no framework or fixture bootstrap is required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Benchmark observations are appropriately described as environment-specific rather than as durable performance promises. | PERF-01 | Source assertions and rendered documentation show the wording, but a maintainer must judge whether a new benchmark result is being misrepresented. | Review `task benchmark` output together with the updated README, architecture guide, and maintainer policy; confirm no fixed throughput claim replaces the installed compiled floor. |
| The educational drone example is not presented as certified flight-control software. | DOC-01 | This is an audience/safety-communication judgment beyond functional behavior. | Review the example header and documentation page after `task docs-check`; confirm the simulation disclaimer remains prominent and no real-time or certification claim was introduced. |

---

## Validation Sign-Off

- [x] All planned tasks have an automated verification route using existing infrastructure.
- [x] Sampling continuity: every task has a focused automated check; no sequence of three tasks lacks feedback.
- [x] Wave 0 covers all references because no test-framework bootstrap is needed.
- [x] No watch-mode flags are used.
- [x] Focused feedback latency is bounded below 120 seconds.
- [ ] `nyquist_compliant: true` set in frontmatter after execution evidence is green.

**Approval:** approved 2026-09-07
