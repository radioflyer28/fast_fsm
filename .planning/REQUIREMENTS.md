# Requirements: Fast FSM v0.4.0 Priority-Aware Guarded Transitions

**Defined:** 2026-09-06
**Core Value:** Blazing-fast, zero-overhead FSM transitions — singleton
`trigger()` remains ≥200,000 ops/sec, while competing guarded candidates resolve
deterministically with an explicit local cost.
**Scope source:** User-approved priority-transition design and v0.4.0 project
research synthesis.

## v0.4.0 Requirements

### Priority Registration

- [ ] **PRIO-01**: A library consumer can register multiple transitions for one
  `(source state, trigger)` through `add_transition(..., priority=...)` without
  a second registration API.
- [ ] **PRIO-02**: Candidate selection is independent of registration order:
  priorities are exact non-boolean integers, lower values win, conflicting ties
  fail atomically, and exact duplicate registrations remain idempotent.
- [ ] **PRIO-03**: Batch, multi-source, bidirectional, emergency, and builder
  registration preserve complete candidate groups, graph-version correctness,
  and clone isolation.

### Deterministic Resolution

- [ ] **SEL-01**: A synchronous machine selects the first candidate that passes
  its transition guard, declarative guard, and target-state permission in
  ascending priority order.
- [ ] **SEL-02**: An asynchronous machine applies the same ordered semantics by
  awaiting candidates sequentially; ordinary rejection falls through while
  exceptions and cancellation fail closed.
- [ ] **SEL-03**: Candidate selection completes before lifecycle callbacks;
  exactly one selected candidate can enter lifecycle work, history, and success
  observers.
- [ ] **SEL-04**: Group exhaustion returns one truthful, uncommitted selection
  failure and notifies failure observers once, while missing-trigger resolution
  failures retain their existing meaning.

### Complete Library Parity

- [ ] **PAR-01**: Declarative handlers, factories, quick builders, and
  deserialization preserve candidate identity and priority without singular
  trigger-key overwrites.
- [ ] **PAR-02**: `can_trigger*()`, `TransitionResult`, transition history,
  tracing, cloning, topology snapshots, and query helpers expose coherent
  priority-aware behavior without changing callback signatures.
- [ ] **PAR-03**: `to_dict()`/`from_dict()` round-trip candidate topology and
  candidate-specific guard attachment without serializing callables.

### Diagnostics and Output

- [ ] **DIAG-01**: Validation treats strictly ordered candidate groups as
  deterministic, rejects malformed ties, and reports provably shadowed lower
  candidates conservatively.
- [ ] **DIAG-02**: JSON, Mermaid, PlantUML, Markdown, adjacency data, and
  generated paths preserve candidate multiplicity and priority under existing
  escaping and budget contracts.

### Performance and Documentation

- [ ] **PERF-01**: The architecture preserves O(1) source/trigger lookup and
  singleton dispatch; grouped selection and local group mutation are documented
  and measured as O(k) without unrelated-graph scans or dispatch-time sorting.
- [ ] **PERF-02**: Source, pure-wheel, and compiled-wheel artifacts prove the
  same priority winner, evaluation order, result/history metadata, and failure
  semantics; compiled singleton dispatch remains ≥200,000 ops/sec.
- [ ] **DOC-01**: Documentation and the drone example show one telemetry event
  dispatched to FSM-owned priority resolution, while telemetry services provide
  facts such as heartbeat age without selecting transitions.

## Future Requirements

### Advanced Transition Policies

- **FUTR-01**: A consumer can use dynamic or callable priorities, score-based
  best-match selection, or an explicit equal-priority tie-break policy.
- **FUTR-02**: A consumer can mutate, remove, or reorder registered candidates
  at runtime.
- **FUTR-03**: An async machine can evaluate candidate guards in parallel under
  a separately specified precedence and cancellation policy.
- **FUTR-04**: A machine can opt into queued reentrant transitions with an
  explicit ordering and overflow policy.
- **FUTR-05**: A consumer can define compensation actions for external side
  effects after post-commit callback failure.
- **FUTR-06**: A machine can be shared across event loops through a documented
  ownership-transfer protocol.

### Extended Tooling

- **FUTR-07**: A consumer can serialize callable guards or use a public topology
  snapshot v2 with compatibility guarantees beyond existing `to_dict()`
  composition.
- **FUTR-08**: `CompiledFuncCondition` storage can be redesigned if measurements
  show its documented slots exception materially harms the memory contract.

## Out of Scope

| Feature | Reason |
|---------|--------|
| A second `add_transition_candidate()` API | Priority is an attribute of an ordinary transition; duplicate APIs obscure one transition model. |
| Registration-order tie breaking | Reordering setup code must never silently alter safety or routing behavior. |
| Automatic telemetry classification, schedulers, or eventless transitions | Telemetry helpers expose facts; callers still submit events and the FSM owns transition selection. |
| Parallel guard evaluation or fallback after exceptions/lifecycle failure | These alter precedence, cancellation, and lifecycle semantics and need independent design. |
| Callable serialization or a public topology snapshot v2 | Existing serialization remains topology-oriented and callable-safe. |
| New runtime graph dependency or splitting `core.py` | The standard library and one selectively compiled `core.py` unit remain project constraints. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRIO-01 | Phase 21 | Pending |
| PRIO-02 | Phase 21 | Pending |
| PRIO-03 | Phase 21 | Pending |
| SEL-01 | Phase 22 | Pending |
| SEL-02 | Phase 22 | Pending |
| SEL-03 | Phase 22 | Pending |
| SEL-04 | Phase 22 | Pending |
| PAR-01 | Phase 23 | Pending |
| PAR-02 | Phase 23 | Pending |
| PAR-03 | Phase 23 | Pending |
| DIAG-01 | Phase 24 | Pending |
| DIAG-02 | Phase 24 | Pending |
| PERF-01 | Phase 25 | Pending |
| PERF-02 | Phase 25 | Pending |
| DOC-01 | Phase 25 | Pending |

**Coverage:**

- v0.4.0 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0
- Coverage: 100% ✓

---
*Requirements defined: 2026-09-06*
*Last updated: 2026-09-06 after v0.4.0 roadmap creation*
