# Roadmap: Fast FSM

## Overview

Fast FSM v0.4.0 evolves one source/trigger slot from a singular edge into a finite, priority-ordered guarded candidate group without surrendering the singleton fast path. The work freezes atomic registration first, integrates deterministic sync/async selection with the existing lifecycle second, then carries candidate identity through constructors, tooling, installed-artifact proof, and the drone example.

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- ✅ **v0.2.2 Introspection & Agent Tooling** — Phases 7–11.1 (shipped 2026-04-05)
- ✅ **v0.2.3 Timing Condition Helpers** — Phases 12–14 (shipped 2026-04-05)
- ✅ **v0.3.0 Reliability & Runtime Hardening** — Phases 15–20 (completed 2026-09-06; untagged and unreleased)
- 🚧 **v0.4.0 Priority-Aware Guarded Transitions** — Phases 21–25 (planned)

## Phases

<details>
<summary>✅ v0.2.1 Code Health & Quality (Phases 1–6) — SHIPPED 2026-04-04</summary>

Version metadata, exception handling, typing, state inheritance, test triage, and the compiled throughput CI gate. **14/14 requirements satisfied.** Full details: `.planning/milestones/v0.2.1-ROADMAP.md`.

</details>

<details>
<summary>✅ v0.2.2 Introspection & Agent Tooling (Phases 7–11.1) — SHIPPED 2026-04-05</summary>

Topology serialization, transition history, PlantUML and JSON output, plus performance verification. **21/21 requirements satisfied.** Full details: `.planning/milestones/v0.2.2-ROADMAP.md`.

</details>

<details>
<summary>✅ v0.2.3 Timing Condition Helpers (Phases 12–14) — SHIPPED 2026-04-05</summary>

Timeout, cooldown, and elapsed conditions with integration tests and documentation. **15/15 requirements satisfied.** Full details: `.planning/milestones/v0.2.3-ROADMAP.md`.

</details>

<details>
<summary>✅ v0.3.0 Reliability & Runtime Hardening (Phases 15–20) — COMPLETED 2026-09-06</summary>

Release integrity, canonical graph and dispatch invariants, atomic lifecycle semantics, safe ownership, bounded diagnostics, and installed-artifact proof. **50/50 requirements satisfied.** Full details: `.planning/milestones/v0.3.0-ROADMAP.md`.

</details>

### 🚧 v0.4.0 Priority-Aware Guarded Transitions (Planned)

**Milestone Goal:** Add deterministic, priority-aware guarded transition resolution so one `(state, trigger)` selects among finite ordered candidates without external dispatch logic.

- [x] **Phase 21: Priority Contract & Atomic Registration** — establish the finite candidate topology and deterministic, atomic registration rules. (completed 2026-09-06)
- [x] **Phase 22: Ordered Runtime Selection & Lifecycle Integration** — select exactly one eligible candidate with matching sync/async failure semantics. (completed 2026-09-06)
- [x] **Phase 23: Construction, Declarative & Serialization Parity** — preserve candidate identity through every public construction and introspection path. (completed 2026-09-06)
- [x] **Phase 24: Candidate-Aware Diagnostics & Output** — make validation, graph analysis, and renderers truthful about multiplicity and priority. (completed 2026-09-07)
- [ ] **Phase 25: Performance, Artifact Proof & Drone Guidance** — prove the complexity and installed-artifact contracts and publish the motivating usage pattern.

## Phase Details

### Phase 21: Priority Contract & Atomic Registration

**Goal**: Library consumers can construct immutable, finite, deterministically ordered candidate groups through the existing transition API without partial topology mutation.
**Depends on**: Phase 20
**Requirements**: PRIO-01, PRIO-02, PRIO-03
**Success Criteria** (what must be TRUE):

  1. A consumer can use `add_transition(..., priority=...)` repeatedly for one source/trigger, while internal immutable-topology inspection verifies every registered candidate and a one-candidate slot retains the direct singleton representation; supported public candidate inspection is explicitly deferred to Phase 23 and this phase adds no public inspection API.
  2. Priority accepts exact non-boolean integers, lower values win independent of registration order, conflicting equal priorities reject the whole operation, and exact duplicate registration is an idempotent no-op.
  3. Batch, multi-source, bidirectional, emergency, and builder-backed registration either publish every affected candidate group or leave topology and graph version unchanged.
  4. Candidate groups are immutable after publication, remain isolated across clones, and `core.py` continues to pass the native compilation/type boundary.

**Plans:** 2/2 plans complete

Plans:

- [x] 21-01-PLAN.md — Establish the priority topology contract and atomic same-slot registration.
- [x] 21-02-PLAN.md — Complete helper/builder transport, clone isolation, and compiled singleton proof.

### Phase 22: Ordered Runtime Selection & Lifecycle Integration

**Goal**: Sync and async machines resolve the first fully eligible candidate in priority order before exactly one transition lifecycle begins.
**Depends on**: Phase 21
**Requirements**: SEL-01, SEL-02, SEL-03, SEL-04
**Success Criteria** (what must be TRUE):

  1. Synchronous dispatch evaluates transition guard, declarative guard, and target-state permission in ascending priority order and commits the first candidate for which all three permit transition.
  2. Asynchronous dispatch awaits candidates sequentially in the same order; ordinary rejection falls through, while exceptions and cancellation abort without evaluating lower-priority candidates or mutating state.
  3. Selection completes before lifecycle callbacks, and one trigger attempt can produce at most one lifecycle, one committed history record, and one success-observer sequence.
  4. Exhausting a group returns one uncommitted selection-stage failure and notifies failure observers once, while an absent trigger remains a distinct resolution failure.

**Plans:** 3/3 plans complete

Plans:

- [x] 22-01-PLAN.md — Add deterministic synchronous selection, failure boundaries, query parity, and one-lifecycle handoff.
- [x] 22-02-PLAN.md — Mirror selection sequentially across async queries/dispatch, exceptions, cancellation, and lifecycle.
- [x] 22-03-PLAN.md — Propagate runtime priority metadata and prove slots, native parity, O(1) singleton, and local O(k) group work.

### Phase 23: Construction, Declarative & Serialization Parity

**Goal**: Every supported construction, declarative, clone, query, and serialization path preserves complete candidate identity and priority-aware behavior.
**Depends on**: Phase 22
**Requirements**: PAR-01, PAR-02, PAR-03
**Success Criteria** (what must be TRUE):

  1. Builders, declarative handlers, factories, quick builders, helper APIs, and deserialization construct the same ordered candidate groups as direct registration without trigger-key or handler overwrite.
  2. `can_trigger*()` selects eligibility consistently without mutation, and results, history, tracing, topology snapshots, cloning, and query helpers identify the selected candidate priority without changing callback signatures.
  3. `to_dict()` followed by `from_dict()` preserves every candidate and its priority, including multiple candidates with the same source, trigger, and target.
  4. Deserialization can attach guards to a specific candidate without serializing callables, and ambiguous legacy guard keys fail explicitly rather than attaching to the wrong transition.

**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 23-01-PLAN.md — Promote candidate-complete cold topology and add callable-safe round-trip, snapshot, query, and clone parity.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 23-02-PLAN.md — Preserve plural declarative identity through exact sync/async handler selection and builder preflight.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 23-03-PLAN.md — Complete quick/factory construction parity and lock pure/native compiled-core compatibility.

### Phase 24: Candidate-Aware Diagnostics & Output

**Goal**: Diagnostics and structured or human-readable outputs represent each transition candidate exactly once in deterministic priority order under existing safety budgets.
**Depends on**: Phase 23
**Requirements**: DIAG-01, DIAG-02
**Success Criteria** (what must be TRUE):

  1. Validation accepts strictly ordered candidate groups as deterministic, rejects malformed equal-priority groups, and distinguishes provably shadowed lower candidates from possible shadowing.
  2. JSON, Mermaid, PlantUML, Markdown, and adjacency output preserve candidate multiplicity and numeric priority with stable ordering and the established escaping contracts.
  3. Diagnostic edge counts, work budgets, and generated paths count candidates rather than collapsed source/trigger pairs and retain explicit incomplete-result behavior when a budget is exhausted.
  4. All diagnostic consumers project from one immutable topology snapshot instead of depending on private singleton/group runtime storage.

**Plans**: 3 plans

**Wave 1**

- [x] 24-01-PLAN.md — Extend the immutable diagnostic projection and implement strict-priority, conservative shadow validation.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 24-02-PLAN.md — Propagate candidate identity, priority, escaping, and candidate-sized budgets through adjacency, paths, and every output sink.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 24-03-PLAN.md — Lock pure/native diagnostic parity, source-origin cleanliness, and the living maintainer contract.

### Phase 25: Performance, Artifact Proof & Drone Guidance

**Goal**: Users and maintainers can rely on truthful complexity guidance, equivalent installed pure/native behavior, and an example where the FSM owns telemetry-driven routing.
**Depends on**: Phase 24
**Requirements**: PERF-01, PERF-02, DOC-01
**Success Criteria** (what must be TRUE):

  1. Project policy and public documentation state and demonstrate O(1) source/trigger lookup and singleton dispatch, plus O(k) local candidate-group mutation and ordered selection without dispatch-time sorting or unrelated-graph scans.
  2. Benchmarks characterize groups of representative depths and winner positions, while freshly installed compiled singleton dispatch retains the ≥200,000 operations/sec gate.
  3. Source, pure-wheel, and compiled-wheel conformance prove identical winner, evaluation order, result/history priority metadata, exhaustion stage, and exception/cancellation semantics.
  4. The drone example submits one telemetry event to a controller-owned FSM; transition guards own priority decisions, aircraft callbacks issue commands, and telemetry services expose facts such as heartbeat age without selecting transitions.
  5. Ruff, mypy/mypyc, the full sync/async test suite, documentation builds, and installed-artifact checks pass from clean evidence origins.

**Plans**: TBD

## Requirement Coverage

| Phase | Requirement IDs | Count |
|-------|-----------------|-------|
| 21 | PRIO-01, PRIO-02, PRIO-03 | 3 |
| 22 | SEL-01, SEL-02, SEL-03, SEL-04 | 4 |
| 23 | PAR-01, PAR-02, PAR-03 | 3 |
| 24 | DIAG-01, DIAG-02 | 2 |
| 25 | PERF-01, PERF-02, DOC-01 | 3 |
| **Total** | **All v0.4.0 requirements** | **15/15** |

**Coverage:** 100% — every v0.4.0 requirement is assigned to exactly one phase.

## Phase Ordering Rationale

- Phase 21 freezes the public priority contract and canonical immutable representation before any runtime or adapter depends on it.
- Phase 22 proves ordered selection and lifecycle boundaries against that representation before higher-level constructors can replay the behavior.
- Phase 23 removes singular assumptions from every construction and identity-preserving surface, producing the stable topology projection required by tooling.
- Phase 24 updates diagnostics and renderers only after candidate identity and snapshot shape are complete.
- Phase 25 validates the fully integrated system across installed artifacts, then publishes performance claims and the drone example against proven behavior.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 21. Priority Contract & Atomic Registration | v0.4.0 | 2/2 | Complete    | 2026-09-06 |
| 22. Ordered Runtime Selection & Lifecycle Integration | v0.4.0 | 3/3 | Complete    | 2026-09-06 |
| 23. Construction, Declarative & Serialization Parity | v0.4.0 | 3/3 | Complete    | 2026-09-06 |
| 24. Candidate-Aware Diagnostics & Output | v0.4.0 | 3/3 | Complete    | 2026-09-07 |
| 25. Performance, Artifact Proof & Drone Guidance | v0.4.0 | 0/TBD | Not started | — |

---
*Roadmap created: 2026-09-06 for v0.4.0 Priority-Aware Guarded Transitions*
