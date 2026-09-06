# Phase 22: Ordered Runtime Selection & Lifecycle Integration - Pattern Map

**Mapped:** 2026-09-06  
**Files analyzed:** 7 planned/modified files  
**Analogs found:** 7 / 7 (6 exact runtime/test analogs; 1 new focused-test file with strong neighboring analogs)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | core runtime / model / lifecycle orchestrator | request-response + event-driven callbacks + transform | Same file: `_prepare_transition`, `_trigger_owned`, `_trigger_async_owned`, `_execute_transition*`, `_finalize_failure` | exact seams |
| `tests/test_priority_selection.py` | focused contract/integration test | request-response + event-driven guard ordering | `tests/test_graph_invariants.py` and `tests/test_transition_lifecycle.py` | strong new-file analog |
| `tests/test_transition_lifecycle.py` | lifecycle/result integration test | event-driven/request-response | Existing pre-commit, history, observer, and cancellation matrix in same file | exact |
| `tests/test_async.py` | async runtime integration test | event-driven/await sequence | Existing `can_trigger_async`, trigger, cancellation, and history tests in same file | exact |
| `tests/test_logging_config.py` | trace/redaction contract test | event-driven output | Existing `FSMTraceEvent` redactor and payload-confidentiality tests | exact |
| `tests/test_mypyc_guard.py` | compiled-boundary/AST/build guard | transform/build verification | Existing private-record, slot, result, and native-probe guards in same file | exact |
| `tests/test_performance_benchmarks.py` | performance/regression test | request-response measurement | Existing dictionary-count, singleton throughput, history, and trace gates in same file | exact |

## Pattern Assignments

### `src/fast_fsm/core.py` (core runtime/lifecycle, request-response + event-driven)

**Analog:** existing runtime seams in the same file. Keep `core.py` as the only selectively compiled module and preserve its import/type style (`:1-70`). Do not move selection into `conditions.py`; condition classes intentionally remain an interpreted, subclassable boundary.

**Runtime slot representation and direct lookup** (`:579-624`, `:2102-2153`):

```python
# Current Phase 21 shape
class TransitionEntry:
    __slots__ = ("to_state", "condition", "priority")

@dataclass(frozen=True, slots=True)
class _TransitionGroup:
    entries: Tuple[TransitionEntry, ...]

_TransitionSlot = Union[TransitionEntry, _TransitionGroup]

entries = self._transitions.get(current_name)
slot = entries.get(trigger) if entries is not None else None
if slot is None:
    return self._build_failure_result(
        current_name, trigger, error_msg, stage=_LIFECYCLE_STAGE_RESOLUTION
    )
```

Keep the singleton branch literal and direct. Iterate only `slot.entries` for a real group; do not normalize a singleton into a tuple, copy the tuple, sort at dispatch time, or use `_require_singleton_entry()` (that helper remains the fail-closed projection boundary at `:613-617`). Capture the source state/name and slot before async awaits. Group work is local O(k); singleton lookup/dispatch remains O(1).

**Prepared handoff** (`:670-680`):

```python
@dataclass(frozen=True, slots=True)
class _PreparedDispatch:
    entry: TransitionEntry
    current_name: str
    trigger: str
    args: Tuple[Any, ...]
    condition_kwargs: Optional[Dict[str, Any]]
    declarative_handler: Optional[Dict[str, Any]]
```

Extend this private handoff (or introduce a similarly explicit slotted outcome) so it contains the exact winning entry, captured source context, sanitized guard kwargs, and target-specific declarative handler. The winner must be fully eligible before lifecycle work begins. Carry priority on the private object/result fields, never as an internal `priority=` keyword beside caller `**kwargs`; application code may legitimately pass a keyword with that name.

**Three-stage eligibility** (`:2063-2271`, `:2386-2490`):

For every candidate, preserve this order: transition `entry.condition` via `_evaluate_condition_sync()` / `_evaluate_condition_async()`; `_resolve_declarative_handler(source_state, trigger, entry.to_state)` followed by the existing declarative evaluator; then `_can_transition_after_declarative_guard(...)` or its async counterpart with the candidate target.

The existing condition evaluator handles wrapper graphs, async leaves, awaitable rejection, cycle checks, and interpreted subclasses; reuse it rather than classifying callables again. `_sanitize_condition_kwargs()` remains the fresh bounded mapping for guards, while lifecycle callbacks receive the original application kwargs unchanged. A normal false means “continue” only while scanning a group. An ordinary `Exception` is terminal and becomes one truthful pre-commit result with the existing stage/cause. Never catch `BaseException` in candidate evaluation: async cancellation must escape to the established outer boundary.

**Sync one-selection/one-lifecycle shape** (`:3092-3298`):

Current flow prepares one entry, evaluates guard/declarative/permission, then calls `_execute_transition()` once. Refactor this to have selection return exactly one prepared winner or one terminal failure, then feed the winner into the same lifecycle runner once. Do not put `_execute_transition()` inside the candidate loop: lifecycle failure never falls through, callbacks/listeners/history are not candidate probes, and one attempt may have at most one commit/history record/success-observer sequence.

```python
prepared = self._prepare_transition(trigger, args, kwargs)
if isinstance(prepared, TransitionResult):
    return self._finalize_failure(prepared, kwargs)
...
result = self._execute_transition(
    to_state,
    trigger,
    *args,
    declarative_handler=prepared.declarative_handler,
    **kwargs,
)
if not result.success:
    return self._finalize_failure(result, kwargs)
return result
```

**Lifecycle commit and result finalization** (`:2671-2757`, `:2759-3298`):

```python
def _commit_transition(self, old_state, to_state, trigger):
    record = None
    history = self._history
    if history is not None:
        record = TransitionRecord(
            old_state.name, trigger, to_state.name, time.monotonic()
        )
    if record is not None:
        history.append(record)
    self._current_state = to_state

def _finalize_failure(self, result, kwargs):
    observers = tuple(self._on_failed_callbacks)
    for observer_index, observer in enumerate(observers):
        try:
            observer(result.trigger, result.from_state, result.error, **kwargs)
        except BaseException as observer_error:
            _emit_legacy_warning(...)
    return result
```

Use `_build_failure_result()` then `_finalize_failure()` exactly once for group exhaustion, guard/declarative/permission exceptions, and lifecycle failures. Group exhaustion is distinct from missing-trigger resolution: it is an uncommitted `selection` stage with `to_state=None`, `cause=None`, and `priority=None`; no rejected candidate is individually observed. Preserve singleton false/exception stage meaning (`guard` or `state-permission`) rather than changing singleton behavior to `selection`.

**Async mirror and cancellation** (`:3882-4135`):

`can_trigger_async()` currently binds/checks the loop, prepares one transition, awaits its stages, and returns a boolean without lifecycle or failure observation (`:3882-3908`). Mirror the sync group scan with one candidate stage awaited at a time; do not create tasks, use `gather()`, or parallelize guards. Ordinary false falls through, ordinary exceptions terminate, and `asyncio.CancelledError` propagates unchanged.

`trigger_async()` owns the cancellation finalizer (`:3935-3964`, `:3966-4135`):

```python
except asyncio.CancelledError as cancellation:
    cancelled_result = self._build_failure_result(
        old_state.name,
        trigger,
        f"Transition cancelled at {lifecycle_stage[0]}",
        stage=lifecycle_stage[0],
        to_state=to_state.name if committed[0] else None,
        committed=committed[0],
        cause=cancellation,
    )
    self._finalize_failure(cancelled_result, kwargs)
    raise
```

Keep cancellation outside ordinary `Exception` branches and update the stage tracker to identify selection when cancellation occurs during candidate evaluation. `can_trigger_async()` should propagate cancellation without invoking failure observers because it is an observer-free query.

**Declarative target identity** (`:4178-4199`):

```python
handler_info = source_state._handlers.get(trigger)
...
if target_state is not None and not _metadata_matches_state(
    handler_info["to_state"], target_state.name
):
    return None
return handler_info
```

Resolve this per candidate and retain the exact handler on the winner. Do not redesign decorator storage or resolve a singular handler after selection; public construction/declarative parity belongs to Phase 23.

**Runtime metadata and trace** (`:118-303`, `:518-576`, `:2671-2684`, `:3935-3964`):

- Append nullable `priority` to `TransitionResult` with `compare=False`, preserving the legacy five-field construction/equality surface and existing slotted dataclass convention.
- Add a priority slot/constructor field to `TransitionRecord`; pass the selected candidate’s priority through `_commit_transition()` so committed history records identify the edge chosen.
- Add nullable priority to `FSMTraceEvent` and `_emit_fsm_trace()` as scalar metadata. Preserve the disabled-trace early return before event allocation and the existing redactor allowlist/fail-closed behavior. Emit one trace event for the overall attempt, never one event per rejected candidate.
- Use selected/evaluated candidate priority for success, candidate exceptions, and committed lifecycle failures; `None` for missing trigger and exhausted group.

### `tests/test_priority_selection.py` (new focused contract test, request-response + event-driven)

**Analogs:** `tests/test_graph_invariants.py:20-45,250-315` for real FSM construction/private slot identity, and `tests/test_transition_lifecycle.py:290-337,607-705` for event ledgers and truthful results. Build real `StateMachine`/`AsyncStateMachine` instances; avoid mocking private selectors.

Cover synchronous ascending priority despite registration order; strict guard/declarative/permission order; false fallthrough versus terminal exceptions; group exhaustion versus missing-trigger resolution; unchanged singleton behavior; async sequential awaits/exception/cancellation; observer-free `can_trigger*`; priority in result/history/trace; and unchanged application kwargs. Use event handshakes rather than sleeps, matching `tests/test_transition_lifecycle.py:81-103` and `:925-1033`.

### `tests/test_transition_lifecycle.py` (lifecycle/result, event-driven)

**Analog:** same file’s stage catalog and failure matrices (`:168-185`, `:290-337`, `:460-487`, `:511-603`) and ordered lifecycle ledger (`:607-705`).

Extend the stage catalog with `selection` while keeping stable existing order. Add grouped cases proving all eligibility events precede lifecycle callbacks, listeners, commit, history, and handlers. Assert lifecycle failures after selection do not inspect a lower candidate, history has exactly one committed record only after commit succeeds, and failure observers run once. Preserve cause identity and secret-free error text.

### `tests/test_async.py` (async runtime, event-driven sequential awaits)

**Analog:** async condition/query cases (`:318-365`, `:703-777`), async history (`:1105-1170`), and nested async builder preflight (`:1178-1200`).

Reuse `AsyncCondition` subclasses and real `AsyncStateMachine`. Add grouped candidates with event lists/`asyncio.Event` gates. Assert one active candidate at a time, lower candidates untouched after exception/cancellation, identical bare-raised cancellation, and failure observation only for `trigger_async()`. Extend history assertions with priority while preserving FIFO/invalid-capacity behavior.

### `tests/test_logging_config.py` (trace/redaction, event-driven output)

**Analog:** `FSMTraceEvent` redactor contract (`:630-677`), confidential sync/async trace tests (`:450-475`, `:483-540`, `:546-628`), and bounded-key tests (`:883-904`).

Update exact event-field expectations to include nullable scalar priority. Verify success, selection exhaustion, and candidate exception trace metadata carry only allowed fields; raw args, kwargs values, condition reprs, and exception strings remain absent. Preserve custom-redactor allowlisting, broken-redactor suppression, parent-handler behavior, and disabled-trace zero-inspection assumptions.

### `tests/test_mypyc_guard.py` (compiled boundary, AST/build verification)

**Analog:** frozen/slotted private records (`:383-460`), result slot/order guard (`:1385-1441`), and native probe/typecheck tests (`:350-380`, `:1249-1321`).

Extend exact AST field/slot expectations for `_PreparedDispatch`, `TransitionResult`, `TransitionRecord`, `FSMTraceEvent`, and the `selection` stage catalog. Keep records frozen/slotted, `core.py` as the sole compiled unit, and no new public exports. Add a targeted compiled/pure behavior probe for singleton/group selection and priority propagation. Avoid dynamic attributes and implicit-union/generator helpers that mypyc cannot compile reliably; run blocking `task typecheck-mypy`.

### `tests/test_performance_benchmarks.py` (performance/regression, request-response measurement)

**Analog:** operation-count invariants (`:120-155`), singleton priority proof (`:131-142`), lifecycle throughput floor (`:868-907`), history ratio (`:908-963`), and disabled trace boundary (`:1100-1158`).

Retain the direct singleton `<=2` topology-operation proof across unrelated topology sizes. Add a group call-count proof showing work proportional to candidate rank/group length and no runtime `sorted()`/copy/topology scan. Keep singleton compiled throughput floor and history/trace regressions intact; benchmark assertions remain environment-labeled evidence.

## Shared Patterns

### Capture → select → finalize/execute once

**Sources:** `src/fast_fsm/core.py:2102-2271,2671-2757,3092-3298,3882-4135`; `tests/test_transition_lifecycle.py:290-337,511-603`.

Resolve the direct slot once, scan only the immutable group when needed, and produce one prepared winner or one terminal result. Rejections are internal scan control; only exhaustion, exceptions, or lifecycle failure reach `_finalize_failure()`. Feed one winner to the pre-existing lifecycle runner/commit seam.

### Source/target identity and sanitized context

**Sources:** `src/fast_fsm/core.py:2102-2153,2190-2271,4178-4199`; `tests/test_async.py:350-365`; `tests/test_logging_config.py:131-153`.

Capture the source used for lookup, resolve declarative metadata per target, use a fresh bounded sanitized mapping for guard evaluation, and pass original callback kwargs unchanged. Never pass internal priority through application kwargs or trace raw values.

### Failure and cancellation finalization

**Sources:** `src/fast_fsm/core.py:2686-2757,3935-4135`; `tests/test_transition_lifecycle.py:342-380,460-603`.

Build a truthful staged result, preserve cause identity without leaking it, snapshot failure observers once, isolate observer failures, release ownership in `finally`, and bare re-raise async cancellation. Queries remain observer-free.

### Slotted compiled boundary

**Sources:** `src/fast_fsm/core.py:518-680`; `tests/test_mypyc_guard.py:383-460,1385-1441`.

All hot-path records stay slotted; private dataclasses remain frozen/slotted; exact field assertions must be updated deliberately. Keep `conditions.py` interpreted and `core.py` as the sole compiled module.

### Singleton fast path and bounded group work

**Sources:** `src/fast_fsm/core.py:599-617,2102-2153`; `tests/test_performance_benchmarks.py:120-155`.

Do not regress direct dictionary lookup for singleton slots. Group selection is the only O(k) work, using the registration-sorted tuple with early exit and no dispatch-time ordering or allocation.

## No Analog Found

| File/construct | Role | Data Flow | Reason |
|---|---|---|---|
| `tests/test_priority_selection.py` | focused selection contract | request-response + event-driven | No existing test owns ordered candidate selection; compose graph-invariant identity helpers with lifecycle event-ledger patterns. |
| Private selection outcome/helper inside `core.py` | runtime utility/orchestrator | transform + request-response | Phase 21 introduced the slot union but no selector; reuse existing prepared-dispatch/failure seams rather than adding a second condition or lifecycle engine. |

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`, `tests/test_graph_invariants.py`, `tests/test_transition_lifecycle.py`, `tests/test_async.py`, `tests/test_logging_config.py`, `tests/test_mypyc_guard.py`, `tests/test_performance_benchmarks.py`, and Phase 21/22 planning artifacts.  
**Files scanned:** 7 primary planned files plus Phase 21 topology patterns and Phase 22 research/validation.  
**Pattern extraction date:** 2026-09-06

## PATTERN MAPPING COMPLETE
