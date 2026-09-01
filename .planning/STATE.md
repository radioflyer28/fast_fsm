---
gsd_state_version: 1.0
milestone: v0.3.0
milestone_name: Reliability & Runtime Hardening
current_phase: 18
current_phase_name: Safe Ownership & Concurrency
status: executing
stopped_at: Completed 18-03-PLAN.md
last_updated: "2026-09-01T21:24:08.502Z"
last_activity: 2026-09-01
last_activity_desc: Phase 18 execution started
state_head: bedcb3178dd696e110a4a253751af7c95589aa6b
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 26
  completed_plans: 22
  percent: 50
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-29)

**Core value:** Blazing-fast, zero-overhead FSM transitions — `trigger()` ≥200,000 ops/sec and all core runtime operations O(1).
**Current focus:** Phase 18 — Safe Ownership & Concurrency

## Current Position

Phase: 18 (Safe Ownership & Concurrency) — EXECUTING
Plan: 4 of 7
Status: Ready to execute
Last activity: 2026-09-01 — Phase 18 execution started

Progress: [█████░░░░░] 50%

## Performance Metrics

**Velocity:**

- Total plans completed: 19
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 15–20 | 0 | TBD | — |
| 15 | 9 | - | - |
| 16 | 5 | - | - |
| 17 | 5 | - | - |

**Recent Trend:** Phases 15 through 17 complete; Phase 18 is ready for planning.
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 15 P01 | 16 min | 3 tasks | 7 files |
| Phase 15 P02 | 29m | 3 tasks | 10 files |
| Phase 15 P05 | 20m | 2 tasks | 1 files |
| Phase 16 P05 | 12m | 3 tasks | 5 files |
| Phase 17 P01 | 16 min | 2 tasks | 8 files |
| Phase 17 P02 | 10 min | 2 tasks | 6 files |
| Phase 17 P03 | 13 min | 2 tasks | 6 files |
| Phase 17 P04 | 11 min | 2 tasks | 5 files |
| Phase 17 P05 | 20m | 3 tasks | 11 files |
| Phase 18 P01 | 25 min | 3 tasks | 9 files |
| Phase 18 P02 | 15m | 2 tasks | 5 files |
| Phase 18 P03 | 10m | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Current milestone decisions:

- Safe defaults take precedence over unsafe pre-production callback, reentrancy, and concurrency semantics.
- Existing public symbols remain available; `core.py` remains one mypyc compilation unit with one runtime dependency.
- Runtime hardening must preserve ≥200,000 compiled `trigger()` operations/sec and O(1) core operations.
- Installed pure and compiled artifacts must prove equivalent hardened behavior before release.
- [Phase 15]: Centralized build intent in FAST_FSM_BUILD_MODE while preserving FAST_FSM_PURE_PYTHON=1 as the pure alias.
- [Phase 15]: Made release evidence fail closed and non-destructive; only CompiledFuncCondition and TransitionError are registered slots exceptions.
- [Phase 15]: Use evidence --write only for intentional regeneration; CI evidence --check remains read-only.
- [Phase 15]: Read PEP 517 build provenance from uv.lock and constrain isolated builds to exact reviewed pins.
- [Phase 15]: Mypy is blocking while ty remains an independently visible advisory gate.
- [Phase 15]: Accepted only a terminal 29-job Actions run whose head SHA equals the pushed Phase 15 branch.
- [Phase 15]: Published the authorized v0.2.3 correction additively after unchanged URL, tag-ref, and asset checks.
- [Phase 16]: Phase 16 evidence archives must explicitly overlay the complete source, test, documentation, and evidence inventory before origin proof.
- [Phase 16]: Use helper-validated evidence interfaces and record environment-labelled pure/native measurements; compiled trigger floor remains 200000 ops/sec.
- [Phase 17]: Phase 17 Wave 0: destination State.on_enter failures return committed=True at destination-enter, retain a hidden cause, and notify ordered observers exactly once.
- [Phase 17]: Phase 17 Wave 0: lifecycle evidence accepts only fresh pure or freshly compiled exports, never checkout native shadows.
- [Phase 17]: Phase 17: Resolution, guard, and state-permission failures are pre-commit results finalized exactly once at the public sync or async trigger boundary.
- [Phase 17]: Phase 17: Failure observers isolate BaseException locally, preserving ordered notification and the original result cause.
- [Phase 17]: Ordinary synchronous transitions use a fail-fast lifecycle transaction with a non-user-code commit boundary.
- [Phase 17]: Direct control operations retain best-effort callbacks through a separate runner, outside ordinary trigger finalization.
- [Phase 17]: Async callbacks share synchronous lifecycle slots; cancellation finalizes once and bare re-raises without shield or rollback.
- [Phase 17]: Published the lifecycle order and structured TransitionResult fields as one redacted public contract.
- [Phase 17]: Use asserted fresh source/native exports as Phase 17 proof; installed-wheel parity remains Phase 20.
- [Phase 17]: Keep a fixed compiled throughput floor; exact rates remain environment-labelled observations.
- [Phase 18]: Keep ordinary trigger ownership through every Phase 17 callback and failure observer.
- [Phase 18]: Give force_state, reset, and restore distinct public labels but one private _force_state_owned body.
- [Phase 18]: Retain direct-control best-effort Exception behavior while finally releasing after BaseException.
- [Phase 18]: Async machines bind permanently to their first event loop and thread.
- [Phase 18]: Causal child-task reentry is rejected before it waits on its parent-owned lock.

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 15 must make release identity and import mode trustworthy before later evidence is accepted.
- Phases 16–18 touch `core.py`; benchmark compiled and pure overhead before freezing each design.
- Phase 19 must choose deterministic diagnostic budget behavior during planning.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Transition policy | Queued reentrancy and callback compensation | Future | v0.3.0 requirements |
| Async ownership | Cross-loop transfer and automatic callback offload | Future | v0.3.0 requirements |
| Tooling | Public topology snapshot v2 and possible `CompiledFuncCondition` redesign | Future | v0.3.0 requirements |

## Session Continuity

Last session: 2026-09-01T21:24:08.379Z
Stopped at: Completed 18-03-PLAN.md
Resume file: None
