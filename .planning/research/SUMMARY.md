# Project Research Summary

**Project:** Fast FSM
**Domain:** High-performance, in-process, flat deterministic finite-state machines
**Researched:** 2026-09-15
**Confidence:** HIGH for project integration and semantic recommendations; MEDIUM for current competitor/version details

## Executive Summary

Fast FSM is a performance-oriented flat FSM whose product identity is direct current-state/trigger lookup, immutable local candidate groups, and a fresh installed compiled singleton floor of 200,000 operations per second. Experts would implement this milestone by keeping `core.py` as the single mypyc unit, normalizing and validating topology at construction, and carrying only fixed scalar metadata through the existing selection, lifecycle, result, history, and projection seams.

The recommended v0.5.0 scope is explicit final states with an O(1) termination query, immutable per-transition internal/external self semantics, and a structured expected domain rejection distinct from false guards and unexpected exceptions. External self-transition remains the backward-compatible default; internal transitions skip state exit/entry while retaining transition-level work, logical commit, history, and truthful timing. Expected rejection is caught only at pre-commit eligibility seams and stops priority fallthrough. No new runtime dependency, queue, scheduler, hierarchy, eventless processing, state store, lazy context, or reflection-heavy injection is warranted.

The principal risks are semantic corruption at the commit boundary, incomplete propagation through builders/serialization/diagnostics, swallowed async cancellation, and accidental taxation of the singleton fast path. Mitigate them with normalize-before-publish atomic registration, one canonical scalar snapshot for all cold projections, explicit sync/async and pure/compiled required-value oracles, and a two-tier evidence policy: retain the hard installed compiled singleton floor while reporting feature-local and competitor timings as labelled observations. Compare exact, isolated `python-statemachine` 2.5.0 historical and 3.2.1 contemporary lanes only after untimed semantic preflight.

## Key Findings

### Recommended Stack

Keep the production and build stack unchanged. Final flags, transition mode, termination, and rejection conversion fit existing core types and the standard library; the one runtime dependency remains `mypy-extensions`. Keep CPython >=3.10, mypy/mypyc 1.17.1, setuptools 80.9.0, wheel 0.45.1, and the reviewed uv 0.12.6 evidence pin. Do not combine this semantic work with a compiler/backend upgrade.

**Core technologies:**

- `src/fast_fsm/core.py`: canonical runtime, registration, selection, lifecycle, results, builder, and sync/async execution — preserve it as one mypyc compilation unit.
- Exact slotted/native state and transition metadata: final and internal booleans normalized at registration — keeps dispatch to a direct entry plus one predictable mode branch.
- `TransitionResult` plus a narrow `TransitionRejected`: structured outcome fields and failure-only allocation — avoids a new validator/context framework and preserves successful-path cost.
- `tools/artifact_conformance.py` and `tools/release_evidence.py`: extend the existing source/pure-wheel/compiled-wheel oracle — proves artifact identity and parity without a second packaging system.
- Isolated PEP 723/uv runners for `python-statemachine==2.5.0` and `==3.2.1`: exact historical and contemporary comparison lanes — removes the ambiguity of the current floating lower bound and lock preference.
- Existing stdlib timing (`perf_counter`, `statistics`, `gc`) and pytest/Hypothesis/Sphinx tooling: semantic and evidence tests — avoid adding `pyperf` or `pytest-benchmark` before evidence demonstrates a need.

Detailed stack decisions are in [STACK.md](STACK.md).

### Expected Features

**Must have (table stakes):**

- Immutable `State(..., final=True)` and O(1) `is_terminated` derived from the current state's marker; initial-final machines are valid and non-final sinks remain non-terminated traps.
- Atomic rejection of every ordinary outgoing edge from final states across direct, batch, builder, factory, declarative, bidirectional, emergency, and deserialization paths.
- Per-transition keyword-only `internal=False`, with exact self-target validation; external self-transition preserves current full exit/commit/entry behavior and timing reset.
- Internal self-transition skips all state exit/entry hooks and listeners but runs before/after transition surfaces, actions, history, and logical commit while preserving entry-relative timing.
- Three-way outcomes: false guard/permission falls through a priority group, `TransitionRejected(code)` stops with an uncommitted structured rejection, and all other exceptions retain stage/cause semantics. Cancellation is re-raised.
- Construction, clone, persistence, diagnostics, visualization, history/results, sync/async, and pure/compiled parity.

**Should have (competitive):**

- Feature-local measurements that demonstrate zero topology-scaling cost and preserve the direct singleton representation.
- Payload-safe rejection codes and trace/result metadata, plus callback-order and commit-boundary evidence.
- Exact-version historical/current competitor reports with semantic comparability status, raw samples, artifact provenance, and environment labels.
- Progressive controller-owned drone guidance: direct transitions, guards/priority/timing, internal telemetry refresh, explicit landing finals, and rejection handling.

**Defer (v2+):**

- Bounded deferred/reentrant event queues, lazy event context, and external state-store adapters; these need independent ownership and performance research.
- Hierarchy, parallel regions, eventless transitions, completion events, scheduling, invocation/task supervision, automatic sync/async dispatch, and reflection-heavy injection; these change the engine category or compromise predictable cost.
- A dedicated completion callback or richer localized rejection detail unless real usage proves existing final-entry/after observation and stable codes insufficient.

Detailed feature contracts are in [FEATURES.md](FEATURES.md).

### Architecture Approach

Use one canonical pipeline: exact public-value normalization → canonical endpoint resolution → atomic off-table validation/merge → direct singleton or local immutable candidate selection → one lifecycle seam → result/history/trace. Finality belongs to `State`; internal mode belongs to immutable `TransitionEntry`; expected rejection is a typed input at pre-commit selection and a scalar result outcome. Keep sync and async engines explicit but make their outcome and lifecycle matrices identical.

**Major components:**

1. **State/transition carriers and canonical registrar** — own fixed `final`/`internal` metadata, reject final-source and non-self internal edges before publication, and preserve duplicate identity and graph-version atomicity.
2. **Selectors and lifecycle runners in `core.py`** — retain O(1) direct singleton and local O(k) groups; let only false eligibility fall through; branch once for internal lifecycle and preserve commit/timestamp/cancellation truth.
3. **Results, history, snapshots, and projections** — expose internal and rejection facts additively, capture scalar final/mode data in `_GraphSnapshot`, and let validation/JSON/Mermaid/PlantUML consume that one cold-path source.
4. **Construction adapters** — route State subclasses, builder, factories, decorators, declarative states, clone, and `from_dict` through the same normalization rather than parallel semantics.
5. **Artifact and benchmark evidence** — verify fresh installed pure/compiled wheels, direct native loader/origin, semantic oracle, singleton floor, and exact competitor adapters before timing.

Detailed architecture seams and data flow are in [ARCHITECTURE.md](ARCHITECTURE.md).

### Critical Pitfalls

1. **Inferring finality from missing edges** — keep explicit immutable final metadata and enforce no final-source topology in the one normalize-before-publish registrar; retain structural sink/trap diagnostics separately.
2. **Changing termination or commit truth at the wrong point** — derive `is_terminated` from current state and publish destination/history before entry callbacks; post-commit callback failure or cancellation remains committed and final.
3. **Collapsing internal and external self-transitions** — store per-edge mode, suppress every state exit/entry surface only for internal transitions, retain transition-level work/history, preserve internal residency time, and keep external as default.
4. **Letting expected rejection fall through or catch post-commit signals** — catch only `TransitionRejected` at approved eligibility seams; false continues, rejection and unexpected exceptions stop selection, and lifecycle-raised rejection remains a normal staged failure.
5. **Taxing or invalidating the singleton fast path** — no context allocation, reflection, topology scan, generic group wrapper, or dispatch-time normalization; prove fresh installed compiled direct dispatch and unrelated-topology independence.

Also treat serialization/projection drift, swallowed `CancelledError`, stale native extensions, and unfair floating competitor fixtures as release-blocking evidence failures. The full risk matrix is in [PITFALLS.md](PITFALLS.md).

## Implications for Roadmap

Based on the dependency graph and shared risk boundaries, use seven focused phases:

### Phase 1: Semantic Contract and Benchmark Baselines

**Rationale:** Freeze definitions before implementation because internal mode changes callback/timing behavior and rejection changes priority selection. The unchanged singleton fixture must be protected before any new branch lands.

**Delivers:** Contract tests and sync/async matrices for finality, lifecycle, result/history fields, rejection taxonomy, serialization defaults, zero-cost-when-unused criteria, topology-independence checks, and shared benchmark/evidence schema; exact 2.5.0 and 3.2.1 comparison lanes with semantic preflight.

**Addresses:** Baseline and evidence features; historical/current benchmark comparison.

**Avoids:** Scope drift into queues/statecharts and premature universal performance floors.

### Phase 2: Explicit Final States

**Rationale:** Final metadata is foundational for termination, outgoing-edge validation, projections, and the tutorial; implement it before transition mode and adapter fan-out.

**Delivers:** Exact immutable `final`, O(1) `is_terminated`, initial-final behavior, atomic final-source rejection, commit-boundary and post-commit failure/cancellation semantics, and control-operation/clone rules.

**Addresses:** Explicit finals, termination, final lifecycle, and no-outgoing invariant.

**Avoids:** Sink/final conflation, sticky termination latches, topology scans on queries, and partial batch publication.

### Phase 3: Same-State Transition Modes

**Rationale:** The canonical transition carrier and final-source invariant must be stable before lifecycle specialization; this phase owns the most delicate callback and timing behavior.

**Delivers:** Exact immutable per-transition `internal`, canonical same-object self validation, external compatibility default, internal/external callback-order semantics, logical commit/history, timestamp preservation/reset, and sync/async cancellation parity.

**Uses:** Slotted/native carriers and one lifecycle branch in the existing mypyc unit.

**Avoids:** Machine-wide mode switches, source-is-target inference, internal no-op behavior, and accidental external re-entry changes.

### Phase 4: Expected Domain Rejection

**Rationale:** Rejection is cross-cutting but must enter only after selector/lifecycle carriers are settled; its safety property is the false/rejected/unexpected triad.

**Delivers:** Public `TransitionRejected` with bounded stable code, structured `TransitionResult` rejection fields, singleton/group/async handling, observer/query policy, redaction, and lifecycle-raised rejection classification.

**Addresses:** Expected domain rejection and priority interaction.

**Avoids:** Lower-priority fallback after rejection, broad outer catches, rollback lies, exception leakage, and swallowed cancellation.

### Phase 5: Construction and Persistence Parity

**Rationale:** Once runtime metadata is canonical, every input and reconstruction path must preserve it before cold tooling is updated.

**Delivers:** State subclasses/create, builder, batch/factory/decorator/declarative paths, clone, `to_dict`/`from_dict` additive schema (`final_states`, transition `internal`), exact malformed-input validation, exports, and golden directional compatibility tests.

**Implements:** Canonical normalization and atomic publication across all construction adapters.

**Avoids:** Tuple/schema drift, semantic loss in round trips, executable deserialization, and partially cached builders.

### Phase 6: Diagnostics and Projection Parity

**Rationale:** Projections should consume one settled immutable snapshot, preserving existing structural terminal observations while adding explicit semantic facts.

**Delivers:** Final-aware validators, trap/final distinction, JSON/history/result/trace fields, Mermaid/PlantUML/internal-edge rendering, path/comparison/debug projections, escaping, and bounded-output tests.

**Addresses:** Diagnostic and visualization truthfulness.

**Avoids:** Re-discovering private runtime state, relabeling every sink as final, leaking rejection details, and making tools runtime dependencies.

### Phase 7: Installed Artifact, Benchmark, and Guidance Proof

**Rationale:** This is the release gate only after all semantics and projections are complete; artifact identity and tutorial behavior must be verified against what users install.

**Delivers:** Fresh installed pure and compiled conformance, mypyc/slots/type gates, unchanged compiled singleton median >=200,000 ops/sec, feature-local labelled samples, topology scaling proof, exact-version competitor reports, and doctested progressive drone guidance.

**Addresses:** Installed pure/compiled proof, performance identity, benchmark comparison, and usability.

**Avoids:** Source-checkout benchmarks, stale/shadowed extensions, construction-inclusive timings, unlabelled ratios, competitor drift, and tutorial-owned scheduling or hidden completion processing.

### Phase Ordering Rationale

- Contract and evidence precede runtime changes because they define commit truth, candidate outcome algebra, compatibility direction, and the durable versus descriptive performance policies.
- Finality precedes internal mode because canonical state metadata and final-source registration invariants feed construction, validation, rendering, and completion guidance.
- Internal mode and rejection are separate because lifecycle specialization and selection-time exception classification have distinct failure/cancellation surfaces.
- Construction adapters precede projections so every projection reads settled canonical facts rather than compensating for path-specific semantics.
- Installed evidence and documentation are last because they must prove all artifacts and surfaces together; competitor comparison remains manual and never required CI.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 1:** Confirm exact permitted pre-commit rejection seams, `can_trigger*()` behavior, result field naming, serialization default emission, and comparable scenarios for the historical adapter.
- **Phase 3:** Validate mypyc native/non-native exception boundaries, internal logical commit/history/timestamp behavior, and cancellation at every async await point.
- **Phase 5:** Decide and test directional old/new serialization compatibility; an old reader cannot honor fields it does not know.
- **Phase 7:** Reconfirm current competitor pin/adapter behavior and establish measured feature-local envelopes without turning observations into permanent floors.

Phases with standard patterns (skip `--research-phase` unless implementation reveals a gap):

- **Phase 2:** Immutable boolean metadata, current-state property reads, and atomic registrar validation fit established project patterns.
- **Phase 6:** Snapshot-to-projection fan-out and existing bounded diagnostic/escaping rules are documented repository patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Runtime/build boundaries and integration seams are repository-verified; current competitor release and uv behavior are primary-source but time-sensitive. |
| Features | HIGH | Recommendations follow explicit project constraints, existing lifecycle/result contracts, and cross-checked official FSM documentation. |
| Architecture | HIGH | Core ownership, immutable carriers, selector/lifecycle seams, and artifact oracle are directly evidenced in the repository. |
| Pitfalls | HIGH | Risks map to existing ADRs, source/tests, prior artifact failures, and explicit milestone exclusions; exact feature costs remain unmeasured. |

**Overall confidence:** HIGH for scope, semantics, architecture, and sequencing; MEDIUM for external comparison details and performance until collected.

### Gaps to Address

- **Public naming and compatibility:** Confirm exact `TransitionResult` fields and whether default serialization emits false/empty values or omits them; accept both reader forms if possible while documenting directional loss for old readers.
- **Rejection seam:** Decide whether transition conditions, declarative guards, and state-permission hooks all permit the signal, and ensure composed conditions propagate it without coercion.
- **Historical comparability:** Verify which final/internal scenarios `python-statemachine==2.5.0` can express; mark unsupported cells `not_comparable` rather than forcing ratios.
- **Measured cost:** No feature-local throughput claims are justified yet. Collect raw source/pure-installed/compiled-installed samples and same-run ratios after implementation.
- **Release process:** Confirm how feature-local rows are stored (release manifest versus evidence report) while keeping the singleton floor and competitor suite policies separate.

## Sources

### Primary (HIGH confidence)

- [PROJECT.md](../PROJECT.md) — milestone goal, active requirements, exclusions, constraints, and performance identity.
- [STACK.md](STACK.md), [FEATURES.md](FEATURES.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PITFALLS.md](PITFALLS.md) — detailed milestone research synthesized here.
- [python-statemachine gap assessment](python-statemachine-gap-assessment.md) — scoped comparison, non-goals, and proposed phase shape.
- `src/fast_fsm/core.py`, `_diagnostics.py`, `validation.py`, `visualization.py` — current runtime and projection contracts.
- `tools/artifact_conformance.py`, `tools/release_evidence.py`, `Taskfile.yml`, CI, and tests — installed-artifact identity, semantic oracle, benchmark floor, and existing quality gates.
- Project ADRs 002, 003, 004, 007, and 008 — result-value failures, mypyc boundary, atomic lifecycle, priority topology, and timing semantics.

### Secondary (MEDIUM confidence)

- [`python-statemachine` 3.2.1 on PyPI](https://pypi.org/project/python-statemachine/) and official states, validations, transitions, guards, and upgrade documentation — final states, termination, self-transition modes, validator/rejection vocabulary, and current release identity.
- [`transitions` official documentation](https://github.com/pytransitions/transitions) — comparative reflexive/internal and final-state vocabulary.
- [W3C SCXML 1.0](https://www.w3.org/TR/scxml/) — statechart terminology and explicit boundary for excluded queues, completion events, hierarchy, and macrosteps.
- [uv script and resolution documentation](https://docs.astral.sh/uv/guides/scripts/) — isolated adjacent locks and lock-preference behavior.
- [Python timing documentation](https://docs.python.org/3/library/timeit.html) and [`perf_counter`](https://docs.python.org/3/library/time.html#time.perf_counter) — repeated samples, noise, and monotonic short-duration measurement.
- [mypyc native classes and compilation units](https://mypyc.readthedocs.io/en/stable/native_classes.html) — fixed-field and compilation-boundary constraints.

### Tertiary (LOW confidence)

- None used for roadmap decisions. Exact feature-local performance and future competitor behavior remain validation items, not assumptions.

---
*Research completed: 2026-09-15*
*Ready for roadmap: yes*
