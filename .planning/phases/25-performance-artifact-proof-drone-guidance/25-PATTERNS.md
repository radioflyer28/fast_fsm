# Phase 25: Performance, Artifact Proof & Drone Guidance - Pattern Map

**Mapped:** 2026-09-07  
**Files analyzed:** 19 implementation, test, benchmark, documentation, policy, and evidence files  
**Analogs found:** 19 / 19 (existing files are the analogs; no new package seam is needed)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/fast_fsm/core.py` | core/runtime utility | request-response / CRUD registration | `src/fast_fsm/core.py` (`_merge_transition_slot`, selectors) | exact |
| `tests/test_priority_selection.py` | unit/integration test | request-response, sync/async | same file's winner, exhaustion, exception, and cancellation tests | exact |
| `tests/test_performance_benchmarks.py` | structural/performance test | request-response / measurement | same file's counting-dict and local-group tests | exact |
| `benchmarks/performance_demo.py` | benchmark CLI/demo | batch measurement / transform | same file's existing `main()` and measurement helpers | role-match (stale claims) |
| `benchmarks/benchmark_fast_fsm.py` | benchmark fixture/CLI | batch measurement | same file's benchmark fixtures | role-match (no reporting entry point) |
| `tools/artifact_conformance.py` | conformance utility/oracle | transform / request-response | same file's scenario registry and collector | exact |
| `tools/release_evidence.py` | release verifier | file I/O / request-response | same file's `verify_installed_wheel()` | exact |
| `tests/test_artifact_conformance.py` | schema/contract test | transform / validation | same file's inventory and mutation tests | exact |
| `tests/test_installed_artifacts.py` | integration/artifact test | file I/O / isolated request-response | same file's `tracer_wheels` and installed parity test | exact |
| `examples/drone_failsafes.py` | example component/controller | event-driven request-response | same file's `DroneController`, `TelemetryPolicy`, and `AircraftCommands` | exact (routing is stale) |
| `tests/test_drone_failsafes_example.py` | executable example test | event-driven request-response | same file's module-loader and heartbeat fact test | role-match |
| `README.md` | public documentation | transform/presentation | current design-principles and performance table | role-match (stale wording) |
| `docs/dev/architecture.md` | architecture documentation | transform/presentation | current core data-structure and trigger explanation | role-match (stale topology) |
| `docs/examples/index.md` | example documentation | transform/presentation | current `literalinclude` gallery entries | exact |
| `.github/copilot-instructions.md` | maintainer policy/config | transform/presentation | current performance, release, and test rules | role-match (stale O(1) blanket) |
| `.planning/PROJECT.md` | project contract/config | transform/presentation | current Core Value, constraints, and priority decisions | role-match |
| `.specify/memory/spr-core-api.md` | stable API reference | transform/presentation | current priority and performance contract rows | exact |
| `Taskfile.yml` | workflow/config | batch / file I/O / request-response | current benchmark, docs, and installed-artifact tasks | exact |
| `evidence/release-baseline.json` | generated evidence artifact | file I/O / batch | current release baseline schema and observations | exact (regenerate, do not hand-edit) |

The research text names `tests/test_priority_transitions.py`; the checked-out equivalent is `tests/test_priority_selection.py`, which contains the complete sync/async candidate-group suite and should be treated as the intended seam.

## Pattern Assignments

### `src/fast_fsm/core.py` (core/runtime, request-response + CRUD registration)

**Analog:** `src/fast_fsm/core.py`

**Immutable topology pattern** (lines 655-681):

```python
@dataclass(frozen=True, slots=True)
class _TransitionGroup:
    """Private immutable, ascending-priority candidates for one slot."""

    entries: Tuple[TransitionEntry, ...]

_TransitionSlot = Union[TransitionEntry, _TransitionGroup]
```

Keep the direct `TransitionEntry` singleton and promote only competing candidates to `_TransitionGroup`; preserve frozen/slotted/tuple-backed storage and do not add a dispatch-time sort.

**Registration/atomicity pattern** (lines 1687-1710, 1713-1739): `_commit_transition_plan()` accumulates replacements, compares object identity against original slots, writes only changed slots, and advances `_graph_version` once. `_merge_transition_slot()` constructs a new candidate, returns the existing slot for an exact duplicate, and raises `ValueError("transition priority is already registered for this slot")` for a different same-priority candidate. Replace only the final `tuple(sorted(...))` with one scan over already-ordered `entries`, recording the first greater priority and splicing once:

```python
insert_at = len(entries)
for index, entry in enumerate(entries):
    if entry.priority == candidate.priority:
        if (entry.to_state is candidate.to_state
                and entry.condition is candidate.condition
                and entry.condition_ref == candidate.condition_ref):
            return existing
        raise ValueError("transition priority is already registered for this slot")
    if entry.priority > candidate.priority:
        insert_at = index
        break
return _TransitionGroup(entries[:insert_at] + (candidate,) + entries[insert_at:])
```

**Selection pattern** (lines 2354-2416; async equivalent 4221-4278): perform `self._transitions.get(current_name)` then `entries.get(trigger)`. For a group, iterate its stored ascending tuple and return the first non-`None` fully eligible candidate; normal exhaustion returns `_PRIORITY_GROUP_EXHAUSTED_ERROR` at stage `selection`. A singleton remains on the direct `_select_*_candidate(..., scan_group=False)` branch. Async selection awaits candidates sequentially; cancellation/exception must not fall through.

**Public complexity docs to correct** (lines 2270-2275 and 3554-3568): current docstrings say unconditional `O(1)` and `~250,000`; change to lookup/singleton dispatch `O(1)`, grouped selection/local mutation `O(k)`, and environment-labeled throughput while preserving `*args, **kwargs` and `TransitionResult` behavior.

### `tests/test_priority_selection.py` (unit/integration, request-response sync/async)

**Analog:** same file, especially lines 110-149, 220-289, 292-335, and 480-591.

**Sync winner/lifecycle pattern** (lines 540-591): register candidates out of order, use recording guards, enable history, invoke one trigger with payload, and assert selected target, history tuple, exact guard/permission/lifecycle order, and payload forwarding. Extend this style for insertion beginning/middle/end and exact priority metadata.

**Exhaustion and exception pattern** (lines 665-758): all-false candidates produce one failed `TransitionResult` with `committed=False`, stage `selection`, error `No eligible transition candidate`, unchanged current state/history, and all guard labels in priority order; a raising guard produces terminal stage `guard`, retains the exact hidden cause, and does not evaluate lower candidates.

**Async pattern** (lines 110-150, 220-289, 292-335): `AsyncCondition.check_async()` records order and yields; assert sequential evaluation, no speculative lower candidate, stage/cause on exception, and cancellation at the current priority. Cancellation is re-raised after one observer finalization and the machine remains reusable (`recover` succeeds).

### `tests/test_performance_benchmarks.py` (structural/performance, request-response + batch measurement)

**Analog:** same file.

**Direct-registry counting pattern** (lines 44-105, 120-155): `_CountingDict` wraps only `_states` and `_transitions`; compare exact operation counts across `_COMPLEXITY_TOPOLOGY_SIZES = (4, 64, 512)` and assert a fixed upper bound. Reuse this seam to prove source/trigger lookup is independent of unrelated graph size.

**Local group pattern** (lines 158-235): a slotted `State` records permission calls and a slotted `Condition` records guard labels; register priorities out of order and assert guard/permission calls stop at the winner (`first`, `second`, `winner`) for every unrelated topology size. Add depth `2`, `8`, `32`, first/middle/last winners, exhaustion, and insertion tests here; assert counts/order, never fragile timing ratios.

**Throughput gate pattern** (lines 757-824): warm a minimal two-state toggle, time 200,000 unasserted transitions, detect compiled mode from `find_spec("fast_fsm.core").origin` suffix, and retain compiled floor `>= 200_000` (pure floor `30_000`, coverage bypass). This is a hard gate only for the established installed compiled path; descriptive group timings must include environment metadata.

### `benchmarks/performance_demo.py` (benchmark CLI, batch measurement)

**Analog:** same file's `measure_time()`, `performance_header()`, and `main()` (lines 15-27, 255-268). Preserve the human-readable sectioned output and add a real callable entry point for a representative priority-group matrix. Replace blanket claims at lines 270-278 (`All operations maintain O(1)`, fixed `~250K`, `1000x`) with observed values labeled by Python version, implementation/loader, platform, topology/group depth, winner position, guard count, and sample count. Use repeated high-resolution timing for observations; structural tests remain the complexity proof.

### `benchmarks/benchmark_fast_fsm.py` (benchmark fixture/CLI, batch measurement)

**Analog:** existing fixture classes and setup (lines 1-296). It currently defines benchmark data but no command-line reporting entry point. Either add a small `main()`/matrix reporter following `performance_demo.py`'s section/output style or change the Taskfile target to invoke the descriptive demo; do not claim this fixture alone proves Big-O.

### `tools/artifact_conformance.py` (shared conformance oracle, transform/request-response)

**Analog:** same file.

**Imports and portability** (lines 1-26): the module deliberately imports the installed `fast_fsm` package plus standard library only; keep the copied child probe checkout-independent and payload-free.

**Scenario registry pattern** (lines 42-256): every scenario has a stable `id`, `family`, ordered `fields`, and optional `required_values`. Add sorted sync/async priority scenarios for winner, exhaustion, guard exception, and cancellation. Required values must assert exact target/priority, guard order, result/history priority, stage, terminal state, and cancellation/reuse facts; keep `SCHEMA_VERSION = 1` if the top-level shape is unchanged.

**Collector and validation pattern** (lines 1267-1440): append standalone collector functions to `_scenario_collectors()`, sort records by ID, require exact inventory/field tuples, apply `required_values`, recompute suite and semantic SHA-256, and reject payload sentinels. Follow existing real-FSM collectors such as `_lifecycle_destination_enter_failure()` (291-346) and `_sync_async_equivalence()` (465-556); return deterministic scalar/list records only.

**Comparison pattern** (lines 1443-1460): use `compare_conformance(expected, actual)` for source-to-wheel parity; report only scenario/field names. Equal records are insufficient, so required values must independently establish correctness.

### `tools/release_evidence.py` (release verifier, file I/O + isolated request-response)

**Analog:** `verify_installed_wheel()` (lines 3311-3443).

**Fresh-origin pattern:** validate explicit `expected_mode`/`build_intent`, compute expected suite digest, snapshot the wheel and SHA-256, inspect archive mode, create a `uv venv --no-project --no-config` under a neutral directory, recheck the snapshot hash, install the exact archive, copy the oracle probe, and run it with `--installed-probe` (3318-3401). Validate runtime origin/loader/architecture before accepting conformance.

**Child-schema pattern** (3216-3270): accept only the fixed conformance keys, schema version 1, SHA-256 digests, nonempty scenario list, bounded scalar records, no forbidden fields/tokens, and recomputed semantic digest. Extend nothing with payload-bearing telemetry.

**Installed performance pattern** (3006-3083, 3413-3422): warm alternating singleton transitions, collect at least three samples, report median plus interpreter/platform/mode/loader metadata, and run it only for compiled expected mode. Keep the `ExtensionFileLoader` and `>=200_000` assertions in tests, not as an accidental group benchmark threshold.

### `tests/test_artifact_conformance.py` (oracle contract, transform/validation)

**Analog:** same file's `test_tracer_lifecycle_record_is_stable_and_payload_safe()` (67-102), inventory test (119-128), mutation test (130-158), and hardened observation test (222-290).

Assert collection is deterministic, families and IDs are complete/sorted, and each new priority record has exact required values. Extend negative mutations to remove/duplicate/reorder priority scenarios, alter required winner/order/stage/priority fields, add unallowlisted fields, and inject payload sentinels; call `_rehash()` only when testing post-digest validation rather than bypassing schema checks.

### `tests/test_installed_artifacts.py` (integration, file I/O + isolated request-response)

**Analog:** `_build_wheel()`/`tracer_wheels` (162-185) and `test_tracer_installs_exact_artifact_and_matches_source_lifecycle()` (188-218).

Build exactly one explicit `pure` and one `compiled` wheel with `FAST_FSM_BUILD_MODE`, invoke `release_evidence.verify_installed_wheel()` by absolute path, assert runtime mode/origin and payload-free conformance, then compare each installed record to a clean-source `artifact_conformance.collect_conformance()` baseline. Preserve compiled `core_loader == "ExtensionFileLoader"`, median `>= 200_000`, and `len(samples_ops_per_second) >= 3`; pure performance remains `None`.

### `examples/drone_failsafes.py` (controller example, event-driven request-response)

**Analog:** current classes and builder (lines 16-138, 141-183, 197-267, 270-319).

**Composition/adapter pattern** (16-87, 270-284): retain `AircraftCommands(Protocol)`, slotted `SimulatedAircraft`, `DroneState` post-commit entry action, and `DroneController` ownership of aircraft, telemetry policy, and FSM. `SimulatedAircraft` stays replaceable hardware and never subclasses the FSM.

**Fact-only telemetry pattern** (89-138, 141-183): `TelemetryPolicy.observe()` stores the latest normalized sample and heartbeat timestamp; `heartbeat_older_than()` and `.sample` expose facts. Guards (`battery_critical`, `link_lost`, `critical_fault_present`, etc.) query facts and remain side-effect-free; they must not return event/state/command decisions.

**Required routing replacement:** delete `TELEMETRY_EVENT_PRIORITY` and the loop at lines 186-194 and 291-311. Register competing state-local candidates on one trigger named `telemetry_tick`, with lower exact integer priorities for more urgent faults (critical before link loss before low battery). `update_from_telemetry()` should observe once and call `self._fsm.trigger("telemetry_tick", telemetry_policy=self._telemetry_policy)` exactly once, returning `TransitionResult`; bound state entry actions issue only the selected command after commit. Keep the training/non-hardware disclaimer at lines 1-7.

### `tests/test_drone_failsafes_example.py` (example contract, event-driven request-response)

**Analog:** module loader `_load_example_module()` (8-17) and heartbeat fact test (20-33). Load the script by file path without making `examples` a package. Extend with a fake/counting `AircraftCommands` adapter and controller tests proving one update invokes one `telemetry_tick`, simultaneous critical/link/low selects critical, link+low selects link, healthy ticks do not transition, selected entry command fires exactly once after commit, and `TelemetryPolicy` remains a fact provider.

### `README.md` (public docs, presentation/transform)

**Analog:** current Design Principles and Performance Characteristics table (712-734). Preserve concise table style, but split operations: source/trigger lookup and singleton dispatch `O(1)`; grouped selection and finite group mutation `O(k)`; `add_state()` remains `O(1)`; `FSMBuilder.build()` remains one-time `O(n)`. Replace the current blanket line 716 and rows 726-730. Link the runnable drone example and describe one telemetry tick entering FSM-owned priority resolution.

### `docs/dev/architecture.md` (architecture docs, presentation/transform)

**Analog:** current StateMachine hierarchy and data-structure table (54-72). Change `_transitions` from `dict[str, dict[str, TransitionEntry]]` to the singleton-or-group slot topology (`TransitionEntry | _TransitionGroup`), explain stored ascending groups and local `O(k)` selection/mutation, and preserve the direct two-dictionary lookup explanation for singleton dispatch. Use the existing canonical topology/atomicity section (74-95) to explain immutable publication and version-neutral duplicates.

### `docs/examples/index.md` (example docs, presentation/transform)

**Analog:** existing `literalinclude` gallery entry style (18-24) and drone section (52-74). Keep source displayed via `literalinclude` rather than copying code. Rewrite the drone prose to say one normalized sample is observed, one `telemetry_tick` is dispatched, guards own fail-safe precedence, and callbacks command the adapter after commit; remove “offer ordered candidate triggers” and external controller ordering language. Retain explicit non-safety-certified disclaimer.

### `.github/copilot-instructions.md` (maintainer policy/config, presentation/transform)

**Analog:** Performance rules at lines 40-53 and release/test policy at 60-74. Keep `uv`, slots, selective mypyc, clean-source preflight, and compiled floor rules. Replace line 52's blanket `add_transition() O(1)` statement with the D-01 split and state that exact benchmark observations are environment-labeled. Preserve sequential tests and non-destructive release evidence instructions.

### `.planning/PROJECT.md` (project contract/config, presentation/transform)

**Analog:** Core Value/constraints (7-9, 117-123) and priority decisions (77-89, 139-142). Update stale blanket “all core operations O(1)” wording to distinguish lookup/singleton versus local grouped work, while retaining the `>=200,000` compiled target and single-file `core.py`/mypyc boundary. Do not broaden scope into dynamic priorities, schedulers, or telemetry classifiers.

### `.specify/memory/spr-core-api.md` (stable API reference, presentation/transform)

**Analog:** current priority contract rows 9-10, 20-25. This is the checked-out path (not `.specify/spr-core-api.md`). Keep the exact public contract: exact built-in integer priorities, lower-first order, duplicate no-op/conflict failure, direct singleton versus immutable group, local ordered scan, and result/history/trace priority propagation. Update only wording needed to align the D-01 complexity split; preserve all compatibility and callback signatures.

### `Taskfile.yml` (workflow/config, batch + file I/O)

**Analog:** benchmark targets (206-221), docs targets (227-252), installed-artifact task (294-315), and installed performance task (455-474). Keep task dependencies on `pure-source-check`, explicit `FAST_FSM_BUILD_MODE` values, temporary output dirs, one-wheel assertions, and `verify-installed-wheel` CLI. Make `task benchmark` invoke a real descriptive matrix reporter. Make the artifact gate capture a clean source oracle and compare both verified wheel records to it; retain separate compiled performance gate and docs checks. Avoid unreviewed broad cleanup or implicit source-path manipulation.

### `evidence/release-baseline.json` (generated evidence, file I/O/batch)

**Analog:** current manifest generated by `release_evidence.py`. Do not hand-edit JSON. Regenerate through the reviewed pinned uv `0.12.6` workflow after the conformance suite changes, inspect that only expected suite/conformance/benchmark observations changed, then run the read-only freshness check. Preserve environment labels and avoid treating descriptive timings as durable policy.

## Shared Patterns

### Candidate topology and complexity

**Sources:** `src/fast_fsm/core.py:655-681,1687-1739,2354-2416`; `.specify/memory/spr-core-api.md:9-10,20-25`; `tests/test_performance_benchmarks.py:120-235`.

```python
slot = entries.get(trigger) if entries is not None else None
if isinstance(slot, _TransitionGroup):
    for entry in slot.entries:       # already ascending; local O(k)
        selected = self._select_sync_candidate(..., scan_group=True)
        if selected is not None:
            return selected
else:
    return self._select_sync_candidate(cast(TransitionEntry, slot), ..., scan_group=False)
```

Apply D-01 consistently: two direct dictionary lookups and singleton dispatch are O(1); group selection and immutable group mutation are local O(k); no dispatch-time sort or unrelated graph scan.

### Artifact provenance and parity

**Sources:** `tools/release_evidence.py:3216-3443`; `tests/test_installed_artifacts.py:162-218`; `tools/artifact_conformance.py:1416-1470`.

```python
source = artifact_conformance.collect_conformance()
record = release_evidence.verify_installed_wheel(
    wheel, expected_mode=mode, build_intent=mode
)
assert artifact_conformance.compare_conformance(
    source, record["conformance"]
) == []
```

The parent verifier owns snapshot/hash, neutral venv, runtime origin/mode, strict child schema, and installed performance. Use one shared oracle and required values so source, pure wheel, and compiled wheel prove correctness as well as parity.

### Lifecycle and failure semantics

**Sources:** `tests/test_priority_selection.py:665-758,292-335`; `src/fast_fsm/core.py:2398-2403,4260-4265`.

Normal false falls through only within the local candidate group. Exhaustion is one redacted `selection` failure with unchanged state/history. Guard exceptions and async cancellation are terminal at the active candidate, preserve stage/priority/cause semantics, skip lower candidates, finalize observers once, and leave the machine reusable after cancellation.

### Controller-owned one-tick telemetry

**Sources:** `examples/drone_failsafes.py:16-138,197-319`; `tests/test_drone_failsafes_example.py:8-33`; `docs/examples/index.md:52-74`.

```python
def update_from_telemetry(self, sample: TelemetrySample) -> TransitionResult:
    self._telemetry_policy.observe(sample)
    return self._fsm.trigger(
        "telemetry_tick", telemetry_policy=self._telemetry_policy
    )
```

Telemetry services expose observations/facts only. State-local guarded candidates encode precedence; selected `DroneState` entry callbacks invoke the replaceable `AircraftCommands` adapter after commit. No external trigger loop or command in a guard.

### Evidence-safe benchmark reporting

**Sources:** `tests/test_performance_benchmarks.py:40-117,757-824`; `tools/release_evidence.py:3006-3083`; `benchmarks/performance_demo.py:15-27,255-279`.

Use counting/guard-order assertions for asymptotic contracts. Use repeated timing only for environment-labeled observations, including Python version, implementation, loader/mode, platform, topology/group depth, winner position, and sample count. Retain only the established uninstrumented installed compiled singleton median floor as a hard throughput gate.

## No Analog Found

None. All requested changes have an existing implementation or test seam. The only path discrepancies are the research's `tests/test_priority_transitions.py` (actual file: `tests/test_priority_selection.py`) and `.specify/spr-core-api.md` (actual file: `.specify/memory/spr-core-api.md`).

## Metadata

**Analog search scope:** `src/fast_fsm`, `tests`, `benchmarks`, `tools`, `examples`, `docs`, `.github`, `.planning`, `.specify`, `Taskfile.yml`, and `evidence`.  
**Files scanned:** 19 primary files plus existing priority/serialization/property-based test seams.  
**Pattern extraction date:** 2026-09-07
