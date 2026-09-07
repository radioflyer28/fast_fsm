# Fast FSM — High-Performance Finite State Machine Library

A high-performance, memory-efficient finite state machine library for Python
with a clean, intuitive API.

**Full documentation:** after installing, run
`uv run sphinx-build -b html docs docs/_build/html` and open
`docs/_build/html/index.html`, or browse the Markdown sources under `docs/`.

## Performance Highlights

- **Stable performance contract** — fresh installed compiled singleton
  `trigger()` throughput is at least 200,000 operations per second.
- **Memory-conscious design** — direct dictionary lookups and `__slots__` keep
  the hot path lean.
- **Production-ready verification** — 700+ tests, optional validation, and
  optional mypyc compilation.

Exact test, coverage, toolchain, source-origin, artifact-mode, and collected
environment-labeled benchmark observations are recorded in the tracked
[`evidence/release-baseline.json`](evidence/release-baseline.json) manifest.
Regenerate or verify that evidence with the commands in the developer testing
guide; do not treat a historical local benchmark as a universal result.

## v0.3.0 Installed-Artifact Release Proof

v0.3.0 requires a complete installed-artifact proof matrix: pure, compiled, and
source-derived artifacts must be verified from fresh environments before a
release can be authorized. The local matrix is an explicitly non-authorizing
projection for development; only the complete hosted release matrix can
authorize publication. SHA-256 binds exact bytes to the recorded evidence, not
publisher authenticity. Exact artifact records, environment labels, and any
performance observations remain in the manifest rather than this narrative.

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

### Timing Conditions

Built-in time-based guards remove the need for manual clock logic:

```python
from fast_fsm import StateMachine, State, TimeoutCondition, CooldownCondition, ElapsedCondition

fsm = StateMachine(State("idle"), name="timed")
fsm.add_state(State("active"))
fsm.add_state(State("cooldown"))

# TimeoutCondition — allow a transition only within the first N seconds
timeout = TimeoutCondition(30.0)          # 30-second window
fsm.add_transition("activate", "idle", "active", condition=timeout)

# CooldownCondition — enforce a minimum interval between triggers  
cooldown = CooldownCondition(5.0)         # at least 5 s between fires
fsm.add_transition("retry", "active", "active", condition=cooldown)

# ElapsedCondition — gate a transition until N seconds have passed
warmup = ElapsedCondition(10.0)           # wait 10 s before allowing
fsm.add_transition("ready", "active", "cooldown", condition=warmup)

# All timing conditions use time.monotonic() (immune to NTP jumps)
# and provide a reset() method to restart their internal clock:
timeout.reset()
```

### Multi-Source Transitions

```python
fsm.add_transition("emergency_reset", ["error", "processing", "waiting"], "idle")
```

### Error Handling

By default `trigger()` returns a `TransitionResult`, including ordinary
transition failures. Inspect its structured lifecycle fields before deciding
whether to use exception-based flow:

```python
from fast_fsm import TransitionError

# `committed` tells you whether the destination/history commit happened.
result = fsm.trigger("start")
if not result.success:
    assert result.stage is not None       # stable lowercase lifecycle stage
    assert result.cause is None or isinstance(result.cause, BaseException)
    if result.committed:
        # A later callback failed; the destination remains current.
        assert fsm.current_state.name == result.to_state

# Raises TransitionError only when success is False. Its original cause is
# available through exception chaining; avoid formatting callback payloads or
# causes into application logs.
try:
    result.raise_if_failed()
except TransitionError as exc:
    assert exc.result is result
    print(exc.result.error)       # concise, stage-aware reason
    print(exc.result.from_state)  # state at time of failure

# Chain directly when you also need the destination
target = result.raise_if_failed().to_state
```

`TransitionError.result` holds the original `TransitionResult` for inspection.
Successful results have `success=True`, `committed=True`, `stage=None`, and
`cause=None`. Failed pre-commit results preserve the source state with
`committed=False`; failed post-commit results preserve the destination with
`committed=True`. `cause` retains the original exception object when one
exists, but is deliberately omitted from result representations and error text.

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

# Clone — verbatim copy reset to initial state; callbacks and topology are preserved
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

All four methods are optional — omit any you don't need. Multiple callbacks in
every collection preserve registration order. An ordinary lifecycle callback
failure is fail-fast: it stops the remaining lifecycle suffix, produces a
failed `TransitionResult`, and never rolls back a completed commit. The
empty-list guards keep the no-listener path lean.

**Ordinary trigger lifecycle order:**

| Stage | Ordered work |
|---|---|
| Pre-commit | `before_transition` listeners → source `State.on_exit` → registered source `on_exit` callbacks → `on_exit_state` listeners |
| Commit | Update the current state and append one optional history record together; no user callback or async await occurs here. |
| Post-commit | destination `State.on_enter` → registered destination `on_enter` callbacks → `on_enter_state` listeners → selected declarative handler → trigger-specific callbacks → `after_transition` listeners |

The stable result stages identify the failing slot, including
`before-transition`, `source-exit`, `source-exit-callback`,
`exit-state-listener`, `destination-enter`, `destination-enter-callback`,
`enter-state-listener`, `declarative-handler`, `trigger-callback`, and
`after-transition` (with `resolution`, `guard`, and `state-permission` for
pre-lifecycle failures).

`on_failed(trigger, from_state, error, **kwargs)` keeps its existing
signature. Each failed trigger invokes registered failure observers exactly
once in registration order. An observer failure cannot replace the original
result/cause or prevent the remaining observers from receiving their one call.

**Common pattern — application-side transition history:**

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

# Fires once whenever a trigger attempt fails (wrong state, condition blocked,
# lifecycle callback, or cancellation observation)
fsm.on_failed(lambda t, from_s, err, **kw: print(f"BLOCKED: {t} from {from_s} — {err}"))

# Fires after every successful "submit" trigger specifically
fsm.on_trigger("submit", lambda src, tgt, t, **kw: metrics.record(t))
```

`clone()` copies all callbacks and listeners (shallow copy). Adding new callbacks
to the clone after cloning does not affect the original.

Listeners work identically on `AsyncStateMachine` through the paired async
lifecycle runner. Synchronous callbacks still run inline; Fast FSM never
automatically offloads them to a worker.

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

Register `async` per-state callbacks with `on_enter_async()`/`on_exit_async()`.
They are awaited at the matching source-exit or destination-enter slot,
immediately after that slot's synchronous callbacks—not as an async tail after
the whole transition:

```python
async def log_alert(from_s, trigger, **kw):
    await db.record(f"{from_s.name} → alert")

fsm.on_enter_async("alert", log_alert)
```

If an awaited lifecycle operation is cancelled, `trigger_async()` invokes the
registered failure observers once for the reached stage and re-raises the same
`asyncio.CancelledError`. It does not shield work, roll back a completed
transition, or invoke later lifecycle callbacks. Cancellation before commit
leaves the source/history untouched; cancellation after commit leaves the
destination and its one history record intact.

### Ownership, Concurrency, and Reentry

Fast FSM serializes **each machine independently**. This is an ownership
contract for public writes, not a global scheduler:

- `trigger()`, `safe_trigger()`, `force_state()`, `reset()`, `restore()`, graph
  mutators, history enable/disable, and listener/callback/failure-observer
  registration all share the same per-machine ownership policy. Reads remain
  available, but do not promise a cross-field topology or diagnostic snapshot.
- On `StateMachine`, independent threads serialize one complete write at a
  time. A same-thread call made from an owned callback (or another owned write)
  raises a redacted `RuntimeError` before validation, preparation, a guard,
  callback, or mutation runs. Ownership is released after every result,
  ordinary exception, and `BaseException` without altering the existing
  state/history commit boundary.
- On `AsyncStateMachine`, the first async control operation permanently binds
  the machine to its running event loop. Independent tasks on that loop wait
  with an asyncio-native per-machine lock, so the event loop remains
  responsive. A foreign loop/thread, a direct reentry, or a child task created
  by an owned callback raises `RuntimeError` before lock acquisition; child
  tasks inherit the causal ownership root rather than waiting behind their
  parent. Cancellation while waiting propagates unchanged and never installs
  ownership; cancellation while owning follows the lifecycle's `finally`
  cleanup and Phase 17 state/history rules.
- `safe_trigger()` performs ownership, loop, causal-root, foreign-thread, and
  busy preconditions **before** its ordinary exception-conversion catch, so
  misuse raises `RuntimeError`. Ordinary post-admission `Exception` failures
  still return the usual value result. Ownership messages use stable operation
  categories only; they never contain trigger arguments, callback payloads,
  causes, or arbitrary exception text.
- Synchronous callbacks on an async machine run inline on its event-loop
  thread. Registered async callbacks are awaited at their matching lifecycle
  slots. Fast FSM does not infer blocking work or automatically offload a
  callback to a worker.

This contract intentionally makes **no** fairness, timeout, queue-order,
loop-transfer, automatic-offload, cross-field-snapshot, or installed-artifact
promise. Queueing reentry, loop transfer, and worker offload are future design
work; stable diagnostic snapshots are Phase 19, and installed-wheel/sdist
parity is Phase 20.

### Visualization

Generate Mermaid state diagrams, PlantUML diagrams, and self-contained Markdown documents:

```python
from fast_fsm import to_mermaid, to_mermaid_fenced, to_mermaid_document, to_plantuml

# Raw Mermaid diagram string
print(to_mermaid(fsm))

# Fenced block for embedding in .md files
print(to_mermaid_fenced(fsm))

# Full document: diagram + adjacency matrix + transitions table
from fast_fsm.validation import FSMValidator
adj = FSMValidator(fsm).get_adjacency_matrix()
doc = to_mermaid_document(fsm, adjacency_matrix=adj)
print(doc)   # or save to a .md file

# PlantUML output
print(to_plantuml(fsm))
```

### Bounded Diagnostics and Safe Output

Diagnostics are opt-in design-time work. They preserve O(1) source/trigger
lookup, direct singleton dispatch, and `add_state()` work, while immutable
candidate-group insertion and ordered selection remain local O(k). Importing
or using diagnostic APIs adds no runtime dependency and never puts graph
traversal on either dispatch path. Each top-level validator, comparison, JSON export, or renderer
captures one immutable private graph view and shares one budget through its
nested analysis. Structural reachability always begins at the machine's
declared initial state. The captured current state is reported separately; it
does not change the answer.

Use a keyword-only `DiagnosticLimits` override when the default ceilings are
too small for a known diagnostic job:

| Limit | Default | Counted before the operation |
|---|---:|---|
| `max_work` | 50,000 | graph visits, edge examinations, and other analysis work |
| `max_results` | 10,000 | published diagnostic rows, components, paths, and similar results |
| `max_dense_cells` | 200,000 | a requested dense matrix's complete cell allocation |
| `max_path_expansions` | 20,000 | followed edges during generated-path exploration |

These are finite operation counters, not elapsed-time limits. `DiagnosticStatus`
is the structured completion record: `complete`, `exhausted_dimension`,
`exhausted_stage`, `work_count`, `result_count`, `dense_cell_count`, and
`path_expansion_count`. Structured validation, comparison, batch, report, and
JSON output expose it. A legacy set, list, scalar, printed report, diagram, or
dense-matrix shape cannot safely carry partial metadata, so it raises
`DiagnosticBudgetExceeded` with the fixed message `diagnostic budget exhausted`
instead of returning hidden partial output.

`compare_fsms(*fsms, limits=None)` and
`batch_validate(*fsms, show_summary=True, limits=None)` preserve every input
by zero-based `position`, even when labels are empty or duplicated. Comparison
entries are `{position, name, score, metrics, issue_count, diagnostic_status}`;
rankings are `{position, name, score}` records sorted by descending score then
ascending position, and `best_fsm` is `{position, name}`. Batch entries are
`{position, name, validator, diagnostic_status}`. Names are display labels,
never dictionary keys. Comparing zero machines returns empty `entries` and
`rankings`, `best_fsm=None`, `count=0`, `total_issues=0`, and
`avg_score=score_range=None`—the zero-machine numeric aggregates are `None`,
not invented zeroes.

Cycle membership is complete strongly connected component (SCC) membership:
self-loops and every member of longer cycles appear once in deterministic
snapshot order. A DAG reports `dag_longest_path`; a cyclic graph reports the
longest depth of its SCC condensation DAG as `condensation_dag_depth`. This is
not an exact longest-simple-path claim inside a cycle. Sparse state/event/edge
rows are the default `O(V + E)` representation. Dense `V × events` transition
and `V²` adjacency matrices are explicit compatibility outputs that preflight
their full counted allocation before construction. Generated paths use
iterative traversal and are bounded independently by requested length/path
caps and the shared expansion, work, and result budgets.

Diagram identity and text are separate. Mermaid and PlantUML use opaque,
snapshot-position node IDs (`s0`, `s1`, ...) rather than labels, so labels that
sanitize alike remain collision-free. Mermaid text, PlantUML text, and Markdown
headings/table cells each use their own grammar-specific, one-line encoding
boundary for titles, state labels, triggers, and condition names. JSON and
documents preserve snapshot order; dense JSON/document output is opt-in. A
caller-supplied adjacency matrix must exactly match the captured states,
events, transitions, and every cell or fails with
`ValueError("adjacency matrix does not match captured snapshot")`.

### Safe Trace Logging

Trace output is metadata-only by default. At `logging.DEBUG - 5` it records
fixed operation/stage/result categories, `trace_arg_count`, and capped,
sanitized `trace_keyword_names`; it never puts trigger/state names, argument
or keyword values, exception payloads, object representations, or raw values
in a `LogRecord`, its arguments, `extra`, or formatted output. The disabled
trace guard runs before event allocation, value traversal, handler lookup, or
redactor work.

An explicit `FSMTraceRedactor` receives one ephemeral frozen `FSMTraceEvent`
with exactly `operation`, `stage`, `result`, `trigger`, `source_state`,
`destination_state`, `positional_args`, `keyword_args`, and `error`. It may
return only the scalar keys `operation`, `stage`, `result`, and `detail`; text
is capped at 200 characters. An ordinary `Exception` raised by a redactor,
`None`/non-mapping result, forbidden key, non-scalar value, or oversized
string fails closed by emitting only the fixed `redaction_failure`
metadata—never a raw fallback. Non-`Exception` `BaseException` subclasses
(including `KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError`) are
not converted: they emit no trace record and are re-raised. This is a
fail-closed boundary, not best-effort formatting.

`configure_fsm_logging(level=logging.WARNING, logger_name="fast_fsm",
format_string="%(message)s", *, propagate=None, redactor=None)` returns an
`FSMLoggingHandle`. It preserves application-owned handlers, filters,
formatters, ordering, and open state; repeated library configuration replaces
only its marked library handler. `propagate=None` preserves the application's
existing setting, while a Boolean is a deliberate library choice.
`FSMLoggingHandle.restore()` is idempotent and generation-scoped: it removes
only its own library handler and restores a previous level/propagation value
only when a newer configuration or application change has not superseded it.
`set_fsm_logging_level(verbosity, logger_name="fast_fsm", *, propagate=None,
redactor=None)` validates its verbosity name and delegates to the same
ownership-preserving configuration seam. No logging backend is introduced.

### Serialization & Introspection

Round-trip topology snapshots and machine-readable JSON export for agents:

```python
# Serialize topology to a plain dict (JSON-safe)
d = fsm.to_dict()
rebuilt = StateMachine.from_dict(d)   # lossless roundtrip (guards excluded)

# Machine-readable JSON for coding agents
from fast_fsm import to_json
data = to_json(fsm)
data["topology"]["states"]              # sorted state names
data["analysis"]["reachability"]        # reachable / unreachable / terminal
data["analysis"]["cycles"]             # has_cycles, states_in_cycles
data["analysis"]["quality"]            # overall_score, grade, issues
```

### Transition History

Opt-in bounded recording of committed transitions — zero cost when disabled.
The machine appends each record at the internal commit point, so a pre-commit
failure or cancellation records nothing while a later failure retains the
already committed record:

```python
fsm.enable_history(max_entries=1000)
fsm.trigger("start")
fsm.trigger("stop")
for rec in fsm.history:
    print(f"{rec.from_state} --{rec.trigger}--> {rec.to_state} @ {rec.timestamp}")
fsm.disable_history()   # clears buffer and stops recording
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

- **Ultra-High Performance** — fresh installed compiled singleton `trigger()`
  contract ≥200,000 ops/sec; other timings are environment-labeled observations
- **Memory Efficient** — direct dictionary lookups and slots-aware hot paths
- **Type Safe** — full type hints, `ty` and `mypy` clean
- **Clean API** — builder pattern, factory helpers, fluent interface
- **Conditional Transitions** — `FuncCondition`, `CompiledFuncCondition`, `unless=` negation
- **Error Handling** — `raise_if_failed()` / `TransitionError` for exception-based flow
- **State Control** — `force_state()`, `reset()`, `snapshot()`/`restore()`, `clone()`, `from_dict()`, `to_dict()`
- **Lifecycle Hooks** — `CallbackState`, `fsm.on_enter()`, `fsm.on_exit()`, async `on_enter_async()`/`on_exit_async()`, listeners, `before_transition`/`on_failed`/`on_trigger` inline callbacks
- **Async Support** — `AsyncStateMachine`, `AsyncCondition`, `trigger_async()`, fluent async callbacks via `FSMBuilder`
- **Declarative States** — `@transition` decorator for inline state definitions
- **Transition History** — opt-in `enable_history()` / `disable_history()` with a bounded `TransitionRecord` buffer and environment-labeled performance evidence
- **Optional Validation** — scoring (structural + completeness), tunable thresholds, batch comparison, lint, export
- **Visualization** — Mermaid diagrams, PlantUML output, fenced blocks, full Markdown documents with adjacency matrix
- **Agent Tooling** — `to_json()` exports topology + reachability + cycles + quality for programmatic consumption
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
| [`drone_failsafes.py`](examples/drone_failsafes.py) | One telemetry tick through FSM-owned failsafe priority; deterministic training simulation only, not flight-control software |

The drone example is educational and deterministic: it neither controls real
hardware nor provides certified or real-time flight-control guidance.

## Running Tests

```bash
uv run pytest tests/ -x -q     # full suite (700+ tests)
```

For the authoritative, exact release evidence, use
[`evidence/release-baseline.json`](evidence/release-baseline.json) with the
write/check workflow in [`docs/dev/testing.md`](docs/dev/testing.md).

## Architecture

```
src/fast_fsm/
├── core.py               # StateMachine, AsyncStateMachine, State, FSMBuilder, conditions
├── conditions.py          # Condition, FuncCondition, AsyncCondition base classes
├── condition_templates.py # Reusable condition builders
└── validation.py          # FSMValidator, EnhancedFSMValidator, scoring, lint
```

### Design Principles

1. **`__slots__` on hot paths** — all relevant production classes are audited
   recursively; the measured exceptions are documented in the contributor guide
2. **Direct lookup, local groups** — current-source and trigger lookup plus
   direct singleton dispatch are O(1); immutable group insertion and
   first-eligible ordered selection are local O(k), never scan unrelated graph
   topology, and do not sort during dispatch
3. **Minimal abstraction** — clean API without unnecessary layers
4. **Optional features** — validation/logging add zero runtime overhead when unused
5. **Selective mypyc compilation** — `core.py` compiled, `conditions.py` stays
   interpreted so users can subclass `Condition` freely

### Performance Characteristics

| Operation | Complexity | Throughput | Memory |
|-----------|-----------|------------|--------|
| `trigger()` / `can_trigger()` with a singleton | O(1) lookup and direct dispatch | fresh installed compiled singleton ≥200,000 ops/sec | implementation-dependent |
| `trigger()` / `can_trigger()` with a candidate group | local O(k) first-eligible ordered selection | environment-labeled observation | implementation-dependent |
| `trigger()` + history | dispatch path above plus O(1) bounded append | environment-labeled observation | implementation-dependent |
| `add_state()` | O(1) | implementation-dependent | implementation-dependent |
| `add_transition()` singleton | O(1) | implementation-dependent | implementation-dependent |
| `add_transition()` into an immutable candidate group | local O(k) insertion | environment-labeled observation | implementation-dependent |
| `FSMBuilder.build()` | one-time builder work over staged declarations | environment-labeled observation | implementation-dependent |

Stored candidate groups are already priority ordered, so their dispatch path does
not sort them. Neither path scans unrelated graph topology. Exact benchmark
timings are environment-specific observations; the durable throughput floor
applies only to fresh installed compiled singleton dispatch. See the [release
evidence manifest](evidence/release-baseline.json) for reviewed observations.

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
