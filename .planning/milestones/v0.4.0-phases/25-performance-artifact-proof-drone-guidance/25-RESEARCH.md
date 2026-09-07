# Phase 25: Performance, Artifact Proof & Drone Guidance - Research

**Researched:** 2026-09-07
**Domain:** Priority-group complexity, artifact conformance, and controller-owned FSM guidance
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Prove and document the completed priority-aware FSM as users consume it: truthful
complexity/benchmark guidance, equivalent clean source and installed pure/native
artifacts, and a runnable drone-controller example. Do not change priority
registration, selection, construction, or diagnostic semantics.

- **D-01:** Documentation and benchmarks state O(1) source/trigger lookup and
  direct singleton dispatch; finite candidate-group mutation and ordered
  selection are local O(k), with no dispatch-time sort or unrelated graph scan.
- **D-02:** Conformance uses clean source, pure-wheel, and compiled-wheel
  origins to prove the same priority winner, guard evaluation order,
  result/history metadata, exhaustion, exceptions, and cancellation; compiled
  singleton dispatch retains the existing 200,000 ops/sec gate.
- **D-03:** The example owns `TelemetryPolicy`, the FSM, and an `AircraftCommands`
  adapter in a `DroneController`; bound FSM callbacks command the aircraft.
  `SimulatedAircraft` remains replaceable hardware, not an FSM subclass.
- **D-04:** One `telemetry_tick` enters the controller-owned FSM. Guards encode
  fail-safe precedence; telemetry exposes facts such as heartbeat age and does
  not choose events, transitions, states, or commands. — **Reversibility: costly**
  — external dispatch would duplicate and undermine the finite transition model.

### the agent's Discretion

- Select benchmark group depths/winner positions and exact example module/doc
  organization consistent with existing test, artifact, and documentation tools.

### Deferred Ideas (OUT OF SCOPE)

Dynamic priorities, automatic telemetry classifiers, schedulers, parallel
guards, and runtime candidate mutation remain out of scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PERF-01 | “The architecture preserves O(1) source/trigger lookup and singleton dispatch; grouped selection and local group mutation are documented and measured as O(k) without unrelated-graph scans or dispatch-time sorting.” [VERIFIED: `.planning/REQUIREMENTS.md:69-73`] | The current selector already performs two dictionary lookups and either a direct singleton branch or one ordered local scan; the current registrar must replace its per-insertion `sorted()` call with linear ordered insertion before O(k) mutation can be claimed. [VERIFIED: `src/fast_fsm/core.py:1713-1739`; `src/fast_fsm/core.py:2354-2416`] |
| PERF-02 | “Source, pure-wheel, and compiled-wheel artifacts prove the same priority winner, evaluation order, result/history metadata, and failure semantics; compiled singleton dispatch remains ≥200,000 ops/sec.” [VERIFIED: `.planning/REQUIREMENTS.md:74-77`] | Extend the existing shared conformance oracle, then compare clean source to both installed-wheel records. Reuse the existing fresh-environment verifier and compiled median gate. [VERIFIED: `tools/artifact_conformance.py:1267-1470`; `tools/release_evidence.py:3311-3443`; `tests/test_installed_artifacts.py:181-218`] |
| DOC-01 | “Documentation and the drone example show one telemetry event dispatched to FSM-owned priority resolution, while telemetry services provide facts such as heartbeat age without selecting transitions.” [VERIFIED: `.planning/REQUIREMENTS.md:78-79`] | Replace the example's external ordered trigger loop with one `telemetry_tick` candidate group per source state, retaining controller ownership and bound aircraft-command callbacks. [VERIFIED: `examples/drone_failsafes.py:16-318`] |
</phase_requirements>

## Summary

Phase 25 is primarily a proof-and-guidance phase, but one small core correction is required before its promised complexity statement is true. Dispatch already resolves a `(source state, trigger)` slot through O(1) dictionary lookup, preserves a direct singleton branch, and scans only an immutable ascending-priority tuple for a group. [VERIFIED: `src/fast_fsm/core.py:2354-2416`] Registration, however, currently calls `sorted()` every time a candidate is added to an existing slot. [VERIFIED: `src/fast_fsm/core.py:1713-1739`] That is comparison-sort work rather than the locked local O(k) mutation contract. Replace it with a single scan that detects duplicate/conflicting priorities and records the insertion index, then splice the already-ordered tuple once. This is a local algorithm repair, not a semantic redesign.

Artifact proof should remain centered on the existing `artifact_conformance.py` oracle and `verify_installed_wheel()` isolation boundary. The verifier already snapshots the exact wheel, installs it into a fresh neutral environment, verifies origin/mode, collects conformance, and runs installed compiled performance when requested. [VERIFIED: `tools/release_evidence.py:3311-3443`] Add priority-selection scenarios with fixed required values so source, pure wheel, and compiled wheel cannot merely agree on the same incorrect behavior; compare both wheel records against a clean-source baseline; retain the compiled singleton median floor of `200_000`. [VERIFIED: `tests/test_installed_artifacts.py:188-218`]

The drone example presently has the right ownership boundary but the wrong event-routing boundary: `DroneController` loops through an externally ordered tuple of trigger names and stops after the first success. [VERIFIED: `examples/drone_failsafes.py:186-194`; `examples/drone_failsafes.py:270-318`] Register all telemetry-driven alternatives for each state under one `telemetry_tick`, with integer priorities representing failsafe precedence. `TelemetryPolicy` should continue to expose facts such as `heartbeat_older_than()` and the latest sample, while state entry callbacks invoke the replaceable `AircraftCommands` adapter. [VERIFIED: `examples/drone_failsafes.py:16-138`]

**Primary recommendation:** Plan three implementation waves: (1) linearize group insertion and add structural/representative performance evidence, (2) extend the shared conformance oracle and installed-artifact gate, and (3) rewrite and test the drone example plus all stale complexity and usage guidance.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Priority candidate storage and resolution | Core FSM runtime | Tests/benchmarks | The runtime owns canonical `(source, trigger)` slots, ordered immutable groups, and first-eligible selection; tests prove complexity boundaries without adding policy outside the FSM. [VERIFIED: `src/fast_fsm/core.py:611-681`; `src/fast_fsm/core.py:2354-2416`] |
| Priority artifact parity | Release-evidence tooling | Isolated wheel environments | The parent verifier owns artifact identity/origin validation and delegates only the shared semantic probe to clean installed interpreters. [VERIFIED: `tools/release_evidence.py:3273-3443`] |
| Telemetry-to-transition policy | FSM guards owned by `DroneController` | `TelemetryPolicy` fact provider | The controller composes dependencies; telemetry supplies observations and time-derived facts; registered guards own state-specific transition decisions. [VERIFIED: `examples/drone_failsafes.py:89-183`; `examples/drone_failsafes.py:270-318`] |
| Aircraft behavior | FSM state callbacks | `AircraftCommands` adapter | State entry is the committed lifecycle seam for issuing a command, while the protocol keeps simulation and real hardware replaceable. [VERIFIED: `examples/drone_failsafes.py:16-87`] |
| User-facing complexity and example guidance | README/Sphinx/project policy | Core docstrings | The current public and maintainer docs contain stale blanket O(1) statements that must be reconciled with the canonical priority topology. [VERIFIED: `README.md:712-734`; `docs/dev/architecture.md:61-72`; `.github/copilot-instructions.md:35-50`] |

## Project Constraints (from AGENTS.md)

- Use `bd` for all issue tracking; do not create Markdown TODO lists or a second tracker. Programmatic commands use `--json`, and discovered work is linked with `discovered-from`. [VERIFIED: `AGENTS.md:15-77`]
- Use `uv` for Python execution and dependency work; the documented forms include `uv run pytest`, `uv run python`, `uv sync`, and `uv add`. [VERIFIED: `.github/copilot-instructions.md:30-34`]
- Preserve `__slots__` on hot-path classes. The registered exception names are quoted verbatim as “CompiledFuncCondition, TransitionError, and DiagnosticBudgetExceeded.” [VERIFIED: `.github/copilot-instructions.md:37-46`]
- Compiled `trigger()` throughput must remain at least `200,000 ops/sec`; exact benchmark observations must be environment-labeled rather than elevated to durable policy. [VERIFIED: `.github/copilot-instructions.md:5-8`; `.github/copilot-instructions.md:47-50`]
- Mypy is the blocking mypyc compatibility authority; ty remains an independently visible advisory check. [VERIFIED: `.github/copilot-instructions.md:109-123`]
- Run targeted tests while developing, then run the full suite once before merge; the suite runs sequentially. [VERIFIED: `.github/copilot-instructions.md:55-59`; `.github/copilot-instructions.md:93-103`]
- Release evidence must start from pure-source/origin preflight, must not silently delete native shadows, and must use reviewed manifest writes followed by the read-only freshness check. [VERIFIED: `.github/copilot-instructions.md:61-69`]
- Public API or behavior changes require synchronized executable tests, README/API docs, and the stable-programming-reference contract. [VERIFIED: `.github/copilot-instructions.md:244-281`]
- Stage and commit only explicit task paths; never use `git add .` or `git add -A` when concurrent work may exist. [VERIFIED: `.github/copilot-instructions.md:86-88`]

## Standard Stack

### Core

| Component | Version/contract | Purpose | Why Standard |
|-----------|------------------|---------|--------------|
| CPython | Project requires `>=3.10`; validation environment observed `3.12.10`. [VERIFIED: `pyproject.toml:9-15`] | Run source, pure-wheel, and compiled-wheel behavior. | This is the package's declared runtime and the interpreter used by the repository's uv-managed tests. |
| Fast FSM core | In-repository source, version `0.3.0`. [VERIFIED: `pyproject.toml:7-15`] | Store ordered transition groups, resolve candidates, and execute lifecycle callbacks. | The phase must improve proof around the existing API, not introduce another FSM or policy engine. |
| `tools/artifact_conformance.py` | Schema value is quoted verbatim as `SCHEMA_VERSION = 1`. [VERIFIED: `tools/artifact_conformance.py:22-30`] | Single deterministic semantic oracle for source and installed artifacts. | It already validates scenario inventory, payload bounds, suite digest, and semantic digest. [VERIFIED: `tools/artifact_conformance.py:1290-1470`] |
| `tools/release_evidence.py` | In-repository release tooling | Prove exact wheel identity, isolated origin, native/pure mode, semantics, and installed performance. | It already enforces the clean installation boundary and should be extended rather than duplicated. [VERIFIED: `tools/release_evidence.py:3273-3443`] |

### Supporting

| Tool | Verified version/constraint | Purpose | When to Use |
|------|-----------------------------|---------|-------------|
| uv | Release baseline records exact value `"uv": "0.12.6"`; workstation default observed `0.12.9`, and a reviewed `0.12.6` binary is available at `/private/tmp/fast-fsm-uv-0.12.6/uv-aarch64-apple-darwin/uv`. [VERIFIED: `evidence/release-baseline.json:977`] | Resolve/run tools, build wheels, create clean environments. | Use the baseline-pinned binary when regenerating the durable manifest; use uv for every Python command. |
| pytest | Dependency floor `pytest>=8.4.1`; observed environment `8.4.1`. [VERIFIED: `pyproject.toml:31-39`] | Unit, integration, example, and performance-contract tests. | Targeted during implementation, full sequential suite at the phase gate. |
| Ruff | Dependency floor `ruff>=0.12.11`; observed environment `0.12.11`. [VERIFIED: `pyproject.toml:31-39`] | Format and lint changed Python files. | Before type checks and final test gate. |
| mypy/mypyc | `mypy[mypyc]>=1.17.1`; observed environment `1.17.1`. [VERIFIED: `pyproject.toml:31-39`] | Blocking type and compiled-boundary validation. | After core, example, or tooling edits. |
| Sphinx + MyST | `sphinx>=8.0`, `myst-parser>=4.0`; observed `sphinx-build 9.1.0`. [VERIFIED: `pyproject.toml:40-45`] | Render documentation and execute documentation checks. | After complexity/API/example guidance changes. |
| Task | Observed `3.53.1`. [VERIFIED: environment probe on 2026-09-07] | Run repository-defined quality/evidence workflows. | Prefer task targets for compound clean-origin, docs, and artifact checks. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Linear insertion into an already-sorted immutable tuple | Re-sort after every registration | Re-sorting preserves order but contradicts the locked O(k) local-mutation claim; one scan plus one tuple splice preserves all current semantics with linear local work. [VERIFIED: `src/fast_fsm/core.py:655-659`; `src/fast_fsm/core.py:1713-1739`] |
| Shared source/installed conformance oracle | Separate wheel-specific tests | Separate suites can drift and may not prove the same scenario inventory or required values. The current suite digest is explicitly designed to bind the installed probe to the parent. [VERIFIED: `tools/release_evidence.py:3229-3269`; `tools/release_evidence.py:3328-3401`] |
| One FSM `telemetry_tick` | Externally ordered trigger loop | External ordering duplicates precedence and permits application code to select transitions before the FSM sees the observation. The current example exhibits that exact anti-pattern. [VERIFIED: `examples/drone_failsafes.py:186-194`; `examples/drone_failsafes.py:291-311`] |

**Installation:** No new package installation is required. [VERIFIED: `pyproject.toml:1-45`]

## Package Legitimacy Audit

Not applicable: this phase reuses the repository's declared build, test, documentation, and release-evidence dependencies and should add no external package. [VERIFIED: `pyproject.toml:1-45`]

## Architecture Patterns

### System Architecture Diagram

```text
TelemetrySample
      |
      v
TelemetryPolicy.observe(sample)  -- stores observations / derives heartbeat age only
      |
      v
DroneController.update_from_telemetry()
      |
      | exactly one trigger("telemetry_tick", telemetry_policy=policy)
      v
StateMachine
  current-state dict --O(1)--> trigger slot
                                  |
                   +--------------+--------------+
                   |                             |
             singleton entry               ordered group
             direct dispatch               scan first..winner, O(k)
                   |                             |
                   +--------------+--------------+
                                  v
                    commit transition + lifecycle
                                  |
                                  v
                    bound state-entry callback
                                  |
                                  v
             AircraftCommands protocol implementation
                  /                         \
       SimulatedAircraft              real adapter (consumer)

clean source -----------+
pure wheel -> fresh venv +--> shared conformance oracle --> exact record comparison
compiled wheel -> fresh -+              |
                                        +--> compiled singleton >= 200,000 ops/sec
```

The direct singleton and ordered-group branches shown above match the current selector; the controller and adapter nodes match the existing example ownership types, while the single telemetry event is the required Phase 25 rewrite. [VERIFIED: `src/fast_fsm/core.py:2354-2416`; `examples/drone_failsafes.py:16-87`; `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:28-34`]

### Recommended Project Structure

```text
src/fast_fsm/core.py                         # linear local group insertion; truthful docstrings
tests/test_priority_transitions.py           # registration/selection semantic regression tests
tests/test_performance_benchmarks.py          # operation-count and representative group evidence
benchmarks/performance_demo.py                # human-readable, environment-labeled matrix
tools/artifact_conformance.py                 # shared priority scenarios and required values
tools/release_evidence.py                     # existing isolated installed-artifact verifier
tests/test_artifact_conformance.py            # oracle schema/negative validation
tests/test_installed_artifacts.py              # source vs pure vs compiled comparison + floor
examples/drone_failsafes.py                    # controller-owned single-event example
tests/test_drone_failsafes_example.py          # executable example contract
README.md                                      # public complexity/example guidance
docs/dev/architecture.md                       # topology and asymptotic contract
docs/examples/index.md                         # drone walkthrough
.github/copilot-instructions.md                # maintainer performance policy
.planning/PROJECT.md                           # project-level truthful constraint
.specify/spr-core-api.md                       # stable programming reference if wording changes
Taskfile.yml                                   # runnable benchmark/artifact/docs gates
evidence/release-baseline.json                 # intentionally regenerated durable evidence
```

These are existing seams except for any optional dedicated benchmark module; no new package namespace is needed. [VERIFIED: `.github/copilot-instructions.md:10-25`; `Taskfile.yml:202-221`; `Taskfile.yml:294-315`]

### Pattern 1: Linear, Immutable Candidate Insertion

**What:** Treat the existing tuple as sorted input. Scan once to find an equal priority or first greater priority. Preserve the current no-op definition for an exact duplicate, preserve the existing conflict error for a different candidate at the same priority, and return one new immutable tuple only when the slot changes. [VERIFIED: `src/fast_fsm/core.py:1713-1739`]

**When to use:** Every grouped `add_transition()`/bulk construction merge. Singleton creation remains a direct object return. [VERIFIED: `src/fast_fsm/core.py:1687-1710`; `src/fast_fsm/core.py:1741-1779`]

**Recommended implementation shape:**

```python
# Recommended replacement inside _merge_transition_slot.
insert_at = len(entries)
for index, entry in enumerate(entries):
    if entry.priority == candidate.priority:
        if (
            entry.to_state is candidate.to_state
            and entry.condition is candidate.condition
            and entry.condition_ref == candidate.condition_ref
        ):
            return existing
        raise ValueError("transition priority is already registered for this slot")
    if entry.priority > candidate.priority:
        insert_at = index
        break

return _TransitionGroup(entries[:insert_at] + (candidate,) + entries[insert_at:])
```

The field names and exact conflict text in this sketch are quoted from the current implementation; the linear insertion algorithm is the prescriptive Phase 25 change. [VERIFIED: `src/fast_fsm/core.py:1713-1739`]

### Pattern 2: Structural Complexity Proof Plus Representative Timing

**What:** Separate asymptotic proof from observed timings. Use operation-count/structural tests to prove that dispatch touches only the current source map and one local candidate group, that guards stop at the winner, and that registration contains no `sorted()` call. Use a human-readable benchmark for environment-labeled observations, not for proving Big-O. [VERIFIED: `tests/test_performance_benchmarks.py:40-105`; `tests/test_performance_benchmarks.py:158-235`]

**Recommended benchmark matrix:** group depths `2`, `8`, and `32`; winner positions first, middle, and last; plus all-guards-false exhaustion. Repeat against unrelated topology sizes `4`, `64`, and `512` to show local work is invariant with total graph size. The topology sizes reuse the repository's existing operation-count fixture, while group depths are a Phase 25 discretion choice. [VERIFIED: `tests/test_performance_benchmarks.py:40-42`] [ASSUMED]

For every matrix cell record guard evaluations, operations/second, Python version, implementation, loader/mode, platform, and sample count. Assert exact guard counts (`1`, middle rank, `k`, or `k` for exhaustion); do not assert fragile timing ratios. Python's official `timeit` guidance recommends multiple repetitions and notes that the best result is normally the useful lower bound for small snippets. [CITED: https://docs.python.org/3/library/timeit.html] The release gate is a distinct project contract and must retain its existing three-sample median calculation. [VERIFIED: `tools/release_evidence.py:3006-3082`]

### Pattern 3: Shared Required-Value Conformance

**What:** Add priority scenarios to the existing collector registry and scenario definitions, then hard-code expected semantic fields in `required_values`. Comparing digests alone is insufficient because all three origins could share the same defect. [VERIFIED: `tools/artifact_conformance.py:42-90`; `tools/artifact_conformance.py:1267-1378`]

**Scenario coverage:**

| Scenario | Required record facts |
|----------|-----------------------|
| Sync winner | Selected target and priority; exact guard order; result priority; history priority. |
| Sync exhaustion | All guard priorities visited in order; failure stage equals the quoted runtime value `"selection"`; terminal state unchanged. [VERIFIED: `src/fast_fsm/core.py:2398-2403`] |
| Sync exception | Earlier rejection followed by one raising guard; candidate priority and lifecycle stage preserved; no lower guard evaluated; terminal state unchanged. |
| Async winner | Same winner/order/metadata contract through the async selector's sequential local loop. [VERIFIED: `src/fast_fsm/core.py:4221-4278`] |
| Async cancellation | Cancellation at a candidate is terminal, records the active priority/stage, evaluates no lower candidate, leaves the machine reusable, and is not converted into normal fallthrough. [VERIFIED: `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:35-59`] |

Keep `SCHEMA_VERSION = 1` if the top-level conformance shape remains unchanged; adding scenarios naturally changes the suite digest and therefore binds installed probes to the expanded inventory. [VERIFIED: `tools/artifact_conformance.py:22-30`; `tools/artifact_conformance.py:1290-1378`]

### Pattern 4: Clean Source as an Explicit Third Origin

**What:** Run `pure-source-check`, collect the source oracle from that clean origin, build explicit `FAST_FSM_BUILD_MODE` wheels for values quoted verbatim as `"pure"` and `"compiled"`, verify each in a fresh environment, then compare each installed conformance record to the captured source record. [VERIFIED: `setup.py:23-26`; `.github/copilot-instructions.md:61-69`; `tools/release_evidence.py:3311-3443`]

**When to use:** The Phase 25 artifact gate and installed-artifact integration test. The test already builds both exact wheel modes and calls `compare_conformance(collect_conformance(), record["conformance"])`; expanding the oracle automatically extends most of the proof. [VERIFIED: `tests/test_installed_artifacts.py:162-218`]

uv officially supports `uv build --wheel` and installation into an explicitly selected interpreter with `uv pip install --python`. [CITED: https://docs.astral.sh/uv/concepts/projects/build/] [CITED: https://docs.astral.sh/uv/pip/environments/] Continue using the repository verifier rather than scripting a less strict duplicate.

### Pattern 5: One Telemetry Tick, FSM-Owned Precedence

**What:** On every update, the controller stores the sample in `TelemetryPolicy` and calls the FSM exactly once:

```python
def update_from_telemetry(self, sample: TelemetrySample) -> TransitionResult:
    self._telemetry_policy.observe(sample)
    return self._fsm.trigger(
        "telemetry_tick", telemetry_policy=self._telemetry_policy
    )
```

Register state-local candidates on that one event. Use lower integers for more urgent guards, preserving the existing exact-integer public contract. [VERIFIED: `src/fast_fsm/core.py:684-688`; `.specify/decisions/ADR-007-priority-topology.md:20-39`]

Recommended finite transition table:

| Source | Priority | Guard fact/request | Target | Bound entry behavior |
|--------|----------|--------------------|--------|----------------------|
| `PreArm` | `100` | operator requests arm and pre-arm checks pass | `Armed` | `command_arm()` |
| `Armed` | `100` | operator requests takeoff | `Takeoff` | `command_takeoff()` |
| `Takeoff` | `0` | critical fault | `EmergencyLanding` | `command_emergency_landing()` |
| `Takeoff` | `10` | heartbeat/link lost | `ReturnHome` | `command_return_to_home()` |
| `Takeoff` | `20` | low battery | `ReturnHome` | `command_return_to_home()` |
| `Takeoff` | `100` | operator requests mission/start condition met | `Mission` | mission command if supported |
| `Mission` | `0` | critical fault | `EmergencyLanding` | `command_emergency_landing()` |
| `Mission` | `10` | heartbeat/link lost | `ReturnHome` | `command_return_to_home()` |
| `Mission` | `20` | low battery | `ReturnHome` | `command_return_to_home()` |
| `ReturnHome` | `0` | critical fault | `EmergencyLanding` | `command_emergency_landing()` |
| `ReturnHome` | `100` | home reached | `Landing` | `command_land()` |
| `Landing` | `100` | on ground | `Landed` | no flight command |
| `EmergencyLanding` | `100` | on ground | `Landed` | no flight command |

The state names, command names, and telemetry fields above already exist in the example; using a single trigger and the shown numeric precedence is the recommended rewrite under D-04. [VERIFIED: `examples/drone_failsafes.py:16-183`; `examples/drone_failsafes.py:197-267`] The example should return the `TransitionResult` so tests and users can observe success/failure and chosen priority without inspecting private FSM storage. [VERIFIED: `src/fast_fsm/core.py:3554-3568`]

### Anti-Patterns to Avoid

- **Dispatch-time sorting:** Candidate groups are published in priority order; sorting during `trigger()` adds avoidable work and makes dispatch complexity harder to reason about. [VERIFIED: `src/fast_fsm/core.py:655-659`; `src/fast_fsm/core.py:2354-2403`]
- **Calling registration O(k) before removing `sorted()`:** The current insertion implementation performs a full duplicate scan and then comparison-sorts the copied tuple. [VERIFIED: `src/fast_fsm/core.py:1713-1739`]
- **Timing-only Big-O claims:** Wall-clock results are noisy and environment-specific; structural operation counts and guard-order assertions are the durable complexity proof. [VERIFIED: `.github/copilot-instructions.md:5-8`; `tests/test_performance_benchmarks.py:40-105`]
- **Hard-coded `~250,000` marketing text:** Current core docstrings and demo output include this observation, while project policy now uses an environment-labeled compiled floor of `200,000`. [VERIFIED: `src/fast_fsm/core.py:3554-3560`; `benchmarks/performance_demo.py:270-278`; `.github/copilot-instructions.md:47-50`]
- **One wheel proving both modes:** Build intent and observed archive/runtime mode must be explicit for each wheel. [VERIFIED: `tools/release_evidence.py:3311-3341`]
- **Parity without required values:** Equal wrong results still compare equal; scenario definitions must reject incorrect winners, orders, metadata, and terminal states. [VERIFIED: `tools/artifact_conformance.py:1290-1378`]
- **Telemetry policy as a router:** A helper may calculate heartbeat age or expose a sample, but it must not return events, states, transitions, or commands. [VERIFIED: `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:31-34`]
- **One external trigger per condition:** The current `TELEMETRY_EVENT_PRIORITY` loop encodes precedence outside the state machine and must be deleted, not renamed. [VERIFIED: `examples/drone_failsafes.py:186-194`; `examples/drone_failsafes.py:291-311`]
- **Aircraft adapter as FSM subclass:** Keep `SimulatedAircraft` behind the protocol and owned by the controller; callbacks may be bound to it, but it is not state-machine infrastructure. [VERIFIED: `examples/drone_failsafes.py:16-87`; `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:28-30`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Installed wheel isolation | Ad-hoc `sys.path` manipulation or in-process wheel import | `release_evidence.verify_installed_wheel()` | It snapshots identity, creates a neutral environment, installs by exact path, validates runtime origin/mode/architecture, and collects semantics/performance. [VERIFIED: `tools/release_evidence.py:3311-3443`] |
| Source/pure/compiled behavioral suite | Three copied test implementations | `artifact_conformance.collect_conformance()` plus `compare_conformance()` | One suite definition and suite digest prevent coverage drift. [VERIFIED: `tools/artifact_conformance.py:1416-1470`] |
| Priority routing in application code | Ordered `if` chain or trigger-name loop | Multiple guarded `telemetry_tick` candidates | The FSM already stores and resolves ordered candidates. [VERIFIED: `src/fast_fsm/core.py:2354-2416`] |
| Benchmark timing harness | Custom low-resolution timestamps around one call | Existing installed performance collector for the release floor; `timeit`/repeat for the descriptive group matrix | The installed collector already handles warm-up, multiple samples, median, origin, and payload shape. [VERIFIED: `tools/release_evidence.py:3006-3082`] [CITED: https://docs.python.org/3/library/timeit.html] |
| Documentation source snippets | Duplicated example code in several pages | Sphinx `literalinclude` for displayed source plus dedicated pytest execution | `literalinclude` keeps displayed code tied to the runnable file; behavior remains enforced by tests. [CITED: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html] |

**Key insight:** The repository already has the hard isolation and semantic machinery. Phase 25 should deepen those existing seams and remove the two remaining duplicate-policy points: re-sorting during registration and prioritizing telemetry events outside the FSM.

## Common Pitfalls

### Pitfall 1: Complexity Documentation Gets Ahead of the Algorithm

**What goes wrong:** README, docstrings, and project policy claim O(k) local mutation while `sorted()` remains in `_merge_transition_slot()`. [VERIFIED: `src/fast_fsm/core.py:1713-1739`]

**Why it happens:** The stored result is ordered and dispatch is linear, so the insertion-time sort is easy to overlook.

**How to avoid:** Land the linear insertion and its structural regression test before or atomically with public complexity wording. Verify ascending order, exact duplicate no-op identity, equal-priority conflict atomicity, and multi-source bulk atomicity. [VERIFIED: `.specify/decisions/ADR-007-priority-topology.md:20-50`]

**Warning signs:** `sorted(` occurs in the group merge path; a benchmark reports only dispatch; or docs say every `add_transition()` is O(1).

### Pitfall 2: “Representative” Benchmarks Become Brittle Gates

**What goes wrong:** CI fails due to machine noise, or a timing ratio is misrepresented as proof of O(k).

**Why it happens:** Small benchmark samples mix interpreter warm-up, CPU scaling, and callback cost with the algorithm under test.

**How to avoid:** Make guard counts/topology access the asserted contract. Report group timings with full environment metadata and repeated samples. Keep only the established freshly installed compiled singleton `>=200_000` floor as a hard throughput gate. [VERIFIED: `tests/test_performance_benchmarks.py:758-827`; `tools/release_evidence.py:3006-3082`]

**Warning signs:** Assertions compare first/middle/last nanoseconds, benchmark records omit loader/mode, or group timings run from the checkout while being described as installed compiled evidence.

### Pitfall 3: Source Origin Is Not Actually Clean

**What goes wrong:** The “source” baseline imports an in-tree compiled extension or the installed-artifact child imports from the checkout.

**Why it happens:** Python import precedence and current working directory can silently shadow intended origins.

**How to avoid:** Run the non-destructive pure-source preflight first; capture source conformance only afterward; let `verify_installed_wheel()` run from its neutral directory and validate `package_origin`, `core_origin`, and loader. [VERIFIED: `.github/copilot-instructions.md:61-69`; `tools/release_evidence.py:3330-3412`]

**Warning signs:** `ExtensionFileLoader` in the source record, checkout paths in wheel runtime records, or wheel tests that mutate `PYTHONPATH`.

### Pitfall 4: Equal-but-Wrong Artifact Results

**What goes wrong:** Source, pure, and compiled records match, but all select the wrong priority or lose failure metadata.

**Why it happens:** Pairwise comparison proves parity, not correctness.

**How to avoid:** Put exact winners, guard order, stages, priorities, and terminal-state expectations into each conformance scenario's `required_values`; keep mutation tests that ensure validators reject altered records. [VERIFIED: `tools/artifact_conformance.py:1290-1378`]

**Warning signs:** New scenario collectors exist without matching required values, or tests only compare semantic digests.

### Pitfall 5: Baseline Regeneration Uses the Wrong Toolchain

**What goes wrong:** A semantic suite change legitimately changes the release manifest, but regeneration also introduces unrelated toolchain drift.

**Why it happens:** The workstation default uv is `0.12.9`, while the durable baseline records `"uv": "0.12.6"`. [VERIFIED: `evidence/release-baseline.json:977`] [VERIFIED: environment probe on 2026-09-07]

**How to avoid:** Run baseline write/check through the reviewed uv `0.12.6` binary available in `/private/tmp/fast-fsm-uv-0.12.6/uv-aarch64-apple-darwin/uv`, inspect the manifest diff, and accept only expected suite/evidence changes. [VERIFIED: environment probe on 2026-09-07]

**Warning signs:** Manifest diff changes tool versions in addition to conformance hashes/counts.

### Pitfall 6: State Entry Commands Fire for Rejected Candidates

**What goes wrong:** An aircraft command is issued during guard evaluation or before the selected transition commits.

**Why it happens:** Fact gathering, selection, and behavior are coupled in one condition function.

**How to avoid:** Guards remain side-effect-free fact checks. Issue commands only from bound `DroneState` entry actions; the existing class invokes its bound action from `on_enter()`. [VERIFIED: `examples/drone_failsafes.py:69-87`]

**Warning signs:** A guard calls `command_return_to_home()`, a rejected lower-priority candidate changes the command log, or a failed transition still issues a command.

### Pitfall 7: Example Documentation Looks Right but Does Not Execute

**What goes wrong:** Sphinx includes a source file successfully even though its simulation behavior is broken.

**Why it happens:** `literalinclude` renders source; it is not an execution test. [CITED: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html]

**How to avoid:** Keep dedicated pytest tests for controller behavior and run the example script as a smoke test. Use Sphinx doctest only for small executable snippets where exact output is stable. [CITED: https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html]

**Warning signs:** Documentation is the only coverage for one-tick dispatch or aircraft command calls.

## Code Examples

### Artifact Parity Gate

```python
# Recommended Taskfile/helper shape, using the repository's existing APIs.
source = artifact_conformance.collect_conformance()

pure = release_evidence.verify_installed_wheel(
    pure_wheel,
    expected_mode="pure",
    build_intent="pure",
)
compiled = release_evidence.verify_installed_wheel(
    compiled_wheel,
    expected_mode="compiled",
    build_intent="compiled",
)

assert artifact_conformance.compare_conformance(source, pure["conformance"]) == []
assert artifact_conformance.compare_conformance(source, compiled["conformance"]) == []
assert compiled["performance"]["median_ops_per_second"] >= 200_000
```

The exact wheel modes, record keys, comparison function, and performance field already exist in the installed-artifact test and verifier. [VERIFIED: `tests/test_installed_artifacts.py:188-218`; `tools/release_evidence.py:3429-3443`]

### Priority Group Work Assertion

```python
# For a group with winner at zero-based index n:
assert guard_order == priorities[: n + 1]
assert result.priority == priorities[n]

# Exhaustion visits every local candidate and does not inspect unrelated states.
assert guard_order == priorities
assert unrelated_source_map_operations == 0
```

This assertion pattern follows the current first-eligible ordered scan and existing counting-map tests. [VERIFIED: `src/fast_fsm/core.py:2384-2403`; `tests/test_performance_benchmarks.py:40-105`; `tests/test_performance_benchmarks.py:158-235`]

### Controller-Owned Telemetry Update

```python
class DroneController:
    def __init__(
        self,
        telemetry_policy: TelemetryPolicy,
        aircraft: AircraftCommands,
    ) -> None:
        self._telemetry_policy = telemetry_policy
        self._aircraft = aircraft
        self._fsm = create_drone_fsm(aircraft)

    def update_from_telemetry(
        self, sample: TelemetrySample
    ) -> TransitionResult:
        self._telemetry_policy.observe(sample)
        return self._fsm.trigger(
            "telemetry_tick", telemetry_policy=self._telemetry_policy
        )
```

The component names and ownership fields are existing example values; the one-trigger body is the required Phase 25 replacement for the current external loop. [VERIFIED: `examples/drone_failsafes.py:16-138`; `examples/drone_failsafes.py:270-318`]

## State of the Art

| Existing approach | Phase 25 approach | Impact |
|-------------------|-------------------|--------|
| Group insertion scans for duplicates, then calls `sorted()` on every changed slot. [VERIFIED: `src/fast_fsm/core.py:1713-1739`] | One scan finds equality/conflict/insertion point, followed by one immutable tuple splice. | Makes the locked local O(k) registration claim truthful without changing ordered semantics. |
| Dispatch already uses direct singleton vs ordered-group branches. [VERIFIED: `src/fast_fsm/core.py:2354-2416`] | Preserve runtime logic; add representative depth/winner evidence and correct blanket docstrings. | Improves proof without risking hot-path redesign. |
| Installed conformance covers broad lifecycle behavior but has no dedicated priority scenario family. [VERIFIED: `tools/artifact_conformance.py:42-259`; `tools/artifact_conformance.py:1267-1287`] | Add required-value priority scenarios used identically by source, pure, and compiled origins. | Proves winner, evaluation order, metadata, exhaustion, exception, and cancellation parity. |
| Direct artifact task builds/verifies each wheel independently. [VERIFIED: `Taskfile.yml:294-315`] | Capture clean source once and compare each verified wheel record against it in the same gate. | Makes the required three-origin proof explicit and actionable. |
| Drone controller loops across `TELEMETRY_EVENT_PRIORITY` trigger names. [VERIFIED: `examples/drone_failsafes.py:186-194`; `examples/drone_failsafes.py:291-311`] | One `telemetry_tick`; state-local guards encode precedence; callbacks issue adapter commands. | Demonstrates the library's core value and eliminates duplicate external routing policy. |

**Deprecated/outdated guidance:**

- `StateMachine.trigger()` and `can_trigger()` docstrings currently describe the operation unconditionally as O(1); they must say lookup and singleton dispatch are O(1), while a candidate group is O(k) in the local group. [VERIFIED: `src/fast_fsm/core.py:2270-2275`; `src/fast_fsm/core.py:3554-3560`]
- README's performance table labels `trigger`, `can_trigger`, and `add_transition` simply O(1); it must split singleton and grouped paths. [VERIFIED: `README.md:712-734`]
- Developer architecture describes a singular transition mapping with O(1) operations; it must document the `TransitionEntry | _TransitionGroup` slot topology. [VERIFIED: `docs/dev/architecture.md:61-72`; `src/fast_fsm/core.py:611-681`]
- Maintainer policy says all four core operations, including `add_transition()`, are O(1); revise it to the D-01 split. [VERIFIED: `.github/copilot-instructions.md:47-50`]
- `benchmarks/performance_demo.py` prints blanket O(1), fixed `~250K`, and `1000x` claims; replace these with environment-labeled observations and the representative group matrix. [VERIFIED: `benchmarks/performance_demo.py:270-278`]
- The current `task benchmark` executes `benchmarks/benchmark_fast_fsm.py`, which defines fixtures but has no command-line reporting entry point; make the task run the actual descriptive benchmark or add an explicit priority benchmark target. [VERIFIED: `Taskfile.yml:206-216`; `benchmarks/benchmark_fast_fsm.py:1-296`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Group depths `2`, `8`, `32` and graph sizes `4`, `64`, `512` provide a representative small/medium/deep matrix for this library. | Architecture Pattern 2 | Low. These are reporting samples, not semantic or release thresholds; planner may adjust depths while retaining first/middle/last/exhaustion coverage. |

## Open Questions

None blocking. The exact benchmark depths and final documentation organization are explicitly delegated to the agent; the recommendation above resolves both for planning. [VERIFIED: `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:36-38`]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| CPython via uv environment | Tests, benchmarks, builds | Yes | `3.12.10` | Project supports `>=3.10`. [VERIFIED: `pyproject.toml:9-15`] |
| uv default | Routine commands | Yes | `0.12.9` | Use reviewed pinned uv for baseline work. [VERIFIED: environment probe on 2026-09-07] |
| reviewed uv | Durable release baseline | Yes | `0.12.6` at `/private/tmp/fast-fsm-uv-0.12.6/uv-aarch64-apple-darwin/uv` | None needed. [VERIFIED: `evidence/release-baseline.json:977`; environment probe on 2026-09-07] |
| pytest | Unit/integration suite | Yes | `8.4.1` | None needed. [VERIFIED: environment probe on 2026-09-07] |
| Ruff | Formatting/lint | Yes | `0.12.11` | None needed. [VERIFIED: environment probe on 2026-09-07] |
| mypy/mypyc | Type/compiled checks | Yes | `1.17.1` | None needed. [VERIFIED: environment probe on 2026-09-07] |
| Sphinx | Documentation build | Yes | `9.1.0` | None needed. [VERIFIED: environment probe on 2026-09-07] |
| Task | Compound workflow targets | Yes | `3.53.1` | Invoke underlying uv commands if necessary. [VERIFIED: environment probe on 2026-09-07] |
| Native compiler toolchain | Compiled wheel/mypyc | Yes, demonstrated by existing compiled artifact tests and environment | Repository-controlled | Treat a build failure as blocking rather than silently substituting pure mode. [VERIFIED: `tests/test_installed_artifacts.py:181-218`] |

**Missing dependencies with no fallback:** None observed.

**Missing dependencies with fallback:** None observed. The sandboxed uv default cache was unreadable during the probe; setting `UV_CACHE_DIR` to the existing phase-local cache provided the verified tool environment. [VERIFIED: environment probe on 2026-09-07]

## Validation Architecture

Nyquist validation is enabled: the configuration value is quoted verbatim as `"nyquist_validation": true`. [VERIFIED: `.planning/config.json:15-21`]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1` [VERIFIED: environment probe on 2026-09-07] |
| Config file | `pyproject.toml`; marker values are quoted verbatim as `"performance: performance and benchmark tests"`, `"integration: integration tests spanning process or artifact boundaries"`, and `"asyncio: async tests"`. [VERIFIED: `pyproject.toml:60-71`] |
| Quick run command | `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache uv run pytest tests/test_priority_transitions.py tests/test_performance_benchmarks.py tests/test_artifact_conformance.py tests/test_drone_failsafes_example.py -x -q` |
| Installed artifact command | `task release-installed-artifacts-check` [VERIFIED: `Taskfile.yml:294-315`] |
| Documentation commands | `task docs-check` and `task docs-test` [VERIFIED: `Taskfile.yml:226-252`] |
| Full suite command | `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache uv run pytest tests/ -x -q` [VERIFIED: `.github/copilot-instructions.md:55-59`] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| PERF-01 | Linear group insertion; ordered candidate scan touches exactly winner-rank guards and no unrelated source map; representative depths/positions run. | Unit + structural + benchmark characterization | `uv run pytest tests/test_performance_benchmarks.py tests/test_priority_transitions.py -x -q` | Existing files; new cases required. [VERIFIED: `tests/test_performance_benchmarks.py:120-235`] |
| PERF-02 | Clean source, installed pure wheel, and installed compiled wheel produce identical required priority records; compiled singleton median remains `>=200_000` from at least three samples. | Integration/artifact | `uv run pytest tests/test_artifact_conformance.py tests/test_installed_artifacts.py -x -q -m integration` | Existing files; priority scenarios/expectations required. [VERIFIED: `tests/test_installed_artifacts.py:188-218`] |
| PERF-02 | Exact direct artifact workflow performs source/pure/compiled proof and native performance gate. | Task smoke/integration | `task pure-source-check && task release-installed-artifacts-check && task release-installed-performance-check` | Existing tasks; artifact task needs explicit source comparison/dependency. [VERIFIED: `Taskfile.yml:294-315`; `Taskfile.yml:455-474`] |
| DOC-01 | One call per telemetry sample; simultaneous critical/link/low selects critical; link+low selects link; healthy tick does not transition; callback commands adapter once after commit; heartbeat helper remains fact-only. | Unit/example | `uv run pytest tests/test_drone_failsafes_example.py -x -q` | Existing file; substantial cases required. [VERIFIED: `tests/test_drone_failsafes_example.py:1-33`] |
| DOC-01 | README, architecture, example page, core docstrings, and policy render with no stale blanket complexity/ordered-trigger guidance. | Docs/lint | `task docs-check && task docs-test` | Existing infrastructure. [VERIFIED: `Taskfile.yml:226-252`] |

### Required Behavioral Tests

1. Registration at beginning/middle/end produces ascending priorities and never calls `sorted`; exact duplicate registration returns the identical published slot; same-priority conflict leaves topology/version unchanged. [VERIFIED: `src/fast_fsm/core.py:1687-1739`; `.specify/decisions/ADR-007-priority-topology.md:20-50`]
2. For depths `2`, `8`, `32`, first/middle/last winners evaluate exactly through the winner; exhaustion evaluates exactly `k`; unrelated topology size does not change current-source lookup count. [ASSUMED]
3. Conformance records assert exact sync/async winner, guard order, result/history priority, selection exhaustion, exception priority/stage/terminal state, and cancellation terminal/reusable state. [VERIFIED: `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md:15-59`]
4. Both installed modes compare to a previously captured clean-source record; compiled record reports `"core_loader": "ExtensionFileLoader"`, median at least `200_000`, and at least three samples. [VERIFIED: `tests/test_installed_artifacts.py:201-218`]
5. One drone sample causes exactly one `trigger("telemetry_tick", ...)` invocation; simultaneous facts select only the highest-priority eligible candidate; command log contains only the selected state's bound command. [VERIFIED: `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:28-34`]

### Sampling Rate

- **Per task commit:** Run the smallest targeted files listed above plus Ruff on changed Python files.
- **Per wave merge:** Run `task typecheck-mypy`, keep `task typecheck-ty` visible as advisory, and run the relevant artifact/docs task for that wave. [VERIFIED: `.github/copilot-instructions.md:109-123`]
- **Phase gate:** Run formatting/lint, mypy/mypyc, full sequential sync/async tests, `docs-check`, `docs-test`, pure-source preflight, source/pure/compiled conformance, installed compiled performance, and release baseline check. This is the roadmap's fifth success criterion. [VERIFIED: `.planning/ROADMAP.md:157-162`]

### Wave 0 Gaps

- Add priority scenario definitions/collectors/required values in `tools/artifact_conformance.py`; update `tests/test_artifact_conformance.py` inventory and negative-mutation assertions. [VERIFIED: `tools/artifact_conformance.py:42-90`; `tools/artifact_conformance.py:1267-1378`]
- Expand `tests/test_drone_failsafes_example.py` beyond its current heartbeat-only test to cover one-tick resolution and adapter commands. [VERIFIED: `tests/test_drone_failsafes_example.py:1-33`]
- Add group-insertion structural/operation-count cases to `tests/test_performance_benchmarks.py`; the existing group test covers only one four-candidate winner position. [VERIFIED: `tests/test_performance_benchmarks.py:158-235`]
- Repair the runnable benchmark entry point/Task target so the representative matrix actually prints environment-labeled results. [VERIFIED: `Taskfile.yml:206-216`; `benchmarks/benchmark_fast_fsm.py:1-296`; `benchmarks/performance_demo.py:1-280`]

## Security Domain

Security enforcement is enabled by default because `.planning/config.json` contains no `security_enforcement: false` override. [VERIFIED: `.planning/config.json:1-26`]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Library, benchmark, and local artifact verification expose no authentication surface. [VERIFIED: `pyproject.toml:1-45`; `tools/release_evidence.py:3311-3443`] |
| V3 Session Management | No | No user/session state is introduced. [VERIFIED: phase boundary in `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:9-12`] |
| V4 Access Control | No | No authorization boundary is introduced. [VERIFIED: phase boundary in `.planning/phases/25-performance-artifact-proof-drone-guidance/25-CONTEXT.md:9-12`] |
| V5 Input Validation | Yes | Preserve exact-int priority validation; strictly validate untrusted child JSON shape, digests, bounds, scenario types, and forbidden payload fields/tokens before accepting evidence. [VERIFIED: `src/fast_fsm/core.py:684-688`; `tools/release_evidence.py:3216-3270`] |
| V6 Cryptography | No new cryptography | Reuse SHA-256 artifact/suite/semantic identity checks; do not invent cryptographic protocols. [VERIFIED: `tools/release_evidence.py:3229-3269`; `tools/release_evidence.py:3334-3364`] |

### Known Threat Patterns for This Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Installed child emits malformed or payload-bearing evidence | Tampering / Information Disclosure | Parent-side exact schema, bounds, forbidden-field/token, suite-digest, and semantic-digest validation. [VERIFIED: `tools/release_evidence.py:3216-3270`] |
| Checkout or native shadow contaminates source/wheel origin | Tampering | Pure-source preflight, neutral installed environment, explicit runtime origin/loader/mode validation, non-destructive reporting. [VERIFIED: `.github/copilot-instructions.md:61-69`; `tools/release_evidence.py:3330-3412`] |
| Artifact changes between validation and install | Tampering | Private snapshot plus SHA-256 recheck immediately before installation. [VERIFIED: `tools/release_evidence.py:3330-3364`] |
| Drone example is mistaken for production flight-safety software | Safety misuse | Preserve and strengthen the simulation/educational disclaimer; never claim certification, real-time guarantees, or hardware suitability. [VERIFIED: `examples/drone_failsafes.py:1-14`] |
| Telemetry/log payload enters conformance evidence | Information Disclosure | Record only deterministic booleans/enums/counts/stages/priorities; retain payload leak validation. [VERIFIED: `tools/artifact_conformance.py:1290-1378`; `tools/release_evidence.py:3229-3255`] |

## Sources

### Primary (HIGH confidence)

- Repository source and tests: `src/fast_fsm/core.py`, `examples/drone_failsafes.py`, `tools/artifact_conformance.py`, `tools/release_evidence.py`, `tests/test_performance_benchmarks.py`, `tests/test_installed_artifacts.py`, and `tests/test_drone_failsafes_example.py`. [VERIFIED: direct file reads on 2026-09-07]
- Canonical project decisions: `.specify/decisions/ADR-007-priority-topology.md`, Phase 22–24 verification reports, Phase 25 context, roadmap, requirements, project policy, and stable programming reference. [VERIFIED: direct file reads on 2026-09-07]
- Build/test/docs workflow: `pyproject.toml`, `setup.py`, `Taskfile.yml`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.planning/config.json`. [VERIFIED: direct file reads on 2026-09-07]

### Secondary (MEDIUM confidence)

- Python `timeit` official documentation — repeat/minimum guidance and timing caveats. [CITED: https://docs.python.org/3/library/timeit.html]
- uv official build documentation — explicit wheel construction. [CITED: https://docs.astral.sh/uv/concepts/projects/build/]
- uv official environment documentation — environment creation and interpreter-targeted installation. [CITED: https://docs.astral.sh/uv/pip/environments/]
- Sphinx official directive documentation — `literalinclude`. [CITED: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html]
- Sphinx official doctest documentation — executable documentation blocks. [CITED: https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html]

### Tertiary (LOW confidence)

- The exact recommended representative group depths are a researcher-selected matrix, not a published industry standard. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — existing repository tools and installed versions were directly inspected; no new packages are proposed.
- Architecture: HIGH — core registration/selection, artifact isolation, and example ownership seams were read directly and are constrained by locked decisions.
- Pitfalls: HIGH — each material pitfall is visible in current source/docs/tests or in the authoritative tool contracts; only the exact benchmark depth selection is discretionary.

**Research date:** 2026-09-07
**Valid until:** 2026-10-07 (stable internal architecture; re-check toolchain pins if the release baseline changes)
