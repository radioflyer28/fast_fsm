# Phase 19: Bounded Diagnostics & Safe Output - Pattern Map

**Mapped:** 2026-09-02  
**Files analyzed:** 26 planned/modified files
**Analogs found:** 25 / 26 (the new diagnostics module has no exact implementation analog)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | runtime/model, snapshot and logging boundary | request-response + synchronized read/configuration | existing `_GraphSnapshot`, ownership envelopes, and logging helpers in the same file | exact structural seams; new scalar snapshot/logging policy is additive |
| `src/fast_fsm/_diagnostics.py` | internal utility/service | transform + graph traversal + bounded batch output | `FSMValidator` graph methods in `src/fast_fsm/validation.py` | role/data-flow match; new module has no exact analog |
| `src/fast_fsm/validation.py` | public analysis service | CRUD-like graph query + batch/transform | existing `FSMValidator`/`EnhancedFSMValidator` | exact |
| `src/fast_fsm/visualization.py` | serializer/renderer adapter | transform + file/text output | current Mermaid, PlantUML, JSON, and Markdown helpers in same file | exact |
| `src/fast_fsm/__init__.py` | public API registry | import/re-export | existing explicit imports and `__all__` | exact |
| `tests/test_diagnostic_contracts.py` | new integration/property test | bounded graph transform | `tests/test_graph_invariants.py`, `tests/test_validation.py`, `tests/test_hypothesis.py` | role match |
| `tests/test_output_safety.py` | new hostile-input/golden test | text serialization | `tests/test_visualization.py` | role/data-flow match |
| `tests/test_logging_config.py` | integration/security regression test | event-driven logging/configuration | existing real-handler tests in same file | exact |
| `tests/test_validation.py` | regression/schema test | graph analysis + batch response | existing validation tests in same file | exact |
| `tests/test_visualization.py` | regression/golden test | renderer/JSON output | existing rendering tests in same file | exact |
| `tests/test_mypyc_guard.py` | structural/compile test | static AST + subprocess | existing slot and compilation guards in same file | exact |
| `tests/test_release_evidence.py` | tooling regression test | subprocess/file-I/O manifest validation | existing evidence CLI tests in same file | role match |
| `tests/test_performance_benchmarks.py` | performance regression test | batch measurement | existing trigger throughput tests in same file | exact |
| `tools/phase16_isolated_verify.py` | verification harness | subprocess + isolated file overlay | existing Phase 18 suite branch and inventory | exact |
| `README.md` | public entry-point documentation | user-facing API discovery + tested examples | existing Visualization, Serialization & Introspection, and Validation feature sections plus `tests/test_readme_examples.py` | exact documentation and verification pattern |
| `docs/api/validation.md` | API documentation | request-response contract | existing validator/adjacency documentation | exact |
| `docs/api/visualization.md` | API documentation | text-output contract | existing renderer usage notes | exact |
| `docs/api/core.md` | API documentation | logging/configuration contract | existing autodoc core page | role match |
| `docs/dev/architecture.md` | architecture documentation | transform/contract model | existing snapshot, lifecycle, ownership, and mypyc sections | exact structural style |
| `docs/dev/testing.md` | developer/test documentation | batch verification | existing Phase 18 isolated-gate section | exact |
| `.specify/memory/spr-core-api.md` | living API memory | contract summary | existing ownership/snapshot bullets | exact style |
| `.specify/memory/spr-validation.md` | living API memory | analysis/schema summary | existing sparse/dense validator bullets | exact style |
| `.specify/memory/spr-visualization.md` | living API memory | serialization summary | existing renderer bullets | exact style |
| `.specify/decisions/ADR-006-bounded-diagnostics-safe-output.md` | decision record | durable cross-module contract | `ADR-005-safe-ownership-concurrency.md` | exact documentation convention |
| `evidence/release-baseline.json` | generated evidence artifact | batch measurement/reporting | current release baseline and Phase 17 evidence workflow | exact |
| `.planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md` | phase evidence record | batch measurement/reporting | `17-PERFORMANCE-EVIDENCE.md` | exact |

`tests/test_graph_invariants.py` is an unchanged verification dependency, not a
Phase 19 new/modified file. Plan 19-01 and the validation strategy run
it to protect existing snapshot and mypyc invariants, but no Phase 19 task owns
a content edit to that file. It is therefore excluded from the 26-file plan
union and remains a focused analog/verification input below.

## Pattern Assignments

### `src/fast_fsm/core.py` (runtime/model, synchronized snapshot and logging)

**Analog:** the existing slot-backed machine, `_GraphSnapshot`, ownership helpers, and logging functions in `src/fast_fsm/core.py`.

**Imports, slots, and initialization pattern** (`core.py:521-610`):

```python
class StateMachine:
    __slots__ = (
        "_name", "_initial_state", "_current_state", "_states",
        "_transitions", "_graph_version", "_logger",
        "_before_listeners", "_on_exit_listeners", "_on_enter_listeners",
        "_after_listeners", "_on_failed_callbacks", "_trigger_callbacks",
        "_state_exit_callbacks", "_state_enter_callbacks", "_history",
        "_history_max", "_sync_ownership_lock", "_sync_owner_thread_id",
    )

    self._states: Dict[str, State] = {}
    self._transitions: Dict[str, Dict[str, TransitionEntry]] = {}
    self._graph_version = 0
    self._logger = logging.getLogger(logger_name)
    self._sync_ownership_lock = threading.Lock()
    self._sync_owner_thread_id: Optional[int] = None
```

Keep new snapshot/logging fields in `__slots__`; do not add an instance
dictionary or import `_diagnostics.py` into the compiled core. Core changes must
remain compatible with the one-file mypyc boundary.

**Ownership-aware synchronized read seam** (`core.py:612-626`):

```python
def _acquire_sync_ownership(self, operation: str) -> int:
    owner_thread_id = threading.get_ident()
    if self._sync_owner_thread_id == owner_thread_id:
        raise RuntimeError(f"FSM ownership violation: reentrant {operation}")
    self._sync_ownership_lock.acquire()
    self._sync_owner_thread_id = owner_thread_id
    return owner_thread_id

def _release_sync_ownership(self, owner_thread_id: int) -> None:
    if self._sync_owner_thread_id != owner_thread_id:
        raise RuntimeError("FSM ownership violation: foreign trigger release")
    self._sync_owner_thread_id = None
    self._sync_ownership_lock.release()
```

Use this as the implementation model for an internal snapshot capture boundary:
capture fully while the topology writer owns the machine, release in `finally`,
and make callback-local reentry aware without routing a diagnostic read through a
public write/policy method. Capture scalar state/trigger/condition labels while
the boundary is held; retain the existing identity-bearing fields needed by
Phase 16/18 compatibility.

**Current snapshot shape to extend without replacing** (`core.py:372-394,
1026-1047`):

```python
@dataclass(frozen=True, slots=True)
class _GraphTransition:
    from_state: "State"
    trigger: str
    to_state: "State"
    condition: Optional[Condition]

@dataclass(frozen=True, slots=True)
class _GraphSnapshot:
    name: str
    initial_state: "State"
    graph_version: int
    states: Tuple["State", ...]
    transitions: Tuple[_GraphTransition, ...]

def _graph_snapshot(self) -> _GraphSnapshot:
    states = tuple(state for _, state in sorted(self._states.items()))
    transitions = tuple(
        _GraphTransition(self._states[from_name], trigger,
                         entry.to_state, entry.condition)
        for from_name, entries in sorted(self._transitions.items())
        for trigger, entry in sorted(entries.items())
    )
    return _GraphSnapshot(self._name, self._initial_state,
                          self._graph_version, states, transitions)
```

The new diagnostic projection should copy immutable scalar labels from this
deterministically ordered source, not dereference mutable `State.name` or
condition objects after capture. Top-level public callers capture exactly once
and pass the result to private render/analysis helpers.

**Existing redaction/sanitization convention** (`core.py:1883-1924`):

```python
safe_kwargs: Dict[str, Any] = {}
for key, value in kwargs.items():
    if not isinstance(key, str) or len(key) > 100:
        self._logger.warning("%s: Skipping invalid kwarg key for condition", self._name)
        continue
    if key.startswith("_"):
        self._logger.debug("%s: Skipping private kwarg '%s' for condition", self._name, key)
        continue
    if len(safe_kwargs) == 50:
        continue
    safe_kwargs[key] = value
```

Use the same metadata-only posture for default trace records: fixed operation,
stage, result category, argument count, and sanitized keyword names only. Raw
trigger/state/argument/keyword/cause/repr data must never reach `LogRecord`.
An explicit redactor receives a minimum ephemeral event and is filtered
fail-closed before calling `logger.log`.

**Current logging configuration to replace only at its ownership seam**
(`core.py:4573-4665`):

```python
logger = logging.getLogger(logger_name)
logger.setLevel(level)
logger.handlers.clear()
if level <= logging.INFO:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
```

Preserve the logger-name/level vocabulary and the `set_fsm_logging_level()`
delegation (`core.py:4648-4665`), but replace `handlers.clear()` with an
explicit private ownership marker, `addHandler`/`removeHandler`, and a
slot-backed reversible handle. Reconfiguration removes/closes only marked
library handlers; application handlers, formatter, filters, and propagation
remain untouched unless the caller explicitly asks to change propagation.
Restore should be idempotent and compare generation/identity before restoring
level or propagation, so an old handle cannot overwrite a later application
change.

**Core constraints:** diagnostics stay out of `trigger()`, `can_trigger()`,
`add_state()`, and `add_transition()` hot paths. If trace is disabled, retain a
single `logger.isEnabledFor(...)` branch and allocate no event. Add no runtime
dependency and keep every new production class slot-protected.

---

### `src/fast_fsm/_diagnostics.py` (new internal utility/service, graph transform)

**Analog:** `FSMValidator`'s extraction/traversal/matrix/path methods
(`validation.py:21-262`, `283-319`, `688-706`), but do not copy its mutable sets,
recursive DFS, or unconditional dense allocation. There is no exact existing
module analog; this is the shared interpreted seam prescribed by research.

**New module boundary:** import only standard-library types plus the private
snapshot type under a type-checking-safe import. `core.py` must not import this
module. Construct one immutable scalar `_DiagnosticGraph` from one
`_GraphSnapshot`, then thread one mutable slot-backed budget through all nested
operations.

**Use the current extraction shape only as the compatibility reference**
(`validation.py:46-70`):

```python
self.states: Set[str] = set()
self.transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(
    lambda: defaultdict(set)
)
self.events: Set[str] = set()
...
for from_state, transitions in self.fsm._transitions.items():
    for trigger, entry in transitions.items():
        to_state = entry.to_state.name
        self.states.add(from_state)
        self.states.add(to_state)
        self.transitions[from_state][trigger].add(to_state)
        self.events.add(trigger)
```

Replace that live-dictionary coupling with snapshot-order tuples, integer state
indices, sorted edge rows, forward/reverse sparse adjacency, initial index, and
captured condition labels. Build all ordering from tuples, never hash/set
iteration.

**Reachability analog** (`validation.py:72-98`):

```python
reachable = set()
queue = deque([start_state])
reachable.add(start_state)
while queue:
    current_state = queue.popleft()
    for event in self.events:
        for next_state in self.transitions[current_state].get(event, set()):
            if next_state not in reachable:
                reachable.add(next_state)
                queue.append(next_state)
```

Implement this iteratively over ordered sparse adjacency, always beginning at
the snapshot's declared initial index. Count vertex visits/edge examinations
before doing them. The budget object is shared with SCC/depth/path/render
adapters; it must not be reset by nested helpers.

**Cycle and depth analogs to replace** (`validation.py:283-319` and
`688-706`):

```python
if state in rec_stack:
    cycle_start = path.index(state)
    cycles.append(path[cycle_start:] + [state])
...
def dfs_longest(state: str, visited: Set[str]) -> int:
    if state in visited:
        return 0
    visited.add(state)
    max_depth = 0
    for ...:
        depth = 1 + dfs_longest(next_state, visited.copy())
        max_depth = max(max_depth, depth)
    return max_depth
```

Use iterative Kosaraju (forward finish order, reverse traversal), sort each SCC
by snapshot index, and call a component cyclic for size > 1 or a self-loop.
Condense cross-SCC edges and memoize longest depth on the resulting DAG. Report
the explicit interpretation (`dag_longest_path` or
`condensation_dag_depth`) rather than claiming an exact cyclic simple path.
Use iterative path frames with separate max-length, max-path, and expansion
budgets; reserve work/result units before copying/appending.

**Dense compatibility analog** (`validation.py:141-196`):

```python
n = len(sorted_states)
matrix: List[List[List[int]]] = [[[] for _ in range(n)] for _ in range(n)]
for t in transitions_list:
    matrix[t["from_state_idx"]][t["to_state_idx"]].append(t["idx"])
```

Retain the established matrix schema through a compatibility adapter, but
preflight `V*V`/`V*E` against the dense-cell/result budget before allocation.
Sparse edge records are the default. A budget exhaustion must produce explicit
status metadata for structured results or one fixed redacted
`DiagnosticBudgetExceeded` boundary for legacy list/scalar/string returns.

---

### `src/fast_fsm/validation.py` (public analysis and comparison service)

**Analog:** `FSMValidator` and `EnhancedFSMValidator` in the same file. Keep
`__slots__`, constructor/name compatibility, scoring semantics, and callable
legacy symbols. Change the constructor internally to capture one snapshot and
delegate to a private from-snapshot initializer; do not let public nested calls
recapture the machine.

**Constructor/slots pattern** (`validation.py:21-70`):

```python
class FSMValidator:
    __slots__ = (
        "fsm", "states", "transitions", "events", "initial_state", "_report_name"
    )

    def __init__(self, fsm: StateMachine, *, name: Optional[str] = None):
        self.fsm = fsm
        self._report_name = name if name is not None else fsm.name
        self.states: Set[str] = set()
        self.transitions = defaultdict(lambda: defaultdict(set))
        self.events: Set[str] = set()
        self.initial_state: str = fsm.current_state.name
        self._extract_fsm_structure()
```

Preserve `name=` as a report label, but source structural data from the
diagnostic graph and use declared initial state, not current state. Existing
methods (`find_unreachable_states`, `find_dead_states`, `find_missing_transitions`,
`check_determinism`, `find_cycles`) remain available as compatibility adapters
with deterministic order and bounded semantics.

**Completeness/report shape** (`validation.py:198-230`) is the compatibility
anchor:

```python
return {
    "fsm_name": self._report_name,
    "total_states": len(self.states),
    "total_events": len(self.events),
    "total_transitions": total_transitions,
    "initial_state": self.initial_state,
    "current_state": self.fsm.current_state.name,
    "unreachable_states": unreachable,
    "dead_states": dead_states,
    "missing_transitions": missing,
    "is_complete": len(missing) == 0,
    "is_reachable": len(unreachable) == 0,
    "has_dead_states": len(dead_states) > 0,
    "transition_matrix": self.get_transition_matrix(),
}
```

Extend structured reports with a common complete/exhausted/count status. Never
silently truncate legacy results. Add keyword-only limits or additive sibling
APIs; preserve existing positional signatures and defaults (`max_length=10`,
`max_paths=50`) unless calibrated compatibility tests document a change.

**Enhanced scoring analog** (`validation.py:414-491`, `753-825`):
reuse `EnhancedFSMValidator`'s issue list, metrics, score weights, and report
serialization, but feed it one shared graph-analysis result. Guard every
undefined aggregate (especially zero-machine comparison) with explicit `None`.

**Comparison/batch seam to replace** (`validation.py:1112-1154`,
`1187-1222`):

```python
results: Dict[str, Any] = {}
validators: Dict[str, Any] = {}
for fsm in fsms:
    validator = EnhancedFSMValidator(fsm)
    validators[fsm.name] = validator
    results[fsm.name] = {
        "score": validator.get_validation_score(),
        "metrics": validator.metrics,
        "issue_count": len(validator.issues),
    }
ranked = sorted(results.items(),
                key=lambda x: x[1]["score"]["overall_score"], reverse=True)
...
"avg_score": sum(...) / len(results),
```

Replace name-keyed identity with ordered positional records (`position`,
`name`, score/metrics/issues), tie-break rankings by ascending position, and
return `best_fsm=None`, empty entries/rankings, `count=0`, `total_issues=0`,
`avg_score=None`, and `score_range=None` for zero inputs. Capture each input
once, and pass its graph/budget through analysis. Batch summary printing may
retain the current human-readable loop but must iterate ordered entries.

---

### `src/fast_fsm/visualization.py` (renderer/JSON adapter)

**Analog:** all current helpers in `visualization.py:28-427`. Preserve lazy
optional validation behavior only where it does not hide correctness or budget
errors; replace live dictionary reads with private from-snapshot functions.

**Current Mermaid path** (`visualization.py:69-104`) is the exact output loop to
adapt:

```python
lines: list[str] = []
if title:
    lines.append(f"%% {title}")
lines.append("stateDiagram-v2")
state_ids: dict[str, str] = {}
for state_name in fsm._states:
    sid = _mermaid_id(state_name)
    state_ids[state_name] = sid
    if sid != state_name:
        lines.append(f'state "{state_name}" as {sid}')
...
lines.append(f"    {from_id} --> {to_id} : {label}")
```

Allocate `s0`, `s1`, ... from snapshot order for every state, including safe
names. Use a Mermaid-specific final-step encoder for aliases, labels, titles,
triggers, and condition text; encode controls/newlines as inert visible data.
Do not use `_mermaid_id()` as identity or a shared generic sanitizer.

**Current PlantUML path** (`visualization.py:139-170`) is the renderer analog:

```python
lines: list[str] = ["@startuml"]
if title:
    lines.append(f"title {title}")
lines.append(f"[*] --> {initial_name}")
for from_name, triggers in fsm._transitions.items():
    ...
    lines.append(f"{from_name} --> {to_name} : {label}")
for state_name in fsm._states:
    if state_name not in states_with_outgoing:
        lines.append(f"{state_name} --> [*]")
lines.append("@enduml")
```

Use opaque IDs and a separate PlantUML encoder for all caller text. Ensure
`!include`, `!import`, comments, `@startuml`/`@enduml`, Creole, URL/image
syntax, quotes, and physical newlines cannot be emitted from user fields.

**One-snapshot JSON/fenced/document seams** (`visualization.py:206-306`,
`309-349`, `352-427`):

```python
initial_name = next(iter(fsm._states))
...
quality = None
try:
    from fast_fsm.validation import EnhancedFSMValidator
    v = EnhancedFSMValidator(fsm)
    ...
except Exception:
    quality = None

diagram = to_mermaid(fsm, title=title, show_conditions=show_conditions)
return f"```mermaid\n{diagram}\n```"
```

Capture once at each public top-level function, then call private renderer/JSON
helpers with that snapshot and one budget. Fenced/document helpers must not call
public `to_mermaid()` again. JSON quality, reachability, cycles, topology, and
status all derive from the same graph. Remove broad fallback that converts
budget/correctness failures to `quality=None`.

The Markdown document currently interpolates headings/table cells directly
(`visualization.py:388-425`). Add a Markdown-specific cell/heading encoder,
validate any caller-supplied adjacency data against the captured graph (or
reject stale data with a fixed error), and make dense tables explicit/limited.

---

### `src/fast_fsm/__init__.py` (public export registry)

**Analog:** explicit import groups and `__all__` in `__init__.py:7-110`.

```python
from .visualization import (...)
from .validation import (...)
...
__all__ = [
    "State", "StateMachine", ...,
    "to_mermaid", "to_mermaid_fenced", "to_mermaid_document",
    "to_plantuml", "to_json",
    "FSMValidator", "EnhancedFSMValidator", ...,
]
```

Retain every existing import/symbol. Add only intentionally public limits,
status, and budget exception/handle types if the implementation publishes
them. Keep `_diagnostics.py` private and do not export internal graph/budget
records.

---

### Tests: `test_diagnostic_contracts.py`, `test_output_safety.py`, and existing regression files

**Real-object setup analogs:** `tests/test_graph_invariants.py:18-47` builds
machines and fingerprints identity/version/snapshot without mocks;
`tests/test_validation.py:37-97` provides small, problematic, cyclic, and
high-branching fixtures; `tests/test_hypothesis.py:23-58` builds generated
topologies with bounded Hypothesis settings.

```python
def graph_fingerprint(machine: StateMachine) -> tuple[Any, ...]:
    transitions = tuple(sorted((source_name, trigger, id(entry.to_state), ...)
                               for source_name, entries in machine._transitions.items()
                               for trigger, entry in entries.items()))
    snapshot = machine._graph_snapshot()
    return (..., machine._graph_version, id(machine.current_state), snapshot)
```

Build `test_diagnostic_contracts.py` around real machines and exact assertions:
declared-initial reachability after moving current state; duplicate-name batch
cardinality/order; zero-input comparison schema and `None` aggregates; self-loop,
3-cycle, overlapping SCC, and tail membership; DAG and condensation depth;
sparse default/no dense allocation; exact budget boundary (`required` passes,
`required-1` exhausts); bounded path expansion; and one snapshot call with a
mutation after capture unable to mix output. Use events/barriers only where
coordination is needed; no timing sleeps.

For generated graphs, follow the bounded strategy style in
`test_hypothesis.py:44-58`, but fix examples/settings so budget boundaries are
counted-work assertions, not machine-speed assertions. Add hostile strings for
all render sinks in `test_output_safety.py`; assert opaque IDs are distinct and
caller-provided newlines/directives/fences/comment markers do not occur raw.

**Existing rendering test pattern** (`tests/test_visualization.py:87-215` and
`222-485`):

```python
out = to_mermaid(simple_fsm)
assert out.startswith("stateDiagram-v2")
assert "[*] --> idle" in out
assert "idle --> running : start" in out
...
data = to_json(simple_fsm)
assert "topology" in data
assert "analysis" in data
```

Retain ordinary output regression assertions while updating expected IDs/schema
deliberately. Test byte stability on repeated calls and async-machine support.

**Logging test pattern** (`tests/test_logging_config.py:24-114`): tests use
real `logging` infrastructure and `caplog`, not mocks:

```python
configure_fsm_logging(logging.INFO, "fast_fsm.test_cfg_2")
logger = logging.getLogger("fast_fsm.test_cfg_2")
assert len(logger.handlers) >= 1
...
with caplog.at_level(logging.DEBUG, logger="fast_fsm.log_test_2"):
    fsm.trigger("start")
assert any("start" in r.message for r in caplog.records)
```

Replace the current unsafe clear-handler expectation at lines 35-48 with an
application-owned handler preservation test, marked library handler replacement,
propagation choice, idempotent/out-of-order restore, custom redactor minimum
event, redactor failure fail-closed, and scans of `record.__dict__`, formatted
message, and every application handler for trigger/state/arg/kwarg/error/repr
sentinels.

**Structural/mypyc pattern** (`tests/test_mypyc_guard.py:382-448`): parse
`core.py` with `ast`, assert frozen slot dataclasses/field sets and required
`StateMachine.__slots__`; add assertions for new slots, one public snapshot
boundary, no diagnostics import into core, and no raw logging trace path. Keep
subprocess compile/import checks and explicit pure/native origin assertions.

**Performance pattern** (`tests/test_performance_benchmarks.py:36-100`): use
real FSMs, warm up, measure with `time.perf_counter()`, and assert a broad
threshold. Phase 19 should add a disabled-trace/no-allocation or trigger floor
regression without placing diagnostics in the measured hot path; exact durable
observations belong in evidence, not prose.

---

### `tools/phase16_isolated_verify.py` (verification harness)

**Analog:** Phase 18 inventory and suite (`phase16_isolated_verify.py:82-108`,
`972-1039`) plus the safe task/manifest overlay (`137-160`, `808-860`).

```python
PHASE18_INVENTORY = (
    "src/fast_fsm/core.py",
    ...,
    "tests/test_ownership_concurrency.py",
    "tools/phase18_native_probe.py",
    ".github/workflows/ci.yml",
    "evidence/release-baseline.json",
)
...
if args.suite == "phase18":
    semantic = ("uv", "run", "pytest", ...)
    for build_mode in ("pure", "compiled"):
        status = _run_suite_command(...)
```

Add a `PHASE19_INVENTORY` containing every changed source/test/doc/SPR/ADR/tool
file needed for clean semantic proof and a `phase19` suite branch that runs
fresh pure and compiled origins for diagnostic/output/logging tests, then the
slots/type/release/docs/performance gates. Preserve argument-array subprocess
safety, fresh `HEAD` export plus explicit overlays, pre-import origin checks,
and refusal to touch checkout-native shadows. Extend parser choices and tests
atomically; do not alter prior suite behavior.

For baseline generation, follow `baseline-write` (`phase16_isolated_verify.py:
837-860`): require an explicit output path, run pure mode in an isolated tree,
copy the generated manifest atomically, and review the diff before committing.

---

### Documentation, memory, ADR, and evidence files

**README analog:** `README.md:461-548` already presents visualization,
serialization/introspection, and design-time validation as concise
consumer-facing feature sections before routing readers to deeper reference
material. Extend that same feature-oriented structure with the shipped Phase 19
limits/status/budget, positional batch/comparison, grammar-specific rendering,
metadata-only trace redaction, and reversible logging contracts. Preserve the
existing runnable-example style and keep any changed example covered by
`tests/test_readme_examples.py`, the established README verification analog.

**API docs analogs:** `docs/api/validation.md:1-20` establishes zero-runtime
overhead and sparse/dense prose; `docs/api/validation.md:87-139` documents
schemas and autodoc functions. `docs/api/visualization.md:1-71` documents
zero-overhead imports, function signatures, and the plain-dict adjacency
pipeline. Extend these pages with keyword-only limits, status/exhaustion
semantics, complexity, initial-state identity, positional comparison schema,
opaque IDs, target-specific escaping, stale matrix behavior, and logging
redaction/ownership (in `docs/api/core.md` where appropriate).

**Architecture/testing analogs:**
`docs/dev/architecture.md:68-99` documents canonical snapshots and explicitly
assigns Phase 19 ownership; `docs/dev/architecture.md:263-297` documents the
mypyc boundary. Extend the import DAG with interpreted `_diagnostics.py`, show
the one-capture → shared graph/budget → validator/JSON/renderer flow, and state
that diagnostics remain outside O(1) runtime operations.

`docs/dev/testing.md:144-170` is the canonical evidence workflow and
`docs/dev/testing.md:222-271` is the Phase 18 fresh-origin gate. Add the Phase
19 suite, exact counted-work adversarial matrix, hostile renderer/logging
fixtures, and the same pure/compiled origin requirements. Keep test counts and
throughput observations in the manifest/evidence file only.

**SPR analogs:**
`.specify/memory/spr-validation.md:7-22`,
`.specify/memory/spr-visualization.md:7-14`, and
`.specify/memory/spr-core-api.md:7-18` use compact durable bullets with category,
created/updated dates, public signatures, compatibility constraints, and
cross-phase ownership. Update all three in the same implementation commit as
the behavior they summarize; keep the internal diagnostics module private.

**ADR analog:** `ADR-005-safe-ownership-concurrency.md:1-83` records status/date,
context, numbered decision, and explicit contract; `:85-135` preserves
considered alternatives, consequences, and deferred work. Create ADR-006 for
the costly public schemas/escaping/logging/budget decisions, including why
SCC/condensation and sparse-first output were selected and what remains
FUTR-05/Phase 20.

**Evidence analog:**
`.planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md:1-54`
uses environment-labelled tables, exact commands, fresh-origin language, and
explicit non-claims. Use the same format for Phase 19 performance/coverage
observations. The generated `evidence/release-baseline.json` is authoritative
for exact counts/toolchain/coverage; use `tools/phase16_isolated_verify.py`
baseline-write/check and review the write diff rather than hand-editing it.

## Shared Patterns

### One immutable snapshot per top-level diagnostic call

**Sources:** `src/fast_fsm/core.py:1026-1047`; ownership envelope
`src/fast_fsm/core.py:612-626`; renderer nesting
`src/fast_fsm/visualization.py:348-349`.

Capture one synchronized scalar projection at the public boundary. Pass it to
private `*_from_snapshot` functions and one shared budget. JSON, validation,
Mermaid, PlantUML, fenced, and Markdown document helpers must not call another
public helper that recaptures or rereads live dictionaries.

### Deterministic ordering and positional identity

**Sources:** sorted snapshot construction (`core.py:1033-1040`), current
matrix ordering (`validation.py:161-183`), and name-keyed comparison/batch code
(`validation.py:1122-1153`, `1200-1222`) that must be corrected.

Use snapshot order for state/edge/renderer output; use input position for batch
and comparison identity. Names are labels only. Tie rankings by position and
never iterate sets for externally visible ordering.

### Count-before-work bounded analysis

**Sources:** current recursive/path and dense implementations
(`validation.py:185-189`, `232-262`) and established result/report assembly
(`validation.py:216-230`).

Thread one slot-backed ledger through all nested operations. Reserve before
vertex/edge examination, result append, path expansion, or dense allocation.
Structured results expose complete/exhausted and exact counters; legacy
list/scalar/string helpers fail closed with a fixed redacted budget exception.
No wall-clock sleeps or timing-based budgets.

### Slot/mypyc and runtime dependency boundary

**Sources:** `tests/test_mypyc_guard.py:382-448`,
`docs/dev/architecture.md:263-297`, and `setup.py:16-39`.

Keep `core.py` as the sole compiled module. `_diagnostics.py`, validation, and
visualization remain interpreted design-time modules. New production records,
limits, handles, and ledgers use slots/frozen slots where applicable. Add no
runtime dependency beyond the existing standard-library implementation.

### Contextual output and log redaction

**Sources:** unsafe renderer sinks (`visualization.py:71-102`, `141-169`,
`388-425`) and current safe key filtering (`core.py:1896-1924`).

Opaque IDs are identity; grammar-specific encoders are the final sink for
Mermaid, PlantUML, and Markdown. Default trace logging stores no raw payload in
the record; custom redactors are explicit, minimum-input, bounded, and
fail-closed. Application handlers always remain application-owned.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/fast_fsm/_diagnostics.py` | internal graph utility/service | transform + bounded traversal | No shared scalar graph projection, SCC, or counted-budget module currently exists; use the validation algorithms only as migration references and follow research/CONTEXT contracts. |

## Metadata

**Analog search scope:** `src/fast_fsm`, `tests`, `tools`, `docs`,
`.specify/memory`, `.specify/decisions`, `.planning/phases/17-*`, and release
evidence artifacts.  
**Files scanned:** 26 planned/modified candidates plus focused source/test/docs
analogs.  
**Pattern extraction date:** 2026-09-02
