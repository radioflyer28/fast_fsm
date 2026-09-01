# Phase 17: Atomic Transition Lifecycle - Context

**Gathered:** 2026-09-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Define and implement one truthful transition transaction across synchronous and asynchronous machines: a shared pre-commit, commit, and post-commit order; structured failure outcomes; exactly-once failure observation; and coherent committed-only history through callback failure and async cancellation. Reentrancy/concurrency ownership, diagnostic output, and installed-artifact release parity remain in Phases 18–20.

</domain>

<decisions>
## Implementation Decisions

### Lifecycle Stage Order
- **D-01:** Sync and async dispatch use one authoritative lifecycle stage model. Guard resolution and state permission happen before lifecycle callbacks; callback stages are explicitly classified as pre-commit or post-commit rather than inferred from whether state mutation already happened. — **Reversibility:** costly — changing this after v0.3.0 would reorder user side effects across every callback surface.
- **D-02:** The observable order is: before-transition listeners; source state's `on_exit`; registered source exit callbacks (sync then async at this same slot for async machines); exit-state listeners; **commit** current state and append history; destination state's `on_enter`; registered destination enter callbacks (sync then async at this same slot); enter-state listeners; declarative handler; trigger-specific callbacks; after-transition listeners. Registration order is preserved within each collection. — **Reversibility:** costly — applications may depend on this documented order for resource and persistence work.
- **D-03:** Async lifecycle work is awaited at the equivalent sync lifecycle slot. `trigger_async()` must not run the complete sync lifecycle and then append a second async callback tail.
- **D-04:** The first lifecycle callback failure stops later lifecycle callbacks for that transition. A pre-commit failure leaves the source current; a post-commit failure leaves the destination current. No compensating callback or rollback is attempted.

### Truthful Failure Result
- **D-05:** Keep the established value-returning API. Extend `TransitionResult` additively with `committed: bool`, a stable documented stage identifier, and the original exception as `cause`; do not make ordinary `trigger()`/`trigger_async()` callback failures raise by default. — **Reversibility:** costly — these fields become the public v0.3.0 failure-inspection contract.
- **D-06:** A successful transition has `success=True`, `committed=True`, no failure stage, and no cause. Every failed result has `success=False`; pre-commit failures report `committed=False`, while post-commit failures report `committed=True`.
- **D-07:** Stage identifiers are stable lowercase strings documented as part of the result contract. They distinguish at least resolution, guard, state permission, before-transition, source-exit, commit, destination-enter, declarative-handler, trigger-callback, and after-transition failures; private helper types may organize them internally.
- **D-08:** `TransitionResult.raise_if_failed()` remains the opt-in exception boundary and raises `TransitionError` chained from the stored cause. Error text is concise and stage-aware; raw callback payload values are never added to it or logs.

### Exactly-Once Failure Observation
- **D-09:** Route every failed trigger path through one internal failure finalizer. Each registered `on_failed` observer is invoked exactly once, in registration order, whether failure comes from resolution, a guard, state permission, a lifecycle callback, a declarative handler, or cancellation.
- **D-10:** An exception raised by a failure observer never recursively invokes failure handling and never replaces the transition's original result/cause. Continue to the remaining failure observers once each and emit only redacted diagnostic metadata for observer failures.
- **D-11:** Preserve the existing failure-observer call signature for backward compatibility. Structured stage, commit, and cause information belongs on the returned `TransitionResult`; do not inject new reserved payload keys that could collide with caller kwargs.

### Cancellation and Committed History
- **D-12:** The commit section is non-awaiting and indivisible with respect to the event loop: update current state and append one history record together. History records committed transitions even when a later callback fails, and never records a transition that fails or is cancelled before commit.
- **D-13:** `asyncio.CancelledError` is never converted into an ordinary failed result or swallowed. Notify failure observers once using the reached stage, preserve source/no-history before commit or destination/history after commit, then re-raise the original cancellation.
- **D-14:** Do not shield the lifecycle from cancellation and do not attempt rollback after commit. Cancellation stops at the current awaited callback; all later callbacks remain uncalled.

### Agent's Discretion
- Exact private lifecycle context/result-builder types and helper names, provided `core.py` remains the sole mypyc compilation unit and hot-path objects satisfy the slots policy.
- Exact stable stage-string spelling within the categories above, error-message wording, and test helper organization.
- Whether history append is expressed immediately before or after the current-state assignment inside the non-awaiting commit helper, provided no callback/await can observe an intermediate state and failure/cancellation semantics remain coherent.
- How to minimize unconditional-success overhead while retaining the ≥200,000 compiled `trigger()` operations/sec floor.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Contract
- `.planning/ROADMAP.md` — Phase 17 goal, success criteria, dependency on Phase 16, and boundaries with Phases 18–20.
- `.planning/REQUIREMENTS.md` — LIFE-01 through LIFE-06 acceptance requirements.
- `.planning/PROJECT.md` — safe-default posture, public compatibility, performance floor, single compilation unit, and one runtime dependency.

### Upstream Runtime Contracts
- `.planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md` — shared dispatch, declarative exactly-once, guard context, and bounded-history decisions that Phase 17 must preserve.
- `.planning/phases/16-canonical-graph-dispatch-invariants/16-VERIFICATION.md` — executable proof and exact integration seams entering this phase.
- `.specify/decisions/ADR-002-trigger-result-not-exception.md` — established result-value rather than default-exception public contract.
- `.specify/decisions/ADR-003-mypyc-compilation-boundary.md` — `core.py`-only compilation constraint.
- `.specify/memory/spr-core-api.md` — current runtime, builder, guard, declarative, history, and callback behavior.

### Assessment and Quality Policy
- `.planning/codebase/CONCERNS.md` — original callback swallowing, non-transactional async lifecycle, history, and state-atomicity concerns.
- `.github/copilot-instructions.md` — repository quality, compatibility, slots, mypyc, testing, documentation, and performance gates.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_PreparedDispatch`, shared guard preparation, and canonical declarative resolution from Phase 16 already align sync/async work before lifecycle execution.
- `_execute_transition()`, `trigger()`, and `trigger_async()` contain the current callback paths to consolidate into a staged executor without splitting `core.py`.
- `TransitionResult`, `TransitionError`, `TransitionRecord`, bounded `deque` history, and existing callback registries provide the public/result/storage surfaces to extend rather than replace.
- `tools/phase16_isolated_verify.py` provides the proven clean-export pure/native harness pattern; Phase 17 can extend or generalize its explicit inventory and semantic matrix.

### Established Patterns
- Expected transition failures are returned as `TransitionResult`; exception-style flow is opt-in through `raise_if_failed()`.
- Runtime code uses direct dictionary lookup and slot-backed objects; optional behavior stays off the unconditional hot path.
- Tests use real FSM/state/callback objects, exact order/call-count assertions, warnings-as-errors, and fresh pure/compiled contexts rather than mocks or developer-checkout native shadows.
- User callback exceptions are currently caught and logged inconsistently; Phase 17 replaces that scattered behavior with one structured finalization seam.

### Integration Points
- `StateMachine.trigger()` and `AsyncStateMachine.trigger_async()` must enter the same lifecycle contract after shared preparation and permission checks.
- State hooks, per-state callbacks, enter/exit listeners, declarative handlers, trigger callbacks, after listeners, failure observers, and history all connect at the staged executor.
- `FSMBuilder` callback registration and declarative dispatch must inherit the new order without new public builder methods.
- Public docs, ADR/SPR memory, release evidence, and pure/native tests must describe and prove the same stage semantics.

</code_context>

<specifics>
## Specific Ideas

- Treat the commit boundary as a named, test-visible semantic seam even if its helper remains private.
- Use a table-driven sync/async callback recorder so every stage, failure point, result field, state, history entry, and observer count can be compared from the same scenario matrix.
- Cancellation tests should synchronize with events at each awaited stage instead of using timing sleeps.

</specifics>

<deferred>
## Deferred Ideas

- Reentrant transition rejection and independent-caller serialization remain Phase 18.
- Redacted trace payloads, logging-handler ownership, and bounded diagnostics remain Phase 19.
- Installed wheel lifecycle parity across the final release matrix remains Phase 20.

</deferred>

---

*Phase: 17-atomic-transition-lifecycle*
*Context gathered: 2026-09-01*
