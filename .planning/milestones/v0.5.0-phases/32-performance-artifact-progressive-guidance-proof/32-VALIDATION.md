---
phase: 32
slug: performance-artifact-progressive-guidance-proof
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-19
---

# Phase 32 — Validation Strategy

> Per-phase feedback and evidence contract, audited after all six plans and the code-review fixes.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 8.4.1; Sphinx doctest |
| Config file | `pyproject.toml`, `docs/conf.py` |
| Quick run command | `uv run pytest tests/test_artifact_conformance.py tests/test_performance_benchmarks.py tests/test_drone_failsafes_example.py tests/test_readme_examples.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |
| Estimated runtime | Focused commands are the per-task loop; full baseline/artifact runs take several minutes and are phase gates. |

## Sampling Rate

- After each task commit, run the relevant focused file(s) from the map below.
- After each plan wave, run the full suite and, if docs changed, `task docs-check` and `task docs-test`.
- Before phase verification, run the full suite, mypy, advisory ty, fresh installed artifact parity, and the installed compiled performance floor.
- Heavy wheel-build and hosted-matrix runs are phase-gate evidence, not per-edit feedback.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|---|
| 32-01-01 | 01 | 1 | PERF-04 | Oracle truth | Fixed final/sink values reject rehashed mutation | unit/artifact | `uv run pytest tests/test_artifact_conformance.py -k phase32_final -x -q` | ✅ | ✅ green |
| 32-01-02 | 01 | 1 | PERF-04 | Oracle truth | Typed required values, no payload leakage | unit/artifact | `uv run pytest tests/test_artifact_conformance.py -x -q` | ✅ | ✅ green |
| 32-03-01 | 03 | 1 | PERF-01, PERF-02 | Direct path | Singleton branch avoids unrelated work | unit/native | `uv run pytest tests/test_performance_benchmarks.py -k 'singleton or constant_lookup or priority_group_work or trace' -x -q` | ✅ | ✅ green |
| 32-03-02 | 03 | 1 | PERF-03 | Evidence provenance | Four feature-cost rows carry environment/origin | unit/CLI | `uv run pytest tests/test_performance_benchmarks.py -x -q` | ✅ | ✅ green |
| 32-04-01 | 04 | 1 | DOC-01 | Command ordering | Commands follow committed entry only | example | `uv run pytest tests/test_drone_failsafes_example.py -k 'mode or final or critical or telemetry_tick' -x -q` | ✅ | ✅ green |
| 32-04-02 | 04 | 1 | DOC-01 | Rejection terminality | False guard versus rejection has no unintended command | example | `uv run pytest tests/test_drone_failsafes_example.py -x -q` | ✅ | ✅ green |
| 32-05-01 | 05 | 2 | DOC-02, DOC-03 | N/A | Builder-first and migration timing are correct | docs | `uv run pytest tests/test_readme_examples.py -x -q` | ✅ | ✅ green |
| 32-05-02 | 05 | 2 | DOC-04 | N/A | Paired semantic examples have exact outputs | docs | `uv run pytest tests/test_readme_examples.py -x -q` | ✅ | ✅ green |
| 32-06-01 | 06 | 3 | DOC-01, DOC-02 | N/A | Tutorial/gallery agrees with tested drone behavior | Sphinx | `task docs-check` | ✅ | ✅ green |
| 32-06-02 | 06 | 3 | DOC-04 | N/A | API distinctions execute as doctests | Sphinx | `task docs-test` | ✅ | ✅ green |
| 32-02-01 | 02 | 3 | PERF-04 | Origin boundary | Pure/native/wheel modes fail closed on mismatch | unit/artifact | `uv run pytest tests/test_release_evidence.py -k 'phase32_origin or phase32_shadow or phase32_local_scope' -x -q` | ✅ | ✅ green |
| 32-02-02 | 02 | 3 | PERF-01, PERF-04 | Evidence refresh | Guarded manifest write then read-only check | release gate | `task release-baseline-check` | ✅ | ✅ green |

## Wave 0 Requirements

- [x] Oracle final/sink, self-mode, and rejection rows with independent mutation and strict type/value tests.
- [x] Labelled feature-cost reporter tests, including priority-row labels.
- [x] Drone and documentation regressions before tutorial claims.
- [x] Existing pytest, Sphinx, and artifact infrastructure used without new dependencies.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| Hosted cross-platform release matrix, if publication is later authorized | Future release workflow, outside Phase 32 | Local candidate proof is explicitly non-authorizing | Follow release workflow on published artifacts; do not label current local candidate as a release. |

## Validation Sign-Off

- [x] Every plan task has an automated verify step or explicit Wave 0 dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] Wave 0 closes missing test references.
- [x] No watch-mode flags.
- [x] Focused tests are the per-task feedback loop; multi-minute artifact builds are phase gates.
- [x] `nyquist_compliant: true` is set after validation.

**Approval:** validated 2026-09-19

## Validation Audit 2026-09-19

| Metric | Count |
|---|---:|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All eight Phase 32 requirements have automated local proof. The final read-only release baseline check passed with 2,210/2,216 pure tests, 97.81% total and 97.05% core source coverage; the fresh installed compiled floor was also verified above 200,000 transitions/s. The hosted publication matrix remains a separately authorized future workflow, not an untested Phase 32 implementation claim.
