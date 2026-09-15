---
gsd_state_version: 1.0
milestone: v0.5.0
milestone_name: Explicit Flat-FSM Semantics (Planned)
current_phase: 26
current_phase_name: Canonical Construction & Evidence Contract
status: executing
stopped_at: Completed 26-01-PLAN.md
last_updated: "2026-09-15T17:58:59.202Z"
last_activity: 2026-09-15
last_activity_desc: Phase 26 execution started
state_head: a5413d3d8c9afd61681cd8fce8cccb3df1d12402
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 5
  completed_plans: 1
  percent: 0
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-15)

**Core value:** Preserve direct O(1) singleton dispatch and its installed compiled ≥200,000 operations/sec floor while adding explicit, finite flat-FSM semantics.
**Current focus:** Phase 26 — Canonical Construction & Evidence Contract

## Current Position

Phase: 26 (Canonical Construction & Evidence Contract) — EXECUTING
Plan: 2 of 5
Status: Executing plan 2 of 5
Last activity: 2026-09-15 — Phase 26 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Prior milestone plans completed: 57
- Current milestone plans completed: 0
- Current milestone execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 26–32 | 0 | TBD | — |

**Recent Trend:** v0.4.0 shipped all five phases; v0.5.0 is ready for Phase 26 planning.
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 26 P01 | 12min | 2 tasks | 3 files |

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

Last session: 2026-09-15T17:58:40.395Z
Stopped at: Completed 26-01-PLAN.md
Resume file: None

## Operator Next Steps

- Discuss or plan Phase 26: Canonical Construction & Evidence Contract.
