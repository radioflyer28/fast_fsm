# Phase 28: Same-State Transition Modes - Context

**Gathered:** 2026-09-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Add immutable per-transition `internal` intent and the corresponding runtime lifecycle specialization for canonical self-transitions. Preserve the existing external self-transition as the default, make internal transitions truthful committed events without state exit/re-entry or residency reset, and prove matching synchronous and asynchronous behavior. This phase establishes the canonical carrier, validation, lifecycle, result, history, timing, priority, failure, and cancellation semantics. Complete propagation through every legacy construction adapter and dictionary round trip belongs to Phase 30; diagnostic and diagram rendering belongs to Phase 31; public tutorial and release evidence belongs to Phase 32.

</domain>

<decisions>
## Implementation Decisions

### Transition Mode Model
- **D-01:** `internal` is immutable metadata on each canonical transition entry, exposed as a keyword-only exact built-in boolean with a backward-compatible `False` default. It is not a machine-wide compatibility switch. — **Reversibility:** costly — changing ownership or default semantics later would alter registration signatures, immutable carrier layouts, and existing self-transition behavior.
- **D-02:** `internal=True` is valid only when every canonical source is the identical canonical target object. A multi-source request with any non-self expansion is rejected atomically before publication, and a final source remains invalid under Phase 27 even for an internal self-transition.
- **D-03:** Mode participates in immutable candidate identity. Re-registering an otherwise identical equal-priority candidate with a different mode is a semantic conflict, not an idempotent no-op.

### Lifecycle Boundary
- **D-04:** External self-transitions retain the complete existing order: resolution/timing/guards/permission; before-transition listeners; all source exit surfaces; commit/history with entry-time reset; all destination entry surfaces; declarative transition handler; trigger callbacks; after-transition listeners.
- **D-05:** Internal self-transitions retain resolution, timing, guards, state permission, before-transition listeners, one logical commit/history operation, declarative handler, trigger callbacks, after-transition listeners, result production, tracing, and failure observation.
- **D-06:** Internal self-transitions skip every state lifecycle surface together: `State.on_exit`, registered synchronous and asynchronous source-exit callbacks, exit-state listeners, `State.on_enter`, registered synchronous and asynchronous destination-entry callbacks, and enter-state listeners. The branch occurs once at the lifecycle seam after canonical selection; mode is never inferred from source/target equality.
- **D-07:** Direct-control APIs (`force_state`, `reset`, and `restore`) keep their existing external control lifecycle and do not gain an `internal` option. Internal mode belongs only to registered event transitions.

### Commit, Timing, and Observable Truth
- **D-08:** A successful internal transition is a real logical commit with `committed=True`, the same canonical source and destination, the selected priority, one optional history record, and explicit comparison-neutral `internal=True` metadata in `TransitionResult` and `TransitionRecord`. It is not a guard-only or action-only no-op.
- **D-09:** Internal commit preserves `_state_entered_at`. If history is disabled, it need not read the clock merely to reassign the same state; if history is enabled, the record timestamp describes event commit time without becoming a new entry epoch.
- **D-10:** External self-transition commit continues to reassign the canonical state and reset `_state_entered_at`; therefore `after=` and `within=` eligibility restart only on external re-entry. Repeated internal events cannot extend or restart a residency deadline.
- **D-11:** Mode metadata is observable without being injected into callback keyword arguments, avoiding collision with application payload. Existing callback positional and keyword conventions remain unchanged.

### Failure, Cancellation, and Machine Parity
- **D-12:** A failure in an internal before-transition listener is pre-commit and suppresses the commit, history, and all later work. Failures in retained declarative handlers, trigger callbacks, or after-transition listeners are post-commit and preserve state/history/mode truth exactly as for other transitions.
- **D-13:** Synchronous and asynchronous machines use the same selected mode, priority, stage, committed flag, result, history, and timing rules. Async exit/entry callbacks are skipped for internal transitions at the same lifecycle slots as their synchronous counterparts.
- **D-14:** Cancellation retains the established lifecycle-stage and commit-truth contract: cancellation before the internal commit is uncommitted; cancellation in retained post-commit work is committed; skipped state lifecycle stages cannot originate internal-transition failures or cancellation.
- **D-15:** Guard evaluation and priority fallthrough are mode-neutral. Internal and external candidates resolve in the existing deterministic priority order, and the mode of only the selected immutable entry controls execution.

### Construction Scope for This Phase
- **D-16:** Phase 28 adds the canonical `internal` scalar to `TransitionEntry`, `_TransitionRequest`, `_PreparedTransition`, selected dispatch state, graph transition snapshots, clone replay, and the primary direct/builder registration surfaces needed to author and execute the behavior. — **Reversibility:** costly — these private carrier layouts form the semantic spine consumed by later adapter, persistence, and diagnostic phases.
- **D-17:** Phase 30 remains responsible for proving and completing parity across every retained batch/factory/helper/declarative/deserialization adapter and dictionary round trip. Phase 28 must leave one canonical normalization and lifecycle seam for that fan-out rather than introducing adapter-specific behavior.

### the agent's Discretion
- Exact private helper names and whether the internal lifecycle is expressed as one specialized runner or a tightly bounded branch inside the existing runner, provided the default external path pays at most one predictable boolean branch.
- Additive constructor parameter ordering beyond the locked keyword-only public spelling, bounded error wording, test-file organization, and internal stage bookkeeping.
- Whether `TransitionResult` and `TransitionRecord` always store explicit `False` or use an equivalent comparison-neutral default representation, provided public truth, typing, and backward-compatible positional/equality behavior are preserved.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Scope and Requirements
- `.planning/ROADMAP.md` §Phase 28 — phase goal, dependency, and five success criteria.
- `.planning/REQUIREMENTS.md` §Internal and External Transitions — MODE-01 through MODE-06.
- `.planning/PROJECT.md` — flat-FSM boundary, performance identity, compatibility posture, and mypyc constraint.

### Approved Milestone Research
- `.planning/research/FEATURES.md` §External and Internal Self-Transitions — exact lifecycle truth table, validation, history, result, timing, and direct-control rules.
- `.planning/research/ARCHITECTURE.md` §Transition mode, Lifecycle specialization, Commit and Timing Flow, Sync/Async Parity Contract, and Phase 3 — carrier ownership, one-seam branching, persistence hand-off, and rollout boundary.
- `.planning/research/PITFALLS.md` §Internal Self-Transitions Become No-Ops or External Re-entry — failure modes and required proof strategy.
- `.planning/research/python-statemachine-gap-assessment.md` §Explicit internal versus external self-transitions — motivating comparison and flat-FSM fit.

### Runtime and Prerequisite Contracts
- `.specify/memory/spr-core-api.md` — living construction, priority selection, lifecycle, timing, ownership, history, and result contract.
- `.specify/memory/constitution.md` — performance, testing, compatibility, atomicity, and compiled-boundary requirements.
- `.planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md` — one canonical normalization/publication transaction and evidence rules.
- `.planning/phases/26-canonical-construction-evidence-contract/26-VERIFICATION.md` — verified adapter, clone, pure/native, and atomicity foundation.
- `.planning/phases/27-explicit-final-states/27-CONTEXT.md` — immutable final-state model and no-outgoing-final-source invariant that internal transitions must preserve.
- `.planning/phases/27-explicit-final-states/27-VERIFICATION.md` — verified final-state construction, lifecycle, clone, persistence, typing, and compiled parity.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TransitionEntry`, `_TransitionRequest`, and `_PreparedTransition` in `src/fast_fsm/core.py`: existing slotted/immutable carrier chain for mode metadata and canonical validation.
- `_normalize_transition_request()`, `_apply_transition_requests_owned()`, and `_merge_transition_slot()`: Phase 26 transaction boundary for exact-bool validation, self-target enforcement, atomic fan-out rejection, and candidate identity.
- `_PreparedDispatch`, `_prepare_transition()`, and priority selectors: already return the selected canonical entry, so execution can consume mode without re-resolving or scanning.
- `_execute_transition()` and `_execute_transition_async()`: matching lifecycle order with explicit pre/post-commit stages; the natural single specialization seam.
- `_commit_transition()` and `_state_entered_at`: existing no-user-code state/history/timing commit boundary that can preserve entry time for internal mode.
- `TransitionResult` and `TransitionRecord`: established truthful result/history surfaces for additive comparison-neutral mode metadata.
- `_GraphTransition` / `_GraphSnapshot` and `clone()`: immutable cold-path projection and structural-copy seams that must not erase mode before Phases 30–31 consume it.

### Established Patterns
- Normalize exact public scalar values and canonical endpoints before mutation, build complete replacement slots off-table, and advance graph version only after publication.
- Preserve singleton O(1) dispatch and deterministic priority groups; construction-only validation must not enter the hot selector.
- Treat commit truth as authoritative through post-commit failure and cancellation, with one public-boundary failure finalizer.
- Keep `core.py` mypyc-compatible, hot-path classes slotted, and pure/native observable behavior identical.
- Use deterministic fake clocks and event/barrier handshakes rather than sleeps for timing and async cancellation evidence.

### Integration Points
- Direct `StateMachine.add_transition()` and primary `FSMBuilder.add_transition()` authoring surfaces.
- Batch and helper requests that already converge on `_TransitionRequest`, without completing Phase 30's public compatibility/deprecation work early.
- Sync and async lifecycle runners, transition callbacks/listeners, declarative handlers, failure finalization, tracing, history, and timing windows.
- Public typing in `src/fast_fsm/core.pyi`, pure source behavior, freshly compiled extension behavior, and installed-artifact conformance.

</code_context>

<specifics>
## Specific Ideas

Model internal telemetry refresh as a committed in-state event that runs transition actions and observers without restarting state-owned entry/exit behavior or the residency clock. Model an external self-transition as intentional restart/re-entry. Keep both explicit on individual edges so a single state can support both behaviors under different triggers or priority candidates.

</specifics>

<deferred>
## Deferred Ideas

- Complete propagation through every retained construction adapter, declarative reconstruction path, clone/dictionary persistence contract, and builder-first deprecation guidance — Phase 30.
- Diagnostic validation facts, JSON projection, Mermaid, and PlantUML distinction between internal and external self-transitions — Phase 31.
- Progressive drone tutorial, public documentation, installed-wheel proof, and feature-local performance evidence — Phase 32.
- Expected domain rejection and priority-abort semantics — Phase 29.
- Targetless internal transitions, hierarchical descendant semantics, deferred event queues, and machine-wide mode switches remain outside the v0.5.0 flat-FSM scope.

</deferred>

---

*Phase: 28-same-state-transition-modes*
*Context gathered: 2026-09-16*
