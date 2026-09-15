# Requirements: Fast FSM v0.5.0

**Defined:** 2026-09-15
**Core Value:** Blazing-fast FSM transitions with direct O(1) singleton dispatch and finite, deterministic guarded candidate resolution.

## v0.5.0 Requirements

### Final States

- [x] **FINAL-01**: Users can declare a state final with an immutable `final=True` property.
- [x] **FINAL-02**: Users can query termination in O(1) through `is_terminated`, including when the initial state is final.
- [x] **FINAL-03**: Users receive an atomic construction error when any supported construction path would add an outgoing transition to a final state.
- [x] **FINAL-04**: Users can distinguish a non-final sink state from a terminated final state.
- [ ] **FINAL-05**: Users observe the machine as terminated after a transition commits into a final state even if later entry or observer work fails.
- [ ] **FINAL-06**: Users receive consistent termination semantics after reset, restore, clone, and deserialization operations.

### Internal and External Transitions

- [ ] **MODE-01**: Users can select explicit internal transition semantics with `internal=True`, while omitted or false values retain existing external semantics.
- [ ] **MODE-02**: Users can register internal transitions only when source and destination are the same state, with invalid registration rejected atomically.
- [ ] **MODE-03**: Users observe the complete exit-and-reentry lifecycle and reset state-entry timing for external self-transitions.
- [ ] **MODE-04**: Users observe internal transitions without state exit or entry hooks and listeners, while non-state transition behavior, logical commit, results, history, and appropriate observers remain intact.
- [ ] **MODE-05**: Users observe uninterrupted state-residency timing across internal transitions.
- [ ] **MODE-06**: Users receive equivalent internal and external transition behavior across synchronous and asynchronous machines, prioritized selection, cancellation, and failure handling.

### Expected Transition Rejection

- [ ] **REJECT-01**: Users can signal expected domain rejection during pre-commit eligibility evaluation with public `TransitionRejected(code)`.
- [ ] **REJECT-02**: Users receive stable, bounded, payload-safe rejection identifiers rather than arbitrary exception messages or objects.
- [ ] **REJECT-03**: Users receive expected-rejection semantics only when rejection originates from transition guards, declarative guards, or state permission checks.
- [ ] **REJECT-04**: Users observe a rejection aborting the complete prioritized candidate group, while an ordinary false condition alone permits fallthrough.
- [ ] **REJECT-05**: Users receive an uncommitted `TransitionResult` with explicit rejection status and code, distinct from unexpected exception causes.
- [ ] **REJECT-06**: Users receive false from synchronous and asynchronous `can_trigger` queries for an expected rejection, while trigger operations preserve the structured rejection code.
- [ ] **REJECT-07**: Users observe existing failure observers exactly once for a rejected trigger without needing a separate rejection listener system.
- [ ] **REJECT-08**: Users can compose conditions without expected rejection being swallowed or converted to an ordinary false result.
- [ ] **REJECT-09**: Users receive ordinary execution-failure semantics when `TransitionRejected` is raised outside pre-commit eligibility evaluation.

### Construction Interface and Topology Integrity

- [ ] **BUILD-01**: Users are guided to `FSMBuilder` as the primary construction interface, direct machine construction as the advanced interface, and `from_dict` as the serialization adapter.
- [ ] **BUILD-02**: Users can author declarative behavior through the canonical construction machinery without a separate topology implementation.
- [ ] **BUILD-03**: Users of `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` receive documented deprecation guidance and a supported compatibility cycle.
- [x] **BUILD-04**: Maintainers can enforce all retained construction semantics through one private normalization and validation seam.
- [x] **BUILD-05**: Users can retry or inspect construction after a failed registration, build, or deserialization without partial topology, stale indexes, or corrupted reusable builders.
- [ ] **BUILD-06**: Users receive identical final-state and transition-mode validation through direct, batch, builder, factory, declarative, helper, callback, clone, and deserialization paths.
- [ ] **BUILD-07**: Users can clone and serialize machines without losing final-state or internal-transition metadata, while older serialized data receives backward-compatible defaults.
- [ ] **BUILD-08**: Users can continue using snapshot format v1, with termination derived from the receiving machine's current state and topology.

### Diagnostics and Visualization

- [ ] **DIAG-01**: Users can interpret finality, transition mode, and expected rejection consistently in results, history, validation, tracing, and JSON output wherever each concept applies.
- [ ] **DIAG-02**: Users can distinguish final states, internal transitions, and non-final sink states in Mermaid and PlantUML output.
- [ ] **DIAG-03**: Users receive deterministic, bounded diagnostic fields suitable for logs, tests, and serialized evidence.

### Performance and Release Evidence

- [ ] **PERF-01**: Users retain direct O(1) compiled singleton dispatch at or above 200,000 transitions per second when the new semantics are unused.
- [ ] **PERF-02**: Users who do not enable the new semantics incur no unrelated candidate scans, reflection, or per-dispatch allocation.
- [ ] **PERF-03**: Maintainers can measure final-state, transition-mode, and rejection costs independently with environment-labelled evidence.
- [ ] **PERF-04**: Users receive conformant behavior from pure-source, compiled-extension, installed-wheel, and release-artifact execution under the existing evidence harness.
- [x] **PERF-05**: Maintainers can compare semantically equivalent Fast FSM scenarios with exact isolated installations of `python-statemachine` 2.5.0 and 3.2.1.
- [x] **PERF-06**: Maintainers receive competitor results as labelled manual or scheduled observations rather than mandatory CI gates.

### Documentation and Examples

- [ ] **DOC-01**: Users can learn final states, prioritized telemetry guards, internal and external self-transitions, expected rejection, and owned aircraft commands through the progressive drone tutorial.
- [ ] **DOC-02**: Users encounter the canonical builder-first interface before advanced direct construction in the README and Sphinx documentation.
- [ ] **DOC-03**: Users can migrate from deprecated construction conveniences using documented replacements and compatibility timing.
- [ ] **DOC-04**: Users can clearly distinguish termination from dead-end topology, rejection from guard ineligibility, and internal transition from external self-transition in the public documentation.

## Future Requirements

### Runtime Policy

- **FUTR-01**: Users can configure bounded deferred-event processing without turning the FSM into a scheduler or task runtime.
- **FUTR-02**: Users can defer event-context construction until a selected transition needs it without penalizing ordinary dispatch.
- **FUTR-03**: Users can integrate a pluggable state-storage adapter without moving persistence policy into the flat FSM core.
- **FUTR-04**: Users can observe completion or carry richer localized rejection details if implementation evidence demonstrates a need beyond existing observers and bounded codes.

### Extended State Models

- **FUTR-05**: Users needing hierarchical, parallel, or history-pseudostate semantics can use a separately designed statechart engine without burdening Fast FSM's flat-machine hot path.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hierarchical, parallel, and history-pseudostate semantics | They require a different execution model and would compromise the milestone's explicit flat-FSM boundary. |
| Eventless transitions, schedulers, timers, and task orchestration | Scheduling and event-loop ownership belong above the passive FSM runtime. |
| Automatic synchronization between sync and async APIs | Hidden bridging creates ownership and cancellation ambiguity. |
| Reflection-based callback argument injection | Reflection adds complexity and hot-path risk without serving the core value. |
| New runtime dependencies or compiler upgrades solely for these features | The semantics can be implemented within the existing dependency and mypyc boundary. |
| Immediate removal of deprecated construction interfaces | Users receive at least one documented compatibility cycle. |
| Mandatory competitor benchmarks in ordinary CI | Isolated third-party installs are slower and less stable than release-oriented manual or scheduled evidence. |
| Snapshot topology format v2 | Existing topology serialization plus state-only snapshot v1 remains the composable contract. |

## Traceability

Every v0.5.0 requirement maps to exactly one roadmap phase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FINAL-01 | Phase 27 | Complete |
| FINAL-02 | Phase 27 | Complete |
| FINAL-03 | Phase 27 | Complete |
| FINAL-04 | Phase 27 | Complete |
| FINAL-05 | Phase 27 | Pending |
| FINAL-06 | Phase 27 | Pending |
| MODE-01 | Phase 28 | Pending |
| MODE-02 | Phase 28 | Pending |
| MODE-03 | Phase 28 | Pending |
| MODE-04 | Phase 28 | Pending |
| MODE-05 | Phase 28 | Pending |
| MODE-06 | Phase 28 | Pending |
| REJECT-01 | Phase 29 | Pending |
| REJECT-02 | Phase 29 | Pending |
| REJECT-03 | Phase 29 | Pending |
| REJECT-04 | Phase 29 | Pending |
| REJECT-05 | Phase 29 | Pending |
| REJECT-06 | Phase 29 | Pending |
| REJECT-07 | Phase 29 | Pending |
| REJECT-08 | Phase 29 | Pending |
| REJECT-09 | Phase 29 | Pending |
| BUILD-01 | Phase 30 | Pending |
| BUILD-02 | Phase 30 | Pending |
| BUILD-03 | Phase 30 | Pending |
| BUILD-04 | Phase 26 | Complete |
| BUILD-05 | Phase 26 | Complete |
| BUILD-06 | Phase 30 | Pending |
| BUILD-07 | Phase 30 | Pending |
| BUILD-08 | Phase 30 | Pending |
| DIAG-01 | Phase 31 | Pending |
| DIAG-02 | Phase 31 | Pending |
| DIAG-03 | Phase 31 | Pending |
| PERF-01 | Phase 32 | Pending |
| PERF-02 | Phase 32 | Pending |
| PERF-03 | Phase 32 | Pending |
| PERF-04 | Phase 32 | Pending |
| PERF-05 | Phase 26 | Complete |
| PERF-06 | Phase 26 | Complete |
| DOC-01 | Phase 32 | Pending |
| DOC-02 | Phase 32 | Pending |
| DOC-03 | Phase 32 | Pending |
| DOC-04 | Phase 32 | Pending |

**Coverage:**

- v0.5.0 requirements: 42 total
- Mapped to phases: 42
- Unmapped: 0

---
*Requirements defined: 2026-09-15*
*Last updated: 2026-09-15 after roadmap creation*
