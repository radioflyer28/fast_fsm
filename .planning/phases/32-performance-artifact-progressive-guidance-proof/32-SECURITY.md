---
phase: 32
slug: performance-artifact-progressive-guidance-proof
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-19
---

# Phase 32 — Security

> ASVS L1 audit of the 20 threats authored in the six Phase 32 plans. `threats_open` counts only open threats at or above the configured high-severity block threshold.

## Trust Boundaries

| Boundary | Data crossing | Control |
|---|---|---|
| Wheel/native artifact → evidence parent | Archive and child JSON | Exact archive snapshot, contained loader/origin, fixed typed semantic oracle |
| Local candidate → release claim | Evidence metadata | `local-non-authorizing`, `authorizes_release=false`; no publication step |
| Telemetry facts → FSM → aircraft port | Simulated sample and commands | One FSM-owned `telemetry_tick`; commands only on committed entry |
| Benchmark/docs output → user claim | Timing and copied examples | Environment labels, fixed floor separate from descriptive costs, executable examples |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Evidence / residual | Status |
|---|---|---|---|---|---|---|
| T-32-01 | Tampering | Collector record | high | mitigate | Typed fixed `required_values` and rehashed-mutation tests in `tools/artifact_conformance.py`, `tests/test_artifact_conformance.py` | closed |
| T-32-02 | Spoofing | Installed origin | high | mitigate | `verify_installed_wheel()` checks archive mode, contained loader and runtime origin before conformance | closed |
| T-32-03 | Information disclosure | Scenario JSON | medium | mitigate | Scalar allowlist and payload-sentinel tests reject leakage | closed |
| T-32-04 | Spoofing | Source/native loader | high | mitigate | Exact path, suffix, containment and build-mode assertions in installed-artifact tests and release evidence tool | closed |
| T-32-05 | Tampering | Archive/manifest | high | mitigate | Snapshot/hash checks, narrow guarded refresh and read-only baseline check | closed |
| T-32-06 | Repudiation | Local candidate | medium | mitigate | Local aggregate records non-authorizing scope and false release authorization | closed |
| T-32-07 | Denial of service | Build/probe subprocess | medium | mitigate | Installed neutral child commands have time/output caps, but `_run_checked()`, Taskfile `invoke()`, and fresh-native test build remain uncapped | open — below high threshold |
| T-32-08 | Repudiation | Timing row | medium | mitigate | Every priority and semantic row records environment label, origin/build, versions, platform, method and samples | closed |
| T-32-09 | Tampering | Native floor | high | mitigate | Separate fixed 200,000/s installed-native validator retained and passed | closed |
| T-32-10 | Denial of service | Benchmark fixture | low | accept | Maintainer-controlled finite fixtures; nonpositive inputs rejected | closed — accepted |
| T-32-11 | Tampering | Telemetry guards | high | mitigate | One FSM event and priority tests for simultaneous critical/link/battery signals | closed |
| T-32-12 | Elevation of privilege | Aircraft command callback | high | mitigate | Destination-entry callbacks and state-at-command tests; false/rejected/internal paths emit no entry command | closed |
| T-32-13 | Information disclosure | Rejection report | medium | mitigate | Fixed bounded code/status output; no sample or exception representation | closed |
| T-32-14 | Repudiation | Training claim | medium | mitigate | Script and gallery explicitly say deterministic training-only, not hardware/certified flight control | closed |
| T-32-15 | Tampering | Public snippets | medium | mitigate | Builder/semantic examples execute with exact assertions in README tests | closed |
| T-32-16 | Repudiation | Migration guidance | medium | mitigate | Tests cover four mappings and v0.5.x/v0.6.0 timing | closed |
| T-32-17 | Information disclosure | Rejection example | low | accept | Fixed payload-free example and bounded-code API | closed — accepted |
| T-32-18 | Tampering | API docs | medium | mitigate | Sphinx `testcode`/`testoutput` and runtime-focused tests pass | closed |
| T-32-19 | Repudiation | Drone tutorial | medium | mitigate | Gallery discloses training-only scope and points to smoke test | closed |
| T-32-20 | Information disclosure | Doc output | low | accept | Fixed literal codes, no caller payload | closed — accepted |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| R-32-01 | T-32-10 | Local benchmark fixtures are maintainer-controlled and bounded in sample/iteration size. | Phase 32 approved plan | 2026-09-19 |
| R-32-02 | T-32-17 | Public rejection example uses fixed payload-free literals. | Phase 32 approved plan | 2026-09-19 |
| R-32-03 | T-32-20 | Documentation output uses fixed literal codes, not user data. | Phase 32 approved plan | 2026-09-19 |

T-32-07 is **not accepted or closed**. Its residual uncapped local build/probe calls are a visible non-blocking finding under the current `security_block_on: high` policy; any later claim that *all* build/probe subprocesses are bounded requires remediation and re-audit.

## Security Audit Trail

| Audit Date | Threats Total | Closed (including accepted) | Open | Run By |
|---|---:|---:|---:|---|
| 2026-09-19 | 20 | 19 | 1 (medium, non-blocking) | GSD security auditor and orchestrator |

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted low risks are recorded above.
- [x] `threats_open: 0` at the configured high-severity block threshold.
- [x] `status: verified` set; T-32-07 remains explicitly open below threshold.

**Approval:** verified at ASVS L1 on 2026-09-19; one medium residual is not waived.
