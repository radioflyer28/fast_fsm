# Fast FSM — High-Performance Finite State Machine Library

A blazing-fast, memory-efficient finite state machine library for Python that
outperforms popular alternatives by **5–20×** while providing a clean,
intuitive API.

**Full documentation:** after installing, run
`uv run sphinx-build -b html docs docs/_build/html` and open
`docs/_build/html/index.html`, or browse the Markdown sources under `docs/`.

## Performance Highlights

- **~250,000 transitions/sec** — maintains parity with hand-tuned implementations
- **Ultra-low memory footprint** — ~1,000× more efficient than popular libraries
- **Zero-overhead design** — `__slots__` optimization, direct dictionary lookups
- **Production ready** — 290 tests, optional validation, mypyc compilation

| Library | Speed (ops/sec) | Memory | Ratio |
|---------|----------------|--------|-------|
| **fast_fsm** | ~250K | ~0.2 KB | baseline |
| python-statemachine | ~30K | ~25–40 KB | 8× slower, 125× more memory |
| transitions | ~50K | ~30–50 KB | 5× slower, 150× more memory |

*100,000 transitions with realistic usage patterns.*
*Run with* `uv run python benchmarks/benchmark_fast_fsm.py`

## Requirements

**Python ≥ 3.10** — requires `@dataclass(slots=True)` (PEP 681).

**Runtime dependency:** `mypy-extensions ≥ 1.0` (provides the `@mypyc_attr` decorator).

### Compatibility Matrices

**User — Python × mypy-extensions** (runtime)

| Python | mypy-extensions 1.0.0 (`requires_python ≥3.5`) | mypy-extensions 1.1.0 (`requires_python ≥3.8`) |
|--------|------------------------------------------------|-------------------------------------------------|
| 3.10 | ✅ | ✅ |
| 3.11 | ✅ | ✅ |
| 3.12 | ✅ | ✅ |
| 3.13 | ✅ | ✅ |
| 3.14 | ✅ | ✅ |

**Dev — Python × mypy\[mypyc\]** (build/type-check)

| Python | mypy 1.5–1.14 (`≥3.8`) | mypy 1.15–1.17 (`≥3.9`) | mypy 1.19+ (`≥3.9`) |
|--------|------------------------|-------------------------|---------------------|
| 3.10 | ✅ | ✅ | ✅ |
| 3.11 | ✅ | ✅ | ✅ |
| 3.12 | ✅ (1.8+) | ✅ | ✅ |
| 3.13 | ✅ (1.14+) | ✅ | ✅ |
| 3.14 | ❌ | ✅ (1.17+) | ✅ |

## Quick Start

### Installation

```bash
git clone <repository-url>
cd fast_fsm
uv sync          # install all dependencies
```

### Basic Usage

```python
from fast_fsm import State, StateMachine

idle = State("idle")
processing = State("processing")

fsm = StateMachine(idle, name="demo")
fsm.add_state(processing)
fsm.add_transition("start", "idle", "processing")
fsm.add_transition("complete", "processing", "idle")

result = fsm.trigger("start")   # idle → processing
print(f"Success: {result.success}")
```

### Builder Pattern

```python
from fast_fsm import State, FSMBuilder

fsm = (
    FSMBuilder(State("idle"))
    .add_state(State("processing"))
    .add_transition("start", "idle", "processing")
    .add_transition("complete", "processing", "idle")
    # Register per-state callbacks in the same fluent chain:
    .on_enter("processing", lambda from_s, t, **kw: print("→ processing"))
    .on_exit("processing",  lambda to_s,   t, **kw: print("← processing"))
    .build()
)
```

### Factory Helpers

```python
from fast_fsm import simple_fsm

fsm = simple_fsm("idle", "running", "error", initial="idle", name="QuickFSM")
fsm.add_transitions([
    ("start", "idle",    "running"),
    ("fail",  "running", "error"),
    ("reset", "error",   "idle"),
    # Optional 4th element attaches a guard condition:
    # ("start", "idle", "running", FuncCondition("ready", lambda **kw: kw.get("ready"))),
])
```

## Features

### Conditional Transitions

```python
from fast_fsm import FuncCondition, CompiledFuncCondition

enough_energy = FuncCondition("energy", lambda **kw: kw.get("energy", 0) > 5)
fsm.add_transition("proceed", "waiting", "ready", condition=enough_energy)
# CompiledFuncCondition is a mypyc-compiled drop-in for hot paths:
# enough_energy = CompiledFuncCondition(lambda **kw: kw.get("energy", 0) > 5)

fsm.trigger("proceed", energy=10)  # succeeds
fsm.trigger("proceed", energy=3)   # blocked by condition
```

Use `unless=` as a readable negation shorthand — the transition fires when the
condition is **False**:

```python
is_locked = FuncCondition("locked", lambda **kw: kw.get("locked", False))
fsm.add_transition("open", "closed", "open", unless=is_locked)

fsm.trigger("open", locked=False)  # succeeds — not locked
fsm.trigger("open", locked=True)   # blocked — is locked
```

`condition=` and `unless=` are mutually exclusive.

### Multi-Source Transitions

```python
fsm.add_transition("emergency_reset", ["error", "processing", "waiting"], "idle")
```

### Error Handling

By default `trigger()` returns a `TransitionResult` and never raises. Use
`raise_if_failed()` for exception-based flow:

```python
from fast_fsm import TransitionError

# Raises TransitionError when success is False
try:
    fsm.trigger("start").raise_if_failed()
except TransitionError as exc:
    print(exc.result.error)       # human-readable reason
    print(exc.result.from_state)  # state at time of failure

# Chain directly when you also need the destination
target = fsm.trigger("start").raise_if_failed().to_state
```

`TransitionError.result` holds the original `TransitionResult` for inspection.

### Checking Active State

Use `is_in()` to check whether the machine is currently in a given state.
Accepts a state name string or a `State` object:

```python
idle = State("idle")
fsm = StateMachine(idle)
fsm.add_state(State("running"))
fsm.add_transition("start", "idle", "running")

fsm.is_in("idle")    # True
fsm.is_in(idle)      # True — identity comparison
fsm.is_in("running") # False

fsm.trigger("start")
fsm.is_in("running") # True
fsm.is_in("idle")    # False
```

`is_in()` is O(1) and works on both `StateMachine` and `AsyncStateMachine`.

### State Lifecycle Hooks

Attach enter/exit callbacks at construction time using `CallbackState` or
`State.create()`, or add them to any named state after construction with
`fsm.on_enter()` / `fsm.on_exit()`:

```python
from fast_fsm import CallbackState

# Option A — CallbackState (constructed before the machine)
idle = CallbackState(
    "idle",
    on_enter=lambda from_state, trigger, **kw: print("Now idle"),
    on_exit=lambda to_state, trigger, **kw: print("Leaving idle"),
)

# Option B — attach after construction (works on any StateMachine)
fsm.on_enter("running", lambda from_s, t, **kw: print("→ running"))
fsm.on_exit("running",  lambda to_s,   t, **kw: print("← running"))
# Multiple callbacks per state are called in registration order.
```

### State Control

```python
# Force the machine into any state, bypassing guards (testing / error recovery)
fsm.force_state("error")       # full callback chain fires; trigger = "__force__"
fsm.reset()                    # return to initial_state_name

# Snapshot / restore — JSON and pickle safe
snap = fsm.snapshot()          # {"state": "running", "version": 1}
# ... persist snap, restart process, etc. ...
fsm.restore(snap)              # teleports back; full callback chain fires

# Clone — same topology, independent current state, empty listeners
worker = fsm.clone()           # ideal for per-request / per-session instances

# Build from a dict / JSON / YAML config
config = {
    "initial": "idle",
    "transitions": [
        {"trigger": "start",  "from": "idle",    "to": "running"},
        {"trigger": "stop",   "from": "running", "to": "idle"},
        {"trigger": "fail",   "from": ["idle", "running"], "to": "error"},
    ],
}
fsm = StateMachine.from_dict(config, name="MyFSM")
# Add guard conditions at construction time with conditions=:
# from fast_fsm import FuncCondition
# fsm = StateMachine.from_dict(config, conditions={"start": FuncCondition(guard_fn)})
```

### Listeners (Observer Pattern)

Attach observers without touching FSM code. Each listener is a plain object that
implements any subset of the duck-typed protocol:

```python
class TransitionLogger:
    def before_transition(self, source, target, trigger, **kwargs):
        print(f"About to leave {source.name}")

    def on_exit_state(self, source, target, trigger, **kwargs):
        print(f"Leaving {source.name}")

    def on_enter_state(self, target, source, trigger, **kwargs):
        print(f"Entering {target.name}")

    def after_transition(self, source, target, trigger, **kwargs):
        print(f"{source.name} --[{trigger}]--> {target.name}")

fsm.add_listener(TransitionLogger())
```

All four methods are optional — omit any you don't need. Multiple listeners can
be registered; they are called in registration order. Listener exceptions are
caught and logged without crashing the FSM. The empty-list guard
(`if self._on_exit_listeners:`) means **zero overhead** when no listeners are
attached.

**Listener protocol — execution order per successful transition:**

| Method | Fires | Signature |
|---|---|---|
| `before_transition` | First — before any `on_exit` callback | `(source, target, trigger, **kw)` |
| `on_exit_state` | After state's own `on_exit` | `(source, target, trigger, **kw)` |
| `on_enter_state` | After state's own `on_enter` | `(target, source, trigger, **kw)` |
| `after_transition` | Last — after all enter callbacks | `(source, target, trigger, **kw)` |

**Common pattern — transition history:**

```python
class History:
    def __init__(self): self.log = []
    def after_transition(self, source, target, trigger, **kwargs):
        self.log.append((source.name, trigger, target.name))

hist = History()
fsm.add_listener(hist)
# hist.log → [("idle", "start", "running"), ...]
```

**Inline convenience methods** (no listener class required):

```python
# Fires after every successful transition
fsm.after_transition(lambda src, tgt, t, **kw: print(f"{src.name} → {tgt.name}"))

# Fires whenever a trigger attempt fails (wrong state, condition blocked, unknown trigger)
fsm.on_failed(lambda t, from_s, err, **kw: print(f"BLOCKED: {t} from {from_s} — {err}"))

# Fires after every successful "submit" trigger specifically
fsm.on_trigger("submit", lambda src, tgt, t, **kw: metrics.record(t))
```

`on_failed` callbacks are not copied by `clone()`. `on_trigger` callbacks are.

Listeners work identically on `AsyncStateMachine` (same `_execute_transition`
hook, called from `trigger_async`).

### Async Support

```python
import asyncio
from fast_fsm import State, AsyncStateMachine, AsyncCondition

class HighTemp(AsyncCondition):
    def __init__(self, sensor, threshold):
        super().__init__("high_temp", f"Temp >= {threshold}")
        self.sensor = sensor
        self.threshold = threshold

    async def check_async(self, *args, **kwargs) -> bool:
        temp = await self.sensor.read()
        return temp >= self.threshold

monitoring = State("monitoring")
alert = State("alert")

fsm = AsyncStateMachine(monitoring, name="SensorMonitor")
fsm.add_state(alert)
fsm.add_transition("overheat", "monitoring", "alert",
                    condition=HighTemp(my_sensor, threshold=80.0))

async def main():
    result = await fsm.trigger_async("overheat")
    print(f"State: {fsm.current_state.name}")

asyncio.run(main())
```

Register `async` per-state callbacks with `on_enter_async()`/`on_exit_async()` — they fire after all synchronous callbacks, within the same `trigger_async()` call:

```python
async def log_alert(from_s, trigger, **kw):
    await db.record(f"{from_s.name} → alert")

fsm.on_enter_async("alert", log_alert)
```

### Visualization

Generate Mermaid state diagrams and self-contained Markdown documents:

```python
from fast_fsm import to_mermaid, to_mermaid_fenced, to_mermaid_document
from fast_fsm.validation import FSMValidator

# Raw Mermaid diagram string
print(to_mermaid(fsm))

# Fenced block for embedding in .md files
print(to_mermaid_fenced(fsm))

# Full document: diagram + adjacency matrix + transitions table
adj = FSMValidator(fsm).get_adjacency_matrix()
doc = to_mermaid_document(fsm, adjacency_matrix=adj)
print(doc)   # or save to a .md file
```

### Validation (Design-Time)

Comprehensive analysis with zero runtime overhead:

```python
from fast_fsm import validate_fsm, quick_health_check, validate_and_score

# Quick one-liner
print(quick_health_check(fsm))          # "healthy" | "issues" | "critical"

# Full validator
validator = validate_fsm(fsm)
report = validator.validate_completeness()
print(f"Complete: {report['is_complete']}")
print(f"Unreachable states: {report['unreachable_states']}")

# Scored report — structural vs. completeness split
# Intentionally sparse FSMs score against structural health only;
# missing-transition info is reported separately in completeness_score.
from fast_fsm import EnhancedFSMValidator
v = EnhancedFSMValidator(fsm)
score = v.get_validation_score()
print(f"Design style: {score['design_style']}")
print(f"Structural:   {score['structural_score']}/100 (Grade: {score['grade']})")
print(f"Completeness: {score['completeness_score']}/100")

# Export reports
print(v.export_report('markdown'))
print(v.export_report('json'))
```

## Key Capabilities

- **Ultra-High Performance** — 250K+ transitions/sec
- **Memory Efficient** — ~1,000× less than alternatives
- **Type Safe** — full type hints, `ty` and `mypy` clean
- **Clean API** — builder pattern, factory helpers, fluent interface
- **Conditional Transitions** — `FuncCondition`, `CompiledFuncCondition`, `unless=` negation
- **Error Handling** — `raise_if_failed()` / `TransitionError` for exception-based flow
- **State Control** — `force_state()`, `reset()`, `snapshot()`/`restore()`, `clone()`, `from_dict()`
- **Lifecycle Hooks** — `CallbackState`, `fsm.on_enter()`, `fsm.on_exit()`, async `on_enter_async()`/`on_exit_async()`, listeners, `before_transition`/`on_failed`/`on_trigger` inline callbacks
- **Async Support** — `AsyncStateMachine`, `AsyncCondition`, `trigger_async()`, fluent async callbacks via `FSMBuilder`
- **Declarative States** — `@transition` decorator for inline state definitions
- **Optional Validation** — scoring (structural + completeness), tunable thresholds, batch comparison, lint, export
- **Visualization** — Mermaid diagrams, fenced blocks, full Markdown documents with adjacency matrix
- **mypyc Compiled** — `core.py` optionally compiled; `CompiledFuncCondition` for hot condition paths

## Examples

Runnable scripts live in `examples/`. Run any of them with:

```bash
uv run python examples/<script>.py
```

| Script | What it demonstrates |
|--------|---------------------|
| `traffic_light.py` | Timer-based transitions, emergency override |
| `order_processing.py` | Conditional transitions, FSM validation |
| `async_sensor_example.py` | `AsyncStateMachine`, `AsyncCondition` |
| `declarative_state_example.py` | `@transition` decorator, async declarative states |
| `enhanced_builder_example.py` | `FSMBuilder` auto-async detection, fluent API |
| `cross_fsm_demo.py` | Cross-FSM conditions, coordinated multi-FSM systems |

## Running Tests

```bash
uv run pytest tests/ -x -q     # full suite (653 tests)
```

## Architecture

```
src/fast_fsm/
├── core.py               # StateMachine, AsyncStateMachine, State, FSMBuilder, conditions
├── conditions.py          # Condition, FuncCondition, AsyncCondition base classes
├── condition_templates.py # Reusable condition builders
└── validation.py          # FSMValidator, EnhancedFSMValidator, scoring, lint
```

### Design Principles

1. **`__slots__` everywhere** — all core classes, no `__dict__` on hot paths
2. **Direct dictionary lookups** — O(1) `trigger()`, `can_trigger()`, `add_state()`, `add_transition()`
3. **Minimal abstraction** — clean API without unnecessary layers
4. **Optional features** — validation/logging add zero runtime overhead when unused
5. **Selective mypyc compilation** — `core.py` compiled, `conditions.py` stays
   interpreted so users can subclass `Condition` freely

### Performance Characteristics

| Operation | Complexity | Throughput | Memory |
|-----------|-----------|------------|--------|
| `trigger()` | O(1) | ~250K/sec | zero allocation |
| `can_trigger()` | O(1) | ~500K/sec | zero allocation |
| `add_state()` | O(1) | instant | +~32 B/state |
| `add_transition()` | O(1) | instant | +~64 B/transition |
| `FSMBuilder.build()` | O(n) | one-time | optimized result |

## Contributing

See `docs/dev/contributing.md` for the full guide: branching model, quality
gates, coding standards, and mypyc compilation instructions.

```bash
uv sync                    # install deps
uv run pytest tests/ -x -q # run tests
task quality               # lint + type-check
```

## License

Open source — feel free to use, modify, and learn from this implementation.
