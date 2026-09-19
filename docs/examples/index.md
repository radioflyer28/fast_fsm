# Examples

The runnable examples form a progressive learning path. Each script has one
primary lesson, is deterministic, needs no network or hardware, and can be run
from the repository root:

```bash
uv run python examples/<script>.py
```

## Tier 1 — Core mechanics

Start here even if your eventual machine will be async or highly guarded.

### `traffic_light.py` — direct construction

The smallest useful `StateMachine`: register states and transitions, send a
trigger, inspect `TransitionResult`, and handle an unknown trigger.

### `order_processing.py` — builder and lifecycle

Build a business workflow fluently with `FSMBuilder`, a multi-source
transition, multiple entry callbacks, `reset()`, and `raise_if_failed()`.

## Tier 2 — Put decisions in the machine

These examples move domain rules and event handling into Fast FSM.

### `condition_toolkit.py` — focused conditions and entry timing

Compose named `FuncCondition` rules with `&`, `|`, and `~`, route two distinct
priority outcomes, then use a fake clock to demonstrate `after=` and
`within=`. It is deterministic and never sleeps.

### `custom_conditions.py` — small domain rules

Implement four reusable `Condition` subclasses with explicit input behavior:
battery level, heartbeat age with an injected clock, payload matching, and
inventory availability. Each rule is used by a real machine transition.

### `declarative_state_example.py` — state-local handlers

Use `DeclarativeState`, `AsyncDeclarativeState`, and `@transition` when event
handlers belong next to state definitions. It shows one synchronous and one
asynchronous machine without unrelated logging setup.

### `drone_failsafes.py` — controller-owned telemetry

This is the progressive integration example for the flat-FSM semantics taught
by the Tutorial. It is a deterministic training simulation of pre-arm checks
and in-flight failsafes, not an aircraft integration.

`DroneController` owns both its `FSMBuilder`-built machine and a replaceable
aircraft-command adapter. Every normalized sample becomes exactly one
`telemetry_tick`; all state-dependent guard logic and fixed precedence remain
in the machine rather than in controller-side `if`/`elif` routing:

- priorities choose critical fault, link loss, low battery, home arrival, and
  touchdown deterministically;
- a Mission update is an internal self-transition, while an explicit Mission
  re-entry runs the external lifecycle;
- normal and emergency landing are explicit final states, not merely nodes
  with no displayed outgoing edge;
- an ordinary false navigation guard falls through, while a bounded
  `TransitionRejected("navigation-conflict")` is a terminal, command-free
  domain result; and
- entry callbacks issue adapter commands only after the selected transition
  commits.

`TelemetryPolicy` only retains measured facts, including heartbeat age. It
does not choose states or events. The source below is displayed with
`literalinclude`; its independent execution proof is
`tests/test_drone_failsafes_example.py` and the runnable script:

```bash
uv run python examples/drone_failsafes.py
```

This example is educational software. It neither controls hardware nor
provides certified, real-time, or flight-control guidance.

## Tier 3 — Compose larger systems

### `async_sensor_example.py` — asynchronous guards

Read deterministic simulated sensors through `AsyncCondition`, evaluate
competing candidates in priority order, and dispatch with `trigger_async()`.

### `enhanced_builder_example.py` — sync/async build modes

Compare an ordinary synchronous build, automatic upgrade caused by an async
guard, and the deliberate rejection of an async component in forced-sync mode.

### `cross_fsm_demo.py` — coordinated machines

Keep power, cooling, and production as independent FSMs. Cross-machine guards
read sibling state, while deliberate cascading behavior remains explicit at
the owning system boundary.

## Tier 4 — Operate and inspect

### `workflow_persistence.py` — runtime state and topology

Use listeners, success and failure callbacks, bounded history, snapshots,
restore, structural clones, JSON topology export, and `from_dict()` condition
references.

### `diagnostics_and_visualization.py` — design-time tooling

Compare a flawed and corrected graph with health checks, scoring, comparison,
and lint output. Render Mermaid, PlantUML, Markdown, and structured JSON, then
show how `DiagnosticLimits` fails closed when a diagnostic budget is exhausted.

### `async_service_controller.py` — async lifecycle ownership

Register async entry and exit callbacks, query `can_trigger_async()`, and show
that concurrent callers serialize while a lifecycle callback is awaiting.
It also demonstrates ordinary task cancellation without corrupting state.

## Feature-family map

Use this as a routing guide, not as a claim that every public method needs its
own example.

| Feature family | Primary example | Supporting example |
|---|---|---|
| States, transitions, triggers, results | `traffic_light.py` | `order_processing.py` |
| Builder, callbacks, reset, bulk sources | `order_processing.py` | `enhanced_builder_example.py` |
| Reusable, composed, and custom conditions | `condition_toolkit.py` | `custom_conditions.py` |
| Entry-relative transition timing | `condition_toolkit.py` | `workflow_persistence.py` |
| Ordered priority candidates | `drone_failsafes.py` | `async_sensor_example.py` |
| Final states and termination | `drone_failsafes.py` | `workflow_persistence.py` |
| Internal versus external self transitions | `drone_failsafes.py` | `async_service_controller.py` |
| Expected rejection versus guard ineligibility | `drone_failsafes.py` | `condition_toolkit.py` |
| Declarative handlers | `declarative_state_example.py` | — |
| Async guards and dispatch | `async_sensor_example.py` | `enhanced_builder_example.py` |
| Cross-FSM composition | `cross_fsm_demo.py` | — |
| History, listeners, snapshot, clone, serialization | `workflow_persistence.py` | — |
| Validation and bounded diagnostics | `diagnostics_and_visualization.py` | — |
| Mermaid, PlantUML, Markdown, JSON | `diagnostics_and_visualization.py` | — |
| Async lifecycle and ownership | `async_service_controller.py` | — |

## Complete drone example

```{literalinclude} ../../examples/drone_failsafes.py
:language: python
:caption: Controller-owned, single-event deterministic telemetry training simulation
```
