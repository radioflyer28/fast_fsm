# Phase 18: Safe Ownership & Concurrency - Pattern Map

**Mapped:** 2026-09-01  
**Files analyzed:** 17 planned/modified files  
**Analogs found:** 17 / 17 (ownership itself has no existing implementation analog)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | runtime/controller, model, synchronization utility | request-response + state mutation | existing `StateMachine`/`AsyncStateMachine` lifecycle seams in same file | exact structural seam; no ownership analog |
| `tests/test_ownership_concurrency.py` | integration test | event-driven concurrency | `tests/test_transition_lifecycle.py` | role/data-flow match |
| `tests/test_transition_lifecycle.py` | integration regression test | request-response + event-driven cancellation | existing lifecycle/cancellation matrix in same file | exact |
| `tests/test_advanced_functionality.py` | integration regression test | CRUD/control mutation | existing force/reset/restore and clone tests in same file | exact |
| `tests/test_listeners.py` | integration regression test | event-driven observer registration | existing listener protocol tests in same file | exact |
| `tests/test_builder.py` | integration regression test | batch/transform then publication | existing builder staging/build tests in same file | exact |
| `tests/test_async.py` | async integration regression test | request-response + event-driven | existing async machine/callback tests in same file | exact |
| `tests/test_boundary_negative.py` | negative/invariant test | request-response failure | existing invalid-input and `safe_trigger()` tests in same file | exact |
| `tests/test_mypyc_guard.py` | structural/configuration test | static transform/compile verification | AST and subprocess guards in same file | role match |
| `tests/test_performance_benchmarks.py` | performance test | batch measurement | existing throughput gates in same file | exact |
| `tools/phase16_isolated_verify.py` | verification harness | batch/file-I/O + subprocess | existing Phase 17 fresh-origin suite branch | exact |
| `README.md` | user documentation | request-response usage contract | existing lifecycle/async sections | role match |
| `docs/QUICK_START.md` | user documentation | request-response usage contract | existing async and lifecycle guidance | role match |
| `docs/dev/architecture.md` | architecture documentation | transform/ownership model | existing class/lifecycle/compilation sections | role match |
| `docs/dev/testing.md` | developer/test documentation | batch verification | existing Phase 17 source-tree gate section | role match |
| `.specify/memory/spr-core-api.md` | living API memory | transform/contract summary | existing lifecycle and clone bullets | role match |
| `.specify/decisions/ADR-005-safe-ownership-concurrency.md` | ADR/configuration record | decision/contract | `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` | exact documentation convention |
| `.planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md` | evidence record | batch measurement/reporting | Phase 17 performance evidence artifact | exact evidence convention |

## Pattern Assignments

### `src/fast_fsm/core.py` (runtime/model/synchronization, request-response + mutation)

**Analog:** Existing `StateMachine` and `AsyncStateMachine` implementation in `src/fast_fsm/core.py`; ownership has no pre-existing implementation to copy.

**Imports and slots pattern** (lines 15-43, 510-588, 2721-2744):

```python
import logging
import time
from collections import deque
from typing import Optional, Dict, Any, Callable, List, Sequence, Union, Tuple, cast, overload
from dataclasses import dataclass, field
import asyncio
from mypy_extensions import mypyc_attr

class StateMachine:
    __slots__ = (
        "_name", "_initial_state", "_current_state", "_states",
        "_transitions", "_graph_version", "_logger",
        "_before_listeners", "_on_exit_listeners", "_on_enter_listeners",
        "_after_listeners", "_on_failed_callbacks", "_trigger_callbacks",
        "_state_exit_callbacks", "_state_enter_callbacks", "_history",
        "_history_max",
    )

    def __init__(...):
        self._states: Dict[str, State] = {}
        self._transitions: Dict[str, Dict[str, TransitionEntry]] = {}
        self._before_listeners: list = []
        self._on_failed_callbacks: list = []
        self._history: Optional[deque[TransitionRecord]] = None
```

Add ownership state as private slots initialized in `StateMachine.__init__`; preserve the one-unit mypyc boundary and avoid module-global locks/registries. `AsyncStateMachine.__slots__` currently contains only its async callback registries (lines 2733-2744), so subclass-only async metadata should follow that split while sync ownership stays in the base slot layout.

**Current shared-marker seam to replace** (lines 46-132):

```python
_prepared_declarative_guards: Dict[Optional[int], Tuple[int, str, int]] = {}

def _prepared_guard_scope_key() -> Optional[int]:
    try:
        task = asyncio.current_task()
    except RuntimeError:
        return None
    return id(task) if task is not None else None

scope_key = _prepared_guard_scope_key()
previous = _prepared_declarative_guards.get(scope_key)
_prepared_declarative_guards[scope_key] = (id(source_state), trigger, id(to_state))
...
_prepared_declarative_guards[scope_key] = previous
```

Replace the dictionary with a module-level `ContextVar` using explicit `set()`/`reset(token)` for Python 3.10 compatibility, and include machine identity in the marker. Preserve the existing restoration shape for nested declarative policy calls; do not use task IDs or a process-global mutable map as the ownership source of truth.

**Preparation and guard boundary** (lines 1507-1569):

```python
prepared = self._prepare_transition(trigger, args, kwargs)
if isinstance(prepared, TransitionResult):
    return False  # can_trigger; trigger finalizes the failure
entry = prepared.entry
if entry.condition:
    if not self._evaluate_condition_sync(
        entry.condition, prepared.args, prepared.condition_kwargs
    ):
        return False
```

Ownership admission must precede `_prepare_transition()` for every guarded write, so reentry cannot evaluate guards, mutate the declarative marker, or create a result. Keep `can_trigger()` read-only per D-15 unless the plan explicitly treats async loop admission as its separate first-control boundary.

**Canonical topology plan / all-or-nothing mutation** (lines 1094-1128, 1168-1181, 1218-1260):

```python
final_entries: Dict[Tuple[str, str], Tuple[State, Optional[Condition]]] = {}
for plan in plans:
    for source in plan.sources:
        final_entries[(source.name, plan.trigger)] = (plan.target, plan.condition)
...
if not changed:
    return
for (source_name, trigger), (target, guard) in final_entries.items():
    self._transitions[source_name][trigger] = TransitionEntry(target, guard)
self._graph_version += 1

prepared = []
for entry in transitions:
    ...
    prepared.append(self._normalize_transition_request(...))
self._commit_transition_plan(tuple(prepared))
```

Wrap validation and this single commit for `add_state`, `add_transition`, `add_transitions`, `add_bidirectional_transition`, and `add_emergency_transition` in one ownership envelope. Do not acquire separately for each leg or batch entry; preserve preflight-before-mutation and one graph-version advance.

**Direct-control delegation seam** (lines 1901-1980):

```python
def force_state(self, state_name: str) -> None:
    if state_name not in self._states:
        raise KeyError(...)
    to_state = self._states[state_name]
    self._execute_control_transition(to_state, "__force__")

def reset(self) -> None:
    self.force_state(self._initial_state.name)

def restore(self, snapshot: Dict[str, Any]) -> None:
    ...
    self.force_state(state_name)
```

Create one private already-owned control body. Public `reset()`/`restore()` must not call an acquiring public `force_state()` or produce false reentry. Preserve direct-control best-effort callback behavior and synthetic `"__force__"` trigger.

**Commit and failure-finalizer seams** (lines 2053-2138):

```python
def _commit_transition(self, old_state, to_state, trigger) -> None:
    record = None
    history = self._history
    if history is not None:
        record = TransitionRecord(old_state.name, trigger, to_state.name, time.monotonic())
    if record is not None:
        history.append(record)
    self._current_state = to_state

def _finalize_failure(self, result, kwargs):
    observers = tuple(self._on_failed_callbacks)
    for observer_index, observer in enumerate(observers):
        try:
            observer(result.trigger, result.from_state, result.error, **kwargs)
        except BaseException as observer_error:
            self._logger.warning(...)
    return result
```

The ownership release `finally` surrounds the entire public operation, including `_finalize_failure()` and result construction. Keep commit as the no-user-code state/history boundary and keep observer iteration as a tuple snapshot. Ownership `RuntimeError` is a precondition, not a lifecycle result; it must be raised before `trigger()` preparation/finalization and outside `safe_trigger()`’s broad catch.

**Ordinary sync trigger and safe-trigger seams** (lines 2458-2659):

```python
prepared = self._prepare_transition(trigger, args, kwargs)
...
result = self._execute_transition(...)
if not result.success:
    return self._finalize_failure(result, kwargs)
return result

try:
    return self.trigger(trigger, *args, **kwargs)
except Exception as e:
    error_msg = f"Exception during trigger '{trigger}': {e}"
    return TransitionResult(False, from_state=self.current_state_name,
                            trigger=trigger, error=error_msg)
```

Split public ownership admission from a private trigger body. `safe_trigger()` must admit outside its catch and call the private body inside the catch so ordinary escaped exceptions retain compatibility while ownership errors escape. Error strings for ownership may contain only stable operation/category metadata; never interpolate trigger arguments, kwargs, payloads, causes, or arbitrary exception text.

**Async paired runner and cancellation seam** (lines 2816-3031, 3083-3238):

```python
async def _execute_transition_async(..., lifecycle_stage, committed, **kwargs):
    lifecycle_stage[0] = _LIFECYCLE_STAGE_BEFORE_TRANSITION
    for fn in self._before_listeners:
        try:
            fn(old_state, to_state, trigger, **kwargs)
        except Exception as cause:
            return self._build_lifecycle_failure(...)
    ...
    await fn(...)
    self._commit_transition(old_state, to_state, trigger)
    committed[0] = True

async def trigger_async(...):
    lifecycle_stage = [_LIFECYCLE_STAGE_GUARD]
    committed = [False]
    try:
        ...
        result = await self._execute_transition_async(...)
        if not result.success:
            return self._finalize_failure(result, kwargs)
        return result
    except asyncio.CancelledError as cancellation:
        cancelled_result = self._build_failure_result(...)
        self._finalize_failure(cancelled_result, kwargs)
        raise
```

Use the existing paired direct runner rather than wrapping a completed sync run. Bind/check loop and causal root before async lock acquisition; use `async with` for the per-machine lock, install task/root ownership only after acquisition, and clear/reset in one inner `finally`. Cancellation while waiting must never install ownership; cancellation while owning must preserve Phase 17 stage/commit/finalizer behavior and release the lock.

**No safe existing analog:** There is currently no per-instance lock, owner marker, permanent async loop binding, or causal `ContextVar`. The implementation must introduce these private seams and prove them with structural tests because no current code can be copied for correctness.

---

### `tests/test_ownership_concurrency.py` (integration, event-driven concurrency)

**Analog:** `tests/test_transition_lifecycle.py` lines 53-69, 742-806, and 852-945.

Use real `StateMachine`/`AsyncStateMachine` objects and local slot-safe helper classes, matching the lifecycle test style:

```python
class _BlockingAsyncCondition(AsyncCondition):
    def __init__(self, started: asyncio.Event, release: asyncio.Event) -> None:
        super().__init__("blocking-guard", "lifecycle cancellation guard")
        self._started = started
        self._release = release

    async def check_async(self, **kwargs: object) -> bool:
        self._started.set()
        await self._release.wait()
        return True
```

Use `threading.Barrier`/`threading.Event` for sync contenders and `asyncio.Event` plus explicit `create_task()` handshakes for async contenders. Do not use sleeps as evidence. Cover direct and callback reentry for each write family, two independent sync threads, independent machines, same-loop lock waiting with a heartbeat, causal child-task reentry, cross-loop rejection, all release paths, redacted messages, and pure/compiled origins. Watchdog timeouts may fail a hang but are not ordering proof.

**Pattern assignment:** Keep parameterized scenario tables deterministic and assert exact state/history/event cardinality. For callback reentry, catch the `RuntimeError` deliberately when testing outer continuation; separately assert uncaught nested errors are classified by the outer Phase 17 callback stage.

---

### `tests/test_transition_lifecycle.py` (integration, lifecycle/cancellation)

**Analog:** Existing lifecycle matrices lines 115-158, 161-220, 642-739, and 842-1019.

Preserve the dataclass probe inventory and stage catalog. Reuse the event-coordinated cancellation fixture (lines 860-929) and exact assertions that state/history reflect pre/post commit (lines 931-945). Update observer-registration expectations where a registration inside an owned callback now raises; add a separate between-operations registration check to retain tuple-snapshot coverage. Assert nested ownership errors are classified at the callback’s normal stage, not as a new lifecycle stage.

---

### `tests/test_advanced_functionality.py` (integration, CRUD/control mutation)

**Analog:** Existing force/reset/restore and clone sections lines 586-958 and 1024-1090.

Follow the real-machine setup and exact state/callback assertions:

```python
fsm = StateMachine(source, name="...")
fsm.add_state(destination)
fsm.add_transition("advance", "source", "destination")
fsm.force_state("destination")
assert fsm.current_state.name == "destination"
```

Extend the control/clone coverage to assert ownership of `force_state`, `reset`, `restore`, independent clone lock/owner state, and callback-originated registration rejection. Preserve the direct-control best-effort callback contract and current callback order.

---

### `tests/test_listeners.py` (integration, event-driven registration)

**Analog:** Listener helper/setup and protocol tests lines 1-35 and 90-190; failure observer snapshot tests in `test_transition_lifecycle.py:356-376` and `980-1019`.

Use `_make_fsm()` (`StateMachine.quick_build(...)`, lines 19-26) and real duck-typed listener objects. Assert every listener/callback registrar is covered by the same ownership policy, including `add_listener`, `on_enter`, `on_exit`, `after_transition`, `on_failed`, `on_trigger`, `on_enter_async`, and `on_exit_async`. Preserve registration order and defensive snapshot iteration for registrations made between operations; registrations attempted during ownership must fail.

---

### `tests/test_builder.py` (integration, staged batch then publication)

**Analog:** Builder imports and fluent callback/async tests lines 12-32 and 1350-1555; async callback publication tests lines 2019-2050.

Keep builder tests staged and real, with explicit `FSMBuilder(...).add_state(...).add_transition(...).build()` chains. Builder mutators run before publication and retain existing freeze/error semantics. After `build()`, assert machine ownership state is independent per build/clone and that builder staging does not expose a shared lock. Do not move ownership into builder staging or alter async auto-detection.

---

### `tests/test_async.py` (async integration, request-response)

**Analog:** Async imports/helpers lines 8-45, callback behavior lines 621-872, and clone independence lines 900-938.

Use pytest-asyncio’s configured `asyncio_mode = "auto"` and `AsyncStateMachine`/`AsyncCondition` real objects. Preserve synchronous callback inline behavior and same-slot async callback assertions. Add loop-thread identity checks, same-loop serialization, cross-loop/closed-loop rejection, inherited sync mutator admission, callback-created causal child tasks, and cancellation before/after commit. Reuse clone callback-copy setup while asserting async loop/lock/root metadata is not shared.

---

### `tests/test_boundary_negative.py` (negative/invariant, request-response)

**Analog:** Invalid operation fixtures lines 1-35 and safe-trigger tests lines 243-280, 400-425.

Keep `pytest.raises` for operational misuse and `TransitionResult` assertions for ordinary failures:

```python
result = fsm.safe_trigger("go")
assert result.success is False
```

Add the explicit distinction that ownership `RuntimeError` escapes `safe_trigger()` while normal transition/condition exceptions still become failed results. Use unique secret sentinels and assert they are absent from ownership exception text/logs/repr.

---

### `tests/test_mypyc_guard.py` (structural/compile, static transform)

**Analog:** AST slot/compilation guards lines 1-23, 306-420, and setup/harness checks lines 451-490.

Parse `core.py` with `ast`, as existing tests do, and assert required ownership names are in `StateMachine`/`AsyncStateMachine` slots; `setup.py` still passes exactly `['src/fast_fsm/core.py']` to one `mypycify()` call. Add source-structure checks for one public-entry/private-body path, no process-global lock/registry, ContextVar marker usage, and no executor/to_thread callback path. Keep subprocess compilation checks with explicit `FAST_FSM_BUILD_MODE` and asserted module origins.

---

### `tests/test_performance_benchmarks.py` (performance, batch measurement)

**Analog:** Existing slow throughput gates lines 378-439 and 440-474.

Follow the warm-up → `gc.collect()` → `time.perf_counter()` → fixed iteration batch → module-origin detection → mode-specific floor pattern. Add separate uncontended pure/compiled ownership overhead observations, retaining the compiled `trigger()` floor of 200,000 operations/second. Keep benchmark claims environment-labeled and use broad thresholds for non-floor overhead checks; do not add sleeps or assert a universal exact rate.

---

### `tools/phase16_isolated_verify.py` (verification harness, batch/file-I/O)

**Analog:** Phase 17 inventory and suite branch lines 55-81 and 885-943; isolation primitives lines 181-237.

Extend the existing `PHASE17_INVENTORY` into an explicit Phase 18 inventory, retaining runtime/tests/docs/SPR/ADR/evidence overlays. Preserve the safe sequence:

```python
_export_head(source_tree, env)
overlaid = _overlay(includes, source_tree)
_run(("uv", "sync", "--locked", "--all-groups"), ...)
if build_mode == "compiled":
    _run(("uv", "run", "python", "setup.py", "build_ext", "--inplace"), ...)
_assert_origin(source_tree, build_mode, env)
```

Add `phase18` parser choice and run the ownership semantic matrix in both pure and compiled fresh trees, then compiled performance, slots, type/docs/release gates as specified. Keep explicit overlays and no native-shadow deletion.

---

### `README.md`, `docs/QUICK_START.md` (user docs, request-response)

**Analogs:** README lifecycle/async sections lines 300-380; Quick Start async/cancellation section lines 509-516.

Copy the existing contract-first prose style: describe observed lifecycle order, commit/history truth, callback signatures, and cancellation without promising hidden behavior. Add concise safe-default ownership guidance: sync writes serialize per instance; reentry raises stable `RuntimeError`; async control binds permanently to the first loop, same-loop tasks await, foreign loops fail; synchronous callbacks remain inline and async callbacks are awaited at matching slots; `safe_trigger()` does not swallow ownership preconditions. Avoid payload-bearing examples in ownership error messages.

---

### `docs/dev/architecture.md` (architecture documentation, transform/model)

**Analog:** Class/data-structure sections lines 29-99, lifecycle section lines 161-214, and compilation constraints lines 216-258.

Add an ownership subsection beside the lifecycle model. Use a small sync/async flow diagram or table showing admission before preparation, per-instance primitive, owner cleanup, permanent loop binding, causal root, and inherited sync-mutator rules. State that Phase 19 owns diagnostic snapshots and Phase 20 owns installed-artifact parity. Preserve the strict import DAG, slots policy, one-unit mypyc boundary, and explicit inline callback contract.

---

### `docs/dev/testing.md` (test documentation, batch verification)

**Analog:** Quick reference/test-file map lines 1-53 and Phase 17 fresh-origin gate lines 171-219.

Extend the Phase 17 gate section with Phase 18 commands and file map. Preserve the task-mode explicit `--include` pattern and fresh temporary checkout/origin assertion. Document deterministic barriers/events, no sleeps, isolated loop threads, same-loop heartbeat, causal child-task test, pure/compiled semantic runs, compiled throughput floor, slots, mypy, docs, doctests, and baseline freshness.

---

### `.specify/memory/spr-core-api.md` (living API memory, contract summary)

**Analog:** Existing bullet contract lines 5-48, especially lifecycle/history/async/clone bullets.

Append or revise concise bullets (do not rewrite unrelated history): per-instance sync ownership wraps every public write; same-owner reentry and unsupported cross-loop use raise redacted `RuntimeError`; independent sync threads and same-loop async tasks serialize; async first control binds permanently; causal `ContextVar` catches inherited child-task reentry; sync callbacks stay inline; async callbacks remain same-slot awaited; ownership releases across ordinary exceptions, `BaseException`, and cancellation; clones/factories do not share ownership state. Keep Phase 19/20 boundaries explicit.

---

### `.specify/decisions/ADR-005-safe-ownership-concurrency.md` (ADR, decision record)

**Analog:** `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` lines 1-63 and 65-121.

Follow the accepted ADR structure: status/date/deciders, context, numbered decision list, considered alternatives with rejection rationale, consequences, and deferred follow-up. Record stable ownership/reentry/loop/callback contracts and why `RLock`, global locks, blocking thread locks across `await`, task-only identity, automatic callback offload, and cross-loop rebinding are rejected. Keep ADR append-only; do not edit ADR-004.

---

### `.planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md` (evidence, batch measurement)

**Analog:** Phase 17 performance evidence artifact and existing benchmark style in `tests/test_performance_benchmarks.py`.

Use environment-labeled Markdown evidence: date/commit, platform/interpreter/compiler, pure vs compiled module origin, commands, semantic test counts, uncontended ownership overhead, compiled trigger throughput, slots/type/docs gates, and baseline result. Explicitly distinguish observations from durable policy; the only fixed performance floor is compiled `trigger() >= 200,000 ops/sec`.

## Shared Patterns

### Ownership Envelope

**Source:** `src/fast_fsm/core.py:2458-2659`, `src/fast_fsm/core.py:3083-3238`, and topology/control methods at `896-1260`/`1901-1980`.

```text
pre-check owner/loop/root
  -> acquire per-instance primitive
  -> install owner metadata
  -> validation/preparation/guards
  -> lifecycle callbacks + commit + finalizer/result
  -> finally clear owner metadata and release primitive
```

Apply exactly once per public write. Public-to-public delegations route to private already-owned bodies.

### Commit and Failure Truth

**Source:** `src/fast_fsm/core.py:2053-2138`, `tests/test_transition_lifecycle.py:379-447`, `842-945`.

State/history are changed only at `_commit_transition()`; ordinary lifecycle errors remain staged `TransitionResult`s and cancellation is finalized then bare re-raised. Ownership errors are outside this result machinery.

### Observer Snapshot

**Source:** `src/fast_fsm/core.py:2121-2138`.

Use `observers = tuple(self._on_failed_callbacks)` before iteration. Phase 18 adds registration admission, but does not remove the defensive snapshot for registrations made between completed operations.

### Async Same-Slot Callback Contract

**Source:** `src/fast_fsm/core.py:2826-3031`, `tests/test_transition_lifecycle.py:743-806`, `README.md:366-368`.

Synchronous callbacks execute inline on the event-loop thread; async callbacks are awaited at source-exit/destination-enter slots. Never introduce implicit executor/`to_thread` work.

### Slots and Single Compilation Unit

**Source:** `src/fast_fsm/core.py:516-534`, `src/fast_fsm/core.py:2733-2744`, `tests/test_mypyc_guard.py:306-420`, `setup.py:16-39`.

All hot-path state goes into slots; `core.py` remains the sole mypyc input and `conditions.py` remains interpreted. Use AST guards and fresh pure/native origins to catch accidental layout or compilation drift.

### Fresh-Origin Verification

**Source:** `tools/phase16_isolated_verify.py:181-237, 885-943` and `docs/dev/testing.md:171-219`.

Export committed `HEAD`, overlay only explicit Phase 18 files, choose build mode before setup, reject native shadows in pure mode, build compiled mode fresh, assert `fast_fsm.core.__file__`, then run semantics. Do not import the developer checkout as evidence.

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| Per-instance synchronous owner and lock | runtime synchronization | request-response | No existing locking or ownership primitive exists in `core.py`. |
| Permanent async loop binding and asyncio lock | runtime synchronization | event-driven request-response | Existing async machine has no loop identity or lock metadata. |
| Causal child-task reentry marker | runtime context utility | event-driven | Existing declarative marker is a task-keyed global dictionary and is not safe for this contract. |
| Cross-loop/inherited sync-mutator policy | runtime integration | mixed thread/async | No current mixed-mode admission seam exists. |
| Ownership-specific deterministic test fixture | test utility | event-driven | Existing lifecycle fixtures coordinate cancellation but do not contend on machine ownership. |

Planner should use the research recommendations and locked decisions for these new seams, with the existing lifecycle/commit patterns above as the surrounding implementation boundary.

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`; `tests/` lifecycle, async, control, listener, builder, boundary, mypyc, and performance modules; `tools/phase16_isolated_verify.py`; `README.md`; `docs/`; `.specify/memory/`; `.specify/decisions/`.  
**Files scanned:** 17 primary analog files plus `setup.py`, `pyproject.toml`, and Phase 18 context/research/validation.  
**Pattern extraction date:** 2026-09-01
