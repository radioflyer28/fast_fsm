# Architecture Research

**Domain:** Reliability hardening of a high-performance in-process Python finite state machine library
**Milestone:** v0.3.0 Reliability & Runtime Hardening
**Researched:** 2026-08-29
**Confidence:** HIGH for codebase integration; MEDIUM for performance impact until compiled and pure-Python benchmarks run

## Executive Recommendation

Keep `src/fast_fsm/core.py` as the single mypyc compilation unit, but give it explicit internal boundaries instead of duplicating behavior across public methods. The core should own four small internal seams: canonical graph registration, immutable graph snapshots, transition admission/resolution, and staged lifecycle execution. These may be private classes and methods inside `core.py`; they are not a proposal to split the compilation unit.

The safe-default transition contract should be fail-fast and non-queueing. Exactly one transition or topology mutation may own a machine at a time. Reentrant and concurrent attempts fail immediately. Callback failures before the state assignment abort without committing; failures after the state assignment return a failed result that explicitly says the transition committed. Post-commit rollback should not be attempted because arbitrary user callbacks are not reversible.

Validation and visualization should stop reading `_states` and `_transitions` directly. They should consume one immutable `_GraphSnapshot` captured from the machine. This simultaneously fixes initial-state drift, partial cycle membership, representation coupling, and inconsistent output. Expensive diagnostics remain outside the hot path and receive explicit analysis budgets.

## Recommended Architecture

### System Overview

```text
┌────────────────────────────────────────────────────────────────────┐
│ Public construction and execution API                              │
│ StateMachine · AsyncStateMachine · FSMBuilder · factories          │
└───────────────┬───────────────────────────────┬────────────────────┘
                │                               │
                ▼                               ▼
┌────────────────────────────────┐  ┌───────────────────────────────┐
│ Canonical graph owner          │  │ Transition control gate       │
│ state registry                 │  │ non-blocking ownership        │
│ transition table               │  │ reentrancy/concurrency reject │
│ initial-state identity         │  └──────────────┬────────────────┘
│ graph version                  │                 │
└──────────────┬─────────────────┘                 ▼
               │                    ┌───────────────────────────────┐
               │                    │ Shared transition pipeline    │
               │                    │ resolve → guard → pre-commit  │
               │                    │ → commit → post-commit        │
               │                    └──────────────┬────────────────┘
               │                                   │
               ▼                                   ▼
┌────────────────────────────────┐  ┌───────────────────────────────┐
│ Immutable graph snapshot       │  │ Runtime outputs               │
│ states · edges · initial       │  │ result · history · redacted   │
│ current · guard metadata       │  │ logging · failure notification│
└──────────────┬─────────────────┘  └───────────────────────────────┘
               │
       ┌───────┴───────────────────┐
       ▼                           ▼
┌───────────────────────┐  ┌───────────────────────────────────────┐
│ Bounded validation    │  │ Escaped visualization / JSON          │
│ SCC · reachability    │  │ deterministic aliases · shared analysis│
│ sparse-first output   │  │                                       │
└───────────────────────┘  └───────────────────────────────────────┘
```

### Component Responsibilities

| Component | Status | Responsibility | Location |
|-----------|--------|----------------|----------|
| `_TransitionControl` methods/fields | New internal boundary | Own non-blocking transition/topology admission, owner token, and guaranteed release | Inside `core.py`; fields on `StateMachine.__slots__` |
| Canonical graph registration | Modified | Validate all endpoints and duplicates before atomically inserting any state/edge; increment graph version | `_register_state()`, `add_state()`, `add_transition()` in `core.py` |
| `_GraphSnapshot` / `_TransitionSnapshot` | New internal value objects | Immutable, deterministic representation of initial/current state, state names, transitions, guard labels, and graph version | Private slot-backed classes in `core.py` |
| Guard preparation/evaluation | New shared helper boundary | Sanitize guard kwargs once, preserve positional args, evaluate sync/async guards consistently | Private helpers in `core.py`; compatible signatures in `conditions.py` |
| Transition plan and lifecycle pipeline | Modified | Resolve one O(1) entry, execute the same ordered stages for sync and async paths, and return commit-aware results | Private methods in `core.py` used by all trigger variants |
| `TransitionResult` / `TransitionRecord` | Modified additively | Distinguish failure from commit status and preserve committed transitions even when post-commit callbacks fail | `core.py` |
| Declarative handler binding | Modified | Validate decorator metadata during registration and bind the discovered handler to the transition entry | `TransitionEntry`, declarative states, graph registration in `core.py` |
| `FSMBuilder` lifecycle | Modified | Stage configuration until one build; reject every mutator after build; reuse graph validation and recursive async detection | `core.py` |
| `AnalysisBudget` | New design-time component | Bound states, edges, matrix cells, path count, and aggregate work; fail explicitly rather than silently truncate correctness fields | `validation.py` |
| Snapshot-based graph analyzer | Modified | Use initial identity from snapshot, SCC-based cycle/longest-path analysis, sparse adjacency, stable comparison identities | `validation.py` |
| Snapshot-based renderers | Modified | Use deterministic collision-free aliases and syntax-specific escaping; obtain reachability/cycles from shared analyzer | `visualization.py` |
| Library logging boundary | Modified | Log metadata rather than payload values; never clear application handlers; manage only an explicitly created Fast FSM handler | `core.py`, package initialization/docs |
| Artifact parity harness | New verification boundary | Install isolated compiled and pure-Python wheels, assert selected implementation, run the same behavioral traces and performance gate | CI, packaging scripts, tests; no runtime dependency |

## Core Internal Boundaries

### 1. Canonical Graph Registration

`_states` remains the canonical name-to-object registry and `_transitions` remains the O(1) source/trigger lookup. Hardening should enforce these invariants at every mutation boundary:

1. `_initial_state`, `_current_state`, and every transition endpoint are the exact objects stored in `_states[name]`.
2. Every registered state has one transition bucket, even when empty.
3. Every transition source and target is registered before an edge is inserted.
4. Registering the same `State` object twice is an idempotent no-op; registering a different object with the same name raises `ValueError`.
5. A fan-out `add_transition()` validates all source endpoints, target, guard type, and declarative metadata before inserting any edge. Failure leaves the graph unchanged.
6. One `(source, trigger)` key has one entry. Replacement, if retained as supported behavior, is explicit and atomic rather than a side effect of partial registration.
7. Every successful topology mutation increments `_graph_version`.

Do not auto-register an unknown `State` target only because an object was supplied. Requiring explicit registration makes string and object inputs behave identically and prevents accidental cross-machine object reuse. Factory and builder paths already know the full state set and should register it before edges.

Graph mutation must use the same control gate as transition execution. A mutation attempted from a callback or concurrently with a transition raises `RuntimeError` immediately. This is configuration misuse, not an ordinary failed trigger, so an exception is clearer than `TransitionResult`.

### 2. Immutable Graph Snapshot Protocol

Add a private `StateMachine._graph_snapshot()` method returning a slot-backed immutable value with this logical shape:

```python
_GraphSnapshot(
    version: int,
    machine_name: str,
    initial_state: str,
    current_state: str,
    states: tuple[str, ...],
    transitions: tuple[_TransitionSnapshot, ...],
)

_TransitionSnapshot(
    source: str,
    trigger: str,
    target: str,
    has_guard: bool,
    guard_name: str | None,
)
```

The method captures all fields while it exclusively owns the machine control gate, then releases the gate before any analysis. State and transition ordering should be deterministic: state registration order for lifecycle-compatible output, and `(source registration index, trigger)` order for edges. Consumers may sort labels for presentation, but must not infer the initial state from ordering.

The snapshot deliberately excludes callable objects, state instances, callbacks, locks, and history. It is a structural observation boundary, not a clone or persistence format. `validation.py` and `visualization.py` may depend on this private protocol; they should no longer depend on the mutable table layout.

Snapshot capture is O(V + E) and never occurs during `trigger()`. If capture is attempted from inside a callback or while another owner is active, fail explicitly rather than deadlock or return a torn graph.

### 3. Transition Control Gate

Add a primitive `threading.Lock`, an owner token, and an active operation label to the state machine. All state-changing methods (`trigger*`, `force_state`, `reset`, `restore`) and topology mutators acquire the primitive lock with `blocking=False`.

The owner token must include the OS thread identifier and, when running asynchronously, the current task identity. This permits distinct errors for:

- **Reentrant attempt:** same thread/task calls back into the machine while its outer operation is active.
- **Concurrent attempt:** another thread or asyncio task attempts to use the same machine.

Both cases fail immediately. `trigger()` and `trigger_async()` return `TransitionResult(success=False, committed=False, phase="admission", ...)`; mutation/configuration methods raise `RuntimeError`. The gate is held through callback execution and released in `finally`, including when a `BaseException` escapes. `can_trigger*()` should return `False` while another operation is active and must never wait.

Use a primitive `Lock`, not `RLock`: Python documents that `RLock` deliberately permits same-thread recursion, which conflicts with the selected safe default. Never call blocking `acquire()` from an async path. The single non-blocking primitive lock can span awaited callbacks because competitors also use non-blocking acquisition and therefore cannot block an event-loop thread.

This lock is a performance-sensitive seam. The first implementation gate is compiled and pure-Python throughput at or above 200,000 `trigger()` operations/sec. If it fails, optimize owner-token construction and failure allocation before considering a weaker concurrency contract.

### 4. Transition Resolution and Commit Lifecycle

Refactor duplicated sync/async behavior around one logical transition plan:

```text
ADMIT
  non-blocking ownership gate
    ↓
RESOLVE
  current object + O(1) transition entry + original source identity
    ↓
AUTHORIZE
  prepared guard context → entry guard → state/declarative guard
    ↓
PRE-COMMIT (fail-fast)
  before listeners → declarative handler → source exit hook
  → registered exit callbacks/listeners (sync or awaited async)
    ↓
COMMIT (exactly once)
  verify source identity still matches → assign target → append history record
    ↓
POST-COMMIT (fail-fast)
  target enter hook → registered enter callbacks/listeners
  → after-transition listeners → trigger callbacks
    ↓
FINALIZE
  completed result or commit-aware callback failure → notify failure once
```

Concrete failure semantics:

| Failure point | State after return | `success` | `committed` | History |
|---------------|--------------------|-----------|-------------|---------|
| Admission, lookup, guard, state veto | Source | `False` | `False` | No record |
| Declarative handler or any pre-commit callback | Source | `False` | `False` | No record |
| Assignment invariant failure | Source | `False` | `False` | No record |
| Any post-commit callback | Target | `False` | `True` | Record marked callback-failed |
| Complete lifecycle | Target | `True` | `True` | Record marked completed |

Append `committed: bool = False` and `phase: str = ""` to `TransitionResult` so existing positional construction remains valid. Add outcome/error fields with defaults to `TransitionRecord`; when history is enabled, append at the commit point and update the record outcome after post-commit completion. History is then a truthful commit log, not a list of only fully successful callback chains.

Do not attempt automatic rollback after a post-commit callback failure. Earlier callbacks may have performed I/O or mutated external state, and running reverse callbacks would create a second untestable failure chain. The safe behavior is to stop remaining callbacks, retain the target state, return `success=False, committed=True`, identify the failed lifecycle phase, and invoke failure observers exactly once.

`on_failed` observers are reporting hooks, not part of the transaction. Their exceptions are logged without replacing the originating result. They execute while the control gate is still owned so they cannot start a nested transition.

### 5. Guard and Declarative Dispatch Integration

Create one guard-context helper used by `can_trigger`, `trigger`, `can_trigger_async`, and `trigger_async`. It should:

- preserve positional arguments;
- apply the same private-key, key-length, and count policy to keyword arguments;
- return a prepared context without mutating the caller's dictionary;
- never log values;
- feed both interpreted `Condition` subclasses and compiled callable wrappers.

The interpreted `Condition.check()` contract and all wrappers must accept and forward `*args, **kwargs`; otherwise core-side forwarding cannot work. The original unsanitized context may still be delivered to lifecycle callbacks, because guard sanitization is a guard boundary rather than a general callback permission system. This distinction must be documented.

At edge registration, detect whether the source is a declarative state with a matching handler. Validate the decorator's `from_state` and `to_state` metadata against the actual edge, then store the bound handler in the `TransitionEntry`. Normal trigger execution calls that handler in the pre-commit stage. A failed handler aborts the transition; an async handler is awaited. `handle_event*()` remains available for direct state-level dispatch, but normal machine dispatch is no longer disconnected from the declared action.

Construction-time async detection must recursively inspect condition wrappers such as `NegatedCondition` and any boolean composites. Keep this recursion out of the trigger path. One `_requires_async(component)` helper should be shared by builder detection and registration validation.

### 6. Sync/Async Parity

Sync and async public methods should share resolution, failure construction, history recording, and lifecycle stage definitions. The difference should be the stage executor:

- Sync executor invokes sync guards and callbacks and rejects awaitables.
- Async executor awaits async guards/callbacks and invokes permitted sync hooks in the same stage order.
- Both prepare identical guard context and produce equivalent result/history traces.

For `AsyncStateMachine`, introduce a constructor policy for synchronous user callbacks. The safe default is `sync_callback_policy="error"`: registration/build fails when an async machine contains a custom synchronous state hook, synchronous listener, or per-state callback. Explicit opt-ins may be `"inline"` for known non-blocking callbacks or `"thread"` for application-approved offloading. Do not silently move existing callbacks to worker threads; thread affinity and event-loop ownership are application semantics.

Add async listener hooks matching every synchronous lifecycle stage rather than forcing async applications through synchronous observer methods. The parity suite should compare ordered lifecycle traces for guard pass/fail, declarative handlers, exit/enter callbacks, listener failure, history, and reentrancy.

## Builder Lifecycle

`FSMBuilder` should become a one-way staging object:

```text
MUTABLE (collect declarations) ──build()──▶ BUILT (terminal)
       ▲                                      │
       └──────── no transition back ──────────┘
```

Add `_ensure_mutable()` and call it before every mutator: states, transitions, sync/async callbacks, and `force_sync()`/`force_async()`. After `build()`, every mutator raises `RuntimeError`; repeated `build()` returns the already-built machine. This removes stale-cache ambiguity without changing successful builder chains.

Before constructing the machine, validate the entire staged graph and async mode. Then register states first and edges second through the same canonical `StateMachine` methods. Do not maintain a separate relaxed builder interpretation of endpoint names or duplicate states.

## Diagnostic Architecture and Budgets

### Snapshot-Based Analysis

`FSMValidator` captures one `_GraphSnapshot` at construction and uses `snapshot.initial_state`, never `fsm.current_state`, for reachability. It may include `snapshot.current_state` in reports without changing the analysis root.

Build a sparse adjacency mapping once from snapshot transitions. Use it for BFS reachability, dead-state checks, SCC computation, and longest path. Strongly connected components provide complete cycle membership; condense SCCs into a DAG and compute longest path with dynamic programming in O(V + E), replacing exponential path enumeration for that metric.

Dense adjacency matrices remain an explicit export, not the internal representation. Before allocation, enforce `states * states <= max_matrix_cells`. Return a clear diagnostic-limit exception with the requested and allowed sizes; never emit a partial matrix while labeling it complete.

### Default Analysis Budget

Introduce an optional budget object/keyword with conservative defaults:

| Limit | Default | Applied to |
|-------|---------|------------|
| States | 10,000 | Snapshot analysis admission |
| Edges | 100,000 | Snapshot analysis admission |
| Matrix cells | 1,000,000 | Dense adjacency export |
| Generated paths | 1,000 | Test path generation |
| Aggregate work steps | 2,000,000 | Traversals/path expansion |

Public diagnostic functions should accept a budget override. Budget exhaustion is a typed, explicit failure containing the operation and consumed limit. `to_json()` should surface an `analysis_error` object for a budget failure rather than catch every `Exception` and silently set quality to `None`.

### Comparison Identity

`fsm.name` is display metadata, not collection identity. `compare_fsms()` and `batch_validate()` must preserve input ordinal identity. For backward-friendly mapping output, use deterministic disambiguated keys (`name`, `name#2`, `name#3`) and include both `input_index` and original `name` in each result. Empty comparison returns empty rankings with `avg_score=None` and `score_range=None`; no division is attempted.

## Visualization and Serialization Flow

Renderers consume `_GraphSnapshot` and build deterministic aliases independent of user text:

```text
snapshot state order → S0, S1, S2, ...
user state names     → escaped display labels only
edge endpoints       → aliases only
trigger/guard/title  → syntax-specific escaped labels
```

This prevents Mermaid identifier collisions such as `a-b` versus `a b` and avoids treating PlantUML user labels as syntax. Implement separate escaping helpers for Mermaid comments/labels and PlantUML quoted labels; strip or encode newlines and control characters.

`to_json()` should use the snapshot for topology and the shared analyzer for reachability, SCC cycle membership, and quality. It must not maintain a second DFS implementation. Cycle fields then represent all members of every cyclic SCC, including self-loops and middle nodes in longer cycles.

## Logging Boundary

Transition trace logs should include machine name, trigger, source, positional-argument count, and sanitized keyword names only. Never interpolate argument values by default. If payload logging is ever offered, it must require an explicit application-supplied redactor and remain off by default.

`configure_fsm_logging()` is explicitly invoked by an application, so it may create a convenience handler, but it must mark that handler as Fast-FSM-owned. Reconfiguration updates or replaces only the marked handler. It never calls `logger.handlers.clear()`, never removes application handlers, and sets propagation deliberately. Add a matching removal/restoration helper so configuration is reversible. At package import, use only a `NullHandler` if suppression of the standard last-resort handler is desired.

## Compiled and Pure-Python Verification Boundary

Parity cannot be established from an editable checkout because a stale ignored extension can shadow `core.py`. Verification should build and install artifacts in isolated temporary environments:

```text
clean source tree
    ├── strict compiled wheel build
    │     ├── assert core module has extension suffix
    │     ├── run full behavior/parity suite
    │     └── run >=200k trigger/sec gate
    └── intentional pure-Python wheel build
          ├── assert core module has .py suffix
          ├── run the same behavior/parity suite
          └── run >=200k trigger/sec gate
```

The release build must use a strict flag that converts mypyc compilation failure into build failure. A separate intentional pure-Python flag may suppress compilation, but import-path assertions are mandatory in both jobs. Compare serialized transition traces across the two installations for graph invariants, callback ordering/failure, reentrancy, async parity, builder behavior, snapshots, and diagnostics.

Do not add a runtime dependency for this harness. Use existing build tooling, subprocesses/temporary virtual environments, and CI matrices. Keep `conditions.py` interpreted and verify user-defined `Condition` subclasses against both installed artifacts.

## Performance-Sensitive Seams

| Seam | Hot-path rule | Verification |
|------|---------------|--------------|
| Transition control gate | One non-blocking acquire/release; no waiting, queue, context copy, or graph scan | Compiled and pure unguarded trigger benchmark |
| Transition resolution | One current-state lookup and one trigger lookup | Microbenchmark and profiler |
| Guard preparation | Run only when an entry has a guard; no preparation for unconditional transitions | Guarded versus unguarded benchmark |
| Declarative action | One `None` branch for ordinary entries; direct bound call when present | Declarative parity benchmark |
| History | One `None` branch when disabled; `deque(maxlen=...)` append when enabled | Disabled and enabled throughput tests |
| Graph snapshot | Never called from trigger path; O(V + E) only on explicit inspection | Large sparse graph tests |
| Diagnostics | Sparse representation by default; budgets before dense allocation | Budget boundary tests |
| Logging | `isEnabledFor` before constructing metadata; no value formatting | Logging-disabled benchmark |

Use `collections.deque(maxlen=max_entries)` for history. Validate `max_entries` as a positive integer; zero or negative values raise `ValueError`. Python documents bounded deque append/eviction as approximately O(1), unlike list-front deletion.

## High-Risk Integration Points

| Risk | Why high-risk | Required control |
|------|---------------|------------------|
| Lock held across user callbacks/awaits | A missing `finally` can permanently disable a machine | Fault-injection tests for every lifecycle stage and `BaseException` release |
| Post-commit callback failure | Result failure while state is target can surprise callers | Add `committed`, phase-specific errors, history outcome, explicit docs |
| Reentrancy from failure observers | Failure reporting can recursively trigger another failure | Keep ownership through `on_failed`; deterministic reentrancy result |
| Sync/async stage drift | Existing implementations duplicate logic and order callbacks differently | One stage model plus trace-equivalence tests |
| Declarative handler activation | Previously dormant side effects will begin executing | Registration validation, examples, explicit migration note |
| Duplicate state names/object identity | Replacing objects leaves stored entries stale | Same-object idempotence, different-object rejection, invariant tests |
| Graph snapshot under mutation | Torn snapshot corrupts all diagnostics | Capture only under machine ownership gate |
| Diagnostic budget semantics | Silent truncation produces false claims | Typed explicit failure; mark partial outputs as partial if later introduced |
| Identifier escaping | Diagram languages have different grammars | Per-format escaping tests including control text, Unicode, collisions |
| Compiled slot layout | New fields/classes can compile differently from Python | Declare every field, run mypy/mypyc guard, full installed-wheel tests |
| Async sync-callback policy | Rejecting existing sync hooks is behaviorally breaking | Constructor policy, build-time error, migration documentation |
| Strict build mode | Optional compilation currently hides failures | Release-only strict flag plus artifact suffix assertion |

## Dependency-Aware Build Order

1. **Restore an auditable baseline.** Fix version/changelog/test-count drift and make existing lint/format/docs/tests green. Add import-mode assertions before changing runtime behavior so later parity results are trustworthy.
2. **Enforce graph identity and introduce snapshots.** Implement atomic endpoint validation, duplicate-name policy, graph versioning, and `_GraphSnapshot`. Convert simple topology serialization first. This is the dependency for builders, validators, and renderers.
3. **Freeze builder lifecycle and normalize construction.** Add terminal builder state, reuse graph registration, and recursively detect async wrappers. Construction must be trustworthy before dispatch semantics change.
4. **Build the synchronous transition pipeline.** Add control gate, centralized resolution/guard preparation, staged callbacks, commit-aware results/history, deque history, and reentrancy/concurrency tests. Benchmark immediately.
5. **Connect declarative handlers and implement async parity.** Bind handlers at registration, add async stage execution and callback policy, and compare ordered traces against sync behavior. This depends on the stable pipeline rather than duplicating it.
6. **Migrate validation to snapshots and budgets.** Fix initial identity, SCC cycle analysis, longest-path complexity, empty/duplicate comparisons, sparse output, and explicit limits.
7. **Migrate visualization/JSON and harden logging.** Add deterministic aliases/escaping, reuse shared analysis, redact trace metadata, and make explicit logging configuration non-destructive/reversible.
8. **Prove artifact parity and release integrity.** Build isolated strict compiled and intentional pure wheels across supported Python/platform CI, run the full suite and trace comparisons, enforce throughput, then cut v0.3.0 metadata and changelog from one source of truth.

The ordering intentionally places semantic runtime work after graph invariants and before diagnostics. Otherwise validators and visualizers would be repaired against an unstable private representation, and sync/async fixes would be implemented twice without a shared lifecycle contract.

## Anti-Patterns to Avoid

### Splitting the Core to Achieve Conceptual Separation

**Do not:** Move transition helpers into new runtime modules imported by `core.py` merely to make files smaller.

**Why:** `core.py` is the required mypyc compilation unit, and cross-module helpers would change compilation/subclass behavior and add call boundaries.

**Instead:** Define small private slot-backed values and methods inside `core.py`; separate responsibilities conceptually and with tests.

### Reentrant Locks or Transition Queues

**Do not:** Use `RLock` or silently queue nested/concurrent triggers.

**Why:** `RLock` permits the exact same-thread recursion that corrupts current behavior. Queueing changes ordering, lifetime, backpressure, and exception delivery into a scheduler problem.

**Instead:** Non-blocking admission and immediate typed failure.

### Automatic Callback Rollback

**Do not:** Assign the source state again after a target-enter or after-transition callback fails.

**Why:** External side effects are not reversible; rollback callbacks can fail and produce a third state of truth.

**Instead:** Distinguish committed failure from uncommitted failure and require application-level compensation.

### Catch-All Diagnostic Degradation

**Do not:** Catch every exception and emit `quality=None`.

**Why:** Algorithm bugs, malformed topology, and budget exhaustion become indistinguishable from an optional import.

**Instead:** Catch only expected availability/budget exceptions and serialize an explicit error category.

### Application Logging Ownership

**Do not:** Clear handlers or attach anonymous library handlers.

**Why:** Handler choice belongs to the host application and clearing handlers destroys unrelated configuration.

**Instead:** Use namespaced loggers, optional `NullHandler`, and an explicitly marked reversible convenience handler.

## Scaling Considerations

| Graph scale | Runtime dispatch | Snapshot/validation | Visualization |
|-------------|------------------|---------------------|---------------|
| Up to 100 states | Direct O(1) lookup; full diagnostics acceptable | Default budget, dense matrix usually safe | Full Mermaid/PlantUML/JSON |
| 100–10,000 states | Same runtime architecture; watch callback/history costs | Sparse adjacency, SCC/DP, matrix only under cell budget | Prefer JSON/streamed topology; diagrams may be impractical |
| Above 10,000 states | Dispatch remains O(1), but construction/memory dominate | Require explicit raised budgets and memory planning | Reject full diagram by default or require explicit override |
| Adversarial/config-driven graph | Validate endpoint/count limits before analysis | Treat budget exhaustion as expected result, never hang | Escape all labels; never interpret them as syntax |

## Sources

### Primary codebase evidence (HIGH)

- `src/fast_fsm/core.py` — canonical runtime, duplicated sync/async dispatch, callback ordering, builder, history, logging, and compilation-sensitive classes.
- `src/fast_fsm/validation.py` — current private-table coupling, current-state initial identity, exponential longest path, dense matrices, and name-keyed comparisons.
- `src/fast_fsm/visualization.py` — identifier sanitization, raw PlantUML output, duplicated cycle traversal, and broad quality exception handling.
- `.planning/codebase/CONCERNS.md` — reproduced defects and hardening scope dated 2026-08-29.
- `.planning/codebase/ARCHITECTURE.md` — mapped current boundaries and data flow dated 2026-08-29.
- `.planning/PROJECT.md` — v0.3.0 constraints and selected safe-default posture.

### Official documentation (MEDIUM, verified primary documentation)

- [Python 3.10 threading locks](https://docs.python.org/3.10/library/threading.html) — primitive lock non-blocking behavior and `RLock` reentrancy semantics.
- [Python asyncio synchronization primitives](https://docs.python.org/3/library/asyncio-sync.html) — task-oriented, non-thread-safe async locks and fair waiting semantics.
- [Python Logging HOWTO: configuring logging for a library](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library) — namespaced loggers, `NullHandler`, and application ownership of handlers.
- [Python 3.10 `collections.deque`](https://docs.python.org/3.10/library/collections.html#collections.deque) — bounded eviction and approximately O(1) endpoint operations.
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html) — native-class attribute/inheritance constraints and interpreted-subclass opt-in.

## Open Verification Questions

- Measure the cost of a non-blocking primitive lock and owner-token creation in both compiled and pure-Python `trigger()` paths. Architecture confidence is MEDIUM until both remain above 200,000 ops/sec.
- Confirm mypyc accepts the selected lock/owner slot annotations and immutable snapshot value implementation on Python 3.10–3.13 across the supported OS matrix.
- Validate the exact migration surface of `sync_callback_policy="error"` against examples and existing async tests; retain the safe default but document explicit opt-ins.
- Choose concrete exception class names and whether diagnostic budgets become public API or remain optional keyword dictionaries during requirements planning.

---
*Architecture research for Fast FSM v0.3.0 Reliability & Runtime Hardening.*
