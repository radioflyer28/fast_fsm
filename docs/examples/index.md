# Examples

Runnable examples live in the `examples/` directory. Each script demonstrates
a specific Fast FSM feature set. Run any example with:

```bash
uv run python examples/<script>.py
```

## Traffic Light

**File:** `examples/traffic_light.py`

A simple traffic light with 3 states (Red, Yellow, Green), timer-based
transitions, and an emergency override. Good starting point for understanding
custom `State` subclasses and `FSMBuilder`.

```{literalinclude} ../../examples/traffic_light.py
:language: python
:lines: 1-10
:caption: traffic_light.py (excerpt)
```

**Concepts:** Custom states, FSMBuilder, emergency transitions.

---

## Order Processing

**File:** `examples/order_processing.py`

An e-commerce workflow with 5 states (Pending → Processing → Shipped →
Delivered, plus Cancelled). Demonstrates conditional transitions based on
payment/inventory status and FSM validation with `validate_fsm()`.

**Concepts:** Conditional transitions, `on_enter` callbacks, validation.

---

## Async Sensor Monitoring

**File:** `examples/async_sensor_example.py`

Real-time sensor monitoring with `AsyncStateMachine` and `AsyncCondition`.
Simulates temperature and pressure sensors that drive state transitions
asynchronously.

**Concepts:** `AsyncStateMachine`, `AsyncCondition`, `trigger_async()`.

---

## Declarative States

**File:** `examples/declarative_state_example.py`

Define transitions directly on state classes using the `@transition` decorator.
Shows both sync (`DeclarativeState`) and async (`AsyncDeclarativeState`)
variants with integrated logging and condition support.

**Concepts:** `DeclarativeState`, `@transition` decorator, async declarative states.

---

## Enhanced Builder

**File:** `examples/enhanced_builder_example.py`

Deep dive into `FSMBuilder` features: auto-detection of async requirements,
explicit mode selection, fluent API chaining, and mixed sync/async component
handling.

**Concepts:** `FSMBuilder` advanced usage, auto async detection, fluent API.

---

## Cross-FSM Dependencies

**File:** `examples/cross_fsm_demo.py`

Patterns for FSMs that depend on each other's states: a security system
where a door can only open when the alarm is disarmed, a factory production
line gated on material availability, and a coordinated power + cooling +
machine startup sequence.

**Concepts:** Cross-FSM conditions, `condition_builder`, coordinated multi-FSM systems.
