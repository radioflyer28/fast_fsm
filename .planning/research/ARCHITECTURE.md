# Architecture Research: Priority-Aware Guarded Transitions

**Project:** Fast FSM
**Milestone:** v0.4.0 Priority-Aware Guarded Transitions
**Researched:** 2026-09-06
**Confidence:** HIGH for codebase integration points; MEDIUM for the final compiled performance envelope until measured

## Executive Recommendation

Represent each `(source state, trigger)` as either the existing single
`TransitionEntry` fast path or a private immutable `_TransitionGroup` containing
two or more `TransitionEntry` candidates sorted by explicit integer priority.
Keep the two dictionary lookups that locate the local slot. Only a slot that
actually contains competing candidates performs a candidate-local ordered scan.
This avoids a second registration API, preserves the ordinary machine's memory
and dispatch shape, and makes the unavoidable cost proportional to the number of
rules that can genuinely compete for that event—not to total machine size.

The runtime rule should be: lower integer priority wins; false guards and state
permission vetoes continue to the next candidate; a guard/permission exception
aborts selection; the first fully eligible candidate enters the existing atomic
transition lifecycle. Equal priorities for distinct candidates are invalid. An
exact duplicate registration may remain idempotent. Registration order must not
be a tie-breaker.

This feature conflicts with the current Fast FSM constitution as written. The
constitution says every `trigger()` is O(1) and explicitly prohibits “a loop over
candidates.” No implementation can evaluate an arbitrary set of guarded
alternatives in strict O(1) time: in the worst case it must evaluate `k`
predicates to discover that only the last—or none—passes. The milestone must
therefore amend the contract before changing code: state/trigger lookup remains
O(1), the existing single-entry path retains its throughput floor, and grouped
selection is O(k) in the local candidate count while remaining independent of
the global state/transition count.

Priority must become canonical topology metadata, not a trigger-loop detail.
The same value has to flow through registration, builders, declarative handler
binding, clones, graph snapshots, topology serialization, structured JSON,
validation, diagrams, generated paths, history/results, tests, and benchmarks.
Implementing runtime selection first and repairing these consumers afterward
would temporarily make every inspection surface lie about the machine.

## Current Architecture and the Exact Constraint

Today the authoritative table is:

```text
_transitions: dict[source_name, dict[trigger, TransitionEntry]]
                                              ├── to_state
                                              └── condition
```

`_commit_transition_plan()` reduces each normalized request to a mapping keyed
by `(source_name, trigger)`, so a later entry with the same key replaces the
earlier one. `_prepare_transition()` then performs one outer and one inner
dictionary lookup and prepares exactly one `TransitionEntry`. Sync and async
dispatch both assume that singular shape.

Multiple transitions from one state are already supported when their triggers
differ. Multiple transitions between the same pair of states are also supported
when their triggers differ. The missing capability is multiple guarded edges
sharing the same source and trigger, whether or not those edges share a target.

### Integration Map

| Surface | Current singular assumption | Required change |
|---|---|---|
| `TransitionEntry` | Stores target and guard only | Add explicit `priority`; retain slots |
| `_transitions` | One entry per source/trigger | Store `TransitionEntry | _TransitionGroup` |
| `_PreparedTransition` | Carries one target/guard | Carry priority through atomic planning |
| `_commit_transition_plan()` | Last request wins by dict key | Merge, validate, sort, and atomically publish candidate groups |
| `_prepare_transition()` | Resolves target and declarative handler immediately | Resolve the local slot first; bind target-specific metadata while selecting |
| `can_trigger()` / `trigger()` | Evaluate one guard and one state permission | Share one ordered sync selection contract |
| `can_trigger_async()` / `trigger_async()` | Await one guard | Share the identical ordered async selection contract |
| `FSMBuilder` | Stages 4-tuples | Stage priority and replay it during atomic build |
| `transition()` / `DeclarativeState._handlers` | One handler dict per trigger | Support target/priority-qualified handlers without overwrite |
| `quick_build()` / `add_transitions()` | Tuple shapes omit priority | Extend existing tuple forms; do not add a parallel registration method |
| `from_dict()` / `to_dict()` | One serialized row per slot; conditions keyed only by trigger | Emit every candidate with priority and reattach guards by candidate identity |
| `_graph_snapshot()` | Flattens one edge per slot | Flatten every candidate in deterministic source/trigger/priority order |
| `clone()` | Shallow-copies inner dictionaries | Share only immutable group values; topology additions replace values |
| query helpers | Read one `entry.to_state` | Flatten or existentially test group candidates |
| `_DiagnosticEdge` | No candidate identity | Carry priority/rank and preserve parallel edges |
| validator | Multiple targets imply non-determinism | Treat a strict priority order as deterministic; diagnose shadowing |
| Mermaid/PlantUML/JSON | Labels omit priority | Render/export priority for competing edges |
| history/result/trace | Identifies trigger and target only | Include selected priority so same-target candidates remain distinguishable |
| performance tests | Prove two dict lookups and one-entry throughput | Preserve those gates and add candidate-depth measurements |

## Recommended Core Data Model

```text
source name (dict lookup)
    └── trigger (dict lookup)
          ├── TransitionEntry                         # common fast path
          │     target · condition · priority
          │
          └── _TransitionGroup                        # only when k >= 2
                candidates: tuple[TransitionEntry, ...]
                sorted by ascending priority
```

Recommended private/public shapes inside the existing compiled `core.py` unit:

```python
class TransitionEntry:
    __slots__ = ("to_state", "condition", "priority")

    def __init__(self, to_state, condition=None, priority=0): ...


class _TransitionGroup:
    __slots__ = ("candidates",)

    def __init__(self, candidates: tuple[TransitionEntry, ...]): ...
```

`TransitionEntry` is already exported from `fast_fsm`, so extending its
constructor with a trailing/defaulted priority is preferable to replacing it.
`_TransitionGroup` should remain private. A group must be created only for two
or more entries; collapsing back to one entry preserves the normal shape if a
future removal/replacement feature is introduced.

Do not store a list for every source/trigger. An always-list representation is
simpler on paper but adds one container allocation and an index/iteration branch
to every ordinary transition. Do not store a heap: selection needs complete
priority order and guard evaluation, while heaps optimize repeated destructive
minimum extraction. Do not add a runtime dependency for a sorted collection.

Group objects should be immutable by convention after construction. Every graph
mutation creates and publishes a replacement group instead of mutating a shared
tuple. This is important because `clone()` intentionally shares state, condition,
and transition value objects while copying the outer/inner dictionaries. A
mutated shared group would allow additions to a clone to alter the original.

## Registration Semantics

### Public Contract

Evolve the existing method directly:

```python
fsm.add_transition(
    "telemetry_tick",
    "Mission",
    "EmergencyLanding",
    condition=critical_fault,
    priority=10,
)
```

Recommended rules:

1. `priority` is keyword-only, an integer, and lower values run first.
2. Reject `bool` even though it is an `int` subclass; boolean priority is almost
   certainly an accidental API use.
3. Default priority is `0`, preserving a compact call for non-competing edges.
4. Distinct candidates in one `(source, trigger)` group must have distinct
   priorities. A tie raises `ValueError` before any topology change.
5. An exact duplicate—same canonical target, guard identity, and priority—may be
   an idempotent no-op. A different edge at the same priority is not replacement.
6. Registration order never changes resolution.
7. Multi-source and batch requests validate the entire future graph before one
   atomic commit and one `_graph_version` increment.

The batch planner must not repeat the current `final_entries[(source, trigger)]`
reduction because that destroys candidates inside one request. Instead, build a
temporary mapping from each affected key to all normalized proposed entries,
merge it with that key's existing slot, validate all groups, sort by priority,
materialize replacement slots, and publish only after every affected key passes.

A sorted tuple/list has O(k) insertion because moving list elements dominates
the logarithmic bisection search. That is acceptable at configuration time, but
it must be documented honestly: ordinary first registration remains O(1) after
endpoint validation; adding to a competing group is O(k) in that local group.

### Helper APIs

Existing helpers should carry priority rather than creating a second concept:

- `FSMBuilder.add_transition(..., priority=0)` stages a 5-field record.
- `add_transitions()` accepts a 5-tuple `(trigger, from, to, condition, priority)`
  in addition to its existing 3/4-tuples.
- `add_bidirectional_transition()` accepts `priority1` and `priority2`.
- `add_emergency_transition()` accepts `priority`; each expanded source is
  merged into its local group atomically.
- `quick_build()` should accept the same 3/4/5 tuple family so it does not remain
  a topology-only dead end for the milestone's central feature.
- `quick_fsm()` forwards the extended quick-build shape.

The helper expansion belongs in the same registration phase because leaving any
path with overwrite semantics creates two incompatible graph models.

## Runtime Selection Pipeline

The two dictionary lookups still resolve the local slot:

```text
current state + trigger
        │
        ▼
TransitionEntry ───────────────▶ existing single-entry fast path
        or
_TransitionGroup
        │
        ▼
for candidate in ascending priority:
    transition guard false?       continue
    declarative guard false?      continue
    source permission false?      continue
    otherwise                     SELECT and stop
        │
        ▼
existing lifecycle: before → exit → commit/history → enter → handler → after
```

Eligibility must include all pre-lifecycle policy that can vary by target:

1. the candidate's registered `condition` / `unless` guard;
2. a matching declarative handler guard for that trigger, target, and priority;
3. `source_state.can_transition(trigger, candidate.to_state, ...)` or its async
   equivalent.

False is ordinary ineligibility and proceeds to the next candidate. An ordinary
exception is not equivalent to false: abort the trigger with its current
redacted guard/state-permission result and hidden cause. Falling through after
an exception would hide a broken high-priority safety rule. In async selection,
`CancelledError` must finalize failure once and re-raise unchanged; lower
candidates are not evaluated.

Once a candidate is selected, no other candidate guard is evaluated and the
existing ADR-004 lifecycle runs exactly once. Before/exit/enter/declarative/
after callbacks belong to the selected edge only. Candidate selection remains
inside the existing sync/async ownership envelope, so topology and current state
cannot change between guard evaluation and commit.

If the group exists but no candidate is eligible, return one failure, invoke
`on_failed` once, and expose no target. Add a stable `selection` lifecycle stage
for this grouped exhaustion case rather than claiming that the final rejected
guard or state permission was uniquely causal. Missing source/trigger remains a
`resolution` failure; raised conditions retain `guard`; raised state policy
retains `state-permission`.

### Shared Preparation Without Common-Path Regression

`_prepare_transition()` currently sanitizes kwargs once only when a registered
or declarative guard needs them. Retain that property:

- for a `TransitionEntry`, keep the current direct target/handler preparation;
- for a `_TransitionGroup`, sanitize at most once for the whole selection and
  reuse that mapping for every evaluated guard;
- lifecycle callbacks still receive the original `*args, **kwargs` under the
  existing contract;
- no graph snapshot, validation, sorting, or allocation proportional to total
  topology may enter dispatch.

Factor candidate eligibility into paired private selectors, not four copied
loops. A sync selector and async selector may differ at await boundaries, but
both must consume the same stored order and produce the same selected priority,
target, stage, and error rules. `can_trigger*()` uses the selector without
failure observers; `trigger*()` uses it and then enters lifecycle. As today,
calling `can_trigger()` before `trigger()` evaluates user guards twice; this
feature should not pretend otherwise.

## Sync/Async Parity

`AsyncStateMachine` inherits topology registration and storage, so priority
must not be represented in an async-only table. The parity contract is:

| Case | Sync | Async |
|---|---|---|
| Single unconditional entry | Existing direct path | Existing direct path |
| Single sync guard | Evaluate once | Evaluate once inline |
| Group with sync guards | Ordered first eligible | Same order and winner |
| Group with async guard | Reject before registration/dispatch | Await in priority order |
| Guard returns awaitable unexpectedly | Close/reject; abort selection | Await; continue only if false |
| Guard raises | Failed result; no fallback | Same failed result semantics |
| Cancellation during candidate N | Not applicable | Finalize once, re-raise, no fallback |
| All candidates false | One uncommitted selection failure | Same |
| Winner selected | One existing sync lifecycle | One existing async lifecycle |

Builder auto-detection must scan every staged candidate guard, including nested
condition wrappers and declarative guards. Explicit-sync build must reject an
async requirement anywhere in a candidate group before publishing a machine.
Pure-Python and mypyc-installed artifacts must produce identical winner,
evaluation order, result/history fields, and failure stage.

## Declarative-State Integration

Declarative support contains a second singular map today:
`DeclarativeState._handlers[trigger] = handler_info`. Discovery silently
overwrites an earlier decorated method with the same trigger. Priority-aware
topology makes that ambiguity user-visible and must be fixed in this milestone.

Recommended model:

```text
_handlers[trigger] -> tuple[handler metadata, ...]
handler identity   -> from metadata + to metadata + optional priority
```

Extend the existing `@transition(...)` decorator with optional `priority`, and
make `_resolve_declarative_handler()` match canonical source, trigger, target,
and selected priority. Two handlers with the same effective selector are an
error during state construction, not a `dir()`-order overwrite. A machine edge
with a target/priority-qualified handler binds that one action after commit;
lower-priority handler actions never run.

For direct `DeclarativeState.handle_event*()` calls, where no machine target is
available, multiple matching handlers must either be resolved by their explicit
decorator priorities using the same first-eligible rule or rejected as
ambiguous. Do not quietly choose `dir()`/definition order. The preferred design
is ordered direct resolution because it gives declarative states the same
deterministic rule model, but requirements should make this public behavior
explicit.

Decorator guard evaluation must remain exactly once per candidate attempt.
The existing ContextVar marker is target-qualified; extend it with priority so
same-target candidates do not suppress the wrong handler guard.

## Results, History, and Candidate Identity

Source, trigger, and target do not uniquely identify a selected edge once the
library allows two candidates between the same states. Append a defaulted
`priority: int | None` field to `TransitionResult` and `TransitionRecord`.
Successful results and history records carry the selected priority. Failures
before selection use `None`; a guard/permission exception may carry the
candidate priority internally or publicly if requirements choose, but must not
expose caller payloads or condition representations.

This additive scalar also lets tests and diagnostic tooling prove which rule
won when targets are identical. Existing callback signatures should remain
unchanged: do not inject a reserved priority key into application kwargs. A
candidate-specific action belongs in a target/priority-qualified declarative
handler or an application callback that already knows the rule context.

Default TRACE output can remain category-only. If `FSMTraceEvent` is extended,
priority is a safe scalar but must still reach output only through the existing
explicit redactor allowlist. Emit one trace record for the final trigger outcome,
not one per rejected candidate; detailed candidate tracing would multiply hot
path work and leak policy shape by default.

## Snapshots, Clone, Serialization, and Queries

### Private Graph Snapshot

Flatten every candidate into `_GraphSnapshot.transitions`, ordered by:

```text
(source name, trigger, ascending priority)
```

Extend `_GraphTransition` with at least `priority` and enough grouping metadata
(`candidate_rank`/`candidate_count` or a boolean `competing`) for renderers to
avoid displaying noisy default priorities on ordinary edges. Retain canonical
state/condition identities in the private snapshot and scalar condition names
for interpreted diagnostics. Snapshot capture stays O(V + E), ownership-safe,
and entirely outside dispatch.

### Clone

The current clone copies each source's trigger dictionary but shares entry
objects, conditions, and states. That remains valid if entries/groups are never
mutated after publication. Adding a candidate to either machine must replace
that dictionary value with a newly materialized group. Add clone tests that
register a new candidate on the clone and prove the original snapshot, group,
and graph version remain unchanged.

### Topology Serialization

`to_dict()` must emit one row per candidate and include priority. It may omit the
default priority on non-competing entries for compactness, but emitting it
unconditionally is simpler and more stable for round trips. Conditions remain
objects and therefore are not serialized.

The current `from_dict(..., conditions={trigger: guard})` cannot reconstruct a
group whose candidates have distinct guards. Evolve the same `conditions`
parameter to accept candidate identity keys such as
`(from_state, trigger, priority) -> guard`; a trigger-only key may remain a
single-transition convenience. This avoids inventing serializable callable
identities and lets repeated source/trigger/target edges remain distinct.

Public runtime `snapshot()`/`restore()` persist only active state and should
remain version 1; they do not contain topology. This feature does not justify a
snapshot-v2 format.

### Query Helpers

- `triggers` and `get_available_triggers()` continue returning unique trigger
  names because the dictionary key is unchanged.
- `get_reachable_states()` returns the union of all candidate targets.
- `transition_exists(trigger, from, to)` returns true if any candidate reaches
  the requested target.
- `debug_info()["transition_count"]` counts flattened candidate edges, not
  source/trigger slots.
- `validate_transition_completeness()` flattens candidates for potential
  reachability while retaining one event cell per source/trigger.
- `_resolve_trigger()` is a private compatibility seam and should return the
  selected entry/priority, not a group that callers could execute incorrectly.

## Validation and Diagnostic Graph

Extend `_DiagnosticEdge` with priority and group metadata. All graph algorithms
continue to treat candidates as potential directed edges: guarded transitions
already make reachability optimistic, and priority does not change that
structural interpretation.

The existing validator's `transitions[from][event]` set collapses two candidates
with the same target. It must no longer be the source of transition counts or
determinism. Counts come from `len(graph.edges)`. Dense/sparse adjacency rows
must preserve parallel candidates and their priorities.

Revise determinism semantics. Multiple targets for a state/event are no longer
non-deterministic when the candidate group has a strict explicit order and the
runtime selects the first eligible rule. `check_determinism()` should report
true for a valid priority group and report malformed/tied groups only as a
defensive diagnostic (normal registration already rejects them).

Add priority-specific analysis to `EnhancedFSMValidator`:

- duplicate priorities in one group: error (defensive corruption check);
- unconditional earlier candidate that statically shadows later candidates:
  warning/error with source, trigger, and priority;
- candidate groups containing only one entry: internal normalization warning;
- very large candidate groups: informational complexity warning;
- guarded parallel edges: valid deterministic topology, not a design defect.

Shadow detection must be conservative. A transition with no registered guard
may still be vetoed by a custom `State.can_transition()` override or a matching
declarative guard. Only call it definitely unreachable when the snapshot proves
the earlier candidate has no effective guard and the source uses unconditional
base permission; otherwise label it a possible shadow.

`generate_test_paths()` currently returns `(from, event, to)` tuples, which
cannot distinguish same-target candidates. Since this milestone accepts a
pre-production semantic/schema change, change each step to include priority
(for example `(from, event, priority, to)`) rather than returning duplicate
indistinguishable paths. Record this as a public migration item.

## Visualization and Structured Export

All existing outputs derive from one `_GraphSnapshot` through
`_DiagnosticGraph`; priority should follow that established seam rather than be
re-read from live `_transitions`.

Recommended output behavior:

- Mermaid/PlantUML render every candidate as a parallel edge and append a
  priority label only for competing groups, e.g. `telemetry_tick {p=10}
  [critical_fault]`.
- `to_json()` topology transitions include `priority`, `candidate_rank`, and
  `has_guard`; sparse adjacency edge rows carry the same scalar identity.
- Dense adjacency transition records include priority, and the strict caller-
  supplied adjacency validator compares it.
- Markdown transition tables add a Priority column and do not collapse equal
  source/event/target rows.
- Escaping remains final-sink and grammar-specific; priority is rendered from a
  validated integer, never from caller text.
- Diagnostic work/result budgets count every candidate edge, so a group of `k`
  contributes `k` edges. Dense cell allocation still depends on state/event or
  state/state cardinality, while result/work counts grow with candidates.

No priority analysis should run inside `trigger()`. Construction enforces local
invariants; richer shadowing and graph-quality checks stay opt-in in
`validation.py`, preserving the core/diagnostics import boundary.

## Hot-Path Preservation and Complexity Contract

The constitutional amendment should state these exact bounds:

| Operation | Required complexity |
|---|---|
| Locate source/trigger slot | O(1), two direct dictionary lookups |
| Trigger a single-entry transition | O(1) excluding user guard/callback work |
| Select from `k` competing candidates | O(k) guard/permission evaluations in the worst case |
| Add first transition to an unused slot | O(1) excluding endpoint validation |
| Add/merge a candidate into a group | O(k) local materialization/sorted insertion |
| Graph snapshot / serialization | O(V + E), explicit inspection only |
| Validation/rendering | Outside runtime hot path and bounded by diagnostics budgets |

The existing topology-size tests should continue proving that ordinary trigger,
`can_trigger`, state addition, and first transition registration do not scan
unrelated states or transitions. Add a counting guard suite for groups of size
2/4/8 that proves first, middle, last, and no-match evaluation counts exactly.

Benchmarks need two separate claims:

1. **Non-regression claim:** installed compiled single-entry trigger remains at
   or above the existing 200,000 ops/sec release floor. The current release
   evidence probe already exercises alternating unconditional single entries
   and should remain unchanged so historical observations stay comparable.
2. **Feature cost characterization:** measure grouped sync dispatch at several
   candidate depths (winner first/middle/last and no winner), plus a guarded
   single-entry baseline. Report per-evaluated-candidate cost with environment
   labels; do not promise O(1) or one universal group throughput floor before
   measurement.

Also measure memory for an ordinary entry, the two-entry group threshold, and
incremental candidates. Every new runtime class remains slotted and must pass
the recursive slots-policy audit and mypy/mypyc compilation guard.

## Recommended Implementation Order

### Phase 1 — Contract and Canonical Topology Model

- Write an ADR for explicit numeric priority, first-eligible semantics, ties,
  exceptions, and candidate identity.
- Amend the constitution's O(1)/“no candidate loop” wording and performance
  standards before implementation.
- Add `priority` to `TransitionEntry`/prepared plans and introduce private
  `_TransitionGroup` inside `core.py`.
- Implement atomic group merge, tie rejection, idempotency, graph versioning,
  clone isolation, and helper registration paths.
- Extend invariant/property tests before changing trigger behavior.

This phase is foundational: every later consumer needs one canonical candidate
representation and stable semantics.

### Phase 2 — Sync Selection and Lifecycle Integration

- Split slot preparation from candidate selection without changing the existing
  single-entry branch.
- Implement ordered sync eligibility across transition guard, declarative guard,
  and state permission.
- Define no-winner/exception/failure-observer behavior and selected priority in
  result/history.
- Prove lifecycle callbacks execute once for only the winner.
- Run targeted topology-size and compiled single-entry benchmarks immediately.

### Phase 3 — Async and Declarative Parity

- Implement the paired async selector with identical ordering/failure semantics.
- Preserve cancellation, ownership, and awaitable rejection contracts.
- Upgrade declarative handler storage/resolution to source/target/priority
  identity; add decorator priority metadata and duplicate-selector validation.
- Update builder async preflight across every candidate and handler guard.
- Run pure/native parity traces for winner, all-false, exception, and
  cancellation cases.

This phase follows sync selection so it ports a frozen contract instead of
inventing a second one.

### Phase 4 — Construction, Serialization, and Introspection Truth

- Extend builder, batch, bidirectional, emergency, quick-build, and dictionary
  factory shapes.
- Make `to_dict()`/`from_dict()` round-trip priority and candidate-specific guard
  attachment.
- Update query helpers, debug counts, `TransitionResult`, `TransitionRecord`,
  public docstrings, and type annotations.
- Ensure runtime `snapshot()`/`restore()` remain unchanged.

### Phase 5 — Snapshot, Validation, and Visualization Truth

- Flatten candidate groups through `_GraphSnapshot` and `_DiagnosticGraph`.
- Update sparse/dense adjacency, path generation, counts, determinism, and
  priority/shadow diagnostics.
- Add priority to JSON, Mermaid, PlantUML, Markdown documents, and strict
  adjacency compatibility validation.
- Retain one-snapshot/one-budget behavior and test hostile labels plus duplicate
  source/event/target edges.

### Phase 6 — Example, Documentation, and Performance Evidence

- Refactor the drone loop to emit only `telemetry_tick`; put critical fault,
  heartbeat age/link loss, low battery, home reached, and touchdown rules in
  priority-aware `FuncCondition` transitions.
- Keep telemetry policy as a fact/measurement provider only (for example,
  `heartbeat_older_than(5)`), never a transition selector.
- Document deterministic evaluation, side-effect expectations for guards,
  complexity, tie errors, and migration from replacement semantics.
- Add candidate-depth microbenchmarks, preserve the installed single-entry
  release gate, run slots/mypy/mypyc checks, docs warnings-as-errors, the full
  suite, and installed pure/compiled parity evidence.

## Architectural Risks and Controls

| Risk | Consequence | Control |
|---|---|---|
| Constitution left unchanged | Feature violates the project's highest design authority | ADR and constitutional amendment first |
| Registration order used as tie-break | Refactoring setup code silently changes safety behavior | Explicit integer priority; reject distinct ties |
| False and exception treated alike | Broken high-priority rule silently falls through | False continues; exception aborts with cause |
| State permission checked only after winner | Higher guard can block a lower eligible target | Include target-specific permission in candidate eligibility |
| Lifecycle begins before selection finishes | Exit/action side effects occur for rejected candidates | No lifecycle callback until one winner is fixed |
| Mutable group shared by clone | Clone registration changes original topology | Immutable tuples; replace slot values atomically |
| Declarative trigger map still singular | Handler overwrite or wrong post-commit action | Target/priority-qualified handler groups |
| Serialization keyed only by trigger | Distinct candidate guards cannot be restored | Candidate-identity guard mapping |
| Validator keeps old determinism rule | Valid ordered groups reported non-deterministic | Determinism means strict priority/first-match |
| Graph adapters collapse same target | Counts and exports lose real rules | Preserve one diagnostic edge per candidate |
| Priority omitted from result/history | Same-target winner cannot be identified | Append selected priority scalar |
| Candidate scan reaches ordinary path | Core value regresses for all users | Single-entry union fast path and dedicated benchmark |
| Sorting during every trigger | Avoidable O(k log k) dispatch overhead | Sort/materialize once at registration |
| Guard predicates have side effects | Priority changes observable calls | Document ordered short-circuiting; test call order |
| Candidate group unbounded | Worst-case latency chosen by configuration | Expose group size in validation; characterize depth cost |

## Anti-Patterns to Avoid

### A Second Candidate Registration API

Do not add `add_transition_candidate()`. Priority is an attribute of an ordinary
transition, and every construction path should converge on `add_transition()`'s
canonical normalization/commit seam.

### A List for Every Transition

Do not make `_transitions[source][trigger]` always point to a list. The milestone
should charge candidate iteration/container overhead only to machines using
competition.

### Pre-evaluating or Indexing Arbitrary Guards

Do not try to recover O(1) by indexing callable guard outcomes. Guards can read
arbitrary live values and have user-defined behavior. Any such cache would be
stale or would merely move the same policy back outside the FSM.

### Falling Through After an Exception

Do not reinterpret a raised guard as `False`. It masks a defective higher-
priority safety rule and makes sync/async failure diagnostics misleading.

### Target-Only Candidate Identity

Do not merge candidates because they share a destination. Multiple priority
rules may intentionally reach the same state but differ in guard, history, or
declarative action.

### Diagnostics Reading `_transitions` Directly

Do not teach validators/renderers the union storage layout. Flatten it once in
the immutable core snapshot, then preserve the existing interpreted diagnostic
boundary.

## Sources

### Primary Codebase Evidence (HIGH)

- `src/fast_fsm/core.py` — `TransitionEntry`, `_PreparedTransition`, singular
  `_transitions`, atomic commit, sync/async trigger paths, declarative handlers,
  factories, clone, snapshots, serialization, and builder staging.
- `src/fast_fsm/_diagnostics.py` — scalar edge projection, sparse/dense
  adjacency, path generation, budgets, and edge-order identity.
- `src/fast_fsm/validation.py` — target-set determinism, counts, reachability,
  scoring, and report/export adapters.
- `src/fast_fsm/visualization.py` — one-snapshot Mermaid, PlantUML, JSON, dense
  adjacency validation, and Markdown transition tables.
- `tests/test_graph_invariants.py` — canonical endpoint identity, atomic graph
  versioning, snapshot order, clone lineage, and compound registration tests.
- `tests/test_performance_benchmarks.py` — two-lookup invariants, global-topology
  scaling checks, compiled throughput floors, history, and guarded-path gates.
- `tools/release_evidence.py` — installed compiled alternating-transition probe
  and 200,000 ops/sec release evidence contract.
- `.specify/memory/constitution.md` — current O(1) mandate and explicit ban on
  candidate iteration that this milestone must amend.
- `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` — fixed selection-
  before-lifecycle, failure, commit, observer, history, and cancellation rules.
- `.specify/decisions/ADR-006-bounded-diagnostics-safe-output.md` — immutable
  snapshot, diagnostic budget, stable order, and final-sink encoding rules.

### External Primary References (MEDIUM)

- [W3C SCXML 1.0](https://www.w3.org/TR/scxml/) — selects the first enabled
  transition in a deterministic order when multiple transitions match. Fast FSM
  should use explicit numeric priority instead of SCXML document order, but the
  ordered first-enabled model supports the proposed resolution semantics.
- [Python 3.10 `bisect`](https://docs.python.org/3.10/library/bisect.html) —
  documents that `insort()` is O(n) because list insertion dominates binary
  search, supporting an honest O(k) local-group registration bound.

## Open Decisions for Requirements

- Whether exact duplicate registration remains idempotent or every repeated
  priority is rejected. Idempotency best matches current graph-version behavior.
- Whether no-winner grouped failure adds public stage `selection` or reuses
  `guard`. A distinct stage is more truthful when candidates fail at mixed
  guard/permission boundaries.
- Whether direct declarative `handle_event*()` resolves multiple handlers by
  decorator priority or rejects without a machine target. Ordered direct
  resolution gives better semantic parity.
- Whether `to_dict()` always emits default priority or only emits priority for
  competing groups. Always emitting it gives the simplest stable schema.
- The exact public path-step shape for `generate_test_paths()` after adding
  priority. Keeping the old triple cannot distinguish parallel same-target
  candidates.
- Whether validation treats definitely shadowed candidates as an error or a
  warning. It should never claim definite shadowing when custom state policy
  could veto the earlier candidate.
- Practical candidate-count guidance and performance expectations must be set
  only after pure/native measurements at several winner depths.

---
*Architecture research for Fast FSM v0.4.0 Priority-Aware Guarded Transitions.*
