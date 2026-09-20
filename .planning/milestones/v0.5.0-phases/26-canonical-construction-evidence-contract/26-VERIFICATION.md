---
phase: 26-canonical-construction-evidence-contract
verified: 2026-09-15T21:34:00Z
status: passed
score: 24/24 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 10
  total: 10
  not_honored: []
human_verification: []
---

# Phase 26: Canonical Construction & Evidence Contract Verification Report

**Phase Goal:** Maintainers have one atomic topology-construction boundary and reproducible comparison evidence before new runtime semantics depend on either.
**Verified:** 2026-09-15T21:34:00Z
**Status:** passed
**Re-verification:** Yes — after one code-review gap-fix loop

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | One claimed Phase 26 Beads item governs the work without duplicates. | ✓ VERIFIED | `fast_fsm-qj4` remained assigned to `radioflyer28`, priority 1, and `in_progress` through execution and review. |
| 2 | Direct and batch registration use one immutable-request normalize/validate/off-table-merge/publish transaction. | ✓ VERIFIED | `_TransitionRequest` and `_apply_transition_requests_owned()` are the single machine-owned seam; graph invariant tests pass in pure and native modes. |
| 3 | Empty/singleton/malformed request collections preserve version and topology guarantees. | ✓ VERIFIED | Request collection, no-op, malformed-input, and direct/batch contract tests pass; native malformed-request validation reaches the explicit fail-closed error. |
| 4 | Duplicate, same-slot, cross-slot, priority-conflict, and idempotence behavior remains atomic and deterministic. | ✓ VERIFIED | Phase request atomicity/idempotence/property tests pass; the canonical transaction still publishes through `_commit_transition_plan()` once. |
| 5 | Interrupted construction publishes nothing and releases ownership; singleton runtime lookup remains disconnected from request carriers. | ✓ VERIFIED | Interruption/ownership and structural singleton-path tests pass. |
| 6 | Required comparator records validate semantic preflight before timing and remain bounded/allowlisted. | ✓ VERIFIED | Strict common schema tests and all three live child records pass. |
| 7 | Flat cycle and false-guard behavior are required in every lane. | ✓ VERIFIED | Live 0.4.0/2.5.0/3.2.1 records agree on cycle states and one guard call, unchanged `idle`, zero transition callbacks. |
| 8 | Identity, version, origin, schema, finite sample, and required-preflight contradictions fail closed. | ✓ VERIFIED | Contract tests cover each contradiction; parent comparison validates before ratios. |
| 9 | Optional unsupported capability cells are explicit and ratio-free. | ✓ VERIFIED | `final-state-rejection` reports stable `api-unavailable` cells with empty measurements/rates/ratios. |
| 10 | Ordinary tests neither import nor install competitor libraries. | ✓ VERIFIED | Fixture-only contract tests and static dependency/execution graph assertions pass. |
| 11 | Child and parent output is canonical allowlisted JSON without raw environment or exception payloads. | ✓ VERIFIED | Schema validators, redacted process failures, stdout/output equivalence, and full suite pass. |
| 12 | Every retained sync/async factory, helper, dictionary, declarative, clone, and builder adapter reaches the canonical request seam. | ✓ VERIFIED | Adapter source guards plus graph/builder/async tests pass. |
| 13 | Adapter syntax, State identity, condition references, async classification, error timing, and row context remain intact. | ✓ VERIFIED | Existing suites pass; review regression proves an early failing dictionary row reports its own index. |
| 14 | Early/late failures through retained adapters publish no valid prefix. | ✓ VERIFIED | Factory/helper/builder rollback tests pass across focused and full sequential suites. |
| 15 | Failed builder attempts remain completely repairable; successful builds remain cached. | ✓ VERIFIED | Builder failure/fingerprint/repair/cache matrix passes. |
| 16 | Whole-machine factory candidates do not escape on failure; direct mutations stay internally atomic. | ✓ VERIFIED | Candidate-local construction and transaction publication tests pass. |
| 17 | Clone reconstruction preserves collaborator identity but owns independent topology containers. | ✓ VERIFIED | Clone identity/isolation/concurrency tests pass in pure source; native behavioral construction tests pass. |
| 18 | Human approval preceded external lock generation and names both exact versions plus upstream. | ✓ VERIFIED | Plan 26-04 records the user's exact approval of 2.5.0 and 3.2.1 from `fgmacedo/python-statemachine`. |
| 19 | Approval scope remains limited to the two adjacent comparison dependencies. | ✓ VERIFIED | Project groups and `uv.lock` contain neither comparator; only adjacent script locks carry the approved dependency. |
| 20 | Adjacent uv locks reproduce exact 2.5.0 and 3.2.1 children with matching runtime identity. | ✓ VERIFIED | Lock contract tests and live observation report exact requested/resolved versions and distinct absolute origins. |
| 21 | Required semantic contradictions terminate comparison; optional unsupported cells remain honest. | ✓ VERIFIED | Parent report tests and live observation pass. |
| 22 | `task benchmark-compare` is the sole maintained manual entry point and persists only to explicit `--output`. | ✓ VERIFIED | Taskfile/static wrapper and stdout/output-path tests pass; no implicit result file is named or created. |
| 23 | Ordinary dependencies, CI, quality, release evidence, and readiness remain comparator-free and ratio-independent. | ✓ VERIFIED | Static graph tests and the comparator-free project lock pass. |
| 24 | Counts, child time, incremental output, launch errors, and pipe-holding descendants are bounded; the phase bead closes only after this verifier. | ✓ VERIFIED | Flood, timeout, missing-executable, detached-descendant regressions pass; closure is performed after this report. |

**Score:** 24/24 must-haves verified (0 behavior-unverified)

### Required Artifacts

| Artifact | Status | Details |
| --- | --- | --- |
| `src/fast_fsm/core.py` | ✓ VERIFIED | Frozen/slotted request carrier, one canonical preparation/publication seam, adapter/clone/builder routing, and row-specific diagnostic contexts. |
| `benchmarks/comparison/common.py` | ✓ VERIFIED | Strict bounded child/scenario schema, semantic required values, finite measurement validation, and canonical JSON. |
| Three child adapters and two adjacent locks | ✓ VERIFIED | Exact isolated runtime identity and semantic preflight; no comparator enters project dependencies. |
| `benchmarks/comparison/run_comparison.py` | ✓ VERIFIED | Lock-frozen child commands, neutral working directories, hard resource bounds, redacted failure handling, and canonical observational report. |
| `Taskfile.yml` and `benchmarks/benchmark.py` | ✓ VERIFIED | One manual maintained task and a thin compatibility delegate, disconnected from required automation. |
| Phase test suites | ✓ VERIFIED | Active topology, builder, async, ownership, native-boundary, benchmark-contract, and review regressions. |

### Key Link Verification

| From | To | Via | Status |
| --- | --- | --- | --- |
| Direct/batch/helper/factory adapters | `_apply_transition_requests_owned()` | immutable `_TransitionRequest` tuples | ✓ WIRED |
| Canonical transaction | `_commit_transition_plan()` | complete prepared tuple after validation | ✓ WIRED |
| `FSMBuilder` staging | private candidate | fresh endpoint-bound request copies | ✓ WIRED |
| Clone snapshot | independent clone topology | canonical reconstruction transaction | ✓ WIRED |
| Manual Taskfile command | strict parent | `uv run python benchmarks/comparison/run_comparison.py` | ✓ WIRED |
| Strict parent | exact children | `uv run --locked` project/script commands | ✓ WIRED |
| Child records | report ratios | identity/schema/preflight validation first | ✓ WIRED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full pure-source regression | `uv run pytest tests/ -x -q` | 100% complete, exit 0 | ✓ PASS |
| Construction/evidence focused suite | graph, builder, advanced-functionality, and comparator contract tests | all passed | ✓ PASS |
| Performance-path shape | selected singleton/direct/topology performance tests | all passed | ✓ PASS |
| Exact live observation | `task benchmark-compare -- --warmup 10 --operations 100 --samples 1` | exact versions/origins and semantic matrix accepted | ✓ PASS |
| Static quality and typing | Ruff, mypy, advisory ty, slots policy | all passed | ✓ PASS |
| Source and dependency state | `task pure-source-check`; `uv lock --check` | `core.py` origin; lock current | ✓ PASS |
| Native compatibility | `task build-check` plus five behavior-level compiled construction tests | build/smoke and tests passed | ✓ PASS |
| Native cleanup | remove two generated core shadows; rerun pure-source check | pure-source origin restored | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
| --- | --- | --- | --- |
| BUILD-04 | 26-01, 26-03 | ✓ SATISFIED | One immutable request transaction across retained construction paths, with pure/native proof. |
| BUILD-05 | 26-01, 26-03 | ✓ SATISFIED | Atomic failure, builder retryability, independent clone topology, ownership recovery. |
| PERF-05 | 26-02, 26-04, 26-05 | ✓ SATISFIED | Approved exact adjacent locks, runtime identity, strict semantics-before-timing, live observation. |
| PERF-06 | 26-02, 26-05 | ✓ SATISFIED | Manual observation only, no normal dependency/CI/release edge, no ratio gate. |

Every Phase 26 requirement is claimed by plans and marked complete in `REQUIREMENTS.md`; no orphaned or unverified requirement remains.

### Test Quality Audit

| Test Area | Linked Requirements | Active | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- |
| Graph/ownership construction | BUILD-04, BUILD-05 | Yes | No | identity/behavior/concurrency | ✓ PASS |
| Builder/factory/async construction | BUILD-04, BUILD-05 | Yes | No | behavior/fingerprint/repair | ✓ PASS |
| Comparison contract | PERF-05, PERF-06 | Yes | No — required values are independent constants | schema/behavior/static graph | ✓ PASS |
| Live exact observation | PERF-05 | Manual and executed | No | runtime identity and semantic values | ✓ PASS |

No requirement-linked test is disabled. Platform-specific detached-descendant coverage is skipped only on Windows; it executed on the verification host.

### Code Review Closure

The standard-depth review initially found three warnings: inaccurate `from_dict()` row attribution, a non-locked Fast FSM observation lane, and incomplete subprocess launch/pipe handling. All were fixed test-first. Final native verification then found one mypyc annotation boundary that intercepted the explicit malformed-request error; widening the private tuple annotation restored pure/native parity. The clean review report records zero remaining findings.

### Anti-Patterns Found

No unresolved blocker/warning finding, comparator dependency leak, ratio threshold, implicit benchmark artifact, raw child diagnostic, placeholder, or generated native shadow remains.

## Human Verification

N/A — this is a maintainer construction/evidence foundation phase. Its behavioral criteria are programmatic. The one required human supply-chain judgment was explicitly completed before lock generation and is recorded in Plan 26-04.

## Gaps Summary

**No gaps found.** Phase 26 achieved its goal and all four requirements.

---

_Verified: 2026-09-15T21:34:00Z_
_Verifier: Codex inline fallback for gsd-verifier (subagent dispatch restricted)_
