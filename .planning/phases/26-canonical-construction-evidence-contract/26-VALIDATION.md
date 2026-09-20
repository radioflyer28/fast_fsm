---
phase: 26
slug: canonical-construction-evidence-contract
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-15
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4.1 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_competitor_benchmark_contract.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run the narrow test command named by that task.
- **After every plan wave:** Run `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_competitor_benchmark_contract.py -x -q`.
- **Before `$gsd-verify-work`:** Full sequential suite, type checks, Ruff, slots policy, semantic preflights, and the manual observation command must be green.
- **Max feedback latency:** 120 seconds for automated task-level checks.

## Historical Governance Note

The original Phase 26 plan used Beads/Dolt for phase tracking. That integration was subsequently removed from this project; the historical plan and summaries retain what happened at execution time. Current Nyquist validation uses the committed plan, summary, test, and verification artifacts below and does not require a live Beads service.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | BUILD-04 | T-26-01, T-26-09 | Direct/batch requests share the immutable normalize/merge/publish transaction | unit/structural | `uv run pytest tests/test_graph_invariants.py -x -q -k "construction_request or adapter_transaction or batch_atomic or priority"` | ✅ | ✅ green |
| 26-01-02 | 01 | 1 | BUILD-04, BUILD-05 | T-26-01, T-26-02 | Repeated/interrupted/concurrent machine use is atomic and runtime selectors remain isolated | unit/structural | `uv run pytest tests/test_graph_invariants.py -x -q -k "idempotent or interrupt or concurrent or construction_hot_path"` | ✅ | ✅ green |
| 26-02-01 | 02 | 2 | PERF-05, PERF-06 | T-26-03, T-26-04, T-26-06 | Strict allowlisted Fast FSM identity and both required semantic records precede timing | unit/static | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "schema or fast_fsm or preflight or false_guard or unsupported or bounded"` | ✅ | ✅ green |
| 26-02-02 | 02 | 2 | PERF-05, PERF-06 | T-26-03, T-26-04, T-26-06 | Absolute repo-aware child commands, neutral-cwd Fast resolution, and parent contradictions are offline-testable | unit/static/integration | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "command or exact_version or origin or contradiction or subprocess or unsupported or neutral_cwd or false_guard"` | ✅ | ✅ green |
| 26-03-01 | 03 | 2 | BUILD-04, BUILD-05 | T-26-01, T-26-08, T-26-10 | Helpers/factories/dictionaries/declarative endpoints and clone reconstruction share the transaction and fail outwardly atomically | unit/matrix | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "adapter_matrix or bidirectional or emergency or quick_build or quick_fsm or from_dict or declarative or clone"` | ✅ | ✅ green |
| 26-03-02 | 03 | 2 | BUILD-04, BUILD-05 | T-26-02 | Builder request staging/cache/type remain unchanged and repairable after late failure | unit/matrix | `uv run pytest tests/test_builder.py tests/test_graph_invariants.py -x -q -k "builder and (request or atomic or failure or repair or cache or async)"` | ✅ | ✅ green |
| 26-04-01 | 04 | 3 | PERF-05 | T-26-SC | Human verifies exact official distribution releases/upstream before lock generation | blocking-human | Exact approval recorded in `26-04-SUMMARY.md` | n/a | ✅ approved |
| 26-05-01 | 05 | 4 | PERF-05, PERF-06 | T-26-05 | Adjacent locks match exact scripts and project dependency roots exclude competitors | unit/static | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "project_groups or lock or dependency"` | ✅ | ✅ green |
| 26-05-02 | 05 | 4 | PERF-05, PERF-06 | T-26-03, T-26-04, T-26-06 | Manual exact run passes both required semantics and ordinary CI/release paths remain isolated | contract/integration | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q`; `task benchmark-compare -- --warmup 10 --operations 100 --samples 1` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Plan 26-01 added direct/batch request, adjacency, idempotence, interruption, ownership, and hot-path structural cases to `tests/test_graph_invariants.py`.
- [x] Plan 26-02 added strict record, preflight, origin, bounded-output, and optional-unsupported tests to `tests/test_competitor_benchmark_contract.py`.
- [x] Plan 26-03 expanded adapter and builder transaction/clone/retry tests in `tests/test_graph_invariants.py` and `tests/test_builder.py`.
- [x] Plan 26-05 added lock/project dependency, CI/release isolation, stdout-only, and low-count observation coverage after the recorded package approval.
- [x] Fixture records cover Fast FSM, 2.5.0, 3.2.1, malformed identity, failed required preflights, and unsupported optional scenarios without timing thresholds.
- Existing pytest infrastructure covers the phase; no framework installation is required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Official distribution legitimacy and adjacent lock review | PERF-05 | A human trust checkpoint was required before generating locks | Completed; exact 2.5.0/3.2.1 upstream approval is recorded in `26-04-SUMMARY.md`. |
| Exact isolated comparison observation | PERF-05, PERF-06 | Deliberately excluded from ordinary CI because it downloads competitors and produces environment-sensitive timings | Completed again on 2026-09-20 with `task benchmark-compare -- --warmup 10 --operations 100 --samples 1`; all three lanes reported required semantic preflights and optional unsupported without ratios. |

---

## Validation Sign-Off

- [x] All implementation tasks have automated verification; the package-legitimacy task is an explicit blocking-human trust checkpoint.
- [x] Sampling continuity: no three consecutive implementation tasks lack automated verification.
- [x] Wave 0 work is assigned test-first inside Plans 26-01, 26-02, 26-03, and 26-05.
- [x] No watch-mode flags.
- [x] Focused automated feedback targets stay below 120 seconds; the deliberate external smoke run is a Phase 26 integration gate.
- [x] `nyquist_compliant: true` is set.
- [x] Historical Beads/Dolt prerequisite is not a current validation gate after the project's tracking integration was removed.

**Approval:** plan/task IDs reconciled 2026-09-15; completed test evidence audited 2026-09-20.

## Validation Audit 2026-09-20

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

The focused Phase 26 pytest matrix passed (all tests in `test_graph_invariants.py`, `test_builder.py`, and `test_competitor_benchmark_contract.py`). The exact-version manual comparator smoke passed with requested/resolved 2.5.0 and 3.2.1 lanes; both required preflight facts were present and the optional unsupported cell had no ratio. All eight implementation tasks have automated checks. Plan 26-04 is a separately completed human provenance checkpoint, not a missing automated implementation test.
