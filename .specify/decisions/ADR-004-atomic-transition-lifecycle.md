# ADR-004: Atomic transition lifecycle with truthful value results

**Status**: Accepted  
**Date**: 2026-09-01  
**Deciders**: project maintainer + AI pair

---

## Context

Fast FSM previously had callback paths that could catch-and-continue, append
history after later work, and run asynchronous per-state callbacks as a tail
after a synchronous transition. That made a reported successful transition
ambiguous when a user callback failed, and could leave state/history difficult
to interpret around cancellation.

ADR-002 already establishes that ordinary `trigger()` calls return a value
rather than raising expected transition failures. ADR-003 establishes that
`core.py` remains the single mypyc compilation unit. This decision freezes the
callback order, commit point, result information, observer behavior, and
cancellation semantics within those existing boundaries.

## Decision

1. **One stage model (D-01).** Sync and async dispatch share one stable stage
   catalog. Resolution, guard evaluation, and state permission complete before
   user lifecycle callbacks.
2. **One observable order (D-02).** Ordinary dispatch runs before-transition
   listeners; source `on_exit`; registered source exit callbacks; exit-state
   listeners; **commit**; destination `on_enter`; registered destination enter
   callbacks; enter-state listeners; the declarative handler; trigger
   callbacks; and after-transition listeners. Every registry keeps its own
   registration order.
3. **Same-slot async work (D-03).** `trigger_async()` runs synchronous
   callbacks inline and awaits async source/destination callbacks at their
   matching lifecycle slot, not as a tail.
4. **Fail fast, no rollback (D-04).** The first ordinary lifecycle callback
   failure suppresses the later suffix. Pre-commit failure keeps the source;
   post-commit failure keeps the destination. Fast FSM does not attempt
   compensating callbacks or rollback.
5. **Additive value result (D-05--D-08).** `TransitionResult` keeps its first
   five positional fields and adds `committed`, stable lowercase `stage`, and
   an original exception `cause` hidden from repr/equality. Success is
   `success=True`, `committed=True`, `stage=None`, `cause=None`; failures carry
   truthful commit status. `raise_if_failed()` remains opt-in and chains a
   concise `TransitionError` from `cause` when present, without exposing raw
   callback payloads or cause text in result/error/log output.
6. **One failure-observer finalizer (D-09--D-11).** Every ordinary failure uses
   one finalizer. It calls each registered
   `on_failed(trigger, from_state, error, **kwargs)` observer exactly once in
   order. Observer exceptions are isolated, never recurse, never replace the
   original result/cause, and never add reserved keys to user kwargs.
7. **Commit-owned history and native cancellation (D-12--D-14).** The
   non-awaiting commit updates current state and appends history together.
   Cancellation before commit retains source/no record; cancellation after it
   retains destination/one record. `CancelledError` is observed once by the
   failure finalizer and then bare-re-raised unchanged. The lifecycle uses no
   shielding, rollback, or suffix continuation.

`force_state()`, `reset()`, and `restore()` retain their direct-control
compatibility behavior outside the ordinary trigger transaction. `core.py`
remains the sole mypyc unit and no dependency, public builder method, or
callback signature is added.

## Considered Alternatives

### Option A: One staged, commit-aware value-result transaction ✅ Chosen

The chosen model gives callers one documented order, a truthful result, and a
single place to observe failure without making ordinary failed triggers raise.
It preserves ADR-002's value-returning API, the existing callback signatures,
and ADR-003's compilation boundary.

### Option B: Catch callback errors and continue ❌ Rejected

Continuing after a failed user callback can report success after only a prefix
of side effects. It also makes callback ordering and state/history outcomes
unreliable to reason about.

### Option C: Run all async callbacks after the synchronous lifecycle ❌ Rejected

An async tail changes observable order and places source exit work after the
commit/destination work it is meant to surround. Paired runners make the same
semantic slot explicit in both machine types.

### Option D: Raise ordinary lifecycle failures or hide their causes ❌ Rejected

Raising by default would reverse ADR-002. Hiding the original cause would make
an opt-in exception boundary unable to preserve debugging identity. The result
keeps the cause private from text representations while allowing direct,
intentional inspection and exception chaining.

### Option E: Roll back, shield cancellation, or compensate automatically ❌ Rejected

User callbacks may perform arbitrary external I/O, so Fast FSM cannot make
them transactional. Shielding or rollback would either hide native
cancellation or misrepresent external effects; applications own explicit
compensation.

## Consequences

**Positive:**
- Sync and async callers receive the same documented lifecycle truth.
- State and optional history have one coherent commit boundary.
- Failure observers remain compatible while becoming exactly-once and
  non-recursive.
- Compiled success-path performance remains guarded by the fixed 200,000
  operations/second floor and fresh source-tree conformance.

**Negative / watch-outs:**
- A post-commit failure may leave application side effects and machine state at
  the destination; applications that need compensation must own it.
- `cause` is intentionally an object reference for deliberate inspection, not
  a safe logging field.
- The fixed public order is costly to change after release.

**Deferred follow-up:**
- Reentrancy, ownership, and independent caller serialization are Phase 18.
- Diagnostic/logging architecture and bounded diagnostic output are Phase 19.
- Installed-wheel lifecycle parity is Phase 20; source-tree pure/native proof
  in this phase is not an installed-artifact claim.
