# Phase 27: Explicit Final States - Context

**Gathered:** 2026-09-15
**Status:** Ready for planning
**Mode:** Auto-generated

<domain>
## Phase Boundary

Add explicit immutable final-state intent and O(1) termination truth to the flat FSM. Enforce final-source topology invariants atomically across the construction paths already unified in Phase 26, and preserve finality through transition commit, reset, restore, clone, and dictionary persistence. Internal-transition modes, structured domain rejection, builder-first deprecations, and diagnostic/visual rendering belong to Phases 28–31.

</domain>

<decisions>
## Implementation Decisions

### Final-State Model
- **D-01:** `State(..., final=True)` is the single public declaration surface; `final` is a keyword-only immutable boolean with a backward-compatible `False` default. — **Reversibility:** costly — changing the public constructor/property contract later would affect every construction and persistence adapter.
- **D-02:** Finality is explicit domain intent only. A non-final state with no outgoing edges remains a valid sink and does not make the machine terminated; the library never infers finality from graph shape.
- **D-03:** `State.final` is readable but cannot be reassigned after construction. No `FinalState` subclass or mutable machine-side final-state registry is introduced.

### Construction Invariant
- **D-04:** Any outgoing transition whose canonical source State is final is invalid, including self-transitions, multi-source expansion, priority candidates, helpers, factories, builders, declarative reconstruction, clones, and dictionary input.
- **D-05:** Rejection occurs in the Phase 26 canonical normalization/validation transaction before publication. A mixed batch containing one invalid final-source edge publishes nothing, preserves graph version, and leaves reusable builder/factory inputs repairable.
- **D-06:** A final state may be the initial state and may be the destination of any valid incoming transition. Construction must not require a final state to have an incoming edge.

### Runtime and Lifecycle Truth
- **D-07:** `StateMachine.is_terminated` is a read-only O(1) query of the canonical current state's explicit final marker; no topology scan, cache, or separate termination flag is maintained.
- **D-08:** Termination becomes visible at the same commit boundary that changes `current_state` to a final destination. Normal exit/transition/entry/observer lifecycle still runs; failures after commit do not roll back the state or termination truth.
- **D-09:** A trigger attempted while currently final follows the ordinary missing-transition resolution failure because outgoing final-source edges cannot exist. Finality does not introduce an automatic event, exception class, scheduler, or special completion callback.

### Reset, Restore, Clone, and Persistence
- **D-10:** Reset and snapshot restore derive termination solely from the resulting canonical current State. Resetting to a final initial state is terminated; restoring a non-final current state is not.
- **D-11:** Clone preserves the exact canonical State objects and therefore their immutable final markers while retaining Phase 26's independent transition containers.
- **D-12:** Dictionary persistence is additive: serialize explicit final-state names in a bounded deterministic field while older payloads that omit the field default every state to non-final. Deserialization validates names/types before candidate publication and rejects outgoing final-source edges atomically. — **Reversibility:** costly — serialized field semantics become a compatibility contract consumed by Phase 30.

### the agent's Discretion
- Exact private helper names, bounded public error wording, and test-file placement.
- The additive dictionary field's precise spelling and ordering, provided it is deterministic, backward-compatible, and straightforward for Phase 30 to carry across every persistence adapter.
- Whether `is_terminated` is implemented directly on sync base behavior only or explicitly mirrored for async typing, provided both machine types expose identical observable semantics.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Scope and Requirements
- `.planning/ROADMAP.md` §Phase 27 — phase goal, dependency, and four success criteria.
- `.planning/REQUIREMENTS.md` §Final States — FINAL-01 through FINAL-06.
- `.planning/PROJECT.md` — flat-FSM boundary, performance identity, compatibility posture, and mypyc constraint.

### Runtime and Construction Contracts
- `.specify/memory/spr-core-api.md` — living runtime, construction, lifecycle, serialization, and compiled-boundary contract.
- `.specify/memory/constitution.md` — performance, testing, compatibility, and atomicity requirements.
- `.planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md` — canonical construction seam and deferred final-state boundary established by the direct prerequisite phase.
- `.planning/phases/26-canonical-construction-evidence-contract/26-VERIFICATION.md` — verified transaction, clone, builder, pure/native, and evidence guarantees Phase 27 must preserve.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `State` in `src/fast_fsm/core.py`: slotted state identity and the natural owner of immutable `final` metadata.
- `StateMachine._normalize_transition_request()` and `_apply_transition_requests_owned()`: Phase 26's single validation/publication seam for final-source rejection.
- `_commit_transition()`, sync/async lifecycle runners, reset/restore/clone, and `current_state`: existing commit and control surfaces from which termination can be derived without new mutable state.
- `to_dict()` / `from_dict()`: established bounded dictionary round-trip with row-specific validation context.

### Established Patterns
- Normalize exact public values and canonical endpoints before mutation, prepare complete replacements off-table, and publish once.
- Preserve direct O(1) reads and singleton dispatch; construction-only validation must not enter trigger selection.
- Treat a committed state as authoritative even when later callbacks or observers fail.
- Keep `core.py` mypyc-compatible and hot-path classes slotted; prove both pure and native behavior.

### Integration Points
- State construction and package exports/documentation for the public marker and query.
- Every transition-producing adapter already routed through the Phase 26 request transaction.
- Snapshot/restore/clone and dictionary serialization for continuity of explicit finality.
- Existing graph, lifecycle, async, builder, ownership, serialization, Hypothesis, and mypyc tests for parity and atomicity coverage.

</code_context>

<specifics>
## Specific Ideas

Keep completion deliberately small and finite: one immutable bit on each State, one current-state query, and one canonical construction invariant. Do not create completion events, statechart regions, automatic trigger processing, or implicit dead-end inference.

</specifics>

<deferred>
## Deferred Ideas

- Internal versus external self-transition lifecycle semantics — Phase 28.
- Structured expected domain rejection — Phase 29.
- Builder-first guidance, compatibility deprecations, and complete persistence-adapter parity — Phase 30.
- Final-state validation findings, JSON diagnostics, Mermaid, and PlantUML styling — Phase 31.
- Progressive drone guidance, installed-artifact proof, and feature-local performance evidence — Phase 32.

</deferred>

---

*Phase: 27-explicit-final-states*
*Context gathered: 2026-09-15*
