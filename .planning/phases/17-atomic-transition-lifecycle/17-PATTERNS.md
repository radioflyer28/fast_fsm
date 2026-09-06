# Phase 17: Atomic Transition Lifecycle - Pattern Map

**Mapped:** 2026-09-01  
**Files analyzed:** 17 likely new/modified files  
**Analogs found:** 15 / 17 (two intentional new artifacts)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | runtime/service, result model, sync+async executor | request-response + event-driven callbacks + in-memory history | `StateMachine._execute_transition()` / `AsyncStateMachine.trigger_async()` | exact surface, behavior to replace |
| `tests/test_transition_lifecycle.py` | test | table-driven request-response/event-driven | `tests/test_advanced_functionality.py`, `tests/test_async.py`, `tests/test_listeners.py` | new focused matrix; strong role matches |
| `tests/test_async.py` | test | async request-response/cancellation | existing async callback/declarative/history tests | exact |
| `tests/test_advanced_functionality.py` | test | sync request-response/history | existing result, callback, history tests | exact |
| `tests/test_listeners.py` | test | event-driven observer callbacks | listener order/error-isolation tests | exact, expected semantics change |
| `tests/test_builder.py` | test | staged configuration → request-response | declarative dispatch and builder tests | role-match |
| `tests/test_boundary_negative.py` | test | value/API compatibility | `TestTransitionResult` and `safe_trigger` tests | exact |
| `tests/test_mypyc_guard.py` | test/compatibility guard | static source transform + compiled import | AST slots/subclass guard | exact |
| `tests/test_performance_benchmarks.py` | performance test | batch measurement | trigger/history throughput tests | exact |
| `tools/phase16_isolated_verify.py` | verification harness | file I/O + subprocess batch | Phase 16 isolated suite runner | exact |
| `README.md` | public documentation | request-response usage | error/listener/async/history sections | exact |
| `docs/QUICK_START.md` | public documentation | request-response usage | listener/error/async examples | exact |
| `docs/dev/architecture.md` | maintainer documentation | transform/architecture description | dispatch/history and mypyc sections | exact |
| `docs/dev/testing.md` | maintainer documentation | batch verification procedure | Phase 16 matrix/gates | exact |
| `.specify/memory/spr-core-api.md` | living API contract | documentation transform | current core API bullets | exact |
| `.specify/decisions/ADR-004-*.md` | new ADR | append-only decision record | `ADR-002` result contract; `ADR-003` compilation boundary | no same artifact; use established ADR form |
| `evidence/release-baseline.json` | generated evidence/config artifact | file I/O | existing release evidence manifest | role-match; update only through evidence tooling |

## Pattern Assignments

### `src/fast_fsm/core.py` (runtime service/result model, request-response + event-driven)

**Analogs:** `StateMachine._prepare_transition()` (lines 1481-1515),
`StateMachine._execute_transition()` (1992-2130), `StateMachine.trigger()`
(2132-2249), `AsyncStateMachine.trigger_async()` (2496-2642), and the
declarative invocation helpers (2722-2808).

**Keep the preparation seam** (lines 1481-1515):

```python
prepared = self._prepare_transition(trigger, args, kwargs)
if isinstance(prepared, TransitionResult):
    return prepared
entry = prepared.entry
current_name = prepared.current_name
```

Retain the direct current-state/trigger dictionary lookup, `_PreparedDispatch`,
sanitized guard kwargs, and canonical declarative handler selection. The staged
executor should begin only after guard resolution and state permission pass.

**Result/API pattern** (lines 227-265):

```python
@dataclass(slots=True)
class TransitionResult:
    success: bool
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    trigger: Optional[str] = None
    error: str = ""

    def raise_if_failed(self) -> "TransitionResult":
        if not self.success:
            raise TransitionError(self)
        return self
```

Append `committed`, stable lowercase `stage`, and identity-preserving
`cause` with defaults so old positional construction remains valid. Preserve
value-returning ordinary triggers. Extend `raise_if_failed()` to chain from
`cause`, while keeping `TransitionError.result` and the existing message shape
compatible. Hide `cause` from repr/equality if that is the selected design;
never interpolate callback exception text into public messages or logs.

**Callback registry/import pattern** (lines 519-532, 1255-1378):

```python
self._before_listeners: list = []
self._on_exit_listeners: List[Any] = []
self._on_enter_listeners: List[Any] = []
self._after_listeners: List[Any] = []
self._on_failed_callbacks: list = []
self._trigger_callbacks: dict = {}
self._state_exit_callbacks: Dict[str, List[Any]] = {}
self._state_enter_callbacks: Dict[str, List[Any]] = {}
```

Continue using append-preserving lists and empty-list guards. Registration
methods remain additive and retain `*args, **kwargs` forwarding. The new
executor must call these collections in the locked order: before listeners;
state `on_exit`; registered sync source exit callbacks; exit listeners; commit;
state `on_enter`; registered destination enter callbacks; enter listeners;
declarative handler; trigger callbacks; after listeners. This deliberately
replaces the current callback-swallowing and current after-before-trigger
ordering in `_execute_transition()` (1992-2126).

**Current behavior to replace** (lines 2001-2126):

```python
try:
    fn(old_state, to_state, trigger, **kwargs)
except Exception as e:
    self._logger.warning("%s: Exception in on_exit_state listener: %s", self._name, e)

self._current_state = to_state
...
if self._history is not None:
    self._history.append(TransitionRecord(...))
```

Do not catch-and-continue per lifecycle callback. Catch ordinary callback
exceptions at one stage boundary, stop the remaining stages, and return a
failed result carrying stage/commit/cause. Make commit a private no-`await`
helper that updates `_current_state` and appends one `TransitionRecord`
together; use the existing bounded `deque` and timestamp construction from
lines 844-881 and 2120-2126. `force_state()` (1840-1862) delegates to the
executor and must retain its public signature and synthetic `"__force__"`
behavior unless the plan explicitly scopes a separate compatibility change.

**One failure-finalizer pattern:** the five duplicated loops in `trigger()`
(2147-2240) and `trigger_async()` (2508-2603) are the analog to consolidate.
Lower helpers should construct a result; one narrow finalizer should invoke
all `_on_failed_callbacks` once, in order, with the unchanged
`(trigger, from_state, error, **kwargs)` signature (registration at 1361-1367).
Catch observer failures locally so they cannot recurse, replace the original
cause/result, or prevent later observers. For cancellation, notify once at the
reached stage and re-raise the original `asyncio.CancelledError`; do not use
the ordinary failed-result return path.

**Async runner pattern** (2346-2642):

```python
async def trigger_async(self, trigger: str, *args, **kwargs) -> TransitionResult:
    prepared = self._prepare_transition(trigger, args, kwargs)
    ...
    condition_result = await self._evaluate_condition_async(...)
    ...
    can_proceed = await self._can_transition_after_declarative_guard_async(...)
```

Keep a separate explicit async runner to avoid coroutine/event-loop overhead in
sync `trigger()`. Await async source/destination callbacks at their matching
slots, not as a tail after `_execute_transition()` (2614-2642). Catch
`CancelledError` separately around each await, finalize with the explicit local
committed flag, and use bare `raise`. Do not add locks or reentrancy flags;
those belong to Phase 18.

**Declarative boundary** (2685-2808): retain
`_resolve_declarative_handler()` and exactly-once method selection. Split
invocation outcome normalization from compatibility-only direct
`handle_event*()` behavior as needed so ordinary dispatch treats false,
invalid, and raised handler outcomes as a `declarative-handler` stage failure.
Do not create a second dispatch route.

### `tests/test_transition_lifecycle.py` (new focused test, table-driven)

**Analogs:** `tests/test_advanced_functionality.py:1177-1257` for full callback
order/failure injection, `tests/test_async.py:752-891` for async callback
registration and parity, `tests/test_listeners.py:275-350` for registration
order/error cases, and history tests in
`tests/test_advanced_functionality.py:1533-1702`.

Build real `State`/`CallbackState`/`AsyncStateMachine` objects and record
stage names plus callback calls; do not mock the executor. Parameterize a
single scenario table across sync and async machines and assert, per injection
point, result fields (`success`, `committed`, `stage`, `cause`), current state,
history length, later-call suppression, observer order/count, and kwargs.
Cover resolution, guard false/raise, state permission false/raise, every
pre/post callback slot, declarative outcomes, trigger callback, after listener,
and cancellation at each real awaited point. Use `asyncio.Event` synchronization
instead of sleeps. Add `raise_if_failed()` cause identity/chaining and a
secret-bearing exception regression for repr/message/log redaction.

The old assertions in `test_advanced_functionality.py:320-350`,
`1177-1244`, `tests/test_listeners.py:308-350`, and
`tests/test_async.py:829-891` are useful negative specifications: rewrite
them for fail-fast, commit-aware semantics rather than preserving their old
catch-and-continue expectations.

### Existing behavior suites

#### `tests/test_async.py` (async request-response/cancellation)

Reuse callback registration, kwargs, clone, declarative, and history fixtures
at lines 752-1126. Update the documented old expectations at 829-843 (callback
failure currently succeeds) and 863-891 (async callbacks currently run after
all sync callbacks). Keep direct `handle_event_async()` normalization tests
as compatibility coverage, while ordinary `trigger_async()` tests assert
`declarative-handler` failures and exactly-once machine invocation.

#### `tests/test_advanced_functionality.py` (sync result/history/callbacks)

Reuse `TestTransitionResultRaiseIfFailed` at 1705-1844 for self-returning
success/chaining and `TransitionError.result`; extend it for `.cause`, stage,
committed flag, and `__cause__` identity. Reuse history tests at 1533-1702;
assert history is appended at commit even when post-commit callbacks fail and
is absent for pre-commit failures. Preserve force/reset/restore coverage from
1840-1919 and add explicit regressions if executor refactoring touches it.

#### `tests/test_listeners.py` (event-driven observers)

Keep duck-typed listener registration from 1255-1305 and registration-order
tests at 275-300. Replace the old error-isolation expectations at 308-350 for
first-failure stop semantics. `after_transition` must no longer be used as the
history authority; the machine-owned commit/history seam is authoritative.

#### `tests/test_builder.py` (staged configuration/declarative)

Retain builder auto-async/preflight and candidate wiring patterns around
3024-3481. Use existing ordinary declarative tests at 414-497 and async tests
at 935-1028 to prove the handler is selected and invoked once. Add lifecycle
stage/result assertions without changing builder freeze, identity, or async
mode decisions.

#### `tests/test_boundary_negative.py` (compatibility/API)

Extend `TestTransitionResult` at 179-203 with old five-field positional
construction, additive defaults, hidden cause representation, and stage values.
Keep `safe_trigger` tests at 210-230; `safe_trigger()` remains a last-resort
barrier and should not be used to hide ordinary staged callback failures.

#### `tests/test_mypyc_guard.py` (compiled compatibility guard)

The AST guard at 109-181 enforces decorators on user-subclassable `State`
classes; the source-origin/compiled checks at 240+ and `PHASE16_RUNNER` path
are the analog. New private lifecycle/result classes must be slotted and must
not create a new user-subclassable class without the required decorator. Keep
`TransitionError` as the explicitly registered `native_class=False` exception
boundary and preserve `core.py` as the sole mypyc unit.

#### `tests/test_performance_benchmarks.py` (batch performance)

Use the minimal two-state toggle and warmup/200,000-iteration measurement at
399-438 as the throughput pattern. Keep history-enabled comparison at 441-495
and measure the unconditional-success path after introducing stage helpers;
compiled `trigger()` must retain the 200,000 ops/sec floor and history must
remain within the existing documented ratio. Avoid per-success context/list
allocations.

### `tools/phase16_isolated_verify.py` (verification harness, file I/O/subprocess)

Extend, do not replace, the Phase 16 harness. `_prepare_tree()` (181-210)
exports `HEAD`, overlays an explicit inventory, selects
`FAST_FSM_BUILD_MODE`, runs `uv sync`, builds only compiled mode, and asserts
the imported `fast_fsm.core` origin. `_suite_mode()` (754-859) runs semantic
commands in fresh pure and compiled trees, then compiled performance and the
pure release gate. Add a backward-compatible `phase17` suite/inventory for
the new lifecycle test and docs/SPR/ADR files; keep native-shadow preflight
and explicit inventory rules. Installed-wheel parity remains Phase 20.

### Documentation and contract files

#### `README.md` and `docs/QUICK_START.md` (public usage)

Copy the existing value-returning error example (`README.md:175-194`,
`docs/QUICK_START.md:270-285`) and listener/async examples
(`README.md:270-377`, `docs/QUICK_START.md:168-222`). Update them to document
stable stage/committed/cause inspection, `raise_if_failed()` chaining, the
single callback order, fail-fast behavior, committed-only history, and native
cancellation propagation. Replace claims that listener exceptions are always
ignored and that async callbacks run after all synchronous callbacks. Keep
payload kwargs out of error/log examples.

#### `docs/dev/architecture.md` and `docs/dev/testing.md` (maintainer docs)

Use architecture's existing class/layout and dispatch sections
(`architecture.md:48-175`) as the format. Add a named pre-commit/commit/
post-commit seam and paired sync/async runners, while preserving the existing
canonical preparation, builder, bounded-history, and selective-mypyc sections.
Use the Phase 16 gate description in `testing.md:191-223` as the template for
the Phase 17 pure/native semantic matrix, cancellation tests, slots/type gates,
and throughput proof. State explicit Phase 18-20 exclusions.

#### `.specify/memory/spr-core-api.md` (living contract)

Follow the one-bullet-per-invariant style at lines 7-44. Replace the outdated
claims at 23, 27, 42, and 44 about async-tail ordering, callback swallowing,
and handler/history uncertainty with the frozen Phase 17 lifecycle order,
truthful result fields, observer finalizer, cancellation, and commit-owned
history rules. Keep the existing guard-context, builder, force/reset, and
selective compilation bullets intact.

#### `.specify/decisions/ADR-004-*.md` (new append-only decision)

Use `ADR-002-trigger-result-not-exception.md:1-44,139-155` for status/context/
decision/consequences structure and `ADR-003-mypyc-compilation-boundary.md`
for compatibility/performance rationale. Record the Phase 17 lifecycle and
failure contract as a new ADR; do not edit either accepted ADR in place.

#### `evidence/release-baseline.json` (generated evidence)

Treat this as generated output, not hand-authored documentation. Use the
existing release evidence CLI and Phase 16 source-origin workflow; review the
write diff and preserve environment labels. Do not claim installed-artifact
parity or alter release jobs, which are Phase 20.

## Shared Patterns

### Callback signatures and ordering

State hooks use `(from/to_state, trigger, *args, **kwargs)` at
`core.py:398-455`; machine callbacks/listeners use `**kwargs` at
`core.py:1255-1378`. Preserve registration order and caller payloads. The
new stage catalog is the single source of truth for sync and async; do not
encode stage metadata in observer kwargs.

### Failure and cause handling

Expected failures remain returned values per `ADR-002` and current
`TransitionResult` shape. Construct once, finalize observers once, retain the
original exception object in `cause`, and chain only at explicit
`raise_if_failed()`. Observer exceptions are isolated locally; lifecycle
callback exceptions fail fast; cancellation is re-raised.

### Commit/history

Reuse `deque(maxlen=...)`, `TransitionRecord`, defensive `history` copies, and
the `if self._history is not None` zero-cost-disabled branch at
`core.py:844-881`. Move append into the no-await commit helper with current
state mutation. No rollback is introduced.

### Pure/native and quality gates

Follow `tools/phase16_isolated_verify.py:181-210,813-859`: fresh exported
trees, explicit overlay inventory, origin assertion, pure and newly compiled
semantic runs, compiled throughput, and pure release gate. Run `uv` commands
only, retain slots/mypy/mypyc constraints, and never use checkout-native
shadows as semantic evidence.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `tests/test_transition_lifecycle.py` | test | table-driven request-response/event-driven | No single existing test owns a complete sync/async staged lifecycle matrix; compose the strong analogs above. |
| `.specify/decisions/ADR-004-*.md` | ADR | documentation decision record | New decision; copy the accepted ADR-002/003 structure and record only Phase 17 behavior. |

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `tests/`, `tools/`, `README.md`,
`docs/`, `.specify/memory/`, `.specify/decisions/`, `evidence/`  
**Files scanned:** 16 source/test/tool/doc artifacts plus Phase 17 context and
research  
**Pattern extraction date:** 2026-09-01
