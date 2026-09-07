# Phase 23: Construction, Declarative & Serialization Parity - Pattern Map

**Mapped:** 2026-09-07  
**Files analyzed:** 9 expected implementation/documentation/test files  
**Analogs found:** 9 / 9 (all have a strong live analog)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | component/model/factory | event-driven + transform/file-I/O projection | existing `TransitionEntry`/`_TransitionGroup`, registrar, declarative state, clone | exact |
| `.specify/memory/spr-core-api.md` | contract documentation | reference/serialization | existing priority and trace contract entries | role-match |
| `tests/test_builder.py` | integration test | event-driven construction | existing quick-build, declarative, builder publication/preflight tests | exact |
| `tests/test_advanced_functionality.py` | integration test | file-I/O/transform round-trip | existing `TestFromDict`, `TestToDict`, `TestFromDictConditions` | exact |
| `tests/test_graph_invariants.py` | model/projection test | transform/query | existing graph snapshot, atomicity, group identity tests | exact |
| `tests/test_state_machine_utils.py` | query test | transform/query | existing available-trigger/reachable/target-query tests | role-match |
| `tests/test_transition_lifecycle.py` | lifecycle test | event-driven | existing sync/async declarative lifecycle tests | exact |
| `tests/test_async.py` | async integration test | event-driven | existing async declarative, selector, clone tests | exact |
| `tests/test_mypyc_guard.py` | build/static contract test | batch/build | existing frozen-slot record, selector AST, native probe tests | exact |

`src/fast_fsm/conditions.py` is a reference boundary, not an expected change:
its `Condition`/`GuardCallable` APIs and callable wrappers remain the source of
the opaque live guard objects supplied to `from_dict()`.

## Pattern Assignments

### `src/fast_fsm/core.py` (component/model/factory, event-driven + transform)

**Analogs:** `TransitionEntry`/`_TransitionGroup`, `_commit_transition_plan()`,
`_graph_snapshot_owned()`, `FSMBuilder.build()`, and the declarative resolver.

**Typed topology and mypyc pattern** (lines 611-700):

```python
class TransitionEntry:
    __slots__ = ("to_state", "condition", "priority")

    def __init__(self, to_state, condition=None, priority=0):
        self.to_state = to_state
        self.condition = condition
        self.priority = priority

@dataclass(frozen=True, slots=True)
class _TransitionGroup:
    entries: Tuple[TransitionEntry, ...]

@dataclass(frozen=True, slots=True)
class _GraphTransition:
    from_state: "State"
    trigger: str
    to_state: "State"
    condition: Optional[Condition]
    from_state_name: str
    to_state_name: str
    condition_name: Optional[str]

@dataclass(frozen=True, slots=True)
class _PreparedTransition:
    trigger: str
    sources: Tuple["State", ...]
    target: "State"
    condition: Optional[Condition]
    priority: int
```

Keep new condition-reference fields trailing and scalar/optional, preserve
`__slots__` on mutable hot-path records, and keep private projection records as
`@dataclass(frozen=True, slots=True)`. The compiled core should retain an
explicit `Union[TransitionEntry, _TransitionGroup]`; do not hide it behind
`Any`. Update the AST contract tests whenever fields are intentionally added.

**Cold candidate projection pattern** (lines 646-650, 1345-1373):

```python
def _require_singleton_entry(slot: _TransitionSlot) -> TransitionEntry:
    if isinstance(slot, _TransitionGroup):
        raise RuntimeError(_PRIORITY_GROUP_PROJECTION_ERROR)
    return slot

for from_name, entries in sorted(self._transitions.items()):
    for trigger, slot in sorted(entries.items()):
        entry = _require_singleton_entry(slot)
        transitions.append(_GraphTransition(...))
```

Replace the fail-closed projection call only in cold consumers with one private
helper returning `slot.entries` or `(slot,)`. Preserve direct selector branches
and their no-copy/no-sort O(1)/O(k) behavior. `_graph_snapshot_owned()` is the
right ownership envelope: it captures sorted source/trigger order and immutable
tuple output while the topology read boundary is held. Add priority and the
optional condition reference to each flattened `_GraphTransition`; do not make
the public runtime `snapshot()` a topology schema.

**Atomic registration pattern** (lines 1481-1530):

```python
replacements = {}
original_slots = {}
for plan in plans:
    for source in plan.sources:
        key = (source.name, plan.trigger)
        existing = replacements[key] if key in replacements else self._transitions[source.name].get(plan.trigger)
        replacements[key] = self._merge_transition_slot(existing, plan)

if not changed_replacements:
    return
for source_name, trigger, replacement in changed_replacements:
    self._transitions[source_name][trigger] = replacement
self._graph_version += 1
```

All builders, quick factories, and deserialization should normalize every row
first, then call one `add_transitions()`/`_commit_transition_plan()` boundary.
Do not sort, merge, or publish groups in an adapter. Exact priority validation,
duplicate identity, equal-priority conflicts, graph-version changes, and rollback
belong here. A malformed late row must leave both the existing machine and a
retryable builder unpublished/unchanged.

**Quick/factory construction pattern** (lines 1001-1076 and 1572-1668):

`quick_build()` first registers supplied `State` identities, collects unresolved
names, creates missing string states, creates the private machine, and only then
adds transitions. Extend row parsing from 3 fields to the already-established
3/4/5 forms (`trigger`, source, target, optional condition, optional priority),
preserving ordinary 3-field behavior. Convert all rows into canonical objects
and submit one batch. `quick_fsm()` (lines 5626-5650) should remain a thin
delegate; `from_states()`/`simple_fsm()` declare no transitions and need no
priority adaptation.

**Callable-safe serialization pattern** (lines 1080-1227):

The existing `from_dict()` validates required keys, discovers all states, and
then currently applies `_conditions[entry["trigger"]]` while registering each
row. Keep the two-stage shape but validate/resolve all records before creating
or publishing transitions. Emit one scalar record per candidate in deterministic
sorted source/trigger/ascending-priority order:

```python
{
    "trigger": trigger,
    "from": source,
    "to": target,
    "priority": priority,
    "condition_ref": opaque_ref,  # only when present
}
```

Never serialize a callable or infer an opaque reference from `Condition.name`.
Resolve an explicit non-empty `condition_ref` against the caller-owned
`conditions` registry. Permit legacy bare-trigger mappings only when exactly one
expanded candidate matches; raise an index-oriented ambiguity/missing-reference
error before any registrar call. Extra registry keys may retain the current
ignored behavior. Update the stale `from_dict()` docstring claiming that one
trigger guard fans out to every record.

**Declarative candidate storage/resolution pattern** (lines 4398-4419 and
4610-4818):

Current code discovers a metadata dictionary and overwrites it with
`self._handlers[trigger] = handler_info`. Replace that with an immutable plural
collection per trigger (a typed frozen/slotted declaration record is preferred),
retaining method, `from_state`, `to_state`, condition, async classification, and
exact priority. Accumulate the complete local collection during discovery before
publishing it; decorator/`dir()` order must not choose precedence. Extend
`transition()` with keyword-only `priority=0`, preserving legacy scalar metadata
attributes for unstacked callers and accumulating stacked declarations.

The runtime resolver should receive the already-selected canonical source,
target, and priority, then return exactly one declaration:

```python
handler = _resolve_declarative_handler(
    source_state, trigger, target_state, entry.priority
)
```

Filter on canonical source name, trigger, target name, and exact priority. Sync
and async selectors should put only that handler in `_PreparedDispatch`; the
handler invokes once at its existing lifecycle slot and receives unchanged
`*args, **kwargs`. Direct `handle_event*()`/`can_transition*()` lack enough
candidate context: preserve a unique declaration, but return a failed result /
false without invocation when multiple declarations remain.

**Builder preflight/publication pattern** (lines 4927-4965, 5165-5311):

Both `_detect_async_requirements()` and `_preflight_async_requirements()` must
iterate every declaration in each plural handler collection. Do not call
`.get()` on the collection itself. `build()` already creates a private candidate,
adds states, normalizes five-field transition rows, calls one `add_transitions()`,
wires callbacks, and assigns `_machine` only at the end. Preserve this envelope;
failed topology/async preflight must leave `_machine is None`, staging intact,
and the builder repairable.

**Query/clone pattern** (lines 2022-2118 and 2858-2920):

Keep `triggers` and `get_available_triggers()` deduplicated by trigger name.
Flatten candidate slots for `get_reachable_states()` and return deduplicated
target names; `transition_exists(..., to_state=...)` is true if any candidate
target matches. `can_trigger*()` remains the Phase 22 selector query boundary.
Clone by copying outer/per-state dictionaries and sharing immutable
`TransitionEntry`/`_TransitionGroup` values; do not rebuild via registration.
Copy condition-reference-bearing entries/groups and preserve independent table
ownership. Async clone should continue layering its async callback dictionaries
over `super().clone()`.

### `.specify/memory/spr-core-api.md` (contract documentation, reference)

**Analog:** existing priority topology/selector/result/history/trace entries.
Document the additive candidate identity and serialized `condition_ref` contract
alongside the existing exact-int priority and callback payload rules. State that
priority is candidate-derived metadata, not a callback kwarg; conditions are
external live objects resolved by opaque reference; legacy trigger-only guard
maps are valid only for unambiguous candidates. Keep public `snapshot()` shape
and callback signatures unchanged. This living contract must be updated with
the implementation, not left to a later docs phase.

### `tests/test_builder.py` (integration, event-driven construction)

**Analogs:** quick-build identity tests (around lines 695-812), declarative gap
coverage (820-1175), publication transaction (1675-1860), and async preflight
coverage (1865-2418).

Use the existing pattern of concrete `State` subclasses and assertions on exact
identity, `_machine is None`, staging fingerprints, and `pytest.raises`. Add
coverage for:

- quick/factory 3/4/5-row priority group parity and one-batch atomic rejection;
- stacked/same-trigger declarative declarations, exact target+priority handler
  selection, direct ambiguity returning failure without invocation;
- sync and async preflight visiting every plural declaration;
- duplicate/tie/malformed candidate build failures leaving the builder retryable.

Preserve existing callback payload assertions and run builder + async focused
tests after every declarative change.

### `tests/test_advanced_functionality.py` (integration, file-I/O/transform)

**Analogs:** `TestFromDict` lines 1349-1494, `TestToDict` lines 1500-1580,
and `TestFromDictConditions` lines 1901-2037. Keep JSON round-trip tests using
`json.dumps`/`json.loads`; use `FuncCondition` instances only in the external
conditions registry. Add candidate ordering, same source/trigger/target with
different priorities, explicit reference attachment, missing/repeated/ambiguous
reference failures, and proof that serialized dictionaries contain no callable.
Assert malformed late records do not expose partial topology.

### `tests/test_graph_invariants.py` (model/projection, transform/query)

**Analog:** `graph_fingerprint()` (lines 18-48), immutable snapshot test
(54-82), clone lineage (145-154), atomic group/tie tests (376-452).

Extend fingerprints to include every flattened candidate's priority, condition
identity/reference, and immutable snapshot row. Assert deterministic source,
trigger, priority ordering, candidate multiplicity, no graph-version change on
exact duplicate, and complete rollback on a late conflict. Keep tests white-box
and identity-sensitive; they are the closest proof that adapters use the
canonical registrar rather than a second topology model.

### `tests/test_state_machine_utils.py` (query, transform)

**Analog:** existing helper tests that exercise `quick_build()` and available /
reachable / target checks. Add grouped-slot reachable-state deduplication and
`transition_exists()` any-target semantics while asserting `triggers` and
`get_available_triggers()` remain deduplicated. Do not test diagnostic counts or
rendering here; those belong to Phase 24.

### `tests/test_transition_lifecycle.py` (lifecycle, event-driven)

**Analogs:** `test_sync_lifecycle_runs_the_locked_order...` around lines 848-930,
declarative post-commit outcome coverage around 1027-1060, and async lifecycle
ordering around 1063-1135. Build two same-trigger declarative candidates with
different priorities/handlers and assert only the selector-chosen handler runs,
exactly one lifecycle, unchanged callback kwargs, and selected priority in the
result/history/trace where already covered by Phase 22.

### `tests/test_async.py` (async integration, event-driven)

**Analogs:** async condition/selector tests, async declarative dispatch, and
clone callback independence around lines 945-980 and 1099-1198. Mirror the sync
candidate-identity cases with async handlers/guards, verify async preflight does
not inspect only the first declaration, and verify cloned grouped topology and
async callback ownership remain independent.

### `tests/test_mypyc_guard.py` (static/build, batch)

**Analogs:** frozen/slotted record AST assertions around lines 384-463,
selector shape/no-copy/no-sort checks around lines 1450-1510, and native probe
tests around lines 1055-1265.

Keep `core.py` as the sole mypyc module. Update exact expected field/slot sets
for new candidate metadata, retain frozen/slotted records and explicit union
selectors, and add plural-handler/native behavior coverage. Run AST guard,
Ruff, mypy, ty, slots-policy, in-place compiled build/import, and focused
compiled parity tests. Remove only generated build artifacts through the
established project cleanup flow; do not broaden the compilation boundary.

## Shared Patterns

### Atomic publication

**Source:** `src/fast_fsm/core.py:1481-1530`, `5213-5311`  
**Apply to:** quick builders, factories, `from_dict()`, `FSMBuilder`, and any
new candidate metadata materialization.

Normalize/validate all declarations first, stage replacements locally, then
publish once. Never mutate a published slot while still validating a later row.

### Candidate identity

**Source:** `src/fast_fsm/core.py:611-700`, Phase 22 selector/prepared dispatch  
**Apply to:** declarative handlers, graph snapshots, clone, serialization,
results/history/traces.

Identity is source + trigger + target + exact priority + condition identity (and
optional opaque reference for serialized projection). A trigger-wide dictionary
is not sufficient.

### Callable safety

**Source:** `src/fast_fsm/conditions.py:190-220`, current `from_dict()`/`to_dict()`
boundary at `core.py:1112-1128,1194-1227`  
**Apply to:** serialization and SPR documentation.

Keep live callables in caller-owned registries; serialize only JSON-compatible
scalar/container data and explicit opaque references. Reject ambiguous legacy
attachment instead of guessing.

### Native/slots boundary

**Source:** `src/fast_fsm/core.py:631-714`, `tests/test_mypyc_guard.py:384-463`  
**Apply to:** all new core records/helpers and compiled tests.

Use explicit annotations, `__slots__`, frozen slotted dataclasses for immutable
records, and no new runtime dependency or compiled module. Keep selector hot
paths free of sorting/copying/tuple materialization.

## No Analog Found

None. Phase 23 is an extension of existing construction, lifecycle, query,
serialization, and mypyc contracts; no new architectural role is required.

## Scope Guardrails for Planner

Do not include Phase 24 diagnostic counts/validation/renderers/adjacency or
Phase 25 drone documentation, benchmarks, installed artifacts, or release
proof. Do not add dynamic priorities, equal-priority policies, runtime group
mutation, callable serialization, a public topology snapshot version, or a
second registrar API.

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`,
`tests/test_builder.py`, `tests/test_advanced_functionality.py`,
`tests/test_graph_invariants.py`, `tests/test_state_machine_utils.py`,
`tests/test_transition_lifecycle.py`, `tests/test_async.py`,
`tests/test_mypyc_guard.py`, `.specify/memory/spr-core-api.md`  
**Files scanned:** 10  
**Pattern extraction date:** 2026-09-07
