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
- **Production ready** — 101 tests, optional validation, mypyc compilation

| Library | Speed (ops/sec) | Memory | Ratio |
|---------|----------------|--------|-------|
| **fast_fsm** | ~250K | ~0.2 KB | baseline |
| python-statemachine | ~30K | ~25–40 KB | 8× slower, 125× more memory |
| transitions | ~50K | ~30–50 KB | 5× slower, 150× more memory |

*100,000 transitions with realistic usage patterns.*
*Run with* `uv run python benchmarks/benchmark_fast_fsm.py`

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
    .build()
)
```

### Factory Helpers

```python
from fast_fsm import simple_fsm

fsm = simple_fsm("idle", "running", "error", initial="idle", name="QuickFSM")
fsm.add_transitions([
    ("start", "idle", "running"),
    ("fail",  "running", "error"),
    ("reset", "error", "idle"),
])
```

## Features

### Conditional Transitions

```python
from fast_fsm import FuncCondition

enough_energy = FuncCondition("energy", lambda **kw: kw.get("energy", 0) > 5)
fsm.add_transition("proceed", "waiting", "ready", condition=enough_energy)

fsm.trigger("proceed", energy=10)  # succeeds
fsm.trigger("proceed", energy=3)   # blocked by condition
```

### Multi-Source Transitions

```python
fsm.add_transition("emergency_reset", ["error", "processing", "waiting"], "idle")
```

### State Lifecycle Hooks

```python
from fast_fsm import CallbackState

idle = CallbackState("idle")
idle.set_on_enter(lambda from_state, trigger, **kw: print("Now idle"))
idle.set_on_exit(lambda to_state, trigger, **kw: print("Leaving idle"))
```

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

# Scored report
score = validate_and_score(fsm)
print(f"Score: {score['overall_score']}/100 (Grade: {score['grade']})")
```

## Key Capabilities

- **Ultra-High Performance** — 250K+ transitions/sec
- **Memory Efficient** — ~1,000× less than alternatives
- **Type Safe** — full type hints, `ty` and `mypy` clean
- **Clean API** — builder pattern, factory helpers, fluent interface
- **Conditional Transitions** — guard conditions with `*args, **kwargs`
- **Async Support** — `AsyncStateMachine`, `AsyncCondition`, `trigger_async()`
- **Declarative States** — `@transition` decorator for inline state definitions
- **Optional Validation** — scoring, batch comparison, lint, export (JSON/Markdown)
- **mypyc Compiled** — `core.py` optionally compiled for extra speed

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
uv run pytest tests/ -x -q     # full suite (101 tests)
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
