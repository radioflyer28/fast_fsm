# Phase 24: Candidate-Aware Diagnostics & Output - Pattern Map

**Mapped:** 2026-09-07  
**Files analyzed:** 10 expected implementation/documentation/test files  
**Analogs found:** 10 / 10 (all have strong live analogs)

Phase 24 should remain a cold-path diagnostics/output change. The runtime
singleton/group storage and sync/async selectors are already established by
Phases 21–23. The implementation should carry candidate identity from the
existing immutable snapshot through one scalar diagnostic edge, then let
validation and renderers consume that graph.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | component/model projection | event-driven + transform | `_GraphTransition`, `_graph_snapshot_owned()`, `_transition_entries()` | exact |
| `src/fast_fsm/_diagnostics.py` | utility/graph algorithm | transform + bounded traversal | `_DiagnosticEdge`, `_DiagnosticBudget`, adjacency/path helpers | exact |
| `src/fast_fsm/validation.py` | validator/report adapter | transform + report output | `FSMValidator`, `EnhancedFSMValidator._analyze_determinism()` | exact |
| `src/fast_fsm/visualization.py` | renderer/export sink | transform + file/string output | snapshot capture, Mermaid/PlantUML/JSON/document sinks | exact |
| `tests/test_graph_invariants.py` | model/projection test | transform/query | immutable snapshot and candidate-group tests | exact |
| `tests/test_diagnostic_contracts.py` | diagnostic contract test | bounded graph traversal | one-capture, exact-budget, adjacency/path tests | exact |
| `tests/test_validation.py` | validator/report integration test | transform/output | validator matrix, determinism, report, escaping tests | exact |
| `tests/test_visualization.py` | renderer/output integration test | transform/output | diagram, JSON, Markdown-document, stale-matrix tests | exact |
| `tests/test_mypyc_guard.py` | build/static/native contract test | batch/build + transform | frozen-slot AST and pure/native semantic probes | exact |
| `.specify/memory/spr-core-api.md` | contract documentation | reference/serialization | existing diagnostic, snapshot, priority, and output contract entries | role-match |

No new diagnostic module or duplicate budget test file is indicated. The
context names `tests/test_diagnostic_contracts.py` as the active budget and
snapshot suite; keep all new contract cases there.

## Pattern Assignments

### `src/fast_fsm/core.py` (component/model projection, event-driven + transform)

**Analogs:** `_TransitionGroup`, `_transition_entries()`, `_GraphTransition`,
and `_graph_snapshot_owned()`.

**Immutable candidate and snapshot records** (lines 655-703):

```python
@dataclass(frozen=True, slots=True)
class _TransitionGroup:
    """Private immutable, ascending-priority candidates for one slot."""

    entries: Tuple[TransitionEntry, ...]


@dataclass(frozen=True, slots=True)
class _GraphTransition:
    """Immutable private projection of one canonical transition edge."""

    from_state: "State"
    trigger: str
    to_state: "State"
    condition: Optional[Condition]
    from_state_name: str
    to_state_name: str
    condition_name: Optional[str]
    priority: int
    condition_ref: Optional[str] = None
```

Keep private records frozen and slotted. Add any diagnostic-only scalar fact as
a trailing field; do not move diagnostic logic into runtime `TransitionEntry`
selection. The snapshot already carries exact priority and optional
`condition_ref`; Phase 24's narrow static-shadow fact belongs at this same
snapshot boundary if needed.

**Cold candidate flattening** (lines 677-703 and 1534-1566):

```python
def _transition_entries(slot: _TransitionSlot) -> Tuple[TransitionEntry, ...]:
    """Return the immutable candidate sequence for one cold-path projection."""
    if isinstance(slot, _TransitionGroup):
        return slot.entries
    return (slot,)


def _graph_snapshot_owned(self) -> _GraphSnapshot:
    states = tuple(state for _, state in sorted(self._states.items()))
    state_names = tuple(state.name for state in states)
    transitions: List[_GraphTransition] = []
    for from_name, entries in sorted(self._transitions.items()):
        for trigger, slot in sorted(entries.items()):
            for entry in _transition_entries(slot):
                transitions.append(
                    _GraphTransition(
                        self._states[from_name], trigger, entry.to_state,
                        entry.condition, self._states[from_name].name,
                        entry.to_state.name,
                        entry.condition.name if entry.condition is not None else None,
                        entry.priority, entry.condition_ref,
                    )
                )
```

This is the exact ownership envelope to extend. Preserve source-name,
trigger, and stored ascending-priority order; do not sort again in downstream
diagnostics. Capture static unconditional evidence without invoking guards or
permissions. The safe proof identified by research is
`entry.condition is None and type(source_state) is State`; subclasses and
declarative states must not be treated as proven unconditional merely because
their condition slot is empty. `State.can_transition()` is user-overridable
(lines 827-829), so diagnostics must never call it.

**Runtime boundary to leave untouched** (lines 2351-2400):

```python
if isinstance(slot, _TransitionGroup):
    for entry in slot.entries:
        selected = self._select_sync_candidate(..., entry, ..., scan_group=True)
        if selected is not None:
            return selected
```

The selector scans the already ordered local tuple. `_transition_entries()` is
for cold projections; diagnostic changes must not make dispatch recapture or
resort topology.

### `src/fast_fsm/_diagnostics.py` (utility/graph algorithm, transform + bounded traversal)

**Analog:** `_DiagnosticEdge` and `_graph_from_snapshot()` (lines 80-221).

```python
@dataclass(frozen=True, slots=True)
class _DiagnosticEdge:
    """One scalar edge in immutable snapshot order."""

    from_index: int
    trigger: str
    to_index: int
    condition_name: str | None


def _graph_from_snapshot(snapshot: _GraphSnapshot) -> _DiagnosticGraph:
    state_names = snapshot.state_names
    state_indices = {name: index for index, name in enumerate(state_names)}
    edges = tuple(
        _DiagnosticEdge(
            state_indices[transition.from_state_name],
            transition.trigger,
            state_indices[transition.to_state_name],
            transition.condition_name,
        )
        for transition in snapshot.transitions
    )
    ...
```

Extend this one scalar projection so every edge retains numeric priority (and
the static-shadow evidence if validation needs it). Keep the tuple-backed
`forward`/`reverse` index construction. All downstream graph algorithms should
continue to iterate these edge indices, preserving same-target candidate
multiplicity.

**Reserve-before-work budget pattern** (lines 104-191):

```python
def reserve_work(self, *, stage: str, amount: int = 1) -> None:
    self._reserve("max_work", "_work_count", stage, amount)

def reserve_result(self, *, stage: str, amount: int = 1) -> None:
    self._reserve("max_results", "_result_count", stage, amount)

if current + amount > limit:
    self._complete = False
    self._exhausted_dimension = dimension
    self._exhausted_stage = stage
    raise DiagnosticBudgetExceeded(self.status)
```

Charge each candidate edge independently wherever an edge is inspected or
emitted. Retain the fixed redacted exception message and existing status fields;
do not return a partial result that looks complete. Dense cell preflight stays
separate from candidate transition/result reservations.

**Sparse and dense adjacency patterns** (lines 432-524):

```python
budget.reserve_result(stage="sparse.edges", amount=len(graph.edges))
for edge_index, edge in enumerate(graph.edges):
    budget.reserve_work(stage="sparse.edge")
    edge_rows.append({
        "idx": edge_index,
        "from_state_idx": edge.from_index,
        "to_state_idx": edge.to_index,
        "event_idx": event_indices[edge.trigger],
        "event": edge.trigger,
        "condition": edge.condition_name,
    })
```

Preserve one row per candidate and add the same numeric `priority` key to
sparse rows, dense `transitions`, and transition-matrix candidate records. The
legacy `representation="transition"` target-name-only cells need an ordered
candidate record shape if they are to expose multiplicity and priority; do not
collapse same-target candidates.

**Generated-path pattern** (lines 527-574):

```python
edge = graph.edges[outgoing[edge_offset]]
budget.reserve_path_expansion(stage="path.expand", maximum=max_expansions)
budget.reserve_work(stage="path.expand")
budget.reserve_result(stage="path.result")
next_path = path + ((
    graph.state_names[edge.from_index],
    edge.trigger,
    graph.state_names[edge.to_index],
),)
```

Keep the iterative frame algorithm and deterministic edge order. Extend each
step with the candidate's priority (the research recommendation is the fourth
scalar) and retain separate expansion/result reservations per candidate.

### `src/fast_fsm/validation.py` (validator/report adapter, transform + output)

**Snapshot initialization adapter** (lines 118-173):

```python
self._initialize_from_snapshot(
    fsm,
    fsm._graph_snapshot(),
    name=name,
    budget=_DiagnosticBudget(limits),
)

def _initialize_from_snapshot(...):
    self._snapshot = snapshot
    self._diagnostic_graph = _graph_from_snapshot(self._snapshot)
    self._budget = budget
    self._extract_fsm_structure()

def _extract_fsm_structure(self) -> None:
    self.states = set(self._diagnostic_graph.state_names)
    for edge in self._diagnostic_graph.edges:
        from_state = self._diagnostic_graph.state_names[edge.from_index]
        to_state = self._diagnostic_graph.state_names[edge.to_index]
        self.transitions[from_state][edge.trigger].add(to_state)
        self.events.add(edge.trigger)
```

Keep one snapshot and one shared ledger for a top-level report. The legacy
`self.transitions` set is a compatibility adapter only: same-target candidates
collapse there and it cannot define candidate determinism or candidate counts.
New priority/shadow analysis must consume `self._diagnostic_graph.edges`.

**Existing report/adjacency adapters** (lines 262-367 and 396-424):

```python
return _sparse_adjacency(self._diagnostic_graph, self._operation_budget(limits))

return _dense_adjacency(
    self._diagnostic_graph,
    self._operation_budget(limits),
    representation="transition",
)

for state_index, state_name in enumerate(self._diagnostic_graph.state_names):
    outgoing = self._diagnostic_graph.forward[state_index]
    for event_name in event_names:
        budget.reserve_work(stage="determinism.cell")
        targets = {
            self._diagnostic_graph.edges[edge_index].to_index
            for edge_index in outgoing
            if self._diagnostic_graph.edges[edge_index].trigger == event_name
        }
```

Replace the target-cardinality rule with one pass over contiguous
`(from_index, trigger)` candidate groups. Strictly increasing exact built-in
integer priorities are deterministic regardless of target multiplicity; equal,
descending, Boolean, or non-integer priorities are errors. Keep existing
`is_deterministic` and `non_deterministic_transitions` keys for compatibility,
and add candidate-level malformed-priority, provably-shadowed, and
possibly-shadowed records with source, trigger, target, candidate priority,
and shadowing priority. Never run a condition or state permission.

**Enhanced issue pattern** (lines 772-788):

```python
determinism = self.check_determinism()
for state, event in determinism["non_deterministic_transitions"]:
    self.issues.append(
        ValidationIssue(
            "info", "determinism", description,
            location=f"{state}.{event}",
            recommendation="Consider using conditions to make transitions deterministic",
        )
    )
```

Use this issue-construction seam, but update severity and advice: malformed
priority topology is an error, provable shadowing is a warning, and possible
shadowing is informational. Valid ordered groups must not be reported as
non-deterministic.

**Metrics and Markdown/JSON output** (lines 653-683 and 950-1086):

`actual_transitions` currently sums the compatibility target sets. Preserve
event/state coverage metrics where they are intentionally set-based, but use
candidate edge count for transition totals and candidate rows. The JSON export
already forwards `adj["transitions"]`; add priority there through the shared
adjacency adapter. The Markdown report already has a numbered transition table;
add a `Priority` column and render numeric priority without passing it through
text escaping. Existing report names, issue descriptions, recommendations, and
state/event text still use `_escape_markdown_text`.

### `src/fast_fsm/visualization.py` (renderer/export sink, transform + output)

**Single-capture entry point** (lines 84-103):

```python
def _capture_diagnostic_graph(fsm, limits):
    snapshot = fsm._graph_snapshot()
    return snapshot, _graph_from_snapshot(snapshot), _DiagnosticBudget(limits)

def _transition_label(trigger, condition_name, *, show_conditions, escape):
    label = escape(trigger)
    if show_conditions and condition_name is not None:
        label = f"{label} [{escape(condition_name)}]"
    return label
```

Keep public renderers as thin wrappers around `_capture_diagnostic_graph()`
and private `*_from_snapshot()` sinks. Append generated numeric priority after
the optional condition label; `show_conditions=False` hides only the condition,
never priority. Keep Mermaid and PlantUML text escaping format-specific.

**Mermaid/PlantUML edge sinks** (lines 151-164 and 207-220):

```python
for edge in graph.edges:
    budget.reserve_work(stage="mermaid.edge")
    label = _transition_label(
        edge.trigger, edge.condition_name,
        show_conditions=show_conditions,
        escape=_escape_mermaid_text,
    )
    _append_rendered_line(
        lines, budget, stage="mermaid.edge",
        line=f"    {state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}",
    )
```

Retain opaque positional state IDs (`s0`, `s1`, ...) and reserve each rendered
line before append. Add priority to every edge line and update docstring
snapshots/goldens. Do not interpolate caller text as diagram syntax.

**JSON and adjacency-document sinks** (lines 394-472 and 578-842):

```python
for edge in graph.edges:
    budget.reserve_work(stage="json.transition")
    transitions.append({
        "trigger": edge.trigger,
        "from": graph.state_names[edge.from_index],
        "to": graph.state_names[edge.to_index],
        "has_guard": edge.condition_name is not None,
    })
```

Add numeric `priority` to JSON topology transition records and retain the
shared `_sparse_adjacency()`/`_dense_adjacency()` output. `_validate_adjacency_matrix()`
must compare candidate-complete records—including priority—against the one
captured graph before rendering. Markdown adjacency cells should show each
candidate event plus priority; transition tables should gain a Priority column.
Reuse `_escape_markdown_heading()`/`_escape_markdown_cell()` and preserve the
fixed stale-matrix error (`adjacency matrix does not match captured snapshot`).

### `tests/test_graph_invariants.py` (model/projection, transform/query)

**Analogs:** `test_graph_snapshot_is_fresh_sorted_immutable_and_canonical()`
(lines 70-92), `test_graph_snapshot_flattens_candidate_groups_with_scalar_identity()`
(lines 95-142), and grouped projection/atomicity cases (lines 405-470).

```python
snapshot = machine._graph_snapshot()
assert [
    (row.from_state_name, row.trigger, row.priority, row.condition_ref)
    for row in snapshot.transitions
] == [
    ("idle", "go", -1, "low"),
    ("idle", "go", 5, "high"),
]
with pytest.raises((AttributeError, TypeError)):
    snapshot.transitions[0].condition_ref = "changed"
```

Extend these identity-sensitive white-box assertions for any static snapshot
fact and candidate-complete diagnostic ordering. Use real `State` objects and
assert frozen/slotted immutability, same-target multiplicity, and no mutation
on malformed priority data. Do not alter runtime selector tests to call
diagnostic helpers.

### `tests/test_diagnostic_contracts.py` (diagnostic contract, bounded traversal)

**Analogs:** one-capture mutation test (lines 219-243), exact-work test
(lines 246-284), graph construction/SCC tests (lines 343-423), adjacency/path
boundaries (lines 426-551), and aggregate-budget/JSON snapshot tests
(lines 768-827).

```python
def test_validator_captures_once_and_reachability_uses_only_the_snapshot(...):
    ...
    validator = FSMValidator(machine, limits=DiagnosticLimits(max_work=100))
    assert calls == 1
    assert validator.get_reachable_states() == {"initial", "middle"}
    assert validator._diagnostic_graph.state_names == (
        "initial", "middle", "orphan"
    )
```

Add candidate groups with identical targets and verify sparse/dense adjacency
and generated paths retain every candidate and priority. Follow the existing
generous/exact/one-less budget helper pattern; assert the exhausted dimension,
stage, and counter, and ensure no partial candidate output escapes. Add a
mutation-after-capture case proving all report data derives from one immutable
graph. Keep tests sequential and import private graph helpers directly as the
current contract suite does.

### `tests/test_validation.py` (validator/report integration, transform/output)

**Analogs:** base validator matrix and report tests (lines 163-215),
determinism/path tests (lines 236-255), and hostile Markdown output
(`test_export_markdown_encodes_hostile_caller_text`, lines 407-434).

```python
report = validator.validate_completeness(include_dense=True)
assert report["diagnostic_status"] == validator.diagnostic_status
assert report["diagnostic_status"].dense_cell_count == 2
assert report["diagnostic_status"].result_count > 0
```

Add strict-priority acceptance/rejection and conservative definite/possible
shadow cases to this existing validator suite. Assert valid multi-target
ordered groups are deterministic, malformed priorities are errors, and no
condition or `can_transition()` callback was invoked. Check candidate-level
JSON and Markdown fields, escaping, transition counts, and explicit budget
status. Preserve legacy report keys and compatibility matrix behavior except
where the candidate-complete cell shape is deliberately evolved.

### `tests/test_visualization.py` (renderer/output integration, transform/output)

**Analogs:** Mermaid edge goldens (lines 62-164), document adjacency validation
(lines 287-381), PlantUML edges (lines 389-455), and JSON topology/serializability
tests (lines 463-539).

```python
def test_malformed_adjacency_inputs_fail_with_the_fixed_contract(...):
    wrong_transition = copy.deepcopy(adjacency)
    wrong_transition["transitions"][0] = {}
    with pytest.raises(
        ValueError, match="adjacency matrix does not match captured snapshot"
    ):
        to_mermaid_document(fsm, adjacency_matrix=wrong_transition)
```

Create a candidate fixture with same source/trigger and same or different
targets. Assert one rendered edge/JSON record/table row per candidate, stable
priority order, priority visible even with `show_conditions=False`, and
format-specific escaping remains intact. Update docstring snapshots only as
needed for the generated priority label. Reuse existing stale/malformed matrix
tests to prove priority is part of matrix identity.

### `tests/test_mypyc_guard.py` (build/static/native contract, batch/build + transform)

**Analogs:** frozen-slot AST contract (lines 384-482), exact-priority boundary
(lines 485-506), and mode-invariant semantic probes (lines 1623-1695 and
1697-1778).

```python
assert keywords.get("frozen") is True
assert keywords.get("slots") is True
assert {
    item.target.id for item in node.body
    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
} == fields
```

Extend the expected `_GraphTransition` field set for any new scalar fact and
keep it a frozen slotted dataclass in compiled `core.py`. Add a fresh native
probe that constructs grouped candidates and compares the snapshot/diagnostic
projection with pure mode. Keep the test's existing `importlib.util.find_spec`
artifact-origin assertion and avoid monkeypatch-only seams that compiled calls
can bypass. Run `task pure-source-check` before pure tests after any native
build so in-place extension shadows cannot contaminate source-mode evidence.

### `.specify/memory/spr-core-api.md` (contract documentation, reference/serialization)

**Analog:** existing entries for `_GraphSnapshot`, candidate-complete
`_GraphTransition`, one-snapshot diagnostics, budgets, and `to_dict()` (lines
48-60).

Document that the private diagnostic graph is a candidate-complete scalar
projection of one immutable snapshot; validation accepts strictly increasing
priorities, rejects malformed order, and reports provable versus possible
shadowing conservatively. State that JSON, Mermaid, PlantUML, Markdown,
adjacency, and paths expose numeric priority for each candidate, with existing
escaping and budget semantics unchanged. Keep diagnostics outside the mypyc
runtime hot path and preserve public callback/`snapshot()` compatibility.

## Shared Patterns

### One immutable projection

All top-level consumers must capture once and pass the same snapshot-derived
graph through analysis and output. The visualization helper does this in
`_capture_diagnostic_graph()` (visualization.py:84-89); `FSMValidator.__init__`
does it in `_initialize_from_snapshot()` (validation.py:134-164). Do not read
`fsm._transitions` from validation or renderers, and do not recapture topology
while producing one result.

### Candidate identity and order

The authoritative order is `sorted(source)`, `sorted(trigger)`, and the
immutable ascending candidate tuple from `_transition_entries()`
(core.py:1536-1555). Preserve one edge/record per candidate, including
same-target candidates. Target-set deduplication remains suitable only for
legacy state/event coverage or structural condensation, never candidate output.

### Budget discipline

Use `_DiagnosticBudget` and `reserve_*()` before every candidate inspection,
edge/result emission, path expansion, and dense allocation. Existing tests
prove exact and one-less boundaries (test_diagnostic_contracts.py:383-551).
Keep fixed `DiagnosticBudgetExceeded("diagnostic budget exhausted")` behavior
and scalar `DiagnosticStatus` fields; never silently collapse candidates to fit
a limit.

### Escaping and opaque identities

Use `_escape_mermaid_text`, `_escape_plantuml_text`, and
`_escape_markdown_text`/cell/heading wrappers in their existing sinks
(visualization.py:42-81). Keep opaque positional state aliases from
`_opaque_state_ids()` (visualization.py:47-50). Priority is a validated integer
generated by the library; caller-controlled trigger, condition, state, and
title text still goes through the existing format-specific encoder.

### Compatibility and compiled boundary

`_diagnostics.py`, `validation.py`, and `visualization.py` remain interpreted
and outside `setup.py`'s sole `core.py` mypyc compilation unit. Hot-path classes
remain slotted; private graph rows stay frozen/slotted. Preserve legacy keys
where feasible, document any intentional dense-matrix cell-shape evolution,
and prove source/native parity with AST and fresh compiled probes.

## No Analog Found

None. Every expected Phase 24 file has an existing role/data-flow analog. The
only intentionally new behavior is candidate-aware semantics layered onto the
existing scalar graph, validator, renderer, and budget seams.

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`,
`src/fast_fsm/_diagnostics.py`, `src/fast_fsm/validation.py`,
`src/fast_fsm/visualization.py`, and the five active diagnostic/projection test
files under `tests/`.  
**Files scanned:** 10 expected implementation/documentation/test files plus
their cited helper ranges.  
**Pattern extraction date:** 2026-09-07
