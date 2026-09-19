# Phase 32: Performance, Artifact & Progressive Guidance Proof - Research

**Researched:** 2026-09-19  
**Domain:** Python FSM performance evidence, installed-artifact conformance, and progressive documentation  
**Confidence:** HIGH for inspected in-repo contracts; MEDIUM for external tooling documentation

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Performance and Evidence

- **D-01:** Keep the established fresh installed compiled singleton floor at **200,000 transitions/second**. Do not lower it or substitute source-tree throughput. The unfeatured singleton path remains O(1) and must avoid unrelated candidate scans, graph traversal, reflection, and per-dispatch diagnostic allocation. — **Reversibility:** costly — this is the library's core performance contract and a release gate.
- **D-02:** Measure final-state, internal self, external self, and expected-rejection costs as separately identified scenarios, with exact runtime/build origin, Python/tool versions, platform, sample method, and environment label. Report observations, not universal speedup claims; compare local candidate work against unrelated topology growth.
- **D-03:** Reuse the existing release/artifact evidence harness and `uv.lock`/`uv sync --locked` workflow. Do not add a required uv patch version, offline mode, custom cache, or an automatic baseline rewrite. A manifest write is an explicit reviewed evidence step; read-only checks remain the CI behavior. — **Reversibility:** costly — evidence reproducibility and contributor setup depend on this contract.
- **D-04:** Run the same fixed semantic oracle for pure source, freshly built native core, installed pure and compiled wheels, and release artifacts. Assert exact origin/build intent before accepting each result; generated core shadows are moved only through a path-constrained, recoverable protocol.
- **D-05:** Exact isolated `python-statemachine` 2.5.0 and 3.2.1 comparisons remain labelled manual or scheduled observations with semantic preflight and unsupported-cell disclosure, not ordinary CI pass/fail gates. The native Fast FSM floor is the durable release threshold.

### Progressive Drone Tutorial

- **D-06:** Keep `DroneController` as owner of the FSM and replaceable aircraft command adapter. `TelemetryPolicy` may expose measured facts such as heartbeat age, but all state-dependent transition eligibility and precedence belong in FSM guards on one `telemetry_tick`; the controller does not route failsafes through `if`/`dispatch` branches.
- **D-07:** Teach one concept at a time in the existing deterministic training simulation: prioritized telemetry guards, internal self-updates, external self-reentry, explicit landing finals, expected `TransitionRejected(code)`, and commands issued only by committed entry behavior. Simulated telemetry is deterministic, with no hidden scheduler, actual hardware integration, or real-time flight-safety claim.
- **D-08:** Keep the example builder-first and smoke-testable. Show a distinct false guard (ineligible candidate) versus expected rejection (terminal domain outcome); explain why final landing is not merely a dead-end node.

### README and Sphinx Learning Path

- **D-09:** Start with one small `FSMBuilder` recipe and only then layer guards, priority, mode, finality, rejection, diagnostics, async/direct advanced use, and artifact/performance details. Direct `StateMachine`/`AsyncStateMachine` construction remains supported advanced use; `from_dict()` stays the serialized-topology adapter, not a rival general-purpose builder. — **Reversibility:** costly — this hierarchy is the public onboarding contract from Phase 30.
- **D-10:** Give actionable migration examples for `simple_fsm`, `quick_fsm`, `quick_build`, and `from_states` to `FSMBuilder`, noting their one-warning-per-call compatibility period through v0.5.x and removal no earlier than v0.6.0. Do not suggest that direct constructors, `from_dict()`, or declarative states are deprecated.
- **D-11:** Explain the three important distinctions consistently in README and Sphinx: explicit finality versus no-outgoing topology, expected rejection versus ordinary false/ineligibility versus unexpected failure, and internal self-transition versus external self-transition. Prefer runnable examples and exact output fields over abstract prose alone.

### the agent's Discretion

- Exact benchmark script/module layout, labelled record schema additions, sample counts beyond the unchanged durable floor gate, and documentation page split may follow existing project patterns.
- The tutorial may reuse or simplify `examples/drone_failsafes.py` and its Sphinx literal inclusion, provided the one-example progressive story stays deterministic and all existing command effects remain post-commit.
- Release artifact proof does not itself create a Git tag, GitHub Release, or PyPI publication; milestone audit and the separately authorized release workflow govern external publication.

### Deferred Ideas (OUT OF SCOPE)

- Queued/reentrant processing, deferred event-context construction, pluggable state storage, and statechart/scheduler behavior remain future requirements, not Phase 32 work.
- External publication/tagging is handled after milestone proof and authorization, not inferred from an artifact conformance test.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (verbatim from REQUIREMENTS.md) | Research support |
|---|---|---|
| PERF-01 | Users retain direct O(1) compiled singleton dispatch at or above 200,000 transitions per second when the new semantics are unused. | Existing installed native floor and direct lookup tests; preserve both. |
| PERF-02 | Users who do not enable the new semantics incur no unrelated candidate scans, reflection, or per-dispatch allocation. | Current singleton/group selector split; use deterministic structural tests and slots audit. |
| PERF-03 | Maintainers can measure final-state, transition-mode, and rejection costs independently with environment-labelled evidence. | Extend the descriptive scenario reporter, not the durable floor schema. |
| PERF-04 | Users receive conformant behavior from pure-source, compiled-extension, installed-wheel, and release-artifact execution under the existing evidence harness. | Extend one strict collector, then run it behind exact-origin probes in each mode. |
| DOC-01 | Users can learn final states, prioritized telemetry guards, internal and external self-transitions, expected rejection, and owned aircraft commands through the progressive drone tutorial. | Existing controller, telemetry, adapter, and smoke tests are the base. |
| DOC-02 | Users encounter the canonical builder-first interface before advanced direct construction in the README and Sphinx documentation. | README/Quick Start already lead with builder; tighten hierarchy and examples gallery. |
| DOC-03 | Users can migrate from deprecated construction conveniences using documented replacements and compatibility timing. | Present before/after builder replacements for all four names. |
| DOC-04 | Users can clearly distinguish termination from dead-end topology, rejection from guard ineligibility, and internal transition from external self-transition in the public documentation. | Use runnable paired comparisons and exact result fields. |
</phase_requirements>

## Summary

The implementation should be an evidence-and-teaching phase, not another runtime semantics phase. The live selector already uses two direct dictionary lookups and branches to a local immutable candidate group only when the slot is a group; the project has deterministic lookup/rank tests and a fresh installed compiled median floor. Keep those mechanisms intact and add scenario-specific *observations* beside the existing threshold. [VERIFIED: src/fast_fsm/core.py:2965-3051; tests/test_performance_benchmarks.py:143-165,280-323; tools/release_evidence.py:2969-3055]

The largest functional gap is the fixed artifact oracle: its `_scenario_collectors()` inventory currently covers lifecycle, priority, ownership, diagnostics, and sync/async equivalence, but has no phase-specific finality, internal/external self, or `TransitionRejected` collector. The installed-wheel pipeline already copies this oracle into a neutral venv, verifies archive/build/origin first, and compares it with clean source. Extend the oracle and its fail-closed tests before asserting Phase 32 artifact parity. [VERIFIED: tools/artifact_conformance.py:1811-1853,1981-2040; tools/release_evidence.py:3410-3542; tests/test_artifact_conformance.py:396-465]

The drone example already has one `"telemetry_tick"` dispatch per sample, priority values `0`, `10`, `20`, and post-commit entry commands, but `"Landed"` is non-final and returns to `"PreArm"`; there are no internal/external self or expected rejection teaching beats. A progressive rewrite should add these cases without introducing controller-side precedence or actual flight-control claims. README and Sphinx already have builder material, so reorganize and test the existing path rather than create a competing guide. [VERIFIED: examples/drone_failsafes.py:184-325,344-383; docs/examples/index.md:11-57,117-122; README.md:10-25,107-156]

**Primary recommendation:** Plan three separable deliverables in dependency order: fixed semantic oracle and origin-safe mode proof; independent descriptive performance scenarios plus unchanged native floor; controller-owned tutorial and builder-first documentation with executable tests. [VERIFIED: tools/artifact_conformance.py:1811-1853; tools/release_evidence.py:2969-3055,3410-3542; examples/drone_failsafes.py:184-325]

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Rationale |
|---|---|---|---|
| Fast-path and local-work invariant | Library runtime + deterministic tests | Installed benchmark child | Selector owns work shape; native child owns release throughput observation. [VERIFIED: src/fast_fsm/core.py:2965-3051; tests/test_performance_benchmarks.py:143-165; tools/release_evidence.py:3093-3170] |
| Feature-cost observations | Benchmark/evidence tooling | Library public API | Keep instrumentation outside `trigger()`; report by scenario/environment. [VERIFIED: benchmarks/performance_demo.py:1-27,104-176] |
| Semantic parity | Shared artifact oracle | Release evidence verifier | Collector fixes expected behavior; verifier proves archive, origin, mode, and environment. [VERIFIED: tools/artifact_conformance.py:1811-1853,1981-2040; tools/release_evidence.py:2819-2911,3410-3542] |
| Drone telemetry decisions | FSM guards | Telemetry fact service | Controller observes and dispatches once; command adapter receives committed entry effects. [VERIFIED: examples/drone_failsafes.py:104-181,217-285,288-325] |
| Learning path | README/Sphinx/examples | Pytest and Sphinx doctest | Public docs teach; smoke and doctest keep examples executable. [VERIFIED: docs/examples/index.md:1-9,117-122; docs/conf.py:25-27,55-68; Taskfile.yml:239-255] |

## Project Constraints (from AGENTS.md)

- `.github/copilot-instructions.md` is authoritative for workflows and quality gates. Use the active `.planning/` milestone/phase plan for GSD; create or update GitHub Issues only on explicit request. [VERIFIED: AGENTS.md:1-17]
- Use `uv` for Python commands; keep source/native origin explicit; retain slotted hot-path classes and the fresh installed compiled `200,000` ops/sec floor. [VERIFIED: .github/copilot-instructions.md:35-75,250-268]
- Run focused tests during development, then the sequential full suite; mypy is blocking, ty advisory; build HTML docs with warnings as errors and run doctests when docs change. [VERIFIED: .github/copilot-instructions.md:77-83,179-210]
- Preserve `*args, **kwargs` in condition/callback signatures; only `core.py` is mypyc compiled; keep condition modules interpreted. [VERIFIED: .github/copilot-instructions.md:269-289]
- Review intentional baseline writes; CI performs read-only freshness checks; stage explicit task paths only; before session completion commit/push intended work and verify remote sync. [VERIFIED: .github/copilot-instructions.md:85-98,100-126,290-313; AGENTS.md:19-28]

## Standard Stack

No new package is needed or recommended. Use the existing locked environment and first-party harness; the project metadata declares Python `>=3.10` and one runtime dependency, `"mypy-extensions>=1.0"`. [VERIFIED: pyproject.toml:1-9,11-43]

| Component | Repository-resolved version / contract | Purpose |
|---|---|---|
| uv | Executing binary observed `0.12.17`; version is recorded, not a required patch pin. [VERIFIED: `uv --version` 2026-09-19; .github/copilot-instructions.md:87-96] | `uv sync --locked --all-groups`, wheel/sdist builds, isolated wheel installs. |
| pytest | Locked `"8.4.1"`. [VERIFIED: uv.lock:1413-1416] | Focused semantic, artifact, performance, and example tests. |
| Sphinx + MyST | Lock has `"8.1.3"`, `"9.0.4"`, or `"9.1.0"` by Python resolution; `myst_parser` and `sphinx.ext.doctest` are configured. [VERIFIED: uv.lock:1631-1698; docs/conf.py:20-27] | Progressive HTML docs and executable `{testcode}`/`{testoutput}`. |
| mypy/mypyc and setuptools/wheel | Lock: mypy `"1.17.1"`, setuptools `"80.9.0"`, wheel `"0.45.1"`. [VERIFIED: uv.lock:990-993,1585-1588,1933-1936] | Existing selective native build boundary. |
| Ruff / ty | Lock: Ruff `"0.12.11"`, ty `"0.0.1a19"`. [VERIFIED: uv.lock:1560-1562,1890-1893] | Formatting/lint and advisory second type check. |

Official uv documentation confirms `--locked` refuses an outdated lockfile rather than updating it, while `uv build --wheel` selects wheel output and invokes the configured backend. Official Sphinx documentation confirms grouped `testcode`/`testoutput` blocks run in doctest builds; `testcode` executes as one block, so use explicit `assert`/`print` for observable checks. [CITED: https://docs.astral.sh/uv/concepts/projects/sync/; https://docs.astral.sh/uv/concepts/projects/build/; https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html]

**Installation:** Use the existing `task release-baseline-check` and `task release-installed-artifacts-check` pathways, which invoke `uv sync --locked --all-groups` or exact wheel installation as appropriate; do not run a new package install. [VERIFIED: Taskfile.yml:127-145,297-333]

## Architecture Patterns

### System architecture

```text
public API semantics ──> fixed conformance collector ──> source/native record
        │                           │
        │                           └──> neutral installed-wheel children ──> release matrix
        ├──> scenario reporter ──> labelled, non-gating feature observations
        └──> DroneController ──one telemetry_tick──> FSM guards
                 └── TelemetryPolicy facts          └── committed entry ──> AircraftCommands
```

The source/native mode must be established before collecting semantics; wheel evidence separately validates archive mode, package/core paths, loader, and architecture before performance or parity acceptance. The local matrix is explicitly non-authorizing, while a complete hosted release profile is the authorizing one. Do not report a local candidate build as an already published release. [VERIFIED: tools/release_evidence.py:1735-1772,2819-2911,3410-3542,292-333; Taskfile.yml:355-470]

### Recommended project structure and task boundaries

| Boundary | Work |
|---|---|
| `tools/artifact_conformance.py` + its tests | Add deterministic required-value collectors for final/sink, internal/external self, false-guard versus terminal expected rejection; reject missing/unknown/mutated rows. [VERIFIED: tools/artifact_conformance.py:42-113,1811-1853,1981-2040; tests/test_artifact_conformance.py:293-335] |
| `tools/release_evidence.py`, `Taskfile.yml`, installed-artifact tests | Reuse exact-origin and installed proof; add fresh-native/source check seam if needed; keep wheel snapshot and mode checks before semantic comparison. [VERIFIED: tools/release_evidence.py:1709-1772,3410-3542; Taskfile.yml:297-333] |
| `benchmarks/performance_demo.py` + deterministic performance tests | Add separate repeated reachable scenarios with fixed work shape, environment labels, source/build identity, and median samples; keep the native singleton floor unmodified. [VERIFIED: benchmarks/performance_demo.py:75-176; tests/test_performance_benchmarks.py:143-165,280-361; tools/release_evidence.py:3093-3170] |
| `examples/drone_failsafes.py`, its smoke tests, README/Sphinx pages | Layer one concept per beat, post-commit command assertions, and `testcode`/`testoutput` narrative snippets. [VERIFIED: examples/drone_failsafes.py:184-325; tests/test_drone_failsafes_example.py:79-230; docs/examples/index.md:117-122; docs/conf.py:25-27] |

### Pattern 1: Keep the singleton branch direct

The selector uses `"_transitions.get(current_name)"` then `"entries.get(trigger)"`; only `"isinstance(slot, _TransitionGroup)"` enters the candidate loop. Plan a structural regression for no new scan/reflection/allocation on the single-entry path, and retain the existing count test in both pure and native modes. Do not rely on wall-time alone to establish asymptotic work. [VERIFIED: src/fast_fsm/core.py:2979-3051; tests/test_performance_benchmarks.py:143-165,280-323]

### Pattern 2: Strict oracle before comparison

The oracle has exact scenario IDs/fields, `required_values`, sorted rows, a collector-file digest, and a semantic digest. Add new scenarios to definitions, collectors, and independent mutation tests together. Exact new scenario names are the implementer's choice; **do not reuse** `"graph.guard-rejection"` as proof of `TransitionRejected`, because that existing record checks topology/permission rejection. [VERIFIED: tools/artifact_conformance.py:42-113,437-468,1811-1853,1981-2040; tests/test_artifact_conformance.py:293-335,396-465]

### Pattern 3: One sample, one telemetry event

The current controller calls `observe(sample)` then `trigger("telemetry_tick", telemetry_policy=...)`, while registered priority candidates own critical-fault/link/battery ordering. Extend this model with internal self-update and external self-reentry on distinct states or distinct triggers so their lifecycles cannot be confused; use `final=True` only on actual landing terminal states and remove any outgoing restart from a final. The current `"Landed" -> "PreArm"` transition means the script needs an explicit second-flight strategy (new controller instance or a non-final reset branch). [VERIFIED: examples/drone_failsafes.py:184-285,288-325,365-383; tests/test_final_states.py:142-245]

### Anti-patterns to avoid

- Adding feature probes inside `trigger()` or TRACE-enabled allocation to the disabled path; the speed/slots boundary is the product contract. [VERIFIED: src/fast_fsm/core.py:4495-4544; .github/copilot-instructions.md:46-69]
- Counting a prior published `0.4.0` artifact as evidence for unshipped v0.5.0 source. Local Taskfile release projection declares `"tag": "unreleased"` and `"release_version": "0.4.0"`; preserve lineage rather than mislabel. [VERIFIED: Taskfile.yml:382-405,467-470; pyproject.toml:1-4]
- Letting an expected rejection fall through to a lower candidate or issuing an aircraft command on a false guard/rejection. A false candidate is ineligible; `TransitionRejected` is terminal pre-commit; entry actions are post-commit. [VERIFIED: src/fast_fsm/core.py:3008-3032,3104-3168; examples/drone_failsafes.py:261-285]
- Treating Sphinx `literalinclude` alone as an execution test. Keep script smoke tests and add executable docs snippets; literal inclusion only displays source. [VERIFIED: docs/examples/index.md:117-122; tests/test_drone_failsafes_example.py:43-230; Taskfile.yml:248-255]

## Don't Hand-Roll

| Problem | Avoid | Use instead | Reason |
|---|---|---|---|
| Wheel identity/isolation | New venv/probe shell harness | `verify_installed_wheel()` and existing Taskfile tasks | Already snapshot, classify, install in neutral venv, verify origin and loader, compare oracle, then benchmark. [VERIFIED: tools/release_evidence.py:3410-3542; Taskfile.yml:297-333] |
| Semantic comparison | Ad hoc print matching | `collect_conformance()` + `validate_conformance()` + `compare_conformance()` | Strict inventory/digest/payload-safe field differences. [VERIFIED: tools/artifact_conformance.py:1981-2068] |
| Native-floor substitute | Source-tree benchmark proxy | Existing fresh installed compiled median validator | Hard floor validates exact native loader and three samples. [VERIFIED: tools/release_evidence.py:2969-3055,3093-3170] |
| Drone state entry plumbing | Custom `State` subclass solely to call aircraft | `FSMBuilder.on_enter()` callbacks | Existing built-in ordered callbacks already command after commit. [VERIFIED: examples/drone_failsafes.py:261-285; tests/test_drone_failsafes_example.py:90-108] |
| Documentation execution | Unchecked fenced snippets | Sphinx doctest and existing pytest smoke tests | Existing docs config and Taskfile support this. [VERIFIED: docs/conf.py:25-27,55-68; Taskfile.yml:248-255; CITED: https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html] |

## Common Pitfalls

1. **Parity without truth.** All artifacts can agree on a wrong implementation. Put independent `required_values` for each new semantic scenario and mutation tests that prove each field fails closed. [VERIFIED: tools/artifact_conformance.py:1951-1960; tests/test_artifact_conformance.py:224-275]
2. **Build-origin confusion.** A stale source-tree extension can shadow pure Python; `verify_source()` reports exact shadows before import and never deletes them. A fresh-native test must build from known pure origin and relocate only verified generated `core` shadows to a recoverable location before rerunning pure checks. [VERIFIED: tools/release_evidence.py:1709-1772; .github/copilot-instructions.md:87-98]
3. **Moving the floor.** Feature scenarios need independent labels and descriptive medians; do not add their cost to the unfeatured installed singleton threshold or lower its `200_000` constant. [VERIFIED: tools/release_evidence.py:75-76,2969-3055,3093-3170; benchmarks/performance_demo.py:1-27]
4. **Topology-dependent benchmark fixture.** The repeated operation must remain reachable without private current-state mutation; the existing reporter registers equivalent transitions from each reachable result state, and deterministic guard-count tests already vary unrelated topology. [VERIFIED: benchmarks/performance_demo.py:75-101; tests/test_performance_benchmarks.py:280-361]
5. **Final landing restart contradiction.** Current `"Landed"` has an outgoing `"prepare_next_flight"` transition; marking it final while keeping that edge violates the final-state construction contract. Use a separate controller per flight or a non-final staging node, and smoke-test the two-flight narrative. [VERIFIED: examples/drone_failsafes.py:193-259,344-383; tests/test_final_states.py:245-332]
6. **Overloading a single tutorial beat.** A same-state event with `internal=True` omits exit/entry and must not issue an entry command; default external self re-enters and can issue one. Demonstrate both with command and lifecycle counters, not only with unchanged state names. [VERIFIED: src/fast_fsm/core.py:3895-3916,4044-4045,4248-4365; tests/test_transition_modes.py:104-172]
7. **Documentation version drift.** README currently calls out factory helpers in the top “Why” list and offers compatibility timing without concrete before/after replacements. Keep advanced paths explicitly supported and show exact migration rather than saying everything else is deprecated. [VERIFIED: README.md:35-46,107-156; docs/QUICK_START.md:56-68]

## Code Examples

### Builder-first public recipe

The following existing recipe uses verbatim names `"idle"`, `"running"`, and `"start"` from the README; it is the baseline teaching pattern. [VERIFIED: README.md:10-25]

```python
from fast_fsm import FSMBuilder, State

idle = State("idle")
running = State("running")
machine = (
    FSMBuilder(idle, name="Worker")
    .add_state(running)
    .add_transition("start", "idle", "running")
    .build()
)
assert machine.trigger("start").success
```

The additional literal `"Worker"` is also present verbatim in the source recipe. [VERIFIED: README.md:13-20]

### Existing priority and command pattern

The source uses `"telemetry_tick"` with priorities `0`, `10`, and `20` for critical fault, link loss, and battery respectively; `builder.on_enter(...)` binds the adapter commands. Keep this pattern while adding semantic demonstrations. [VERIFIED: examples/drone_failsafes.py:217-243,261-285]

### Existing proof commands

```bash
task pure-source-check
task release-installed-artifacts-check
task release-installed-performance-check
task docs-check
task docs-test
uv run pytest tests/test_drone_failsafes_example.py -x -q
```

These task names and the test filename are verbatim in the repository's Taskfile and test source. [VERIFIED: Taskfile.yml:120-125,239-255,297-333,473-492; tests/test_drone_failsafes_example.py:1-8]

## State of the Art

| Earlier project state | Current project state | Planning impact |
|---|---|---|
| One transition per slot | Direct singleton or ordered immutable candidate group | Feature costs stay local to the `(source, trigger)` slot. [VERIFIED: src/fast_fsm/core.py:2965-3051] |
| Drone priority and post-commit commands only | Finality/mode/rejection primitives now exist elsewhere in core | Tutorial and artifact oracle must catch up; runtime features need not be reinvented. [VERIFIED: examples/drone_failsafes.py:184-285; tests/test_final_states.py:27-142; tests/test_transition_modes.py:76-172; tests/test_expected_rejection.py:106-172] |
| Pure/source performance observations | Fresh installed native median already gates `200_000` | Preserve hard floor and add descriptive feature rows independently. [VERIFIED: tools/release_evidence.py:75-76,2969-3055,5650-5700] |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | [ASSUMED] The current machine can build and test all requested native modes in one local session despite sandbox restrictions and architecture-specific release cells. | Environment Availability | Planner may need a hosted/authorized proof step and should not claim full release-matrix completion from local evidence. |

## Resolved Questions

1. **RESOLVED — release-artifact evidence before publication:** `task release-evidence-local-check` builds current local release-intent candidates and asserts `scope=local-non-authorizing` with `authorizes_release=false`; its provenance records `"tag": "unreleased"`. The separate hosted release profile requires a complete authorizing matrix. Phase 32 proves local candidates under the fixed oracle but makes no publication claim and does not substitute an older published artifact. [VERIFIED: tools/release_evidence.py:292-333,989-991; Taskfile.yml:382-405,467-470,585]
2. **RESOLVED — normal uv cache access:** The prior `EPERM` arose in the restricted research sandbox, not from project dependency policy. The project uses `uv.lock` and `uv sync --locked --all-groups`; authorized execution uses the ordinary uv cache, with no required uv patch pin, offline flag, or custom cache path. If a sandbox cannot access its cache, use its authorized filesystem path for the run rather than changing repository configuration. [VERIFIED: `uv --version` and `uv run python -V` research observations, 2026-09-19; .github/copilot-instructions.md:77-80; Taskfile.yml:134,144]

## Environment Availability

| Dependency | Required by | Available | Version / observation | Fallback |
|---|---|---|---|---|
| `uv` | Locked sync, tests, build, installed probe | Yes; sandbox cache access restricted | `0.12.17` binary observed; `uv run` hit normal-cache `EPERM`. [VERIFIED: shell command outputs, 2026-09-19] | Run normal uv commands with authorized filesystem access; do not impose custom cache/offline policy. |
| `task` | Existing quality/evidence commands | Yes | `/opt/homebrew/bin/task` observed. [VERIFIED: `command -v task` output, 2026-09-19] | Direct documented uv commands if runner unavailable. |
| Python, Sphinx, pytest, mypy | Tests, docs, native build | Locked, runtime execution not probed because uv cache is inaccessible here | Project requires `>=3.10`; lock carries exact dependency resolutions. [VERIFIED: pyproject.toml:1-43; uv.lock:990-993,1413-1416,1631-1698] | Same authorized uv environment; no new dependencies. |
| Hosted release matrix | Cross-platform release authorization | Not locally established | Local profile is explicitly non-authorizing. [VERIFIED: tools/release_evidence.py:292-333; Taskfile.yml:467-470] | Treat local candidate proof as non-authorizing; hosted workflow later. |

## Validation Architecture

| Property | Value |
|---|---|
| Framework | Locked pytest `"8.4.1"`, plus Sphinx doctest; current config has `"testpaths" = ["tests"]`. [VERIFIED: uv.lock:1413-1416; pyproject.toml:54-70; docs/conf.py:25-27] |
| Quick command | `uv run pytest tests/test_artifact_conformance.py tests/test_performance_benchmarks.py tests/test_drone_failsafes_example.py tests/test_readme_examples.py -x -q` (individual files while iterating). [VERIFIED: .github/copilot-instructions.md:175-210; cited test files above] |
| Full command | `uv run pytest tests/ -x -q`, `task docs-check`, `task docs-test`, `task typecheck-mypy`; `task typecheck-ty` advisory. [VERIFIED: .github/copilot-instructions.md:77-83,179-210; Taskfile.yml:239-255] |

| Requirement | Focused automated proof | Wave 0 gap |
|---|---|---|
| PERF-01 | Existing direct lookup and installed native median tests, then `task release-installed-performance-check`. [VERIFIED: tests/test_performance_benchmarks.py:143-165; tests/test_installed_artifacts.py:395-429; Taskfile.yml:473-492] | No new test file; verify after all changes. |
| PERF-02 | Extend pure/native structural tests; retain topology-size and guard-rank assertions. Measure *incremental feature/diagnostic* allocation rather than asserting zero allocations (ordinary results are allocated). [VERIFIED: tests/test_performance_benchmarks.py:143-165,280-361; src/fast_fsm/core.py:3918-3950] | Add explicit unfeatured reflection and incremental diagnostic-allocation regression if current tests do not cover them. |
| PERF-03 | New reporter tests validate scenario inventory, finite samples, metadata and local-work counts; inspect descriptive output. [VERIFIED: benchmarks/performance_demo.py:104-176; tests/test_performance_benchmarks.py:364-375] | New test cases within existing performance test file. |
| PERF-04 | Oracle required-value/mutation tests, source/native run, installed pure+compiled wheel parity, local release projection. [VERIFIED: tests/test_artifact_conformance.py:224-335,396-483; tests/test_installed_artifacts.py:183-229; Taskfile.yml:297-333,355-470] | New oracle scenarios; explicit fresh-native and release-candidate proof orchestration. |
| DOC-01 | Expand drone smoke assertions for single dispatch, priority, both self modes, finality, terminal rejection, command commit order; run script. [VERIFIED: tests/test_drone_failsafes_example.py:90-230] | New smoke scenarios in existing file. |
| DOC-02/DOC-03 | Static guidance order and each migration before/after; Sphinx doctest. [VERIFIED: tests/test_readme_examples.py:13-52; Taskfile.yml:248-255] | New content-order/migration tests. |
| DOC-04 | Executable paired semantic examples and doc-text assertions; HTML warnings as errors. [VERIFIED: docs/conf.py:25-27; Taskfile.yml:239-255] | New docs snippets and documentation regression tests. |

**Sampling rate:** Focused test(s) after each task; full sequential suite, docs warnings-as-errors/doctest, mypy, then fresh installed artifact/performance checks at phase gate. Heavy build/matrix runs should not be the per-edit loop. [VERIFIED: .github/copilot-instructions.md:77-83,175-210; Taskfile.yml:297-333,473-492]

## Security Domain

ASVS 5.0 reorganized chapter identifiers relative to 4.x; do not apply the old “V5 Input Validation” label to the current standard. For this library phase, the applicable concerns are bounded untrusted archive/probe input and payload-safe diagnostic evidence, not web authentication, sessions, access control, or cryptography. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x05-For-Users-Of-4.0.md; VERIFIED: tools/release_evidence.py:2819-2911; tools/artifact_conformance.py:1981-2013]

| ASVS 5.0 category | Applies? | Phase control |
|---|---|---|
| V2 Validation and Business Logic / V2.2 Input Validation | Yes, by analogy for evidence ingestion | Exact fields, bounded JSON/archive, mode/origin checks before accepting records. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json; VERIFIED: tools/release_evidence.py:2819-2911; tools/artifact_conformance.py:1981-2013] |
| Authentication, session management, access control | No web/user service in this phase | Preserve isolated local subprocess boundaries; do not add credentials or service calls. [VERIFIED: tools/release_evidence.py:2648-2681,3410-3542] |
| Cryptography | No new encryption/signing | Existing SHA-256 is an identity/integrity digest for artifact/semantic comparison, not a new secret or authenticity protocol. [VERIFIED: tools/artifact_conformance.py:447-468; tools/release_evidence.py:2393-2461] |

| Threat pattern | STRIDE | Mitigation |
|---|---|---|
| Archive traversal or swapped artifact | Tampering | Snapshot exact archive, bounded member validation, hash check before install and after copy. [VERIFIED: tools/release_evidence.py:1900-1941,2393-2461,3410-3463] |
| Checkout/native-shadow origin laundering | Spoofing | Pure preflight before import; installed runtime paths contained in isolated environment and loader/mode match. [VERIFIED: tools/release_evidence.py:1735-1772,2819-2911] |
| Caller payload in semantic evidence | Information disclosure | Scalar allowlist, sentinel leakage test, bounded failure messages. [VERIFIED: tools/artifact_conformance.py:42-113,1981-2013] |

## Sources

### Primary: inspected project source (HIGH for current repository)

- `src/fast_fsm/core.py:2965-3051,3895-3916,4495-4558` — selector, internal commit, trigger boundary.
- `tools/artifact_conformance.py:42-113,1811-1853,1981-2118` — strict collector and runtime facts.
- `tools/release_evidence.py:75-99,1735-1772,2819-2911,2969-3300,3410-3542` — floor, origin, installed artifact path.
- `benchmarks/performance_demo.py:1-27,75-176` and `tests/test_performance_benchmarks.py:143-165,280-375` — existing descriptive and deterministic work proof.
- `examples/drone_failsafes.py:104-181,184-325` and `tests/test_drone_failsafes_example.py:43-230` — teaching base and smoke coverage.
- `README.md:10-25,107-156`, `docs/QUICK_START.md:56-68`, `docs/examples/index.md:1-122`, `Taskfile.yml:120-145,239-255,297-333,355-492` — public path and tasks.

### Primary external documentation (MEDIUM via websearch classification)

- https://docs.astral.sh/uv/concepts/projects/sync/ — `--locked` and all-group sync semantics.
- https://docs.astral.sh/uv/concepts/projects/build/ — wheel/sdist build modes and backend boundary.
- https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html — runnable `testcode`/`testoutput` behavior.
- https://github.com/OWASP/ASVS/blob/master/5.0/en/0x05-For-Users-Of-4.0.md — ASVS 5.0 chapter restructuring.

## Metadata

**Confidence breakdown:** Standard stack HIGH for lock/project facts, MEDIUM for current external docs; architecture HIGH for inspected code seams; pitfalls HIGH for inspected existing tests and contracts, MEDIUM for unexecuted full hosted release matrix.  
**Research date:** 2026-09-19  
**Valid until:** 2026-10-19 for repository facts, conditional on no intervening code changes.

**Research seam note:** Context7 MCP/CLI were unavailable. The seam selected Context7; official Sphinx/uv/OWASP documentation was read through web fallback. Digest-cache writes were attempted but denied by filesystem policy outside the project; this did not alter repository research or conclusions. [VERIFIED: research-plan and research-store command outputs, 2026-09-19]
