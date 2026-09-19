# Core API

The core module provides the primary FSM classes and utilities.

## Construction hierarchy

Use `FSMBuilder` for new programmatic topology: it accepts caller-owned
`State` objects, stages the complete graph, and publishes a machine only when
`build()` succeeds. `StateMachine` and `AsyncStateMachine` constructors remain
public, supported **advanced** interfaces for deliberate incremental topology
control or an explicitly managed machine identity. Use `from_dict()` only to
reconstruct serialized topology; it is the persistence adapter, not another
general-purpose programmatic builder.

`simple_fsm()`, `quick_fsm()`, `StateMachine.quick_build()`, and
`StateMachine.from_states()` are retained warned compatibility boundaries
through v0.5.x and may be removed no earlier than v0.6.0. For new code,
replace their programmatic construction role with `FSMBuilder`; do not replace
them with `from_dict()` unless the input is serialized topology.

## State Classes

```{eval-rst}
.. autoclass:: fast_fsm.State
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.CallbackState
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.DeclarativeState
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.AsyncDeclarativeState
   :members:
   :undoc-members:
   :show-inheritance:
```

## State Machine Classes

### Priority-aware guarded candidates

`StateMachine.add_transition()` and `FSMBuilder.add_transition()` accept a
keyword-only `priority=` argument. Multiple transitions may share a source
state and trigger as long as every candidate in that slot has a distinct
priority. Lower integer values are evaluated first; registration order does
not affect the winner.

```{testcode}
from fast_fsm import FSMBuilder, FuncCondition, State

active = State("active")
fallback = State("fallback")
halted = State("halted")

fsm = (
    FSMBuilder(active)
    .add_state(fallback)
    .add_state(halted)
    .add_transition(
        "tick", "active", "halted",
        FuncCondition(lambda **data: data.get("fatal", False)),
        priority=0,
    )
    .add_transition(
        "tick", "active", "fallback",
        FuncCondition(lambda **data: data.get("degraded", False)),
        priority=10,
    )
    .build()
)

result = fsm.trigger("tick", fatal=False, degraded=True)
print(result.to_state, result.priority)
```

```{testoutput}
fallback 10
```

Priority must be an exact built-in `int`; Boolean values, `IntEnum` members,
integer subclasses, floats, and strings are rejected. A false guard falls
through to the next candidate. A raised guard exception, asynchronous
cancellation, or eligible candidate stops selection. If no candidate is
eligible, the result fails at the `selection` stage with `priority=None` and
the machine remains in its source state.

The selected priority is available on `TransitionResult` and, when history is
enabled, `TransitionRecord`. It is also preserved by serialization and shown
by diagnostics and diagram renderers. `add_transitions()` accepts a five-item
row `(trigger, source, target, condition, priority)`.

```{eval-rst}
.. autoclass:: fast_fsm.StateMachine
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.AsyncStateMachine
   :members:
   :undoc-members:
   :show-inheritance:
```

## Builder

`FSMBuilder` is the primary API for ordinary programmatic construction. It
stages explicit transitions and topology-complete declarative definitions as
ordinary requests, then sends their combined collection through one canonical
validation and publication transaction. Decorator guards remain state-owned,
so importing declarations does not duplicate guard evaluation. There is no
parallel declarative topology registrar.

```{eval-rst}
.. autoclass:: fast_fsm.FSMBuilder
   :members:
   :undoc-members:
   :show-inheritance:
```

## Data Classes

```{eval-rst}
.. autoclass:: fast_fsm.TransitionResult
   :members:
   :undoc-members:

.. autoclass:: fast_fsm.TransitionRecord
   :members:
   :undoc-members:
```

## Expected eligibility rejection

`TransitionRejected(code)` is a control signal for an expected domain outcome
while Fast FSM is deciding whether an edge is eligible. `code` must be an exact
built-in `str`, contain 1–64 ASCII characters, and match
`[a-z][a-z0-9_.-]*` without trimming, case-folding, or coercion. For example,
`battery.low` and `mission.altitude_limit` are valid codes.

The selector has three distinct outcomes: a false guard keeps scanning a local
priority group; `TransitionRejected` stops that group with a failed result; an
ordinary exception remains an ordinary staged failure. Cancellation also keeps
its existing cancellation behavior. Fast FSM converts the signal only when it
is raised by a transition guard, a declarative guard, or a state's permission
hook. Signals raised by timing, lifecycle callbacks/listeners, declarative
actions, trigger callbacks, after-transition listeners, observers, or trace
redactors are not expected rejections; they retain the normal failure or
process-control behavior of that boundary.

An expected-rejection `TransitionResult` has `success=False`, `rejected=True`,
the validated `rejection_code`, `cause=None`, and
`error="Transition rejected: <code>"`. It is uncommitted and destination-free,
but retains source, trigger, selection stage, priority, and internal-mode
metadata. `raise_if_failed()` still raises `TransitionError` with the result
attached. `can_trigger()` and `can_trigger_async()` instead return `False`
without changing state or history and without trace or failure-observer work.

Condition evaluation outside a machine propagates `TransitionRejected`
normally. Debug logging records only the validated code; it never formats the
signal, a traceback, or caller-provided values.

## Exceptions

```{eval-rst}
.. autoclass:: fast_fsm.TransitionError
   :members:
   :show-inheritance:

.. autoclass:: fast_fsm.TransitionRejected
   :members:
   :show-inheritance:
```

## Safe Trace Logging

`FSMTraceEvent` is a frozen, slotted, ephemeral input for an explicit
`FSMTraceRedactor`. Its complete field set is `operation`, `stage`, `result`,
`trigger`, `source_state`, `destination_state`, `positional_args`,
`keyword_args`, `error`, and nullable `priority`. Fast FSM constructs this
event only for an explicit redactor; the default trace path never exposes it
in a `LogRecord`.

At `logging.DEBUG - 5`, default trace records contain only fixed
`trace_operation`, `trace_stage`, and `trace_result` categories,
`trace_arg_count`, capped sanitized `trace_keyword_names`, nullable
`trace_priority`, nullable `trace_mode`, nullable `trace_rejection_code`, and
Boolean `trace_current_final`. `trace_mode` is `internal`, `external_self`, or
`external` when a candidate was selected, and `None` when selection is unknown.
An expected rejection exposes only its validated ASCII code (at most 64
characters); ordinary false or unexpected failures use `None`.
`trace_current_final` reads the canonical **current** state's explicit final
flag after an owned attempt. On a pre-commit rejection it does not claim that
the destination is final. The selected priority and mode can still be known
when the destination is withheld from a rejection result. These fields never
contain trigger/state names, positional or keyword values, exception payloads,
or object representations in the message, arguments, `extra`, or formatted
record. The trace enablement check happens before allocating an event,
traversing values/keys, looking up handlers, or invoking a redactor.

`FSMTraceRedactor = Callable[[FSMTraceEvent], Mapping[str, object] | None]`.
Its output may contain only scalar `operation`, `stage`, `result`, `detail`,
and `priority` values, with strings at most 200 characters. An ordinary `Exception`
raised by a redactor, a non-mapping or `None` result, a forbidden key, a
non-scalar value, or an oversized string fails closed: Fast FSM emits only
fixed `redaction_failure` metadata and never falls back to raw payloads.
That fallback has `None` for priority, mode, rejection code, and current-final
fields; it does not reuse potentially sensitive facts from the failed redactor.
Disabled TRACE performs no semantic projection or current-final read.
Non-`Exception` `BaseException` subclasses (including `KeyboardInterrupt`,
`SystemExit`, and `asyncio.CancelledError`) are not converted: they emit no
trace record and are re-raised.

`configure_fsm_logging(level=logging.WARNING, logger_name="fast_fsm",
format_string="%(message)s", *, propagate=None, redactor=None)` returns
`FSMLoggingHandle`. It marks its own stream handler and preserves every
application-owned handler, filter, formatter, order, and open state. Repeated
configuration removes and closes only a marked library handler. `propagate=None`
preserves application propagation; a Boolean makes a deliberate library
change.

`FSMLoggingHandle.restore()` is idempotent. A handle removes only its exact
owned handler, and restores level/propagation only when its generation is
still current and the logger still has the library-configured value. Thus an
old, reconfigured, or out-of-order handle cannot remove a current library
handler or overwrite a later application choice. `set_fsm_logging_level(
verbosity="warning", logger_name="fast_fsm", *, propagate=None,
redactor=None)` accepts `debug`, `info`, `warning`, `error`, `critical`,
`off`, or `trace` and delegates to this same configuration seam.

```{eval-rst}
.. autoclass:: fast_fsm.FSMTraceEvent
   :members:

.. autoclass:: fast_fsm.FSMLoggingHandle
   :members:
```

## Convenience Functions

### Retained compatibility constructors

The convenience constructors below remain exported and callable during v0.5.x,
but each invocation emits one actionable `DeprecationWarning` at the caller.
`simple_fsm()`, `quick_fsm()`, `StateMachine.quick_build()`, and
`StateMachine.from_states()` may be removed no earlier than v0.6.0. Use
`FSMBuilder` for programmatic construction; use `StateMachine.from_dict()` or
`AsyncStateMachine.from_dict()` only for serialized topology reconstruction.

```{eval-rst}
.. autofunction:: fast_fsm.simple_fsm

.. autofunction:: fast_fsm.quick_fsm

.. autofunction:: fast_fsm.configure_fsm_logging

.. autofunction:: fast_fsm.set_fsm_logging_level
```

## Decorators

When a `DeclarativeState` is staged in an `FSMBuilder`, its topology-complete
`@transition` declarations are derived into the same canonical request
transaction as explicit builder transitions. The handler and its guard remain
on the state-owned execution seam, preserving exactly-once behavior.

```{eval-rst}
.. autofunction:: fast_fsm.transition

.. autofunction:: fast_fsm.condition_builder
```
