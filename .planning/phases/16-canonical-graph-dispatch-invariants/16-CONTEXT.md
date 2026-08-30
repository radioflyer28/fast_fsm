# Phase 16: Canonical Graph & Dispatch Invariants - Context

**Gathered:** 2026-08-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish one canonical runtime topology and align construction, guard resolution,
ordinary dispatch, builder lifecycle, and history behavior across synchronous,
asynchronous, builder, and declarative APIs. This phase may introduce private
internal seams inside `core.py`, but it does not define Phase 17 callback-failure
ordering, Phase 18 ownership/locking, Phase 19 diagnostic budgets, or Phase 20
installed-artifact publication proof.

</domain>

<decisions>
## Implementation Decisions

### Canonical State Registry and Atomic Topology Mutation
- **D-01:** State names identify canonical registered objects. Registering the exact same object again is an idempotent no-op; registering a different object with an existing name raises `ValueError` and leaves the registry, transitions, graph version, and current state unchanged.
- **D-02:** Every transition source and target—whether supplied as a string or `State` object—must resolve to the canonical registry before any mutation. A `State` object with a matching name but different identity is not accepted as an endpoint.
- **D-03:** Multi-source transition additions validate and normalize the complete endpoint set, guard configuration, and duplicate sources before inserting any entry. One invalid endpoint rejects the whole call without partial transitions.
- **D-04:** Existing convenience constructors may collect/register their complete declared state set before adding transitions, but ordinary `add_transition()` never implicitly registers an endpoint.

### Immutable Graph Snapshot and Version
- **D-05:** Maintain a monotonic per-machine graph version. It advances once for each successful topology-changing public operation, does not advance for rejection or idempotent same-object registration, and never tracks runtime current-state changes.
- **D-06:** Provide one private/internal immutable graph snapshot for library tools. It contains the graph version, machine name, declared initial state, canonical state objects/names, and canonical transition endpoints/guards in deterministic state-name/trigger order.
- **D-07:** The snapshot is a tool-facing internal contract, not a new public serialization compatibility promise. `to_dict()` and the existing runtime `snapshot()` keep their public roles; Phase 19 migrates validation/visualization to consume the internal graph snapshot.
- **D-08:** Preserve the declared initial state independently from the mutable current state so all later tools can reason from construction identity rather than execution position.

### Builder Freeze and Async Detection
- **D-09:** A builder freezes only after a completely successful build. Every builder mutator, callback registrar, and force-mode method then raises `RuntimeError` immediately; a failed build remains repairable and does not cache a partial machine.
- **D-10:** Repeated successful `build()` calls return the same cached machine object. Build materialization must use local state until all registration and wiring succeeds, assigning the cache only at the end.
- **D-11:** Auto mode recursively detects asynchronous requirements through `unless=`/`NegatedCondition`, supported condition wrappers, declarative handlers, and queued async callbacks, with identity-based cycle protection. Explicit async mode remains authoritative; explicit sync mode fails at build time when any nested async requirement exists rather than warning and dropping behavior.

### Shared Resolution and Guard Context
- **D-12:** Sync/async `can_trigger*()` and `trigger*()` use the same internal transition-resolution and guard-context seams so “can” and “do” cannot disagree because they prepared different inputs.
- **D-13:** Guards receive positional arguments unchanged and one freshly copied, deterministic sanitized keyword mapping on all four paths. Apply the existing safety policy consistently: remove private/dunder and overlong keys, then cap the retained insertion-ordered entries; never mutate the caller's mapping.
- **D-14:** Sanitization is performed once per guard evaluation and the resulting context is passed to every wrapper layer. Raw payload values must not be introduced into logs by this refactor; Phase 19 owns broader trace-redaction policy.

### Declarative Ordinary Dispatch
- **D-15:** A matched declarative transition handler participates in ordinary sync/async trigger dispatch exactly once through the shared dispatch seam. Compatibility helpers must delegate to that seam rather than invoking the handler independently.
- **D-16:** Phase 16 proves one invocation and sync/async parity but does not lock the handler's precise pre-commit/post-commit position or callback-failure result model; Phase 17 defines that lifecycle atomically.

### Bounded History
- **D-17:** `enable_history(max_entries)` raises `ValueError` immediately for zero or negative capacity and, for a valid capacity, replaces any existing buffer with an empty bounded FIFO buffer.
- **D-18:** Eviction is O(1), chronological order is preserved, history remains disabled at zero steady-state cost, and the public `history` property continues to return a defensive `list` copy.

### Agent's Discretion
- Exact private snapshot/container types, private seam names, and internal type annotations, provided snapshot contents cannot be mutated through returned references and compile under mypyc.
- Exact graph-version starting value and whether compound convenience constructors expose one or several internal increments; externally observable requirements are monotonicity, rejection/idempotence stability, and snapshot freshness.
- The registry/snapshot test layout and helper organization within existing flat test modules or a focused new `test_graph_invariants.py` module.
- The private recursive-condition traversal protocol for built-in wrappers, provided it is cycle-safe and does not create a new public wrapper API.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase Contracts
- `.planning/PROJECT.md` — v0.3.0 safe-default posture, one-runtime-dependency constraint, public compatibility, performance floor, and single-file `core.py` boundary.
- `.planning/REQUIREMENTS.md` — authoritative GRAF-01 through GRAF-08 and LIFE-07 behavior, plus later-phase boundaries.
- `.planning/ROADMAP.md` — Phase 16 goal, dependency, and five observable success criteria.
- `.planning/phases/15-release-baseline-evidence-harness/15-CONTEXT.md` — inherited build/evidence contracts and Phase 20 deferrals.

### Architecture and Reproduced Concerns
- `.planning/codebase/ARCHITECTURE.md` — current registry/transition dictionaries, sync/async duplication, builder/declarative structure, and tooling dependencies.
- `.planning/codebase/CONCERNS.md` — reproduced unknown endpoints, duplicate replacement, builder mutation, wrapped async detection, guard parity, double declarative dispatch, and list-history failures.
- `.planning/codebase/TESTING.md` — established real-object test patterns and confirmed missing Phase 16 edge coverage.
- `.specify/decisions/ADR-003-mypyc-compilation-boundary.md` — only `core.py` compiles; condition bases remain interpreted and user-subclassable.

### Runtime and Tests
- `src/fast_fsm/core.py` — canonical registry, transitions, dispatch, history, declarative state, and `FSMBuilder` implementation surface.
- `src/fast_fsm/conditions.py` — `Condition`, `AsyncCondition`, and `NegatedCondition` wrapper semantics relevant to recursive detection.
- `tests/test_basic_functionality.py` — core construction/guard failure conventions.
- `tests/test_async.py` — async guard and history behavior.
- `tests/test_builder.py` — builder/declarative/auto-detection behavior.
- `tests/test_safety_kwargs.py` — existing keyword sanitization contract.
- `tests/test_advanced_functionality.py` — current history, factories, snapshots, and transition helpers.
- `tests/test_mypyc_guard.py` — compilation-boundary structural enforcement.
- `evidence/release-baseline.json` — Phase 15 pure-source quality and performance reference that Phase 16 must not regress.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StateMachine._states` and `_transitions`: retain the O(1) registry/dispatch representation; add validation/versioning around it rather than replacing it with a graph dependency.
- `StateMachine._resolve_transition()` and the existing condition-evaluation helpers: natural integration points for one sync resolution/guard seam, mirrored by the async path.
- `NegatedCondition._inner`: existing wrapper edge that currently hides nested `AsyncCondition` from the builder.
- `FSMBuilder._machine`: already caches successful builds; the phase must make all mutators honor that freeze and prevent partial caching on failed builds.
- `TransitionRecord` plus the public `history` copy: retain the public record/list shape while replacing list-front deletion internally.
- Phase 15's clean pure gate and evidence tooling: use them for before/after correctness and overhead measurements without touching developer native shadows.

### Established Patterns
- Core runtime lookups remain dictionary-based and O(1); diagnostic traversal is kept off the hot path.
- Public symbols and signatures remain available, while unsafe pre-production semantics may fail earlier and more explicitly.
- `core.py` stays one mypyc compilation unit; `conditions.py` stays interpreted for user subclassing.
- Tests prefer real FSM/state/condition objects, explicit negative assertions, and sync/async paired scenarios rather than mocked dispatch.
- Keyword sanitization already filters private/overlong keys and caps context; Phase 16 centralizes that behavior instead of inventing a second policy.

### Integration Points
- Registry and topology versioning: constructor, `_register_state()`, `add_state()`, `add_transition()`, bulk/convenience factories, clone/restore paths, and internal snapshot creation in `src/fast_fsm/core.py`.
- Shared guard seam: `can_trigger()`, `trigger()`, `can_trigger_async()`, and `trigger_async()`.
- Declarative dispatch: `DeclarativeState`/`AsyncDeclarativeState` handler discovery and ordinary machine trigger paths.
- Builder freeze/detection: every fluent mutator, force-mode method, callback registrar, recursive condition inspection, and `build()` cache assignment.
- History: `enable_history()`, append in sync/async commit paths, `disable_history()`, clone behavior, and the `history` property.

</code_context>

<specifics>
## Specific Ideas

- Prefer fail-before-mutation validation and identity-canonical endpoints over later repair of inconsistent graph dictionaries.
- Keep the graph snapshot internal and immutable so Phase 19 can consolidate diagnostics without prematurely publishing a new topology format.
- Preserve caller positional context exactly; centralize only the existing keyword safety policy.
- Treat successful builder materialization as a transaction: cache nothing until all states, transitions, and callbacks have wired successfully.

</specifics>

<deferred>
## Deferred Ideas

- Exact declarative/callback lifecycle order, commit boundary, and failure semantics — Phase 17.
- Reentrant/concurrent mutation ownership and locking around topology/version changes — Phase 18.
- Migration of validators, comparison, JSON, and visualization onto the graph snapshot, including budgets — Phase 19.
- A public versioned topology snapshot format — future requirement FUTR-05; Phase 16 creates only the internal contract.
- Compiled/pure installed-artifact parity and final performance proof — Phase 20.

</deferred>

---

*Phase: 16-canonical-graph-dispatch-invariants*
*Context gathered: 2026-08-29*
