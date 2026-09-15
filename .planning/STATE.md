---
gsd_state_version: 1.0
milestone: v0.5.0
milestone_name: Explicit Flat-FSM Semantics
status: planning
last_updated: "2026-09-15T00:00:00Z"
last_activity: 2026-09-15
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-15)

**Core value:** Preserve direct O(1) singleton dispatch and its installed compiled ≥200,000 operations/sec floor while adding explicit, finite flat-FSM semantics.
**Current focus:** Phase 26 — Canonical Construction & Evidence Contract

## Current Position

Phase: 26 of 32 (Canonical Construction & Evidence Contract)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-09-15 — Approved requirements mapped into a seven-phase v0.5.0 roadmap

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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Current milestone decisions:

- Keep v0.5.0 within explicit flat deterministic FSM semantics; no statechart, queue, scheduler, or task runtime.
- Store finality on immutable states, internal mode on immutable transition entries, and expected rejection only at pre-commit eligibility seams.
- Preserve one direct singleton entry and feature-local costs; no unrelated dispatch scans, reflection, or allocation.
- Make `FSMBuilder` primary, direct machine construction advanced, and `from_dict` the persistence adapter.
- Deprecate `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` through a compatibility cycle rather than removing them immediately.

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

Last session: 2026-09-15
Stopped at: v0.5.0 roadmap created; Phase 26 ready to plan
Resume file: None

## Operator Next Steps

- Discuss or plan Phase 26: Canonical Construction & Evidence Contract.
