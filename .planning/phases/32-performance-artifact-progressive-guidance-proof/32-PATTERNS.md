# Phase 32: Performance, Artifact & Progressive Guidance Proof - Pattern Map

**Mapped:** 2026-09-19  
**Files analyzed:** 16 likely modified files (8 implementation/tooling/config files and 8 test/documentation/example files)  
**Analogs found:** 16 / 16 (same-file extension patterns; no new runtime module is implied)

Phase 32 is an evidence-and-teaching phase. The closest analog for every
planned change is already in the repository: extend the existing conformance
collector, release verifier, descriptive benchmark, controller-owned example,
and builder-first documentation. Do not introduce a second artifact harness,
benchmark policy, or tutorial architecture.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tools/artifact_conformance.py` | utility / evidence collector | transform: FSM behavior → scalar JSON oracle | Existing scenario definitions, collectors, and validators in the same file | exact |
| `tests/test_artifact_conformance.py` | test | batch / transform | Existing required-value and mutation tests in the same file | exact |
| `tools/release_evidence.py` | service / release verifier | file-I/O + request-response subprocess probes | `verify_source()`, installed-wheel verification, and native performance validator in the same file | exact |
| `tests/test_release_evidence.py` | test | file-I/O / subprocess boundary | Existing source-origin, wheel identity, and fail-closed evidence tests | exact |
| `tests/test_installed_artifacts.py` | integration test | file-I/O + installed artifact request-response | Existing pure/compiled wheel fixture and parity tests | exact |
| `benchmarks/performance_demo.py` | utility / benchmark reporter | batch transform: repeated triggers → labelled observations | `collect_priority_group_observations()` and `_runtime_labels()` | exact |
| `tests/test_performance_benchmarks.py` | test | transform / invariant measurement | Existing topology-scaling, local-work, and reporter-label tests | exact |
| `Taskfile.yml` | config / task orchestration | batch subprocess workflow | Existing `release-installed-artifacts-check`, `release-baseline-*`, and docs tasks | role-match |
| `examples/drone_failsafes.py` | component / executable tutorial | streaming: one telemetry sample → one FSM event → committed command | Existing `DroneController`, `TelemetryPolicy`, builder callbacks, and simulated adapter | exact |
| `tests/test_drone_failsafes_example.py` | test | streaming integration | Existing one-sample/one-tick, priority, and post-commit command assertions | exact |
| `README.md` | documentation / executable guidance | request-response examples and migration transform | Existing builder-first sections, priority example, and lifecycle sections | exact |
| `docs/QUICK_START.md` | documentation / quick-start guide | request-response examples | Existing builder recipe, construction hierarchy, and priority pattern | exact |
| `docs/TUTORIAL.md` | documentation / progressive tutorial | request-response examples | Existing four-level tutorial and priority lesson | exact |
| `docs/examples/index.md` | documentation / example index | navigation / request-response | Existing tiered gallery and feature-family map | exact |
| `docs/api/core.md` | documentation / API reference | request-response + executable doctest | Existing priority and expected-rejection sections with `{testcode}`/`{testoutput}` | exact |
| `tests/test_readme_examples.py` | test | transform: docs code regions → executable regression checks | Existing builder/deprecation scan and README example tests | exact |

No new runtime source module is necessary. New semantic scenarios belong in the
shared collector and are copied automatically into neutral installed
environments by the existing release verifier.

## Pattern Assignments

### `tools/artifact_conformance.py` (utility, transform)

**Analog:** the existing scenario registry and standalone collectors in this
file.

**Scenario definition pattern** (lines 28-113):

```python
SCHEMA_VERSION = 1
_SCENARIO_DEFINITIONS = (
    {
        "id": "lifecycle.destination-enter-failure",
        "family": "lifecycle-result-history",
        "fields": _LIFECYCLE_FIELDS,
    },
    {
        "id": "graph.guard-rejection",
        "family": "graph-guard",
        "fields": (...),
    },
)
```

Add final/sink, internal-self, external-self, false-guard, and expected-rejection
rows here with fixed fields and `required_values`. Keep IDs sorted and distinct;
do not overload `graph.guard-rejection`, whose existing meaning is topology and
permission rejection.

**Collector registration pattern** (lines 1811-1837):

```python
def _scenario_collectors() -> tuple[Callable[[], dict[str, Any]], ...]:
    return (
        _lifecycle_destination_enter_failure,
        _graph_guard_rejection,
        _priority_sync_winner,
        # new standalone collectors go here
        _sync_async_equivalence,
    )
```

Each collector must construct a small deterministic machine, return only
allowlisted scalar/list values, and be included exactly once. The same source
file is copied into fresh wheel environments, so imports must remain installed
package + standard library only (lines 1-25).

**Fail-closed validation pattern** (lines 1840-2013):

```python
if set(ids) != set(expected_by_id):
    raise ConformanceError(...)
if ids != sorted(ids):
    raise ConformanceError(...)
if tuple(record) != expected_fields:
    raise ConformanceError(...)
for field, required_value in required_values.items():
    if record.get(field) != required_value:
        raise ConformanceError(...)
```

Extend definitions and collectors together; preserve exact field ordering,
suite digest binding, redaction checks, and `collect_conformance()`'s
`validate_conformance()` call (lines 2016-2040). Never compare only a shared
digest or printed output.

### `tests/test_artifact_conformance.py` (test, batch/transform)

**Analog:** priority contract tests and inventory mutation tests (lines 131-332).

**Concrete expected-record pattern** (lines 138-220):

```python
records = {record["id"]: record for record in payload["scenarios"]}
assert records["priority.sync.winner"] == {
    "id": "priority.sync.winner",
    "family": "priority-selection",
    "success": True,
    ...
}
```

For each new semantic row, assert the complete expected record, especially
`state`, `committed`, lifecycle mode, rejection code, and command/entry facts.
Use the existing `_rehash()` helper (lines 83-91) when deliberately mutating a
record so the test reaches semantic validation rather than failing on a stale
digest.

**Required-value mutation pattern** (lines 224-275):

```python
for field, value in definition["required_values"].items():
    mutated = copy.deepcopy(payload)
    record = next(item for item in mutated["scenarios"] if item["id"] == identifier)
    record[field] = replacement
    _rehash(mutated)
    with pytest.raises(artifact_conformance.ConformanceError):
        artifact_conformance.validate_conformance(mutated)
```

Add parameterized required facts for every new scenario. Also extend the
inventory/ordering and hardened-contract assertions (lines 293-332, 396-465)
so missing, extra, duplicate, unsorted, and false semantic rows fail closed.

### `tools/release_evidence.py` (utility, file-I/O/subprocess)

**Analog:** source-origin preflight and installed-wheel proof in the same file.

**Origin safety pattern** (lines 1709-1772):

```python
shadows = find_native_core_shadows(package_root)
if shadows:
    raise EvidenceError("Native core shadow(s) found ...")
core_module = importlib.import_module(CORE_MODULE_NAME)
if origin.suffix != ".py":
    raise EvidenceError(...)
```

Preserve pure-source preflight before importing `fast_fsm.core`. If a fresh
native build needs a pure rerun, use a path-constrained, recoverable relocation
protocol; do not silently delete or trust a shadow.

**Installed artifact sequencing pattern** (lines 3410-3542):

```python
archive = inspect_wheel(artifact)
environment = _installed_environment()
_run_installed_command([...], stage="environment creation")
_run_installed_command([...], stage="artifact installation")
child = _strict_json_object(_run_installed_command([...], stage="conformance probe"))
conformance, runtime = _extract_child_probe(...)
runtime_record = _validate_runtime_probe(...)
performance = _collect_installed_compiled_performance(...) if ... else None
```

Keep archive identity, mode/build intent, runtime origin/loader, semantic oracle,
and performance in this order. Extend the shared conformance result rather
than creating a second wheel probe. Do not make release publication or a
universal benchmark claim part of this verifier.

**Durable native floor pattern** (lines 2969-3055, 3093-3170):

```python
if checked["statistic"] != "median":
    raise EvidenceError(...)
if numeric_median != float(statistics.median(numeric_samples)):
    raise EvidenceError(...)
if numeric_median < _COMPILED_TRIGGER_OPS_PER_SECOND_MIN:
    raise EvidenceError(...)
```

Leave `_COMPILED_TRIGGER_OPS_PER_SECOND_MIN = 200_000` and the alternating
installed singleton sampler unchanged. Add feature-cost observations beside
this validator with explicit labels; never fold final/self/rejection costs into
the unfeatured release gate.

### `tests/test_release_evidence.py` (test, file-I/O/subprocess)

**Analog:** clean-source/shadow tests (lines 454-488), synthetic wheel identity
tests (lines 168-217, 490-539), and bounded child-process tests (lines 268-319).

```python
source_root = _copy_clean_source(tmp_path)
shadow = source_root / "fast_fsm" / "core.fixture.so"
shadow.write_bytes(original)
completed = _run_evidence("verify-source", "--source-root", str(source_root), "--json")
assert completed.returncode != 0
assert shadow.read_bytes() == original
```

Use isolated `tmp_path` archives/trees and assert exact failure messages and
non-mutation. For new origin/build seams, test both valid exact modes and
contradictory identity surfaces. Keep subprocesses bounded and use `_run_evidence()`
instead of ad hoc shell execution.

### `tests/test_installed_artifacts.py` (integration test, file-I/O)

**Analog:** module-scoped concrete wheel fixtures and clean-source parity (lines
163-229).

```python
@pytest.fixture(scope="module")
def tracer_wheels(...):
    return {mode: _build_wheel(root / mode, mode) for mode in ("pure", "compiled")}

record = release_evidence.verify_installed_wheel(
    wheel, expected_mode=mode, build_intent=mode
)
assert artifact_conformance.compare_conformance(
    clean_source_conformance, record["conformance"]
) == []
```

Extend the existing pure/compiled matrix to assert the new oracle rows and
exact-origin parity. Keep the fresh-wheel fixture module-scoped, and retain the
compiled-only `median_ops_per_second >= 200_000` assertion (lines 223-229).

### `benchmarks/performance_demo.py` (utility, batch transform)

**Analog:** `_build_priority_group_machine()`, `_runtime_labels()`, and
`collect_priority_group_observations()` (lines 24-175).

```python
def _runtime_labels() -> dict[str, str]:
    origin = Path(core.__file__ or "<unknown>").resolve()
    mode = "compiled-native" if str(origin).endswith(suffixes) else "pure-python"
    return {"python": ..., "implementation": ..., "core_mode": mode,
            "core_origin": str(origin), "platform": ...}

elapsed_samples = [measure_time(operation, iterations) for _ in range(sample_count)]
observations.append({**labels, "winner_position": winner_position,
                     "guard_evaluations": expected_guard_evaluations,
                     "sample_count": sample_count,
                     "iterations": iterations,
                     "operations_per_second": iterations / statistics.median(elapsed_samples)})
```

Add final-state, internal-self, external-self, and expected-rejection scenarios
as separately named, reachable fixtures. Use fixed sample/iteration counts,
runtime origin and environment labels, and structural guard-work checks. Keep
benchmark instrumentation outside the production `trigger()` hot path.

### `tests/test_performance_benchmarks.py` (test, transform/invariant)

**Analog:** constant lookup and local priority work tests (lines 143-165,
181-258, 280-361) and reporter schema test (lines 364-390).

```python
def test_priority_group_work_stops_at_winner_and_ignores_unrelated_topology():
    ...
    assert guard_calls == ...
    assert sum(counts.values()) == _expected_mapping_operations()
```

Test that singleton dispatch remains two direct lookups independent of graph
size; test each new scenario's local work shape independently of unrelated
topology. For reporter rows, assert labels and fields, not a universal
throughput number. Preserve the existing no-sort/no-unrelated-scan AST checks
(lines 261-277).

### `Taskfile.yml` (config, batch subprocess workflow)

**Analog:** `release-baseline-*`, `release-installed-artifacts-check`,
`docs-check`, and `docs-test` tasks (lines 120-145, 239-255, 297-333).

```yaml
release-installed-artifacts-check:
  deps:
    - task: pure-source-check
  cmds:
    - |
        uv run python - <<'PY'
        ...
        release_evidence.verify_installed_wheel(...)
        ...
        PY
```

Reuse existing locked `uv` tasks and keep write/check behavior distinct. If a
new task is needed for labelled descriptive observations, make it read-only and
call the existing benchmark/evidence module. Do not add an offline/cache/uv
version policy or an automatic baseline rewrite.

### `examples/drone_failsafes.py` (component, streaming)

**Analog:** existing controller-owned telemetry loop and builder callbacks (lines
104-181, 184-285, 288-341).

**Fact-only policy and one-event boundary** (lines 104-137, 309-326):

```python
def heartbeat_older_than(self, seconds: float) -> bool:
    if self._last_heartbeat_at is None:
        return True
    return self._clock() - self._last_heartbeat_at > seconds

def update_from_telemetry(self, sample: TelemetrySample) -> TransitionResult:
    self._telemetry_policy.observe(sample)
    return self._report(
        self._fsm.trigger("telemetry_tick", telemetry_policy=self._telemetry_policy)
    )
```

Keep `TelemetryPolicy` as measured facts only; all state-dependent eligibility
and precedence remains in FSM guards. Every sample produces one `telemetry_tick`.

**Priority and post-commit command pattern** (lines 217-285):

```python
.add_transition("telemetry_tick", ["Takeoff", "Mission"], "ReturnHome",
                condition=FuncCondition(link_lost, name="link_lost"), priority=10)
...
builder.on_enter(state_name, report_state_entry(state_name))
builder.on_enter(state_name, issue_aircraft_command(command))
```

Extend with the required internal-self, external-self, explicit-final landing,
and expected-rejection teaching beats. Keep commands bound with
`FSMBuilder.on_enter()` after commit; do not subclass `State`, route priority in
controller `if` statements, add a scheduler, or claim flight safety.

### `tests/test_drone_failsafes_example.py` (test, streaming integration)

**Analog:** one-observation boundary test (lines 110-149), simultaneous priority
test (lines 151-207), and ineligible/no-command test (lines 209-230).

```python
assert policy.observations == 1
assert len(counting_fsm.calls) == 1
assert counting_fsm.calls[0][0] == "telemetry_tick"
...
assert aircraft.commands == ["command_emergency_land"]
assert aircraft.states_when_commanded == ["EmergencyLanding"]
```

Add lifecycle counters to distinguish internal self from external self, assert
final landing cannot transition out, and assert `TransitionRejected(code)` is a
committed-false, command-free terminal outcome while a false guard is ordinary
selection ineligibility. Keep tests deterministic and adapter-replaceable.

### `README.md`, `docs/QUICK_START.md`, `docs/TUTORIAL.md` (documentation,
request-response examples)

**Analog:** existing builder-first opening and progressive sections in README
lines 1-25, 72-156, 158-249, 251-318; Quick Start lines 25-68, 70-165; Tutorial
levels 1-4 and priority lesson lines 159-198.

**Builder-first pattern:**

```python
machine = (
    FSMBuilder(State("idle"), name="Worker")
    .add_state(State("running"))
    .add_transition("start", "idle", "running")
    .build()
)
```

Lead with this small recipe, then layer conditions, priority, callbacks, async,
finality, rejection, diagnostics, persistence, and performance. For each
deprecated convenience (`simple_fsm`, `quick_fsm`, `quick_build`, `from_states`)
show a concrete builder replacement and the v0.5.x warning/removal timing.
Keep direct constructors, `from_dict()`, and declarative states explicitly
supported where their stated use fits.

**Runnable distinction pattern:** reuse the priority examples' exact output and
assertions, then add paired examples for final-vs-sink, false-vs-rejected, and
internal-vs-external self. Keep documentation snippets compatible with the
existing README/example regression scanner and Sphinx doctest conventions.

### `docs/examples/index.md` (documentation, navigation)

**Analog:** current tiered gallery and feature-family map (lines 1-122).

Keep one primary lesson per example and a progressive tier order. Update the
drone entry to mention all new teaching beats while retaining the warning that
it is deterministic training software. Use `literalinclude` for the full script
but rely on pytest/Sphinx doctest for execution; literal inclusion alone is not
a test.

### `docs/api/core.md` (documentation, executable API reference)

**Analog:** existing priority `{testcode}`/`{testoutput}` block and expected
rejection section (lines 47-167).

```markdown
```{testcode}
result = fsm.trigger("tick", fatal=False, degraded=True)
print(result.to_state, result.priority)
```

```{testoutput}
fallback 10
```
```

Use executable blocks for exact fields/output when documenting finality,
transition mode, rejection, or artifact-facing behavior. Keep the API
reference's precise distinction between false guard fallthrough, expected
`TransitionRejected`, and ordinary failures.

### `tests/test_readme_examples.py` (test, transform)

**Analog:** active-region builder/deprecation scan (lines 12-52) plus existing
example execution tests (lines 54-139).

```python
regions = _active_python_regions(path)
assert "FSMBuilder" in regions
assert _DEPRECATED_CONSTRUCTION.search(regions) is None
```

Extend the paths/regions only when docs are changed. Keep compatibility names in
prose allowed but reject them in executable teaching regions. Add focused tests
for new exact output or migration examples rather than duplicating the runtime
implementation in test helpers.

## Shared Patterns

### Exact provenance before semantics

**Sources:** `tools/release_evidence.py:1709-1772,3410-3542`,
`tests/test_release_evidence.py:454-488`,
`tests/test_installed_artifacts.py:189-229`.

Apply to all artifact/evidence plans. Establish clean source/native/build mode,
archive identity, loader, and runtime path before accepting semantic rows or
performance measurements. Keep generated native shadows recoverable and never
silently clean user files.

### Strict scalar oracle

**Sources:** `tools/artifact_conformance.py:42-113,1811-2040`,
`tests/test_artifact_conformance.py:224-332`.

Apply to all artifact-mode semantic scenarios. Every row has a fixed ID/family/
field schema, independent required values, stable ordering, payload redaction,
suite digest, and mutation tests.

### Environment-labelled observations

**Sources:** `benchmarks/performance_demo.py:104-175`,
`tests/test_performance_benchmarks.py:364-390`,
`tools/release_evidence.py:2969-3055`.

Apply to descriptive feature-cost benchmarks. Report runtime/build origin,
platform, sample count, iterations, scenario/work shape, and median. Use only
the existing fresh installed compiled singleton threshold as a durable gate.

### One input, one event, committed effects

**Sources:** `examples/drone_failsafes.py:309-341`,
`tests/test_drone_failsafes_example.py:110-230`.

Apply to the drone tutorial. The controller observes facts and sends exactly one
event; FSM guards select; adapter commands run from committed entry callbacks.
False guards, expected rejections, and final states must not issue commands.

### Progressive builder-first documentation

**Sources:** `README.md:72-156`, `docs/QUICK_START.md:25-68`,
`docs/examples/index.md:1-122`, `tests/test_readme_examples.py:27-52`.

Apply to all public docs. Start light, lead with `FSMBuilder`, progressively
introduce advanced features, and keep advanced direct construction and
serialization distinctions explicit.

## No Analog Found

None for the files currently implied by CONTEXT.md and RESEARCH.md. New
scenario logic has same-file analogs; new public docs have existing sections and
test conventions. A planner should use the same-module patterns above rather
than inventing a new harness.

## Metadata

**Analog search scope:** `tools/`, `benchmarks/`, `examples/`, `tests/`,
`README.md`, `docs/`, `Taskfile.yml`, and `.github/copilot-instructions.md`  
**Files scanned:** 16 primary files plus current phase context/research  
**Pattern extraction date:** 2026-09-19
