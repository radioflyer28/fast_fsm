# Project Research Summary

**Project:** Fast FSM
**Domain:** High-performance Python finite-state-machine transition selection
**Milestone:** v0.4.0 Priority-Aware Guarded Transitions
**Researched:** 2026-09-06
**Confidence:** HIGH for codebase integration and the behavioral direction; MEDIUM for final API details and measured native performance

## Executive Summary

Fast FSM v0.4.0 should make a `(source state, trigger)` resolve a finite,
statically registered group of guarded transition candidates. The machine—not
an application-side dispatcher—will evaluate those candidates in explicit
numeric-priority order and commit the first fully eligible transition. Lower
integer values win; false guards and state-permission vetoes continue to the
next candidate; exceptions and cancellation fail closed. Once a winner is
selected, the existing atomic lifecycle runs exactly once and never falls
through to another candidate after callbacks or side effects begin.

The implementation should preserve the current two-dictionary lookup and
single-transition fast path. A source/trigger slot remains a direct slotted
`TransitionEntry` until competition exists, then becomes a private immutable
group whose tuple is ordered at registration time. This changes the honest
complexity contract: lookup and singleton dispatch remain O(1), while selecting
from `k` arbitrary guarded candidates is necessarily O(k). The milestone must
amend the constitution and documentation before implementation rather than
hide this local cost behind the old blanket O(1) claim.

Priority is canonical topology metadata and must remain truthful through sync
and async dispatch, builders, declarative handlers, clone, serialization,
results/history, graph snapshots, diagnostics, validation, diagrams, and
installed pure/compiled artifacts. The largest risks are implicit tie-breaking,
an unconditional candidate shadowing safety rules, finalizing each false guard
as a failed trigger, beginning lifecycle work before selection is complete,
and adapters silently collapsing candidates back to one edge. Five ordered
phases—contract/topology, runtime selection, construction parity, tooling
truthfulness, then performance/docs/examples—contain those risks cleanly.

## Reconciled Decisions

The research documents agree on the architecture and first-enabled semantics,
but differed on a few details. Use these decisions as the requirements baseline:

| Topic | Synthesized Decision | Rationale |
|-------|----------------------|-----------|
| Public API | Evolve existing `add_transition(..., priority=...)`; do not add `add_transition_candidate()` | Priority is an attribute of an ordinary transition, and the user explicitly rejected a second API |
| Priority type | Keyword-only, exact non-boolean `int`; lower value wins; signed values and gaps allowed | Simple mypyc/JSON representation and reviewable ordering |
| Default | `priority=0` for ordinary calls | Keeps singleton use compact and gives `TransitionEntry` one concrete scalar type; competing policies should still number every candidate explicitly |
| Ties | Distinct candidates with equal priority in one source/trigger group raise atomically | Registration order, target name, and hash order must never decide precedence |
| Exact duplicate | Same canonical target, condition identity, and priority is an idempotent no-op | Preserves current graph-version/idempotency behavior without permitting conflicting ties |
| Winner | First candidate passing transition guard, matching declarative guard, and target-specific state permission | A candidate is not enabled until all pre-lifecycle policy permits it |
| False eligibility | Continue to next candidate | Rejection is candidate elimination, not failure of the overall trigger |
| Guard/permission exception | Abort selection with cause; do not continue | A broken high-priority rule must not be silently treated as false |
| Async behavior | Await sequentially in the same order; cancellation aborts and re-raises | Timing and concurrency must not replace explicit priority |
| Group exhaustion | One uncommitted `TransitionResult`, one failure-observer notification, no target, and a new `selection` stage | Mixed guard/permission rejection is a group-selection outcome, not accurately attributable to the final rejected guard |
| Unconditional candidate | Allowed as fallback; validation diagnoses any lower candidates it shadows | Registration cannot always prove a custom state/declarative permission is unconditional |
| Observability | Add nullable selected priority to result and history; expose bounded scalar metadata in traces/exports | Same-source/trigger/target candidates otherwise cannot be audited |
| Serialization guard key | Candidate key `(from_state, trigger, priority)` plus legacy trigger-key fallback | A trigger string alone cannot reattach distinct guards |

## Key Findings

### Recommended Stack

Keep the production stack unchanged. The feature requires no new runtime
dependency, language-floor change, compiler upgrade, or new graph library.
Implement the representation and dispatch logic inside the existing selectively
compiled `core.py`; keep conditions and diagnostics interpreted.

**Core technologies:**

- **CPython 3.10+** — use standard dictionaries, immutable tuples, integers,
  and existing synchronization primitives.
- **mypy/mypyc 1.17.1** — retain the reviewed compiler pin while changing the
  native hot-path representation; do not combine this milestone with toolchain
  churn.
- **`mypy-extensions`** — remain the sole runtime dependency for the established
  compilation/subclass boundary.
- **Slotted `TransitionEntry | _TransitionGroup`** — preserve direct singleton
  storage and promote only competing source/trigger slots to an immutable,
  preordered tuple.
- **pytest, pytest-asyncio, Hypothesis, Ruff, mypy, Sphinx, and uv** — reuse the
  existing semantic, type, docs, artifact, and release-evidence harness.

The cold path may rebuild a local group in O(k); dispatch must never sort,
snapshot, validate, or scan unrelated topology. Sanitize guard kwargs at most
once per trigger attempt and reuse equivalent content across candidates.

### Expected Features

**Must have (committed v0.4 scope):**

- Multiple ordinary transitions for one `(source, trigger)`, including multiple
  guarded candidates between the same two states.
- Explicit, unique integer priorities with lower-first, registration-order-
  independent selection.
- First fully eligible sync/async selection with short-circuiting, fail-closed
  exceptions, cancellation safety, and one lifecycle for the winner.
- A stable no-winner result distinct from a missing trigger, with no state,
  history, callback, or observer overcount.
- Atomic fan-out and batch registration, graph-version correctness, exact-
  duplicate idempotency, and clone isolation.
- Priority support through `FSMBuilder`, `add_transitions`, bidirectional and
  emergency helpers, quick builders/factories, and `from_dict()`.
- Candidate-aware declarative handler storage/resolution; no `dir()`-order or
  singular `_handlers[trigger]` overwrite.
- Priority-preserving topology snapshots, query helpers, JSON, Mermaid,
  PlantUML, validation, path generation, results, history, and trace metadata.
- Singleton non-regression plus pure/compiled candidate-depth measurements and
  installed-artifact semantic parity.
- Drone example refactored so the controller records normalized facts and calls
  `trigger("telemetry_tick")` once; guards and FSM topology own all routing.

**Should have (contained differentiators):**

- Validation that distinguishes valid priority-resolved overlap from malformed
  ties and reports definite/possible unconditional shadowing conservatively.
- Numeric priority and candidate rank/count in structured outputs, shown in
  human diagrams only where a group competes.
- Property tests proving the same winner and export order across arbitrary
  registration order.
- Candidate-count diagnostics/guidance for latency-sensitive configurations,
  without imposing an arbitrary runtime cap.

**Defer beyond v0.4:**

- Dynamic or callable priorities, score-based “best match,” and equal-priority
  tie-break policies.
- Runtime priority mutation, transition removal/reordering, or an implicit
  replacement API.
- Parallel async guard evaluation or fallback after an exception, cancellation,
  or lifecycle failure.
- Automatic telemetry classification, scheduler/eventless transitions, or
  polling/heartbeat machinery inside the FSM. Fact providers may calculate
  `heartbeat_older_than(5)` but may not choose transitions.
- Callable serialization, a public topology snapshot v2, hierarchical/
  parallel-state conflict rules, or a new runtime dependency.
- Splitting or broadening the mypyc compilation boundary.

### Architecture Approach

The canonical runtime table becomes:

```text
dict[source_name][trigger]
    ├── TransitionEntry                 # singleton fast path
    │     target · condition · priority
    └── _TransitionGroup                # only when k >= 2
          candidates: tuple[TransitionEntry, ...]
          ascending priority, immutable after publication
```

**Major components:**

1. **Registration planner** — normalizes target/guard/priority, merges complete
   affected groups, validates type/ties/idempotency, and publishes atomically
   with one graph-version increment.
2. **Paired sync/async candidate selectors** — consume the same stored order,
   evaluate all pre-lifecycle eligibility, and return one selected entry or one
   structured failure.
3. **Existing lifecycle executor** — receives only the selected candidate and
   preserves Phase 17 callback, commit, failure, observer, history, and
   cancellation guarantees.
4. **Builder/declarative/configuration adapters** — carry candidate identity
   without overwriting handlers or applying one trigger-wide guard to distinct
   candidates.
5. **Immutable graph projection and interpreted consumers** — flatten one row
   per candidate for clone, serialization, validation, diagnostics, Mermaid,
   PlantUML, JSON, and generated paths.
6. **Evidence harness** — proves single-entry non-regression and equivalent
   candidate behavior in source, pure-wheel, and compiled-wheel execution.

The group value must be immutable because clones shallow-share state,
condition, and transition values. Adding a candidate publishes a replacement
slot rather than mutating a list that another clone or snapshot may observe.

### Critical Pitfalls

1. **Implicit tie order** — reject conflicting equal priorities before any
   mutation and test reversed/randomized registration orders.
2. **Candidate rejection finalized too early** — false guard or permission only
   eliminates that candidate; construct and observe one failure only after the
   group is exhausted.
3. **Lifecycle before selection** — complete all candidate-local guards and
   permission checks before callbacks; never try another candidate after any
   lifecycle stage begins.
4. **Unconditional shadowing** — treat unguarded entries as fallback branches,
   expose priority clearly, and diagnose lower candidates conservatively.
5. **Async timing replaces priority** — await sequentially, propagate
   cancellation, release ownership in `finally`, and leave no candidate tasks.
6. **Adapters collapse identity** — builder staging, declarative handler maps,
   serialization keys, snapshots, target sets, and diagrams must preserve
   parallel same-target candidates.
7. **Performance claims remain stale** — amend the O(1) constitution language,
   retain the direct singleton gate, and characterize O(k) by winner depth.
8. **Side-effecting guards** — document guards as pure, cheap predicates and
   prove each candidate runs at most once within one trigger attempt.

## Requirements Guidance

The roadmapper should derive explicit requirements in these groups.

### Priority Registration

- `add_transition`, builder, decorator, helpers, batch forms, factories, and
  deserialization accept and preserve exact non-boolean integer priority.
- Lower value wins; distinct ties are atomic errors; exact duplicates are
  idempotent; registration order has no behavioral effect.
- Multi-source/batch conflicts leave topology and graph version unchanged.
- Duplicate `(source, trigger)` calls no longer silently replace an edge.

### Runtime Selection

- Sync and async evaluate candidates in ascending priority and stop at the first
  candidate passing transition guard, declarative guard, and state permission.
- False eligibility continues; exceptions and cancellation abort; lower guards
  never run after selection or lifecycle begins.
- Group exhaustion produces one uncommitted selection-stage failure and one
  failure notification; missing triggers remain resolution failures.
- `can_trigger*()` applies identical eligibility without observers or mutation.

### Candidate Identity and Integration

- Result/history identify selected priority while existing callback signatures
  and application kwargs remain unchanged.
- Declarative handlers are candidate-aware and never overwritten or selected by
  attribute discovery order.
- Clone, graph snapshot, topology queries, debug counts, and construction paths
  preserve every candidate.
- `to_dict()`/`from_dict()` round-trip priority and support candidate-specific
  guard attachment without serializing callables.

### Diagnostics and Output

- Validation treats strict ordered candidate groups as deterministic, rejects or
  defensively diagnoses malformed ties, and identifies shadowed fallbacks only
  when provable.
- JSON, Mermaid, PlantUML, Markdown, adjacency data, and generated test paths
  retain candidate multiplicity and priority under existing escaping/budgets.
- Diagnostic work/result budgets count candidates as edges and remain outside
  the dispatch hot path.

### Performance and Proof

- Constitution/docs state O(1) slot lookup and singleton dispatch, O(k)
  candidate selection, and O(k) local group insertion/materialization.
- No sorting or group-proportional allocation occurs during a trigger beyond
  unavoidable guard context handling.
- Installed compiled singleton dispatch remains at least 200,000 operations/sec.
- Tests/benchmarks cover groups of 2/4/8 with first, middle, last, and no match,
  plus async ordering, exception, cancellation, memory, slots, and registration
  scaling independent of unrelated graph size.
- The same winner, result/history metadata, evaluation order, and failure stage
  are proven in source, pure-wheel, and compiled-wheel modes.

## Implications for Roadmap

Use five dependency-ordered phases continuing after Phase 20.

### Phase 21: Priority Contract and Atomic Registration

**Rationale:** Every adapter and runtime path needs one frozen candidate identity
and priority contract. The current constitution explicitly bans the candidate
scan this feature requires.

**Delivers:** ADR/SPR and constitutional amendment; `priority=0` public contract;
slotted `TransitionEntry | _TransitionGroup`; atomic group merge; tie/type/
idempotency rules; immutable publication; helper/fan-out registration; graph-
version and clone-isolation foundations; native compilation probe.

**Addresses:** Explicit deterministic ordering, duplicate-registration migration,
single-entry preservation, and finite candidate topology.

**Avoids:** Registration-order ties, partial batches, mutable groups shared by
clones, invalid priority types, and an implementation that violates project
policy before tests begin.

### Phase 22: Sync/Async Selection and Lifecycle Integration

**Rationale:** With canonical groups established, freeze one eligibility and
failure model before building higher-level adapters.

**Delivers:** Shared sync/async ordered selection; false-rejection fallthrough;
exception/cancellation fail-closed behavior; `selection` no-match result;
candidate priority in result/history/trace; exactly one lifecycle and one
failure notification; candidate evaluation counters and early performance probe.

**Addresses:** First fully eligible winner, `can_trigger*()` parity, state
permission, observability, and lifecycle correctness.

**Avoids:** Per-candidate failure notifications, callback side effects before a
winner, fallback after commit/failure, parallel awaits, and ownership leaks.

### Phase 23: Builder, Declarative, Factory, and Serialization Parity

**Rationale:** Adapters currently encode singular assumptions and can silently
erase the core feature even when direct registration works.

**Delivers:** Priority-aware builder staging/async preflight; multi-handler
declarative storage/resolution and decorator metadata; batch, bidirectional,
emergency, quick-build, and factory parity; candidate-level condition keys;
`to_dict()`/`from_dict()` round trip; clone/query/debug/path identity and
construction conformance tests.

**Addresses:** All public machine-construction modes and same-target candidate
identity.

**Avoids:** Handler overwrite, trigger-wide guard reuse, partial failed builds,
lossy round trips, and direct/builder/declarative semantic drift.

### Phase 24: Candidate-Aware Validation, Diagnostics, and Visualization

**Rationale:** Tooling can become truthful only after the canonical snapshot and
all constructors preserve candidate identity.

**Delivers:** One graph row per candidate; candidate-aware `_DiagnosticEdge`;
revised determinism and transition counts; conservative unconditional-shadow
analysis; priority-aware budgets/adjacency/test paths; JSON, Mermaid, PlantUML,
and Markdown output with stable ordering and existing safe escaping.

**Addresses:** Introspection, charting, export, generated tests, and agent-grade
diagnostics promised by the milestone.

**Avoids:** Edge-set collapse, false nondeterminism warnings, hidden evaluation
order, budget undercounting, and renderers coupling directly to runtime storage.

### Phase 25: Documentation, Drone Example, Performance, and Artifact Proof

**Rationale:** Public guidance and performance claims must describe the final
integrated behavior, then prove what users install rather than only the checkout.

**Delivers:** Drone controller with one telemetry trigger and fact-only telemetry
provider; API/migration/guard-purity docs; updated complexity claims; singleton
and candidate-depth benchmarks; memory/slots evidence; full Ruff/mypy/tests/docs;
installed pure/compiled conformance and throughput proof.

**Addresses:** The motivating use case, safe adoption, performance identity, and
release-level confidence.

**Avoids:** External transition arbitration, stale O(1) marketing, benchmark
blind spots, pure/native divergence, and examples that teach the workaround the
milestone removes.

### Phase Ordering Rationale

- Amend semantics and project policy before code so later phases share one
  priority direction, default, tie rule, identity, and complexity contract.
- Build atomic immutable topology before runtime iteration; otherwise dispatch,
  clone, and concurrent snapshots can observe partial or shared mutation.
- Implement selection before adapters; builder and declarative paths should
  replay a proven core behavior rather than invent their own.
- Update diagnostics after graph identity is stable so all tools consume one
  flattened snapshot instead of learning private union storage.
- Close with examples and artifact measurements because their claims depend on
  the complete integrated implementation, while running an early native probe
  in every core-touching phase to catch regressions sooner.

### Research Flags

Phases likely needing deeper phase research:

- **Phase 21:** Validate mypyc behavior and memory/layout cost for a slotted
  entry/group union; freeze the constitutional amendment and public default.
- **Phase 23:** Resolve exact declarative candidate identity and direct
  `handle_event*()` behavior; verify candidate-key typing for `from_dict()`.
- **Phase 24:** Confirm public schema changes for adjacency and generated path
  records, and set conservative shadow-diagnostic severity.
- **Phase 25:** Measure candidate-count guidance and installed native/pure
  performance before publishing any new quantitative claim.

Phases with established patterns:

- **Phase 22:** Sequential first-enabled selection, short-circuiting, staged
  lifecycle, failure observation, and cancellation build directly on existing
  Phase 17–18 contracts and official state-machine/Python semantics.
- **Phase 24 renderer plumbing:** Once the snapshot schema is frozen, carrying a
  validated integer through existing escaping and budget seams is routine.

## Committed Scope Versus Deferrals

| Committed for v0.4.0 | Explicitly Deferred |
|----------------------|---------------------|
| Static candidate groups per source/trigger | Dynamic/callable priorities or scored selection |
| Existing `add_transition(..., priority=...)` API | A second candidate-registration API |
| Unique numeric precedence and exact-duplicate idempotency | Equal-priority tie-break modes or registration-order semantics |
| Sequential sync/async first-eligible resolution | Parallel guard execution |
| Fail-closed exceptions/cancellation and one lifecycle | Fallback after errors or lifecycle side effects |
| Builder, declarative, factories, helpers, clone, serialization parity | Runtime transition removal/reprioritization/replacement API |
| Candidate-aware results/history/snapshots/diagnostics/visualizations | Callable serialization or topology snapshot v2 |
| Fact-only telemetry provider and one FSM telemetry event | Scheduler, auto-fire timers, or external transition policy |
| Flat-machine candidate priority | Hierarchical and parallel-state conflict resolution |
| O(1) singleton preservation plus O(k) evidence | Claiming arbitrary guarded selection is O(1) |

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Current Python/mypyc/dependency/tool boundaries are directly verified in the repository; no new technology is needed |
| Features | HIGH | Core direction, one-API decision, explicit priority, deterministic ties, and motivating example come from direct user decisions and project inspection |
| Architecture | HIGH/MEDIUM | Singular seams and affected consumers are directly identified; exact compiled layout and cost require measurement |
| Pitfalls | HIGH/MEDIUM | Most failure modes follow directly from current one-entry assumptions and accepted lifecycle contracts; severity/default choices require tests |

**Overall confidence:** HIGH in the milestone shape and phase order; MEDIUM in
unmeasured native performance and the remaining declarative/schema choices.

### Gaps to Address

- **Constitution conflict:** Amend the blanket O(1) and no-candidate-loop rules
  before implementation. This is a prerequisite, not optional documentation.
- **Declarative identity:** Decide how decorator source/target/priority metadata
  maps to machine candidates without requiring inconsistent duplicate policy;
  define ambiguous direct `handle_event*()` behavior.
- **Serialization typing:** Freeze the candidate-level guard key and precedence
  between tuple keys and legacy trigger keys; reject ambiguous mappings.
- **Selection-stage schema:** Add and document the grouped-exhaustion stage while
  preserving existing resolution/guard/state-permission exception stages.
- **Shadow severity:** Report definite versus possible unconditional shadowing
  conservatively because custom state/declarative permission can veto an
  otherwise unguarded edge.
- **Public record migration:** Confirm priority fields on `TransitionResult`,
  `TransitionRecord`, generated path steps, and adjacency rows preserve existing
  positional construction where still desired.
- **Performance guidance:** Set candidate-count recommendations only after pure
  and compiled first/middle/last/no-match data; keep only the existing compiled
  singleton floor as a hard quantitative requirement beforehand.
- **Project metadata cleanup:** `PROJECT.md` currently lists “Transition API
  evolution” under Out of Scope even though it is the milestone's central
  target; requirements generation should remove or correct that contradictory
  row.

## Sources

### Primary Repository Evidence (HIGH confidence)

- [`STACK.md`](STACK.md) — unchanged dependency/toolchain recommendation,
  native representation, benchmark matrix, and complexity analysis.
- [`FEATURES.md`](FEATURES.md) — user-facing registration/selection contract,
  acceptance scenarios, migration, and deferrals.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — singular integration seams, immutable
  group design, lifecycle data flow, adapter/tooling changes, and implementation
  order.
- [`PITFALLS.md`](PITFALLS.md) — failure taxonomy, prevention controls,
  phase-specific warnings, and exit evidence.
- [`PROJECT.md`](../PROJECT.md), [`core.py`](../../src/fast_fsm/core.py),
  [`_diagnostics.py`](../../src/fast_fsm/_diagnostics.py),
  [`validation.py`](../../src/fast_fsm/validation.py), and
  [`visualization.py`](../../src/fast_fsm/visualization.py) — current milestone,
  one-entry assumptions, accepted lifecycle/ownership semantics, and all
  topology consumers.

### External Primary References (MEDIUM confidence via GSD research seam)

- [W3C SCXML 1.0](https://www.w3.org/TR/scxml/) — deterministic first-enabled
  selection before transition execution.
- [XState guarded transitions](https://stately.ai/docs/guards) — ordered guarded
  alternatives, first match, and final fallback convention.
- [python-statemachine conditions](https://python-statemachine.readthedocs.io/en/stable/guards.html)
  — multiple guarded transitions per event and first-passing resolution.
- [Stateless guard clauses](https://github.com/dotnet-state-machine/stateless/blob/dev/README.md#guard-clauses)
  — contrasting mutually exclusive guards and explicit unhandled-trigger policy.
- [Python `bisect`](https://docs.python.org/3.10/library/bisect.html) — O(k)
  ordered insertion/materialization behavior.
- [Python asyncio tasks](https://docs.python.org/3.10/library/asyncio-task.html) —
  sequential await/cancellation and cleanup semantics.
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html)
  and [mypyc Python differences](https://mypyc.readthedocs.io/en/stable/differences_from_python.html)
  — native slots/layout, interpreted subclass, and concurrency constraints.

---
*Research completed: 2026-09-06*
*Ready for requirements and roadmap: yes*
