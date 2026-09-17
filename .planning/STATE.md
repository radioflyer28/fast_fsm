---
gsd_state_version: 1.0
milestone: v0.5.0
milestone_name: Explicit Flat-FSM Semantics (Planned)
current_phase: 29
current_phase_name: Expected Domain Rejection
status: executing
stopped_at: Completed 29-02-PLAN.md
last_updated: "2026-09-17T16:36:43.079Z"
last_activity: 2026-09-17
last_activity_desc: Phase 29 execution started
state_head: ccb48cd1c0ebb3d1f047f636213d4e3c5790a32d
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 15
  completed_plans: 13
  percent: 43
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-15)

**Core value:** Preserve direct O(1) singleton dispatch and its installed compiled ≥200,000 operations/sec floor while adding explicit, finite flat-FSM semantics.
**Current focus:** Phase 29 — Expected Domain Rejection

## Current Position

Phase: 29 (Expected Domain Rejection) — EXECUTING
Plan: 3 of 4
Status: Ready to execute
Last activity: 2026-09-17 — Phase 29 execution started

Progress: [████░░░░░░] 43%

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
| 27 | 3 | - | - |
| 28 | 3 | - | - |

**Recent Trend:** Phases 26–28 are complete and independently verified; Phase 29 has four checker-approved execution plans.
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 26 P01 | 12min | 2 tasks | 3 files |
| Phase 26 P02 | 17min | 2 tasks | 6 files |
| Phase 26 P03 | 16min | 2 tasks | 6 files |
| Phase 26 P04 | checkpoint | 1 task | 0 files |
| Phase 26 P05 | 18min | 2 tasks | 10 files |
| Phase 27 P01 | 5min | 2 tasks | 4 files |
| Phase 27 P02 | 9min | 2 tasks | 7 files |
| Phase 27 P03 | 18min | 2 tasks | 5 files |
| Phase 28 P01 | 7 min | 2 tasks | 6 files |
| Phase 28 P02 | 4min | 2 tasks | 3 files |
| Phase 28 P03 | 48min | 2 tasks | 4 files |
| Phase 29 P01 | 16 min | 2 tasks | 9 files |
| Phase 29 P02 | 4 min | 2 tasks | 3 files |

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
- [Phase 27]: Finality is immutable State metadata; termination is derived from the canonical current State.
- [Phase 27]: Construction surfaces forward keyword-only final while AsyncDeclarativeState inherits the same path.
- [Phase 27]: Final-source validation runs once after canonical source resolution and before prepared topology publication.
- [Phase 27]: All retained adapters delegate final-source rejection to the canonical transaction; runtime selectors remain unchanged.
- [Phase 27]: Persist explicit final names in sorted final_states metadata; omitted legacy data remains non-final.
- [Phase 27]: Keep termination derived from committed current State through controls and post-commit failures; no latch or rollback exists.
- [Phase 27]: Keep exact public final validation and raw-list copying dynamic at native boundaries to preserve source/compiled parity.
- [Phase 28]: Internal mode stays on the selected immutable entry; the external lifecycle remains the default.
- [Phase 28]: Internal commits preserve residency timing and append history only when recording is enabled.
- [Phase 28]: Primary builder staging and clone/graph replay carry the canonical internal scalar.
- [Phase 28]: Use local fake clocks and lifecycle sentinels to prove internal commits preserve residency timing without sleep-based tests.
- [Phase 28]: Keep MODE-06 pending until async and cancellation parity is proven in Plan 03.
- [Phase 28]: Phase 28: Async execution branches only on prepared.entry.internal; cancellation retains selected mode task-locally without payload injection.
- [Phase 28]: Phase 28: Fresh native proof builds from a pure origin and relocates only verified core shadows before restored pure-suite validation.
- [Phase 29]: TransitionRejected accepts only exact bounded ASCII strings and is revalidated only on the rejection path.
- [Phase 29]: Expected rejection remains a terminal TransitionResult; None remains reserved for ordinary group fallthrough.
- [Phase 29]: Failure observers remain owned by existing trigger finalization, with no rejection listener family.
- [Phase 29]: Phase 29: Async selector conversion stays at the three approved eligibility seams and reuses the existing terminal result path.
- [Phase 29]: Phase 29: Query APIs project terminal expected rejection to False without failure finalization or mutation.
- [Phase 29]: Phase 29: Condition combinators remain catch-free; rejection and cancellation propagate with their original identities.

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

Last session: 2026-09-17T16:36:42.964Z
Stopped at: Completed 29-02-PLAN.md
Resume file: 

None

- Complete the Phase 27 review/gap cycle, post-execution gates, and goal verification.
