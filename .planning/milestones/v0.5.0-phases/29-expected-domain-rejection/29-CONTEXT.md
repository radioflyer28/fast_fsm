# Phase 29: Expected Domain Rejection - Context

**Gathered:** 2026-09-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Add one public, bounded `TransitionRejected(code)` signal for expected domain
rejection during pre-commit eligibility evaluation. Guards, declarative guards,
and state-permission checks may raise it; the selector converts it into a
structured uncommitted result, stops the complete priority group, and preserves
sync/async parity. Ordinary false eligibility still falls through, unexpected
exceptions remain failures, and the same signal raised after selection remains
an ordinary staged execution failure.

This phase does not add a validator family, a rejection-listener family, richer
localized rejection payloads, queued processing, rollback, or statechart
behavior. Broader diagnostic/serialization projection belongs to Phase 31 and
public examples/guidance belong to Phase 32.

</domain>

<decisions>
## Implementation Decisions

### Rejection-Code Contract

- **D-01:** `TransitionRejected(code)` accepts an exact `str`; enums and arbitrary string-convertible objects are rejected. — **Reversibility:** costly — widening the accepted public input later is additive, but narrowing a released contract would require a compatibility cycle.
- **D-02:** Codes are non-empty, at most 64 characters, and match `[a-z][a-z0-9_.-]*` exactly.
- **D-03:** Construction validates eagerly without trimming, case-folding, or other normalization: non-strings raise `TypeError`; empty, oversized, or malformed strings raise `ValueError`.

### Result and Exception API

- **D-04:** `TransitionResult` stores one comparison-neutral `rejection_code: str | None`; a read-only `rejected` property derives status from that field. Do not store a second boolean or replace the existing result model with a status enum. — **Reversibility:** costly — this becomes the public result contract consumed by application code and later diagnostics.
- **D-05:** A rejected result has `cause=None` and bounded `error="Transition rejected: <code>"`; the validated code, not the error string, is the authoritative identifier.
- **D-06:** `TransitionResult.raise_if_failed()` continues to raise `TransitionError` with the originating result attached. `TransitionRejected` is solely the control signal raised inside eligibility hooks, not the exception emitted when consuming a failed result.
- **D-07:** `rejection_code` uses `compare=False` so legacy result equality remains stable, but stays visible in `repr` for debugging.

### Condition Composition

- **D-08:** `AndCondition` and `OrCondition` propagate `TransitionRejected` immediately and evaluate no later child. Rejection is terminal regardless of boolean operator.
- **D-09:** `NotCondition` and `NegatedCondition` propagate rejection unchanged; they negate only boolean eligibility.
- **D-10:** The propagation rule applies recursively across synchronous, asynchronous, deferred, and nested composition. Async cancellation remains cancellation and must never become rejection.
- **D-11:** Direct condition evaluation outside an FSM lets `TransitionRejected` propagate normally. Only an approved FSM eligibility boundary converts it into a `TransitionResult`.

### Observer, Query, and Metadata Behavior

- **D-12:** Trigger operations notify the existing failure-observer family exactly once using its unchanged callback signature and the rejected result. Do not add callback arguments or a parallel listener family.
- **D-13:** `can_trigger()` and `can_trigger_async()` stop selection and return `False` for expected rejection without mutation, observer notification, history, or trace events. Callers use `trigger*()` when they need the code.
- **D-14:** Runtime logging for expected rejection is metadata-only at debug level and may include the validated code; it emits no warning, traceback, or exception representation.
- **D-15:** Rejected results preserve the existing pre-commit failure metadata: source, trigger, lifecycle stage, selected priority, and internal mode. They do not add a history record or expose a new destination field.

### the agent's Discretion

- Exact private helper names, carrier layout, and test-file partitioning are left to research and planning, provided the public and semantic decisions above remain intact.
- The fixed internal constants used for validation and bounded error text may follow established naming conventions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase Contract

- `.planning/PROJECT.md` — milestone goal, performance identity, compatibility posture, and explicit flat-FSM boundary.
- `.planning/REQUIREMENTS.md` — authoritative REJECT-01 through REJECT-09 requirements and later-phase boundaries.
- `.planning/ROADMAP.md` — Phase 29 goal, five success criteria, dependencies, and sequencing rationale.

### Prior Research and Settled Runtime Semantics

- `.planning/research/FEATURES.md` — three-way eligibility outcome, rejection/result recommendations, anti-features, and scenario matrix.
- `.planning/research/SUMMARY.md` — consolidated v0.5.0 architecture, pitfalls, and scope recommendations.
- `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md` — selected-entry, priority, failure, cancellation, and internal-mode decisions that Phase 29 must preserve.
- `.specify/memory/spr-core-api.md` — living core selection, lifecycle, result, ownership, and performance contract.

### Existing Public Documentation

- `docs/api/core.md` — current public result, exception, state, machine, and async API documentation.
- `docs/api/conditions.md` — current condition and composition surface.
- `docs/dev/architecture.md` — documented hot-path and module-boundary constraints; live source remains authoritative if this older narrative differs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `TransitionResult` and `TransitionError` in `src/fast_fsm/core.py`: additive `compare=False` metadata and the existing opt-in exception boundary are the natural public result seam.
- `_select_transition_sync()`, `_select_sync_candidate()`, and their async counterparts: already distinguish group fallthrough (`None`), terminal `TransitionResult`, and selected `_PreparedDispatch` before lifecycle work.
- `_build_failure_result()` and `_finalize_failure()`: central construction and exactly-once observer paths for rejected trigger results.
- `AndCondition`, `OrCondition`, `NotCondition`, `NegatedCondition`, and deferred async guard helpers in `src/fast_fsm/conditions.py`: existing composition surfaces that must preserve the control signal.
- Existing task-local async selection metadata: selected priority/internal mode and cancellation finalization already establish parity and reuse patterns.

### Established Patterns

- Direct singleton selection stays separate from finite local group scanning; no unrelated topology scan, sort, reflection, or success-path allocation may be introduced.
- Ordinary false timing/guard/declarative/permission outcomes are scan control only inside a candidate group; unexpected exceptions and cancellation are terminal.
- Failure results carry bounded public text plus an optional non-repr `cause`; rejection instead uses a validated scalar code and `cause=None`.
- Public runtime carriers and stubs maintain exact mypyc-safe field order, slots, and pure/native parity.
- The public facade in `src/fast_fsm/__init__.py` and `core.pyi` must expose new public symbols consistently.

### Integration Points

- Catch and convert `TransitionRejected` only around transition guards, declarative guards, and state-permission hooks in both selectors.
- Preserve the signal through condition composition and direct evaluation; do not catch it in lifecycle callbacks as an expected outcome.
- Populate selected priority/internal metadata on rejection before the trigger boundary finalizes failure observation.
- Keep `can_trigger*()` on the same selection ordering while returning only `False` and avoiding finalization or diagnostics.
- Extend structural, typing, lifecycle, priority, composition, cancellation, and pure/native tests rather than creating an isolated alternate dispatch path.

</code_context>

<specifics>
## Specific Ideas

- Example valid codes include `mission.altitude_limit`, `battery.low`, and `link-lost`; validation is exact and does not canonicalize user input.
- The classification triad is: ordinary false → local fallthrough; `TransitionRejected(code)` → structured expected rejection; every other exception → unexpected staged failure.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Richer localized rejection details remain the existing `FUTR-04` future requirement unless stable codes prove insufficient.

</deferred>

---

*Phase: 29-Expected Domain Rejection*
*Context gathered: 2026-09-17*
