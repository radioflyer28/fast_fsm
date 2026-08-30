# Roadmap: Fast FSM

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- ✅ **v0.2.2 Introspection & Agent Tooling** — Phases 7–11.1 (shipped 2026-04-05)
- ✅ **v0.2.3 Timing Condition Helpers** — Phases 12–14 (shipped 2026-04-05)
- 🚧 **v0.3.0 Reliability & Runtime Hardening** — Phases 15–20 (in progress)

## Phases

<details>
<summary>✅ v0.2.1 Code Health & Quality (Phases 1–6) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Quick Wins — version sync + import fix
- [x] Phase 2: State ABC Cleanup — remove misleading `ABC` base
- [x] Phase 3: Exception Handling Audit — annotate all 16 broad catches
- [x] Phase 4: py.typed Marker — PEP 561 typed package declaration
- [x] Phase 5: Test Suite Triage — audit and prune 4 low-value tests
- [x] Phase 6: Benchmark CI — 200k ops/sec throughput gate + CI job

**14/14 requirements satisfied.** Full details: `.planning/milestones/v0.2.1-ROADMAP.md`

</details>

<details>
<summary>✅ v0.2.2 Introspection & Agent Tooling (Phases 7–11.1) — SHIPPED 2026-04-05</summary>

- [x] Phase 7: Serialization (`to_dict()`) — topology roundtrip via `StateMachine.to_dict()`
- [x] Phase 8: Transition History — opt-in `enable_history()` / `disable_history()` with `TransitionRecord`
- [x] Phase 9: PlantUML Output — `to_plantuml()` in `visualization.py`
- [x] Phase 10: Machine-Readable JSON Export — `to_json()` with topology + analysis + quality signals
- [x] Phase 11: Performance Verification & Docs — benchmark gate, README updates, milestone wrap-up
- [x] Phase 11.1: History-Enabled Performance Benchmark — gap closure for PERF-02 (2026-04-05)

**21/21 requirements satisfied.** 695 tests, 1.2M ops/sec.

</details>

<details>
<summary>✅ v0.2.3 Timing Condition Helpers (Phases 12–14) — SHIPPED 2026-04-05</summary>

- [x] Phase 12: Timing Condition Implementation — `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition`
- [x] Phase 13: Testing & Integration Verification — 27 new tests, 722 total, 200k+ ops/sec
- [x] Phase 14: Documentation — README examples, Sphinx API reference

**15/15 requirements satisfied.** 722 tests, no mypyc rebuild needed.

</details>

### 🚧 v0.3.0 Reliability & Runtime Hardening (In Progress)

**Milestone Goal:** Make Fast FSM release-auditable, internally consistent, and safe by default while preserving its public symbols, single mypyc compilation unit, one runtime dependency, and compiled throughput floor.

- [x] **Phase 15: Release Baseline & Evidence Harness** — establish trustworthy version, quality, pure-source, and toolchain evidence (completed 2026-08-29)
- [ ] **Phase 16: Canonical Graph & Dispatch Invariants** — make construction, builders, guards, declarative handlers, and history internally consistent
- [ ] **Phase 17: Atomic Transition Lifecycle** — expose one truthful pre-commit, commit, and post-commit contract across sync and async machines
- [ ] **Phase 18: Safe Ownership & Concurrency** — reject reentry and serialize independent callers with exception-safe per-machine ownership
- [ ] **Phase 19: Bounded Diagnostics & Safe Output** — produce correct bounded analysis, escaped diagrams, and non-invasive redacted logging
- [ ] **Phase 20: Installed Artifact Parity & Release Proof** — prove shipped pure and compiled artifacts have identical semantics and meet the release contract

## Phase Details

### Phase 15: Release Baseline & Evidence Harness

**Goal**: Maintainers can trust the repository's version, quality-gate, toolchain, and pure-source evidence before runtime semantics change.
**Depends on**: Phase 14
**Requirements**: REL-02, REL-04, REL-05, REL-06, REL-08, TEST-02
**Success Criteria** (what must be TRUE):

  1. A maintainer can audit the immutable v0.2.3 mismatch correction and see one documented 722-or-greater baseline pass formatting, lint, stable typing, full tests, Sphinx HTML, and doctests from a clean checkout.
  2. A maintainer can intentionally build an identifiable pure-Python wheel, and pure-source verification proves that no stale native extension shadowed `core.py` while recording meaningful source coverage.
  3. Release-producing tools resolve to reproducibly pinned versions, and stable compatibility checking does not depend solely on the pre-release `ty` checker.
  4. The shipped memory policy identifies and measures every deliberate slots exception, including `CompiledFuncCondition`, so maintainers can reconcile the implementation with performance claims.

**Plans**: 9/9 plans executed

**Wave 1**

- [x] 15-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 15-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 15-04-PLAN.md
- [x] 15-06-PLAN.md
- [x] 15-07-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 15-03-PLAN.md

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 15-08-PLAN.md

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 15-09-PLAN.md

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 15-05-PLAN.md

### Phase 16: Canonical Graph & Dispatch Invariants

**Goal**: Users get one canonical machine topology and equivalent construction and dispatch behavior across sync, async, builder, and declarative APIs.
**Depends on**: Phase 15
**Requirements**: GRAF-01, GRAF-02, GRAF-03, GRAF-04, GRAF-05, GRAF-06, GRAF-07, GRAF-08, LIFE-07
**Success Criteria** (what must be TRUE):

  1. Invalid transition endpoints and conflicting duplicate state names are rejected without partial mutation, while tools observe an immutable, deterministically ordered, versioned graph snapshot with the declared initial state.
  2. Every builder mutator fails after the first build, repeated builds return the same result, and wrapped asynchronous `unless=` conditions select an asynchronous machine automatically.
  3. Positional and sanitized keyword guard context behaves identically in sync and async `can_trigger*()` and `trigger*()` calls, and declarative handlers run exactly once during ordinary dispatch.
  4. History rejects non-positive capacities, evicts records in O(1), and still returns defensive copies to callers.
  5. Public symbols remain available and the aligned internal resolution and dispatch seams keep `core.py` as one mypyc compilation unit.

**Plans**: TBD

- [ ] 16-01-PLAN.md
- [ ] 16-02-PLAN.md
- [ ] 16-03-PLAN.md
- [ ] 16-04-PLAN.md
- [ ] 16-05-PLAN.md

### Phase 17: Atomic Transition Lifecycle

**Goal**: Users receive truthful, state-atomic transition outcomes when guards or callbacks fail in either sync or async execution.
**Depends on**: Phase 16
**Requirements**: LIFE-01, LIFE-02, LIFE-03, LIFE-04, LIFE-05, LIFE-06
**Success Criteria** (what must be TRUE):

  1. Sync and async machines expose the same documented callback order with explicit pre-commit, commit, and post-commit stages.
  2. A pre-commit failure preserves the source state and identifies its stage and original cause; a post-commit failure preserves the destination, reports `committed=True`, and never reports success.
  3. Each failed transition notifies failure observers exactly once without swallowing the original exception or recursively invoking failure handling.
  4. History contains only committed transitions and remains coherent through callback exceptions and asynchronous cancellation.
  5. Equivalent sync and async transitions produce matching state, result, callback-order, guard-context, and failure behavior.

**Plans**: TBD

### Phase 18: Safe Ownership & Concurrency

**Goal**: A machine is safe by default under reentrant and concurrent use without global locks or event-loop blocking.
**Depends on**: Phase 17
**Requirements**: OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07
**Success Criteria** (what must be TRUE):

  1. A trigger or mutator called reentrantly by its current owner fails before lock acquisition and cannot overwrite the outer operation.
  2. Independent threads are serialized per synchronous machine, while independent same-loop tasks are serialized per asynchronous machine without blocking the event loop.
  3. Cross-event-loop access fails explicitly instead of silently rebinding ownership or corrupting state.
  4. Trigger, force, reset, restore, and topology changes share the ownership policy, which is always released after exceptions, `BaseException`, or cancellation at a documented coherent boundary.
  5. Async users can observe and rely on the documented rule that synchronous callbacks run inline and are not implicitly offloaded to worker threads.

**Plans**: TBD

### Phase 19: Bounded Diagnostics & Safe Output

**Goal**: Users and tools receive correct, bounded, snapshot-consistent diagnostics and safely encoded output without payload or logging side effects.
**Depends on**: Phase 18
**Requirements**: DIAG-01, DIAG-02, DIAG-03, DIAG-04, DIAG-05, DIAG-06, DIAG-07, DIAG-08, OUT-01, OUT-02, OUT-03, OUT-04, OUT-05
**Success Criteria** (what must be TRUE):

  1. Validation starts from the declared initial state, preserves every duplicate-named input, and handles an empty comparison without division by zero.
  2. Cycle analysis reports every member of every cycle, and longest-path and generated-graph analysis use bounded or memoized algorithms with explicit incomplete-result or error reporting when budgets are exhausted.
  3. Sparse or generated graphs can be analyzed without mandatory dense N×N allocation or unbounded path expansion, under documented diagnostic complexity contracts.
  4. Validation, comparison, JSON analysis, and diagram generation all describe the same immutable graph snapshot rather than independently reading mutable private dictionaries.
  5. Mermaid and PlantUML output uses collision-free identifiers and grammar-specific escaping, while trace logs redact payload values by default, accept an application redactor, and preserve application-owned handlers through reversible configuration.

**Plans**: TBD

### Phase 20: Installed Artifact Parity & Release Proof

**Goal**: Maintainers can publish v0.3.0 only when installed pure and compiled artifacts prove the same hardened behavior, identity, and performance.
**Depends on**: Phase 19
**Requirements**: REL-01, REL-03, REL-07, TEST-01, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):

  1. A requested compiled build fails closed on compilation or extension-inclusion failure, and CI exercises installed pure and compiled artifacts rather than the source checkout.
  2. One conformance suite proves matching hardened behavior across sync, async, builder, declarative, pure-source, and compiled modes on supported native targets.
  3. Release verification identifies each installed artifact's module origin, metadata version, native architecture, semantic behavior, and intended pure or compiled type.
  4. Benchmarks cover every performance-sensitive core phase, compiled `trigger()` remains at least 200,000 operations/sec, core runtime operations remain O(1), and diagnostics enforce their separate budgets.
  5. Package metadata, `fast_fsm.__version__`, changelog, documentation, release tag, quality gates, and published artifacts all identify and substantiate v0.3.0.

**Plans**: TBD

## Progress

**Execution Order:** Phase 15 → Phase 16 → Phase 17 → Phase 18 → Phase 19 → Phase 20

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 15. Release Baseline & Evidence Harness | v0.3.0 | 9/9 | Complete    | 2026-08-29 |
| 16. Canonical Graph & Dispatch Invariants | v0.3.0 | 0/5 | Planned    |  |
| 17. Atomic Transition Lifecycle | v0.3.0 | 0/TBD | Not started | - |
| 18. Safe Ownership & Concurrency | v0.3.0 | 0/TBD | Not started | - |
| 19. Bounded Diagnostics & Safe Output | v0.3.0 | 0/TBD | Not started | - |
| 20. Installed Artifact Parity & Release Proof | v0.3.0 | 0/TBD | Not started | - |
