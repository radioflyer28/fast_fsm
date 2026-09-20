# Phase 28: Same-State Transition Modes - Pattern Map

**Mapped:** 2026-09-16  
**Files analyzed:** 6  
**Analogs found:** 6 / 6

Phase 28 is a semantics-spine change. The canonical implementation belongs in
`core.py`, with the public stub kept in lockstep and a new central behavioral
oracle supplemented by existing structural, topology, and property-test suites.
Legacy tuple/factory/helper/declarative/dictionary adapters are intentionally
not assigned here; their complete propagation is Phase 30. Diagnostics and
documentation/release evidence remain Phases 31 and 32.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | service / runtime | event-driven + request-response + CRUD construction | existing `StateMachine` registration, selection, commit, and lifecycle seams in the same file | exact |
| `src/fast_fsm/core.pyi` | public type contract | request-response | existing runtime signatures and dataclass declarations in the same stub | exact |
| `tests/test_transition_modes.py` | test | event-driven + request-response | `tests/test_transition_lifecycle.py`, with timing cases from `tests/test_transition_timing.py` | role/data-flow match |
| `tests/test_graph_invariants.py` | test | CRUD / batch construction | existing canonical transaction, identity, snapshot, and version tests in the same file | exact |
| `tests/test_hypothesis.py` | test | batch / transform | existing generated-topology and reordered-batch invariants in the same file | exact |
| `tests/test_mypyc_guard.py` | test | request-response / structural transform | existing AST, slots, stub, and pure/native probes in the same file | exact |

## Pattern Assignments

### `src/fast_fsm/core.py` (service/runtime, event-driven + request-response)

**Analog:** current `src/fast_fsm/core.py` canonical registration and lifecycle
implementation. Keep the hot path slotted and preserve the existing
selection/ownership boundaries.

**Imports and carrier conventions** (lines 15-51):

```python
import logging
import math
import time
import threading
import contextvars
from collections import deque
from typing import Optional, Dict, Any, Callable, List, Mapping, Sequence, Union, Tuple, cast, overload
from dataclasses import dataclass, field
import asyncio
from inspect import iscoroutinefunction
from mypy_extensions import mypyc_attr
from .conditions import (
    AndCondition as AndCondition,
    AsyncCondition as AsyncCondition,
    CompiledFuncCondition as CompiledFuncCondition,
    Condition as Condition,
    FuncCondition as FuncCondition,
    GuardCallable as GuardCallable,
    GuardResult as GuardResult,
    NegatedCondition as NegatedCondition,
    NotCondition as NotCondition,
    OrCondition as OrCondition,
    _bind_compiled_func_condition_check,
    _is_awaitable_result,
)
```

Use the existing imports and avoid introducing an enum or strategy object for a
two-valued mode. `core.py` is the only mypyc compilation unit.

**Result/history and slotted carrier pattern** (lines 546-644):

```python
@dataclass(slots=True)
class TransitionResult:
    success: bool
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    trigger: Optional[str] = None
    error: str = ""
    committed: bool = field(default=False, compare=False)
    stage: Optional[str] = field(default=None, compare=False)
    cause: Optional[BaseException] = field(default=None, repr=False, compare=False)
    priority: Optional[int] = field(default=None, compare=False)

class TransitionRecord:
    __slots__ = ("from_state", "trigger", "to_state", "timestamp", "priority")
```

Append `internal` after the existing fields with a backward-compatible default;
for `TransitionResult`, use comparison-neutral metadata (`compare=False`). Keep
the first five positional/equality fields unchanged. Add the corresponding
trailing slot and constructor parameter to `TransitionRecord`.

**Canonical transition carriers** (lines 614-644, 722-837):

```python
class TransitionEntry:
    __slots__ = (
        "to_state", "condition", "priority", "condition_ref", "after", "within"
    )

@dataclass(frozen=True, slots=True)
class _GraphTransition:
    from_state: "State"
    trigger: str
    to_state: "State"
    condition: Optional[Condition]
    from_state_name: str
    to_state_name: str
    condition_name: Optional[str]
    priority: int
    condition_ref: Optional[str] = None
    after: Optional[float] = None
    within: Optional[float] = None
    statically_unconditional: bool = False

@dataclass(frozen=True, slots=True)
class _TransitionRequest:
    trigger: str
    sources: Tuple[Union[str, "State"], ...]
    to_state: Union[str, "State"]
    condition: Optional[Union[Condition, GuardCallable]] = None
    unless: Optional[Union[Condition, GuardCallable]] = None
    priority: Any = 0
    condition_ref: Optional[str] = None
    after: Any = None
    within: Any = None

@dataclass(frozen=True, slots=True)
class _PreparedTransition:
    trigger: str
    sources: Tuple["State", ...]
    target: "State"
    condition: Optional[Condition]
    priority: int
    condition_ref: Optional[str] = None
    after: Optional[float] = None
    within: Optional[float] = None

@dataclass(frozen=True, slots=True)
class _PreparedDispatch:
    entry: TransitionEntry
    source_state: "State"
    current_name: str
    trigger: str
    args: Tuple[Any, ...]
    condition_kwargs: Optional[Dict[str, Any]]
    declarative_handler: Optional[_DeclarativeHandler]
```

Add `internal: bool = False` to the canonical entry/request/prepared/graph
chain and preserve the selected `prepared.entry.internal` as the sole runtime
source of mode truth. Do not add a redundant mode to `_PreparedDispatch` unless
the compiled boundary requires it. Clone replay must copy the scalar.

**Exact validation and prepare-before-publish transaction** (lines 1823-1927,
1954-1997):

```python
normalized_priority = _normalize_priority(priority)
...
for raw_source in raw_sources:
    source = self._resolve_canonical_state(raw_source, role="source")
    if source.final:
        raise ValueError("final state cannot be a transition source")
    ...
target = self._resolve_canonical_state(to_state, role="target")
...
return _PreparedTransition(
    trigger, tuple(sources), target, normalized_condition,
    normalized_priority, condition_ref, normalized_after, normalized_within,
)
```

Validate `type(internal) is bool` at this boundary before any topology
mutation. Resolve canonical endpoints first, then reject `internal=True` if any
source is not the identical target object. Preserve final-source rejection
precedence. `_apply_transition_requests_owned()` normalizes every request and
calls `_commit_transition_plan()` only after all requests prepare successfully;
retain this atomic publication seam.

**Mode-aware candidate identity** (lines 1999-2038):

```python
candidate = TransitionEntry(
    plan.target, plan.condition, plan.priority, plan.condition_ref,
    plan.after, plan.within,
)
...
if entry.priority == candidate.priority:
    if (
        entry.to_state is candidate.to_state
        and entry.condition is candidate.condition
        and entry.condition_ref == candidate.condition_ref
        and entry.after == candidate.after
        and entry.within == candidate.within
    ):
        return existing
    raise ValueError("transition priority is already registered for this slot")
```

Include `entry.internal == candidate.internal` in the exact duplicate predicate.
Same-priority candidates with a different mode must take the conflict path;
same complete identity returns the published slot and leaves graph version
unchanged. Keep candidate ordering solely by priority.

**Selection and timing pattern** (lines 2748-2876):

```python
slot = entries.get(trigger) if entries is not None else None
...
if isinstance(slot, _TransitionGroup):
    for entry in slot.entries:
        selected = self._select_sync_candidate(..., entry, ..., now=selection_now)
        if selected is not None:
            return selected
...
if entry.after is not None or entry.within is not None:
    assert now is not None
    elapsed = now - self._state_entered_at
```

Mode is selection-neutral: guards, timing, permission, fallthrough, and priority
remain unchanged. Once selected, branch on `prepared.entry.internal`; never
infer mode from `old_state is to_state`. The existing direct singleton branch
must remain direct O(1), and group work remains local O(k).

**External lifecycle compatibility path** (lines 3652-3868):

```python
# Pre-commit: before-transition listeners.
for fn in self._before_listeners:
    try:
        fn(old_state, to_state, trigger, **kwargs)
    except Exception as cause:
        return self._build_lifecycle_failure(..., committed=False, priority=priority)

try:
    old_state.on_exit(to_state, trigger, *args, **kwargs)
except Exception as cause:
    return self._build_lifecycle_failure(..., "source-exit", cause,
                                         committed=False, priority=priority)

try:
    self._commit_transition(old_state, to_state, trigger, priority=priority)
except Exception as cause:
    return self._build_lifecycle_failure(..., "commit", cause,
                                         committed=False, priority=priority)

to_state.on_enter(old_state, trigger, *args, **kwargs)
...
return TransitionResult(True, from_state=old_state.name,
                        to_state=to_state.name, trigger=trigger,
                        committed=True, priority=priority)
```

Preserve this external body/order and `_commit_transition()` behavior for
`internal=False`: exit hooks/callbacks/listeners, commit/history, entry
hooks/callbacks/listeners, declarative handler, trigger callbacks, and after
listeners. The commit helper currently reads the clock, appends history, assigns
`_current_state`, and resets `_state_entered_at` (lines 3553-3573); do not reuse
that reset behavior for internal mode.

**Specialized internal commit/lifecycle seam:**

Use one predictable branch immediately after canonical selection and route to a
tightly bounded internal runner. Its order is before listeners → internal
logical commit/history → declarative handler → trigger callbacks → after
listeners → result/failure finalization. The internal commit should follow the
existing no-user-code commit boundary, but:

```python
history = self._history
if history is None:
    return  # no clock read, state assignment, or residency reset
timestamp = self._read_clock()
record = TransitionRecord(
    old_state.name, trigger, to_state.name, timestamp, priority,
    internal=True,
)
history.append(record)
```

Construct/read before append so clock or record failures are uncommitted
`commit` failures. With history enabled, timestamp the event but preserve
`_state_entered_at`; with history disabled, do not read the clock merely to
reassign the same state. Update the result's `committed=True` and `internal=True`
only after the logical commit succeeds. Do not pass mode in callback kwargs.

**Failure and observer pattern** (lines 3575-3650):

```python
return TransitionResult(
    False,
    from_state=from_state,
    to_state=to_state,
    trigger=trigger,
    error=error,
    committed=committed,
    stage=stage,
    cause=cause,
    priority=priority,
)

observers = tuple(self._on_failed_callbacks)
for observer in observers:
    try:
        observer(result.trigger, result.from_state, result.error, **kwargs)
    except BaseException:
        ...  # warn, preserve original outcome
```

Use `_build_lifecycle_failure()` and `_finalize_failure()` for internal failures.
Before-listener and commit failures are pre-commit; declarative, trigger, and
after failures are post-commit and retain destination/history/mode truth. Keep
exactly-once failure observation and redacted error text.

**Async parity and cancellation boundary** (lines 4416-4652, 4760-4826,
4909-5015):

The async runner mirrors the same slots and mutable truth cells:

```python
lifecycle_stage[0] = _LIFECYCLE_STAGE_COMMIT
try:
    self._commit_transition(old_state, to_state, trigger, priority=priority)
except Exception as cause:
    return self._build_lifecycle_failure(..., committed=False, priority=priority)
committed[0] = True
```

For internal mode, skip all sync and async source-exit and destination-entry
surfaces together. Keep the outer `trigger_async()` cancellation finalizer,
bare cancellation re-raise, ownership release in `finally`, and task-local
selection metadata. Extend the existing `_async_selection_priority` pattern
(lines 90-95 and 4962-5009) with equivalent mode truth if needed so guard-time
cancellation and selected-candidate failures report the same mode as sync.

**Clone and cold graph projection** (lines 1740-1797, 3483-3534):

```python
for entry in _transition_entries(slot):
    requests.append(
        _TransitionRequest(
            trigger, (source,), entry.to_state, entry.condition,
            priority=entry.priority,
            condition_ref=entry.condition_ref,
            after=entry.after, within=entry.within,
        )
    )
new_fsm._apply_transition_requests_owned(tuple(requests))
new_fsm._graph_version = self._graph_version
```

Add `internal=entry.internal` to clone requests and add the scalar to each
`_GraphTransition` created by `_graph_snapshot_owned()`. Preserve graph version
neutrality and structural independence of clone slots. Do not expand public
`to_dict()` or diagnostics in this phase.

**Direct and builder authoring surfaces** (lines 2040-2091, 5764-5839,
5994-6054):

```python
def add_transition(..., *, unless=None, priority=0, after=None, within=None):
    owner_thread_id = self._acquire_sync_ownership("add_transition")
    try:
        self._add_transition_owned(...)
    finally:
        self._release_sync_ownership(owner_thread_id)
```

Add keyword-only `internal=False` to direct and primary builder methods, thread
it into `_TransitionRequest`, and let the builder continue binding names to
canonical candidate states before one `_apply_transition_requests_owned()` call.
Retain builder staging repairability after failed candidate builds. Do not add
mode-specific behavior to deferred adapters.

---

### `src/fast_fsm/core.pyi` (public type contract, request-response)

**Analog:** existing `src/fast_fsm/core.pyi` declarations (lines 66-158,
246-257, 384-404).

Append fields and defaults in the same order as runtime classes:

```python
@dataclass(slots=True)
class TransitionResult:
    success: bool
    from_state: str | None = ...
    to_state: str | None = ...
    trigger: str | None = ...
    error: str = ...
    committed: bool = field(default=False, compare=False)
    stage: str | None = field(default=None, compare=False)
    cause: BaseException | None = field(default=None, repr=False, compare=False)
    priority: int | None = field(default=None, compare=False)
    internal: bool = field(default=False, compare=False)
```

Add matching `internal: bool = ...` to `TransitionRecord` and `TransitionEntry`
and matching keyword-only `internal: bool = False` (or stub ellipsis) to
`StateMachine.add_transition()` and `FSMBuilder.add_transition()`. Keep the
existing first five result fields and all callback `*args, **kwargs` signatures
unchanged. Private carrier declarations should mirror runtime field order so
strict mypy consumers and native structural tests see the same shape.

---

### `tests/test_transition_modes.py` (test, event-driven + request-response)

**Analog:** `tests/test_transition_lifecycle.py` is the strongest match for
ordered lifecycle/failure/cancellation behavior (imports and recorder at lines
1-100; lifecycle order at 832-931; failure matrix at 934-1053; async
cancellation handshake at 1156-1267). Use `tests/test_transition_timing.py`
lines 21-61 and 188-213 for deterministic clock assertions.

**Imports and local fixtures:**

```python
from dataclasses import dataclass
import asyncio
import pytest
from fast_fsm.conditions import AsyncCondition, Condition
from fast_fsm.core import (
    _LIFECYCLE_STAGES, AsyncStateMachine, CallbackState,
    DeclarativeState, State, StateMachine,
    TransitionRecord, TransitionResult, transition,
)
```

Keep helpers local (the research contract says not to import fixtures from other
test modules). Reproduce `LifecycleRecorder`, slotted async condition helpers,
and event/barrier handshakes; never use sleeps for cancellation or timing.

**External lifecycle oracle:** copy the exact ordered list style from
`test_sync_lifecycle_runs_the_locked_order_and_preserves_registration_order()`
(lines 832-931): register state hooks, per-state callbacks, listeners,
declarative handler, trigger callbacks, and after listeners; assert the complete
external order, canonical state/history, and `TransitionResult` compatibility.

**Internal lifecycle oracle:** use sentinel state hooks/callbacks/listeners that
would append or fail if invoked. Assert internal mode runs before listener,
logical commit/history, declarative handler, trigger callbacks, and after
listener exactly once while skipping every source/destination state lifecycle
surface. Assert callback kwargs retain caller payload and contain no injected
`internal` key.

**Failure oracle:** adapt the parameterized stage test at lines 934-1006. Assert
before/commit failures are `committed is False` with no history, while retained
post-commit failures have `committed is True`, `result.internal is True`, one
history entry, suffix stopping, and one failure-observer pass.

**Timing oracle:** copy `FakeClock` (lines 21-30). Assert history-disabled
internal commit does not increment clock calls, history-enabled internal commit
records event time but leaves `_state_entered_at` unchanged, external self
re-entry resets it, and repeated internal events do not restart `after=` or
`within=` windows.

**Async/cancellation oracle:** adapt the event handshake from lines 1166-1267.
Exercise guard cancellation before commit and retained declarative cancellation
after internal commit; assert skipped async exit/entry sentinels, matching stage,
commit/mode/history truth, identical cancellation re-raise, released owner/lock,
and successful reuse.

---

### `tests/test_graph_invariants.py` (test, CRUD / batch construction)

**Analog:** the same file's `graph_fingerprint()` (lines 23-63), snapshot test
(74-97), singleton/group test (628-649), duplicate identity test (694-704),
and request atomicity tests (706-827) are direct matches.

**Identity fingerprint pattern:**

```python
tuple(
    (
        id(entry), entry.priority, id(entry.to_state),
        id(entry.condition) if entry.condition is not None else None,
        entry.condition_ref, entry.after, entry.within,
    )
    for entry in (slot.entries if isinstance(slot, _TransitionGroup) else (slot,))
)
```

Include `entry.internal` in this fingerprint. Add assertions that internal
self-entries survive `_graph_snapshot()`, clone replay, and direct singleton or
local group storage. Invalid mode/type/fan-out requests must leave fingerprint,
slot identity, graph version, and all source tables unchanged.

**Atomic registration pattern:** use the existing before/after identity and
version assertions around `pytest.raises`, as in lines 743-758 and 838-849.
Cover exact duplicate same mode (version-neutral) and equal-priority different
mode (conflict). Verify a multi-source request with any non-self expansion is
rejected atomically and a final source remains rejected.

---

### `tests/test_hypothesis.py` (test, batch / transform)

**Analog:** existing strategies and generated invariants (lines 25-95,
103-198), plus reordered mixed final-source batch rejection (230-254).

```python
@given(order=st.permutations(("before", "invalid", "after")))
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_final_source_rejects_every_reordered_mixed_batch(order):
    before = (machine._graph_version, machine._graph_snapshot())
    with pytest.raises(ValueError, match="^final state cannot be a transition source$"):
        machine.add_transitions([rows[name] for name in order])
    assert (machine._graph_version, machine._graph_snapshot()) == before
```

Add compact strategies for exact bool mode and valid/invalid canonical self vs
non-self requests. Generate request permutations and assert no partial
publication, deterministic priority topology, and mode identity. Keep Hypothesis
examples bounded and use real `StateMachine` objects; do not introduce a new
fixture framework.

---

### `tests/test_mypyc_guard.py` (test, request-response / structural transform)

**Analog:** existing AST/slots/native guards. The private frozen-slot dataclass
contract is at lines 499-608; result/field ordering at 1870-1900; selector
structure and async metadata at 1929-2008; record slots at 2028-2068; pure/native
semantic probe at 2087-2158; exact priority boundary at 923-957.

**Carrier AST pattern:**

```python
tree = ast.parse(CORE_PY.read_text(encoding="utf-8"), filename=str(CORE_PY))
classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
...
assert keywords.get("frozen") is True
assert keywords.get("slots") is True
```

Extend expected field/slot lists with `internal` in exact runtime/stub order for
`TransitionEntry`, `_TransitionRequest`, `_PreparedTransition`,
`_GraphTransition`, `TransitionResult`, and `TransitionRecord`. Preserve the
private/non-exported boundary and `_PreparedDispatch.entry`-only selected mode.

**Exact-bool native boundary:** mirror the parameterized non-exact priority test
(lines 906-957) with `True`/false-like subclasses, integers, strings, and
coercible objects. Assert rejection occurs before slot or graph-version mutation
and before caller coercion. Run the same narrow mode/lifecycle/history oracle in
pure and freshly built native modes, asserting direct singleton representation,
stub signatures, and no source-tree native shadow.

## Shared Patterns

### Canonical atomic construction

**Sources:** `src/fast_fsm/core.py:1823-2038`,
`tests/test_graph_invariants.py:720-827`,
`tests/test_builder.py:243-285`.

**Apply to:** all registration and construction tests.

Normalize exact scalar values and canonical endpoint identity, build every
replacement off-table, publish once, and increment graph version only after
success. Reuse builder's staging fingerprint and repair-after-failure pattern.

### Selected-entry mode and priority

**Sources:** `src/fast_fsm/core.py:2748-2920`,
`tests/test_priority_selection.py:110-174`.

**Apply to:** sync/async runtime and central mode oracle.

Selection remains deterministic ascending priority and mode-neutral. Only the
selected immutable entry controls lifecycle specialization; rejected candidates
must produce no lifecycle effects.

### Lifecycle/failure truth

**Sources:** `src/fast_fsm/core.py:3553-3868,4416-4652,4909-5015`,
`tests/test_transition_lifecycle.py:832-1006,1156-1267`.

**Apply to:** both machines and all failure/cancellation tests.

Keep the one pre/post-commit stage model, exactly-once failure observers, mutable
`committed` truth cells for async cancellation, bare cancellation re-raise, and
ownership release in `finally`.

### Residency timing

**Sources:** `src/fast_fsm/core.py:3553-3573,2842-2846,4762-4766`,
`tests/test_transition_timing.py:21-61,188-213`.

**Apply to:** internal commit and timing tests.

Use the injected `FakeClock` pattern. External commits reset entry epoch; internal
history timestamps event time only and preserve `_state_entered_at`; history-off
internal commits avoid the clock read.

### Slots, typing, and pure/native parity

**Sources:** `src/fast_fsm/core.py:546-837`,
`src/fast_fsm/core.pyi:66-158,246-257,384-404`,
`tests/test_mypyc_guard.py:499-608,1870-2158`.

**Apply to:** all carrier and API changes.

Append defaulted fields, preserve slots and field order, retain callback variadic
signatures, keep `core.py` as the only compiled unit, and prove semantic
equivalence in pure/native modes.

## No Analog Found

None. Every in-scope file has an exact or strong role/data-flow analog. New
behavioral coverage should borrow the existing lifecycle, timing, topology,
Hypothesis, and native-probe patterns above rather than inventing a parallel
framework.

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `src/fast_fsm/core.pyi`, and
`tests/` lifecycle, timing, priority, builder, async, graph-invariant,
Hypothesis, and mypyc guard suites.  
**Files scanned:** 10 primary source/test files plus the phase context,
research, validation, and project instruction files.  
**Pattern extraction date:** 2026-09-16
