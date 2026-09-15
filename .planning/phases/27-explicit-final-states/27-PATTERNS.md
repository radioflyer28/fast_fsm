# Phase 27: Explicit Final States - Pattern Map

**Mapped:** 2026-09-15  
**Files analyzed:** 9 (one new behavioral test module, one core implementation,
six adjacent test contracts, and one living SPR)  
**Analogs found:** 9 / 9

This phase has one implementation seam: `src/fast_fsm/core.py`.  All public
topology adapters already converge on its canonical request transaction.  The
remaining files are contract extensions and memory/documentation updates; do
not create adapter-local final-state logic or a second termination flag.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | component / model / runtime | event-driven, transform, serialization | existing `State`, `StateMachine`, lifecycle, and persistence seams in the same file | exact |
| `tests/test_final_states.py` | test | event-driven + transform + serialization | `tests/test_state_machine_utils.py`, `tests/test_graph_invariants.py`, `tests/test_transition_lifecycle.py` | role-match |
| `tests/test_graph_invariants.py` | test | transform / construction transaction | existing `graph_fingerprint()` and atomicity tests in the same file | exact |
| `tests/test_transition_lifecycle.py` | test | event-driven lifecycle | existing sync/async failure-boundary matrix in the same file | exact |
| `tests/test_builder.py` | test | batch construction / transform | existing builder staging and retryability tests in the same file | exact |
| `tests/test_async.py` | test | event-driven async | existing `AsyncStateMachine` and clone parity tests in the same file | exact |
| `tests/test_hypothesis.py` | test | generated transform / event-driven sequences | existing generated topology and trigger invariants in the same file | exact |
| `tests/test_mypyc_guard.py` | test / compatibility guard | source transform + compiled artifact | existing AST, slots, and native-boundary assertions in the same file | exact |
| `.specify/memory/spr-core-api.md` | living reference documentation | contract transform | existing core API bullets and persistence/control contract in the same file | exact |

## Pattern Assignments

### `src/fast_fsm/core.py` (component/model/runtime, event-driven + serialization)

**Analog:** the existing slotted state model, canonical construction
transaction, commit seam, and dictionary adapter in `src/fast_fsm/core.py`.

**State model and subclass construction** (current lines 838-937, 5251-5277):

```python
@mypyc_attr(allow_interpreted_subclasses=True)
class State:
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    @classmethod
    def create(...):
        return CallbackState(name, on_enter, on_exit)

class CallbackState(State):
    __slots__ = ("_on_enter", "_on_exit")

    def __init__(self, name: str, on_enter=None, on_exit=None):
        super().__init__(name)
        self._on_enter = on_enter
        self._on_exit = on_exit

class DeclarativeState(State):
    __slots__ = ("_handlers", "_logger")

    def __init__(self, name: str, logger_name: Optional[str] = None):
        super().__init__(name)
        self._handlers = {}
        ...
        self._discover_handlers()
```

Add the exact keyword-only flag to every explicit constructor/factory surface,
validate `type(final) is bool` before assignment, store it in a private
`State` slot, and expose only a getter.  Preserve `name` mutability,
`allow_interpreted_subclasses`, callback `*args, **kwargs`, and subclass slots.
`AsyncDeclarativeState` inherits the declarative constructor and needs no async
copy of the flag.

**Canonical endpoint validation and publication** (current lines 1739-1808,
1867-1935):

```python
source = self._resolve_canonical_state(raw_source, role="source")
if source.name in source_names:
    raise ValueError(...)
source_names.add(source.name)
sources.append(source)
target = self._resolve_canonical_state(to_state, role="target")
...
prepared.append(self._normalize_transition_request(...))
...
self._commit_transition_plan(tuple(prepared))
```

Check `source.final` immediately after canonical source resolution, before
target/guard/timing work.  Keep the check only here: direct, batch,
multi-source, priority, helper, factory, builder, clone, and dictionary paths
already submit `_TransitionRequest` tuples to this seam.  Preserve the
off-table preparation and single publication/version increment in
`_commit_transition_plan`; a mixed invalid batch must leave all existing slots,
`_graph_version`, and reusable builder staging unchanged.  Use the existing
`error_contexts` tuple so dictionary failures retain bounded row context.

**Runtime query and commit truth** (current lines 2282-2300 and 3483-3503):

```python
@property
def current_state(self) -> State:
    return self._current_state

@property
def current_state_name(self) -> str:
    return self._current_state.name

def _commit_transition(...):
    ...
    self._current_state = to_state
    self._state_entered_at = timestamp
```

Implement `is_terminated` as a getter returning
`self._current_state.final`.  Do not add `_terminated`, scan the transition
table, or modify the commit ordering.  The current-state assignment is the
commit boundary; post-commit callbacks/listeners and async cancellation may
fail, but the final destination and derived query remain authoritative.
`AsyncStateMachine` (current lines 4107-4153) subclasses `StateMachine`, so the
inherited property gives sync/async parity.

**Control and clone continuity** (current lines 3307-3444):

```python
def _force_state_owned(self, state_name: str) -> None:
    if state_name not in self._states:
        raise KeyError(...)
    self._execute_control_transition(self._states[state_name], "__force__")

def reset(self) -> None:
    ...
    self._force_state_owned(self._initial_state.name)

def restore(self, snapshot: Dict[str, Any]) -> None:
    ...
    self._force_state_owned(state_name)

def _clone_owned(self) -> "StateMachine":
    new_fsm = self.__class__(self._initial_state, name=self._name, clock=self._clock)
    new_fsm._states = dict(self._states)
    ...
    new_fsm._apply_transition_requests_owned(tuple(requests))
```

Reuse these control and clone paths.  Reset/restore derive finality from the
resulting canonical state; leave snapshot v1 state-only.  Clone the exact
canonical `State` objects and reconstruct independent transition containers
through the canonical transaction, so immutable final markers are preserved
without sharing mutable topology.

**Dictionary persistence** (current lines 1264-1583):

```python
fsm = cls.from_states(*all_state_names, initial=initial, name=fsm_name, clock=clock)
...
fsm._apply_transition_requests_owned(
    tuple(requests),
    error_contexts=tuple(f"from_dict: transition[{index}]" for index, *_ in parsed_rows),
)
...
return {
    "name": self._name,
    "initial": self._initial_state.name,
    "states": sorted(self._states.keys()),
    "transitions": transitions,
}
```

Keep `snapshot()` unchanged.  Add one top-level deterministic sorted
`final_states` name list to `to_dict()`; absent legacy input means no final
states.  Validate that the field is a list of non-empty strings and that every
name resolves to the declared/derived state set before constructing canonical
states with `final=`.  Submit all transition rows once with `error_contexts`;
do not serialize objects, callbacks, or conditions.  Keep the existing
`cls(...)` construction so async deserialization retains its machine type.

### `tests/test_final_states.py` (test, event-driven + transform + serialization)

**Analogs:** `tests/test_state_machine_utils.py` property tests (current lines
1-70, 272-312), `tests/test_graph_invariants.py` atomic fingerprints (lines
22-70, 395-468), and `tests/test_transition_lifecycle.py` boundary matrix
(lines 932-997 and 1146-1248).

Create the central behavioral oracle rather than scattering all FINAL-01–06
cases across unrelated suites.  Use real `State`/`CallbackState`/
`DeclarativeState`/`AsyncDeclarativeState` objects, as the existing suites do;
avoid mocks.  Organize tests by state model, termination query, construction
atomicity, lifecycle commit truth, and control/persistence continuity.

**Property/test style to copy:**

```python
idle = State("idle")
running = State("running")
machine = StateMachine(idle, name="test")
machine.add_state(running)
machine.add_transition("start", idle, running)
assert machine.current_state is idle
assert machine.trigger("start").success
assert machine.current_state is running
```

For rejection tests capture the existing graph fingerprint and assert the
fingerprint, current-state identity, and graph version remain unchanged after
direct, batch, multi-source, priority, helper, quick-build, builder,
declarative, clone, and dictionary failures.  Assert exact-bool rejection and
property assignment failure.  Include a final initial state, an explicit
final sink versus a structurally identical non-final sink, sync and async
machines, post-commit entry/listener failure, and async destination-entry
cancellation using the event-handshake pattern from the lifecycle analog.

### `tests/test_graph_invariants.py` (test, construction transform)

**Analog:** existing `graph_fingerprint()` and canonical atomicity tests at
lines 22-62, 269-300, 395-468, and 893-956.

Extend the fingerprint only as needed to prove state-marker identity/value and
update the exact `to_dict()` schema expectation for the additive
`final_states` field.  Preserve the test's private-contract posture: compare
canonical State identities, transition entry identities, `_graph_version`,
current state, and `_graph_snapshot()`.  Follow the existing mixed-batch
pattern:

```python
before = graph_fingerprint(machine)
with pytest.raises(ValueError, match="final"):
    machine.add_transitions([
        ("good", idle, running),
        ("bad", final_state, running),
    ])
assert graph_fingerprint(machine) == before
```

Also retain the source-shape assertions that adapters call
`_apply_transition_requests_owned()` exactly once and do not bypass the
canonical transaction.

### `tests/test_transition_lifecycle.py` (test, event-driven lifecycle)

**Analog:** sync lifecycle failure matrix at lines 932-997 and async
cancellation matrix at lines 1146-1256.

Reuse `CallbackState` and listener registration to put a `final=True`
destination at the existing post-commit boundaries.  Copy the established
assertions for `result.committed`, `result.stage`, `result.cause`, current
State identity, history length, and exactly-once observers.  Add
`machine.is_terminated is True` whenever the destination-enter/observer stage
is reached, including when the callback raises.  For async cancellation, use
`asyncio.Event` handshakes and cancellation cleanup; never use sleeps or
rollback compensation.

### `tests/test_builder.py` (test, batch construction transform)

**Analog:** builder staging fingerprint and repairability tests at lines
123-184, 187-267, 1125-1152, and 2142-2196.

Use `builder_staging_fingerprint()` to prove a final-source failure leaves
`_machine is None`, staged requests intact, and the builder repairable.  Test
that final-state objects are retained by `add_state()` and that a later valid
build publishes only after the complete candidate transaction succeeds.  Keep
the builder's cached-machine/freeze behavior and async preflight assertions
unchanged.

### `tests/test_async.py` (test, event-driven async)

**Analog:** `two_state_async_fsm` fixture and async basics at lines 205-251,
async callback/clone parity at lines 946-985, and priority clone parity at
lines 1229-1274.

Prefer inherited-surface assertions (`isinstance(machine, StateMachine)`,
`current_state`, `trigger_async`) over async-specific implementation checks.
Verify a final initial state reports terminated, a final destination reports
terminated after `trigger_async`, and clone preserves final State identity and
independent transition tables.  Use `pytest.mark.asyncio` and existing
`AlwaysAsyncCondition`/callback helpers when a guard or lifecycle boundary is
needed.

### `tests/test_hypothesis.py` (test, generated transform + event sequences)

**Analog:** generated topology builder and invariant tests at lines 23-93 and
101-183.

Preserve the small bounded strategies and `@settings(...)` values.  Add a
strategy for explicit final markers only where generated edges can be filtered
or expected to reject; never generate invalid final-source edges as valid
topologies.  Assert that arbitrary valid trigger sequences keep
`is_terminated == fsm.current_state.final`, and that failed construction does
not publish a prefix.  Keep the existing direct `_current_state` resets only
for property-test isolation.

### `tests/test_mypyc_guard.py` (test, source/native compatibility)

**Analog:** decorated-class guard at lines 241-259, slots/field assertions at
lines 390-445 and 990-1010, and source-shape guards throughout the file.

Extend AST/source assertions for the new `State` slot/property and any
required `_Graph*`/prepared-field changes.  Confirm the final marker does not
introduce a dynamic `__dict__`, that subclassability decorators remain, and
that `StateMachine` exposes the query without a second mutable termination
slot.  Keep the native-mode behavior checks separate from pure-source
restoration; compile only through the repository's `task build-check`/`uv`
workflow.

### `.specify/memory/spr-core-api.md` (living reference documentation,
contract transform)

**Analog:** existing bullets for `State`, canonical construction, commit,
control, clone, and dictionary persistence (notably current lines 11, 29,
44, 49, 51, 61, and 66).

Update the living core API memory in the same behavior commit.  Record the
immutable `State.final` contract, explicit-only finality, O(1) inherited
`StateMachine.is_terminated`, final-source rejection in the canonical
transaction, unchanged snapshot v1, and deterministic `final_states` dict
metadata.  Keep the SPR compact and normative; do not add a parallel TODO or
implementation narrative.

## Shared Patterns

### Canonical all-or-nothing construction

**Source:** `src/fast_fsm/core.py:1739-1935`, exercised by
`tests/test_graph_invariants.py:448-498`.

Resolve exact registered endpoint identities, validate every request into a
private prepared tuple, then publish replacements once.  Every adapter should
remain a carrier into this seam.  A final-source check belongs after source
canonicalization and before any publication.

### Commit-before-post-commit work

**Source:** `src/fast_fsm/core.py:3483-3503` and
`tests/test_transition_lifecycle.py:946-997`.

The no-user-code commit writes history/current state/time first; destination
entry, callbacks, listeners, and observers run afterward.  Finality must be a
derived read of the committed current State, so later failures do not undo it.

### Exact identity and slots

**Source:** `src/fast_fsm/core.py:838-925` and
`tests/test_mypyc_guard.py:241-259`.

Preserve slotted hot-path objects and exact canonical State identity.  Validate
the new public boolean without coercion and expose no setter or dynamic
attribute path.

### Bounded deterministic persistence

**Source:** `src/fast_fsm/core.py:1264-1583` and
`tests/test_graph_invariants.py:395-410`.

Use JSON-native names, sorted deterministic collections, additive fields, and
row-context-aware errors.  Legacy dictionaries that omit the new field must
deserialize with every state non-final; malformed or unknown final names must
fail before transition publication.

### Pure/native and sync/async parity

**Source:** `setup.py:16-39`, `Taskfile.yml:189-202`,
`tests/test_async.py:220-251`, and `tests/test_mypyc_guard.py`.

Keep `core.py` as the sole mypyc compilation unit, run targeted tests before
the full sequential suite, and verify both compiled and pure-source imports.
`AsyncStateMachine` should inherit the query and use the same canonical
construction invariant rather than gaining a parallel implementation.

## No Analog Found

None.  The new `tests/test_final_states.py` is a new aggregation point, but
its unit, lifecycle, atomicity, async, and persistence patterns all have
strong adjacent analogs listed above.

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `tests/`, `setup.py`,
`Taskfile.yml`, `.specify/memory/`  
**Files scanned:** 9 planned files plus adjacent core/test/build references  
**Pattern extraction date:** 2026-09-15
