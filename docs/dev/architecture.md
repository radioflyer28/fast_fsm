# Architecture

This page describes the internal architecture of Fast FSM. It is intended for
contributors, AI coding agents, and anyone who needs to understand *how*
Fast FSM works under the hood.

For the authoritative set of design rules, see the
[Constitution](https://github.com/fast-fsm/fast-fsm/blob/main/.specify/memory/constitution.md).

## Module Layout

```text
src/fast_fsm/
├── __init__.py             # Public API — every exported symbol is in __all__
├── core.py                 # StateMachine, AsyncStateMachine, State, FSMBuilder, …
├── conditions.py           # Condition, FuncCondition, AsyncCondition
├── condition_templates.py  # Reusable condition builder functions
└── validation.py           # FSMValidator, EnhancedFSMValidator, scoring, linting
```

**Import DAG (strict — no cycles):**

```text
conditions  →  core  →  validation
```

`validation` may import from `core`; `core` MUST NOT import from `validation`.

## Key Classes

### State Hierarchy

```text
State (ABC, __slots__)
├── CallbackState          # has _on_enter / _on_exit slots
├── DeclarativeState       # @transition decorator support
│   └── AsyncDeclarativeState
└── (user subclasses)
```

- **`State`** — abstract base with `name`, `on_enter()`, `on_exit()`.
  Uses `__slots__` — you cannot add arbitrary attributes.
- **`CallbackState`** — when you need callbacks stored *on the state object*,
  use this class instead of fighting `__slots__`.
- **`DeclarativeState`** / **`AsyncDeclarativeState`** — define transitions
  via the `@transition` decorator on methods.

### StateMachine & AsyncStateMachine

```text
StateMachine (__slots__)
└── AsyncStateMachine      # adds trigger_async(), awaits AsyncCondition.check()
```

Core data structures (all O(1) lookup):

| Attribute | Type | Purpose |
|-----------|------|---------|
| `_states` | `dict[str, State]` | Name → State |
| `_transitions` | `dict[str, dict[str, tuple]]` | `trigger → {from_state → (to_state, condition)}` |
| `_current_state` | `State` | Active state reference |

`trigger()` is a single dictionary lookup into `_transitions`, then a
dictionary lookup by the current state name. No scanning, no iteration.

### Condition System

```text
Condition (ABC, __slots__)
├── FuncCondition          # wraps any Callable[..., bool]
└── AsyncCondition         # async check() — requires AsyncStateMachine
```

All conditions accept `**kwargs` in `check()`. Functions passed to
`FSMBuilder.add_transition()` are auto-wrapped in `FuncCondition`.

### FSMBuilder

Fluent builder that auto-detects whether any condition is `AsyncCondition`
and returns the appropriate machine type:

```python
fsm = (
    FSMBuilder("my_fsm")
    .add_state(idle)
    .add_state(running)
    .add_transition("start", "idle", "running", condition=my_cond)
    .set_initial("idle")
    .build()  # → StateMachine or AsyncStateMachine
)
```

## mypyc Selective Compilation

Fast FSM uses [mypyc](https://mypyc.readthedocs.io/) to compile
performance-critical modules to C extensions. Compilation is **selective** —
only hot-path modules are compiled; modules that users subclass remain
interpreted.

### Compilation Boundary

| Module | Compiled? | Why |
|--------|-----------|-----|
| `core.py` | **Yes** | Contains `StateMachine`, `State`, `trigger()` — the entire hot path |
| `conditions.py` | **No** | Users subclass `Condition` / `FuncCondition` / `AsyncCondition`. mypyc-compiled classes **cannot** be subclassed from interpreted Python. |
| `condition_templates.py` | **No** | Inherits from uncompiled `Condition` |
| `validation.py` | **No** | Design-time only, not on the hot path |

### Build Command

```bash
uv run python setup.py build_ext --inplace
```

This compiles `core.py` via `mypycify()` (configured in `setup.py`,
opt_level 3). The resulting `.so` / `.pyd` file is placed next to the
source in `src/fast_fsm/`.

### Key Constraints

- The library MUST work correctly **with and without** compilation.
  Compilation is an optimization, not a requirement.
- `conditions.py` MUST stay uncompiled — compiling it would break
  every user who writes a custom `Condition` subclass.
- Tests MUST use composition (create instances, call methods), not
  inheritance of `State` or `StateMachine`, to stay compatible with
  the compiled build.

## Performance Architecture

### Why `__slots__` Everywhere

Every class in `src/fast_fsm/` uses `__slots__`. This eliminates `__dict__`
per instance, yielding:

- ~1000× lower memory per FSM vs. dict-based alternatives
- Better cache locality (contiguous attribute storage)
- Faster attribute access

| Metric | Threshold |
|--------|-----------|
| `trigger()` throughput | ≥ 200,000 ops/sec |
| `can_trigger()` throughput | ≥ 400,000 ops/sec |
| Base FSM memory | ≤ 0.5 KB |
| Per-state overhead | ≤ 64 bytes |
| Core operation complexity | O(1) |

### Hot-Path Rules

1. **No validation in dispatch.** `validation.py` is a design-time tool.
   It MUST NOT be called from `trigger()` or `can_trigger()`.
2. **No iteration where lookup suffices.** Transition dispatch is a dict
   lookup, never a loop over candidates.
3. **Lazy logging.** Logger calls are guarded to avoid string formatting
   when logging is disabled.

## Convenience Functions

These are thin wrappers that reduce boilerplate. They do NOT alter the
core dispatch path.

| Function | Purpose |
|----------|---------|
| `simple_fsm(*states, initial=)` | Create a basic FSM from state names |
| `quick_fsm(initial, transitions)` | Create an FSM from a transition list |
| `condition_builder(func)` | Decorator to wrap a function as a named condition |
| `configure_fsm_logging()` | Set up logging for named FSMs |
| `set_fsm_logging_level(level)` | Adjust log verbosity |

## Validation (Design-Time Only)

The validation module provides analysis tools that never affect runtime:

- **`FSMValidator`** — basic reachability/completeness checks
- **`EnhancedFSMValidator`** — scoring (0–100, letter grades), structured
  issues, batch validation, comparison, linting
- **Convenience functions:** `validate_fsm()`, `quick_health_check()`,
  `fsm_lint()`, `batch_validate()`, etc.

All validation lives in `validation.py` and is imported separately from
the core dispatch machinery.
