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
├── _diagnostics.py         # Interpreted scalar graph projection and bounded ledger
├── conditions.py           # Condition, FuncCondition, AsyncCondition
├── condition_templates.py  # Reusable condition builder functions
├── validation.py           # FSMValidator, EnhancedFSMValidator, scoring, linting
└── visualization.py        # Snapshot-backed Mermaid, PlantUML, JSON, and Markdown
```

**Import DAG (strict — no cycles):**

```text
conditions  →  core  →  validation
                     ↘
_diagnostics  ←  validation, visualization
```

`validation` and `visualization` may import from `core` and the interpreted
`_diagnostics` seam. `core` MUST NOT import from `validation`, `visualization`,
or `_diagnostics`; this keeps the runtime core as one mypyc compilation unit.

## Key Classes

### State Hierarchy

```text
State (__slots__)
├── CallbackState          # has _on_enter / _on_exit slots
├── DeclarativeState       # @transition decorator support
│   └── AsyncDeclarativeState
└── (user subclasses)
```

- **`State`** — directly instantiable state with `name`, `on_enter()`, and
  `on_exit()`. Uses `__slots__` — you cannot add arbitrary attributes.
- **`CallbackState`** — when you need callbacks stored *on the state object*,
  use this class instead of fighting `__slots__`.
- **`DeclarativeState`** / **`AsyncDeclarativeState`** — define transitions
  via the `@transition` decorator on methods.

### StateMachine & AsyncStateMachine

```text
StateMachine (__slots__)
└── AsyncStateMachine      # adds trigger_async(), awaits AsyncCondition.check()
```

Core data structures use O(1) registry lookup; candidate-group work is local to
one already selected `(source, trigger)` slot:

| Attribute | Type | Purpose |
|-----------|------|---------|
| `_states` | `dict[str, State]` | Name → State |
| `_transitions` | `dict[str, dict[str, TransitionEntry \| _TransitionGroup]]` | `from_state → {trigger → direct singleton or immutable candidate group}` |
| `_initial_state` | `State` | Declared construction identity |
| `_current_state` | `State` | Active state reference |
| `_graph_version` | `int` | Monotonic successful-topology version |

`trigger()` and `can_trigger()` look up the current-state name, then the
trigger, through dictionaries. A direct `TransitionEntry` singleton dispatches
in O(1); an immutable `_TransitionGroup` scans its local ordered candidates in
O(k) until the first eligible entry. Groups are stored already ordered, so
dispatch does not sort them, and neither path scans unrelated graph topology.
`_TransitionGroup` is a private storage detail, not public inspection API.
`add_state()` remains O(1); builder work is a separate one-time pass over its
staged declarations.

Candidate precedence is part of topology, not caller-side event routing.
`add_transition(..., priority=...)` accepts only an exact built-in non-Boolean
integer. Lower values precede higher values, and distinct candidates cannot
share a priority within one `(source, trigger)` slot. Exact normalized
duplicates are idempotent. Registration constructs a replacement singleton or
immutable group off-table and publishes it atomically, so validation failure
cannot expose a partial group.

The sync and async selectors apply the same pipeline to each candidate: its
transition guard, any matching declarative guard, and destination-state
permission. Ordinary ineligibility continues within the local group; an
exception or cancellation terminates the attempt. Selection itself invokes no
state callbacks, command adapters, observers, or history writes. Only the
selected candidate enters the normal pre-commit/commit/post-commit lifecycle,
and its priority then flows to the result, history, and trace metadata.

### Canonical Topology and Private Graph Projection

`_states` is the authoritative canonical registry. State names use ordinary
Python string equality: registering the same object again is an idempotent
no-op, but a different object with the same name is rejected with
`ValueError`. Every ordinary transition endpoint is resolved through that
registry before topology is changed; a foreign `State` with the right name is
not interchangeable with the canonical object.

`add_transition()`, batch addition, bidirectional addition, and emergency
addition first materialise and validate their complete request. Invalid,
duplicate, or foreign endpoints therefore leave the registry, transitions,
current state, and graph version unchanged. Successful compound operations
make one atomic topology commit. Convenience constructors may register their
declared state set while constructing a machine, but ordinary transition
addition never creates an endpoint implicitly.

The machine retains its declared `_initial_state` separately from the mutable
current state. `_graph_version` starts at the constructor baseline and is
monotonic only across successful topology changes; movement of the current
state and idempotent registrations/replacements do not advance it. The
private `_graph_snapshot()` tool seam returns a fresh, tuple-backed
`_GraphSnapshot` containing that version, name, declared initial state, and
deterministically name/trigger-sorted canonical state and transition rows.
It deliberately retains canonical `State`/`Condition` identities while making
its own structure immutable.

This graph snapshot is an internal, single-owner tool contract rather than a
public serialization format or concurrency promise. It does not change the
public `snapshot()` or `to_dict()` roles. Phase 18 owns concurrent topology
ownership, Phase 19 owns snapshot consumers and diagnostic budgets, and
FUTR-05 owns any public topology format.

### Bounded Diagnostic Data Flow (Phase 19)

Phase 19 keeps analysis outside the runtime lookup path. One public diagnostic
entry point—validation, comparison, batch validation, JSON, Mermaid,
PlantUML, fenced Mermaid, or a Markdown document—takes exactly one
ownership-synchronized `_graph_snapshot()` and passes it through private
from-snapshot helpers:

```text
top-level diagnostic call
        │
        ▼
core.py: _graph_snapshot() ── scalar labels copied under the owner boundary
        │                     (core does not import diagnostic code)
        ▼
_diagnostics.py: _DiagnosticGraph + one _DiagnosticBudget
        │
        ├── validation.py: reachability, SCCs, depth, comparison, batch, reports
        └── visualization.py: JSON, Mermaid, PlantUML, fenced/document output
```

The one shared `DiagnosticLimits` ledger reserves each counted operation before
work, result publication, dense-cell allocation, or path expansion. Its
scalar `DiagnosticStatus` makes structured completion explicit; legacy shapes
raise the fixed redacted `DiagnosticBudgetExceeded` rather than return an
unlabelled partial value. Declared `initial_state` is the structural root;
captured `current_state` is metadata only.

The graph algorithms are intentionally interpreted and opt-in. Sparse rows
are `O(V + E)`; dense `V × events` and `V²` compatibility outputs preflight
their complete allocation; paths use iterative frames and independent
expansion/result caps. Iterative SCC membership is the cycle oracle. Depth is
dynamic programming over a DAG or the SCC condensation DAG, never an
enumeration of cyclic simple paths. JSON, diagrams, fences, and documents use
the same snapshot and budget rather than calling public helpers that recapture.

`core.py` supplies only capture plus guarded trace/logging seams. It performs
no diagnostic traversal or dense allocation, so source/trigger lookup and
singleton dispatch remain O(1), while immutable grouped insertion and ordered
selection stay local O(k). At the trace level, the core first checks
`logger.isEnabledFor(logging.DEBUG - 5)` before
constructing an event, traversing keys/values, looking up a handler, or calling
a redactor. The ordinary default record is metadata-only; raw data exists only
in the ephemeral explicit-redactor event. A marked, generation-aware library
handler isolates reversible logging configuration from application-owned
handlers and propagation.

### Condition System

```text
Condition (ABC, __slots__)
├── FuncCondition          # wraps any GuardCallable
├── CompiledFuncCondition  # interpreted public wrapper + compiled invocation bridge
└── AsyncCondition         # async check() — requires AsyncStateMachine
```

`GuardResult = bool | Awaitable[bool]` and
`GuardCallable = Callable[..., GuardResult]` are public aliases from both
`fast_fsm` and `fast_fsm.core`. All built-in conditions accept and forward
`*args, **kwargs` in `check()`. Functions passed to
`FSMBuilder.add_transition()` are auto-wrapped in `FuncCondition`. A sync
machine closes and rejects an awaitable guard result; the async machine awaits
it. For guarded work, `can_trigger()`, `trigger()`,
`can_trigger_async()`, and `trigger_async()` share one private preparation
seam: positional arguments remain unchanged, while a fresh keyword mapping
filters private, non-string, and overlong keys before retaining the first 50
safe insertion-ordered keys. Built-in `NegatedCondition`, `AndCondition`,
`OrCondition`, and `NotCondition` propagate that prepared context unchanged
and preserve their normal short-circuit semantics.

The focused public vocabulary is `Condition`, `FuncCondition`,
`AsyncCondition`, `AndCondition`, `OrCondition`, and `NotCondition`.
`&`, `|`, and `~` create the compositional forms, with canonical negation
represented by `NotCondition`. `NegatedCondition`, `CompiledFuncCondition`,
and the validation/timer templates remain deprecated compatibility imports;
new application payload policy belongs in a small domain condition instead.

### Transition-entry timing

`add_transition(..., after=..., within=...)` stores immutable eligibility
metadata beside the candidate. The interval is `[after, within)`: `after` is
inclusive, `within` is exclusive, and both values are finite non-negative exact
built-in numbers (not bool), with `after < within` when both are present. A
machine accepts an injectable monotonic `clock`, records its own committed
state-entry timestamp, and samples the clock once before examining a timed
singleton or local priority group. Timing rejects before caller guards, so a
timing-ineligible candidate falls through only to a later local priority.

Queries are observational: `can_trigger()` and `can_trigger_async()` do not
advance entry time or consume mutable timer state. The commit seam validates one
timestamp before updating history/current state and before destination callbacks,
so post-commit callback failures retain the destination's entry time. Untimed
singletons keep the existing direct O(1) selection path without a selection-time
clock read; timed singleton selection is O(1), and groups remain local O(k).

The private wrapper classifier recognises only those built-in edges. It is
used by both runtime evaluation and builder preflight, recursively awaits
async leaves in the async evaluator, rejects active wrapper cycles, and
accepts acyclic shared DAGs. This is intentionally not a new public wrapper
protocol.

### FSMBuilder

The fluent builder stages identity-canonical `State` objects, auto-detects
supported nested async requirements, and returns the appropriate machine type:

```{testcode}
from fast_fsm import FSMBuilder, State

idle = State("idle")
running = State("running")

fsm = (
    FSMBuilder(idle, name="my_fsm")
    .add_state(running)
    .add_transition("start", "idle", "running")
    .build()  # → StateMachine or AsyncStateMachine
)

assert fsm.current_state is idle
assert fsm.trigger("start").success
assert fsm.current_state is running
```

`build()` creates and wires a local candidate and publishes its cached machine
only after every step succeeds. That successful cache is also the freeze
marker: repeated builds return the same object, while every later mutator,
callback registrar, and force-mode selector raises `RuntimeError`. A failed
build leaves the staging area mutable and repairable. Explicit async/sync
selection remains authoritative; explicit sync rejects a detected async
requirement before allocating a candidate.

### Atomic Transition Lifecycle

Ordinary sync and async triggers share stable private
`_LIFECYCLE_STAGE_*` constants, collected in the ordered
`_LIFECYCLE_STAGES` catalog. Resolution, guard evaluation, and state permission
happen before the lifecycle; every ordinary callback slot then belongs to one
of three named regions:

| Region | Ordered work |
|---|---|
| Pre-commit | before-transition listeners → source `State.on_exit` → registered source exit callbacks → exit-state listeners |
| Commit | `_commit_transition()` updates `_current_state` and appends the optional `TransitionRecord` without a callback or await. |
| Post-commit | destination `State.on_enter` → registered destination enter callbacks → enter-state listeners → selected declarative handler → trigger callbacks → after-transition listeners |

The lifecycle labels are public result strings even though the catalog is
private: `resolution`, `guard`, `state-permission`, `before-transition`,
`source-exit`, `source-exit-callback`, `exit-state-listener`, `commit`,
`destination-enter`, `destination-enter-callback`, `enter-state-listener`,
`declarative-handler`, `trigger-callback`, and `after-transition`.

`_execute_transition()` and `_execute_transition_async()` are paired direct
runners rather than an async wrapper around a completed synchronous run. The
async runner calls synchronous callbacks inline and awaits registered async
source/destination callbacks at the matching source-exit/destination-enter
slot. No automatic worker offload is implied.

The first ordinary lifecycle callback exception returns a redacted
`TransitionResult` and suppresses its remaining suffix. It never rolls back:
pre-commit failures retain source state with `committed=False`, while
post-commit failures retain the destination/history record with
`committed=True`. Successful results use `success=True`, `committed=True`,
`stage=None`, and `cause=None`; failures preserve the original exception by
identity in hidden-from-repr `cause`. `raise_if_failed()` is the explicit
exception boundary and chains `TransitionError` from that cause without
formatting it into public text.

All failed ordinary paths terminate through `_finalize_failure()` at the public
trigger boundary. It preserves the existing
`on_failed(trigger, from_state, error, **kwargs)` observer signature, invokes
each observer exactly once in registration order, and isolates observer
`BaseException` failures so they neither recurse nor replace the original
result/cause. Direct `force_state()`/`reset()`/`restore()` retain their
separate best-effort control path; they are not ordinary trigger transactions.

`trigger_async()` catches `asyncio.CancelledError` only at its public boundary,
finalizes observers once with the reached stage and commit status, then bare
re-raises the original cancellation. It neither shields lifecycle work nor
rolls back a commit. History remains disabled with `None` and no normal-path
buffer allocation; enabled history uses `deque(maxlen=...)` and its public
property returns a chronological defensive `list` copy.

### Safe Ownership and Concurrency

Phase 18 makes every public machine write an ownership-admitted operation while
preserving the Phase 17 lifecycle. The implementation has one private body per
operation: the public boundary admits once, then delegates to an
already-owned body. Public methods must never obtain ownership by calling
another public writer (`safe_trigger()`/`trigger()`, `reset()`/`force_state()`,
and `restore()`/`force_state()` are the important delegation seams).

The synchronous admission flow first checks the per-instance owner marker,
then acquires that machine's private lock, installs ownership, executes the
complete operation, and clears/releases in `finally`. It covers preparation,
guards, lifecycle callbacks, commit, history, topology updates, and final
result construction. A same-owner call raises a redacted `RuntimeError` before
preparation; independent threads serialize a full write. The per-machine lock
does not promise fairness, a timeout, queue order, or sharing between machines.

Async control first gets the running loop and permanently binds or validates
the exact loop identity. It then checks the machine's active causal root before
awaiting its per-instance asyncio lock. After admission it stores the current
task/root, runs the private async body, resets the module-level `ContextVar`
token and owner state in `finally`, and releases the lock. A callback-created
child task inherits the root and is rejected as reentrant before it can wait
behind its parent. No thread lock is held across an await; cancellation while
waiting never installs an owner, and cancellation while owning releases it
without changing the Phase 17 state/history boundary.

Inherited synchronous writers on `AsyncStateMachine` use the D-12 admission
gate. The short, non-awaiting per-instance gate atomically installs or checks
reservations during first-use configuration and is never held across an await,
callback, lifecycle, or mutation body. Before binding it permits ordinary
configuration under sync ownership. After binding it requires the bound-loop
thread while idle, rejects async-owned or foreign-loop/thread callers, and
never blocks an event loop. This makes loop identity permanent rather than a
lock implementation detail.

The policy applies to transitions, direct control, graph and history writers,
and all listener/callback/failure-observer registrars. Synchronous async
callbacks remain inline on the event-loop thread, and async callbacks are
awaited at their corresponding lifecycle slots; no automatic offload occurs.
`safe_trigger()` performs ownership admission outside its ordinary
`Exception`-to-result boundary, so ownership misuse is a precondition
`RuntimeError` while post-admission ordinary failures still return a value.
Messages use stable categories only and exclude user payloads and cause text.

The model does not add a global/shared lock, reentry queue, fairness protocol,
timeout, loop transfer, cross-field read snapshot, or worker scheduler. Phase
19 owns diagnostic snapshot consistency; Phase 20 owns installed-artifact
parity. Fresh source-tree pure/native evidence is not an installed-artifact
claim.

## mypyc Selective Compilation

Fast FSM uses [mypyc](https://mypyc.readthedocs.io/) to compile
performance-critical modules to C extensions. Compilation is **selective** —
only hot-path modules are compiled. The open `State` hierarchy remains a
supported interpreted-subclass boundary through an explicit mypyc compatibility
decorator, while the machine types remain closed compiled types.

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
- Use composition for `StateMachine` and `AsyncStateMachine`; they are closed
  compiled types and are not supported subclassing surfaces.
- `State`, `CallbackState`, `DeclarativeState`, and `AsyncDeclarativeState`
  intentionally support interpreted subclasses through
  `@mypyc_attr(allow_interpreted_subclasses=True)`. Tests for a state subclass
  hook may use a minimal local subclass and must run in both pure and compiled
  contexts; unrelated tests should still prefer composition.
- `core.py` remains the one mypyc compilation unit and
  `mypy-extensions` remains the sole runtime dependency. Phase 16 adds only
  private seams: no public export or existing public signature is removed.

## Performance Architecture

### Measured `__slots__` Policy

Relevant production classes in `src/fast_fsm/` are recursively audited by

```bash
uv run python tools/release_evidence.py slots-policy --json
```

They must be slot-protected unless they appear in that measured exception
registry. The two current exceptions are `CompiledFuncCondition`, which stays
interpreted to support user subclassing while delegating invocation to a
compiled core helper, and `TransitionError`, which uses
`@mypyc_attr(native_class=False)` to retain ordinary Python exception behavior.
Both can have an instance `__dict__`; the policy command—not an absolute
dictionary-free claim—is the authority when maintaining or auditing classes.

Slot-protected instances eliminate `__dict__` per instance, yielding:

- ~1000× lower memory per FSM vs. dict-based alternatives
- Better cache locality (contiguous attribute storage)
- Faster attribute access

| Metric | Threshold |
|--------|-----------|
| Fresh installed compiled singleton `trigger()` throughput | ≥ 200,000 ops/sec |
| Grouped dispatch and all other timings | Environment-labeled observations, not durable thresholds |
| Base FSM memory | ≤ 0.5 KB |
| Per-state overhead | ≤ 64 bytes |
| Lookup/singleton complexity | O(1) |
| Immutable group insertion / ordered selection | Local O(k) |

### Hot-Path Rules

1. **No validation in dispatch.** `validation.py` is a design-time tool.
   It and `_diagnostics.py`/`visualization.py` MUST NOT be called from
   `trigger()`, `can_trigger()`, `add_state()`, or `add_transition()`.
2. **No unrelated graph scan or dispatch-time sort.** Transition dispatch uses
   dictionary lookup, then either direct singleton dispatch or an ordered local
   candidate-group scan.
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

The supporting `_diagnostics.py` module is likewise interpreted and private:
it supplies immutable scalar rows, reserve-before-work status accounting, SCC
and sparse/dense/path primitives. It adds no runtime dependency and has no
import path back into `core.py`.
