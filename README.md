# Fast FSM

A fast, memory-conscious finite state machine library for Python.

Fast FSM keeps the common path small: define states, connect them with named
transitions, and send triggers. When a workflow grows, the same model extends
to guarded priority candidates, lifecycle callbacks, async I/O, persistence,
validation, and visualization.

```python
from fast_fsm import State, StateMachine

machine = StateMachine(State("idle"), name="Worker")
machine.add_state(State("running"))
machine.add_transition("start", "idle", "running")

result = machine.trigger("start")
assert result.success
assert machine.is_in("running")
```

Fast FSM supports Python 3.10 through 3.14. The runtime has one dependency:
`mypy-extensions`.

- [Quick start](docs/QUICK_START.md)
- [Tutorial](docs/TUTORIAL.md)
- [Tiered examples](docs/examples/index.md)
- [API reference](docs/api/core.md)

## Why Fast FSM?

- **Straightforward core API.** Direct construction, factory helpers, a fluent
  builder, and declarative states all produce the same machine model.
- **Deterministic decisions.** Conditions and ordered priority candidates keep
  transition eligibility and precedence inside the FSM.
- **Sync and async support.** Async guards and lifecycle callbacks are awaited
  at their actual transition stage.
- **Operational visibility.** Structured results, bounded history, listeners,
  snapshots, validation, and diagram exporters are built in.
- **Lean runtime.** Direct dictionary lookup and slots-aware hot paths keep the
  dispatch path focused. Validation and visualization remain opt-in.

**Jump to:** [guards](#put-transition-rules-in-guards) ·
[priority](#resolve-competing-outcomes-with-priority) ·
[callbacks](#attach-behavior-to-the-transition-lifecycle) ·
[async](#use-async-machines-for-io-bound-decisions) ·
[persistence](#query-control-and-persist-a-machine) ·
[examples](#follow-the-progressive-examples) ·
[advanced contracts](#advanced-runtime-contracts)

## Install

Add the published package:

```bash
uv add fast_fsm
```

For development from source:

```bash
git clone https://github.com/radioflyer28/fast_fsm.git
cd fast_fsm
uv sync --all-groups
```

## Start with the core API

A machine has one current state. A trigger selects a transition registered for
that state and either returns a successful `TransitionResult` or a structured
failure.

```python
from fast_fsm import State, StateMachine

order = StateMachine(State("pending"), name="Order")
order.add_state(State("paid"))
order.add_state(State("shipped"))

order.add_transition("pay", "pending", "paid")
order.add_transition("ship", "paid", "shipped")

paid = order.trigger("pay")
print(paid.success, paid.from_state, paid.to_state)

rejected = order.trigger("pay")
print(rejected.success, rejected.stage, rejected.error)
```

`trigger()` does not raise for an ordinary rejected transition. Use
`result.raise_if_failed()` when exception-based control flow is a better fit:

```python
order.trigger("ship").raise_if_failed()
```

## Choose the construction style that fits

All construction styles create ordinary `StateMachine` or
`AsyncStateMachine` instances. Start with the simplest style that expresses
the topology clearly.

| Style | Best fit |
|---|---|
| `StateMachine` | Explicit construction and maximum local clarity |
| `simple_fsm()` | A few named states, with transitions added afterward |
| `quick_fsm()` | A compact transition table |
| `FSMBuilder` | Fluent setup, callbacks, or automatic async detection |
| Declarative states | Event handlers that naturally belong to state classes |
| `from_dict()` | Topology loaded from JSON, YAML, TOML, or another config source |

### Factory helpers

```python
from fast_fsm import quick_fsm, simple_fsm

connection = simple_fsm(
    "disconnected",
    "connected",
    initial="disconnected",
    name="Connection",
)
connection.add_transition("connect", "disconnected", "connected")

job = quick_fsm(
    "queued",
    [
        ("start", "queued", "running"),
        ("finish", "running", "done"),
        ("fail", "running", "failed"),
    ],
    name="Job",
)
```

### Fluent builder

```python
from fast_fsm import FSMBuilder, State

worker = (
    FSMBuilder(State("idle"), name="Worker")
    .add_state(State("running"))
    .add_state(State("stopped"))
    .add_transition("start", "idle", "running")
    .add_transition("stop", ["idle", "running"], "stopped")
    .on_enter("running", lambda source, trigger, **_: print("started"))
    .build()
)
```

Passing a list of source states is shorthand for registering the same
transition from each source.

## Put transition rules in guards

A condition receives the same arguments as `trigger()`. Use `FuncCondition`
for ordinary functions or subclass `Condition` when a guard needs reusable
state.

```python
from fast_fsm import FuncCondition

has_credit = FuncCondition(
    lambda *, credit=0, cost=0, **_: credit >= cost,
    name="has_credit",
)

checkout.add_transition(
    "purchase",
    "basket",
    "confirmed",
    condition=has_credit,
)

checkout.trigger("purchase", credit=20, cost=12)
```

Use `unless=` when the negative form reads better:

```python
is_locked = FuncCondition(
    lambda *, locked=False, **_: locked,
    name="is_locked",
)
door.add_transition("open", "closed", "open", unless=is_locked)
```

`condition=` and `unless=` are mutually exclusive. Guard signatures should
accept `*args, **kwargs` or an equivalent flexible keyword shape so callers can
add context without breaking the condition.

### Reusable and time-aware conditions

`fast_fsm.condition_templates` includes key-presence, membership, regex,
comparison, boolean-composition, and negation conditions. The top-level package
also exports:

- `TimeoutCondition(seconds)`: passes until its time window expires.
- `CooldownCondition(seconds)`: passes immediately, then enforces an interval.
- `ElapsedCondition(seconds)`: passes after the interval has elapsed.

Each timing condition uses `time.monotonic()` and provides `reset()`.
See [`condition_toolkit.py`](examples/condition_toolkit.py) for composition
examples.

## Resolve competing outcomes with priority

Several transitions may share one `(source state, trigger)` slot. Fast FSM
evaluates eligible candidates from the lowest priority integer upward and
commits the first match.

```python
from fast_fsm import FuncCondition, State, StateMachine

drone = StateMachine(State("mission"), name="Drone")
drone.add_state(State("return_home"))
drone.add_state(State("emergency_landing"))

drone.add_transition(
    "telemetry_tick",
    "mission",
    "emergency_landing",
    condition=FuncCondition(
        lambda *, critical_fault=False, **_: critical_fault,
        name="critical_fault",
    ),
    priority=0,
)
drone.add_transition(
    "telemetry_tick",
    "mission",
    "return_home",
    condition=FuncCondition(
        lambda *, link_ok=True, **_: not link_ok,
        name="link_lost",
    ),
    priority=10,
)
drone.add_transition(
    "telemetry_tick",
    "mission",
    "return_home",
    condition=FuncCondition(
        lambda *, battery_pct=100, **_: battery_pct < 25,
        name="low_battery",
    ),
    priority=20,
)

result = drone.trigger(
    "telemetry_tick",
    critical_fault=False,
    link_ok=True,
    battery_pct=18,
)
assert result.success
assert result.priority == 20
assert drone.is_in("return_home")
```

Priority belongs to transition topology, not caller-side `if`/`elif` routing.
Application-specific calculations still belong inside guards.

Priorities are unique exact built-in integers within a shared slot. A normal
guard rejection falls through to the next candidate. A guard exception or
async cancellation aborts selection instead of silently trying a lower
priority. Exact duplicate registration is idempotent; a different candidate at
an occupied priority is rejected atomically.

The complete [drone failsafe example](examples/drone_failsafes.py) shows a
controller feeding one telemetry event into priority candidates and issuing
simulated aircraft commands only after the selected transition commits. It is
training software, not flight-control or safety-certified software.

## Attach behavior to the transition lifecycle

Use state callbacks for behavior owned by one state, machine callbacks for
behavior attached during composition, and listeners for cross-cutting
observation.

### State and machine callbacks

```python
from fast_fsm import State

running = State.create(
    "running",
    on_enter=lambda source, trigger, **_: print("state entered"),
    on_exit=lambda target, trigger, **_: print("state exited"),
)

machine.on_enter(
    "running",
    lambda source, trigger, **_: metrics.increment("starts"),
)
machine.on_exit(
    "running",
    lambda target, trigger, **_: metrics.increment("stops"),
)
machine.on_trigger(
    "submit",
    lambda source, target, trigger, **_: metrics.increment("submissions"),
)
machine.after_transition(
    lambda source, target, trigger, **_: audit.record(trigger),
)
machine.on_failed(
    lambda trigger, from_state, error, **_: audit.reject(trigger, error),
)
```

Multiple callbacks in the same collection run in registration order.
`CallbackState` is the explicit class equivalent of `State.create()`.

### Listeners

A listener may implement any subset of this duck-typed protocol:

```python
class TransitionListener:
    def before_transition(self, source, target, trigger, **kwargs):
        pass

    def on_exit_state(self, source, target, trigger, **kwargs):
        pass

    def on_enter_state(self, target, source, trigger, **kwargs):
        pass

    def after_transition(self, source, target, trigger, **kwargs):
        print(f"{source.name} --{trigger}--> {target.name}")


machine.add_listener(TransitionListener())
```

Listeners observe transitions without coupling the state classes to logging,
metrics, or auditing concerns.

## Use async machines for I/O-bound decisions

`AsyncCondition`, async declarative handlers, or async lifecycle callbacks
require `AsyncStateMachine` and `trigger_async()`. `FSMBuilder` automatically
selects an async machine when staged components require one.

```python
import asyncio

from fast_fsm import AsyncCondition, AsyncStateMachine, State


class ServiceReady(AsyncCondition):
    __slots__ = ("client",)

    def __init__(self, client):
        super().__init__("service_ready")
        self.client = client

    async def check_async(self, **kwargs) -> bool:
        return await self.client.is_ready()


machine = AsyncStateMachine(State("waiting"), name="Service")
machine.add_state(State("ready"))
machine.add_transition(
    "poll",
    "waiting",
    "ready",
    condition=ServiceReady(client),
)


async def main():
    result = await machine.trigger_async("poll")
    print(result.success)


asyncio.run(main())
```

Async entry and exit callbacks are awaited at their matching lifecycle slot:

```python
async def announce_ready(source, trigger, **kwargs):
    await event_bus.publish("service.ready")


machine.on_enter_async("ready", announce_ready)
```

Fast FSM does not automatically move synchronous callbacks to a worker thread.
Keep blocking work out of callbacks running on an event-loop thread.
`can_trigger_async()` is also available for advisory eligibility checks; the
actual trigger evaluates its guard again at dispatch time.

## Use declarative states for state-local handlers

The `@transition` decorator associates a handler—and optionally its
condition—with an event handled by a state class.

```python
from fast_fsm import DeclarativeState, StateMachine, transition


class Locked(DeclarativeState):
    @transition("unlock", condition=lambda *, pin="", **_: pin == "1234")
    def unlock(self, **kwargs):
        print("authorized")
        return True


class Unlocked(DeclarativeState):
    @transition("lock")
    def lock(self, **kwargs):
        return True


door = StateMachine(Locked("locked"), name="Door")
door.add_state(Unlocked("unlocked"))
door.add_transition("unlock", "locked", "unlocked")
door.add_transition("lock", "unlocked", "locked")
```

`AsyncDeclarativeState` supports async conditions and handlers with an
`AsyncStateMachine`. Use declarative states when colocating event behavior
improves the domain model; use ordinary states plus callbacks when composition
should own the behavior.

## Query, control, and persist a machine

### State queries and direct control

```python
machine.is_in("running")
machine.can_trigger("stop")

machine.force_state("error")  # bypass guards; runs the lifecycle
machine.reset()               # force the declared initial state
```

`is_in()` accepts a state name or a `State` object and is O(1).
`force_state()`, `reset()`, and `restore()` use the synthetic `"__force__"`
trigger and run the normal callback chain.

### Current-state snapshots

```python
snapshot = machine.snapshot()
# {"state": "running", "version": 1}

serialized = json.dumps(snapshot)
machine.restore(json.loads(serialized))
```

Snapshots capture current runtime state, not topology.

### Topology serialization

```python
config = machine.to_dict()
rebuilt = StateMachine.from_dict(config)  # unguarded topology
```

Callable guards are not serialized. Give guarded rows an opaque
`condition_ref` and provide the live implementation during reconstruction:

```python
config = {
    "name": "Publish",
    "initial": "review",
    "states": ["review", "published"],
    "transitions": [
        {
            "trigger": "publish",
            "from": "review",
            "to": "published",
            "condition_ref": "approved",
        }
    ],
}

machine = StateMachine.from_dict(
    config,
    conditions={"approved": lambda *, approved=False, **_: approved},
)
```

### Clones and transition history

```python
worker = machine.clone()  # same topology/callbacks, reset to initial state

machine.enable_history(max_entries=100)
machine.trigger("start")
for record in machine.history:
    print(record.from_state, record.trigger, record.to_state, record.priority)
machine.disable_history()
```

History records successful commits in a bounded buffer. A pre-commit failure
adds nothing; a later callback failure retains the already committed record.
History is disabled by default.

## Compose multiple machines

Separate FSMs remain easier to test and replace than one machine that absorbs
every subsystem. A guard may read another machine's public state:

```python
from fast_fsm import condition_builder


@condition_builder(name="utilities_ready")
def utilities_ready(**kwargs):
    return power.is_in("on") and cooling.is_in("on")


production.add_transition(
    "prepare",
    "offline",
    "ready",
    condition=utilities_ready,
)
```

Keep deliberate cascades—such as stopping production before cooling—at the
controller or system boundary. See
[`cross_fsm_demo.py`](examples/cross_fsm_demo.py) and the
[FSM linking guide](docs/FSM_LINKING_TECHNIQUES.md).

## Follow the progressive examples

Every script is deterministic, requires no network or hardware, and is covered
by a cross-platform smoke test.

| Tier | Example | Primary lesson |
|---:|---|---|
| 1 | [`traffic_light.py`](examples/traffic_light.py) | Direct construction, triggers, and results |
| 1 | [`order_processing.py`](examples/order_processing.py) | Builder, callbacks, fan-out, and reset |
| 2 | [`condition_toolkit.py`](examples/condition_toolkit.py) | Reusable, composed, and timed guards |
| 2 | [`declarative_state_example.py`](examples/declarative_state_example.py) | Sync and async declarative handlers |
| 2 | [`drone_failsafes.py`](examples/drone_failsafes.py) | FSM-owned priority and command callbacks |
| 3 | [`async_sensor_example.py`](examples/async_sensor_example.py) | Deterministic async guards |
| 3 | [`enhanced_builder_example.py`](examples/enhanced_builder_example.py) | Builder sync and async modes |
| 3 | [`cross_fsm_demo.py`](examples/cross_fsm_demo.py) | Cross-machine composition |
| 4 | [`workflow_persistence.py`](examples/workflow_persistence.py) | History, observation, and serialization |
| 4 | [`diagnostics_and_visualization.py`](examples/diagnostics_and_visualization.py) | Validation and renderers |
| 4 | [`async_service_controller.py`](examples/async_service_controller.py) | Async lifecycle ownership |

Run one from the repository root:

```bash
uv run python examples/drone_failsafes.py
```

The [examples guide](docs/examples/index.md) maps each major feature family to
its best starting point.

## Validate and visualize topology

Validation and visualization are design-time tools. They capture a stable graph
view and do not add graph traversal to transition dispatch.

```python
from fast_fsm import (
    compare_fsms,
    quick_health_check,
    to_json,
    to_mermaid,
    to_mermaid_document,
    to_plantuml,
    validate_and_score,
)

print(quick_health_check(machine))
print(validate_and_score(machine))
print(compare_fsms(machine, rebuilt)["best_fsm"])

print(to_mermaid(machine))
print(to_plantuml(machine))
markdown = to_mermaid_document(machine, include_adjacency=True)
payload = to_json(machine, include_adjacency=True)
```

`to_json()` includes topology plus reachability, cycle, and quality analysis
for programmatic consumers. Mermaid and PlantUML use opaque node IDs so display
labels remain distinct and safely encoded.

For deeper analysis, `FSMValidator` and `EnhancedFSMValidator` provide
completeness checks, paths, cycles, adjacency representations, scoring, lint
output, and Markdown or JSON reports. Sparse structural analysis is the
default; dense matrices are explicit compatibility outputs.

## Advanced runtime contracts

The following details matter when callbacks can fail, machines are shared
between execution contexts, or diagnostic inputs are large.

### Transition results and commit boundaries

`TransitionResult` exposes:

| Field | Meaning |
|---|---|
| `success` | The complete transition lifecycle succeeded |
| `from_state`, `to_state`, `trigger` | Selected transition identity |
| `priority` | Selected candidate priority, when applicable |
| `committed` | Current state/history commit already occurred |
| `stage` | Stable lifecycle stage for a failure |
| `error` | Concise stage-aware reason |
| `cause` | Original exception object, omitted from representations and error text |

A failed pre-commit result preserves the source state. A failed post-commit
result preserves the destination state and history record; Fast FSM does not
roll back an already committed transition.

`raise_if_failed()` raises `TransitionError`. The exception's `result`
attribute is the original object, and an original cause is available through
normal exception chaining.

### Lifecycle order

| Boundary | Ordered work |
|---|---|
| Pre-commit | `before_transition` listeners → source state exit → registered source exit callbacks → exit listeners |
| Commit | Update current state and append the optional history record |
| Post-commit | destination state entry → registered destination entry callbacks → enter listeners → declarative handler → trigger callback → `after_transition` listeners |

Lifecycle callback failures are fail-fast. Remaining callbacks in that
transition suffix do not run. Failure observers still receive the original
failure once each; an observer failure cannot replace it.

Stable stages include `resolution`, `guard`, `state-permission`,
`before-transition`, `source-exit`, `source-exit-callback`,
`exit-state-listener`, `destination-enter`, `destination-enter-callback`,
`enter-state-listener`, `declarative-handler`, `trigger-callback`, and
`after-transition`.

### Ownership, concurrency, and reentry

Each machine serializes its own writes; there is no global scheduler.

- A synchronous `StateMachine` serializes independent threads. Reentering the
  same machine from one of its owned callbacks raises `RuntimeError` before a
  second write begins.
- An `AsyncStateMachine` binds permanently to the first running event loop that
  performs async control work. Independent tasks on that loop wait on a
  per-machine async lock.
- A foreign loop or thread, direct callback reentry, or child task inheriting
  an owned callback's causal root raises `RuntimeError` before lock acquisition.
- Cancellation while waiting does not acquire ownership. Cancellation during
  a transition preserves the lifecycle's observed commit boundary and always
  releases ownership.
- `safe_trigger()` converts ordinary admitted exceptions into result values,
  but ownership and loop misuse still raise `RuntimeError`.

The contract does not promise queue fairness, timeouts, automatic worker
offload, loop transfer, or queued reentry.

### Bounded diagnostics

Every diagnostic operation has finite defaults:

| Limit | Default | Protects |
|---|---:|---|
| `max_work` | 50,000 | Graph visits and analysis work |
| `max_results` | 10,000 | Published rows, paths, and components |
| `max_dense_cells` | 200,000 | Complete dense-matrix allocation |
| `max_path_expansions` | 20,000 | Followed edges during path generation |

```python
from fast_fsm import DiagnosticLimits, to_json

payload = to_json(
    machine,
    limits=DiagnosticLimits(max_work=100_000, max_results=20_000),
)
```

These are operation counters, not time limits. Structured APIs expose a
`DiagnosticStatus`. An output shape that cannot safely carry partial metadata
raises `DiagnosticBudgetExceeded("diagnostic budget exhausted")` instead of
returning hidden partial data.

Comparisons and batches identify inputs by position rather than display name,
so duplicate or empty machine names remain distinct. Cycle results report
complete strongly connected component membership. On cyclic graphs, reported
depth is the SCC condensation DAG depth—not an exact longest simple path
inside a cycle.

### Safe trace logging

Trace logging is metadata-only by default. It records fixed operation, stage,
and result categories plus capped argument counts and sanitized keyword names.
It never places trigger/state names, values, exception payloads, or object
representations into default trace records.

`configure_fsm_logging()` installs one library-owned handler without replacing
application handlers. It returns an `FSMLoggingHandle` whose `restore()` method
removes only that configuration generation. `set_fsm_logging_level()` delegates
to the same ownership-preserving seam.

An optional `FSMTraceRedactor` may translate one ephemeral `FSMTraceEvent`
into the scalar fields `operation`, `stage`, `result`, and `detail`. Invalid
output or an ordinary redactor exception fails closed to fixed
`redaction_failure` metadata. `BaseException` subclasses such as
`KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError` are never
converted.

## Performance and architecture

The durable performance contract is deliberately narrow: fresh installed
compiled singleton `trigger()` throughput must remain at least 200,000
operations per second. Exact timings are environment-specific evidence, not
universal promises.

| Operation | Complexity |
|---|---|
| Current-state and trigger lookup | O(1) |
| Singleton transition dispatch | O(1) direct selection |
| Priority candidate selection | Local O(k), first eligible in stored order |
| `add_state()` | O(1) |
| Singleton transition registration | O(1) |
| Candidate-group insertion | Local O(k) |
| Bounded history append | O(1) |
| Builder work | One-time work over staged declarations |

Candidate groups are stored in priority order and are not sorted during
dispatch. Dispatch never scans unrelated graph topology.

The package is intentionally split around the runtime boundary:

```text
src/fast_fsm/
├── core.py                 # machines, states, builder, lifecycle
├── conditions.py           # subclassable condition interfaces
├── condition_templates.py # reusable guard implementations
├── validation.py           # opt-in design-time analysis
├── visualization.py        # Mermaid, PlantUML, Markdown, JSON
└── _diagnostics.py         # bounded snapshot-backed graph work
```

`core.py` may be compiled with mypyc. Conditions remain interpreted so users
can subclass `Condition` normally; `CompiledFuncCondition` delegates
callable evaluation across that boundary when a hot guard needs it. Hot-path
production classes use `__slots__` where the runtime boundary allows it. The
recursive slots policy, measured exceptions, and packaging modes are documented in the
[architecture guide](docs/dev/architecture.md).

## Compatibility and release evidence

Fast FSM requires Python 3.10 or newer and `mypy-extensions >= 1.0`.
CI exercises Python 3.10 through 3.14 on Linux, macOS, and Windows.

| Python | Runtime support | Current mypy/mypyc toolchain |
|---:|:---:|:---:|
| 3.10 | Yes | Yes |
| 3.11 | Yes | Yes |
| 3.12 | Yes | Yes |
| 3.13 | Yes | Yes |
| 3.14 | Yes | Yes |

The tracked
[`evidence/release-baseline.json`](evidence/release-baseline.json) records
exact test counts, coverage, toolchain versions, source origin, artifact mode,
and environment-labeled benchmark observations. Verify it with:

```bash
task release-baseline-check
```

For v0.4.0 and later, release authorization requires fresh hosted proof for
pure, compiled, and source-derived artifacts. A local run is useful development
evidence but is intentionally non-authorizing. SHA-256 binds exact artifact
bytes to a record; it does not establish publisher identity.

See the [testing guide](docs/dev/testing.md) and
[release guide](docs/dev/releasing.md) for the complete evidence model.

## Development

```bash
uv sync --locked --all-groups
uv run pytest tests/ -x -q
uv run ruff format --check .
uv run ruff check .
task typecheck-mypy
task docs-test
```

Useful documentation:

- [Architecture](docs/dev/architecture.md)
- [Testing and evidence](docs/dev/testing.md)
- [Contributing](docs/dev/contributing.md)
- [Releasing](docs/dev/releasing.md)

Contributions should preserve callback and condition compatibility with
`*args, **kwargs`, the documented ownership and commit boundaries, the
optional nature of diagnostics, and the hot-path complexity contract.

## License

This repository does not currently include a license file. Do not assume
permission to copy, modify, or redistribute the project beyond rights provided
by applicable law.
