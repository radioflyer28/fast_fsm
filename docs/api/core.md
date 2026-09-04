# Core API

The core module provides the primary FSM classes and utilities.

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

## Exceptions

```{eval-rst}
.. autoclass:: fast_fsm.TransitionError
   :members:
   :show-inheritance:
```

## Safe Trace Logging

`FSMTraceEvent` is a frozen, slotted, ephemeral input for an explicit
`FSMTraceRedactor`. Its complete field set is `operation`, `stage`, `result`,
`trigger`, `source_state`, `destination_state`, `positional_args`,
`keyword_args`, and `error`. Fast FSM constructs this event only for an
explicit redactor; the default trace path never exposes it in a `LogRecord`.

At `logging.DEBUG - 5`, default trace records contain only fixed
`trace_operation`, `trace_stage`, and `trace_result` categories,
`trace_arg_count`, and capped sanitized `trace_keyword_names`. They never
contain trigger/state names, positional or keyword values, exception payloads,
or object representations in the message, arguments, `extra`, or formatted
record. The trace enablement check happens before allocating an event,
traversing values/keys, looking up handlers, or invoking a redactor.

`FSMTraceRedactor = Callable[[FSMTraceEvent], Mapping[str, object] | None]`.
Its output may contain only scalar `operation`, `stage`, `result`, and
`detail` values, with strings at most 200 characters. A raising redactor, a
non-mapping or `None` result, a forbidden key, a non-scalar value, or an
oversized string fails closed: Fast FSM emits only fixed `redaction_failure`
metadata and never falls back to raw payloads.

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

```{eval-rst}
.. autofunction:: fast_fsm.simple_fsm

.. autofunction:: fast_fsm.quick_fsm

.. autofunction:: fast_fsm.configure_fsm_logging

.. autofunction:: fast_fsm.set_fsm_logging_level
```

## Decorators

```{eval-rst}
.. autofunction:: fast_fsm.transition

.. autofunction:: fast_fsm.condition_builder
```
