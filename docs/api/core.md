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
