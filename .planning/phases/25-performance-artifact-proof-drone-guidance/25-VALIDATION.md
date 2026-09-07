---
phase: 25
slug: performance-artifact-proof-drone-guidance
status: validated
nyquist_compliant: true
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
| **Quick run command** | `uv run pytest tests/test_priority_selection.py tests/test_performance_benchmarks.py tests/test_artifact_conformance.py tests/test_drone_failsafes_example.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
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
| 25-01-01 | 01 | 1 | PERF-01 | T-25-01 | Ordered candidate insertion does one local linear scan, preserves duplicate/conflict atomicity, and never sorts at dispatch. | unit/structural | `UV_OFFLINE=1 FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_priority_selection.py tests/test_performance_benchmarks.py -x -q` | ✅ | ✅ green |
| 25-01-02 | 01 | 1 | PERF-01 | T-25-01 | Representative depth/winner/exhaustion records prove local guard work and no unrelated topology scan; observations carry environment metadata. | benchmark characterization | `UV_OFFLINE=1 task benchmark` | ✅ | ✅ green |
| 25-02-01 | 02 | 2 | PERF-02 | T-25-02, T-25-03 | Source, pure wheel, and compiled wheel share required priority scenario values and reject malformed or incomplete evidence. | unit | `UV_OFFLINE=1 FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_artifact_conformance.py -x -q` | ✅ | ✅ green |
| 25-02-02 | 02 | 2 | PERF-02 | T-25-02, T-25-03 | Parent-side artifact validation and Taskfile wiring receive fast feedback before any wheel build or clean-origin proof. | unit/task inspection | `UV_OFFLINE=1 FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_installed_artifacts.py -m "not integration" -x -q && task --summary release-installed-artifacts-check && task --summary release-installed-performance-check` | ✅ | ✅ green |
| 25-02-03 | 02 | 2 | PERF-02 | T-25-02, T-25-03 | Clean source origin is compared to each fresh installed artifact; compiled provenance and three-sample median remain at least 200,000 ops/sec. | installed-artifact | `UV_OFFLINE=1 task release-installed-artifacts-check && task release-installed-performance-check && task release-baseline-check` | ✅ | ✅ green |
| 25-03-01 | 03 | 3 | DOC-01 | T-25-04 | A controller sends exactly one `telemetry_tick`; priority guards select the winner and bound entry callbacks alone issue the selected aircraft command. | example/unit | `UV_OFFLINE=1 FAST_FSM_BUILD_MODE=pure uv run pytest tests/test_drone_failsafes_example.py -x -q && uv run python examples/drone_failsafes.py` | ✅ | ✅ green |
| 25-03-02 | 03 | 3 | PERF-01, DOC-01 | T-25-04 | Public and maintainer guidance describe singleton O(1) versus local grouped O(k), preserve the simulation disclaimer, and render the runnable example. | docs/lint | `UV_OFFLINE=1 task docs-check && task docs-test && uv run pytest tests/test_readme_examples.py tests/test_drone_failsafes_example.py -x -q` | ✅ | ✅ green |
| 25-04-01 | 04 | 4 | PERF-02 | T-25-G02 | Superseded security policy; constrained baseline refresh/byte preservation remains verified in Plan 05. | release-evidence integration | `task release-baseline-check` | ✅ | ✅ green |
| 25-04-02 | 04 | 4 | PERF-02 | T-25-G03, T-25-G04 | Full release quality, clean source/pure/compiled parity, native loader provenance, and the three-sample compiled singleton median preserve strict gates. | release integration | `task release-readiness-check` | ✅ | ✅ green |
| 25-05-01 | 05 | 5 | PERF-02 | T-25-G01, T-25-G02, T-25-SC | `uv.lock` with `uv sync --locked` governs resolution; a protected baseline validates an allowlisted candidate before changing bytes. | unit/release-evidence integration | `uv run pytest tests/test_release_evidence.py -x -q && task release-baseline-check` | ✅ | ✅ green |
| 25-05-02 | 05 | 5 | PERF-02 | T-25-G03 | The complete normal-environment readiness proof retains source/pure/compiled provenance and performance gates. | release integration | `task release-readiness-check` | ✅ | ✅ green |

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
- [x] `nyquist_compliant: true` set in frontmatter after execution evidence is green.

**Approval:** approved 2026-09-07; re-audited after Plan 05 policy correction.

## Validation Audit 2026-09-07

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

The Nyquist audit executed the focused behavioral suite, documentation/benchmark tasks,
clean-source proof, read-only baseline check, fresh pure/compiled wheel parity proof,
installed compiled singleton gate, and the full release gate with pinned offline uv 0.12.6.
The sequential suite result was 1,799 passed and 6 expected skips; the fresh installed
compiled singleton median was 662,758.70 ops/sec, above the fixed 200,000 ops/sec floor.
Wave 4's existing automated evidence routes were added to this map; no implementation or
test change was required.

## Validation Audit 2026-09-07 (Plan 05)

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Plan 05 has focused adversarial coverage for guarded baseline refreshes, durable-drift
rejection, byte preservation, and relative/absolute protected-path routing. The normal
locked `uv` workflow was then proved by the successful `task release-baseline-write`,
`task release-baseline-check`, and complete `task release-readiness-check` run: 1,806
passed of 1,812 collected, six expected skips, zero failures, and all release artifact
and performance checks passed. No automated validation gap remains.
