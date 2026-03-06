# ADR-002: `trigger()` returns `TransitionResult` rather than raising exceptions

**Status**: Accepted  
**Date**: 2026-03-06  
**Deciders**: project maintainer + AI pair

---

## Context

When a triggered event cannot complete — because the guard condition fails,
the trigger is not registered from the current state, or the state itself
rejects the transition — the FSM must communicate that outcome to the caller.

The two dominant conventions in FSM libraries are:

1. **Return a result object** and let the caller inspect it.
2. **Raise a typed exception** (`TransitionError`, `GuardFailed`, etc.)
   and let the caller catch it.

This decision also affects whether `trigger()` and `safe_trigger()` have
distinct roles, and how the library behaves in high-throughput control loops
where transitions are expected to fail frequently (e.g., an event fired
optimistically from every state).

---

## Decision

`trigger()` **returns** a `TransitionResult(success, from_state, to_state,
trigger, error)` dataclass for all outcomes — success, guard failure,
unregistered trigger, and state rejection. It does not raise on expected
failure paths.

`safe_trigger()` additionally wraps `trigger()` in a `try/except` to
catch any unexpected exception (bug in user code, condition raising, etc.)
and convert it to a `TransitionResult(success=False, error=...)`.

Callers that want exception semantics can trivially layer them:
```python
result = fsm.trigger("start")
if not result.success:
    raise TransitionError(result.error)
```

---

## Considered Alternatives

### Option A: Return `TransitionResult` for expected failures ✅ Chosen

Described above.

**Pros:**
- Guard failures are *expected* in real systems — a guard that never
  fails is not a guard. Using exceptions for expected paths pollutes
  `try/except` blocks and degrades performance (Python exception handling
  is not free — unwinding the stack, building tracebacks).
- Callers in tight control loops can check `result.success` with a simple
  attribute access — no exception handling overhead.
- `TransitionResult` is a `@dataclass(slots=True)`, so inspection is O(1)
  and memory-cheap.
- `error` field gives a human-readable explanation without needing to
  parse an exception message.

**Cons / tradeoffs:**
- Callers can silently ignore a failed transition if they don't check
  `result.success`. Exception-based APIs make failures harder to ignore.
- Slightly more verbose for callers that always want to assert success.

---

### Option B: Raise `TransitionError` on all failures ❌ Rejected

`trigger()` raises `TransitionError` when any failure occurs; callers
wrap in `try/except`.

**Why rejected:**
- Guard conditions failing is not exceptional — it is the normal
  operation of a guarded FSM. In a traffic-light controller that fires
  `emergency_stop` from every state, most calls will "fail". Encoding
  normal-path behaviour as exceptions is semantically wrong.
- Exception handling has measurable overhead in CPython. In a 250,000
  ops/sec system, exception-centric failure paths would degrade throughput
  for systems that legitimately try many transitions.
- Libraries like `python-statemachine` raise; we explicitly differentiate
  here as a performance and API-clarity choice.

---

### Option C: Raise on unregistered trigger, return on guard failure ❌ Rejected

Distinguish *programming errors* (trigger not registered — you likely
have a bug) from *expected failures* (guard said no) by raising on the
former and returning on the latter.

**Why rejected:**
- The distinction is caller-context-dependent, not intrinsic. In a
  dynamic system where triggers are added at runtime, an unregistered
  trigger from a given state is expected, not a bug.
- Creates two different failure handling patterns in the same codebase,
  increasing cognitive load.
- `TransitionResult.error` already communicates which failure mode
  occurred — callers that want to treat unregistered triggers as bugs
  can check `result.error` and raise themselves.

---

### Option D: Return `Optional[TransitionResult]` (None = success) ❌ Rejected

Some FSM libraries return `None` on success and a result/error on
failure.

**Why rejected:**
- Requires `if result is not None` checks, which are less readable than
  `if result.success`.
- Loses the `from_state`/`to_state`/`trigger` fields on the success path,
  which are useful for logging and auditing.
- `Optional` return types require `None`-guards before any attribute
  access, adding noise.

---

### Option E: `safe_trigger()` only — no bare `trigger()` ❌ Rejected

Expose only `safe_trigger()` which never raises, and remove the
unprotected `trigger()`.

**Why rejected:**
- Removes the ability for callers to distinguish "expected failure I
  handled" from "unexpected exception (bug)". `safe_trigger()` converts
  both to the same `TransitionResult(success=False)`.
- `safe_trigger()` exists specifically for defensive callers (e.g.,
  event loops that cannot afford to crash). Having both gives callers
  the choice.

---

## Consequences

**Positive:**
- High-frequency guard failures incur zero exception-handling overhead.
- `TransitionResult` carries full context (from/to/trigger/error) for
  logging, auditing, and debugging without raising.
- `safe_trigger()` provides a genuine "never crash" guarantee for
  callers that need it.

**Negative / watch-outs:**
- Silent failure is possible if callers don't check `result.success`.
  Documentation and linting should emphasise this.
- Callers migrating from exception-based FSM libraries need to adapt
  their error handling patterns.

**Follow-up work:**
- Consider adding a `result.raise_if_failed()` convenience method so
  callers that prefer exceptions can write one-liners without wrapping
  (fast_fsm-5y3).
