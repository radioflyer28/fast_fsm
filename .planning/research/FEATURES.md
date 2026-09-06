# Feature Landscape: Priority-Aware Guarded Transitions

**Project:** Fast FSM v0.4.0
**Domain:** High-performance Python finite-state-machine transition selection
**Researched:** 2026-09-06
**Overall confidence:** HIGH for the project contract; MEDIUM for ecosystem comparisons

## Executive Recommendation

Fast FSM should treat every `(source state, trigger)` as a finite candidate
group. A group normally contains one transition and keeps the existing direct
lookup fast path. When a group contains competing guarded transitions, the
machine evaluates them sequentially from lowest numeric `priority` to highest
and selects the first candidate whose complete pre-transition eligibility
checks pass.

The public surface should remain one coherent API:

```python
fsm.add_transition(
    "telemetry_tick",
    "Mission",
    "EmergencyLanding",
    condition=FuncCondition(critical_fault_present),
    priority=10,
)
fsm.add_transition(
    "telemetry_tick",
    "Mission",
    "ReturnHome",
    condition=FuncCondition(link_lost),
    priority=20,
)
fsm.add_transition(
    "telemetry_tick",
    "Mission",
    "ReturnHome",
    condition=FuncCondition(battery_critical),
    priority=30,
)
```

No external dispatcher should reproduce state eligibility, guards, or
priority. An integration may normalize and retain raw facts—for example,
`heartbeat_older_than(5)`—but one call to `trigger("telemetry_tick", ...)`
must let the FSM choose the transition.

This is a deliberate evolution of the existing duplicate-registration
semantics. Fast FSM is not yet used in production, so v0.4.0 should prefer an
explicit, deterministic model over preserving silent replacement of an
existing `(source, trigger)` edge.

## Table Stakes

Features users need for the capability to be coherent rather than merely
syntactic.

| Feature | Why Expected | Complexity | Committed Behavior |
|---------|--------------|------------|--------------------|
| Multiple candidates per `(source, trigger)` | One event must be able to route to different targets without external `if` chains | High | Ordinary transitions become members of one finite candidate group |
| Explicit numeric priority | Registration order is too fragile for safety or business policy | Medium | Lower integer wins; gaps and negative values are allowed; `bool` and non-integers are rejected |
| First fully eligible candidate wins | This is the established guarded-choice model in SCXML, XState, and python-statemachine | High | Evaluate in ascending priority and stop at the first candidate whose guard and state permission pass |
| Deterministic tie handling | Equal priorities otherwise reintroduce implicit ordering | Low | Reject equal priorities within the same candidate group atomically |
| Stable no-match outcome | A valid trigger may have no enabled candidate for the supplied facts | Medium | Return a failed, uncommitted `TransitionResult`; preserve the source state and run no transition lifecycle callbacks |
| Sync/async parity | An async guard must not change selection semantics | High | Same order and result semantics; async guards are awaited sequentially |
| Single-candidate fast path | Existing common use must retain Fast FSM's value proposition | High | Direct lookup remains; no per-trigger sorting or candidate allocation for a singleton |
| Tooling truthfulness | Candidate groups are topology, not hidden dispatch detail | High | Clone, snapshots, validation, exports, diagrams, and diagnostics expose every candidate and its priority |
| Candidate observability | Same trigger and target can have multiple guarded routes | Medium | Results, history, and trace metadata identify the selected or faulting priority without exposing payload values |
| Construction parity | Builder and configuration APIs must not collapse candidates | High | `FSMBuilder`, batch addition, declarative integration, and `from_dict()` preserve priority and candidate identity |

## Detailed Behavioral Contract

### 1. Registration Semantics

`StateMachine.add_transition()` and `FSMBuilder.add_transition()` gain a
keyword-only `priority: int | None = None` parameter.

- Lower numeric values have higher precedence: `10` is evaluated before `20`.
- Priorities need not be contiguous. Leaving gaps supports later insertion
  without renumbering policy.
- `bool` must be rejected even though it subclasses `int`; `True` and `False`
  are not meaningful policy labels.
- Priority is scoped to one `(canonical source state, trigger)` group. Reusing
  `10` for another source or another trigger is valid.
- A singleton transition may omit priority. As soon as a second candidate is
  registered, every candidate in that group must have an explicit, unique
  priority. This prevents an implicit default from accidentally outranking an
  explicitly designed policy.
- Re-registering the exact same target, condition identity, and priority is an
  idempotent no-op. Registering a different candidate at an occupied priority
  raises `ValueError`.
- A `from_state=[...]` registration applies the same candidate and priority to
  each source's independent group. Validation is atomic: a collision for any
  source rejects the whole operation and leaves graph version and topology
  unchanged.
- Multiple candidates may lead to the same destination. Their different
  guards can represent distinct reasons or escalation thresholds.
- An unconditional candidate is permitted as an explicit fallback. It should
  carry the lowest precedence in its group; lower-precedence candidates after
  it are unreachable and must be reported by validation.

The existing `add_transitions()` API should accept a fifth tuple item for
priority while retaining its three- and four-item forms:

```python
fsm.add_transitions([
    ("tick", "Mission", "EmergencyLanding", critical_fault, 10),
    ("tick", "Mission", "ReturnHome", link_lost, 20),
    ("tick", "Mission", "ReturnHome", low_battery, 30),
])
```

Bidirectional and emergency helpers must forward per-edge priority rather than
silently replacing an existing candidate. Exact parameter spelling can follow
their current per-direction convention (`priority1` / `priority2` for the
bidirectional helper).

### 2. Candidate Selection

For one trigger attempt, selection follows this finite sequence:

```text
O(1) lookup of current-state + trigger group
    → candidates already ordered by numeric priority
        → transition condition / unless guard
        → matching declarative guard, if any
        → source State.can_transition(...)
    → first candidate passing every eligibility check is selected
    → execute exactly one existing transition lifecycle
```

Guard rejection is fallthrough, not failure of the whole group. If priority
`10` returns false, priority `20` is evaluated. State permission rejection is
also candidate-local and allows evaluation of the next candidate; otherwise
the machine would select an edge that it already knows it cannot take.

Once a candidate is selected, selection is finished. A later before/exit/enter
callback failure, listener failure, declarative handler failure, or post-commit
failure must not try a lower-priority candidate. Falling through after side
effects begin would violate the established atomic lifecycle contract.

Candidates receive the same positional arguments and one equivalently
sanitized keyword context. Guards must be documented as side-effect-free,
because a rejected guard may run even though another candidate ultimately
commits.

### 3. Guard Exceptions and Async Cancellation

A guard exception is not equivalent to `False`.

- Stop candidate selection immediately.
- Return the existing guard-stage failure with the original `cause` and the
  faulting candidate's priority.
- Do not evaluate lower-priority candidates; doing so would silently mask a
  defect in a higher-priority safety or business rule.
- For `AsyncStateMachine`, cancellation propagates according to the existing
  cancellation contract and never resumes selection at another candidate.
- Async candidates are evaluated sequentially. Parallel guard execution is
  deferred because it weakens deterministic ordering and may create observable
  side-effect races in user guards.

### 4. No Candidate Matches

When a `(source, trigger)` group exists but no candidate is enabled:

- `trigger()` returns `TransitionResult(success=False, committed=False)`.
- `from_state` and `trigger` are populated; `to_state` and selected priority
  are `None` because no edge was selected.
- If every candidate was rejected by transition/declarative guards, `stage` is
  `"guard"`. If at least one candidate passed its guards but every such
  candidate was rejected by `State.can_transition`, `stage` is
  `"state-permission"`.
- The error message identifies the candidate group and number evaluated, but
  does not include telemetry values, guard return values, or arbitrary object
  representations.
- The source state, history, entry/exit callbacks, transition callbacks, and
  listeners remain untouched except for the existing single failure-observer
  notification.
- `can_trigger()` / `can_trigger_async()` return `True` iff at least one
  candidate is fully eligible under the same selection rules.

A missing `(source, trigger)` remains the distinct existing resolution-stage
failure. This distinction matters for diagnostics: “event is unknown here” is
different from “event is modeled here, but current facts enable no route.”

### 5. Runtime Observability

Priority must remain observable after registration without changing callback
argument conventions.

- Add an optional, comparison-neutral priority field to `TransitionResult` so
  successful selection and guard faults can identify the candidate.
- Add the selected priority to `TransitionRecord`; otherwise two candidates
  with identical source, trigger, and destination are indistinguishable in
  audit history.
- Trace output may include numeric priority and candidate counts. It must
  preserve v0.3.0's metadata-only redaction and never log raw trigger payloads.
- Failure observers still fire once for the overall trigger attempt, not once
  for every rejected candidate.
- Transition callbacks and state callbacks keep their existing signatures.
  Injecting priority into user kwargs would risk collisions with application
  payloads and is not recommended.

### 6. Introspection, Export, and Reconstruction

All topology consumers must see candidates rather than a lossy synthetic edge.

- The immutable graph snapshot contains one row per candidate with priority.
- `get_reachable_states()` returns every distinct candidate destination.
- `transition_exists(trigger, from_state, to_state)` returns true when any
  candidate matches; it does not imply that the candidate's guard currently
  passes.
- `get_available_triggers()` and `triggers` continue to deduplicate trigger
  names.
- `clone()` copies complete candidate groups while sharing condition identities
  according to the existing shallow-clone contract.
- `to_dict()` writes each candidate as a separate transition entry and includes
  priority. `from_dict()` accepts that field and reconstructs the group.
- Because trigger-only `conditions={"tick": guard}` cannot distinguish
  candidates, `from_dict()` needs a stable candidate-level condition key in
  addition to its legacy trigger-key fallback. A practical Python-side key is
  `(from_state, trigger, priority)`. Callable serialization itself remains out
  of scope.
- JSON analysis, Mermaid, and PlantUML label parallel edges with priority so a
  reader can recover evaluation order from the output.

### 7. Declarative-State Behavior

Declarative dispatch must execute exactly one handler associated with the
selected candidate. Discovery may no longer collapse all methods sharing a
trigger into one `_handlers[trigger]` value.

The selected candidate's canonical target and priority must be sufficient to
resolve its handler. If the same trigger, source, and target has multiple
candidate handlers, declarative metadata needs priority to disambiguate them.
The implementation should not require authors to declare priority twice: one
registration remains authoritative, and declarative metadata either matches
that candidate or fails validation during construction.

Direct `DeclarativeState.handle_event()` compatibility must be defined rather
than allowed to depend on attribute discovery order. At minimum it must apply
the same priority selection when enough topology metadata is present; otherwise
it should reject an ambiguous direct call explicitly.

### 8. Validation and Diagnostics

Registration enforces facts that can be proven locally:

- priority type is valid;
- candidate-group priorities are explicit and unique;
- canonical source/target invariants still hold;
- compound/batch registration remains atomic.

Design-time validation reports structural policy mistakes:

- an unconditional candidate precedes another candidate;
- exported or declarative candidate metadata is ambiguous or missing;
- a candidate group cannot be reconstructed losslessly;
- sync machines contain async requirements anywhere in the group.

Overlapping guarded predicates are not an error. Priority exists precisely to
make overlap deterministic. The validator should not claim to prove arbitrary
user callables mutually exclusive.

### 9. Complexity and Performance Contract

Priority changes the honest complexity statement:

- group lookup remains O(1);
- a singleton transition remains O(1) and must retain the allocation-minimal
  fast path;
- a competing group takes O(k) guard checks in the worst case, where `k` is
  the finite number of candidates for that `(source, trigger)`;
- ordering is prepared at registration/build time—never sorted on each
  trigger attempt;
- candidate registration may be O(k) if it publishes a new immutable ordered
  group; this bounded configuration-time cost is preferable to charging every
  dispatch.

Documentation and benchmarks must stop describing a guarded candidate group as
strict O(1) end-to-end work. The compiled normal-transition throughput floor of
200,000 operations/second remains mandatory, and benchmarks should report
singleton, first-match, middle-match, last-match, and no-match groups.

## Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Explicit priority rather than declaration order | Reordering setup code cannot silently change safety policy | Medium | Ecosystem tools often use document/declaration order; Fast FSM can make precedence reviewable as data |
| Priority-aware compiled fast path | Deterministic routing without surrendering the library's performance identity | High | Preserve a direct singleton representation and pre-order competing groups |
| Truthful candidate topology | Diagrams, JSON, history, and validators all describe the same rules the runtime uses | High | Prevents the common split between runtime choice and rendered graph |
| Guard-fault fail-closed behavior | A broken high-priority rule cannot be mistaken for a false predicate | Medium | Particularly important for safety-oriented examples such as drone failsafes |
| Stable policy under incremental registration | Explicit gaps permit later insertion without setup-order coupling | Low | `10, 20, 30` is clearer and easier to evolve than implicit list position |

## Anti-Features and Deferrals

| Anti-Feature / Deferral | Why Avoid in v0.4.0 | What to Do Instead |
|-------------------------|---------------------|-------------------|
| A second `add_transition_candidate()` API | Splits one domain concept across redundant registration surfaces | Evolve `add_transition(..., priority=...)` |
| Registration order as hidden priority | Refactors and config generation can silently alter behavior | Require explicit unique priorities for competing groups |
| Equal-priority tie-breaking | Reintroduces ambiguity through insertion order, target name, or condition name | Reject ties atomically |
| Dynamic/callable priorities | Makes topology and diagrams depend on runtime payload and complicates finiteness | Keep priority a static registered integer |
| “Best score” evaluation of all guards | Guards return eligibility, not comparable scores; evaluating all increases cost and side effects | Stop at the first fully eligible candidate |
| Fallback after lifecycle failure | May execute multiple callback chains and external commands for one event | Fall through only during eligibility checks |
| Parallel async guard evaluation | Produces unnecessary work and weakens deterministic fault/cancellation semantics | Await candidates sequentially |
| Automatic telemetry-to-event classification | Moves transition logic back outside the machine | Fact providers may derive measurements; guards own transition eligibility |
| Priority mutation/removal/reordering API | Expands concurrency, graph-version, and identity semantics substantially | Rebuild topology; consider explicit mutation APIs in a later milestone |
| Arbitrary callable serialization | Python callables cannot be safely or portably encoded in JSON | Serialize priority/topology and reattach guards by stable candidate key |
| Hierarchical/statechart conflict rules | Descendant-vs-ancestor and parallel-region resolution are a separate model expansion | Limit v0.4.0 to flat Fast FSM source-state candidate groups |
| Eventless/automatic transitions | Introduces scheduling and possible livelock concerns unrelated to candidate priority | Continue requiring caller-driven triggers |

## Feature Dependencies

```text
[Candidate identity + explicit priority validation]
    └──enables──> [Ordered sync selection]
                     └──parity──> [Ordered async selection]
                     └──feeds──> [Transition lifecycle + observability]

[Candidate-aware graph snapshot]
    ├──enables──> [Clone and topology queries]
    ├──enables──> [to_dict/from_dict reconstruction]
    ├──enables──> [Validation and diagnostics]
    └──enables──> [Mermaid/PlantUML/JSON truthfulness]

[Core selection semantics]
    └──enables──> [Builder + declarative parity]
                     └──enables──> [Drone telemetry_tick example]

[Correctness contract]
    └──measured by──> [Pure/compiled benchmarks and conformance tests]
```

### Recommended Phase Ordering

1. **Candidate model and registration contract** — establish identity,
   priority validation, atomic mutation, graph versioning, and singleton
   compatibility.
2. **Sync/async selection and lifecycle integration** — implement the first
   fully eligible rule, no-match diagnostics, fail-closed guard faults, and
   result/history observability.
3. **Construction and declarative parity** — update builder, batch helpers,
   configuration reconstruction, clone, and declarative handler resolution.
4. **Graph consumers and validation** — update snapshots, topology queries,
   validators, JSON, Mermaid, and PlantUML from one canonical candidate model.
5. **Performance, documentation, and example migration** — benchmark singleton
   and candidate groups, update complexity claims, and reduce the drone loop to
   one `telemetry_tick` trigger.

## Acceptance Scenarios

| Scenario | Expected Outcome |
|----------|------------------|
| One ordinary unguarded transition without priority | Existing successful behavior and singleton fast path |
| Three candidates; priorities `10`, `20`, `30`; all guards true | Priority `10` commits; lower candidates are not evaluated |
| Priority `10` false; priority `20` true | Priority `20` commits; priority `30` is not evaluated |
| Priority `10` guard raises | Overall guard-stage failure with cause and priority `10`; no lower candidate runs |
| All guards false | Uncommitted guard-stage failure; current state unchanged; one failure notification |
| Guard passes but state permission rejects; lower candidate passes | Lower candidate is selected and commits |
| Two candidates register priority `10` in same group | Atomic `ValueError`; topology and graph version unchanged |
| Singleton without priority later receives a competitor | Registration fails until the entire group uses explicit priorities |
| An unconditional fallback has the greatest numeric priority | It runs only when all higher-precedence guards reject |
| Unconditional candidate precedes another | Validation reports the later candidate as unreachable |
| Same source, trigger, and destination with two guards | Both remain distinct; selected priority appears in result/history |
| Async guard is cancelled | Selection stops; state and history follow existing cancellation boundary |
| Clone/export/diagram of a candidate group | Every candidate and priority remains visible and deterministic |
| Drone telemetry contains critical fault, stale heartbeat, and low battery | One `telemetry_tick` chooses critical-fault emergency landing without controller arbitration |

## Migration Implications

Most users with one transition per `(source, trigger)` require no source
changes. The intentional break affects code that relied on a later
`add_transition()` call silently replacing an earlier edge.

Migration guidance should say:

1. If both edges express real alternatives, retain both and assign unique
   explicit priorities and guards.
2. If the later edge was meant as configuration mutation, construct the
   desired final machine directly; v0.4.0 does not add an implicit replace API.
3. If multiple alternatives were dispatched by an application `if` chain,
   replace that chain with one trigger and move predicates into transition
   guards.
4. If topology is loaded from dictionaries, include priority and use
   candidate-level guard keys where one trigger has multiple conditions.

The changelog should call out the duplicate-registration change prominently,
even though the project has explicitly accepted pre-production API evolution.

## MVP Recommendation

Prioritize:

1. Candidate groups through the existing `add_transition()` API with explicit,
   unique integer priorities.
2. Identical sync/async first-eligible selection, fail-closed guard exceptions,
   and precise no-match results.
3. Candidate-aware graph snapshots plus builder, declarative, export,
   validation, history, visualization, and clone parity.
4. Performance evidence proving the singleton fast path remains viable and
   documenting O(k) candidate selection honestly.
5. A drone example in which the controller records telemetry facts and calls
   `trigger("telemetry_tick")` once; the FSM owns all failsafe routing.

Defer dynamic priorities, mutation/removal APIs, parallel guard evaluation,
callable serialization, hierarchy/parallel-state conflict rules, and automatic
event scheduling.

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Existing Fast FSM behavior | HIGH | Direct inspection of `core.py`, current docs, examples, archived requirements, and v0.3.0 lifecycle contracts |
| Explicit priority contract | HIGH | Directly established in milestone discussion and `PROJECT.md`; tie rejection and one-API direction were user decisions |
| First-passing semantics | HIGH | W3C SCXML, XState, and python-statemachine independently use deterministic first-enabled selection |
| No-match recommendation | HIGH | Extends Fast FSM's existing staged `TransitionResult` contract without exceptions or state mutation |
| Guard-exception recommendation | HIGH | Preserves v0.3.0 truthful failure/cause behavior and avoids masking higher-priority defects |
| Declarative/configuration API details | MEDIUM | Required for parity, but exact stable candidate-key representation needs implementation-phase design validation |
| Performance shape | HIGH | O(k) guard evaluation is intrinsic; exact throughput and storage representation require benchmarks |

## Sources

External findings were routed through the GSD research seam and assigned
MEDIUM confidence after cross-checking official sources:

- [W3C SCXML 1.0 Recommendation](https://www.w3.org/TR/scxml/) — selects the
  first enabled transition in document order and defines deterministic conflict
  resolution.
- [XState guards](https://stately.ai/docs/guards) and
  [transition selection](https://stately.ai/docs/transitions) — ordered guarded
  alternatives, first match, optional unconditional fallback, and unchanged
  state when no transition is enabled.
- [python-statemachine conditions](https://python-statemachine.readthedocs.io/en/stable/guards.html)
  — multiple transitions for one event, first passing guard, configurable
  no-match handling, and side-effect-free condition guidance.
- [Stateless guard clauses](https://github.com/dotnet-state-machine/stateless/blob/dev/README.md#guard-clauses)
  — contrasting mutually-exclusive-guard model and explicit unhandled-trigger
  behavior.
- [Fast FSM project definition](../PROJECT.md),
  [v0.3.0 requirements](../REQUIREMENTS.md),
  [`core.py`](../../src/fast_fsm/core.py), and
  [drone failsafe example](../../examples/drone_failsafes.py) — current API,
  lifecycle, topology, diagnostics, and example constraints.

---
*Feature research for Fast FSM v0.4.0 Priority-Aware Guarded Transitions*
