# Phase 21: Priority Contract & Atomic Registration - Pattern Map

**Mapped:** 2026-09-06  
**Files analyzed:** 9 planned/modified files  
**Analogs found:** 9 / 9 (7 exact/near-exact implementation or test analogs; 2 documentation/decision analogs)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | model/service/registrar/builder | CRUD + request-response + transform | `src/fast_fsm/core.py:579-592,1329-1661,2469-2500,4490-4942` | exact seams |
| `.specify/memory/constitution.md` | policy/config | static contract | `.specify/memory/constitution.md:35-47,108-124` | exact policy |
| `.specify/decisions/ADR-007-priority-topology.md` (new) | architecture decision | static decision record | `.specify/decisions/ADR-006-bounded-diagnostics-safe-output.md:1-29,55-78` | role-match |
| `.specify/memory/spr-core-api.md` | living architecture/API contract | static contract | `.specify/memory/spr-core-api.md:1-18,20-35,45-58` | exact |
| `tests/test_graph_invariants.py` | invariant test | request-response + CRUD | same file `:18-39,43-90,127-212` | exact |
| `tests/test_ownership_concurrency.py` | concurrency/invariant test | event-driven/request-response | same file `:234-330` and ownership stress cases | exact |
| `tests/test_builder.py` | builder/integration test | batch/transform | same file `:116-144,1559-1607,1669-1705,1745-1805` | exact |
| `tests/test_mypyc_guard.py` | static/build guard test | transform/build verification | same file `:382-434,581-599,701-753,1289-1328` | exact |
| `tests/test_hypothesis.py` | property test | batch/transform | same file `:28-60,68-95` | role-match |

The research text mentions `docs/adr` and `docs/spr-core-api`, but this checkout's authoritative locations are `.specify/decisions` and `.specify/memory`; use the existing locations above. No runtime selection, adapters, diagnostics, output, serialization, or telemetry files belong in this phase.

## Pattern Assignments

### `src/fast_fsm/core.py` (core model/registrar/builder, CRUD + request-response)

**Analog:** existing core seams in the same file. Keep `core.py` as the sole selectively compiled module and preserve its import style (`:13-40`).

**Slotted immutable records** (`:579-592,628-635`):

~~~
class TransitionEntry:
    __slots__ = ("to_state", "condition")

    def __init__(self, to_state: "State", condition: Optional[Condition] = None) -> None:
        self.to_state: "State" = to_state
        self.condition: Optional[Condition] = condition

@dataclass(frozen=True, slots=True)
class _PreparedTransition:
    trigger: str
    sources: Tuple["State", ...]
    target: "State"
    condition: Optional[Condition]
~~~

Extend `TransitionEntry` compatibly with `priority=0`; add the private group using the same `@dataclass(frozen=True, slots=True)` convention as `_GraphTransition`/`_GraphSnapshot`. Store tuple-backed candidates and publish replacement values; never publish or mutate a list. The new group is private, not an `__all__` symbol.

**Ownership envelope** (`:842-856,1430-1461`):

~~~
def add_transition(..., *, unless=None) -> None:
    owner_thread_id = self._acquire_sync_ownership("add_transition")
    try:
        self._add_transition_owned(..., unless=unless)
    finally:
        self._release_sync_ownership(owner_thread_id)

def _add_transition_owned(..., *, unless=None) -> None:
    prepared = self._normalize_transition_request(..., unless=unless)
    self._commit_transition_plan((prepared,))
~~~

Retain one public ownership admission and private owned/planning body for every helper. Do not make owned helpers call public registrars (the lock is explicitly non-reentrant).

**Normalize before mutation** (`:1329-1407`): resolve canonical states, reject duplicate source objects, enforce `condition`/`unless` exclusivity, normalize guards, and return one immutable prepared value. Add exact priority validation at this boundary. The implementation input must remain `priority: object`; check `type(priority) is int` before any cast/narrowing so compiled mypyc code cannot coerce `True` to `1`. Do not use `isinstance`, `int(priority)`, or a pre-typed `int` implementation parameter.

**Atomic staged commit** (`:1409-1428`):

~~~
def _commit_transition_plan(self, plans: Tuple[_PreparedTransition, ...]) -> None:
    # Existing code currently builds final_entries, then writes all entries.
    # Replace that last-write collapse with staged slot merges.
    ...
~~~

Build replacements off-table keyed by `(source.name, trigger)`. Each request must merge against `replacements.get(key, existing_slot)`, including repeated keys in one plan. A merge returns the same slot for an exact canonical duplicate, raises before publication for a distinct equal-priority candidate, and otherwise returns a new singleton/group sorted by ascending priority. Publish only after all plans merge successfully; increment `_graph_version` exactly once iff at least one slot identity changed. An all-duplicate plan leaves slot identities and version unchanged. This is the direct replacement for the current `final_entries[(source.name, plan.trigger)] = ...` at `:1411-1417`.

**Fan-out helpers** (`:1463-1661`):

~~~
prepared = []
for entry in transitions:
    if len(entry) not in (3, 4):
        raise ValueError("each transition entry must contain 3 or 4 items")
    trigger, from_state, to_state, *rest = entry
    prepared.append(self._normalize_transition_request(...))
self._commit_transition_plan(tuple(prepared))
~~~

Preserve accepted legacy batch tuple shapes while adding the five-field `(trigger, from_state, to_state, condition, priority)` shape. Bidirectional registration should normalize both legs then commit `(first, second)` once; carry separate keyword-only priorities. Emergency registration should carry one priority through its all-state prepared request. All validation must precede publication, including helper legs and multi-source fan-out.

**Ownership-safe snapshot/clone** (`:1256-1303,2469-2500`):

~~~
if self._sync_owner_thread_id == threading.get_ident():
    return self._graph_snapshot_owned()
self._sync_ownership_lock.acquire()
try:
    return self._graph_snapshot_owned()
finally:
    self._sync_ownership_lock.release()

new_fsm._states = dict(self._states)
new_fsm._transitions = {
    state_name: dict(triggers)
    for state_name, triggers in self._transitions.items()
}
new_fsm._graph_version = self._graph_version
~~~

Keep shared immutable entry/group values but copy outer and per-source tables. Make clone capture owner-aware using a public lock-taking wrapper plus an owned copy body, so concurrent registration cannot produce a torn snapshot and an owned caller cannot self-deadlock. Clone must have fresh ownership primitives.

**Builder staging/materialization** (`:4490-4705,4837-4942`):

~~~
self._transitions: List[tuple] = []
...
self._transitions.append((trigger, from_state, to_state, condition))
...
candidate = candidate_type(self._initial_state, **self._machine_kwargs)
for trigger, from_state, to_state, condition in self._transitions:
    candidate.add_transition(trigger, from_state_single, to_state_obj, condition)
self._machine = candidate
~~~

Extend staging/fingerprints/unpacking with priority while retaining the builder's atomic staging validation. During `build()`, install all states, materialize all staged transitions through one batch commit (rather than one public write per edge), and publish `_machine` only after the local candidate succeeds. A failed build leaves `_machine` unset and staging repairable.

### `.specify/memory/constitution.md` (policy/config, static contract)

**Analog:** current performance principles (`:35-47`) and anti-pattern table (`:108-124`). Amend the blanket “all core operations O(1)” and “single dict lookup, not a loop over candidates” statements before candidate topology lands. Use the precise replacement: source/trigger lookup and singleton dispatch remain O(1); local group construction and eventual selection are O(k); no unrelated graph scan and no dispatch-time sort; preserve the compiled singleton throughput floor. Keep the existing slots requirement and make the policy amendment append-only/versioned as required by project instructions.

### `.specify/decisions/ADR-007-priority-topology.md` (new decision, static record)

**Analog:** `.specify/decisions/ADR-006-bounded-diagnostics-safe-output.md:1-29,55-78`. Copy its structure: `Status`, `Date`, `Deciders`, `Context`, `Decision`, `Considered Alternatives`, `Consequences`, and `Deferred Follow-up`. Record the locked exact-int contract, singleton-or-frozen-group representation, registration-time sorting, staged atomic publication/version semantics, clone isolation, and explicit Phase 22+ deferrals. Do not create a parallel ADR directory or rewrite an existing ADR.

### `.specify/memory/spr-core-api.md` (living API contract, static contract)

**Analog:** existing entries (`:1-18,20-35,45-58`). Update in place in the same change as the public API. Preserve its terse factual bullets and explicit compiled/pure boundary. Add `priority` to the `add_transition` and helper signatures, exact built-in-int rejection, duplicate/conflict identity rules, singleton/group topology, one-version batch commit, clone table isolation, and builder transport. Correct the complexity statement to distinguish O(1) singleton lookup from O(k) local group work. Do not document selection semantics, serialization, diagnostics, or adapters here before their roadmap phases.

### `tests/test_graph_invariants.py` (invariant test, CRUD/request-response)

**Analog:** same file. Its test-only identity fingerprint (`:18-39`) captures state identity, target/condition identity, graph version, current state, and immutable snapshot; extend it with priority/group identity without comparing registration order. Existing version/idempotence tests (`:75-90`) and helper transaction tests (`:162-212`) are the fixtures for new cases.

~~~
def graph_fingerprint(machine: StateMachine) -> tuple[Any, ...]:
    transitions = tuple(sorted(
        (source_name, trigger, id(entry.to_state),
         id(entry.condition) if entry.condition is not None else None)
        for source_name, entries in machine._transitions.items()
        for trigger, entry in entries.items()
    ))
    snapshot = machine._graph_snapshot()
    return (..., machine._graph_version, id(machine.current_state), snapshot)
~~~

Add direct singleton/default-priority assertions, signed/gapped sorting, permutation-independent groups, exact duplicate identity no-op, equal-priority conflict rollback, mixed duplicate/new one-version increment, repeated-key batch merging, multi-source/bidirectional/emergency rollback, and clone shared-value / independent-table assertions. Keep runtime winner selection out of these tests.

### `tests/test_ownership_concurrency.py` (concurrency/invariant test, request-response)

**Analog:** public writer inventory and reentry matrix (`:234-330`). The parametrized `TOPOLOGY_HISTORY_WRITERS` list and callback reentry test establish that every registrar enters/releases one ownership envelope and rejects nested writes before mutation. Apply the same setup to clone capture and concurrent registration; assert no torn version/topology and no shared mutable group.

~~~
owner_thread_id = machine._acquire_sync_ownership("test-owner")
try:
    ...
finally:
    machine._release_sync_ownership(owner_thread_id)
~~~

Reuse real `StateMachine`, `threading.Event`/barriers, and identity assertions; do not mock commit logic. Preserve redacted ownership errors and lock release on validation failure/BaseException.

### `tests/test_builder.py` (builder/integration test, batch/transform)

**Analog:** topology fingerprint/staging helpers (`:116-144`), publication and clone ownership tests (`:1559-1607`), and repairable build tests (`:1745-1805`). Extend `_machine_topology_fingerprint` and `builder_staging_fingerprint` for priority. Add five-field staging/materialization, grouped same-slot candidates, invalid-priority staging rollback, duplicate/conflict build behavior, one graph commit, and failed-build repair tests. Keep the established pattern that `_machine` is a cache/freeze marker and failed candidates never publish it.

### `tests/test_mypyc_guard.py` (static/build guard, transform/build verification)

**Analog:** AST guard tests. `test_private_graph_records_are_frozen_slot_dataclasses` (`:382-434`) asserts exact fields/decorators; `test_state_machine_graph_version_remains_in_slots` (`:581-599`) guards StateMachine slots; lock/owned-body checks (`:701-753`) guard per-instance ownership; export and sole-core checks (`:1289-1328`) prevent public private-record leakage and additional mypyc modules.

~~~
assert keywords.get("frozen") is True
assert keywords.get("slots") is True
...
assert [item.value for item in calls[0].args[0].elts] == [
    "src/fast_fsm/core.py"
]
~~~

Extend exact field/slot expectations for the private group and priority, retain the no-export/sole-`core.py` checks, and add a compiled-core regression proving `bool`, `IntEnum`, int subclasses, float, str, and coercible values are rejected before mutation. Verify ownership wrappers remain one-entry and mypyc-compatible.

### `tests/test_hypothesis.py` (property test, batch/transform)

**Analog:** `fsm_with_transitions` and `build_fsm` (`:28-60`) plus deterministic runtime invariants (`:68-95`). Keep existing legacy runtime strategy free of grouped slots until Phase 22. Add a separate registration-only permutation property that builds equivalent plans in different orders and compares canonical priority/identity fingerprints; include only valid distinct priorities so the property tests topology construction, not winner selection.

## Shared Patterns

### Validate → stage → publish

**Sources:** `src/fast_fsm/core.py:1329-1428`, `tests/test_graph_invariants.py:162-212`. Normalize every request, merge all replacements in a temporary map, and publish only after the complete operation succeeds. One changed operation means exactly one `_graph_version` increment; all duplicates or all failures leave version and slot identities untouched.

### Ownership and clone isolation

**Sources:** `src/fast_fsm/core.py:842-856,1256-1303,2469-2500`, `tests/test_ownership_concurrency.py:234-330`. Use one per-machine non-reentrant ownership envelope for writes and an owner-aware read boundary for clone/snapshot capture. Share immutable values but copy outer/per-source dictionaries and ownership primitives.

### Slots and compiled boundary

**Sources:** `src/fast_fsm/core.py:579-635`, `tests/test_mypyc_guard.py:382-434,701-753,1289-1328`. Keep hot-path values slotted, private records frozen, and `core.py` as the only compiled module. Validate exact priority type at an `object` boundary before mypyc narrowing; preserve interpreted condition subclassability.

## No Analog Found

| File/construct | Role | Data Flow | Reason |
|---|---|---|---|
| Private immutable candidate-group record/merge helper | model/utility | CRUD/transform | No existing multi-candidate slot exists; copy `_GraphTransition`/`_GraphSnapshot` frozen-slotted tuple conventions and the staged `_commit_transition_plan` transaction. |
| Priority-specific ADR | architecture decision | static contract | No existing priority decision; use ADR-006's append-only decision format. |

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `.specify/memory`, `.specify/decisions`, `tests/test_graph_invariants.py`, `tests/test_ownership_concurrency.py`, `tests/test_builder.py`, `tests/test_mypyc_guard.py`, and `tests/test_hypothesis.py`.  
**Files scanned:** 9 primary files plus policy/decision references.  
**Pattern extraction date:** 2026-09-06

## PATTERN MAPPING COMPLETE

