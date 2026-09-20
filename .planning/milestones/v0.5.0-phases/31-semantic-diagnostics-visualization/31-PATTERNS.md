# Phase 31: Semantic Diagnostics & Visualization - Pattern Map

**Mapped:** 2026-09-19  
**Files analyzed:** 20 anticipated implementation, test, typing, and documentation surfaces  
**Analogs found:** 20 / 20

## File Classification

| New/Modified File or Responsibility | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` — snapshot fields, result/history, sync/async trace | component / model | event-driven runtime + snapshot transform | `_GraphSnapshot`, `_GraphTransition`, `_emit_fsm_trace()` | exact |
| `src/fast_fsm/core.pyi` — private snapshot/public trace/result types | config / typing | request-response | runtime dataclasses and methods | exact |
| `src/fast_fsm/_diagnostics.py` — scalar graph and predicates | utility / service | transform and bounded graph queries | `_DiagnosticGraph`, `_graph_from_snapshot()`, `_DiagnosticBudget` | exact |
| `src/fast_fsm/validation.py` — final/sink reports and scoring | service / validator | batch graph analysis | `FSMValidator`, `EnhancedFSMValidator` | exact |
| `src/fast_fsm/visualization.py` — Mermaid, PlantUML, JSON, document | utility / renderer | transform and text/file I/O | private from-snapshot renderers and JSON builder | exact |
| `tests/test_diagnostic_contracts.py` — snapshot, mutation, JSON, budgets | test | bounded graph transform | capture and exact-budget tests | exact |
| `tests/test_validation.py` — dead-state compatibility and scoring | test | batch graph analysis | validator test classes | exact |
| `tests/test_visualization.py` — markers, fields, serializability | test | text/JSON transform | PlantUML and JSON classes | exact |
| `tests/test_output_safety.py` — hostile text, barriers, row budgets | test | bounded text I/O | hostile corpus and renderer limits | exact |
| `tests/test_logging_config.py` — sync/async trace/redactor | test | event-driven logging | metadata-only and priority trace tests | exact |
| `tests/test_expected_rejection.py` — rejection code/result boundaries | test | event-driven request-response | result and approved-boundary matrix | role-match |
| `tests/test_transition_modes.py` — internal/external mode result/history | test | event-driven | self-transition lifecycle tests | exact |
| `tests/test_final_states.py` — explicit final versus non-final sink | test | state/model invariant | final metadata/termination tests | exact |
| `tests/test_mypyc_guard.py` — frozen fields and pure/native parity | test / structural guard | build artifact and transform parity | diagnostic and trace AST tests | exact |
| `docs/api/core.md` — rejection/result/trace contract | documentation / API | request-response | existing rejection and trace sections | role-match |
| `docs/api/validation.md` — bounded reports and topology semantics | documentation / API | batch analysis | bounded diagnostics section | role-match |
| `docs/api/visualization.md` — snapshot, budget, escaping | documentation / API | text/JSON transform | renderer contract section | role-match |
| `.specify/memory/spr-core-api.md` — living runtime/trace contract | documentation / model | contract projection | existing finality/mode/trace bullets | role-match |
| `.specify/memory/spr-validation.md` — living validator contract | documentation / model | batch graph analysis | existing ledger/score bullets | role-match |
| `.specify/memory/spr-visualization.md` — living renderer contract | documentation / model | text/JSON transform | existing renderer/escaping bullets | role-match |

## Pattern Assignments

### `src/fast_fsm/core.py` (component/model, event-driven runtime + snapshot transform)

**Analogs:** `core.py:633-708, 821-857, 1900-1958, 2534-2540, 307-367, 4472-4492, 5581-5603`.

Keep runtime dispatch free of `_diagnostics` imports. Finality remains a direct current-state read; do not add a cached finality field to a result or history record.

**Result/history carrier** (`core.py:633-708`):

~~~python
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
    internal: bool = field(default=False, compare=False)
    rejection_code: Optional[str] = field(default=None, compare=False)

    @property
    def rejected(self) -> bool:
        return self.rejection_code is not None

class TransitionRecord:
    __slots__ = (
        "from_state", "trigger", "to_state", "timestamp",
        "priority", "internal",
    )
~~~

The authoritative runtime query is:

~~~python
@property
def is_terminated(self) -> bool:
    """Return whether the canonical current state is explicitly final."""
    return self._current_state.final
~~~

**Immutable graph carrier/capture** (`core.py:821-857, 1921-1958`):

~~~python
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
    internal: bool = False

@dataclass(frozen=True, slots=True)
class _GraphSnapshot:
    name: str
    initial_state: "State"
    graph_version: int
    states: Tuple["State", ...]
    transitions: Tuple[_GraphTransition, ...]
    initial_state_name: str
    current_state_name: str
    state_names: Tuple[str, ...]
~~~

~~~python
states = tuple(state for _, state in sorted(self._states.items()))
state_names = tuple(state.name for state in states)
transitions: List[_GraphTransition] = []
for from_name, entries in sorted(self._transitions.items()):
    source_state = self._states[from_name]
    for trigger, slot in sorted(entries.items()):
        for entry in _transition_entries(slot):
            transitions.append(
                _GraphTransition(
                    source_state, trigger, entry.to_state,
                    entry.condition, source_state.name, entry.to_state.name,
                    entry.condition.name if entry.condition is not None else None,
                    entry.priority, entry.condition_ref, entry.after, entry.within,
                    entry.condition is None and type(source_state) is State,
                    entry.internal,
                )
            )
return _GraphSnapshot(
    self._name, self._initial_state, self._graph_version, states,
    tuple(transitions), self._initial_state.name, self._current_state.name,
    state_names,
)
~~~

Extend this ownership-boundary capture with scalar final flags parallel to `state_names`; let diagnostics copy them. Never reread live `State.final` after capture.

**Trace helper** (`core.py:307-367`):

~~~python
if not logger.isEnabledFor(_FSM_TRACE_LEVEL):
    return

trace_fields: Dict[str, object] = {
    "trace_operation": operation,
    "trace_stage": stage,
    "trace_result": result,
    "trace_arg_count": len(positional_args),
    "trace_keyword_names": _trace_keyword_names(keyword_args),
    "trace_priority": priority,
}
~~~

Add only bounded scalar rejection code/mode/known-finality fields. Preserve the fixed fallback:

~~~python
trace_fields = {
    "trace_operation": "redaction_failure",
    "trace_stage": "redaction_failure",
    "trace_result": "failure",
    "trace_arg_count": 0,
    "trace_keyword_names": (),
    "trace_priority": None,
}
~~~

Both public trigger boundaries (`4472-4492`, `5581-5603`) call the same helper after the owned result and release ownership in `finally`. Keep sync/async additions synchronized; use `None` for unknown finality.

### `src/fast_fsm/core.pyi` (config/typing, request-response)

**Analog:** `core.pyi:76-140`, matching `core.py:821-857, 633-650`.

The stub’s frozen/slotted graph records already mirror runtime mode:

~~~python
@dataclass(frozen=True, slots=True)
class _GraphTransition:
    from_state: State
    trigger: str
    to_state: State
    condition: Condition | None
    from_state_name: str
    to_state_name: str
    condition_name: str | None
    priority: int
    condition_ref: str | None = ...
    after: float | None = ...
    within: float | None = ...
    statically_unconditional: bool = ...
    internal: bool = ...

@dataclass(frozen=True, slots=True)
class _GraphSnapshot:
    name: str
    initial_state: State
    graph_version: int
    states: tuple[State, ...]
    transitions: tuple[_GraphTransition, ...]
    initial_state_name: str
    current_state_name: str
    state_names: tuple[str, ...]
~~~

Add any new scalar snapshot/trace field in the same order/type in runtime and stub. Keep result/history fields `priority`, `internal`, and `rejection_code`; do not invent a finality carrier.

### `src/fast_fsm/_diagnostics.py` (utility/service, graph transform + bounded analysis)

**Analogs:** `_diagnostics.py:80-227, 438-532, 535-583`.

This interpreted stdlib-only module is the cold projection boundary. Current records and projection are:

~~~python
@dataclass(frozen=True, slots=True)
class _DiagnosticEdge:
    from_index: int
    trigger: str
    to_index: int
    condition_name: str | None
    priority: int
    has_guard: bool
    statically_unconditional: bool

@dataclass(frozen=True, slots=True)
class _DiagnosticGraph:
    state_names: tuple[str, ...]
    edges: tuple[_DiagnosticEdge, ...]
    forward: tuple[tuple[int, ...], ...]
    reverse: tuple[tuple[int, ...], ...]
    initial_index: int | None
    initial_state_name: str
    current_state_name: str
    graph_version: int
~~~

~~~python
state_names = snapshot.state_names
state_indices = {name: index for index, name in enumerate(state_names)}
edges = tuple(
    _DiagnosticEdge(
        state_indices[transition.from_state_name],
        transition.trigger,
        state_indices[transition.to_state_name],
        transition.condition_name,
        transition.priority,
        transition.condition is not None,
        transition.statically_unconditional,
    )
    for transition in snapshot.transitions
)
forward_lists: list[list[int]] = [[] for _ in state_names]
reverse_lists: list[list[int]] = [[] for _ in state_names]
for edge_index, edge in enumerate(edges):
    forward_lists[edge.from_index].append(edge_index)
    reverse_lists[edge.to_index].append(edge_index)
~~~

Copy final flags beside `state_names` and `internal` from each transition into the scalar edge. Define explicit-final indices, topology sinks (`not forward[index]`), and non-final sinks once here; validators, JSON, and renderers consume those predicates.

**Budget:** `_DiagnosticBudget.reserve_work()`, `reserve_result()`, and `_reserve()` (`144-194`) reserve before allocation/append:

~~~python
if current + amount > limit:
    self._complete = False
    self._exhausted_dimension = dimension
    self._exhausted_stage = stage
    raise DiagnosticBudgetExceeded(self.status)
setattr(self, counter_name, current + amount)
~~~

Keep dense/supplied adjacency compatibility shape. Canonical JSON transition rows are the safest mode-bearing surface; enriching dense rows requires coordinated validation and exact-shape updates.

### `src/fast_fsm/validation.py` (service/validator, bounded batch analysis)

**Analogs:** `validation.py:118-173, 220-362, 722-858, 991-1064`.

Construction is one snapshot and one ledger:

~~~python
self._initialize_from_snapshot(
    fsm,
    fsm._graph_snapshot(),
    name=name,
    budget=_DiagnosticBudget(limits),
)
self._diagnostic_graph = _graph_from_snapshot(self._snapshot)
self._budget = budget
self._extract_fsm_structure()
~~~

Preserve topology-oriented `find_dead_states()`:

~~~python
for state_index, state_name in enumerate(self._diagnostic_graph.state_names):
    budget.reserve_work(stage="dead-state.visit")
    if not self._diagnostic_graph.forward[state_index]:
        budget.reserve_result(stage="dead-state.result")
        dead_states.append(state_name)
~~~

`validate_completeness()` currently emits `dead_states`, `has_dead_states`, missing transitions, and shared status (`307-362`). Keep those meanings and add separately named explicit-final/non-final-sink values. In `EnhancedFSMValidator._analyze_completeness()` (`810-858`), skip intentional finals before dead-end/missing-transition issue creation; retain non-final sink warnings. In `get_validation_score()` (`991-1064`), remove only the intentional-final issue from structural/completeness counts while preserving design style, grade, blend, and status.

### `src/fast_fsm/visualization.py` (utility/renderer, bounded text and JSON)

**Analogs:** `visualization.py:47-113, 115-237, 338-479, 560-578, 586-652, 705-860`.

Capture once and append only after reserve:

~~~python
def _capture_diagnostic_graph(fsm, limits):
    snapshot = fsm._graph_snapshot()
    return snapshot, _graph_from_snapshot(snapshot), _DiagnosticBudget(limits)

def _append_rendered_line(lines, budget, *, stage, line):
    budget.reserve_result(stage=stage)
    lines.append(line)
~~~

Keep opaque `s{snapshot_position}` IDs and the existing Mermaid/PlantUML/Markdown escapers. Add completion markers only for explicit-final indices. Add fixed `internal` or `external self` labels only for same-state edges; preserve trigger, guard name, priority, and ordinary non-self arrows.

Current edge loop (Mermaid, `152-166`) is the direct analog:

~~~python
for edge in graph.edges:
    budget.reserve_work(stage="mermaid.edge")
    label = _transition_label(
        edge.trigger, edge.condition_name, edge.priority,
        show_conditions=show_conditions, escape=_escape_mermaid_text,
    )
    _append_rendered_line(
        lines, budget, stage="mermaid.edge",
        line=f"    {state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}",
    )
~~~

Current JSON loop (`432-444`) keeps topology/analysis separate and reserves per row. Add final/non-final sink facts and per-edge string mode without replacing `terminal`, `from`, `to`, `has_guard`, or `priority`. Keep document composition through `_to_mermaid_fenced_from_snapshot()` (`705-747`) with no recapture.

### `tests/test_diagnostic_contracts.py` (test, snapshot transform + budgets)

**Analogs:** `test_diagnostic_contracts.py:45-160, 189-243, 246-280, 814-880`.

Reuse real fixtures and the mutation barrier:

~~~python
snapshot = machine._graph_snapshot()
initial.name = "initial-mutated"
middle.name = "middle-mutated"
condition.name = "condition-mutated"
assert snapshot.state_names == ("initial", "middle", "orphan")
assert snapshot.transitions[0].condition_name == "condition-label"
~~~

Extend this exact oracle with captured final flags/edge mode, one-capture validator/JSON assertions, and output truth after late mutation. Use `_assert_exact_budget()` (`163-186`) for exact/one-less work/results and preserve scalar-only `DiagnosticBudgetExceeded.status`.

### `tests/test_validation.py` (test, bounded batch graph analysis)

**Analogs:** `test_validation.py:44-104, 130-182, 349-429, 556-623, 781-795`.

Keep the fixture and legacy topology style:

~~~python
def test_dead_states_detected(self, problematic_fsm):
    v = FSMValidator(problematic_fsm)
    dead = v.find_dead_states()
    assert "error" in dead
    assert "orphaned" in dead

def test_validate_completeness_defaults_to_sparse_adjacency(self, well_designed_fsm):
    result = FSMValidator(well_designed_fsm).validate_completeness()
    assert "sparse_adjacency" in result
    assert "transition_matrix" not in result
    assert result["diagnostic_status"].complete is True
~~~

Add explicit-final, non-final-sink, unreachable, and initial-final/no-edge cases. Assert `dead_states` and sparse/dense matrix shapes remain compatible; finals do not create completeness warnings/errors or score penalties, while ordinary sinks remain reportable. Keep guards uncalled and capture count one.

### `tests/test_visualization.py` (test, text rendering + JSON)

**Analogs:** `test_visualization.py:409-476, 483-531, 545-590`.

The existing PlantUML expectations are the direct semantic update point:

~~~python
def test_terminal_state_marked(self, simple_fsm):
    out = to_plantuml(simple_fsm)
    assert "s0 --> [*]" in out

def test_single_state_no_transitions(self):
    fsm = StateMachine(State("lonely"), name="Solo")
    out = to_plantuml(fsm)
    assert "[*] --> s0" in out
    assert "s0 --> [*]" in out
~~~

Change these to explicit-final-only markers and add Mermaid marker coverage. Add internal/external self labels, guard/priority preservation, JSON final/mode/non-final-sink fields, and serializability. Reuse `TestPriorityCandidateOutput` for every candidate row.

### `tests/test_output_safety.py` (test, bounded text/file I/O)

**Analogs:** `test_output_safety.py:150-193, 197-250, 471-517`.

Keep hostile corpus/containment helpers and the snapshot barrier:

~~~python
output = _render(renderer, machine, "")
assert calls == 1
assert "s0" in output and "s1" in output
_assert_physical_line_containment(renderer, output)
~~~

Every semantic label must use the existing language/Markdown escaper. Budget rows continue to reserve before append:

~~~python
output = renderer(machine, limits=DiagnosticLimits(max_results=required_results))
assert isinstance(output, str)
with pytest.raises(DiagnosticBudgetExceeded) as raised:
    renderer(machine, limits=DiagnosticLimits(max_results=required_results - 1))
assert raised.value.status.exhausted_dimension == "max_results"
assert raised.value.status.result_count == required_results - 1
~~~

Update required counts for final marker rows and cover raw, fenced, and composed documents.

### `tests/test_logging_config.py` (test, event-driven trace/redaction)

**Analogs:** `test_logging_config.py:415-477, 686-730, 736-789, 861-989, 999-1021`.

The custom redactor and priority tests are the direct pattern:

~~~python
def redactor(event: FSMTraceEvent) -> dict[str, object]:
    redactor_events.append(event)
    return {"priority": event.priority}

assert [event.priority for event in redactor_events] == [-8]
assert redacted_records[0]["trace_priority"] == -8
~~~

Extend event-field and default-record assertions for validated rejection code, selected mode/priority, and known current/source finality. Assert disabled trace returns before event/redactor work; sync and async key sets match; failure falls back to fixed metadata. Never expose exception text, payload, trigger text, callback repr, or unvalidated redactor data.

### `tests/test_expected_rejection.py` (test, result/trace boundary)

**Analogs:** `test_expected_rejection.py:67-130, 159-236, 350-388, 398-451`.

Use existing rejection facts as the trace projection source:

~~~python
assert result.rejected is True
assert result.rejection_code == "battery.low"
assert result.cause is None
assert result.committed is False
assert result.to_state is None
assert result.priority == -5
assert result.internal is False
~~~

Reuse the transition-guard/declarative-guard/state-permission matrix with both mode values. Outside-boundary lifecycle/timing signals remain ordinary failures and must not gain selector-only rejection metadata.

### `tests/test_transition_modes.py` (test, event-driven mode/history)

**Analogs:** `test_transition_modes.py:103-169, 270-303, 530-590, 664-717`.

Use lifecycle and staged-failure assertions as the diagram/JSON mode oracle:

~~~python
assert result.success is True
assert result.committed is True
assert result.internal is True
assert machine.history[-1].internal is True
assert events == ["before", "trigger-callback", "after"]
~~~

Internal self edges render as `internal`, external self edges as `external self`; non-self external edges keep established notation. Preserve selected priority/internal on staged failures and do not add finality to result/history.

### `tests/test_final_states.py` (test, state/model invariant)

**Analogs:** `test_final_states.py:23-76, 160-179, 269-300`.

The explicit-final/non-final-sink oracle is:

~~~python
done = State("done", final=True)
machine = StateMachine(done)
assert machine.is_terminated is True

sink = State("sink")
machine = StateMachine(sink)
assert machine.get_available_triggers() == []
assert machine.is_terminated is False
~~~

Use these fixtures for diagnostics. Preserve final-source construction and restore/clone tests proving current-state termination is canonical, not cached in a diagnostic carrier.

### `tests/test_mypyc_guard.py` (test, structural/native parity)

**Analogs:** `test_mypyc_guard.py:659-723, 1008-1072, 1176-1263, 737-800`.

This is the structural guard for frozen/slotted fields, no compiled-core import of diagnostics, no projection sorting, disabled trace before event construction, and one-truth-source finality:

~~~python
assert diagnostic_fields == {
    "from_index", "trigger", "to_index", "condition_name",
    "priority", "has_guard", "statically_unconditional",
}
assert "_diagnostics" not in core_source
assert "sorted(" not in projection_source
assert event_call.lineno > guard.lineno
~~~

Extend expected AST field sets and pure/native semantic values deliberately. Reuse the existing source-origin/native-shadow restoration harness.

### Documentation surfaces

**Analogs:** `docs/api/core.md:139-230`, `docs/api/validation.md:92-146`, `docs/api/visualization.md:31-77`, and SPR bullets at `.specify/memory/spr-core-api.md:8,72-78`, `spr-validation.md:7-34`, `spr-visualization.md:7-22`.

- **Core API:** document that results/history retain selected mode/priority/rejection, `is_terminated` reads canonical current state, and trace fields are bounded metadata; retain fail-closed wording and avoid promising cached result finality.
- **Validation API:** document `dead_states`/legacy `terminal` as topology-only, with separate explicit-final/non-final-sink facts, while retaining one snapshot, one ledger, sparse-first defaults, and fixed budget failure.
- **Visualization API:** document explicit-final-only completion markers and internal/external self labels while preserving opaque IDs, language-specific escaping, stable order, additive JSON keys, and supplied-matrix validation.
- **SPR memory:** update living core/validation/visualization bullets concisely in the same public-contract change; do not pull Phase 32 tutorial/performance claims into these files.

## Shared Patterns

### One owned snapshot, one scalar diagnostic graph

**Sources:** `core.py:1900-1958`; `_diagnostics.py:197-227`; `visualization.py:84-89`; `test_diagnostic_contracts.py:219-243`; `test_output_safety.py:197-235`.

Apply to validators, JSON, Mermaid, PlantUML, and documents:

~~~text
canonical state/transition tables
  -> owned _graph_snapshot() (names, final flags, edge internal scalars)
  -> _graph_from_snapshot() (_DiagnosticGraph indexed by snapshot order)
  -> one _DiagnosticBudget per top-level operation
  -> validator / JSON / diagram / document consumers
~~~

Never reread mutable State objects after capture, evaluate guards in diagnostics, or recapture inside composed renderers.

### Explicit finality versus topology sink compatibility

**Sources:** `core.py:944-971,2534-2540`; `validation.py:220-232,307-362`; `visualization.py:411-419`; `test_final_states.py:160-179`.

Keep `dead_states`/`terminal` as “no outgoing edge” facts. Add separately named explicit-final and non-final-sink facts. Explicit finals may have no outgoing edge and must not be warned/scored as defects; non-final sinks remain visible/non-terminated. Completion arrows use only explicit final flags.

### Reserve before work and output

**Sources:** `_diagnostics.py:144-194`; `visualization.py:107-113,152-166`; `test_output_safety.py:480-517`.

Every state/edge/field/marker/table row reserves before allocation or append. Exact limits succeed; one less raises fixed-message `DiagnosticBudgetExceeded` with scalar status and no partial payload.

### Fixed metadata-only trace

**Sources:** `core.py:250-367`; `test_logging_config.py:415-477,686-789`; `test_expected_rejection.py:350-388`.

Preserve the early disabled return. Default records may include only bounded scalar code/mode/priority/known-finality. Redactor output stays allowlisted and scalar; ordinary failures use fixed `redaction_failure`; process-control exceptions propagate without a record. Sync/async call sites and stubs agree.

### Opaque IDs and sink-specific escaping

**Sources:** `visualization.py:47-82`; `test_output_safety.py:150-193`; `docs/api/visualization.md:48-60`.

Keep `s{snapshot_position}` as the only diagram identity. Escape caller state, trigger, guard, title, and Markdown text immediately before output. Fixed semantic labels are constants and cannot carry caller syntax.

### Compatibility-shaped dense data and additive schemas

**Sources:** `_diagnostics.py:438-532`; `visualization.py:432-454,586-652`; `test_diagnostic_contracts.py:832-880`; `test_validation.py:468-483`.

Keep sparse/dense shapes and order unchanged unless matrix validation/tests are coordinated. Put required mode in canonical JSON transition rows first; add final/mode keys without removing legacy topology/analysis keys.

### Pure/native and stub/source parity

**Sources:** `core.py:821-857`; `core.pyi:76-140`; `test_mypyc_guard.py:659-723,1008-1072,1176-1263`.

Maintain frozen/slotted private records, keep diagnostics outside compiled core, update stubs with runtime fields, and extend the existing AST plus pure/native oracle. Do not add reflection/traversal/allocation to trigger hot paths.

## No Analog Found

None. Every anticipated Phase 31 surface has an existing role/data-flow analog. New field names and exact diagram wording remain discretionary, but their implementation should copy the seams above.

## Metadata

**Analog search scope:** `src/fast_fsm/`, focused `tests/`, `docs/api/`, `.specify/memory/`, and Phase 31 context/research/validation artifacts.  
**Files scanned:** 20 primary surfaces plus referenced project contracts and prior-phase artifacts.  
**Pattern extraction date:** 2026-09-19


