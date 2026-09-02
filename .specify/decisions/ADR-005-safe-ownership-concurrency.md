# ADR-005: Safe per-machine ownership and concurrency

**Status**: Accepted  
**Date**: 2026-09-02  
**Deciders**: project maintainer + AI pair

---

## Context

ADR-004 makes a single transition's lifecycle, commit point, failure result,
and cancellation truth explicit, but it deliberately left reentrancy and
independent callers to Phase 18. Without ownership admission, a callback could
mutate a machine during its own transition, independent threads could overlap,
and async tasks could deadlock or silently use different event loops. The
solution must preserve the Phase 17 state/history boundary, keep `core.py` as
the sole mypyc compilation unit, and make no new public scheduler or artifact
promise.

## Decision

1. **D-01: precondition errors.** Reentrant and cross-loop ownership misuse
   raises a stable, redacted `RuntimeError` immediately; it is neither a
   `TransitionResult` failure nor a new lifecycle stage or exception type.
2. **D-02: admission before work.** Current-execution reentry is detected
   before a lock, preparation, guard, callback, lifecycle, or mutation. It is
   rejected rather than queued.
3. **D-03: outer lifecycle ownership.** An uncaught nested ownership error is
   classified by the existing outer callback stage. A callback may catch the
   error and continue, but the nested operation never owns or mutates.
4. **D-04: redacted errors.** Ownership text contains only stable operation and
   category metadata; it excludes trigger arguments, keyword values, callback
   payloads, stored causes, and arbitrary exception text.
5. **D-05: per-instance synchronous ownership.** Every synchronous machine has
   a private synchronization primitive and owner marker. There is no global,
   caller-supplied, or shared lock registry; checks and uncontended acquisition
   remain O(1).
6. **D-06: sync serialization.** Same-thread reentry fails before acquisition;
   independent threads serialize one full public write. Fast FSM promises
   mutual exclusion, not fairness, timeout, or queue ordering.
7. **D-07: complete envelope.** Ownership covers validation/preparation,
   guards, lifecycle callbacks, commit, declarative/trigger callbacks, failure
   observers, and result construction, so callbacks cannot open a partial-work
   window.
8. **D-08: cleanup.** One `try`/`finally` release shape clears owner state and
   releases after success, ordinary exception, every `BaseException`, or
   callback failure, preserving Phase 17's coherent pre/post-commit boundary.
9. **D-09: permanent loop identity.** The first async control operation binds
   an `AsyncStateMachine` to its exact running loop. A different loop raises
   before lock acquisition; an idle or closed old loop does not allow rebinding.
10. **D-10: async serialization and cancellation.** Independent tasks in the
    bound loop await one per-machine asyncio lock without blocking the loop.
    Cancellation while waiting propagates without ownership; cancellation while
    owning follows Phase 17 and releases in `finally`.
11. **D-11: causal reentry.** A module-level `ContextVar` root complements task
    identity. A child task created in an owned callback inherits the root and
    raises rather than waits behind its parent; independently-created tasks
    serialize normally.
12. **D-12: mixed-mode admission.** Inherited sync mutators use a short,
    non-awaiting per-instance reservation gate for first-use configuration. It
    is never held across an await, callback, lifecycle, or mutation. Once
    bound, only the bound loop's thread may write while idle; async-owned and
    foreign thread/loop callers fail explicitly rather than blocking the loop.
13. **D-13: callback execution.** Synchronous callbacks on an async machine
    run inline on the event-loop thread; async callbacks are awaited at their
    existing slots. Fast FSM does not infer blocking work or offload it.
14. **D-14: full write coverage.** The policy covers `trigger()`/
    `trigger_async()`, direct control, graph/state/transition mutations,
    history enable/disable, and listener/callback/failure-observer registration.
    Reentrant registration is rejected; independent snapshot iteration remains
    defensive.
15. **D-15: read and factory boundary.** Read helpers gain no cross-field
    snapshot guarantee. Builders before publication, factories, and clones keep
    their Phase 16 semantics and never share ownership primitives.
16. **D-16: deterministic evidence.** Tests use barriers, events, and explicit
    handshakes, not sleeps, across sync threads, same-loop tasks, causal
    reentry, loops, writers, `BaseException`, cancellation, fresh pure/native
    origins, O(1) checks, and the compiled 200,000 `trigger()` ops/sec floor.

`safe_trigger()` owns once before its ordinary `Exception` conversion barrier:
ownership, loop, causal-root, foreign-thread, and busy failures raise; ordinary
post-admission exceptions retain value conversion. Public boundaries delegate
only to private already-owned bodies, avoiding public-to-public self-reentry.

## Considered Alternatives

### Option A: Per-machine admission with native synchronization ✅ Chosen

Private `threading.Lock` and `asyncio.Lock` primitives supply exclusion while
the library owns the documented admission policy, causal root, loop identity,
and cleanup. This keeps the fast path local to one machine and lets ADR-004's
lifecycle remain unchanged inside the envelope.

### Option B: RLock or task identity alone ❌ Rejected

An `RLock` silently permits the same reentry that this ADR forbids. Task
identity alone misses callback-created child tasks, which would wait behind
their parent and deadlock.

### Option C: Global/shared lock or a thread lock held across await ❌ Rejected

A shared lock couples unrelated machines and changes contention behavior. A
thread lock across an await can block an event-loop thread; neither design
satisfies D-05, D-10, or D-12.

### Option D: Loop rebinding, automatic offload, or public-to-public delegation ❌ Rejected

Rebinding requires an explicit ownership-transfer protocol. Automatic callback
offload changes ordering, context, exception identity, and cancellation.
Public delegation acquires twice and appears as forbidden same-owner reentry.
They are not implicit compatibility behaviors.

## Consequences

**Positive:**
- Every public write has one auditable ownership boundary and deterministic
  cleanup.
- Sync callers serialize without a global bottleneck; async callers remain
  responsive and causal child-task deadlocks are rejected.
- `safe_trigger()` retains ordinary value failures without disguising misuse.
- Fresh pure/native and hosted exact-SHA evidence can test the same contract.

**Negative / watch-outs:**
- Same-owner callback writes now fail immediately and applications must choose
  a later independent operation or catch the stable `RuntimeError` deliberately.
- Loop binding is permanent, and scheduler fairness/timeout behavior is not an
  API commitment.
- Ownership messages intentionally trade payload detail for stable redaction.

**Deferred follow-up:**
- Queued reentry is FUTR-01; cross-loop transfer/rebinding is FUTR-03; callback
  worker offload is FUTR-04.
- Phase 19 owns stable diagnostic/topology snapshots and read consistency.
- Phase 20 owns installed-wheel/sdist parity; source-tree pure/native evidence
  and an exact-SHA CI matrix do not claim installed-artifact parity.
