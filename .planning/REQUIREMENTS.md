# Requirements: Fast FSM v0.3.0 Reliability & Runtime Hardening

**Defined:** 2026-08-29
**Core Value:** Blazing-fast, zero-overhead FSM transitions — `trigger()` must stay ≥200,000 ops/sec and all core operations must remain O(1).
**Scope source:** `.planning/codebase/CONCERNS.md` plus the v0.3.0 research synthesis

## v0.3.0 Requirements

### Release Integrity

- [ ] **REL-01**: A maintainer can verify that package metadata, `fast_fsm.__version__`, changelog, documentation, and the release tag all identify v0.3.0 before publishing.
- [ ] **REL-02**: A maintainer can audit the historical v0.2.3 version mismatch through an explicit correction record without moving or silently replacing the existing tag.
- [ ] **REL-03**: A requested compiled release fails when mypyc compilation fails or the produced wheel does not contain the expected native extension.
- [ ] **REL-04**: A maintainer can intentionally build and identify a pure-Python wheel without triggering the strict compiled-release failure policy.
- [ ] **REL-05**: A clean checkout passes formatting, lint, stable type compatibility, full tests, Sphinx HTML, and doctests with one documented test baseline.
- [ ] **REL-06**: Release-producing build tools are reproducibly pinned, and compatibility does not depend solely on the pre-release `ty` checker.
- [ ] **REL-07**: CI verifies installed pure and compiled artifacts rather than relying only on imports from the source checkout.
- [ ] **REL-08**: The slots policy documents and measures any deliberate exception such as `CompiledFuncCondition`, so memory claims match shipped behavior.

### Graph and Dispatch Invariants

- [ ] **GRAF-01**: A user cannot add a transition whose source or target is absent from the canonical state registry, and a rejected addition leaves the graph unchanged.
- [ ] **GRAF-02**: A user cannot replace a registered state with a different object using the same name; idempotent registration of the same object remains safe.
- [ ] **GRAF-03**: Runtime tools can consume one immutable graph snapshot containing canonical endpoints, declared initial state, deterministic ordering, and a graph version.
- [ ] **GRAF-04**: After `FSMBuilder.build()`, every builder mutator fails immediately while repeated `build()` calls remain idempotent.
- [ ] **GRAF-05**: `FSMBuilder` recursively detects asynchronous conditions through `unless=` and condition wrappers and builds the correct machine type.
- [ ] **GRAF-06**: Guards receive positional arguments and one consistently sanitized keyword context across sync/async `can_trigger*()` and `trigger*()` paths.
- [ ] **GRAF-07**: Declarative transition handlers execute exactly once during ordinary sync and async trigger dispatch.
- [ ] **GRAF-08**: Shared internal resolution and dispatch seams keep sync, async, builder, and declarative behavior aligned without splitting the mypyc `core.py` compilation unit.

### Atomic Transition Lifecycle

- [ ] **LIFE-01**: A user observes one documented callback order with explicit pre-commit, commit, and post-commit stages in both sync and async machines.
- [ ] **LIFE-02**: A pre-commit callback failure preserves the source state and returns or raises a failure that identifies the failed stage and original cause.
- [ ] **LIFE-03**: A post-commit callback failure preserves the destination state, reports `committed=True`, and never reports the transition as successful.
- [ ] **LIFE-04**: Each failed transition notifies failure observers exactly once without swallowing the callback exception or recursively re-entering failure handling.
- [ ] **LIFE-05**: Transition history records only committed transitions and remains coherent when callbacks fail or async work is cancelled.
- [ ] **LIFE-06**: Sync and async transitions expose equivalent state, result, callback-order, guard-context, and failure semantics.
- [ ] **LIFE-07**: History rejects non-positive capacities and uses O(1) bounded eviction while preserving copy-on-read behavior.

### Ownership and Concurrency

- [ ] **OWN-01**: A transition or mutator invoked reentrantly by its current owner fails immediately before lock acquisition and cannot overwrite the outer operation.
- [ ] **OWN-02**: Independent threads operating on one synchronous machine are serialized without a global lock.
- [ ] **OWN-03**: Independent tasks operating on one asynchronous machine in the same event loop are serialized without blocking the loop.
- [ ] **OWN-04**: Unsupported cross-event-loop use fails explicitly instead of binding or corrupting ownership silently.
- [ ] **OWN-05**: State and topology mutators, including trigger, force/reset/restore, and graph changes, participate in the same per-machine ownership policy.
- [ ] **OWN-06**: Ownership is released after exceptions, `BaseException`, or cancellation, leaving state and history at a documented coherent boundary.
- [ ] **OWN-07**: The async callback contract explicitly states that synchronous callbacks run inline, while async callbacks and machine control remain event-loop safe; automatic thread offload is not implied.

### Bounded Diagnostics

- [ ] **DIAG-01**: Validation always performs reachability from the machine's declared initial state, regardless of its current runtime state.
- [ ] **DIAG-02**: Batch validation and FSM comparison preserve every input when machine names are duplicated.
- [ ] **DIAG-03**: Comparing zero FSMs returns a documented empty result or explicit validation error instead of dividing by zero.
- [ ] **DIAG-04**: Cycle analysis reports every state in each cycle, including all members of cycles longer than two states.
- [ ] **DIAG-05**: Longest-path analysis uses a bounded or memoized graph algorithm rather than enumerating exponentially many acyclic paths.
- [ ] **DIAG-06**: Diagnostic APIs can avoid unconditional dense N×N allocation and unbounded path expansion for sparse or generated graphs.
- [ ] **DIAG-07**: When a deterministic analysis budget is exceeded, the caller receives explicit incomplete-result metadata or a documented error rather than silent partial output.
- [ ] **DIAG-08**: Validation, comparison, JSON analysis, and visualization consume the stable graph snapshot instead of coupling independently to mutable private dictionaries.

### Safe Output and Logging

- [ ] **OUT-01**: Mermaid output assigns collision-free opaque identifiers when distinct state names sanitize to the same text.
- [ ] **OUT-02**: Mermaid and PlantUML state names, triggers, titles, Unicode, control text, and punctuation are escaped according to each target grammar.
- [ ] **OUT-03**: Trace logging redacts trigger values by default and cannot expose raw positional or keyword payloads merely because trace mode is enabled.
- [ ] **OUT-04**: An application can supply an explicit trace redactor when key-only default logging is insufficient.
- [ ] **OUT-05**: `configure_fsm_logging()` preserves application-owned handlers and offers reversible library-owned configuration with deliberate propagation behavior.

### Verification and Performance

- [ ] **TEST-01**: One parameterized conformance suite exercises equivalent sync, async, builder, declarative, pure-source, and compiled behavior for the hardened contracts.
- [ ] **TEST-02**: Pure-Python verification proves that no stale `.so` or `.pyd` shadows `core.py` and records meaningful source coverage.
- [ ] **TEST-03**: Compiled-wheel verification runs substantive behavior tests on supported native targets rather than a smoke import alone.
- [ ] **TEST-04**: Release verification asserts installed module origin, metadata version, architecture, semantic parity, and intended artifact type.
- [ ] **TEST-05**: Every performance-sensitive `core.py` phase measures compiled and pure-Python overhead before its design is frozen.
- [ ] **TEST-06**: Compiled `trigger()` throughput remains at least 200,000 operations/sec after lifecycle and ownership hardening.
- [ ] **TEST-07**: Core runtime operations remain O(1), while diagnostic APIs document and enforce their separate complexity and budget contracts.

## Future Requirements

### Advanced Transition Policies

- **FUTR-01**: A user can opt into queued reentrant transitions with an explicit ordering and overflow policy.
- **FUTR-02**: A user can define compensation actions for external side effects after post-commit callback failure.
- **FUTR-03**: A machine can be shared across event loops through a documented ownership-transfer protocol.
- **FUTR-04**: A user can opt into automatic worker-thread execution for synchronous callbacks on an async machine.

### Extended Tooling

- **FUTR-05**: A user can serialize a public topology snapshot format with compatibility guarantees beyond the existing `to_dict()` composition.
- **FUTR-06**: `CompiledFuncCondition` storage can be redesigned if measurements show its documented slots exception materially harms the library's memory contract.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic rollback of arbitrary callback side effects | External I/O cannot be made transactional by the FSM; expose the commit boundary and require application compensation instead. |
| Implicit queued reentrancy | Queue semantics, ordering, and overflow policy are separate API design work; v0.3.0 rejects reentry safely. |
| Cross-event-loop sharing | Asyncio primitives are loop-bound; v0.3.0 rejects unsupported ownership rather than hiding unsafe behavior. |
| Automatic callback thread offload | Changes callback ordering, context propagation, and cancellation semantics; keep execution explicit. |
| New runtime graph dependency | SCC, sparse adjacency, and budgets are implementable with the standard library and the one-runtime-dependency constraint remains. |
| Splitting `core.py` into modules | `core.py` remains the single mypyc compilation unit; hardening uses internal seams within it. |
| Retagging v0.2.3 to different source | Historical integrity requires documenting the mismatch rather than moving an immutable release reference. |
| Scheduler or auto-fire timers | Timing conditions remain passive guards; scheduling belongs to the caller's event loop. |
| Unrelated public API expansion | This milestone closes correctness, safety, diagnostic, and release debt before adding new product capabilities. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REL-01 | Phase 20 | Pending |
| REL-02 | Phase 15 | Pending |
| REL-03 | Phase 20 | Pending |
| REL-04 | Phase 15 | Pending |
| REL-05 | Phase 15 | Pending |
| REL-06 | Phase 15 | Pending |
| REL-07 | Phase 20 | Pending |
| REL-08 | Phase 15 | Pending |
| GRAF-01 | Phase 16 | Pending |
| GRAF-02 | Phase 16 | Pending |
| GRAF-03 | Phase 16 | Pending |
| GRAF-04 | Phase 16 | Pending |
| GRAF-05 | Phase 16 | Pending |
| GRAF-06 | Phase 16 | Pending |
| GRAF-07 | Phase 16 | Pending |
| GRAF-08 | Phase 16 | Pending |
| LIFE-01 | Phase 17 | Pending |
| LIFE-02 | Phase 17 | Pending |
| LIFE-03 | Phase 17 | Pending |
| LIFE-04 | Phase 17 | Pending |
| LIFE-05 | Phase 17 | Pending |
| LIFE-06 | Phase 17 | Pending |
| LIFE-07 | Phase 16 | Pending |
| OWN-01 | Phase 18 | Pending |
| OWN-02 | Phase 18 | Pending |
| OWN-03 | Phase 18 | Pending |
| OWN-04 | Phase 18 | Pending |
| OWN-05 | Phase 18 | Pending |
| OWN-06 | Phase 18 | Pending |
| OWN-07 | Phase 18 | Pending |
| DIAG-01 | Phase 19 | Pending |
| DIAG-02 | Phase 19 | Pending |
| DIAG-03 | Phase 19 | Pending |
| DIAG-04 | Phase 19 | Pending |
| DIAG-05 | Phase 19 | Pending |
| DIAG-06 | Phase 19 | Pending |
| DIAG-07 | Phase 19 | Pending |
| DIAG-08 | Phase 19 | Pending |
| OUT-01 | Phase 19 | Pending |
| OUT-02 | Phase 19 | Pending |
| OUT-03 | Phase 19 | Pending |
| OUT-04 | Phase 19 | Pending |
| OUT-05 | Phase 19 | Pending |
| TEST-01 | Phase 20 | Pending |
| TEST-02 | Phase 15 | Pending |
| TEST-03 | Phase 20 | Pending |
| TEST-04 | Phase 20 | Pending |
| TEST-05 | Phase 20 | Pending |
| TEST-06 | Phase 20 | Pending |
| TEST-07 | Phase 20 | Pending |

**Coverage:**
- v0.3.0 requirements: 50 total
- Mapped to phases: 50
- Unmapped: 0

---
*Requirements defined: 2026-08-29*
*Last updated: 2026-08-29 after roadmap mapping*
