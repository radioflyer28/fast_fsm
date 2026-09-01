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
| `_transitions` | `dict[str, dict[str, TransitionEntry]]` | `from_state → {trigger → (to_state, condition)}` |
| `_initial_state` | `State` | Declared construction identity |
| `_current_state` | `State` | Active state reference |
| `_graph_version` | `int` | Monotonic successful-topology version |

`trigger()` is a dictionary lookup by the current-state name, then a
dictionary lookup by trigger. No topology scanning is on the dispatch path.

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

Reentrancy and caller ownership/serialization remain Phase 18. Diagnostic and
logging architecture remains Phase 19. Fresh source-tree parity is documented
below, but installed-wheel parity remains Phase 20.

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
