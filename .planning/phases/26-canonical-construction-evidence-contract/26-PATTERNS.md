# Phase 26: Canonical Construction & Evidence Contract - Pattern Map

**Mapped:** 2026-09-15  
**Files analyzed:** 15 implementation, test, tooling, and configuration targets  
**Analogs found:** 13 / 15 (new comparison files use partial analogs from existing benchmark/evidence code; two adjacent locks have no repository analog)

Phase 26 is infrastructure-only. The implementation should deepen the existing
private construction seam and evidence conventions without changing the runtime
selector/lifecycle hot path or adding a public registrar abstraction.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | component / utility | transform + event-driven topology publication | existing `_PreparedTransition` / `_normalize_transition_request()` / `_commit_transition_plan()` | exact |
| `tests/test_graph_invariants.py` | test | event-driven invariant assertions | existing `graph_fingerprint()` and batch/helper atomicity tests | exact |
| `tests/test_builder.py` | test | staged transform + event-driven publication | existing builder fingerprint, retry, and late-failure tests | exact |
| `benchmarks/comparison/common.py` | utility / schema | transform / batch records | `tools/artifact_conformance.py` schema and `benchmarks/performance_demo.py` sampler | role-match |
| `benchmarks/comparison/fast_fsm_runner.py` | benchmark adapter | request-response measurement | `benchmarks/performance_demo.py` runtime-labelled collector | role-match |
| `benchmarks/comparison/python_statemachine_2_5.py` | benchmark child | request-response measurement | `benchmarks/benchmark_py_fsm.py` plus installed evidence child protocol | partial |
| `benchmarks/comparison/python_statemachine_3_2.py` | benchmark child | request-response measurement | `benchmarks/benchmark_py_fsm.py` plus installed evidence child protocol | partial |
| `benchmarks/comparison/run_comparison.py` | orchestrator | subprocess / event-driven aggregation | `tools/release_evidence.py` subprocess and strict-record pipeline | role-match |
| `benchmarks/comparison/python_statemachine_2_5.py.lock` | generated config | file I/O / dependency resolution | no exact analog; uv adjacent script lock convention from research | new pattern |
| `benchmarks/comparison/python_statemachine_3_2.py.lock` | generated config | file I/O / dependency resolution | no exact analog; uv adjacent script lock convention from research | new pattern |
| `tests/test_competitor_benchmark_contract.py` | test | transform + subprocess contract validation | `tests/test_artifact_conformance.py`, `tests/test_release_evidence.py` | role-match |
| `Taskfile.yml` | config / integration entry point | request-response subprocess invocation | existing `benchmark`, `benchmark-compiled`, and release-evidence tasks | exact |
| `pyproject.toml` | config | dependency resolution | existing dependency groups | exact |
| `uv.lock` | generated config | file I/O / dependency resolution | current project lock | exact for regeneration, no hand edits |
| `.specify/memory/spr-core-api.md` / `docs/dev/architecture.md` (if materially changed) | architecture documentation | transform / explanatory | existing canonical-topology and compiled-core sections | role-match |

## Pattern Assignments

### `src/fast_fsm/core.py` (component / utility, topology transform)

**Analog:** `src/fast_fsm/core.py`, `_PreparedTransition`,
`_normalize_transition_request()`, `_commit_transition_plan()`, and the existing
owned adapter methods.

**Private carrier pattern** (lines 759-770):

```python
@dataclass(frozen=True, slots=True)
class _PreparedTransition:
    """Fully validated private transition request awaiting one graph commit."""

    trigger: str
    sources: Tuple["State", ...]
    target: "State"
    condition: Optional[Condition]
    priority: int
    condition_ref: Optional[str] = None
    after: Optional[float] = None
    within: Optional[float] = None
```

Add the raw request carrier in the same module, frozen and slotted. Keep it
private so `core.py` remains the sole mypyc compilation unit and adapters do not
gain another public construction API. Preserve the distinction between raw
endpoint identity (before canonical resolution) and `_PreparedTransition`
(after resolution).

**Canonical normalization pattern** (lines 1733-1835):

```python
normalized_priority = _normalize_priority(priority)
...
source = self._resolve_canonical_state(raw_source, role="source")
target = self._resolve_canonical_state(to_state, role="target")
...
normalized_after, normalized_within = self._normalize_timing(after, within)
...
if condition is None:
    normalized_condition = None
elif isinstance(condition, Condition):
    normalized_condition = condition
elif callable(condition):
    normalized_condition = FuncCondition(condition)
else:
    raise TypeError(...)
return _PreparedTransition(...)
```

The new transaction should call this method for every raw request. Keep
adapter-only syntax parsing (tuple shape, dictionary field context, builder
async classification) outside it. Endpoint resolution, exact priority and
timing normalization, condition normalization, and duplicate-source checks
belong here exactly once.

**Off-table publication pattern** (lines 1837-1860):

```python
replacements = {}
original_slots = {}
for plan in plans:
    for source in plan.sources:
        key = (source.name, plan.trigger)
        existing = replacements[key] if key in replacements else ...
        replacements[key] = self._merge_transition_slot(existing, plan)
changed_replacements = tuple(...)
if not changed_replacements:
    return
for source_name, trigger, replacement in changed_replacements:
    self._transitions[source_name][trigger] = replacement
self._graph_version += 1
```

Formalize this as the one private request-to-plan-to-publication operation.
Normalize the complete request collection, build all replacement slots without
mutating published tables, then publish replacements and increment the graph
version once. Never add rollback/undo writes after a partial table mutation.
The existing `_commit_transition_plan()` remains the only writer of transition
slots.

**Adapter delegation pattern:**

- `add_transition()` / `_add_transition_owned()` (lines 1903-1954) acquire the
  machine ownership envelope, normalize one request, and commit one plan.
- `add_transitions()` / `_add_transitions_owned()` (lines 1956-2024) parse each
  row, normalize every row, and commit the tuple only after the loop succeeds.
- bidirectional and emergency helpers (lines 2026-2195) normalize all legs or
  all source states before one commit.
- `quick_build()` (lines 1117-1234) preserves supplied state identities,
  creates unresolved string states locally, and replays the complete row list
  through `fsm.add_transitions(transition_rows)`; it must not reimplement merge,
  priority, or graph-version policy.
- `from_dict()` (lines 1236-1510) may retain transition-indexed schema errors,
  condition-reference parsing, and dictionary context, but should emit the same
  private request representation/transaction rather than a second registrar.

Do not route `trigger()`, `can_trigger()`, selectors, callback lifecycle, or
history through this cold construction machinery. Preserve the direct
singleton `(state, trigger)` dictionary lookup and local candidate-group work.

### `tests/test_graph_invariants.py` (test, event-driven invariant assertions)

**Analog:** `tests/test_graph_invariants.py`, `graph_fingerprint()` (lines
21-59), endpoint atomicity (lines 318-340), batch/helper atomicity (lines
342-383).

**Identity-sensitive fingerprint pattern** (lines 21-59):

```python
def graph_fingerprint(machine: StateMachine) -> tuple[Any, ...]:
    transitions = tuple(sorted((source_name, trigger, (...)) ...))
    snapshot = machine._graph_snapshot()
    return (
        tuple((name, id(state)) for name, state in sorted(machine._states.items())),
        transitions,
        machine._graph_version,
        id(machine.current_state),
        snapshot,
    )
```

Use this existing helper rather than comparing only state names. New adapter
matrix tests should capture state registry identity, transition entry/condition
identity, graph version, current state, and private snapshot before each late
failure. Assert the fingerprint is identical afterward.

**Atomic failure pattern** (lines 318-383):

```python
before = graph_fingerprint(machine)
with pytest.raises((TypeError, ValueError)):
    operation()
assert graph_fingerprint(machine) == before
```

Extend the table-driven operations to direct, batch, bidirectional,
emergency, quick-build, and dictionary adapters. Include early and late invalid
rows, duplicate priority/tie conflicts, foreign endpoint objects, malformed
conditions, and nested async incompatibility. Assert compound operations do
not publish a valid prefix and advance `_graph_version` only on success.

Add a structural/source assertion only if needed to prove selectors and
lifecycle methods do not reference the request carrier or transaction seam;
the runtime hot path must remain free of construction scans and allocations.

### `tests/test_builder.py` (test, staged transform/publication)

**Analog:** `tests/test_builder.py`, `builder_staging_fingerprint()` and
priority/retry tests around lines 130-225, 1047-1105, and 2096-2150.

**Builder fingerprint pattern** (lines 130-180):

```python
def builder_staging_fingerprint(builder):
    machine = builder._machine
    return (
        tuple((name, id(state)) for name, state in builder._states.items()),
        tuple((trigger, ..., id(condition), priority[0] if priority else 0)
              for trigger, ... in builder._transitions),
        tuple((state_name, id(callback)) for state_name, callback in ...),
        builder._machine_type,
        builder._auto_detect,
        id(machine) if machine is not None else None,
        _machine_topology_fingerprint(machine) if machine is not None else None,
    )
```

If staged rows change from anonymous tuples to the raw carrier, update the
test-only fingerprint projection to compare the carrier fields and identities,
not implementation tuple positions. Keep the test’s purpose: detect mutation
of states, requests, callbacks, auto-detection, machine type, cached machine,
or published topology.

**Retryable builder failure pattern** (lines 212-225 and 1090-1105):

```python
before = builder_staging_fingerprint(builder)
with pytest.raises(ValueError, match="not registered"):
    builder.build()
assert builder._machine is None
assert builder_staging_fingerprint(builder) == before
builder.add_state(State("missing"))
machine = builder.build()
```

Preserve local candidate construction and late publication. Add coverage for
every canonical adapter failure that can happen during build, including a late
row with a different source, duplicate candidate identity, bad priority, and
async mismatch. A failed build must leave `_machine is None`, staging mutable,
and the builder repairable; only a successful complete build freezes the cache.

**Existing builder build boundary:** `FSMBuilder.build()` (lines 5804-5911)
creates a candidate, adds states, converts staged rows, calls
`candidate.add_transitions(...)`, wires callbacks, and assigns `_machine` only
at the end. Keep this publication order while replacing row conversion with
the raw request carrier. `_preflight_async_requirements()` remains a builder
responsibility; canonical topology validation remains machine-owned.

### `benchmarks/comparison/common.py` (utility, transform/batch record schema)

**Analog:** `tools/artifact_conformance.py` scenario definitions and strict
schema validation (lines 21-83, 1840-2043), plus
`benchmarks/performance_demo.py` constants and sampler (lines 24-29,
118-175).

Use a stdlib-only module. Define fixed scenario IDs, bounded positive counts,
finite numeric samples, implementation IDs, exact requested/resolved versions,
module origin/loader, interpreter/platform labels, preflight status, and an
explicit observation (not threshold) marker. Keep supported/unsupported cells
as data; do not encode a performance minimum for competitor ratios.

**Canonical JSON pattern** from `tools/artifact_conformance.py` (lines 447-449):

```python
json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
```

Apply deterministic key ordering and reject NaN/Infinity, booleans where
numeric counts are expected, empty identity fields, unknown scenario IDs, and
unexpected top-level keys. Validate `requested_version == resolved_version`
and require a non-empty resolved origin. An unsupported capability should carry
a bounded stable reason code and no ratio.

### `benchmarks/comparison/fast_fsm_runner.py` (benchmark adapter, measurement)

**Analog:** `benchmarks/performance_demo.py`, `_runtime_labels()` (lines
104-115) and `collect_priority_group_observations()` (lines 118-175).

```python
origin = Path(core.__file__ or "<unknown>").resolve()
suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
mode = "compiled-native" if str(origin).endswith(suffixes) else "pure-python"
labels = {
    "python": platform.python_version(),
    "implementation": platform.python_implementation(),
    "core_mode": mode,
    "core_origin": str(origin),
    "platform": platform.platform(),
}
```

Use equivalent flat scenarios shared with both competitor children. Run an
untimed semantic preflight first, then warm up and measure only supported
scenarios with `time.perf_counter_ns()`/`statistics.median`. Emit one strict
JSON record on stdout and keep repository output clean by default. Record exact
command and environment labels, but treat rates as descriptive observations.

### `benchmarks/comparison/python_statemachine_2_5.py` and
`benchmarks/comparison/python_statemachine_3_2.py` (benchmark children,
request-response measurement)

**Analog:** `benchmarks/benchmark_py_fsm.py` (lines 1-30, 46-123) for the
competitor API shape, and the installed child protocol in
`tools/release_evidence.py` (lines 3126-3166, 3260-3281) for identity and
strict JSON output.

The child scripts must be self-contained PEP 723 scripts with exact inline
dependencies (`python-statemachine==2.5.0` and `==3.2.1`, respectively). They
must not import the other competitor, Fast FSM, or the project dependency
environment. Each child should:

1. resolve and report `importlib.metadata.version("python-statemachine")`;
2. report the imported module `__file__` and loader, interpreter, platform, and
   exact requested version;
3. execute required untimed flat-machine preflight values (initial state,
   alternating cycle, false guard behavior);
4. emit explicit unsupported records when a requested optional scenario cannot
   be represented; and
5. only time scenarios whose preflight passed.

Do not infer semantic equivalence from matching function names. Keep the child
stdout to one bounded JSON object; send human diagnostics to stderr or fail
closed.

### `benchmarks/comparison/run_comparison.py` (orchestrator, subprocess/
aggregation)

**Analog:** `tools/release_evidence.py` subprocess invocation and strict child
acceptance, especially `_run_installed_command()` (around lines 2680-2750),
`validate_installed_compiled_performance()` (lines 2965-3051), and the
parent acceptance order described in research.

The parent must never import `statemachine`. Construct exact child commands,
run them in isolated subprocesses, bound output and execution, parse strict
JSON, then validate in this order:

```text
parse strict JSON
  -> exact schema and bounded values
  -> requested version == resolved version
  -> module origin and interpreter identity
  -> semantic preflight required values
  -> supported timing samples
  -> medians and same-run ratios
```

Reject malformed or contradictory child records. Preserve unsupported cells
with stable reason codes and omit their ratios. Include Fast FSM and both exact
competitor identities in a labelled observation envelope. Output to stdout by
default, with persistence only through an explicit path argument.

### `benchmarks/comparison/*.lock` (generated config, dependency resolution)

**Analog:** none in the repository. Use uv’s documented adjacent PEP 723
script lock convention from `26-RESEARCH.md`, not a hand-written lock format.

Generate only after the human legitimacy checkpoint for the exact upstream
package releases. The lock files must be produced with:

```bash
uv lock --script benchmarks/comparison/python_statemachine_2_5.py
uv lock --script benchmarks/comparison/python_statemachine_3_2.py
```

They are checked-in reproducibility artifacts and must not be added to the
project’s ordinary dependency graph. Never hand-edit generated lock contents;
rerun uv with the corresponding script when metadata changes.

### `tests/test_competitor_benchmark_contract.py` (test, schema/subprocess
contract validation)

**Analog:** `tests/test_artifact_conformance.py` strict scenario assertions
(lines 94-120, 396-464) and `tests/test_release_evidence.py` isolated command,
schema, and static workflow tests (lines 108-119, 268-319, and the phase-20
static contract tests near 4540).

Use fixture dictionaries and pure contract helpers rather than installing or
timing competitors in tests. Cover:

- exact requested/resolved version and origin acceptance;
- malformed or extra fields, NaN/Infinity, negative/zero sample values, and
  oversized output rejection;
- semantic preflight failure versus explicit unsupported cell;
- no ratio when either side is unsupported;
- command construction invokes exact locked scripts and no parent competitor
  import;
- `pyproject.toml` has no comparator dependency in ordinary groups;
- ordinary `.github/workflows/ci.yml` has no comparator runner/task invocation;
- no performance threshold assertion exists for comparator observations.

Use `tmp_path`, `monkeypatch`, and subprocess fixtures only for bounded command
behavior. Do not make ordinary CI download third-party packages.

### `Taskfile.yml` (config/integration entry point, subprocess request-response)

**Analog:** existing benchmark tasks (lines 208-223) and release evidence
tasks elsewhere in the file.

```yaml
benchmark:
  desc: Run environment-labelled priority-group performance observations
  cmds:
    - uv run python benchmarks/performance_demo.py

benchmark-compare:
  desc: Run comparison benchmarks against other FSM libraries
  cmds:
    - uv run python benchmarks/benchmark.py
```

Keep `benchmark` and `benchmark-compiled` unchanged for Fast FSM observations.
Point `benchmark-compare` to the new parent orchestrator and describe it as a
manual, environment-sensitive observation. Do not make it a dependency of
`test`, `quality`, `check`, release evidence, or any ordinary CI task. Use only
`uv` commands and avoid implicit output files.

### `pyproject.toml` (config, dependency resolution)

**Analog:** dependency groups (lines 11-38).

```toml
[dependency-groups]
benchmarks = [
    "matplotlib>=3.10.3",
    "networkx>=3.2",
    "python-statemachine>=2.5.0",
    "transitions>=0.9.3",
]
```

Remove comparator packages from shared groups if the old combined runner is no
longer authoritative (including the legacy `transitions` comparator if it has
no isolated task). Preserve project runtime/dev/release/docs dependencies.
Regenerate `uv.lock` with uv and verify that ordinary `uv sync --locked
--all-groups` no longer supplies an implicit comparator environment.

### `uv.lock` (generated config, dependency resolution)

**Analog:** current project lock generated from `pyproject.toml`.

Regenerate only after the dependency-group edit, using the approved uv command.
Treat the lock as generated output: review the diff for removed root comparator
requirements and unrelated resolution churn. Do not manually add exact
competitor versions to this project lock; exact competitors belong only in
adjacent script locks.

### `.specify/memory/spr-core-api.md` / `docs/dev/architecture.md` (architecture
documentation, explanatory transform; conditional)

**Analog:** canonical topology and performance sections in
`.specify/memory/spr-core-api.md`, and “Canonical Topology and Private Graph
Projection” in `docs/dev/architecture.md`.

If the private request carrier/transaction is materially different from the
current documented seam, update the SPR in the same commit as the source change.
Document that adapter parsing feeds one private normalization/publication
transaction, publication is off-table and atomic, and the direct singleton
dispatch path is untouched. Keep benchmark evidence language observational and
environment-labelled. Do not add a new public registrar or claim competitor
timings are CI gates.

## Shared Patterns

### Atomic topology publication

**Sources:** `src/fast_fsm/core.py:1733-1860`; `tests/test_graph_invariants.py:21-59,318-383`.

All public adapters may parse their own syntax, but every candidate must pass
through one private normalization path and one complete off-table commit.
Invalid later inputs leave every published table, state identity, graph
version, current state, and builder cache unchanged.

### Builder staging and retryability

**Sources:** `src/fast_fsm/core.py:5804-5911`; `tests/test_builder.py:130-225,1090-1105,2096-2150`.

Builder staging is mutable until successful publication. A failed candidate is
discarded; no transient machine type or cached machine leaks into the builder.
The test repairs the staged input and retries a successful build.

### Strict, bounded evidence

**Sources:** `tools/artifact_conformance.py:447-449,1840-2043`;
`tools/release_evidence.py:2965-3051,3089-3166`; `tests/test_artifact_conformance.py:94-120,396-464`.

Use deterministic JSON, finite bounded scalar values, runtime identity/origin
proof, and semantic facts before timing. Treat unsupported capabilities as
explicit records, never zero-valued performance or a false ratio.

### Isolated subprocess execution

**Sources:** `tests/test_release_evidence.py:108-119,268-319` and the installed
child machinery in `tools/release_evidence.py:2680-2750`.

Bound command output and time, fail closed on malformed JSON, and keep
third-party imports outside the parent and ordinary CI environment. The manual
Taskfile command is the only comparison timing entry point.

### Hot-path protection

**Sources:** `.github/copilot-instructions.md:49-66`;
`.specify/memory/spr-core-api.md` performance rules;
`benchmarks/performance_demo.py:104-175`.

Do not add construction-carrier references, topology scans, sorting, reflection,
or allocation to `trigger()`/`can_trigger()`. Construction work is cold and
local; singleton dispatch remains direct O(1), while finite candidate work
remains local O(k).

## No Exact Analog Found

These are intentionally new patterns; planner should use `26-RESEARCH.md` for
the detailed contract and not copy an unrelated implementation:

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `benchmarks/comparison/python_statemachine_2_5.py.lock` | generated config | file I/O / dependency resolution | No existing PEP 723 script lock in repository. |
| `benchmarks/comparison/python_statemachine_3_2.py.lock` | generated config | file I/O / dependency resolution | Same; generated by uv after legitimacy review. |

## Metadata

**Analog search scope:** `src/fast_fsm/core.py`, `tests/`, `benchmarks/`,
`tools/`, `Taskfile.yml`, `pyproject.toml`, `uv.lock`, `.github/workflows/`,
`.specify/memory/`, and `docs/dev/`.  
**Files scanned:** 14 existing source/test/tool/config/documentation files plus
the phase context, research, and validation artifacts.  
**Pattern extraction date:** 2026-09-15  
**Planner note:** Keep Phase 26 limited to BUILD-04, BUILD-05, PERF-05, and
PERF-06. Final-state fields, internal transitions, rejection semantics, public
builder deprecations, and persistence metadata are deferred to later phases.
