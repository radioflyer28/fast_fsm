# Phase 18: Safe Ownership & Concurrency - Context

**Gathered:** 2026-09-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Make each machine safe by default when user callbacks reenter it or independent callers contend for it. Synchronous machines serialize independent threads with per-instance ownership; asynchronous machines serialize same-loop tasks without blocking the event loop, bind explicitly to one loop, and reject unsupported use. The contract covers runtime, graph, history, and callback/listener writes and preserves Phase 17's state/history/cancellation boundaries. Queued reentry, ownership transfer between loops, callback thread offload, diagnostic snapshot consistency, and release-artifact parity remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Ownership Violation Contract
- **D-01:** Reentrant and cross-event-loop ownership violations raise `RuntimeError` immediately as operational precondition failures. They do not become a failed `TransitionResult`, add a lifecycle stage, or introduce a new public exception type. — **Reversibility:** costly — changing the exception surface after v0.3.0 would alter control flow for every guarded public write.
- **D-02:** Reentry by the current execution context is detected before lock acquisition and before transition preparation, guard evaluation, callbacks, or mutation. Reentry is rejected, never queued.
- **D-03:** When an uncaught reentrant call occurs inside a Phase 17 callback, the nested call raises and the existing outer lifecycle classifies that exception at the callback's normal stage. The nested operation never acquires ownership or mutates the machine; a callback may deliberately catch the `RuntimeError` and continue.
- **D-04:** Ownership error messages use stable operation/category metadata only. They must not include trigger positional arguments, keyword values, callback payloads, stored causes, or arbitrary exception text.

### Synchronous Serialization
- **D-05:** Every synchronous machine owns one private synchronization primitive and explicit owner marker stored on the instance; no module-global lock, caller-supplied lock, or shared lock registry is introduced. Ownership checks and uncontended acquisition remain O(1).
- **D-06:** Same-thread reentry fails before acquisition. Independent threads block and serialize one complete public write at a time. The public contract promises neither fairness, timeouts, nor queue ordering beyond mutual exclusion. — **Reversibility:** costly — switching later to fail-if-busy or a fair queue would change scheduling visible to callers.
- **D-07:** The ownership envelope covers the whole public operation: validation/preparation, guard evaluation, lifecycle callbacks, commit, declarative and trigger callbacks, failure observers, and final result construction. Callbacks therefore cannot open an unowned window into partially completed work.
- **D-08:** One `try/finally`-shaped release boundary clears the owner marker and releases the primitive after success, ordinary exceptions, every `BaseException`, and callback failure. The state and history left behind are exactly the coherent pre- or post-commit boundary already defined by Phase 17.

### Async Loop and Task Ownership
- **D-09:** An `AsyncStateMachine` binds permanently to the running event loop of its first async control operation. Later access from a different loop raises `RuntimeError` before lock acquisition; an idle or closed original loop does not authorize silent rebinding. — **Reversibility:** costly — cross-loop rebinding would require an ownership-transfer protocol and invalidate stored synchronization state.
- **D-10:** Independent tasks in the bound loop serialize through one asyncio-native per-machine lock. Waiting never blocks the event-loop thread. Cancellation while waiting propagates unchanged without installing ownership; cancellation while owning follows Phase 17 and releases ownership in `finally`.
- **D-11:** Ownership includes a causal context token in addition to the concrete current task. A child task created inside an owned callback inherits that context and is rejected as reentrant instead of waiting behind the parent and deadlocking it. Tasks created independently outside the owned context serialize normally.
- **D-12:** Synchronous machine mutators inherited by `AsyncStateMachine` may configure an unbound machine under synchronous per-instance protection. After loop binding, they are accepted only from the bound loop's thread while idle; during an async-owned operation they fail immediately, and calls from other threads/loops fail explicitly rather than blocking the event loop.
- **D-13:** Synchronous callbacks on `AsyncStateMachine` continue to run inline on the event-loop thread at their Phase 17 lifecycle slots. Async callbacks are awaited at their matching slots. The library does not infer blocking work or offload callbacks to worker threads. — **Reversibility:** costly — implicit offload would change ordering, context propagation, exception identity, and cancellation behavior.

### Coverage, Cleanup, and Performance
- **D-14:** The shared ownership policy applies to every public machine write: `trigger()`/`trigger_async()`, force/reset/restore, state and transition graph changes (including batch forms), history enable/disable, and callback/listener/failure-observer registration. A registration attempted from an owned callback is rejected; existing snapshot iteration still prevents current-pass observer duplication.
- **D-15:** Read-only properties and helpers do not gain a new cross-field snapshot guarantee in Phase 18. Simple current-state/history reads remain available; stable topology snapshots and diagnostic consistency remain Phase 19. Factories, builders before publication, and independent clones retain their existing Phase 16 semantics and do not share ownership primitives.
- **D-16:** Deterministic tests use barriers, events, and explicit task handshakes rather than sleeps. Evidence must cover sync threads, same-loop tasks, causal child-task reentry, cross-loop rejection, every write family, ordinary exceptions, `BaseException`, cancellation before/after commit, fresh pure/compiled origins, O(1) ownership operations, and the compiled `trigger()` floor of 200,000 operations/second.

### the agent's Discretion
- Private helper/type names, exact slot ordering, and whether owner metadata is represented as identifiers or private token objects, provided the observable rules above and mypyc constraints hold.
- Exact stable wording of redacted `RuntimeError` messages and the organization of table-driven ownership tests.
- Whether closely related public write methods share decorators, context managers, or explicit enter/exit helpers, provided acquisition order and release guarantees are mechanically auditable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Contract
- `.planning/ROADMAP.md` — Phase 18 goal, success criteria, dependency on Phase 17, and Phase 19/20 boundaries.
- `.planning/REQUIREMENTS.md` — OWN-01 through OWN-07 plus deferred FUTR-01, FUTR-03, and FUTR-04 contracts.
- `.planning/PROJECT.md` — v0.3.0 safe-default intent, pre-production compatibility posture, performance floor, one-dependency rule, and single-module compilation constraint.
- `.planning/codebase/CONCERNS.md` — original unsynchronized reentry/concurrency and event-loop blocking concerns that sourced this milestone.

### Existing Runtime Contracts
- `.planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md` — locked lifecycle, commit, failure-observer, history, and cancellation decisions Phase 18 must preserve.
- `.planning/phases/17-atomic-transition-lifecycle/17-VERIFICATION.md` — independently verified implementation seams and fresh pure/compiled gate entering Phase 18.
- `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` — accepted Phase 17 decision record and explicit assignment of ownership/reentry to Phase 18.
- `.specify/memory/spr-core-api.md` — current public runtime, graph, builder, history, callback, and single-mypyc-unit contracts.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StateMachine`'s slotted instance layout in `src/fast_fsm/core.py`: the natural home for per-instance sync ownership state without a global registry.
- `AsyncStateMachine`'s existing slotted subclass and explicit `trigger_async()` boundary: the integration point for loop binding, asyncio locking, task/context ownership, and cancellation-safe release.
- `_prepare_transition()`, `_execute_transition()`, `_execute_transition_async()`, `_commit_transition()`, and `_finalize_failure()`: Phase 16/17 seams that let ownership wrap the whole operation without changing lifecycle order.
- `tools/phase16_isolated_verify.py` and `tests/test_transition_lifecycle.py`: existing fresh-origin and deterministic lifecycle harnesses to extend for Phase 18.

### Established Patterns
- Public misuse/configuration errors already use `RuntimeError` in builder freeze and explicit sync/async conflicts; ordinary transition failures remain value-returning results.
- `core.py` stays the only mypyc compilation unit, runtime classes remain slotted, and no runtime dependency may be added.
- Phase 17 uses fail-fast callback stages, exactly-once failure observation, bare cancellation re-raise, and one non-awaiting commit boundary.
- Tests prefer real machine objects, exact order/cardinality assertions, event handshakes, and asserted pure/freshly compiled module origins.

### Integration Points
- Add ownership slots and private enter/exit helpers around every public machine write in `src/fast_fsm/core.py`.
- Ensure builder/factory-created machines initialize independent ownership state and clones never share locks, loop bindings, owners, or context tokens.
- Extend lifecycle, advanced, listener, builder, async, mypyc/slots, and performance tests without weakening Phase 17 assertions.
- Update README, Quick Start, maintainer architecture, SPR memory, and an append-only ADR with the stable ownership and inline-callback contract.

</code_context>

<specifics>
## Specific Ideas

- Treat callback-created asyncio child tasks as causally reentrant using propagated context, because task identity alone can deadlock when the parent callback awaits the child.
- Keep concurrency tests deterministic with `threading.Event`, barriers, `asyncio.Event`, and task handshakes; timing sleeps are not acceptable proof.
- Record separate uncontended pure and compiled ownership overhead while retaining the existing end-to-end compiled throughput floor.

</specifics>

<deferred>
## Deferred Ideas

- Queued reentrant transitions with ordering and overflow policy — FUTR-01.
- Cross-event-loop ownership transfer or rebinding — FUTR-03.
- Automatic worker-thread execution for synchronous async-machine callbacks — FUTR-04.
- Stable multi-consumer diagnostic graph snapshots and read consistency — Phase 19.
- Installed wheel/sdist parity and final release proof — Phase 20.

</deferred>

---

*Phase: 18-safe-ownership-concurrency*
*Context gathered: 2026-09-01*
