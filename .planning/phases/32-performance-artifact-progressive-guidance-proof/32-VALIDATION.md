---
phase: 32
slug: performance-artifact-progressive-guidance-proof
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-19
---

# Phase 32 — Validation Strategy

> Per-phase feedback and evidence contract. Plan/task IDs will be populated after planning.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 8.4.1; Sphinx doctest |
| Config file | `pyproject.toml`, `docs/conf.py` |
| Quick run command | `uv run pytest tests/test_artifact_conformance.py tests/test_performance_benchmarks.py tests/test_drone_failsafes_example.py tests/test_readme_examples.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |
| Estimated runtime | Measure on this host; installed wheel/native evidence runs separately. |

## Sampling Rate

- After each task commit, run the relevant focused file(s) from the map below.
- After each plan wave, run the full suite and, if docs changed, `task docs-check` and `task docs-test`.
- Before phase verification, run the full suite, mypy, advisory ty, fresh installed artifact parity, and the installed compiled performance floor.
- Heavy wheel-build and hosted-matrix runs are phase-gate evidence, not per-edit feedback.

## Per-Requirement Verification Map

| Requirement | Automated proof | Wave 0 | Status |
|---|---|---|---|
| PERF-01 | `tests/test_performance_benchmarks.py`; `task release-installed-performance-check` keeps ≥200,000/s fresh native floor | Existing harness | ⬜ pending |
| PERF-02 | Pure/native direct-lookup and topology-invariance regression tests in `tests/test_performance_benchmarks.py` | Add missing structural assertions | ⬜ pending |
| PERF-03 | Scenario inventory, environment labels, finite medians and local-work counts in benchmark tests | Add scenario tests | ⬜ pending |
| PERF-04 | Oracle required-value/mutation tests, exact-origin source/native and installed-wheel parity, local release-candidate proof | Add finality, self-mode, and rejection oracle rows | ⬜ pending |
| DOC-01 | `tests/test_drone_failsafes_example.py` plus runnable script | Add progressive semantic beats | ⬜ pending |
| DOC-02 | README/Sphinx ordering checks, `task docs-check`, `task docs-test` | Add hierarchy checks | ⬜ pending |
| DOC-03 | Migration replacement and timing checks for all four deprecated helpers | Add migration checks | ⬜ pending |
| DOC-04 | Executable paired semantic examples and doc regressions | Add comparison checks | ⬜ pending |

## Wave 0 Requirements

- Add missing oracle scenarios and independent mutation tests before declaring artifact parity.
- Add benchmark reporter scenario tests before descriptive performance evidence is accepted.
- Add drone and docs regression tests before tutorial rewrite is considered complete.
- Existing pytest, Sphinx, and artifact infrastructure require no new dependency.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Hosted cross-platform release matrix, if publication is later authorized | PERF-04 | Local candidate proof is explicitly non-authorizing | Follow release workflow on published artifacts; do not label current local candidate as a release. |

## Validation Sign-Off

- [ ] Every plan task has an automated verify step or explicit Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Wave 0 closes missing test references.
- [ ] No watch-mode flags.
- [ ] Feedback latency is measured and bounded in the executed plan summaries.
- [ ] `nyquist_compliant: true` is set after validation.

**Approval:** pending
