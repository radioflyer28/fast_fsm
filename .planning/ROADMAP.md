# Roadmap: Fast FSM

## Overview

Fast FSM v0.5.0 makes completion, same-state lifecycle behavior, and expected domain rejection explicit without widening the library into a statechart runtime. The milestone first establishes one atomic construction seam and fair evidence baselines, then implements final states, internal transitions, and rejection as separate semantic boundaries before carrying them through every supported constructor, persistence format, diagnostic projection, installed artifact, and progressive drone example.

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- ✅ **v0.2.2 Introspection & Agent Tooling** — Phases 7–11.1 (shipped 2026-04-05)
- ✅ **v0.2.3 Timing Condition Helpers** — Phases 12–14 (shipped 2026-04-05)
- ✅ **v0.3.0 Reliability & Runtime Hardening** — Phases 15–20 (completed 2026-09-06; untagged and unreleased)
- ✅ **v0.4.0 Priority-Aware Guarded Transitions** — Phases 21–25 (shipped 2026-09-07)
- 📋 **v0.5.0 Explicit Flat-FSM Semantics** — Phases 26–32 (planned)

## Phases

<details>
<summary>✅ Completed milestones (Phases 1–25)</summary>

Completed milestone details are archived under `.planning/milestones/` and summarized in `.planning/MILESTONES.md`.

</details>

### 📋 v0.5.0 Explicit Flat-FSM Semantics (Planned)

**Milestone Goal:** Make completion, same-state behavior, and expected domain rejection explicit while preserving Fast FSM's decisive speed advantage for flat, deterministic machines.

- [x] **Phase 26: Canonical Construction & Evidence Contract** — establish one atomic construction seam and exact, non-gating competitor evidence lanes. (completed 2026-09-15)
- [x] **Phase 27: Explicit Final States** — make intentional completion immutable, queryable, and lifecycle-truthful. (completed 2026-09-15)
- [x] **Phase 28: Same-State Transition Modes** — distinguish external re-entry from internal logical commits across sync and async execution. (completed 2026-09-16)
- [x] **Phase 29: Expected Domain Rejection** — expose bounded structured rejection without priority fallthrough or lifecycle ambiguity. (completed 2026-09-17)
- [ ] **Phase 30: Builder-First Construction & Persistence Parity** — simplify the public construction story and preserve semantics through every adapter and persisted form.
- [ ] **Phase 31: Semantic Diagnostics & Visualization** — project finality, transition mode, and rejection truthfully through bounded tooling.
- [ ] **Phase 32: Performance, Artifact & Progressive Guidance Proof** — prove installed parity, protect the fast path, and teach the complete workflow progressively.

## Phase Details

### Phase 26: Canonical Construction & Evidence Contract

**Goal**: Maintainers have one atomic topology-construction boundary and reproducible comparison evidence before new runtime semantics depend on either.
**Depends on**: Phase 25
**Requirements**: BUILD-04, BUILD-05, PERF-05, PERF-06
**Success Criteria** (what must be TRUE):

  1. Every retained construction adapter can be routed through one private normalization, validation, and publication seam rather than maintaining its own topology rules.
  2. A failed registration, build, or deserialization leaves topology, graph version, indexes, and reusable builder state unchanged and inspectable.
  3. Maintainers can run semantically preflighted comparison scenarios against exact isolated `python-statemachine` 2.5.0 and 3.2.1 installations, with versions, origins, and unsupported cells reported explicitly.
  4. Competitor results remain labelled manual or scheduled evidence and ordinary CI succeeds without installing or timing competitor packages.

**Plans**: 4/5 plans executed

Plans:
**Wave 1**

- [x] 26-01-PLAN.md — trace direct and batch registration through one immutable canonical construction transaction.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 26-02-PLAN.md — define both required semantic-first comparison cells, exact child adapters, and a neutral-cwd repo-aware parent protocol.
- [x] 26-03-PLAN.md — route every retained transition-producing adapter and clone reconstruction through the transaction and prove retryability/parity.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 26-04-PLAN.md — verify exact external package provenance before adjacent lock generation.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 26-05-PLAN.md — generate exact locks, isolate ordinary dependencies/CI, wire the manual observation command, and carry the phase to verification-only closure.

### Phase 27: Explicit Final States

**Goal**: Users can represent intentional completion directly and rely on termination truth across construction, execution, and control operations.
**Depends on**: Phase 26
**Requirements**: FINAL-01, FINAL-02, FINAL-03, FINAL-04, FINAL-05, FINAL-06
**Success Criteria** (what must be TRUE):

  1. A user can create an immutable `State(..., final=True)` and an initially final machine reports `is_terminated` through an O(1) current-state read.
  2. Every supported construction path rejects an outgoing transition from a final state atomically, while a non-final sink remains valid and non-terminated.
  3. Entering a final state makes termination visible at commit, and later entry, observer, or async cancellation failure does not undo the committed state or finality.
  4. Reset, restore, clone, and deserialization preserve the distinction between explicit finality and topology dead ends.

**Plans**: 3/3 plans executed

Plans:
**Wave 1**

- [x] 27-01-PLAN.md — add immutable explicit final metadata and an O(1) termination query across State construction surfaces.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 27-02-PLAN.md — reject outgoing final-source topology once at the canonical construction seam and prove adapter atomicity.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 27-03-PLAN.md — preserve finality through lifecycle, control, clone, and persistence operations and close native/pure-source validation.

### Phase 28: Same-State Transition Modes

**Goal**: Users can choose whether a self-transition performs external re-entry or an internal logical commit, with identical semantic truth across machine types.
**Depends on**: Phase 27
**Requirements**: MODE-01, MODE-02, MODE-03, MODE-04, MODE-05, MODE-06
**Success Criteria** (what must be TRUE):

  1. `internal=True` is an exact per-transition choice valid only for a canonical self-target, while omission preserves existing external behavior and invalid registration is atomic.
  2. An external self-transition runs the complete exit-and-entry lifecycle and resets entry-relative timing.
  3. An internal transition skips every state exit and entry surface while retaining transition-level behavior, one logical commit, result production, history, and appropriate observers.
  4. Internal transitions preserve the original state-entry timestamp so residency-based conditions remain uninterrupted.
  5. Synchronous and asynchronous machines produce matching mode, priority, failure, and cancellation outcomes without collapsing an internal commit into a no-op.

**Plans**: 3/3 plans executed

Plans:
**Wave 1**

- [x] 28-01-PLAN.md — establish the canonical transition-mode carrier, synchronous tracer, exact validation, atomic identity, builder, graph, and clone seams.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 28-02-PLAN.md — complete synchronous lifecycle, residency timing, priority, and staged failure semantics.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 28-03-PLAN.md — close async cancellation/ownership parity and prove typing, slots, pure/native, and full-suite conformance.

### Phase 29: Expected Domain Rejection

**Goal**: Applications can reject an otherwise considered transition as an expected domain outcome without hiding defects or selecting a lower-priority behavior.
**Depends on**: Phase 28
**Requirements**: REJECT-01, REJECT-02, REJECT-03, REJECT-04, REJECT-05, REJECT-06, REJECT-07, REJECT-08, REJECT-09
**Success Criteria** (what must be TRUE):

  1. Guards and state permission checks can raise public `TransitionRejected(code)` with a stable, bounded, payload-safe identifier, including through composed conditions.
  2. Ordinary false eligibility alone falls through a prioritized candidate group; expected rejection and unexpected exceptions stop evaluation before any lower candidate or lifecycle begins.
  3. A rejected trigger returns an uncommitted result with explicit rejection status and code distinct from unexpected causes, while `can_trigger*()` returns false without mutation or observation.
  4. Existing failure observers receive one notification for a rejected trigger, with no new listener family and no arbitrary exception detail exposed by default.
  5. Raising the same signal outside approved pre-commit eligibility seams retains ordinary staged execution-failure and cancellation truth.

**Plans**: 4/4 plans executed

Plans:
**Wave 1**

- [x] 29-01-PLAN.md — establish the bounded public rejection signal, additive result contract, synchronous eligibility conversion, and atomic four-exception policy authority.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 29-02-PLAN.md — complete query, condition-composition, asynchronous selection, cancellation, and observer parity.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 29-03-PLAN.md — prove lifecycle-boundary classification, payload-safe logging, and focused public API documentation.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 29-04-PLAN.md — close structural, slots-policy, pure/native, performance, restoration, and full-suite evidence.

### Phase 30: Builder-First Construction & Persistence Parity

**Goal**: Users encounter one clear construction path while every supported adapter, clone, and persistence operation preserves the new semantics.
**Depends on**: Phase 29
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, BUILD-08
**Success Criteria** (what must be TRUE):

  1. Public guidance presents `FSMBuilder` as the primary interface, direct `StateMachine` or `AsyncStateMachine` construction as advanced usage, and `from_dict` as the serialization adapter.
  2. Declarative definitions author behavior through the canonical builder/construction machinery instead of maintaining a separate topology implementation.
  3. Users of `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` receive actionable deprecation guidance while those symbols remain usable for the supported compatibility cycle.
  4. Direct, batch, builder, factory, declarative, helper, callback, clone, and deserialization paths enforce identical final-state and transition-mode rules without partial publication.
  5. Clone and dictionary round trips preserve final and internal metadata, legacy dictionaries receive false/default semantics, and state-only snapshot v1 derives termination from the receiving machine.

**Plans**: TBD

- [x] 30-01-PLAN.md
- [x] 30-02-PLAN.md
- [x] 30-03-PLAN.md
- [ ] 30-04-PLAN.md
- [ ] 30-05-PLAN.md
- [ ] 30-06-PLAN.md

### Phase 31: Semantic Diagnostics & Visualization

**Goal**: Users and maintainers can inspect the new semantics consistently without confusing intentional completion with graph shape or weakening output safeguards.
**Depends on**: Phase 30
**Requirements**: DIAG-01, DIAG-02, DIAG-03
**Success Criteria** (what must be TRUE):

  1. Results, history, validation, tracing, and JSON expose finality, transition mode, and expected rejection wherever each fact affects interpretation.
  2. Mermaid and PlantUML diagrams distinguish explicit final states, internal transitions, external self-transitions, and non-final sink states.
  3. Every new diagnostic field and rendering remains deterministic, bounded, escaped, and suitable for logs, tests, and serialized evidence.

**Plans**: TBD

### Phase 32: Performance, Artifact & Progressive Guidance Proof

**Goal**: Users can install any supported artifact, retain Fast FSM's direct-path performance, and learn the complete flat-FSM workflow progressively.
**Depends on**: Phase 31
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04, DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):

  1. Fresh installed compiled singleton dispatch remains direct O(1) and sustains at least 200,000 transitions per second when the new semantics are unused, without unrelated scans, reflection, or per-dispatch allocation.
  2. Environment-labelled evidence measures final-state, internal/external, and rejection costs separately and proves that unrelated topology does not change local dispatch work.
  3. Pure source, compiled extension, installed pure wheel, installed compiled wheel, and release artifacts satisfy the same fixed semantic oracle.
  4. The progressive controller-owned drone tutorial demonstrates prioritized telemetry guards, internal and external self-transitions, explicit landing finals, expected rejection, and committed aircraft commands without hidden scheduling machinery.
  5. README and Sphinx guidance progress from builder-first construction to advanced direct use, explain the deprecation migration, and clearly distinguish finality, dead ends, rejection, guard ineligibility, and self-transition modes.

**Plans**: TBD

## Requirement Coverage

| Phase | Requirement IDs | Count |
|-------|-----------------|-------|
| 26 | BUILD-04, BUILD-05, PERF-05, PERF-06 | 4 |
| 27 | FINAL-01, FINAL-02, FINAL-03, FINAL-04, FINAL-05, FINAL-06 | 6 |
| 28 | MODE-01, MODE-02, MODE-03, MODE-04, MODE-05, MODE-06 | 6 |
| 29 | REJECT-01, REJECT-02, REJECT-03, REJECT-04, REJECT-05, REJECT-06, REJECT-07, REJECT-08, REJECT-09 | 9 |
| 30 | BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, BUILD-08 | 6 |
| 31 | DIAG-01, DIAG-02, DIAG-03 | 3 |
| 32 | PERF-01, PERF-02, PERF-03, PERF-04, DOC-01, DOC-02, DOC-03, DOC-04 | 8 |
| **Total** | **All v0.5.0 requirements** | **42/42** |

**Coverage:** 100% — every v0.5.0 requirement is assigned to exactly one phase.

## Phase Ordering Rationale

- Phase 26 establishes the shared atomic construction seam and evidence vocabulary before new semantic fields multiply adapter behavior.
- Phase 27 introduces final-state truth first because termination and final-source invariants affect every later constructor and projection.
- Phase 28 specializes lifecycle behavior only after state metadata and the canonical registrar are stable.
- Phase 29 adds rejection after selection and lifecycle boundaries can distinguish pre-commit policy from post-commit failure.
- Phase 30 consolidates the public construction story and persistence only after all runtime metadata has a canonical representation.
- Phase 31 updates diagnostics from the settled immutable graph projection instead of duplicating evolving runtime logic.
- Phase 32 verifies the integrated system in fresh artifacts, protects the performance identity, and publishes guidance only for behavior already proven end to end.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 26. Canonical Construction & Evidence Contract | v0.5.0 | 5/5 | Complete    | 2026-09-15 |
| 27. Explicit Final States | v0.5.0 | 3/3 | Complete    | 2026-09-15 |
| 28. Same-State Transition Modes | v0.5.0 | 3/3 | Complete    | 2026-09-16 |
| 29. Expected Domain Rejection | v0.5.0 | 4/4 | Complete    | 2026-09-17 |
| 30. Builder-First Construction & Persistence Parity | v0.5.0 | 3/6 | In Progress|  |
| 31. Semantic Diagnostics & Visualization | v0.5.0 | 0/TBD | Not started | - |
| 32. Performance, Artifact & Progressive Guidance Proof | v0.5.0 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-09-15 for v0.5.0 Explicit Flat-FSM Semantics*
