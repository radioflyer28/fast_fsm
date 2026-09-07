---
gsd_state_version: 1.0
milestone: v0.4.0
milestone_name: Priority-Aware Guarded Transitions
current_phase: 22
current_phase_name: Ordered Runtime Selection & Lifecycle Integration
status: executing
stopped_at: Completed 22-02-PLAN.md
last_updated: "2026-09-07T00:58:16.239Z"
last_activity: 2026-09-06
last_activity_desc: Phase 22 execution started
state_head: aec0731b1d2d02014d22d267dbb5141354ea3131
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 5
  completed_plans: 4
  percent: 20
---

# State: Fast FSM

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Preserve ≥200,000 ops/sec singleton dispatch while finite guarded candidate groups resolve deterministically with explicit local O(k) cost.
**Current focus:** Phase 22 — Ordered Runtime Selection & Lifecycle Integration

## Current Position

Phase: 22 (Ordered Runtime Selection & Lifecycle Integration) — EXECUTING
Plan: 3 of 3
Status: Ready to execute
Last activity: 2026-09-06 — Phase 22 execution started

## Performance Metrics

**Velocity:**

- Total plans completed: 43
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 15 | 9 | - | - |
| 16 | 5 | - | - |
| 17 | 5 | - | - |
| 18 | 8 | - | - |
| 19 | 8 | - | - |
| 20 | 6 | - | - |
| 21 | 2 | - | - |

**Recent Trend:** v0.3.0 completed all six phases and passed the final hosted installed-artifact proof; v0.4.0 now has five dependency-ordered phases with full requirement coverage.
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
| Phase 18 P04 | 13m | 2 tasks | 7 files |
| Phase 18 P05 | 17m | 2 tasks | 5 files |
| Phase 18 P06 | 33m | 2 tasks | 5 files |
| Phase 18 P07 | 1h 25m | 3 tasks | 10 files |
| Phase 18 P08 | 44m | 3 tasks | 7 files |
| Phase 20 P01 | 32m | 3 tasks | 4 files |
| Phase 20 P02 | 20m | 2 tasks | 5 files |
| Phase 20 P05 | 21m | 2 tasks | 5 files |
| Phase 20 P06 | 1004m | 3 tasks | 7 files |
| Phase 21 P01 | 21m | 2 tasks | 7 files |
| Phase 21-priority-contract-atomic-registration P02 | 48m | 2 tasks | 6 files |
| Phase 22 P01 | 6m | 2 tasks | 4 files |
| Phase 22 P02 | 6m | 2 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Current milestone decisions:

- Safe defaults take precedence over unsafe pre-production callback, reentrancy, and concurrency semantics.
- Existing public symbols remain available; `core.py` remains one mypyc compilation unit with one runtime dependency.
- Runtime hardening must preserve ≥200,000 compiled `trigger()` operations/sec and O(1) core operations.
- Installed pure and compiled artifacts must prove equivalent hardened behavior before release.
- [v0.4.0 roadmap]: Evolve the existing `add_transition(..., priority=...)` API; do not create a second candidate-registration API.
- [v0.4.0 roadmap]: Lower exact non-boolean integer priorities win; distinct equal-priority candidates fail atomically and exact duplicates are idempotent.
- [v0.4.0 roadmap]: Preserve O(1) source/trigger lookup and singleton dispatch; document and measure finite candidate selection and local group mutation as O(k).
- [v0.4.0 roadmap]: Complete candidate selection before lifecycle callbacks and prove the same sequential semantics in synchronous and asynchronous machines.
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
- [Phase 18]: All public topology, history, and registrar writes enter ownership once and use private owned bodies.
- [Phase 18]: Callback-time registration fails before mutation; post-operation registration remains ordered for the next snapshot.
- [Phase 18]: Factories, builders, and clones retain distinct ownership primitives and clear live async metadata.
- [Phase 18]: [Phase 18]: safe_trigger admits ownership before ordinary Exception conversion, so redacted ownership RuntimeError values propagate rather than become results.
- [Phase 18]: Declarative guard preparation uses a token-reset ContextVar marker containing machine, source, trigger, and target identity.
- [Phase 18]: [Phase 18] Publish safe_trigger ownership admission as a redacted RuntimeError before ordinary value conversion, and document scheduler, snapshot, transfer, offload, and artifact exclusions.
- [Phase 18]: Phase 18 closure accepts hosted ownership proof only when its exact SHA and all Python 3.10-3.14 native jobs succeed; coverage runs observe semantics while uninstrumented jobs enforce performance floors.
- [Phase 19]: Diagnostics consume immutable graph snapshots and enforce deterministic budgets with explicit incomplete-result semantics.
- [Phase 19]: Structured analysis can report incompleteness, while fixed-shape public output raises a redacted exception instead of silently truncating.
- [Phase 19]: Mermaid and PlantUML output use grammar-specific escaping and collision-free opaque identifiers.
- [Phase 19]: Trace logging is metadata-only by default, custom redactors fail closed, and library logging configuration preserves application-owned handlers.
- [Phase 19]: Fresh pure and compiled exports are authoritative for semantics and performance; installed-artifact parity remains Phase 20-owned.
- [Phase 20]: Use one deterministic checkout-independent oracle for source, pure-wheel, and compiled-wheel semantics.
- [Phase 20]: Bind archive and runtime identity before accepting semantic artifact evidence; semantic digests exclude origins and performance.
- [Phase 20]: Only AUTO may fall back from mypyc; explicit COMPILED must propagate failure and prove native fast_fsm.core.
- [Phase 20]: Verify bounded sdist inventory before extraction, then derive offline pure and compiled child wheels for the verifier interpreter with parent SHA-256 lineage.
- [Phase 20]: Use counted mapping operations as primary O(1) evidence; timing remains a coarse regression backstop.
- [Phase 20]: Gate TEST-06 only on fresh installed compiled native records with a recomputed three-sample median.
- [Phase 20]: Keep historical categorical provenance, pure observations, installed compiled evidence, and diagnostic complexity in separate evidence namespaces.
- [Phase 20]: Preserve the reviewed uv 0.12.6 pin fail-closed; do not substitute host uv 0.12.9 for release readiness.
- [Phase 20]: Scope contents: write exclusively to the final v0.3.0 tag-only release job after exact aggregate and peeled-tag identity.
- [Phase 20]: Local profile evidence is non-authorizing; an explicitly authorized read-only hosted evidence inspection remains required before tagging.
- [Phase 21]: Priority stays object-typed until exact built-in-int validation passes at the mypyc boundary.
- [Phase 21]: One candidate is direct; competing priorities are private frozen sorted tuple groups published atomically.
- [Phase 21]: Singleton lookup/dispatch remains O(1); finite candidate construction and selection are local O(k).
- [Phase 21]: Builder materializes all staged priority rows through one existing add_transitions batch.
- [Phase 21]: Clone captures topology through the owner-aware read boundary while sharing only immutable slots.
- [Phase 22]: Synchronous selection keeps singleton dispatch direct and scans only frozen priority groups before one lifecycle handoff.
- [Phase 22]: Group rejection is private scan control; exceptions are terminal and exhaustion is one redacted selection failure.
- [Phase 22]: Async candidate selection awaits one stored candidate stage at a time and uses a task-local cancellation-stage marker only within the owned trigger boundary.

### Pending Todos

None yet.

### Blockers/Concerns

- v0.3.0 remains internally closed but intentionally has no Git tag, GitHub Release, or package publication.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| quick_tasks | `260404-exx-fill-callback-hook-gaps-before-transitio` | acknowledged | 2026-09-06 | v0.3.0 |
| Transition policy | Queued reentrancy and callback compensation | Future | v0.3.0 requirements | — |
| Async ownership | Cross-loop transfer and automatic callback offload | Future | v0.3.0 requirements | — |
| Tooling | Public topology snapshot v2 and possible `CompiledFuncCondition` redesign | Future | v0.3.0 requirements | — |

## Session Continuity

Last session: 2026-09-07T00:58:16.213Z
Stopped at: Completed 22-02-PLAN.md
Resume file: None

## Rebuild Log

- timestamp: 2026-09-05T01:36:48.999Z
  kind: by-phase-table-reconciled
  section: ## Performance Metrics
  before: | Phase | Plans | Total | Avg/Plan | \n |-------|-------|-------|----------| \n | 15–20 | 0 | TBD | — | \n | 15 | 9 | - | - | \n | 16 | 5 | - | - | \n | 17 | 5 | - | - | \n | 18 | 8 | - | - | \n | 19 | 8 | - | - |
  after: | Phase | Plans | Total | Avg/Plan | \n |-------|-------|-------|----------| \n | 15 | 9 | - | - | \n | 16 | 5 | - | - | \n | 17 | 5 | - | - | \n | 18 | 8 | - | - | \n | 19 | 8 | - | - | \n | 20 | 6 | - | - |
  reason: phase dirs on disk are canonical; rows for missing phases dropped, missing phases added

## Operator Next Steps

- Discuss Phase 21 with `/gsd-discuss-phase 21`.
- Then plan Phase 21 with `/gsd-plan-phase 21`.
