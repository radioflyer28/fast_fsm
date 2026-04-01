# Architecture

## Architectural Pattern

**Library architecture** — Fast FSM is an importable Python package, not a service or
application. Consumers instantiate `StateMachine` objects in their own code. There is
no server, no event loop, no framework to buy into.

**Core design principle:** Minimize abstraction layers. Performance comes from:
1. `__slots__` on all classes (no `__dict__` overhead)
2. Direct dictionary lookups for transitions (`Dict[str, Dict[str, TransitionEntry]]`)
3. No reflection, introspection, or metaclass magic on hot paths
4. Optional mypyc compilation of `core.py` to C extension

## Layers

```
┌─────────────────────────────────────────────────┐
│  User Code                                       │
│  (imports fast_fsm, creates FSMs, triggers)      │
├─────────────────────────────────────────────────┤
│  Convenience Layer                               │
│  - FSMBuilder (fluent builder pattern)           │
│  - quick_build(), from_dict(), from_states()     │
│  - simple_fsm(), quick_fsm()                     │
│  - condition_builder() decorator                 │
├─────────────────────────────────────────────────┤
│  Core Runtime                                    │
│  - StateMachine.trigger() — O(1) hot path        │
│  - State (ABC), CallbackState                    │
│  - TransitionEntry (to_state + optional guard)   │
│  - TransitionResult (success/failure dataclass)  │
│  - AsyncStateMachine (async trigger_async)       │
├─────────────────────────────────────────────────┤
│  Condition System (uncompiled)                   │
│  - Condition ABC → check(**kwargs) → bool        │
│  - FuncCondition, NegatedCondition               │
│  - AsyncCondition (awaitable check)              │
│  - condition_templates.py (reusable patterns)    │
├─────────────────────────────────────────────────┤
│  Design-Time Tools (zero runtime overhead)       │
│  - validation.py — FSMValidator, scoring         │
│  - visualization.py — Mermaid diagram generation │
└─────────────────────────────────────────────────┘
```

## Data Flow: Trigger Execution

The hot path through `StateMachine.trigger()`:

```
trigger("event", **kwargs)
    │
    ├── _resolve_trigger(trigger)
    │   ├── Look up current_state.name in _transitions dict       ← O(1)
    │   └── Look up trigger name in state's transition dict       ← O(1)
    │       → Returns (TransitionEntry, current_state_name)
    │         or TransitionResult(success=False)
    │
    ├── Check entry.condition (if present)
    │   ├── _sanitize_condition_kwargs(kwargs)                    ← strips non-condition params
    │   └── condition.check(**kwargs)                             ← user-defined guard
    │       → If False: return TransitionResult(success=False)
    │
    ├── Check State.can_transition(trigger, to_state)             ← state permission
    │   → Default: True (overridable in subclasses)
    │
    └── _execute_transition(to_state, trigger, **kwargs)
        ├── old_state.on_exit(to_state, trigger, *args, **kwargs)
        ├── Fire per-state exit callbacks
        ├── Notify on_exit_state listeners
        ├── self._current_state = to_state                        ← state change
        ├── to_state.on_enter(old_state, trigger, *args, **kwargs)
        ├── Fire per-state enter callbacks
        ├── Notify on_enter_state listeners
        ├── Notify after_transition listeners
        └── Return TransitionResult(success=True)
```

## Key Abstractions

### State (ABC in `core.py`)
- Abstract base with `__slots__ = ("name",)`
- Factory method `State.create(name)` returns concrete instance
- Override points: `on_enter()`, `on_exit()`, `can_transition()`, `handle_event()`
- All no-ops by default — zero overhead when not overridden

### CallbackState (extends State)
- Adds `_on_enter` and `_on_exit` callback slots
- Used when users need callback storage on a state without subclassing

### StateMachine
- Core class with `__slots__` (18 slots)
- Internal data: `_states: Dict[str, State]`, `_transitions: Dict[str, Dict[str, TransitionEntry]]`
- Multiple construction patterns: constructor, `from_states()`, `quick_build()`, `from_dict()`
- Listener/observer pattern via `add_listener()`
- State persistence: `snapshot()` / `restore()` / `clone()`

### AsyncStateMachine (extends StateMachine)
- Adds `trigger_async()` for awaiting async conditions and callbacks
- Adds `_async_state_enter_callbacks` and `_async_state_exit_callbacks` slots
- `on_enter_async()` / `on_exit_async()` for async per-state callbacks
- FSMBuilder auto-detects async requirements and returns this type

### DeclarativeState / AsyncDeclarativeState
- Convention-over-configuration: methods named `on_enter_<trigger>`, `handle_<event>`, `guard_<trigger>` are auto-discovered
- Uses `_discover_handlers()` to introspect method names at init time
- `transition` decorator for explicit handler declaration

### FSMBuilder
- Fluent builder pattern with method chaining
- Auto-detects async requirements (returns `AsyncStateMachine` if any `AsyncCondition` found)
- Stores deferred state/transition/callback registrations, applies on `build()`

### Condition System
- `Condition` ABC in `conditions.py` — must stay uncompiled for user subclassing
- `FuncCondition` — wraps a callable as a condition
- `CompiledFuncCondition` — mypyc-compiled variant in `core.py` for hot paths
- `AsyncCondition` — async `check()` for use with `AsyncStateMachine`
- `NegatedCondition` — decorator that inverts another condition
- `condition_templates.py` — library of reusable patterns (Always, Never, Comparison, Regex, And, Or, Not)

### Validation (design-time only)
- `FSMValidator` — reachability analysis, dead states, determinism, test path generation
- `EnhancedFSMValidator` — adds scoring, issue classification, recommendations, export (JSON/MD/text)
- Convenience functions: `validate_fsm()`, `quick_health_check()`, `batch_validate()`, `fsm_lint()`
- Zero runtime overhead — only imported when needed

### Visualization (design-time only)
- `to_mermaid()` — generates Mermaid stateDiagram-v2 syntax
- `to_mermaid_fenced()` — wraps in markdown fenced block
- `to_mermaid_document()` — full HTML document with Mermaid rendering

## Entry Points

| Entry point                     | Purpose                              |
|---------------------------------|--------------------------------------|
| `from fast_fsm import ...`      | Primary API — all public symbols     |
| `from fast_fsm.core import ...` | Direct core module access            |
| `from fast_fsm.conditions import ...` | Condition ABC for subclassing  |
| `from fast_fsm.condition_templates import ...` | Reusable conditions  |
| `from fast_fsm.validation import ...` | Design-time validation         |
| `from fast_fsm.visualization import ...` | Mermaid diagram output      |

## Design Decisions

- **TransitionResult over exceptions** (ADR-002): `trigger()` returns a result object
  instead of raising on failure. This avoids exception overhead on the hot path. Use
  `.raise_if_failed()` for exception-style API.
- **Sparse vs. dense scoring** (ADR-001): Validation scoring adapts to FSM density
  (sparse machines scored differently from dense ones).
- **mypyc boundary** (ADR-003): Only `core.py` compiled; conditions stay interpreted.
