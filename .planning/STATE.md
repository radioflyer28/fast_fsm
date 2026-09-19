---
gsd_state_version: 1.0
milestone: v0.5.0
milestone_name: Explicit Flat-FSM Semantics (Planned)
current_phase: 31
current_phase_name: Semantic Diagnostics & Visualization
status: planning
stopped_at: Phase 31 context gathered
last_updated: "2026-09-19T17:20:40.696Z"
last_activity: 2026-09-19
last_activity_desc: Phase 30 complete, transitioned to Phase 31
state_head: c0b61744f305a6db15d848d45eb77401bf30a3ed
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 21
  completed_plans: 21
  percent: 71
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-15)

**Core value:** Preserve direct O(1) singleton dispatch and its installed compiled ≥200,000 operations/sec floor while adding explicit, finite flat-FSM semantics.
**Current focus:** Phase 31 — Semantic Diagnostics & Visualization

## Current Position

Phase: 31 — Semantic Diagnostics & Visualization
Plan: Not started
Status: Ready to plan
Last activity: 2026-09-19 — Phase 30 complete, transitioned to Phase 31

Progress: [███████░░░] 71%

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
| 29 | 4 | - | - |
| 30 | 6 | - | - |

**Recent Trend:** Phases 26–30 are complete and independently verified; Phase 31 is ready for discussion and planning.
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
| Phase 29 P03 | 8min | 1 tasks | 5 files |
| Phase 29 P04 | 11min | 2 tasks | 4 files |
| Phase 30 P01 | 9 min | 2 tasks | 7 files |
| Phase 30 P02 | 43 min | 2 tasks | 7 files |
| Phase 30 P03 | 6 min | 2 tasks | 5 files |
| Phase 30 P04 | 14 min | 2 tasks | 5 files |
| Phase 30 P05 | 11 min | 2 tasks | 9 files |
| Phase 30 P06 | 36 min | 3 tasks | 6 files |

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
- [Phase 29]: Only approved selector eligibility seams convert TransitionRejected; lifecycle and observer signals remain ordinary failures.
- [Phase 29]: Phase 29 API docs expose the bounded rejection contract without adding tutorial material owned by Phase 32.
- [Phase 29]: Phase 29: Classify expected rejection dynamically only after one of the six selector eligibility hooks raises, preserving interpreted subclasses under mypyc without success-path work.
- [Phase 30]: Declarative builder rows are derived afresh at build time and joined with explicit rows in the one canonical transaction. — Preserves reusable builder staging, canonical validation, and one publication seam.
- [Phase 30]: Decorator guards remain state-owned and selected-entry matching includes internal mode. — Prevents double guard evaluation while preserving exact internal/external lifecycle behavior.
- [Phase 30]: Declarative async preflight follows exact staged-owner applicability; foreign source constraints cannot reclassify or reject a builder.
- [Phase 30]: Batch transition rows carry optional internal mode as their eighth field after timing and publish through the canonical request transaction.
- [Phase 30]: Deprecated construction boundaries warn once before delegating to private compatibility workers.
- [Phase 30]: Existing stubs and root exports remain unchanged because they already retain the v0.5.x compatibility signatures.
- [Phase 30]: Topology dictionaries emit internal only as JSON true; missing or exact false remains external.
- [Phase 30]: Clone replays canonical requests into independent mutable containers; snapshot v1 remains state-only and receiver-owned.
- [Phase 30]: Focused guides lead with FSMBuilder; direct construction stays advanced and from_dict stays the serialized-topology adapter.
- [Phase 30]: Phase 30: Keep deprecated construction warnings in interpreted cold wrappers so pure and mypyc builds attribute them to the same caller.
- [Phase 30]: Phase 30: Allow interpreted StateMachine subclasses in mypyc because retained classmethod factories preserve subclass result types.

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

Last session: 2026-09-19T17:20:40.496Z
Stopped at: Phase 31 context gathered
Resume file: .planning/phases/31-semantic-diagnostics-visualization/31-CONTEXT.md

- Phase 30's full suite, verifier, review, security, and native parity gates
  passed; the former offline-cache blocker is closed.

- Next: discuss, plan, and execute Phase 31, then continue through Phase 32
  and milestone audit/completion under the milestone workflow.
