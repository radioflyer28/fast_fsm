---
gsd_state_version: 1.0
milestone: v0.5.0
milestone_name: Explicit Flat-FSM Semantics (Planned)
current_phase: 27
current_phase_name: Explicit Final States
status: executing
stopped_at: Phase 27 context gathered
last_updated: "2026-09-15T22:15:10.930Z"
last_activity: 2026-09-15
last_activity_desc: Phase 27 execution started
state_head: 74985ade8785e57fb964e5ef2eaf5773b460a43c
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 8
  completed_plans: 5
  percent: 14
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-15)

**Core value:** Preserve direct O(1) singleton dispatch and its installed compiled ≥200,000 operations/sec floor while adding explicit, finite flat-FSM semantics.
**Current focus:** Phase 27 — Explicit Final States

## Current Position

Phase: 27 (Explicit Final States) — EXECUTING
Plan: 1 of 3
Status: Executing Phase 27
Last activity: 2026-09-15 — Phase 27 execution started

Progress: [█░░░░░░░░░] 14%

## Performance Metrics

**Velocity:**

- Prior milestone plans completed: 57
- Current milestone plans completed: 4
- Current milestone execution time: 0.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 26–32 | 0 | TBD | — |
| 26 | 5 | - | - |

**Recent Trend:** Phase 26 completed with 24/24 must-haves verified; v0.5.0 is ready for Phase 27 planning.
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 26 P01 | 12min | 2 tasks | 3 files |
| Phase 26 P02 | 17min | 2 tasks | 6 files |
| Phase 26 P03 | 16min | 2 tasks | 6 files |
| Phase 26 P04 | checkpoint | 1 task | 0 files |
| Phase 26 P05 | 18min | 2 tasks | 10 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Current milestone decisions:

- Keep v0.5.0 within explicit flat deterministic FSM semantics; no statechart, queue, scheduler, or task runtime.
- Store finality on immutable states, internal mode on immutable transition entries, and expected rejection only at pre-commit eligibility seams.
- Preserve one direct singleton entry and feature-local costs; no unrelated dispatch scans, reflection, or allocation.
- Make `FSMBuilder` primary, direct machine construction advanced, and `from_dict` the persistence adapter.
- Deprecate `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` through a compatibility cycle rather than removing them immediately.
- [Phase 26]: Copy mutable public source lists at the adapter edge so the request carrier remains frozen and slotted without forbidden dynamic assignment. — Matches the canonicalization boundary established by Phase 26 research and passes runtime audit policy.
- [Phase 26]: Keep construction ownership on existing public envelopes and keep runtime selectors and lifecycle runners unaware of the request carrier. — Preserves atomic serialization and the O(1) direct singleton dispatch boundary.
- [Phase 26]: Required flat-cycle and false-guard scenarios are contradictions when semantics differ; only the optional final-state cell may be unsupported. — Prevents fast-but-wrong behavior from entering comparison evidence.
- [Phase 26]: The comparison parent imports no FSM implementation and computes ratios only after exact record, identity, origin, and preflight validation. — Preserves process isolation and evidence trust ordering.
- [Phase 26]: Retained adapters parse their own input language and then publish one immutable request collection through the machine-owned transaction. — Preserves adapter context without duplicating semantic topology rules.
- [Phase 26]: Clones preserve State and Condition collaborator identity but reconstruct independent transition entries, groups, and tables. — Prevents topology aliasing while retaining shallow collaborator semantics.
- [Phase 26]: FSMBuilder stages immutable named requests and binds fresh endpoint-aware copies only inside a private build candidate. — Keeps failed builds retryable and avoids positional staging drift.
- [Phase 26]: Human approval covers exactly python-statemachine 2.5.0 and 3.2.1 from fgmacedo/python-statemachine for adjacent isolated benchmark locks. — Establishes the external package trust boundary without broadening project dependencies.
- [Phase 26]: Exact comparator packages live only in adjacent uv script locks; the ordinary dependency lock and required automation remain comparator-free. — Keeps competitor observations reproducible without taxing installation, CI, or release paths.
- [Phase 26]: Manual comparison children run from neutral directories with hard time/count limits and incremental per-stream output caps. — Prevents the observational tool from becoming an unbounded local resource or disclosure boundary.

### Pending Todos

None yet.

### Blockers/Concerns

- v0.3.0 remains internally closed but intentionally has no Git tag, GitHub Release, or package publication.
- Exact feature-local performance remains unmeasured until Phase 32; only the installed compiled singleton floor is durable policy.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| quick_tasks | `260404-exx-fill-callback-hook-gaps-before-transitio` | acknowledged | 2026-09-06 | v0.3.0 |
| Transition policy | Queued reentrancy and callback compensation | Future | v0.3.0 requirements | — |
| Async ownership | Cross-loop transfer and automatic callback offload | Future | v0.3.0 requirements | — |
| Tooling | Public topology snapshot v2 and possible `CompiledFuncCondition` redesign | Future | v0.3.0 requirements | — |

## Session Continuity

Last session: 2026-09-15T21:34:26.048Z
Stopped at: Phase 27 context gathered
Resume file: .planning/phases/27-explicit-final-states/27-CONTEXT.md

## Operator Next Steps

- Discuss and plan Phase 27: immutable explicit final states and O(1) termination truth.
