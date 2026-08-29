<!-- refreshed: 2026-08-29 -->
# Architecture

**Analysis Date:** 2026-08-29

**Assessment Basis:** Independent inspection of the runtime, conditions,
validation, visualization, packaging, tests, and executed edge-case probes. The
architecture below distinguishes intended contracts from observed behavior.

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Public package API                        │
│                    `src/fast_fsm/__init__.py`                │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
               ▼                      ▼
┌──────────────────────────┐  ┌───────────────────────────────┐
│ Runtime FSM core         │  │ Optional design-time tooling   │
│ `src/fast_fsm/core.py`   │  │ `validation.py`, `visualization.py` │
│ State/transition/async   │  │ analysis, diagrams, JSON       │
└──────────────┬───────────┘  └───────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────┐  ┌───────────────────────────────┐
│ Guard condition system   │  │ User/application integration   │
│ `conditions.py`          │  │ callbacks, listeners, logging  │
│ `condition_templates.py` │  │ and serialized topology        │
└──────────────────────────┘  └───────────────────────────────┘
```

Fast FSM is a compact library rather than an application service. Runtime state
dispatch is concentrated in `src/fast_fsm/core.py`; optional analysis and output
features consume the runtime model but are not called by `trigger()`.

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Public API facade | Re-export runtime classes, condition types, factories, validators, and visualization helpers; derive `__version__` from package metadata | `src/fast_fsm/__init__.py` |
| Synchronous runtime | Own state registry, current state, transition table, guard evaluation, callbacks, listeners, history, snapshots, and dispatch | `src/fast_fsm/core.py` (`StateMachine`) |
| Asynchronous runtime | Extend `StateMachine` with awaitable guards and async state callbacks | `src/fast_fsm/core.py` (`AsyncStateMachine`) |
| State objects | Represent named states and lifecycle hooks; provide extension points for custom transition permission and event handling | `src/fast_fsm/core.py` (`State`, `CallbackState`, `DeclarativeState`) |
| Condition abstraction | Define synchronous/async guard contracts and callable/negation wrappers | `src/fast_fsm/conditions.py` |
| Reusable guards | Provide common always/never, key, set, regex, comparison, boolean-composition, and timing conditions | `src/fast_fsm/condition_templates.py` |
| Fluent construction | Queue states, transitions, conditions, and callbacks, auto-detecting async requirements before one-time materialization | `src/fast_fsm/core.py` (`FSMBuilder`) |
| Validation | Inspect private FSM topology for reachability, dead states, completeness, determinism, complexity, scoring, linting, and reports | `src/fast_fsm/validation.py` |
| Visualization/introspection | Render Mermaid/PlantUML, export topology and analysis as JSON, and emit fenced/document forms | `src/fast_fsm/visualization.py` |

## Pattern Overview

**Overall:** In-memory object graph with dictionary-indexed deterministic state
dispatch, plus optional builder, observer, strategy/guard, and declarative-state
patterns.

**Key Characteristics:**

- `StateMachine._states` maps state names to `State` objects, while
  `StateMachine._transitions` maps `from_state_name -> trigger_name ->
  TransitionEntry`; dispatch is direct lookup rather than scanning candidate
  transitions (`src/fast_fsm/core.py:287-337`, `src/fast_fsm/core.py:1307-1350`).
- Runtime classes use `__slots__`, and `TransitionEntry` stores the destination
  and optional guard without a per-transition tuple/dict abstraction
  (`src/fast_fsm/core.py:89-104`).
- Conditions are strategy objects with a common `check()` contract. Plain
  callables passed to `add_transition()` are normalized to `FuncCondition`, and
  `unless=` is normalized to `NegatedCondition` (`src/fast_fsm/core.py:640-743`).
- The observer surface is callback-based: listeners are registered once and
  bound-method references are cached in listener lists for the hot path
  (`src/fast_fsm/core.py:901-949`).
- Optional validation, serialization, diagram generation, history, and logging
  are opt-in concerns around the core state transition operation.

## Layers

**Public API layer:**

- Purpose: Provide stable import locations for users.
- Location: `src/fast_fsm/__init__.py`
- Contains: Re-exports and `__all__` for all supported symbols.
- Depends on: `core.py`, `conditions.py`, `condition_templates.py`,
  `validation.py`, and `visualization.py`.
- Used by: Application code, examples, tests, and documentation.

**Runtime model and dispatch layer:**

- Purpose: Register states and transitions and execute one transition from the
  current state.
- Location: `src/fast_fsm/core.py`
- Contains: `State`, `CallbackState`, `StateMachine`, `AsyncStateMachine`,
  `TransitionEntry`, `TransitionResult`, `TransitionRecord`, declarative states,
  builder, factories, and logging helpers.
- Depends on: Standard-library logging/time/asyncio/dataclasses and condition
  types from `src/fast_fsm/conditions.py`.
- Used by: Public facade, validation, visualization, user subclasses, and tests.

**Guard/condition layer:**

- Purpose: Encapsulate transition eligibility checks.
- Location: `src/fast_fsm/conditions.py`, `src/fast_fsm/condition_templates.py`.
- Contains: `Condition`, `FuncCondition`, `AsyncCondition`, `NegatedCondition`,
  and reusable concrete condition classes.
- Depends on: Standard-library `asyncio`, `time`, `re`, and typing.
- Used by: `StateMachine`, `AsyncStateMachine`, `FSMBuilder`, and callers.

**Design-time inspection/output layer:**

- Purpose: Analyze or represent an already-built FSM without changing dispatch.
- Location: `src/fast_fsm/validation.py`, `src/fast_fsm/visualization.py`.
- Contains: `FSMValidator`/`EnhancedFSMValidator`, lint/scoring helpers, and
  Mermaid/PlantUML/JSON output.
- Depends on: The public runtime object and its internal `_states`/
  `_transitions` tables. `visualization.py` uses `TYPE_CHECKING` for its core
  type and imports validation lazily inside `to_json()`.
- Used by: Tests, diagnostics, docs, and tooling; not by the hot dispatch path.

Using `A -> B` to mean “A imports/depends on B,” the practical dependency
direction is `core.py -> conditions.py`, `condition_templates.py ->
conditions.py`, and `validation.py -> core.py`. `visualization.py` imports the
core type only under `TYPE_CHECKING` and imports validation lazily inside
`to_json()`. `core.py` does not import validation or visualization, avoiding a
runtime cycle. `__init__.py` is the aggregation boundary and eagerly imports
all public modules.

## Data Flow

### Primary Synchronous Request Path

1. Caller invokes `StateMachine.trigger(trigger, *args, **kwargs)` at
   `src/fast_fsm/core.py:1492`.
2. `_resolve_trigger()` reads the current state's name and performs a direct
   lookup in `_transitions`; missing entries return a failed `TransitionResult`
   and invoke `on_failed` callbacks (`src/fast_fsm/core.py:1307-1349`).
3. If a guard exists, `trigger()` sanitizes keyword context (drops private keys,
   rejects invalid keys, and caps input at 50 items) and calls
   `Condition.check(*args, **safe_kwargs)` (`src/fast_fsm/core.py:1126-1171`,
   `src/fast_fsm/core.py:1515-1586`). The condition interface itself accepts
   only `**kwargs`, so non-empty positional arguments currently turn a guarded
   transition into a failed result rather than reaching the guard callable.
4. The current state's `can_transition()` hook is evaluated. A false result is
   returned as a failed `TransitionResult` (`src/fast_fsm/core.py:1550-1586`).
5. `_execute_transition()` runs the lifecycle in order: before listeners,
   source `on_exit`, per-source exit callbacks, exit listeners, updates
   `_current_state`, destination `on_enter`, per-destination enter callbacks,
   enter listeners, after listeners, trigger-specific callbacks, and optional
   history recording (`src/fast_fsm/core.py:1350-1490`).
6. A successful `TransitionResult` containing source, destination, and trigger
   names is returned (`src/fast_fsm/core.py:1480-1490`).

### Asynchronous Request Path

1. Caller invokes `await AsyncStateMachine.trigger_async(...)` at
   `src/fast_fsm/core.py:1812`.
2. The same direct transition resolution and failure callback model is used.
3. `AsyncCondition.check_async()` is awaited when the guard is asynchronous;
   synchronous conditions still call `check()` (`src/fast_fsm/core.py:1833-1882`).
   Unlike the sync path, both `trigger_async()` and `can_trigger_async()` pass
   raw keyword arguments and do not call `_sanitize_condition_kwargs()`.
4. The state permission hook uses `can_transition_async()` when the current
   state provides it, otherwise it falls back to `can_transition()`
   (`src/fast_fsm/core.py:1884-1911`).
5. The entire synchronous `_execute_transition()` lifecycle runs first,
   including state mutation, synchronous enter/exit/listener callbacks,
   after-transition callbacks, and history recording. Registered async exit
   callbacks and then async enter callbacks run only afterward
   (`src/fast_fsm/core.py:1913-1944`). This ordering is observable and is not a
   transactional async lifecycle.

### Construction and Inspection Flows

- `StateMachine.from_states()`, `quick_build()`, and `from_dict()` create state
  objects, register them, then call `add_transition()` (`src/fast_fsm/core.py:339-559`).
- `FSMBuilder` queues declarations and creates exactly one machine in `build()`;
  async components promote the selected class when auto-detection is enabled
  (`src/fast_fsm/core.py:2268-2669`).
- `snapshot()` stores only current state and version; `restore()` validates that
  shape and delegates to `force_state()` (`src/fast_fsm/core.py:1209-1253`).
- `to_dict()` exports topology without callable guards, while
  `StateMachine.from_dict(..., conditions=...)` reattaches guards by trigger
  name (`src/fast_fsm/core.py:447-593`).
- Validators and renderers walk `_states` and `_transitions` after construction;
  they do not mutate the machine (`src/fast_fsm/validation.py:21-228`,
  `src/fast_fsm/visualization.py:33-310`).

**State Management:**

- `_initial_state` is retained as the reset target; `_current_state` holds the
  active object. State registration is name-keyed and transitions store actual
  destination objects (`src/fast_fsm/core.py:287-338`,
  `src/fast_fsm/core.py:625-638`).
- `force_state()` and `reset()` bypass guards but preserve lifecycle callback
  execution; `clone()` shallow-copies topology and callback lists while
  resetting current state and disabling copied history (`src/fast_fsm/core.py:1173-1306`).

## Key Abstractions

**`TransitionEntry`:**

- Purpose: Store one trigger's destination `State` and optional `Condition`.
- Examples: `src/fast_fsm/core.py:89-104`, consumed by
  `StateMachine._transitions`.
- Pattern: Compact `__slots__` value object for dictionary-indexed dispatch.

**`Condition`:**

- Purpose: Uniform guard interface for callable, composed, negated, timing, and
  asynchronous checks.
- Examples: `src/fast_fsm/conditions.py:15-149`,
  `src/fast_fsm/condition_templates.py:8-181`.
- Pattern: Strategy/adapter; use `check()` for sync and `check_async()` for async.

**`State`:**

- Purpose: Named extension point for lifecycle hooks, transition permission, and
  event handling.
- Examples: `src/fast_fsm/core.py:173-231`, `CallbackState` at
  `src/fast_fsm/core.py:232-263`, and user-defined subclasses in `examples/`.
- Pattern: Template method/base class; override hooks while preserving the
  machine's dispatch and result contracts.

**`TransitionResult`:**

- Purpose: Explicit success/failure value returned by all transition operations.
- Examples: `src/fast_fsm/core.py:41-62`, `src/fast_fsm/core.py:1492-1630`.
- Pattern: Slot-backed dataclass-style result object; call
  `raise_if_failed()` when exception-style control flow is desired.

**Declarative handler metadata:**

- Purpose: Let state methods declare trigger/from/to/guard metadata with
  `@transition` and be discovered once at state construction.
- Examples: decorator at `src/fast_fsm/core.py:1950-1975`, discovery at
  `src/fast_fsm/core.py:2006-2032`.
- Pattern: Metadata/declarative adapter over normal `State` hooks; use
  `AsyncDeclarativeState` for awaitable handlers and guards.

## Entry Points

**Library import:**

- Location: `src/fast_fsm/__init__.py`
- Triggers: `import fast_fsm`.
- Responsibilities: Expose the supported API and package version.

**Synchronous machine:**

- Location: `src/fast_fsm/core.py` (`StateMachine` and `simple_fsm`/`quick_fsm`).
- Triggers: Direct constructor, class factories, or convenience functions.
- Responsibilities: Build topology and execute `trigger()`.

**Asynchronous machine:**

- Location: `src/fast_fsm/core.py` (`AsyncStateMachine`).
- Triggers: Direct construction or `FSMBuilder.build()` after async detection.
- Responsibilities: Execute `trigger_async()` and await async guards/hooks.

**Declarative states:**

- Location: `src/fast_fsm/core.py` (`transition`, `DeclarativeState`,
  `AsyncDeclarativeState`).
- Triggers: User subclasses decorated with `@transition`.
- Responsibilities: Discover handlers and normalize handler return values into
  `TransitionResult` when callers invoke `handle_event()` or
  `handle_event_async()` directly. Normal `StateMachine.trigger()` /
  `trigger_async()` dispatch does not invoke the decorated handler; it uses only
  the handler metadata's condition through `can_transition*()`.

**Design-time tooling:**

- Location: `src/fast_fsm/validation.py` and `src/fast_fsm/visualization.py`.
- Triggers: Explicit calls such as `validate_fsm(fsm)`, `to_mermaid(fsm)`, or
  `to_json(fsm)`.
- Responsibilities: Report structural quality and emit diagrams/JSON.

## Architectural Constraints

- **Threading:** No locks or worker threads are used. Sync operations run in the
  caller's thread; async operations use the caller's event loop. Concurrent
  mutation/triggering is not coordinated by the library (`src/fast_fsm/core.py`).
- **Global state:** No FSM singleton or module-level mutable machine registry is
  present. Each `StateMachine` owns its tables and callback lists. Python's
  module-level logging registry is used by `configure_fsm_logging()`
  (`src/fast_fsm/core.py:2679-2776`).
- **Circular imports:** No runtime cycle is detected. `core.py` imports condition
  abstractions; `validation.py` imports `StateMachine`; visualization uses a
  type-checking import and lazy validation import (`src/fast_fsm/visualization.py`).
- **Compilation boundary:** `setup.py` compiles only `src/fast_fsm/core.py` with
  mypyc. Keep `src/fast_fsm/conditions.py` interpreted so user-defined condition
  subclasses remain possible (`setup.py`, `src/fast_fsm/core.py:106-166`).
- **Performance:** Core lookup, state registration, and transition insertion are
  designed as O(1); avoid scans, validation, or new allocations in the normal
  `trigger()` path (`src/fast_fsm/core.py`, `docs/dev/architecture.md`).
- **Topology ownership:** `validation.py` and `visualization.py` intentionally
  read private `_states` and `_transitions`; changes to those internal shapes
  require updating both consumers and their tests.
- **Graph invariants are not enforced:** `add_transition()` accepts unknown
  source names and unregistered `State` targets, while duplicate state names
  replace `_states[name]` without rewriting existing `TransitionEntry` object
  references. The runtime, diagnostics, and public `states` list can therefore
  disagree about one machine.
- **Initial-state representation is duplicated:** Runtime reset uses
  `_initial_state`, visualization derives the initial name from the first
  `_states` key, and `FSMValidator` currently captures `current_state` as its
  `initial_state`. These are equivalent only while graph invariants hold and
  validation occurs before dispatch.

## Anti-Patterns

### Calling design-time analysis from dispatch

**What happens:** A caller invokes validation or diagram generation on every
trigger or embeds `FSMValidator` in a runtime callback.

**Why it's wrong:** `src/fast_fsm/validation.py` performs graph walks and scoring,
which defeats the O(1) hot path and adds avoidable allocations.

**Do this instead:** Validate once after construction or in CI using
`validate_fsm()`/`EnhancedFSMValidator` in `src/fast_fsm/validation.py`.

### Mutating private topology tables directly

**What happens:** Code edits `_states`, `_transitions`, or `_current_state`
without the machine methods.

**Why it's wrong:** It can leave transition destinations, per-state tables, and
callback behavior inconsistent; analysis/output modules also depend on their
shape.

**Do this instead:** Use `add_state()`, `add_transition()`, `force_state()`,
`restore()`, and `reset()` in `src/fast_fsm/core.py`.

### Running async components through sync APIs

**What happens:** An `AsyncCondition` or async declarative handler is attached to
`StateMachine`, or `trigger()` is used where asynchronous work is required.

**Why it's wrong:** Sync registration rejects async guards and sync declarative
states cannot await them (`src/fast_fsm/core.py:640-743`,
`src/fast_fsm/core.py:2034-2084`).

**Do this instead:** Use `AsyncStateMachine.trigger_async()` or let
`FSMBuilder` auto-detect async components (`src/fast_fsm/core.py:1782-1944`,
`src/fast_fsm/core.py:2352-2380`).

## Error Handling

**Strategy:** Expected transition failures are values (`TransitionResult`), while
invalid topology/API use raises `ValueError`, `TypeError`, or `KeyError`. Guard
exceptions are converted to failed results and lifecycle callback exceptions are
logged and swallowed. Exceptions from `State.can_transition()` are not caught by
`trigger()` and can propagate; `safe_trigger()` is the public catch-all for those
ordinary `Exception` failures.

**Patterns:**

- Missing triggers, failed guards, and state vetoes return
  `TransitionResult(False, ...)` and invoke registered `on_failed` callbacks
  (`src/fast_fsm/core.py:1492-1630`).
- `TransitionResult.raise_if_failed()` provides opt-in exception behavior via
  `TransitionError` (`src/fast_fsm/core.py:25-62`).
- Invalid target states and mutually exclusive `condition`/`unless` arguments
  fail during `add_transition()` (`src/fast_fsm/core.py:640-743`).
- Lifecycle/listener callback exceptions are logged so user hooks do not corrupt
  control flow (`src/fast_fsm/core.py:1350-1480`). This is best-effort isolation,
  not rollback: the state is mutated before destination-entry callbacks, and a
  successful result may be returned even when one or more side effects failed.

## Cross-Cutting Concerns

**Logging:** Per-machine and per-state loggers use Python `logging`; public
helpers configure hierarchy and verbosity (`src/fast_fsm/core.py:2679-2776`).

**Validation:** Runtime guard context is sanitized in
`StateMachine._sanitize_condition_kwargs()`; structural validation is explicit
and external to dispatch (`src/fast_fsm/core.py:1126-1171`,
`src/fast_fsm/validation.py`).

**Authentication:** Not applicable; Fast FSM is an in-process library with no
service boundary or identity provider.

**Serialization:** Topology is JSON-safe through `to_dict()`/`from_dict()` and
state snapshots through `snapshot()`/`restore()`; callable guards and callback
objects are intentionally not serialized (`src/fast_fsm/core.py:447-593`,
`src/fast_fsm/core.py:1209-1253`).

---

*Architecture analysis: 2026-08-29*
