# Phase 30: Builder-First Construction & Persistence Parity - Context

**Gathered:** 2026-09-17
**Status:** Ready for planning
**Mode:** Auto-selected recommended defaults under the active milestone-completion goal

<domain>
## Phase Boundary

Make `FSMBuilder` the single primary programmatic construction story while
retaining direct `StateMachine` / `AsyncStateMachine` construction as the
advanced interface and `from_dict()` as the persistence adapter. Route
declarative definitions and every retained construction adapter through the
Phase 26 canonical normalization/publication transaction. Complete clone,
dictionary, and snapshot parity for the final-state and internal-transition
semantics delivered by Phases 27–28.

This phase does not remove compatibility constructors, add executable
serialization, introduce a topology snapshot v2, change runtime selection or
lifecycle semantics, or implement diagnostic/visual rendering. Diagnostic
projection belongs to Phase 31; progressive README/tutorial and migration
guidance belongs to Phase 32.

</domain>

<decisions>
## Implementation Decisions

### Construction Hierarchy

- **D-01:** `FSMBuilder` is the primary public interface for new programmatic machine construction. Public API reference and migration guidance should lead with it; examples outside explicit compatibility tests should converge on it as their construction mechanism. — **Reversibility:** costly — changing the primary interface again would churn documentation, examples, and user code.
- **D-02:** Direct `StateMachine` and `AsyncStateMachine` construction remains supported, public, and non-deprecated as the advanced interface for users who need explicit state identity or incremental topology control.
- **D-03:** `StateMachine.from_dict()` and `AsyncStateMachine.from_dict()` remain the supported adapter for declarative external topology data. They are not a competing general-purpose programmatic builder, and no second public construction abstraction is added.
- **D-04:** Builder operations continue to accept caller-owned `State` identities and retain fluent mutation before the first successful `build()`. A successful build keeps the established cached/immutable builder behavior; a failed build leaves the staged builder inspectable and repairable.

### Declarative Definitions Through the Builder

- **D-05:** `@transition` declarations gain or preserve every canonical transition scalar needed by v0.5.0, including exact priority, timing, and keyword-only `internal=False`; declaration metadata is immutable and validated before builder staging. — **Reversibility:** costly — decorator metadata becomes a public authoring contract.
- **D-06:** Adding a `DeclarativeState` or `AsyncDeclarativeState` to `FSMBuilder` imports its decorated transition declarations into ordinary `_TransitionRequest` values and publishes them only through the canonical construction transaction at `build()`. There is no declarative-only topology table, registrar, or second builder class.
- **D-07:** Declaration discovery must preserve canonical source and destination identity, final-state rejection, internal self-target validation, priority ordering, timing fields, async auto-detection, and exactly-once handler execution. Explicit and declarative declarations that collide are rejected by the same duplicate/candidate rules rather than silently overwriting one another.
- **D-08:** Direct `handle_event()` / `handle_event_async()` state behavior remains available for compatibility, but machine topology and machine-owned dispatch semantics are authored and validated through the builder/canonical registrar.

### Compatibility Deprecations

- **D-09:** `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` remain callable but emit one actionable `DeprecationWarning` at the user call site (`stacklevel=2`) naming the `FSMBuilder` replacement. Direct constructors, `from_dict()`, `State.create()`, and declarative state classes are not deprecated.
- **D-10:** The convenience constructors remain behaviorally supported throughout the v0.5.x compatibility cycle and may be removed no earlier than v0.6.0. Their runtime, typing, atomicity, final-state, and transition-mode behavior must remain correct until removal. — **Reversibility:** one-way — once removal ships, restoring these symbols would recreate a public compatibility contract.
- **D-11:** Deprecation wording is fixed and bounded, does not echo caller payloads, and distinguishes programmatic replacement (`FSMBuilder`) from serialized reconstruction (`from_dict`). Tests assert warning category, exact call-site attribution, one warning per public invocation, and continued correct construction.
- **D-12:** Phase 30 may update focused API/deprecation reference material and migrate code examples needed to prevent new use of the helpers. Phase 32 owns the full progressive README/Sphinx tutorial and release-facing migration walkthrough.

### Dictionary, Clone, and Snapshot Compatibility

- **D-13:** Topology dictionaries keep `states: list[str]` and add only deterministic, JSON-native metadata: the existing top-level `final_states` list and transition-row `internal` scalar. `internal` is emitted only when true; absence or explicit false reads as external. Old dictionaries without either field reconstruct non-final states and external transitions. — **Reversibility:** one-way — emitted dictionary fields become a persisted interoperability contract.
- **D-14:** `from_dict()` validates the complete input before candidate publication: exact container/scalar types, unique known final names, exact booleans, internal self-target identity, no outgoing final-source edge, condition references, timing, priority, and row context. A malformed document returns no partial machine and exposes no executable callback or exception payload.
- **D-15:** Compatibility is directional and stated truthfully: old payload → new reader and new payload → new reader are supported; a pre-v0.5 reader may ignore additive metadata and lose semantics. Phase 30 does not add a schema-version key that older readers cannot enforce or claim symmetric new→old semantic safety.
- **D-16:** `clone()` preserves final-state and internal-transition meaning, selected state subclasses, immutable state/entry identities where established, async machine type, and independent topology/callback containers. It retains the existing reset-to-initial behavior rather than copying live current state or history.
- **D-17:** `snapshot()` / `restore()` remains format v1 and state-only. It gains no topology, final-state, or transition-mode fields; termination after restore derives immediately from the receiving machine's canonical current `State.final`, and transition mode remains topology owned.

### Parity and Atomic Evidence

- **D-18:** Direct, batch, builder, legacy factory/helper, declarative, callback-state, clone, and deserialization paths all converge on `_TransitionRequest` plus the Phase 26 prepare-all/publish-once seam. No adapter performs post-publication semantic repair.
- **D-19:** The parity oracle replays the same final/internal topology across synchronous and asynchronous machines, pure and freshly compiled runtimes, and every retained adapter. It compares observable semantics and atomic failure, not merely dictionary equality.
- **D-20:** Deprecated helpers stay inside the parity matrix for the compatibility cycle. Structural tests also prove that adapter code does not bypass canonical normalization, weaken exact-type checks, mutate graph version on failure, or introduce dispatch-time work.

### the agent's Discretion

- Exact private helper names, staging order within a no-user-code construction transaction, warning constant placement, and test-file partitioning.
- Whether declarative import occurs eagerly on `add_state()` into a temporary validated staging plan or at `build()` from immutable metadata, provided builder mutation remains atomic and conflicts surface before machine publication.
- Exact deterministic dictionary key ordering and whether explicit `internal: false` is accepted on input, provided output omits false, both absent/false read as external, and validation remains exact.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase Contract

- `.planning/ROADMAP.md` §Phase 30 — goal, dependency, six requirements, and five success criteria.
- `.planning/REQUIREMENTS.md` §Construction Interface and Topology Integrity — BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, and BUILD-08.
- `.planning/PROJECT.md` — builder simplification intent, flat-FSM boundary, compatibility posture, performance identity, and mypyc constraint.

### Approved Milestone Research

- `.planning/research/FEATURES.md` §Construction, Runtime, and Tooling Parity — adapter matrix, additive persistence fields, and snapshot-v1 rule.
- `.planning/research/ARCHITECTURE.md` §Construction and Persistence Parity — required state/transition propagation and dictionary schema.
- `.planning/research/PITFALLS.md` §Serialization Silently Erases Final or Internal Meaning and §Construction and Diagnostics Disagree With Runtime — compatibility direction, atomicity risks, and evidence expectations.
- `.planning/research/SUMMARY.md` §Phase 5 — construction/persistence scope and sequencing before diagnostic projection.

### Settled Construction and Runtime Semantics

- `.planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md` — canonical request normalization, prepare-all/publish-once transaction, builder reuse, and adapter evidence policy.
- `.planning/phases/26-canonical-construction-evidence-contract/26-VERIFICATION.md` — verified construction transaction, ownership, and atomicity foundation.
- `.planning/phases/27-explicit-final-states/27-CONTEXT.md` — immutable final marker, no-outgoing-final-source rule, clone, dictionary, and snapshot decisions.
- `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md` — immutable internal mode, selected-entry identity, lifecycle behavior, clone hand-off, and Phase 30 adapter boundary.
- `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md` — selector-only rejection and condition propagation contract that construction adapters must not weaken.
- `.specify/memory/spr-core-api.md` — living public construction, persistence, clone, lifecycle, typing, and compiled-runtime contract.
- `.specify/memory/constitution.md` — performance, atomicity, compatibility, testing, and source-of-truth requirements.

### Current User-Facing Surfaces

- `src/fast_fsm/core.py` — factories, canonical request transaction, declarative metadata, clone, persistence, snapshot, and `FSMBuilder` implementation.
- `src/fast_fsm/core.pyi` — public construction, decorator, helper, clone, and persistence typing contract.
- `src/fast_fsm/__init__.py` — package-level public exports retained through the compatibility cycle.
- `README.md` and `docs/QUICK_START.md` — current mixed construction guidance; Phase 30 establishes focused migration truth and Phase 32 completes the progressive rewrite.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `_TransitionRequest`, `_PreparedTransition`, `_normalize_transition_request()`, and `_apply_transition_requests_owned()` in `src/fast_fsm/core.py`: the canonical exact-validation and atomic-publication spine for every adapter.
- `FSMBuilder`: already stages caller-owned states, requests, sync/async callbacks, auto-detects async requirements, preserves failed-build reuse, and publishes one candidate machine.
- `_DeclarativeHandlerMetadata`, `_DeclarativeHandler`, `transition()`, and `DeclarativeState._discover_handlers()`: existing immutable-ish declaration data and condition/handler identity that can feed builder staging.
- `to_dict()`, `from_dict()`, `clone()`, `snapshot()`, and `restore()`: established cold-path reconstruction surfaces with Phase 27 final-state support and remaining internal-mode gaps.
- `tests/test_builder.py`, `tests/test_graph_invariants.py`, `tests/test_final_states.py`, `tests/test_transition_modes.py`, and `tests/test_advanced_functionality.py`: existing adapter, atomicity, persistence, and clone matrices to extend.

### Established Patterns

- Normalize exact public values and canonical endpoint identities before mutation; construct complete replacement slots off-table and advance graph version only after successful publication.
- Keep `State` and transition metadata immutable and slotted; preserve caller-owned subclass identities instead of rebuilding generic objects.
- Separate cold construction/persistence work from direct singleton dispatch; no adapter cleanup or deprecation check belongs in the trigger hot path.
- Keep only `core.py` compiled, retain interpreted user subclasses, and prove pure/native behavior with the existing structural and semantic oracles.

### Integration Points

- Builder initialization and `add_state()` for declarative discovery and async classification.
- `FSMBuilder.add_transition()` / `build()` and every helper/factory row parser for canonical request staging.
- `transition()` decorator metadata and matching declarative handler resolution for mode and identity parity.
- `to_dict()` / `from_dict()` transition rows for `internal`; top-level `final_states` already exists.
- Sync and async `clone()` plus format-v1 snapshot/restore for reconstruction truth.
- Package exports, PEP 561 stubs, deprecation warnings, focused API docs, and compatibility tests.

</code_context>

<specifics>
## Specific Ideas

- A new user should see one ordinary recipe: create explicit `State` objects, pass the initial state to `FSMBuilder`, add states/transitions/callbacks fluently, and call `build()`.
- A declarative user should be able to add decorated state objects to that same builder and receive the same topology validation and runtime semantics, without manually mirroring every decorator as a second transition declaration.
- Migration messages should name a concrete builder replacement rather than merely saying an API is deprecated.

</specifics>

<deferred>
## Deferred Ideas

- Final/internal/rejection projection through validators, JSON diagnostics, Mermaid, and PlantUML — Phase 31.
- Full progressive README/Sphinx restructuring, drone tutorial migration, installed-artifact proof, and release-facing migration walkthrough — Phase 32.
- Immediate removal of deprecated helpers, a topology snapshot v2, executable callback serialization, and a second declarative builder remain outside v0.5.0.

</deferred>

---

*Phase: 30-builder-first-construction-persistence-parity*
*Context gathered: 2026-09-17*
