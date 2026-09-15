# Phase 26: Canonical Construction & Evidence Contract - Research

**Researched:** 2026-09-15
**Domain:** Atomic FSM topology construction and isolated comparative benchmark evidence
**Confidence:** HIGH for repository architecture and validation; MEDIUM for external package tooling

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### the agent's Discretion

All implementation choices are at the agent's discretion because this is a
pure infrastructure phase. Preserve the approved constraints: `core.py`
remains the single mypyc compilation unit, topology publication is atomic,
the direct singleton dispatch path is untouched, competitor dependencies stay
outside ordinary CI, and evidence records exact versions, origins, semantic
preflight outcomes, and unsupported cells.

### Deferred Ideas (OUT OF SCOPE)

- Final-state fields and invariants — Phase 27.
- Internal/external self-transition semantics — Phase 28.
- Expected domain rejection — Phase 29.
- Public builder-first deprecations and persistence metadata — Phase 30.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUILD-04 | Maintainers can enforce all retained construction semantics through one private normalization and validation seam. | Route raw adapter requests to one private prepare-and-publish transaction in `core.py`; keep adapter-only parsing outside that seam. |
| BUILD-05 | Users can retry or inspect construction after a failed registration, build, or deserialization without partial topology, stale indexes, or corrupted reusable builders. | Extend the existing topology fingerprint and builder-staging tests across every retained adapter and every late-failure position. |
| PERF-05 | Maintainers can compare semantically equivalent Fast FSM scenarios with exact isolated installations of `python-statemachine` 2.5.0 and 3.2.1. | Use two PEP 723 runner scripts with adjacent locks, strict child JSON, import-origin/version proof, and untimed semantic preflight before timing. |
| PERF-06 | Maintainers receive competitor results as labelled manual or scheduled observations rather than mandatory CI gates. | Remove competitors from project dependency groups, make the task manual, and unit-test orchestration/schema without running third-party timing in CI. |
</phase_requirements>

## Summary

Phase 26 should deepen an architecture that is already substantially present, not replace it. Direct, batch, bidirectional, emergency, quick-build, builder-build, and dictionary construction already converge on `_normalize_transition_request()` plus `_commit_transition_plan()`, and the latter computes immutable replacement slots before publishing them and incrementing `_graph_version` once. `[VERIFIED: src/fast_fsm/core.py:1733-1860]` Existing graph and builder tests already prove non-mutation for many endpoint, batch, helper, priority, and failed-build cases. `[VERIFIED: tests/test_graph_invariants.py:318-383]` `[VERIFIED: tests/test_builder.py:183-225,1073-1105,2096-2150]`

The remaining construction problem is that each adapter still owns an ad hoc raw tuple or dictionary staging shape before it reaches the prepared-plan seam. The builder stores anonymous seven-position tuples, `add_transitions()` parses variable-length rows, and `from_dict()` creates a separate parsed-row tuple before calling the same normalizer. `[VERIFIED: src/fast_fsm/core.py:647-683,1340-1511,5579-5649,5834-5879]` Phase 26 should introduce one private immutable request carrier and one private transaction method that performs request normalization, off-table merging, and publication. Public adapters should only translate their input into that carrier. This is a cold construction-path change; selectors and lifecycle execution must not call the new machinery.

The existing comparison benchmark does not satisfy the evidence contract. It imports all implementations into one process, uses the project environment, writes a mutable `benchmark_results.json`, and depends on a floating project requirement. `[VERIFIED: benchmarks/benchmark.py:15-21,443-470,583-600]` The current project requirement is verbatim `"python-statemachine>=2.5.0"`, while the lock currently resolves verbatim `name = "python-statemachine"` and `version = "2.5.0"`. `[VERIFIED: pyproject.toml:27-32]` `[VERIFIED: uv.lock:1475-1482]` Every ordinary CI job currently using `uv sync --locked --all-groups` therefore installs the competitor. `[VERIFIED: .github/workflows/ci.yml:25-30,74-83,98-107,365-374]` The correct replacement is two exact PEP 723 scripts with adjacent locks, invoked only by a manual Taskfile command and combined by a stdlib orchestrator that rejects version/origin/preflight contradictions before calculating comparisons.

**Primary recommendation:** Formalize the existing prepared-transition machinery as one private construction transaction, then replace the shared-environment competitor benchmark with locked, exact-version child runners whose semantic preflight gates all timing.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Public construction input parsing | Construction adapters in `core.py` | Private request carrier | Public syntax remains adapter-specific, but every adapter emits the same request representation. `[VERIFIED: src/fast_fsm/core.py:1076-1512,1903-2195,5403-5911]` |
| Canonical endpoint and transition validation | Private topology transaction in `core.py` | Condition graph classifier | Canonical state resolution, priority/timing normalization, condition normalization, local slot merging, and publication already live in the compiled core. `[VERIFIED: src/fast_fsm/core.py:1709-1901]` |
| Builder retryability | `FSMBuilder` staging boundary | Private topology transaction | A candidate machine remains local and `_machine` is assigned only after topology and callback wiring succeeds. `[VERIFIED: src/fast_fsm/core.py:5804-5911]` |
| Competitor environment isolation | `uv` PEP 723 child scripts | Adjacent script lockfiles | Inline-metadata scripts ignore surrounding project dependencies and can have adjacent locks. `[CITED: https://docs.astral.sh/uv/guides/scripts/]` |
| Semantic comparability decision | Untimed child preflight | Parent evidence validator | Each child is authoritative for what its installed version can express; the parent only compares cells reported supported by both lanes. `[CITED: https://python-statemachine.readthedocs.io/en/v2.5.0/readme.html]` |
| Environment-labelled observation | Comparison orchestrator | Taskfile manual entry point | Existing project reporters already emit environment labels and explicitly treat timings as observations, not thresholds. `[VERIFIED: benchmarks/performance_demo.py:104-185]` |
| Ordinary CI isolation | Project dependency groups and workflow | Static contract tests | CI can continue using all project groups once competitor distributions no longer belong to any project group. `[VERIFIED: pyproject.toml:11-38]` `[VERIFIED: .github/workflows/ci.yml:25-30]` |

## Project Constraints (from AGENTS.md)

- Use `uv` for all Python package, interpreter, and test operations. `[VERIFIED: .github/copilot-instructions.md:44-47]`
- Preserve current-source lookup, trigger lookup, direct singleton dispatch, and `add_state()` as O(1); candidate work may be local O(k), and builder work is one-time construction work. `[VERIFIED: .github/copilot-instructions.md:58-66]`
- Keep hot-path production classes slotted and keep `core.py` as the only mypyc-compiled runtime module. `[VERIFIED: .github/copilot-instructions.md:49-57,341-353]`
- Preserve callback and condition `*args, **kwargs` compatibility and use a deprecation cycle before removing public symbols. `[VERIFIED: .github/copilot-instructions.md:68-71]`
- Run targeted tests during development and the full sequential suite once before push. `[VERIFIED: .github/copilot-instructions.md:73-77,229-238]`
- Update an SPR in the same commit when significant behavior or public API changes. Phase 26 is private infrastructure, so the executor should update an architecture/testing/tooling SPR if the construction or evidence contract becomes materially different. `[VERIFIED: .github/copilot-instructions.md:358-366]`
- Preserve concurrent work, stage only explicit task paths, and never use `git add .` or `git add -A`. `[VERIFIED: .github/copilot-instructions.md:116-121]`
- Use beads for implementation work and push completed work; this research artifact itself is not an implementation issue list. `[VERIFIED: AGENTS.md:11-65]`

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| CPython | Project contract verbatim: `requires-python = ">=3.10"`; local research runtime 3.12.10 | Runtime and benchmark interpreter | Keep the supported runtime contract unchanged. `[VERIFIED: pyproject.toml:1-9]` `[VERIFIED: local environment probe 2026-09-15]` |
| `uv` | Local 0.12.12; CI setup value verbatim `version: "0.12.6"` | Project sync plus isolated PEP 723 execution and locks | It is the required project package manager and officially supports locked inline-metadata scripts. `[VERIFIED: .github/workflows/ci.yml:25-30]` `[CITED: https://docs.astral.sh/uv/guides/scripts/]` |
| `pytest` | Project specifier verbatim `"pytest>=8.4.1"` | Construction/evidence contract tests | Existing topology and builder suites already provide the right identity-sensitive fixtures. `[VERIFIED: pyproject.toml:12-20]` `[VERIFIED: tests/test_graph_invariants.py:21-59]` |
| Python standard library | CPython-bundled | `json`, `subprocess`, `statistics`, `time`, `platform`, `importlib.metadata`, `pathlib` | Existing evidence tools use strict JSON, runtime origin, medians, and environment labels without a benchmark framework dependency. `[VERIFIED: tools/release_evidence.py:3089-3166]` |
| Task | Local 3.53.1 | Manual maintainer entry points | The project already exposes `benchmark`, `benchmark-compiled`, and `benchmark-compare` tasks. `[VERIFIED: Taskfile.yml:208-223]` `[VERIFIED: local environment probe 2026-09-15]` |

### External comparison lanes

| Package | Exact Version | Purpose | Use Boundary |
|---------|---------------|---------|--------------|
| `python-statemachine` [WARNING: flagged as suspicious — verify before using.] | `2.5.0` | Historical flat-FSM comparison | Only inside its PEP 723 child environment; official PyPI identifies this release and Python `>=3.7`. `[CITED: https://pypi.org/project/python-statemachine/2.5.0/]` |
| `python-statemachine` [WARNING: flagged as suspicious — verify before using.] | `3.2.1` | Current comparison | Only inside its own PEP 723 child environment; official PyPI identifies this release and Python `>=3.10`. `[CITED: https://pypi.org/project/python-statemachine/3.2.1/]` |

The warning is required because the GSD package-legitimacy seam returned `SUS` with the verbatim reasons `"unknown-age"`, `"unknown-downloads"`, and `"no-repository"`; the seam could not retrieve registry signals in this environment. `[VERIFIED: GSD package-legitimacy seam, 2026-09-15]` This is a tooling-confidence warning, not evidence that the upstream project is malicious: both exact PyPI pages and the upstream release documentation were inspected. `[CITED: https://github.com/fgmacedo/python-statemachine/releases]` The plan must therefore include a human verification checkpoint before committing the two new lockfiles.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Two exact PEP 723 scripts | One project dependency group with a floating lower bound | A single environment cannot simultaneously prove 2.5.0 and 3.2.1, and `--all-groups` installs it in ordinary CI. `[VERIFIED: pyproject.toml:27-32]` `[VERIFIED: .github/workflows/ci.yml:25-30]` |
| Adjacent script locks | `uv run --with python-statemachine==...` on every invocation | Exact inline pins constrain the direct package, but adjacent locks also freeze transitive resolution and are explicitly supported by uv. `[CITED: https://docs.astral.sh/uv/guides/scripts/]` |
| Strict stdlib JSON child protocol | Import both competitors into a parent process | Process isolation is the only simple way to keep both versions exact and independently identify their module origins. The existing in-process runner imports one shared `statemachine` module. `[VERIFIED: benchmarks/benchmark.py:15-21]` |
| Existing `perf_counter`/`statistics` approach | Add `pyperf` or `pytest-benchmark` | Phase 26 needs semantic comparability and isolation, not a new measurement framework; current project evidence already uses repeated samples and medians. `[VERIFIED: tools/release_evidence.py:3089-3166]` |
| Private request carrier in `core.py` | Public registrar class or a new runtime module | The phase decision requires a private seam and keeps `core.py` as the compilation unit. `[VERIFIED: .planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md:11-27]` |

**No project-level installation command is recommended.** Remove competitor distributions from `[dependency-groups]`; each comparison child declares its exact dependency inline. Lock and run them explicitly:

```bash
uv lock --script benchmarks/comparison/python_statemachine_2_5.py
uv lock --script benchmarks/comparison/python_statemachine_3_2.py
uv run --locked --script benchmarks/comparison/python_statemachine_2_5.py
uv run --locked --script benchmarks/comparison/python_statemachine_3_2.py
```

The lock/run pattern is documented by uv; the exact filenames are a Phase 26 recommendation, not existing project values. `[CITED: https://docs.astral.sh/uv/guides/scripts/]`

## Package Legitimacy Audit

| Package | Registry | Release Evidence | Source Repo | Verdict | Disposition |
|---------|----------|------------------|-------------|---------|-------------|
| `python-statemachine` | PyPI | 2.5.0 published 2024-12-03; 3.2.1 published 2026-08-01 | `fgmacedo/python-statemachine`, identified by PyPI provenance for 3.2.1 | SUS from seam because registry telemetry was unavailable | Keep exact pins; planner adds `checkpoint:human-verify` before lock generation. `[CITED: https://pypi.org/project/python-statemachine/2.5.0/]` `[CITED: https://pypi.org/project/python-statemachine/3.2.1/]` |

**Packages removed due to SLOP verdict:** none.

**Packages flagged as suspicious:** `python-statemachine` only. The exact package is already an approved project benchmark dependency and has official PyPI/upstream documentation, but the mandatory seam could not establish its normal registry telemetry. `[VERIFIED: pyproject.toml:27-32]`

## Architecture Patterns

### System Architecture Diagram

```text
Public construction inputs
  direct call | batch rows | helpers | quick factory | builder | dictionary | clone
       |
       v
Adapter-only parsing
  syntax/shape errors, dictionary field context, builder async classification
       |
       v
Private immutable transition requests
       |
       v
Canonical construction transaction (core.py, cold path)
  resolve endpoints -> normalize values/conditions -> build prepared plans
       |
       v
Off-table slot merge and whole-plan validation
       | valid                              | invalid
       v                                    v
Publish replacements once                raise bounded error
increment graph version once             publish nothing
       |
       v
Existing direct singleton / local group runtime tables
       |
       +---- trigger()/can_trigger() remain unchanged

Manual comparison entry point
       |
       v
Parent orchestrator (no competitor import)
       |
       +---- uv locked PEP 723 child: python-statemachine 2.5.0
       |
       +---- uv locked PEP 723 child: python-statemachine 3.2.1
       |
       +---- Fast FSM labelled local child
       v
Strict identity + semantic-preflight validation
       |
       +---- supported in both -> timed observation / optional ratio
       |
       +---- unsupported -> explicit unsupported cell, no ratio
       v
Bounded environment-labelled JSON observation
```

### Recommended Project Structure

```text
src/fast_fsm/core.py                         # private request/prepared plan and atomic publication
benchmarks/comparison/
├── common.py                                # strict scenario IDs, schema validation, sampler
├── run_comparison.py                        # parent subprocess orchestration and report
├── fast_fsm_runner.py                       # labelled Fast FSM implementation adapter
├── python_statemachine_2_5.py               # PEP 723 exact historical child
├── python_statemachine_2_5.py.lock          # adjacent uv script lock
├── python_statemachine_3_2.py               # PEP 723 exact current child
└── python_statemachine_3_2.py.lock           # adjacent uv script lock
tests/test_graph_invariants.py                # direct/batch/helper transaction invariants
tests/test_builder.py                         # builder/factory/from_dict retry and parity
tests/test_competitor_benchmark_contract.py   # schema, command, unsupported, and CI-isolation tests
Taskfile.yml                                  # manual comparison task only
pyproject.toml / uv.lock                      # remove shared competitor dependency
```

The comparison directory is new and intentionally outside `tools/release_evidence.py`: PERF-06 makes competitor observations non-gating, while release evidence contains mandatory artifact gates. `[VERIFIED: .planning/REQUIREMENTS.md:61-62]`

### Pattern 1: One raw request carrier, one prepared plan, one publication

**What:** Add a frozen slotted private request carrier for the common transition fields and a single owned transaction such as `_apply_transition_requests_owned(requests)`. That method maps all requests through `_normalize_transition_request()`, then invokes `_commit_transition_plan()` exactly once. `_PreparedTransition` remains the canonical endpoint/condition/value carrier and `_commit_transition_plan()` remains the only method that writes transition slots. This extends the established deep-module seam rather than adding another public abstraction. `[VERIFIED: src/fast_fsm/core.py:759-771,1733-1901]`

**When to use:** `add_transition`, `add_transitions`, bidirectional and emergency helpers, quick-build replay, builder build, `from_dict` after adapter-specific parsing, and clone reconstruction from already-canonical transition entries.

**Why two carriers:** Raw request identity is needed before a machine can resolve string endpoints; prepared identity is needed after canonical state resolution. Collapsing them forces adapters to either mutate early or duplicate canonical resolution.

**Atomicity rule:** Normalize every request, merge every affected `(source, trigger)` slot into local replacements, and only then assign changed slots and increment the graph version. The current publisher already follows this order. `[VERIFIED: src/fast_fsm/core.py:1837-1860]`

### Pattern 2: Adapter context wraps, but does not reimplement, canonical errors

**What:** `from_dict()` should continue reporting transition indexes and field context, and builder preflight should continue reporting the first async requirement. Those are adapter responsibilities. Endpoint identity, priority, timing, condition/unless normalization, async-condition compatibility, duplicate candidate identity, and slot ordering belong to the canonical seam. `[VERIFIED: src/fast_fsm/core.py:1396-1509,1733-1901,5754-5827]`

**When to use:** Any adapter that needs a richer error prefix or schema validation.

**Important distinction:** Whole-machine factory failure is atomic because the candidate has not escaped; direct machine mutation failure is atomic because no published table changes. Tests should assert the appropriate observable boundary rather than require every adapter to construct states in one giant transaction.

### Pattern 3: Builder is a retryable staging area, not a second registrar

**What:** Keep builder-specific state/callback queues and async classification, but stage the same private request objects later consumed by the machine transaction. Never cache the candidate or publish a transient machine type until topology and callback wiring both succeed. Existing code already assigns `_machine_type` and `_machine` only at the end of a successful build. `[VERIFIED: src/fast_fsm/core.py:5804-5911]`

**When to use:** Every `FSMBuilder.build()` attempt, including retries after missing-state, duplicate-priority, async-compatibility, or callback-wiring failures.

**Verification:** Capture the builder fingerprint before a failed build; assert states, requests, callback queues, auto-detect mode, machine type, and `_machine is None` are unchanged; repair the builder and build successfully. Existing tests provide this pattern. `[VERIFIED: tests/test_builder.py:145-180,212-225,2096-2150]`

### Pattern 4: Semantic preflight precedes timing in each child

**What:** Each child must first prove its resolved distribution version, module origin, Python/environment identity, and required behavior for every scenario. Only supported scenarios are warmed and timed. A false preflight is an evidence failure; a genuinely unavailable API is an explicit unsupported cell.

**Minimum cross-version comparable scenarios:**

1. Construct a flat two-state machine with two named events.
2. Verify initial current-state identity.
3. Execute a complete alternating cycle and verify state identity after each event.
4. Verify a false guard prevents state change; compare guarded candidate timing only if both adapters implement the exact same selection shape.

The 2.5.0 official documentation verifies `StateMachine`, `State(initial=True)`, `State(final=True)`, `.to(...)`, event calls/`send`, guards, and `current_state.id`. `[CITED: https://python-statemachine.readthedocs.io/en/v2.5.0/readme.html]` The 3.2.1 PyPI page documents the same basic flat-machine surface, although it also advertises broader statechart behavior that is outside this comparison. `[CITED: https://pypi.org/project/python-statemachine/3.2.1/]`

**Do not compare in Phase 26:** final-state enforcement, internal transitions, or expected rejection. Those Fast FSM semantics do not exist until Phases 27–29 and the Phase 26 boundary explicitly defers them. `[VERIFIED: .planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md:82-88]`

### Pattern 5: Strict child records, tolerant capability matrix

**What:** The parent accepts an exact, bounded schema and validates finite numeric samples, requested-versus-resolved version equality, origin presence, fixed scenario IDs, and preflight-required values. It rejects malformed or contradictory records. It does not fail merely because a declared optional scenario is unsupported; instead it preserves a stable unsupported reason code and omits the ratio.

**Recommended child record fields:**

- schema version and implementation ID;
- requested and resolved distribution version;
- package/module origin and loader name;
- Python implementation/version, platform, and machine;
- exact command, warmup count, operation count, sample count, samples, statistic, and median;
- per-scenario preflight status, required values, and unsupported reason code;
- an explicit label that the result is an observation, not a threshold.

This follows the established installed-performance record, which carries exact command, core origin/loader, execution identity, sample list, median, Python, platform, machine, and environment label. `[VERIFIED: tools/release_evidence.py:3126-3166]`

### Pattern 6: Manual runner, ordinary-CI contract tests

**What:** `task benchmark-compare` may download/use competitor script environments and collect timing. No normal CI workflow invokes it. CI tests only the parent schema validator, child fixture validation, command construction, unsupported-cell behavior, and static dependency isolation.

**Dependency isolation:** Remove `python-statemachine` and the legacy `transitions` comparison dependency from the shared benchmark group if the replacement task no longer imports either from the project environment. The current benchmark group contains verbatim `"python-statemachine>=2.5.0"` and `"transitions>=0.9.3"`. `[VERIFIED: pyproject.toml:27-32]` This is necessary because all ordinary CI jobs synchronize all groups. `[VERIFIED: .github/workflows/ci.yml:25-30,74-83,98-107]`

### Anti-Patterns to Avoid

- **A second public registrar:** It expands API surface and does not help later semantic fields; keep the seam private in `core.py`.
- **One generic transition executor:** This phase is construction-only. Do not route `trigger()` or `can_trigger()` through request normalization.
- **Builder-only validation:** Direct and dictionary users would drift; builder must consume machine-owned canonical validation at build.
- **State-table rollback after partial writes:** Build replacements off-table and publish once instead of mutating then undoing.
- **One comparator environment with two requested versions:** It cannot prove which implementation was imported and cannot execute both exact versions simultaneously.
- **Timing before preflight:** Fast wrong behavior is not comparable behavior.
- **Treating unsupported as zero or failure:** Record it explicitly and omit a ratio.
- **Using `benchmark_results.json` as an implicit durable artifact:** Output should be stdout by default and write only to an explicit path; environment-specific timing should not dirty the repository.
- **Adding comparator timing to ordinary CI:** Network resolution and machine noise make it a manual/scheduled observation, not a merge gate.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exact competitor environments | Custom venv/cache directory manager | uv PEP 723 inline metadata plus adjacent script locks | uv already creates isolated environments and ignores project dependencies for inline-metadata scripts. `[CITED: https://docs.astral.sh/uv/guides/scripts/]` |
| Transition rollback | Undo log over `_transitions` and `_graph_version` | Existing off-table replacement merge followed by one publication | The current transaction already avoids published partial state. `[VERIFIED: src/fast_fsm/core.py:1837-1860]` |
| New public construction API | Registrar/service object | Private request and prepared carriers in `core.py` | The milestone later simplifies public construction; Phase 26 should reduce implementation surface, not add public choices. `[VERIFIED: .planning/STATE.md:34-44]` |
| Benchmark statistics framework | New dependency for medians/samples | `time.perf_counter`/`perf_counter_ns` and `statistics.median` | Established project evidence already uses these primitives and validates samples. `[VERIFIED: benchmarks/performance_demo.py:54-59,152-173]` `[VERIFIED: tools/release_evidence.py:3089-3123]` |
| Comparator import provenance | Path-name assumptions | `importlib.metadata.version()` and resolved module `__file__`/loader | Existing artifact evidence uses metadata and module origins as runtime facts. `[VERIFIED: tools/artifact_conformance.py:2071-2105]` |
| Semantic equivalence inference | Comparing similarly named benchmark functions | Untimed required-value preflight in each child | The existing aircraft adapters contain different application code and transition topology, so matching function names are not proof of matching work. `[VERIFIED: benchmarks/benchmark_fast_fsm.py:92-140]` `[VERIFIED: benchmarks/benchmark_py_fsm.py:53-123]` |

**Key insight:** Construction correctness is a transaction problem, while comparison correctness is an identity-and-semantics problem. Solving both through narrow existing primitives is safer than adding frameworks to either path.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — the phase touches an in-process library, repository configuration, and ephemeral benchmark output; no database or datastore integration appears in the scoped code. `[VERIFIED: pyproject.toml:1-45]` | None. |
| Live service config | None required — ordinary and benchmark CI definitions are checked-in workflow YAML, not a UI-only service configuration. `[VERIFIED: .github/workflows/ci.yml:1-14,356-374]` | Code edit only if a workflow assertion is needed; do not create a scheduled external job in Phase 26. |
| OS-registered state | None — the current benchmark entry points are Taskfile commands and Python files, with no service/unit registration in scope. `[VERIFIED: Taskfile.yml:204-223]` | None. |
| Secrets/env vars | No competitor credential is used. Existing build mode values are verbatim `FAST_FSM_BUILD_MODE: pure` and `FAST_FSM_BUILD_MODE: compiled`; they concern Fast FSM artifact selection, not comparator identity. `[VERIFIED: .github/workflows/ci.yml:19-30,356-374]` | Preserve existing build-mode behavior; child records should not serialize arbitrary environment variables. |
| Build artifacts / installed packages | The local `.venv` currently resolves installed `python-statemachine` as `2.5.0` from `.venv/lib/python3.12/site-packages/statemachine/__init__.py`, and `uv.lock` contains the 2.5.0 project-group resolution. `[VERIFIED: local environment probe 2026-09-15]` `[VERIFIED: uv.lock:1475-1482]` | Code/config migration: remove shared competitor requirements and regenerate `uv.lock`. Artifact refresh: run project sync so the reusable project environment no longer supplies comparator imports. No data migration. |

## Common Pitfalls

### Pitfall 1: Renaming the existing seam without reducing adapter duplication

**What goes wrong:** The code acquires a new `_register_topology()` name, but builders, variable rows, dictionaries, and helpers still separately decide field order/defaults.

**Why it happens:** `_normalize_transition_request()` is already central enough that a superficial rename appears to satisfy BUILD-04.

**How to avoid:** Introduce one immutable raw request representation and have every retained adapter emit it. Test adapter parity by comparing prepared/published identity, not only public trigger success.

**Warning signs:** Builder still stages anonymous tuples; `from_dict` maintains a second tuple schema; adding a future field requires edits in more than adapter parsing plus the canonical normalizer.

### Pitfall 2: Over-centralizing adapter syntax

**What goes wrong:** Dictionary key/index errors, builder async classification, and public row arity become tangled inside one giant registrar.

**Why it happens:** “One seam” is mistaken for “one parser.”

**How to avoid:** Keep syntax validation and contextual error wrapping at the adapter boundary. Centralize only semantic normalization, canonical resolution, whole-plan merge, and publication.

**Warning signs:** `_normalize_transition_request()` receives raw dictionaries; core semantic errors mention JSON indexes; builder mutation is required merely to validate machine topology.

### Pitfall 3: Treating private candidate construction as published mutation

**What goes wrong:** A factory test requires `_graph_version` never to advance inside an object that is never returned, causing unnecessary whole-machine staging complexity.

**Why it happens:** Direct-machine atomicity and factory outward atomicity are conflated.

**How to avoid:** For direct mutation, fingerprint the same machine before and after failure. For builder/factory/deserialization, prove no candidate escapes and reusable input/staging remains unchanged.

**Warning signs:** Factory internals grow rollback machinery even though the failed candidate is unreachable.

### Pitfall 4: Builder failure changes auto-detected type or cached machine

**What goes wrong:** A failed async preflight or late topology conflict persists `_machine_type`, freezes the builder, or leaves `_machine` pointing at a partial candidate.

**Why it happens:** Classification and candidate publication happen incrementally.

**How to avoid:** Recompute candidate type on each build and assign `_machine_type`/`_machine` only after all registrations and callback wiring succeed. Existing tests already cover this failure mode. `[VERIFIED: tests/test_builder.py:2117-2150]`

**Warning signs:** A second build returns the failed candidate; repair requires reconstructing the builder.

### Pitfall 5: Accidentally taxing the direct singleton path

**What goes wrong:** Trigger dispatch creates request objects, consults a registry service, or traverses all topology.

**Why it happens:** A construction abstraction leaks into runtime selection.

**How to avoid:** Confine all new carriers and methods to registration/build paths. Retain the direct `TransitionEntry` slot and existing selector source/trigger dictionary lookup.

**Warning signs:** `trigger()` references `_TransitionRequest`, `_PreparedTransition`, or any adapter; performance tests show unrelated topology affecting singleton dispatch.

### Pitfall 6: Exact dependency text is mistaken for runtime identity

**What goes wrong:** A record says 3.2.1 because the script requested it even though an unexpected module was imported.

**Why it happens:** Environment isolation is assumed rather than proved.

**How to avoid:** Emit and validate requested version, `importlib.metadata` resolved version, module origin, loader, interpreter, and exact command before preflight/timing.

**Warning signs:** No `site-packages` origin; version comes from a constant; both lanes report the same path.

### Pitfall 7: The project lock reintroduces comparator coupling

**What goes wrong:** Exact child scripts exist, but `python-statemachine` remains in a dependency group, so `--all-groups` CI still installs a third implicit comparator environment.

**Why it happens:** The old benchmark group is retained for convenience.

**How to avoid:** Remove competitor distributions from project groups and the project lock's root dependency metadata; commit the two adjacent script locks instead.

**Warning signs:** `uv run python -c "import statemachine"` still succeeds after an ordinary project-only sync; `uv.lock` still lists the competitor as a root dev dependency.

### Pitfall 8: Unsupported cells produce misleading ratios

**What goes wrong:** Missing internal/final/rejection semantics are approximated with application code, then presented as library throughput ratios.

**Why it happens:** A complete table looks more persuasive than an honest capability matrix.

**How to avoid:** Phase 26 times only shared flat primitives. Preserve `unsupported` with a bounded reason code and compute no ratio unless both preflights assert the same required values.

**Warning signs:** A zero duration or zero throughput represents unsupported; adapters contain custom `if` statements to emulate missing FSM semantics.

### Pitfall 9: Manual evidence becomes an accidental merge gate

**What goes wrong:** Ordinary CI downloads both competitors or fails because a noisy ratio moves.

**Why it happens:** The comparison task is added to a broad quality task or the standard benchmark CI job.

**How to avoid:** Keep child execution only in `task benchmark-compare` or an explicitly scheduled workflow. CI may validate static schema/fixtures, never run competitor timing.

**Warning signs:** A CI YAML line names either child runner; a test imports `statemachine`; a ratio assertion has a minimum threshold.

## Code Examples

### Canonical construction transaction skeleton

The exact private names, request field layout, and defaults in this illustrative skeleton are implementation recommendations, not existing repository values. `[ASSUMED]`

```python
# Recommended private shape; names are intentionally non-public.
@dataclass(frozen=True, slots=True)
class _TransitionRequest:
    trigger: str
    from_state: object
    to_state: object
    condition: object = None
    unless: object = None
    priority: object = 0
    condition_ref: str | None = None
    after: object = None
    within: object = None


def _apply_transition_requests_owned(
    self, requests: tuple[_TransitionRequest, ...]
) -> None:
    plans = tuple(
        self._normalize_transition_request(
            request.trigger,
            request.from_state,
            request.to_state,
            request.condition,
            unless=request.unless,
            priority=request.priority,
            condition_ref=request.condition_ref,
            after=request.after,
            within=request.within,
        )
        for request in requests
    )
    self._commit_transition_plan(plans)
```

The existing canonical method names are verbatim `_normalize_transition_request` and `_commit_transition_plan`. `[VERIFIED: src/fast_fsm/core.py:1733-1837]` The proposed `_TransitionRequest` and `_apply_transition_requests_owned` names are implementation recommendations under the agent's discretion.

### Adapter parity assertion

```python
before = graph_fingerprint(machine)
with pytest.raises((TypeError, ValueError)):
    operation()
assert graph_fingerprint(machine) == before
```

This is the existing test pattern: `graph_fingerprint()` includes registered state identity, transition entry identity, condition identity, graph version, current state, and immutable graph snapshot. `[VERIFIED: tests/test_graph_invariants.py:21-59,318-361]`

### Locked isolated child invocation

```bash
uv run --locked --script benchmarks/comparison/python_statemachine_2_5.py
uv run --locked --script benchmarks/comparison/python_statemachine_3_2.py
```

uv documents that PEP 723 inline metadata causes project dependencies to be ignored and that `uv lock --script` creates an adjacent lock reused by script operations. `[CITED: https://docs.astral.sh/uv/guides/scripts/]`

### Parent acceptance order

```text
parse strict JSON
  -> validate exact schema and bounded values
  -> validate requested version == resolved version
  -> validate module origin and interpreter identity
  -> validate semantic required values
  -> accept supported timing samples
  -> compute medians and same-run ratios
```

This ordering mirrors the project's artifact-evidence principle that runtime identity and semantic conformance precede performance acceptance. `[VERIFIED: tools/release_evidence.py:3239-3296,3299-3335]`

## Recommended Plan Decomposition

### Plan 26-01 — Canonical private construction transaction

**Files:** `src/fast_fsm/core.py`, `tests/test_graph_invariants.py`, `tests/test_builder.py`, relevant architecture/testing SPR.

**Work:**

1. Add the frozen slotted raw request carrier.
2. Add one owned request-to-prepared-plan-to-publication method.
3. Route direct, batch, bidirectional, emergency, quick-build, builder-build, and dictionary adapters through it without changing public signatures or behavior.
4. Replace builder anonymous transition tuples with the request carrier while preserving async detection and repairable staging.
5. Add a table-driven adapter matrix that injects early and late invalid rows and compares machine or builder fingerprints.
6. Add a structural source test proving runtime selectors/lifecycle never reference the construction carrier/seam.

**Acceptance:** Existing targeted construction tests remain green; new parity tests prove graph version, tables, current state, builder state, and cached-machine identity are unchanged after every failure.

### Plan 26-02 — Exact isolated comparison lanes

**Files:** `benchmarks/comparison/*`, `tests/test_competitor_benchmark_contract.py`, `pyproject.toml`, `uv.lock`.

**Work:**

1. Define strict shared scenario and child-record contracts.
2. Create Fast FSM, 2.5.0, and 3.2.1 child adapters; competitor children use exact PEP 723 dependencies, while the Fast FSM command uses an absolute runner path and `uv run --project <repo-root>` so a neutral parent working directory still resolves the intended project distribution/core.
3. Add untimed semantic preflight and explicit unsupported cells before timing.
4. Add parent runtime/version/origin/schema validation and bounded environment-labelled output.
5. Generate adjacent script locks after the package-legitimacy human checkpoint.
6. Remove competitor packages from project dependency groups and regenerate the project lock.

**Acceptance:** Both exact children report their requested version and distinct isolated origins; the parent rejects contradictory fixtures; supported cells compare only after required values match; unsupported cells carry no ratio.

### Plan 26-03 — Manual task and ordinary-CI isolation proof

**Files:** `Taskfile.yml`, `tests/test_competitor_benchmark_contract.py`, optionally benchmark developer documentation.

**Work:**

1. Point `task benchmark-compare` at the new parent orchestrator and label it manual observational evidence.
2. Make output stdout-only by default, with an explicit output-path option if persistence is needed.
3. Add static tests proving ordinary CI does not name comparator scripts/tasks and project dependency groups contain no comparator distributions.
4. Keep the existing installed compiled throughput job unchanged; it is a Fast FSM gate, not a competitor comparison.
5. Run exact-lane smoke collection manually, then run targeted and full project quality gates.

**Acceptance:** Ordinary CI installs only project/test/build/documentation requirements; no competitor timing is required for merge; the manual task runs both exact lanes and emits a labelled observation.

**Dependency order:** 26-01 and the schema portion of 26-02 can be implemented independently. Lock generation and 26-03 depend on the comparison schema/children. The full suite should run after all three plans land.

## State of the Art

| Old Approach | Current Recommended Approach | Impact |
|--------------|------------------------------|--------|
| Shared project benchmark dependency `python-statemachine>=2.5.0` | Two exact PEP 723 scripts with adjacent locks | Historical and current versions are independently reproducible and cannot shadow one another. `[CITED: https://docs.astral.sh/uv/guides/scripts/]` |
| One in-process four-library aircraft benchmark | Small shared semantic cells executed in isolated children | Measures library-equivalent work instead of different application workflows. `[VERIFIED: benchmarks/benchmark.py:75-164,167-258,443-520]` |
| Timing result accepted by function name | Runtime identity plus untimed required-value preflight before timing | Prevents fast-but-wrong or unsupported results from entering ratios. |
| Anonymous adapter tuples | Frozen private request objects feeding `_PreparedTransition` | Later semantic fields have one construction propagation path. `[VERIFIED: src/fast_fsm/core.py:647-683,759-771]` |
| Ordinary CI synchronizes competitor packages through `--all-groups` | Competitor packages exist only in manual script environments | CI remains deterministic and does not install/timing-test third-party FSMs. `[VERIFIED: .github/workflows/ci.yml:25-30,365-374]` |

**Deprecated/outdated for this phase:** The current `benchmarks/benchmark.py` orchestration path should no longer be the `benchmark-compare` authority because it imports one shared comparator environment and writes an implicit repository-root JSON file. `[VERIFIED: benchmarks/benchmark.py:15-21,583-600]` The domain example modules may remain as examples or be removed only if repository usage proves them orphaned; Phase 26 should not broaden into example cleanup.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `[ASSUMED]` The recommended new private carrier/method and comparison filenames are suitable names. | Architecture / Code Examples | LOW — names are private and can change during planning without altering the contract. |
| A2 | `[ASSUMED]` The manual comparison task can rely on one-time registry access to populate exact script environments. | Environment Availability | MEDIUM — if maintainers require permanently offline comparison, the plan must document cache/bootstrap requirements rather than vendor packages. |
| A3 | `[ASSUMED]` The legacy `transitions` comparison package can leave the shared benchmark group with the old combined runner. | Architecture Pattern 6 | LOW — if another maintained task still needs it, give that task its own isolated script rather than leaving it in ordinary CI. |

## Resolved Research Questions

1. **Comparison output persistence — RESOLVED:** Print canonical JSON to stdout by default and accept an explicit `--output` path. The legacy implicit `benchmark_results.json` write is removed, and environment-specific results are not committed in Phase 26. This resolution is implemented by Plan 26-05.

2. **Cross-version guarded scenario — RESOLVED:** `false-guard-no-transition` is a required shared scenario, distinct from prioritized candidate fallthrough. Official 2.5.0 guard documentation and the current Fast FSM condition API establish that all lanes can express one source, one target, one false guard evaluation, unchanged current state, and zero transition callbacks. Every child must preflight those exact values before timing; a lane that cannot satisfy them is a contradiction/failure, not an unsupported cell. Optional unsupported cells remain available only for explicitly non-required capabilities. This resolution is implemented by Plans 26-02 and 26-05. `[CITED: https://python-statemachine.readthedocs.io/en/v2.5.0/guards.html]` `[VERIFIED: src/fast_fsm/core.py:1862-1901]`

3. **Scheduled workflow — RESOLVED:** Deliver only the manual `task benchmark-compare` lane. PERF-06 permits manual or scheduled evidence, and no cadence or retention policy authorizes a scheduled workflow. Ordinary CI remains comparison-free. This resolution is implemented by Plans 26-02 and 26-05.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | Project and PEP 723 runners | Yes | 0.12.12 local; 0.12.6 CI setup | None needed. `[VERIFIED: local environment probe 2026-09-15]` `[VERIFIED: .github/workflows/ci.yml:25-30]` |
| CPython | Tests and comparator children | Yes | 3.12.10 local | uv may select an allowed interpreter from script metadata. `[VERIFIED: local environment probe 2026-09-15]` `[CITED: https://docs.astral.sh/uv/guides/scripts/]` |
| Task | Manual entry point | Yes | 3.53.1 | Direct `uv run` child commands. `[VERIFIED: local environment probe 2026-09-15]` |
| `python-statemachine` 2.5.0 | Historical child | Present only in current project `.venv` | 2.5.0 | Exact PEP 723 child environment. `[VERIFIED: local environment probe 2026-09-15]` |
| `python-statemachine` 3.2.1 | Current child | Not installed in project `.venv` | — | Exact PEP 723 child environment; requires registry/cache population once. `[CITED: https://pypi.org/project/python-statemachine/3.2.1/]` |
| Network/package index | First lock/environment population | Restricted in the research sandbox | — | Run the explicit uv lock/run with approved external access; subsequent locked runs may use uv cache. |

**Missing dependencies with no fallback:** none for ordinary implementation and unit tests.

**Missing dependencies with fallback:** local 3.2.1 comparator installation; the locked script environment is the intended fallback and final design.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest, project specifier `"pytest>=8.4.1"` `[VERIFIED: pyproject.toml:12-20]` |
| Config file | `pyproject.toml`, with verbatim `testpaths = ["tests"]`, `python_files = ["test_*.py"]`, and default `-x -q --tb=short --strict-markers`. `[VERIFIED: pyproject.toml:56-71]` |
| Quick run command | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_competitor_benchmark_contract.py -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |
| Current focused baseline | Existing graph and builder suites passed on 2026-09-15. `[VERIFIED: local pytest run 2026-09-15]` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUILD-04 | Every retained adapter produces equivalent canonical topology through one private transaction | Unit/structural | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "adapter or topology or priority"` | Partial — existing parity and atomicity tests exist; add complete adapter matrix. `[VERIFIED: tests/test_builder.py:990-1045]` |
| BUILD-05 | Late failure preserves machine fingerprint or reusable builder staging/cache/type | Unit/property | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "atomic or failure or repair"` | Partial — strong existing coverage; extend to the new carrier and all adapters. `[VERIFIED: tests/test_graph_invariants.py:318-383]` `[VERIFIED: tests/test_builder.py:1073-1105,2096-2150]` |
| PERF-05 | Exact isolated versions/origins, semantic preflight, supported/unsupported cells | Unit contract plus manual integration | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q`; manual `task benchmark-compare` | No — Wave 0 creates the contract test file. |
| PERF-06 | Comparator execution is absent from ordinary CI and results have no threshold | Static/unit | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "ci or observational"` | No — Wave 0 creates the contract test file. |

### Sampling Rate

- **Per task commit:** targeted construction or comparison contract test file.
- **Per wave merge:** `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_competitor_benchmark_contract.py -x -q`.
- **Phase gate:** full suite green, typecheck/ruff/slots-policy green, both manual exact children preflight successfully, and `task benchmark-compare` emits a validated observation.

### Wave 0 Gaps

- Create `tests/test_competitor_benchmark_contract.py` for strict child records, contradiction rejection, unsupported cells, command construction, and CI/dependency isolation.
- Add a complete table-driven adapter transaction matrix to existing graph/builder tests.
- Add fixture records for 2.5.0, 3.2.1, Fast FSM, malformed identity, failed preflight, and unsupported scenario; fixtures must contain no timing threshold.
- No test-framework installation is needed.

## Security Domain

Phase 26 is not a web application and has no authentication, session, authorization, or cryptographic boundary. ASVS is therefore used as secure-development guidance for untrusted dictionary/child-process input, not claimed as application certification. OWASP describes ASVS as a basis for testing technical security controls and secure-development requirements. `[CITED: https://owasp.org/projects/asvs]`

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user or service identity boundary in an in-process FSM/benchmark tool. |
| V3 Session Management | No | No session state or cookie/token lifecycle. |
| V4 Access Control | No | No authorization decision or protected remote resource. |
| V5 Input Validation | Yes | Exact container/scalar/schema checks for `from_dict` and child JSON; bounded records; no callable evaluation from serialized data. `[VERIFIED: src/fast_fsm/core.py:1309-1447]` `[VERIFIED: tools/release_evidence.py:3299-3335]` |
| V6 Cryptography | No | No cryptographic protocol is introduced; artifact hashes are evidence integrity identifiers handled by existing stdlib/tooling, not a new security primitive. `[VERIFIED: tools/artifact_conformance.py:2001-2009]` |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed dictionary publishes a valid prefix before a late error | Tampering | Parse all rows, normalize all requests, merge off-table, publish once. `[VERIFIED: src/fast_fsm/core.py:1476-1512,1837-1860]` |
| Malformed or spoofed child JSON claims a requested version/origin | Spoofing | Parent validates exact field set, requested/resolved equality, absolute origin/loader presence, finite samples, and semantic required values before use. |
| Arbitrary environment or exception payload leaks into evidence | Information Disclosure | Emit an allowlisted scalar record only; never serialize all environment variables or raw exceptions. Existing conformance validation scans forbidden payload tokens. `[VERIFIED: tools/release_evidence.py:3299-3335]` |
| Comparator process writes unrequested repository files | Tampering | Stdout-only default; explicit output path; child current directory in a temporary/neutral location. |
| Dependency confusion or wrong distribution version | Spoofing / Supply Chain | Exact package pins, committed adjacent locks, official PyPI verification, runtime distribution-version and module-origin proof, and human legitimacy checkpoint. `[CITED: https://pypi.org/project/python-statemachine/3.2.1/]` |
| Comparator timing exhausts CI resources | Denial of Service | No comparator child execution in ordinary CI; bounded positive operation/sample counts in manual runner. |

## Sources

### Primary (HIGH confidence)

- `src/fast_fsm/core.py` — current state/transition carriers, construction adapters, canonical normalization, publication, clone, declarative metadata, and builder.
- `tests/test_graph_invariants.py` and `tests/test_builder.py` — identity-sensitive topology and reusable-builder atomicity tests.
- `benchmarks/benchmark.py`, `benchmark_fast_fsm.py`, `benchmark_py_fsm.py`, and `performance_demo.py` — current comparison defects and established environment-labelled reporter pattern.
- `tools/artifact_conformance.py` and `tools/release_evidence.py` — strict semantic/runtime identity and installed performance evidence patterns.
- `pyproject.toml`, `uv.lock`, `Taskfile.yml`, `.github/workflows/ci.yml` — dependency, lock, task, and CI boundaries.
- `.planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` — locked scope and success criteria.

### Secondary (MEDIUM confidence)

- [uv Running scripts](https://docs.astral.sh/uv/guides/scripts/) — PEP 723 project isolation and adjacent script locks.
- [python-statemachine 2.5.0 on PyPI](https://pypi.org/project/python-statemachine/2.5.0/) — exact historical release metadata.
- [python-statemachine 2.5.0 documentation](https://python-statemachine.readthedocs.io/en/v2.5.0/readme.html) — cross-version flat FSM primitives.
- [python-statemachine 3.2.1 on PyPI](https://pypi.org/project/python-statemachine/3.2.1/) — exact current release metadata and provenance.
- [python-statemachine upstream releases](https://github.com/fgmacedo/python-statemachine/releases) — 2.5.0 feature/API evidence.
- [OWASP ASVS](https://owasp.org/projects/asvs) — secure-development verification framing.

### Tertiary (LOW confidence)

- None used for implementation recommendations.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH for repository tools and versions; MEDIUM for external runner provisioning because 3.2.1 is not installed locally.
- Architecture: HIGH — the current normalization/publication and evidence seams were read directly and their focused tests pass.
- Pitfalls: HIGH — each construction risk maps to current adapter code/tests; comparison risks map to the current in-process runner and CI dependencies.
- External package legitimacy: MEDIUM — official PyPI/upstream sources confirm both exact releases, but the mandatory automated seam returned SUS because it could not retrieve telemetry.

**Research date:** 2026-09-15
**Valid until:** 2026-10-15 for construction architecture; recheck external package release/provenance immediately before regenerating comparison locks.
