# Phase 16: Canonical Graph & Dispatch Invariants - Pattern Map

**Mapped:** 2026-08-29  
**Files analyzed:** 10 implementation/test files, plus release-gate analogs  
**Analogs found:** 10 / 10 planned files

Phase 16 is a convergence refactor around the existing dictionary-backed runtime. Keep `StateMachine._states` and `_transitions` as the O(1) authority, put private orchestration seams in the compiled `core.py` unit, and keep condition bases/wrappers interpreted and subclassable. The new graph snapshot is a tool-facing view, not a replacement for `snapshot()`/`to_dict()`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | service/runtime | CRUD topology, request-response dispatch, event-driven callbacks, bounded history | Existing `StateMachine`, `AsyncStateMachine`, `FSMBuilder`, and declarative classes in the same file | exact role and boundary |
| `src/fast_fsm/conditions.py` | model/utility | request-response guard evaluation, nested wrapper traversal | `Condition`, `FuncCondition`, `NegatedCondition`, `AsyncCondition` | exact role; wrapper evaluation needs extension |
| `src/fast_fsm/condition_templates.py` | model/utility | request-response composite guard evaluation | `AndCondition`, `OrCondition`, `NotCondition` | exact role and data flow |
| `tests/test_graph_invariants.py` | test | CRUD/state-sequence assertions over topology/version/snapshot | `tests/test_basic_functionality.py` construction/error tests and `tests/test_advanced_functionality.py` snapshot tests | new focused module; strong test-style analogs |
| `tests/test_builder.py` | test | construction transaction, request-response builder/declarative behavior | Existing builder and declarative test classes | exact |
| `tests/test_async.py` | test | asynchronous request-response guard/dispatch and callback behavior | Existing `AsyncStateMachine` tests | exact |
| `tests/test_safety_kwargs.py` | test | request-response guard context and failure isolation | Existing `MockCondition`/sanitization tests | exact |
| `tests/test_advanced_functionality.py` | test | bounded FIFO history and topology factory regression | `TestTransitionHistory`, `TestToDict`, and factory tests | exact |
| `tests/test_mypyc_guard.py` | test/utility | batch/static transform of `core.py` AST | Existing recursive subclassability AST guard | exact structural analog |
| `tests/test_performance_benchmarks.py` | test | batch/measurement of trigger and history hot paths | Existing compiled/pure throughput gates | exact performance analog |

The following are validation-only analogs, not planned implementation edits: `Taskfile.yml:281-291` (`release-gate` ordering), `setup.py:16-39` (only `core.py` passed to mypyc), `tools/release_evidence.py:116-130` (non-destructive source-origin preflight), and `evidence/release-baseline.json:39-73` (performance/quality reference).

## Pattern Assignments

### `src/fast_fsm/core.py` (service/runtime; CRUD topology + request-response dispatch)

**Analog:** the current `StateMachine`, `AsyncStateMachine`, declarative state classes, and `FSMBuilder` in this file. This is the only implementation unit that owns the runtime graph and is the only source passed to mypyc.

**Imports and compiled-boundary pattern** (`core.py:15-21`):

```python
import logging
import time
from typing import Optional, Dict, Any, Callable, List, Union, Tuple, overload
from dataclasses import dataclass
import asyncio
from mypy_extensions import mypyc_attr
from .conditions import Condition, FuncCondition, AsyncCondition, NegatedCondition
```

Keep new graph records and dispatch orchestration here. Do not move interpreted condition classes into this unit or add a runtime dependency. `setup.py:16-39` proves the compilation boundary, and `State`/declarative classes use `@mypyc_attr(allow_interpreted_subclasses=True)` (`core.py:165-166`, `236-237`, `1988-1989`, `2162-2163`).

**Slots/runtime-state pattern** (`core.py:267-341`):

```python
__slots__ = (
    "_name", "_initial_state", "_current_state", "_states", "_transitions",
    "_logger", "_before_listeners", "_on_exit_listeners", "_on_enter_listeners",
    "_after_listeners", "_on_failed_callbacks", "_trigger_callbacks",
    "_state_exit_callbacks", "_state_enter_callbacks", "_history", "_history_max",
)

self._initial_state = initial_state
self._current_state = initial_state
self._states: Dict[str, State] = {initial_state.name: initial_state}
self._transitions: Dict[str, Dict[str, TransitionEntry]] = {}
self._register_state(initial_state)
```

Copy this separation for `_graph_version` and any private snapshot state: declared initial state must remain independent from current state. New hot-path runtime records must be tuple-shaped or slot-protected and must pass the recursive slots audit.

**Current registration and transition mutation (anti-pattern to replace)** (`core.py:634-751`):

```python
def _register_state(self, state: State) -> None:
    self._states[state.name] = state
    if state.name not in self._transitions:
        self._transitions[state.name] = {}

# ...
for from_state_name in from_names:
    if from_state_name not in self._transitions:
        self._transitions[from_state_name] = {}
    self._transitions[from_state_name][trigger] = TransitionEntry(
        to_state_obj, normalized_condition
    )
```

The replacement should preserve the dictionary shape but split each mutation into: materialize all sources, resolve string/object endpoints to registry identities, validate condition/`unless`/duplicates, compare for a topology change, then commit all entries and advance `_graph_version` once. A foreign same-name `State` must fail identity comparison; ordinary `add_transition()` must not create registry entries or source buckets. `add_transitions()` currently delegates entry-by-entry (`core.py:753-795`), so planner tasks must decide whether its public operation is wrapped in a complete transaction.

**Convenience construction pattern** (`core.py:343-453`, `455-567`): `from_states()`/`quick_build()` collect or create the complete state set, instantiate the machine, register states, then add transitions. Preserve this convenience behavior while making the ordinary transition path strict. `from_dict()` also validates required config fields before constructing (`core.py:536-564`); use its fail-before-construction style for invalid declarative topology.

**Shared lookup and guard preparation analogs** (`core.py:1110-1181`, `1317-1358`):

```python
current_name = self._current_state.name
if current_name not in self._transitions:
    return False
if trigger not in self._transitions[current_name]:
    return False
entry = self._transitions[current_name][trigger]

safe_kwargs = self._sanitize_condition_kwargs(kwargs)
if not entry.condition.check(*args, **safe_kwargs):
    return False
```

```python
resolved = self._resolve_trigger(trigger, *args, **kwargs)
if isinstance(resolved, TransitionResult):
    return resolved
return self._transitions[current_name][trigger], current_name
```

Use `_resolve_trigger()` as the lookup analog, but make the prepared result carry the selected entry, canonical source/target, unchanged positional args, and one fresh sanitized mapping. `can_trigger()` and `trigger()` should call the same preparation seam; async variants should differ only in evaluator strategy. Filter keys before counting the retained cap (the current method slices raw input first at `core.py:1153-1160`, which is the bug to remove). Do not add raw payload values to logs; current ultra-verbose logging at `core.py:1331-1343` is a specific place to review.

**Transition execution/history analog** (`core.py:1360-1500`):

```python
old_state = self._current_state
...
self._current_state = to_state
...
if self._history is not None:
    if len(self._history) >= self._history_max:
        del self._history[0]
    self._history.append(
        TransitionRecord(old_state.name, trigger, to_state.name, time.monotonic())
    )
```

Retain callback/listener isolation and the public `TransitionRecord` shape. Replace only internal history storage/eviction with `deque(maxlen=...)`, preserve the single `None` disabled branch, and keep `history` copy-on-read. Declarative handler ordering/failure semantics are deliberately not to be frozen here; only exactly-once successful invocation and sync/async parity belong in Phase 16.

**Sync dispatch/error pattern** (`core.py:1502-1595`): resolve first, evaluate a guard inside a `try`/`except`, return a failed `TransitionResult` and notify `_on_failed_callbacks`, then call state permission and `_execute_transition()`. Preserve this result shape and callback isolation while routing condition evaluation through the shared prepared context. State callback signatures already forward `*args, **kwargs` (`core.py:207-227`, `254-264`).

**Async dispatch analog to converge** (`core.py:1701-1954`):

```python
if isinstance(condition, AsyncCondition):
    condition_result = await condition.check_async(*args, **kwargs)
else:
    condition_result = condition.check(*args, **kwargs)
...
if hasattr(self._current_state, "can_transition_async"):
    can_proceed = await self._current_state.can_transition_async(
        trigger, to_state, *args, **kwargs
    )
```

The current async `can_trigger_async()` and `trigger_async()` duplicate lookup/evaluation and pass raw kwargs (`core.py:1792-1820`, `1822-1924`). Replace both with the shared preparation seam and a private recursive evaluator. It must recognize only existing built-in edges, await async leaves, call sync leaves, preserve And/Or short-circuit order, invert `Not`/negation, and reuse the same prepared args/kwargs through all layers.

**Declarative discovery/normalization analog** (`core.py:1988-2159`, `2219-2275`):

```python
handler_info = {
    "method": attr,
    "from_state": getattr(attr, "_fsm_from_state", None),
    "to_state": getattr(attr, "_fsm_to_state", None),
    "condition": getattr(attr, "_fsm_condition", None),
    "is_async": asyncio.iscoroutinefunction(attr),
}
self._handlers[trigger] = handler_info
```

```python
if result is None:
    result = TransitionResult(True)
elif isinstance(result, bool):
    result = TransitionResult(result)
elif not isinstance(result, TransitionResult):
    result = TransitionResult(True, error=f"Invalid return type from handler: {type(result)}")
```

Copy metadata keys and return normalization. Add one state-level resolver/invocation seam keyed by source/trigger/canonical target, and make `handle_event()`/`handle_event_async()` delegate to it. Ordinary `trigger()`/`trigger_async()` must own the single successful invocation; tests should count calls and avoid asserting Phase 17 lifecycle position or exception ordering.

**Builder transaction/freeze analog** (`core.py:2278-2686`):

```python
self._states: Dict[str, State] = {initial_state.name: initial_state}
self._transitions: List[tuple] = []
self._machine = None
```

```python
if self._machine is not None:
    return self._machine

self._machine = self._machine_type(self._initial_state, **self._machine_kwargs)
...
for state_name, cb in self._enter_callbacks:
    self._machine.on_enter(state_name, cb)
return self._machine
```

Use the staged dictionaries/lists and fluent return-`self` convention from `add_state()`/`add_transition()`/callback registration (`core.py:2392-2558`), but add one `_ensure_mutable()` at the start of every mutator, registrar, and force-mode method. `build()` must retain the early cache-return identity behavior (`core.py:2597-2600`), create a local candidate, fully wire it, and publish `_machine` only after the last successful operation. Explicit sync must fail before candidate allocation on any nested async requirement; auto detection must walk `NegatedCondition._inner`, composite condition children, declarative metadata, and queued async callbacks with identity cycle protection.

**Clone/restore analog** (`core.py:1219-1315`): public `snapshot()` is a serializable current-state record and `restore()` uses `force_state()`; do not change that schema. `clone()` shallow-copies topology dictionaries and resets current state/history. Preserve this behavior while deciding the private graph snapshot/version copy deliberately; the snapshot must use canonical object identities and deterministic sorted tuples.

### `src/fast_fsm/conditions.py` (model/utility; guard evaluation)

**Analog:** `Condition`, `FuncCondition`, `NegatedCondition`, and `AsyncCondition` (`conditions.py:15-158`). This module is intentionally uncompiled and user-subclassable.

**Base/callable pattern** (`conditions.py:23-47`, `58-92`):

```python
class Condition(ABC):
    __slots__ = ("name", "description")

    @abstractmethod
    def check(self, **kwargs: Any) -> bool:
        pass

class FuncCondition(Condition):
    __slots__ = ("func",)
    def check(self, **kwargs: Any) -> bool:
        return self.func(**kwargs)
```

Extend the abstract and wrapper signatures to accept verbatim `*args, **kwargs`, forwarding both unchanged to the callable. Keep slots and no new public wrapper protocol.

**Negation analog/edge** (`conditions.py:95-121`):

```python
__slots__ = ("_inner",)

def check(self, **kwargs: Any) -> bool:
    return not self._inner.check(**kwargs)
```

`_inner` is the exact private edge the builder detector and async evaluator must share. The current synchronous child call is unsafe for nested async leaves; the new private classifier/evaluator should preserve inversion while selecting `check_async()` only where required. `AsyncCondition.check()` currently bridges with `asyncio.run()` (`conditions.py:124-158`); avoid invoking that bridge from an active async dispatch path.

### `src/fast_fsm/condition_templates.py` (model/utility; composite guard evaluation)

**Analog:** `AndCondition`, `OrCondition`, and `NotCondition` (`condition_templates.py:118-160`).

```python
class AndCondition(Condition):
    __slots__ = ("conditions",)
    def check(self, **kwargs) -> bool:
        return all(condition.check(**kwargs) for condition in self.conditions)

class OrCondition(Condition):
    __slots__ = ("conditions",)
    def check(self, **kwargs) -> bool:
        return any(condition.check(**kwargs) for condition in self.conditions)

class NotCondition(Condition):
    __slots__ = ("condition",)
    def check(self, **kwargs) -> bool:
        return not self.condition.check(**kwargs)
```

Preserve tuple-shaped `conditions` and Python `all()`/`any()` short-circuit semantics for sync evaluation. The private traversal must recognize `.conditions` for And/Or and `.condition` for Not, while signatures forward `*args` and the one sanitized kwargs mapping. Do not expose a general child traversal API.

### `tests/test_graph_invariants.py` (test; topology/version/snapshot CRUD sequences)

**Analog:** `tests/test_basic_functionality.py:17-69` uses fresh real `State`/`StateMachine` objects and direct identity/state assertions; `tests/test_basic_functionality.py:151-200` uses `pytest.raises`-style negative behavior and confirms current state is unchanged. `tests/test_advanced_functionality.py:1446-1530` is the closest public topology serialization analog.

Use a focused module permitted by the phase context. Add a test-only graph fingerprint capturing registry identities, transition endpoint/guard identities, version, current state, and the private snapshot. For each rejection, compare the fingerprint before/after. Prefer real state/condition objects and explicit negative assertions over mocks. Cover:

- unknown string and same-name foreign object endpoints;
- duplicate sources and later-invalid multi-source requests proving zero partial writes;
- same-object re-registration no-op versus conflicting object `ValueError`;
- version increments only after successful topology changes and not after current-state movement;
- fresh deterministic immutable snapshot with canonical state/endpoint identities and declared initial state.

### `tests/test_builder.py` (test; construction transaction and declarative dispatch)

**Analog:** module-level real fixtures/classes (`test_builder.py:31-89`) and `TestFSMBuilderBasics` (`:97-155`) establish fresh builders, fluent chaining, and repeated-build identity:

```python
builder = FSMBuilder(State("s"), name="once")
fsm1 = builder.build()
fsm2 = builder.build()
assert fsm1 is fsm2
```

Extend `TestFSMBuilderAsyncDetection` (`:162-210`) and `TestFSMBuilderGaps` (`:711-776`) for nested `NegatedCondition`, And/Or/Not wrappers, cycle handling, explicit sync failure, and auto-selected async machine type. Extend `TestFSMBuilderCallbacks` (`:783-977`) to assert all mutators/registrars fail immediately after success and failed builds remain repairable. Existing declarative tests (`:217-360`) and the handler normalization cases (`:532-571`, `:649-695`) are the style analog for exactly-once sync/async integration; use counters and successful results only, leaving lifecycle order to Phase 17.

### `tests/test_async.py` (test; async guard/dispatch parity)

**Analog:** helper conditions and real two-state fixture (`test_async.py:23-108`), then paired trigger tests (`:155-210`) and `can_trigger_async` tests (`:218-244`). Keep `@pytest.mark.asyncio`, fresh `AsyncStateMachine`, and explicit call-count assertions:

```python
cond = AlwaysAsyncCondition()
fsm.add_transition("go", "idle", "running", cond)
result = await fsm.trigger_async("go")
assert result.success
assert cond.call_count == 1
```

Add wrapper recursion and positional/sanitized context cases to both `can_trigger_async()` and `trigger_async()`. Pair them with sync cases in `test_safety_kwargs.py`; assert short-circuit behavior, awaiting, caller mapping preservation, and no state mutation on `can`.

### `tests/test_safety_kwargs.py` (test; guard context)

**Analog:** `MockCondition` records a copied kwargs mapping (`test_safety_kwargs.py:15-25`) and `basic_fsm` creates real states (`:39-48`). Existing safety cases cover normal pass-through and private filtering (`:51-99`), cap behavior (`:101-118`), long-key filtering (`:120-137`), and `can_trigger()` (`:221-233`).

```python
class MockCondition(Condition):
    def check(self, **kwargs):
        self.received_kwargs = kwargs.copy()
        return self.return_value
```

Retain this recording-fixture pattern, adding positional argument identity/order and a filter-then-cap case where invalid/private keys precede later valid keys. Add the async counterpart without mocking dispatch. Assert the original caller mapping is unchanged and all four can/do sync/async paths see equivalent sanitized context.

### `tests/test_advanced_functionality.py` (test; history and factory regression)

**Analog:** `TestToDict` (`test_advanced_functionality.py:1446-1530`) proves deterministic sorted public topology output without changing `snapshot()`, while `TestTransitionHistory` (`:1532-1622`) proves opt-in, chronological records, bounds, replacement, defensive list copy, and clone behavior.

```python
fsm.enable_history(max_entries=3)
...
h = fsm.history
assert len(h) == 3

h.clear()
assert len(fsm.history) == 1
```

Extend this class with immediate `ValueError` for zero/negative capacity while preserving prior history configuration, deque FIFO eviction, reset-on-enable, and copy-on-read. Keep clone history disabled as current behavior. Do not repurpose the public serializable snapshot for the private graph snapshot.

### `tests/test_mypyc_guard.py` (test/utility; structural AST checks)

**Analog:** the existing AST-based recursive subclassability guard (`test_mypyc_guard.py:38-88`) and tests (`:96-168`) read `core.py` from disk, derive inheritance, and fail closed with actionable messages. If a new class inherits from `State`/`ABC`, preserve the decorator requirement; if a new tuple-backed record is used, add only structural assertions needed for its compiled boundary. Keep `INTERNAL_CLOSED` empty unless a class is intentionally sealed. This test is source-based and should not depend on whether a native extension currently shadows `core.py`.

### `tests/test_performance_benchmarks.py` (test; batch performance)

**Analog:** `test_trigger_min_throughput` (`test_performance_benchmarks.py:378-438`) uses a minimal two-state toggle, warmup, `gc.collect()`, a fixed batch, and runtime module-origin detection. `test_trigger_history_enabled_throughput` (`:440-492`) measures disabled/enabled ratios.

```python
for _ in range(1000):
    fsm.trigger("toggle")
gc.collect()
...
assert ops_per_sec >= floor
```

Reuse these gates for history overhead and dispatch hot-path regression. Snapshot sorting and recursive builder scanning must remain off steady-state trigger/can paths. The checked-in Phase 15 baseline is an observation (`evidence/release-baseline.json:39-56`), not a new Phase 16 policy; compare in clean pure/compiled contexts without deleting native shadows.

## Shared Patterns

### Canonical topology transaction

**Sources:** `core.py:634-751`, `core.py:753-795`, factory sequencing at `core.py:343-453`.

**Apply to:** `StateMachine._register_state()`, `add_state()`, `add_transition()`, `add_transitions()`, bidirectional/emergency helpers, and constructor/clone paths.

```text
materialize complete request
  -> resolve every endpoint to exact registry object
  -> validate condition, unless, duplicate sources, and conflicts
  -> commit dictionaries in one short section
  -> increment graph version iff topology changed
```

No rejected request may create source buckets, replace objects, change current state, or advance version.

### One prepared guard context

**Sources:** existing sync sanitizer `core.py:1136-1181`; sync lookup `core.py:1110-1134`; async duplicates `core.py:1792-1820`, `1822-1892`.

**Apply to:** `can_trigger`, `trigger`, `can_trigger_async`, `trigger_async`, and every supported wrapper layer.

The sanitizer must copy insertion order, skip non-string/private/overlong keys, then stop after 50 retained keys. Positional args pass unchanged. The prepared kwargs object is reused through wrapper recursion and never mutates caller data.

### Declarative handler normalization and isolation

**Sources:** metadata discovery `core.py:2016-2042`; sync handler normalization `core.py:2096-2159`; async normalization `core.py:2219-2275`.

**Apply to:** ordinary sync/async dispatch and compatibility helpers. Resolve by trigger plus canonical from/to metadata, invoke through one seam exactly once, and preserve `None`/bool/`TransitionResult` normalization. Do not make Phase 16 tests encode pre/post-commit or callback-failure ordering.

### Builder publish-on-success

**Sources:** staging/mutators `core.py:2392-2558`; force methods `core.py:2560-2595`; current build `core.py:2597-2668`.

**Apply to:** every builder mutator, force mode, callback registrar, async preflight, and `build()`. A successful cache is both the freeze marker and idempotent result. A failed build leaves staging mutable and `_machine` unset.

### History public boundary

**Sources:** storage/append `core.py:603-632`, `1488-1496`; tests `test_advanced_functionality.py:1542-1622`; performance ratio `test_performance_benchmarks.py:440-492`.

**Apply to:** sync/async commit paths, `enable_history`, `disable_history`, clone, and `history`. Use `None` for disabled, `deque(maxlen=capacity)` for enabled, and `list(...)` at the public boundary.

### Pure/compiled verification

**Sources:** `setup.py:16-39`, `Taskfile.yml:281-291`, `tools/release_evidence.py:116-130`, `tests/test_mypyc_guard.py:96-168`, `evidence/release-baseline.json:39-73`.

**Apply to:** final Phase 16 verification. Run the blocking mypyc/typecheck and structural tests, establish source origin before imports, then run targeted tests and clean pure/compiled gates. Native `.so` shadows in the developer checkout are legitimate artifacts and must not be removed implicitly.

## No Analog Found

No planned Phase 16 file lacks a usable role/data-flow analog. The only genuinely new shape is the private immutable graph snapshot and its focused contract module; use the tuple-backed record recommendation in `16-RESEARCH.md`, prove it under the pinned mypyc toolchain, and keep canonical `State`/`Condition` references identity-bearing rather than deep-copying them.

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`, `src/fast_fsm/condition_templates.py`, `tests/`, `tools/release_evidence.py`, `Taskfile.yml`, `setup.py`, and `evidence/release-baseline.json`  
**Files scanned:** 10 planned implementation/test files plus 4 validation-only files  
**Pattern extraction date:** 2026-08-29
