# Phase 30: Builder-First Construction & Persistence Parity - Pattern Map

**Mapped:** 2026-09-17
**Files analyzed:** 15 anticipated implementation, test, typing, and documentation surfaces
**Analogs found:** 14 / 15 (the parity oracle is a new test seam with direct analogs)

## File Classification

| New/Modified File or Responsibility | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| src/fast_fsm/core.py — declarative import, deprecation workers, dictionary mode, clone/snapshot parity | component / construction adapter | batch transform to atomic publication; event-driven runtime unchanged | _TransitionRequest, _apply_transition_requests_owned, and FSMBuilder.build | exact architectural seam |
| src/fast_fsm/core.pyi — decorator and retained helper signatures | config / public type contract | request-response typing | existing transition, FSMBuilder, simple_fsm, quick_fsm declarations | exact |
| src/fast_fsm/__init__.py — compatibility exports | provider / package surface | request-response import surface | explicit imports and __all__ | exact |
| tests/test_builder.py — declarative import and warning behavior | test / component integration | batch construction plus event-driven dispatch | builder publication and declarative suites | exact |
| tests/test_advanced_functionality.py — dictionary round trips and warning helpers | test / adapter integration | dict/JSON transform to machine | TestFromDict, TestToDict, TestPrioritySerialization | exact |
| tests/test_final_states.py — final-state adapter and clone semantics | test / model invariant | state/topology transform | final-source and construction-surface tests | role-match |
| tests/test_transition_modes.py — declarative/internal lifecycle parity | test / event-driven behavior | event-driven | internal lifecycle tests | exact |
| tests/test_graph_invariants.py — canonical convergence, atomicity, no-bypass guards | test / structural invariant | batch publication and static source analysis | canonical transaction and hot-path tests | exact |
| tests/test_mypyc_guard.py — frozen metadata fields and pure/native closure | test / structural/native harness | build artifact and source-origin verification | AST field-set and native semantic probes | exact |
| tests/test_construction_parity.py (if introduced) — shared adapter oracle | test / integration oracle | batch transform plus event-driven replay | builder fingerprints and pure/native probes | new seam; use existing helpers |
| README.md, docs/QUICK_START.md, docs/api/core.md, docs/dev/architecture.md — focused construction/deprecation guidance | documentation / guide | request-response | construction tables, autodoc, architecture contract | role-match |
| .specify/memory/spr-core-api.md — living public construction contract | model/documentation | contract projection | existing additive API bullets | role-match |

## Pattern Assignments

### src/fast_fsm/core.py — canonical construction and adapter convergence

**Primary analogs:** src/fast_fsm/core.py:823-862, 1890-2073, 2118-2251, 6568-6646.

This is a cold-path adapter change. Keep all new adapter data in the existing immutable carrier and route it through the one prepare-all/publish-once seam. Do not create a declarative registrar or second normalization path.

**Canonical request carrier** (src/fast_fsm/core.py:823-847):

~~~python
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
    internal: Any = False

def _freeze_transition_sources(...):
    if isinstance(sources, list):
        return tuple(iter(sources))
    return (sources,)
~~~

Preserve raw Any/object implementation fields until exact validation, especially internal; mypyc must not narrow an untrusted serialized/decorator value before type(value) is bool. Preserve frozen/slotted carriers and copy plural sources at the boundary.

**Normalization and atomic publication** (src/fast_fsm/core.py:1890-2073):

~~~python
def _apply_transition_requests_owned(self, requests, *, error_contexts=None):
    if not isinstance(requests, tuple):
        raise TypeError("transition request collection must be a tuple")
    for request in requests:
        if not isinstance(request, _TransitionRequest):
            raise TypeError("each transition request must be _TransitionRequest")
    prepared = []
    for index, request in enumerate(requests):
        try:
            prepared.append(self._normalize_transition_request(...))
        except (TypeError, ValueError) as error:
            if error_contexts is None:
                raise
            raise type(error)(f"{error_contexts[index]} {error}") from None
    self._commit_transition_plan(tuple(prepared))
~~~

_normalize_transition_request owns canonical endpoint identity, exact priority/mode checks, final-source rejection, internal self-target validation, timing, condition normalization, and async compatibility. _commit_transition_plan builds replacement slots off-table and increments _graph_version only after successful publication. New adapters should only parse/bind requests and call _apply_transition_requests_owned once.

**Builder candidate transaction** (src/fast_fsm/core.py:6568-6646):

~~~python
if self._machine is not None:
    return self._machine
candidate = candidate_type(self._initial_state, **self._machine_kwargs)
for state in self._states.values():
    if state is not self._initial_state:
        candidate.add_state(state)
bound_requests = []
for staged in self._transitions:
    # bind names to exact staged State identities
    bound_requests.append(_TransitionRequest(...))
candidate._apply_transition_requests_owned(tuple(bound_requests))
# wire callbacks only after topology succeeds
...
self._machine = candidate
return candidate
~~~

Declarative requests should be derived afresh inside this build-time transaction from immutable handler metadata, concatenated with explicit bound requests, and submitted in the same one call. Never append derived rows to self._transitions; a failed build must leave the builder inspectable and repairable, while a successful build remains cached/frozen by _machine and _ensure_mutable.

**Factory adapter pattern** (src/fast_fsm/core.py:1273-1359): quick_build first collects caller-owned State identities, creates only unresolved string endpoints, constructs a private candidate, translates the complete input with _transition_requests_from_rows, then calls _apply_transition_requests_owned(requests). It does not call public add_transition/add_transitions in a loop. Reuse this pattern for retained helpers and keep classmethod result types by using cls or private classmethod workers.

**Declarative metadata and handler resolution** (src/fast_fsm/core.py:5588-5665, 5891-5990):

~~~python
declarations = tuple(getattr(func, "_fsm_declarations", ()))
declarations += (_DeclarativeHandlerMetadata(...),)
func._fsm_declarations = declarations
...

handlers = source_state._handlers.get(trigger, ())
return tuple(
    handler for handler in handlers
    if _metadata_matches_state(handler.from_state, source_state.name)
    and (... target match ...)
    and (priority is None or handler.priority == priority)
)
~~~

Extend both _DeclarativeHandlerMetadata and _DeclarativeHandler with internal; deep-freeze plural source constraints before storing them; include mode in declarative identity/matching. The machine-owned resolver must match source, trigger, target, priority, and internal, while direct handle_event compatibility calls may omit mode only when the declaration is unambiguous. Generated topology requests must leave the declaration guard on _DeclarativeHandler.condition rather than copying it into _TransitionRequest.condition: runtime selection already evaluates entry and declarative guards in distinct seams, so copying would execute it twice. Preserve _invoke_declarative_handler_for_transition* as the exactly-once lifecycle boundary.

**Deprecation wrapper pattern:** Current nesting at src/fast_fsm/core.py:1198-1359, 6956-7012 is the negative analog: simple_fsm calls warning-target from_states, and quick_fsm calls warning-target quick_build. Replace this with a private non-warning worker shared by the public boundaries. Each of from_states, quick_build, simple_fsm, and quick_fsm should warn exactly once, first, with a fixed bounded DeprecationWarning and stacklevel=2, then delegate to the worker. Do not warn in direct constructors, from_dict, State.create, builder methods, declarative classes, or dispatch. Preserve cls/subclass behavior in classmethod workers.

**Persistence adapter pattern** (src/fast_fsm/core.py:1362-1709):

~~~python
raw_transitions = config.get("transitions", [])
...
for index, entry in enumerate(raw_transitions):
    if not isinstance(entry, dict):
        raise TypeError(f"from_dict: transition[{index}] must be a dictionary")
    # validate required fields, sources, priority, timing, condition_ref
    parsed_rows.append((index, trigger, sources, target, priority, ...))
...
canonical_states = {... State(name, final=...) ...}
fsm = cls(canonical_states[initial], ...)
...
requests.append(_TransitionRequest(...))
fsm._apply_transition_requests_owned(
    tuple(requests),
    error_contexts=tuple(f"from_dict: transition[{index}]" for index, *_ in parsed_rows),
)
~~~

Keep parsing local and complete before publication. Add exact built-in container/scalar validation for internal, accept omitted/explicit False as external, and emit only internal: True from to_dict. Continue to resolve only opaque condition references; never serialize executable callbacks or exception payloads. Let canonical normalization enforce final-source and internal-self constraints rather than repairing after publication. Compatibility is directional: old payloads read as defaults; old readers may silently lose new additive semantics.

**Clone and snapshot patterns** (src/fast_fsm/core.py:3578-3711):

~~~python
def snapshot(self):
    return {"state": self._current_state.name, "version": 1}

def _clone_owned(self):
    new_fsm = self.__class__(self._initial_state, name=self._name, clock=self._clock)
    new_fsm._states = dict(self._states)
    new_fsm._transitions = {state_name: {} for state_name in self._states}
    requests = []
    for source_name, triggers in self._transitions.items():
        for trigger, slot in triggers.items():
            for entry in _transition_entries(slot):
                requests.append(_TransitionRequest(..., internal=entry.internal))
    new_fsm._apply_transition_requests_owned(tuple(requests))
    new_fsm._graph_version = self._graph_version
    new_fsm._state_exit_callbacks = {k: list(v) for k, v in ...}
    ...
    new_fsm._history = None
    return new_fsm
~~~

Retain state-only snapshot v1 exactly; finality/mode after restore come from the receiving machine's canonical state/topology. Clone should preserve concrete sync/async class, canonical state/subclass and callable identities, final/internal metadata, but rebuild independent transition tables, candidate entries/groups, callback/listener containers, ownership primitives, and reset to initial state with history disabled.

### src/fast_fsm/core.pyi and src/fast_fsm/__init__.py — public contract

**Analogs:** src/fast_fsm/core.pyi:371-479 and src/fast_fsm/__init__.py:7-111.

Keep runtime/stub synchronized. Add keyword-only internal: bool = False to transition and preserve exact FSMBuilder.add_transition typing. Retain all deprecated helper names and signatures through v0.5.x. Package exports are explicit imports plus __all__; do not remove helpers or add a second builder export. The public stub can advertise the intended type while runtime implementation accepts object for exact validation.

### tests/test_builder.py — declarative import, builder reuse, warnings

**Analogs:** helpers at tests/test_builder.py:80-170, builder transaction tests at 170-355 and 2040-2305, declarative tests at 503-905, and cross-adapter comparison around 1120-1160.

Use real states, conditions, and handlers; this file documents “no mocking.” Preserve the established fingerprints for atomicity and identity:

~~~python
def builder_staging_fingerprint(builder):
    return (
        tuple((name, id(state)) for name, state in builder._states.items()),
        tuple((request.trigger, request.sources, request.to_state,
               id(request.condition), request.priority, request.internal)
              for request in builder._transitions),
        builder._machine_type, builder._auto_detect,
        id(builder._machine) if builder._machine is not None else None,
    )
~~~

Extend for declarative-only builder topology (no manual mirror rows), exact-once guard/handler counters, mode-aware declarations, stacked/plural immutable source metadata, async auto-detection, explicit-sync rejection, explicit/declarative conflicts, failed-build repair, cached build, and one warning per deprecated public invocation. Capture warnings with pytest.warns or warnings.catch_warnings(record=True); assert category, exact bounded message, caller filename/line, count, and unchanged result behavior. Reuse the repair idiom: capture staging fingerprint, assert _machine is None after failure, repair staged state/row, build successfully.

### tests/test_advanced_functionality.py — dictionary/clone/snapshot adapter tests

**Analogs:** TestFromDict (1348-1510), TestToDict (1511-1595), TestClone (965-1110), TestSnapshot (857-963), and TestPrioritySerialization (2227-2410).

Follow the current round-trip style: construct JSON-native config, call from_dict, trigger, export with to_dict, run json.dumps/json.loads, reconstruct, and assert behavior—not only dictionary equality. Add legacy omission/defaults, true-only internal output, explicit false input, exact bool/type negatives with indexed messages, final/internal atomic failure and graph version, and condition-ref identity. For clone, assert initial reset, concrete async type, shared state/callable identity but independent tables/lists, final/internal entry fidelity, and history disabled. For snapshots, assert exactly {"state": ..., "version": 1} and receiver-owned termination/mode after restore.

### tests/test_final_states.py and tests/test_transition_modes.py — semantic regression surfaces

**Analogs:** final construction matrix and atomic graph checks in tests/test_final_states.py:79-221; internal lifecycle/result/async tests in tests/test_transition_modes.py:90-220, 342-470, 546-670, 799-833.

Keep these files focused on observable behavior. Add adapter parity cases proving final-source rejection and internal self-target validation are identical through builder, declarative, helper, clone, and from_dict; do not duplicate normalization logic in tests. For internal declarations, assert selected TransitionResult.internal, history mode, lifecycle omission, handler count, and sync/async equivalence. Reuse existing stateful event trace lists and pytest.mark.asyncio patterns.

### tests/test_graph_invariants.py — transaction and no-bypass structural patterns

**Analog:** test_retained_transition_adapters_use_the_canonical_request_transaction at lines 310-354, canonical atomicity at 456-595 and 763-887, and hot-path exclusion at 1028-1050.

Use source slicing and graph fingerprints for structural guarantees:

~~~python
for adapter_source in regions:
    assert "_TransitionRequest" in adapter_source
    assert adapter_source.count("_apply_transition_requests_owned") == 1
    assert "_commit_transition_plan" not in adapter_source
~~~

Extend the adapter region set to cover declarative builder derivation and private compatibility workers. Assert declaration import and warning code are absent from selector/lifecycle regions; assert no post-publication repair. Preserve tests proving graph version and published slots do not change on late failures, tie conflicts, foreign identities, final-source rows, or invalid internal values. This is the strongest analog for BUILD-06 and the structural home for one canonical seam.

### tests/test_mypyc_guard.py — frozen layout and pure/native evidence

**Analog:** test_private_graph_records_are_frozen_slot_dataclasses at tests/test_mypyc_guard.py:490-590, exact TransitionEntry field assertions immediately after it, and pure/native semantic probes around lines 2434+ and 2599+.

Update exact AST field sets for _DeclarativeHandlerMetadata and _DeclarativeHandler when internal is added; retain frozen=True, slots=True, and exact TransitionEntry field order. Keep core.py as the only compiled unit and reuse the existing source-origin/native-shadow restoration harness. Add Phase 30's parity scenario to the same semantic oracle used in pure source and fresh native runs. Do not create a parallel compilation harness or leave a native core shadow in the source tree.

### tests/test_construction_parity.py (optional new file) — central parity oracle

No exact existing file; closest analogs are builder_staging_fingerprint and _machine_topology_fingerprint in tests/test_builder.py:88-170, cross-adapter construction around tests/test_builder.py:1120-1160, and tests/test_mypyc_guard.py pure/native probes.

If a dedicated file is created, make it a small reusable test oracle rather than a new production fixture framework. Build equivalent topology through direct, batch, builder, deprecated helper, declarative, callback-state, clone, and deserialization adapters; compare selected state, finality, internal/external lifecycle, priority, history, callbacks, graph version, atomic failure, and identity rules. Keep inputs executable in pure and native modes. If no file is created, isolate the same helpers in tests/test_builder.py and reference existing source-origin commands.

### Documentation surfaces — builder-first hierarchy and bounded migration

**Analogs:** construction table/examples in README.md:1-150, Quick Start recipes in docs/QUICK_START.md:1-90, autodoc/API guidance in docs/api/core.md:1-80, and architecture invariants in docs/dev/architecture.md (especially Canonical Topology and builder paragraphs).

Phase 30 should make focused API/deprecation corrections only; the full progressive rewrite belongs to Phase 32. Lead the ordinary recipe with FSMBuilder, describe direct StateMachine/AsyncStateMachine construction as advanced, and describe from_dict as serialized topology reconstruction. Move deprecated helpers to compatibility/migration sections with replacement and v0.5.x support timing. Keep examples executable with existing Sphinx testcode/testoutput conventions where applicable. Do not claim symmetric old-reader compatibility: old payloads read by new versions retain defaults, while pre-v0.5 readers may ignore additive final/internal metadata.

### .specify/memory/spr-core-api.md — living API contract

**Analog:** existing additive construction/runtime bullets in .specify/memory/spr-core-api.md (builder caching, canonical request transaction, clone/snapshot, and current serialization notes).

Update the living contract in the same public-API change set. Record builder-first positioning, direct construction as advanced, from_dict as persistence adapter, warning cycle/removal floor, declarative import through _TransitionRequest, true-only internal serialization, directional compatibility, clone preservation/isolation, and unchanged snapshot v1. Keep this file normative and concise; implementation detail belongs in docs/dev/architecture.md.

## Shared Patterns

### One canonical normalization/publication seam

**Sources:** src/fast_fsm/core.py:1890-2073; tests/test_graph_invariants.py:310-354 and 763-887.

**Apply to:** every adapter in core.py, including direct/batch, builder, declarative import, factories, callbacks, clone, and from_dict.

~~~text
raw adapter input
  -> immutable _TransitionRequest tuple
  -> _normalize_transition_request for exact endpoint/final/mode/timing/guard rules
  -> _PreparedTransition tuple
  -> _commit_transition_plan replacement slots
  -> one graph-version advance after publication
  -> runtime dispatch (unchanged)
~~~

No adapter may call _commit_transition_plan directly, normalize only a prefix, mutate a published slot, or repair semantics after publication.

### Cold-path only

**Sources:** builder build at src/fast_fsm/core.py:6568-6646; runtime exclusion at tests/test_graph_invariants.py:1028-1050; performance/slots rules in .github/copilot-instructions.md:40-59.

Apply to declaration discovery, warning emission, parsing, cloning, and validation. Keep request import, warnings, reflection, and compatibility branching out of selectors, lifecycle, and trigger hot-path regions. Direct singleton dispatch remains dictionary lookup/O(1); grouped selection scans only its local immutable candidates.

### Exact validation and bounded errors

**Sources:** _normalize_priority and _normalize_transition_request at src/fast_fsm/core.py:778-786 and 1890-2002; indexed from_dict errors at src/fast_fsm/core.py:1480-1545.

Use exact built-in checks for priority, mode, serialized containers/scalars, and immutable source constraints. Prefix deserialization errors with stable indexed context, never include caller payload reprs or executable callback details, and validate everything before publication.

### Identity and container ownership

**Sources:** builder state registration at src/fast_fsm/core.py:6298-6332; clone at src/fast_fsm/core.py:3659-3711; graph identity tests at tests/test_graph_invariants.py:205-307.

Retain caller-owned State and callable identities where promised. Copy source lists, candidate groups, transition dictionaries, callback/listener registries, and ownership primitives. Same object/name is idempotent; a different object with the same name is rejected atomically.

### Sync/async and pure/native parity

**Sources:** builder async preflight at src/fast_fsm/core.py:6517-6566; async clone runtime/stub at src/fast_fsm/core.py:4532-4760; native probes in tests/test_mypyc_guard.py.

Use the same topology oracle for sync/async classes and asserted pure/fresh compiled origins. Async detection traverses existing supported condition wrappers and declarative handlers. Do not introduce hidden bridging or a second native harness.

### Public compatibility cycle

**Sources:** exports src/fast_fsm/__init__.py:75-111, signatures src/fast_fsm/core.pyi:467-479, wrappers src/fast_fsm/core.py:6956-7012.

Keep deprecated symbols exported, typed, and behaviorally correct throughout v0.5.x. Emit one fixed DeprecationWarning at stacklevel=2 per public invocation; private workers prevent nested warnings. Earliest removal is v0.6.0.

## No Analog Found

| File / Responsibility | Role | Data Flow | Reason |
|---|---|---|---|
| tests/test_construction_parity.py if introduced | integration test oracle | adapter transform to runtime replay to pure/native replay | No dedicated all-adapter semantic oracle exists; compose builder fingerprints, graph invariants, serialization tests, and native probes listed above. |

## Metadata

**Analog search scope:** src/fast_fsm/core.py, src/fast_fsm/core.pyi, src/fast_fsm/__init__.py, relevant tests, README/docs, .specify/memory/spr-core-api.md, and Phase 26-29 artifacts.
**Files scanned:** 15 primary code/test/doc surfaces plus Phase 30 context, research, and validation.
**Pattern extraction date:** 2026-09-17

