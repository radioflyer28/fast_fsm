---
phase: 26
slug: canonical-construction-evidence-contract
status: draft
nyquist_compliant: false
wave_0_complete: false
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

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 0 | PERF-05, PERF-06 | T-26-03, T-26-05 | Strict allowlisted child identity and semantic records | unit/static | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q` | ❌ W0 | ⬜ pending |
| 26-01-02 | 01 | 1 | BUILD-04 | T-26-01 | Every adapter reaches one normalize/validate/publish transaction | unit/structural | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "adapter or topology or priority"` | ✅ partial | ⬜ pending |
| 26-01-03 | 01 | 1 | BUILD-05 | T-26-01, T-26-02 | Late failure changes no topology or reusable builder state | unit/property | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "atomic or failure or repair"` | ✅ partial | ⬜ pending |
| 26-02-01 | 02 | 2 | PERF-05 | T-26-03, T-26-05 | Exact isolated versions and origins pass untimed semantic preflight before timing | contract/integration | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q` | ❌ W0 | ⬜ pending |
| 26-02-02 | 02 | 2 | PERF-06 | T-26-04, T-26-06 | Unsupported cells have no ratio and ordinary CI never runs competitors | static/unit | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "ci or observational or unsupported"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_competitor_benchmark_contract.py` — strict child records, contradiction rejection, unsupported cells, command construction, and CI/dependency isolation.
- [ ] Adapter transaction matrix additions in `tests/test_graph_invariants.py` and `tests/test_builder.py`.
- [ ] Fixture records for Fast FSM, 2.5.0, 3.2.1, malformed identity, failed preflight, and unsupported scenarios without timing thresholds.
- Existing pytest infrastructure covers the phase; no framework installation is required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Official distribution legitimacy and adjacent lock review | PERF-05 | Package telemetry was unavailable to the automated research seam | Confirm both exact distributions and source provenance on official PyPI/upstream pages before committing generated locks. |
| Exact isolated comparison observation | PERF-05, PERF-06 | Deliberately excluded from ordinary CI because it downloads competitors and produces environment-sensitive timings | Run `task benchmark-compare`; verify both child versions/origins, all required semantic preflights, explicit unsupported cells, and no ratio for unsupported scenarios. |

---

## Validation Sign-Off

- [ ] All tasks have automated verification or explicit Wave 0 dependencies.
- [ ] Sampling continuity: no three consecutive tasks without automated verification.
- [ ] Wave 0 covers all missing test references.
- [ ] No watch-mode flags.
- [ ] Automated feedback latency stays below 120 seconds.
- [ ] `nyquist_compliant: true` is set after validation.

**Approval:** pending
