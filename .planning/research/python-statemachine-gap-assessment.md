# Fast FSM vs. `python-statemachine`: Gap Assessment

**Captured:** 2026-09-11  
**Comparison target:** Fast FSM after v0.4.0 and condition-interface quick task
260911-ra8; `python-statemachine` 3.2 documentation and repository  
**Purpose:** Identify semantics, architecture patterns, and usability improvements
worth considering without compromising Fast FSM's defining performance advantage.

## Executive conclusion

Fast FSM should borrow selected semantics from `python-statemachine`, but it
should not copy its general-purpose statechart runtime.

The libraries now occupy different design points:

- Fast FSM is a flat, deterministic, performance-oriented finite state machine
  with direct dictionary lookup, a direct singleton-transition path, and finite
  priority candidate groups.
- `python-statemachine` 3.2 is an SCXML-style statechart engine with compound and
  parallel configurations, history, eventless transitions, internal and
  external queues, delayed events, invocation, and callback dependency
  injection. Its documentation explicitly describes statechart configurations
  and a run-to-completion macrostep/microstep engine.

Sources:

- [`python-statemachine` core concepts](https://python-statemachine.readthedocs.io/en/latest/concepts.html)
- [`python-statemachine` processing model](https://python-statemachine.readthedocs.io/en/latest/processing_model.html)
- [`python-statemachine` transition semantics](https://python-statemachine.readthedocs.io/en/latest/transitions.html)
- [`python-statemachine` behavioral modes](https://python-statemachine.readthedocs.io/en/latest/behaviour.html)

The relevant question is therefore not "which features are missing?" It is
"which additions deepen Fast FSM's existing model while preserving the hot
path, and which additions would turn it into a different kind of engine?"

## Governing constraint: speed is product identity

Fast FSM exists to be significantly faster and more memory-efficient than
`python-statemachine` and similar general-purpose libraries. Every future
feature must preserve the following constraints:

1. The unused-feature cost must be effectively zero. An ordinary unguarded
   singleton transition must retain its direct O(1) lookup and dispatch path.
2. Registration-time normalization is preferable to dispatch-time work.
   Validation, signature inspection, ordering, and adapter resolution should
   happen before the machine begins processing events.
3. The hot path should avoid reflection, topology scans, hidden coroutine
   selection, and unconditional context-object allocation.
4. Optional features should pay their own local cost rather than taxing every
   transition.
5. New runtime semantics must be measured in both pure Python and freshly
   installed compiled artifacts.
6. Exact timings remain environment-labelled observations. The durable product
   contract is the compiled singleton throughput floor plus complexity and
   semantic invariants.

## Recommended additions

### 1. Explicit final states and termination

**Value:** High  
**Fit:** High  
**Likely scope:** One focused phase plus integration and proof

Fast FSM currently treats a state with no outgoing edges as terminal for some
diagnostic purposes. That is a graph observation, not an explicit domain
invariant. A final-state flag would support:

- construction-time rejection of outgoing transitions from final states;
- an unambiguous `is_terminated` query;
- clearer controller loops and examples;
- truthful serialization, visualization, validation, and clone behavior;
- optional completion notification without inferring intent from topology.

The dispatch cost can be limited to the transition that enters a final state,
or termination can be derived from the already-current state. Ordinary
non-final dispatch need not scan or allocate.

`python-statemachine` models initial and final states explicitly and exposes
termination as part of its statechart runtime. See its
[state documentation](https://python-statemachine.readthedocs.io/en/latest/states.html).

### 2. Explicit internal versus external self-transitions

**Value:** High  
**Fit:** High  
**Likely scope:** One semantic-contract phase plus parity work

An external self-transition exits and re-enters the same state. An internal
transition executes its transition action without firing state exit and entry
actions. This distinction is useful for common operations such as updating a
cart, refreshing telemetry, or recording progress without restarting
state-owned behavior.

This should be immutable transition metadata normalized during registration.
Execution needs only a predictable branch at the lifecycle seam. It should not
be a machine-wide behavioral flag because the intent belongs to each
transition. `python-statemachine` documents the same distinction explicitly in
its [transition model](https://python-statemachine.readthedocs.io/en/latest/transitions.html#self-transitions-and-internal-transitions).

### 3. Expected domain rejection distinct from guard failure

**Value:** Medium-high  
**Fit:** High if kept small  
**Likely scope:** Include with transition semantics

Three outcomes should remain distinguishable:

1. A guard returns false: this candidate is ineligible, so priority resolution
   may continue.
2. Domain validation intentionally rejects the event: return an expected,
   structured rejection reason to the caller.
3. A guard or callback raises an unexpected exception: preserve the existing
   stage-aware execution failure contract.

`python-statemachine` represents the second case with validators that raise
instead of silently skipping a transition. Fast FSM should borrow the semantic
distinction without importing another callback family or reflection-heavy
resolution system. A small `TransitionRejected` exception with a stable,
redacted reason/code is likely sufficient.

The exception path does not affect successful dispatch throughput. Guard
selection must continue to treat only a false guard as candidate fallthrough.

### 4. Bounded deferred events after commit

**Value:** High for workflows  
**Fit:** Medium; architectural  
**Likely scope:** Separate later milestone, not an incidental addition

Fast FSM currently rejects callback reentry. That safe rule prevents deadlocks
and ambiguous nested lifecycle execution, but it also means a committed state
callback cannot request a follow-up event through the machine.

A bounded, opt-in deferred queue could permit a callback to enqueue an event
that runs only after the current transition fully completes. This would retain
serialized ownership and remove some controller boilerplate. It should begin
with one queue and one clear post-commit rule, not the complete SCXML
macrostep/microstep model.

Required safeguards include:

- disabled-by-default or lazily allocated storage;
- finite queue depth and finite drain limits;
- deterministic FIFO ordering;
- explicit exhaustion/cycle failure;
- sync/async ownership and cancellation rules;
- no change to direct callback-reentry rejection;
- independent feature-enabled performance evidence.

`python-statemachine` maintains separate internal and external FIFO queues and
stabilizes eventless transitions within macrosteps. That design is instructive,
but adopting it wholesale would change Fast FSM's engine category and impose
complexity unrelated to ordinary flat dispatch. See its
[run-to-completion processing model](https://python-statemachine.readthedocs.io/en/latest/processing_model.html#event-queues).

### 5. Lazily materialized event or transition context

**Value:** Medium  
**Fit:** Medium-high if allocation is avoidable  
**Likely scope:** Design together with deferred events

An immutable context can give lifecycle callbacks a coherent view of the event,
source, selected transition, target, priority, and timing. It may also reduce
signature drift among guards, listeners, and actions.

Fast FSM should not create such an object for every ordinary trigger. Prefer:

- raw existing callback arguments on the fastest path;
- registration-time callback adaptation;
- lazy context creation only when a registered consumer asks for it;
- one shared context instance per transition attempt when materialized.

Avoid `python-statemachine`'s broad signature-based dependency injection and
naming conventions. They improve convenience but add reflection, hidden
binding rules, and audit complexity.

### 6. A narrow external state-store adapter

**Value:** Medium  
**Fit:** Medium  
**Likely scope:** Future adapter milestone or extension

Persisting current state directly on a domain model is convenient for ORM and
workflow applications. A useful seam would be a minimal state store with clear
read, commit, and failure semantics. It should be considered only when there
are at least two real adapters—for example, the existing in-memory behavior and
an attribute-backed adapter.

Do not make arbitrary model methods implicit listeners or bind domain behavior
by naming convention. The controller-owned pattern used by the drone example
remains the clearer default.

### 7. Progressive same-domain tutorial

**Value:** High  
**Fit:** Very high  
**Likely scope:** Documentation phase attached to the relevant milestone

The examples are now individually focused, which is useful. A complementary
learning path should evolve one domain—preferably the drone controller—through:

1. states and direct transitions;
2. callbacks and aircraft commands;
3. guards and boolean composition;
4. priority candidates;
5. entry-relative timing;
6. async telemetry or persistence;
7. final states and internal transitions when available.

This improves usability without adding runtime machinery and makes the
performance-oriented design easier to understand progressively.

## Features not recommended for the Fast FSM core

### Hierarchical, parallel, and history statecharts

These are legitimate features, but they replace one active state with an active
configuration and replace one selected edge with sets of microsteps. They
should not be added incrementally to `StateMachine`. If demand becomes strong,
they belong in a separate `fast_fsm.statecharts` module or separate package
with its own performance contract.

### Eventless transitions

Automatic stabilization requires repeated transition discovery, cycle limits,
and well-defined interactions with queues and callbacks. Adding it alone would
invite unbounded work and weaken Fast FSM's explicit event model.

### Delayed-event scheduling and state-owned background invocation

Fast FSM now owns transition eligibility timing through `after=` and `within=`.
It should not also become a scheduler, thread manager, or task supervisor.
Controllers and injected scheduling adapters are more composable owners of
time and work.

### Automatic sync/async engine selection

Fast FSM's separate `StateMachine` and `AsyncStateMachine` types make ownership,
return types, and event-loop requirements explicit. A method that sometimes
returns a value and sometimes an awaitable would weaken usability despite
appearing convenient. Builder-time async detection is the appropriate limit.

### Reflection-heavy callback injection and naming conventions

Fast FSM should keep callback interfaces explicit. Registration-time adapters
may improve ergonomics, but dispatch-time signature inspection and magic method
discovery conflict with mypyc compatibility, auditability, and predictable
cost.

### Converting arbitrary callback exceptions into domain events

Unexpected programmer errors should remain visible through the existing
stage-aware `TransitionResult` and failure-observer contracts. Applications can
model explicit fault events themselves. Silently converting implementation
errors into events can hide defects.

### Executable SCXML/YAML import in the core

Fast FSM's current topology serialization deliberately represents callable
guards with references rather than executing serialized code. A general
executable format introduces a substantial trust boundary and belongs in an
optional, separately audited adapter if ever required.

## Condition-system implications

The condition-interface quick task already established the appropriate focused
vocabulary: `Condition`, `FuncCondition`, `AsyncCondition`, `AndCondition`,
`OrCondition`, and `NotCondition`, with application policy implemented in small
domain conditions.

The comparison does not justify restoring a broad built-in predicate catalogue:

- An `In(...)` condition is meaningful for hierarchical and parallel
  configurations, but is mostly redundant inside a flat machine whose source
  transition already declares the active state.
- Cross-machine state checks can remain explicit application `FuncCondition`
  logic unless repeated real use demonstrates a stable adapter seam.
- Validator semantics merit consideration, but as one expected-rejection
  mechanism rather than another compositional condition hierarchy.
- Boolean composition should continue to compile or normalize at construction
  time and short-circuit locally during selection.

## Architecture implications

`core.py` is intentionally one mypyc compilation unit, so splitting it into
public modules is currently out of scope. Nevertheless, future implementation
should preserve conceptual internal seams within that unit:

- immutable graph and transition registration;
- candidate resolution;
- lifecycle execution and commit;
- ownership and deferred-event policy;
- public machine facade.

These should remain internal seams. New public classes are justified only when
they provide real substitution or composition leverage.

The validation interface also deserves periodic depth review. Fast FSM exposes
several validator/report helpers. Future work should prefer one stable analysis
result with small rendering adapters over continuing to add shallow aliases.
That is a maintainability observation, not a requirement imported from
`python-statemachine`.

## Benchmark and comparison gap

The benchmark dependency is declared as `python-statemachine>=2.5.0`, but the
current lock resolves 2.5.0 while the current upstream documentation describes
3.2.0. Future comparative evidence should label and test both:

- 2.5.0 as the historical comparison baseline;
- current 3.2.x as the contemporary competitor and statechart reference.

Comparative benchmarks should remain manual or scheduled rather than making
the full competitor suite a required CI job. Each Fast FSM feature should have:

1. an untouched singleton-dispatch measurement;
2. a feature-enabled local-cost measurement;
3. pure/compiled semantic parity;
4. a regression test proving unrelated graph topology is not scanned.

The purpose is not to win every feature-equivalent benchmark. It is to prove
that Fast FSM remains materially faster for the flat deterministic FSM use case
it deliberately serves.

## Proposed roadmap shape

### Recommended next milestone: explicit flat-FSM semantics

A coherent next milestone could contain:

1. **Contract and benchmark baselines** — compare locked 2.5.0 and current
   3.2.x, freeze untouched and feature-enabled measurement shapes, and define
   zero-cost-when-unused acceptance criteria.
2. **Final-state semantics** — explicit construction, termination query,
   validation, lifecycle behavior, and illegal outgoing-edge handling.
3. **Internal-transition semantics** — per-transition mode, external
   self-transition behavior, sync/async parity, and lifecycle proof.
4. **Expected domain rejection** — structured rejection distinct from false
   guards and unexpected failures, without a new condition family.
5. **Construction and tooling parity** — builder, declarative form,
   serialization, clone, diagnostics, figures, and history.
6. **Installed-artifact and usability proof** — pure/compiled parity,
   performance gates, and the progressive drone tutorial.

This scope deepens the existing flat machine and has a defensible user theme:
make workflow completion, in-state events, and domain rejection explicit while
preserving the direct fast path.

### Separate later milestone: bounded deferred events

Deferred events should not be smuggled into the semantic milestone. They alter
ownership and lifecycle processing enough to deserve their own research,
threat model, limits, sync/async contract, and performance proof.

### Seeds or backlog rather than active scope

- Lazy transition context should travel with deferred-event design.
- External state-store adapters should wait for concrete adapter use cases.
- A hierarchical/parallel statechart engine should remain a separate product
  decision, not a presumed Fast FSM roadmap item.
- Validation-interface consolidation is maintainability work and should be
  evaluated against actual user confusion and module depth before promotion.

## Decision recommendation

Use `$gsd-new-milestone` for the explicit flat-FSM semantics milestone because
v0.4.0 is closed and `.planning/STATE.md` is awaiting the next milestone.

Use `$gsd-capture --seed` for bounded deferred events so the idea resurfaces
when a future milestone explicitly targets callback-driven workflows,
run-to-completion behavior, or reentry ergonomics.

Do not use `$gsd-phase` to append work to v0.4.0, and do not promote every
comparison gap into the active roadmap. The statechart-class features are
deliberate non-goals unless the product's core value changes.

