# Code Conventions

## Code Style

- **Formatter:** Ruff (replaces Black) — line length 88 (default)
- **Linter:** Ruff — runs both format and lint checks
- **Type checker:** `ty` (primary), `mypy` (secondary, for mypyc compat verification)
- **Python version:** >=3.10, uses modern type annotation syntax

## `__slots__` Everywhere

**Mandatory for all classes in `src/fast_fsm/`.** This is a hard performance constraint.

Every class uses `__slots__`:
- `State.__slots__ = ("name",)`
- `CallbackState.__slots__ = ("_on_enter", "_on_exit")`
- `StateMachine.__slots__` = 18 fields (all internal state)
- `TransitionEntry.__slots__ = ("to_state", "condition")`
- `TransitionResult` uses `@dataclass(slots=True)`
- `Condition.__slots__ = ("name", "description")`
- `FSMValidator.__slots__` = 6 fields
- `ValidationIssue.__slots__` = 6 fields
- All condition templates use `__slots__`

**Consequence:** You cannot add dynamic attributes to any FSM object. Use dedicated
slots or `CallbackState` (which has `_on_enter`/`_on_exit` slots).

## Argument Passing Convention

Every condition `.check()` and state callback (`on_enter`, `on_exit`, `can_transition`)
receives `*args, **kwargs`. This pattern is preserved across the entire codebase for
forward compatibility:

```python
# Condition check signature
def check(self, **kwargs: Any) -> bool: ...

# State callback signatures
def on_enter(self, from_state: "State", trigger: str, *args, **kwargs) -> None: ...
def on_exit(self, to_state: "State", trigger: str, *args, **kwargs) -> None: ...
def can_transition(self, trigger: str, to_state: "State", *args, **kwargs) -> bool: ...
```

## Error Handling Pattern

- **Hot path (trigger):** Returns `TransitionResult` with `success=False` instead of raising
  - Use `.raise_if_failed()` for exception-style flow
- **Construction errors:** Raises `ValueError` or `TypeError` immediately
  - Missing states, invalid configs, type mismatches
- **Callback exceptions:** Caught, logged as warnings, never propagated
  - State `on_enter`/`on_exit` exceptions don't crash the FSM
  - Listener exceptions are isolated from each other
- **Async errors:** Same pattern, with `await` in async variants

## Docstring Format

- **Style:** Google-style (parsed by `napoleon` extension)
- **Type annotations:** In signatures only — `sphinx-autodoc-typehints` renders them
- **DO NOT** duplicate types in docstrings
- Performance notes included inline: `Performance: O(1) - Direct dictionary lookup`

Example pattern from `StateMachine.add_state()`:
```python
def add_state(self, state: State) -> None:
    """
    Add a state to the machine.

    Performance: O(1) - Constant time state registration
    Memory: +~32 bytes per state (slots optimization)
    """
```

## Import Patterns

```python
# Standard library imports first
import logging
from abc import ABC
from typing import Optional, Dict, Any, Callable, List, Union, Tuple

# Third-party
from mypy_extensions import mypyc_attr

# Internal imports
from .conditions import Condition, FuncCondition, AsyncCondition, NegatedCondition
```

- Relative imports within the package (`.conditions`, `.core`)
- `condition_templates.py` is the exception: imports via `from fast_fsm import Condition`
  (through `__init__.py`)

## Logging Pattern

- Every `StateMachine` instance gets its own logger: `fast_fsm.{name}`
- Level-gated log calls to avoid string formatting overhead:
  ```python
  if self._logger.isEnabledFor(logging.DEBUG - 5):
      self._logger.log(logging.DEBUG - 5, "%s: ...", self._name, ...)
  ```
- Standard Python logging — no third-party logging libraries

## `@mypyc_attr(native_class=False)` Decorator

Applied to classes in `core.py` that need to be subclassable from interpreted Python
despite being in the compiled module:
- `TransitionError` — users may catch/subclass
- `CompiledFuncCondition` — inherits from uncompiled `Condition`
- `State` — users subclass for custom state behavior

## Factory & Builder Patterns

Multiple construction patterns offered for different use cases:
- `StateMachine(initial_state)` — full control constructor
- `StateMachine.from_states("a", "b", "c")` — quick from names
- `StateMachine.quick_build("idle", [("start", "idle", "running")])` — from transition list
- `StateMachine.from_dict(config)` — from serializable dict (JSON/YAML/TOML friendly)
- `FSMBuilder()` — fluent builder with method chaining
- `simple_fsm()` / `quick_fsm()` — convenience module-level functions

## Property Naming

- Properties are clean (no underscore prefix): `.name`, `.current_state`, `.states`
- Internal storage uses underscore: `_name`, `_current_state`, `_states`
- Read-only properties: `name`, `current_state`, `current_state_name`, `initial_state_name`

## Transition Storage

```python
_transitions: Dict[str, Dict[str, TransitionEntry]]
#              ^state_name  ^trigger  ^(to_state, condition)
```

Two-level dict: `state_name → trigger → TransitionEntry`. O(1) lookup at each level.
