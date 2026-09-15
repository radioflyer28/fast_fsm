# Feature Research

**Project:** Fast FSM v0.5.0 Explicit Flat-FSM Semantics
**Domain:** High-performance Python flat finite-state machines
**Researched:** 2026-09-15
**Confidence:** HIGH for recommendations grounded in existing Fast FSM contracts; MEDIUM for current ecosystem comparisons

## Executive Recommendation

Fast FSM v0.5.0 should add four tightly connected semantics: an immutable
`final` marker on states, an O(1) `is_terminated` query, per-transition
`internal` metadata for self-transitions, and a structured expected-rejection
outcome. These features should make domain intent explicit without changing the
engine category: one current state, one caller-supplied event, one selected
transition, and no hidden stabilization or queue.

The lifecycle contract should remain the organizing principle. Entering a final
state commits and makes `is_terminated` true before destination-entry callbacks.
An external self-transition follows the complete existing exit/commit/entry
lifecycle and resets entry-relative timing. An internal self-transition still
represents one selected and committed transition, but skips every state exit and
entry surface and preserves the original state-entry timestamp. Both modes run
transition-level observation and action surfaces.

Expected rejection must form a third outcome beside guard ineligibility and
unexpected failure. A false guard remains candidate-local and permits priority
fallthrough. A deliberate `TransitionRejected` signal aborts selection and
returns a structured, uncommitted rejection. Any other exception remains an
unexpected stage-aware failure with its original `cause`. Do not add a second
validator callback family; recognize one narrow signal at the existing
eligibility seams.

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Observable Behavior | Confidence |
|---------|--------------|------------|---------------------|------------|
| Explicit final-state declaration | Completion is domain intent, not the accidental absence of outgoing edges | MEDIUM | `State("done", final=True)` exposes immutable final metadata; a non-final sink is not terminated | HIGH |
| Constant-time termination query | Controller loops need a clear completion check | LOW | `machine.is_terminated` is `machine.current_state.final`; it performs no topology scan and is not a sticky historical latch | HIGH |
| No ordinary outgoing transitions from final states | A final state that still accepts modeled events is not final | MEDIUM | Registration, batches, builders, declarative construction, and deserialization reject every final-source edge atomically, including internal self-transitions | MEDIUM |
| Final-entry commit semantics | Completion must agree with the existing no-rollback boundary | MEDIUM | On transition commit into a final state, `is_terminated` becomes true before entry callbacks; a later callback failure remains committed and terminated | HIGH |
| External self-transition as compatibility default | Existing same-state transitions already execute exit and entry lifecycle | MEDIUM | Omitting `internal` keeps full before/exit/commit/enter/action/after behavior and resets the state-entry timestamp | HIGH |
| Explicit internal self-transition | In-state events often update data without restarting state-owned behavior | HIGH | `internal=True` is valid only when canonical source and target are the same state; state exit/entry hooks, callbacks, and state listeners do not run | MEDIUM |
| Internal transition commit and timing rules | Skipping lifecycle cannot make history, results, or timing ambiguous | HIGH | Successful internal transitions return `committed=True`, can append history, keep the same current-state object, and do not reset entry-relative timing | HIGH |
| Three-way selection outcome | Callers must distinguish “not eligible,” “valid event rejected,” and “implementation failed” | HIGH | False guard: fall through. `TransitionRejected`: stop with structured rejection and no cause. Any other exception: stop with stage and cause | HIGH |
| Priority interaction | v0.4.0 candidate ordering must stay deterministic | HIGH | Only ordinary false/timing/state-permission ineligibility continues to a lower priority; expected rejection, unexpected exception, and cancellation abort the group | HIGH |
| Sync/async semantic parity | Awaiting user code must not change the meaning of final, internal, or rejection | HIGH | Sync and async machines produce the same result, lifecycle, history, and topology; cancellation is never converted into expected rejection | HIGH |
| Construction and persistence parity | A semantic flag that disappears in a helper or roundtrip is unsafe | HIGH | Direct, builder, batch, factory, declarative, clone, and `from_dict()` paths preserve final/internal metadata without inference | HIGH |
| Diagnostic and visualization truthfulness | Tooling must distinguish final from trap and internal from external self-transition | HIGH | JSON, validation, Mermaid, PlantUML, history, and results expose the selected semantics; snapshots remain current-state-only | HIGH |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes | Confidence |
|---------|-------------------|------------|-------|------------|
| Feature-local cost with untouched direct dispatch | Adds useful workflow semantics without adopting a general statechart runtime | HIGH | Normalize flags during construction; use one predictable lifecycle branch; do not allocate contexts or scan topology on dispatch | HIGH |
| Result-valued expected rejection | Fits Fast FSM's existing `TransitionResult` style while retaining a stable machine-readable reason | MEDIUM | The user raises one narrow control signal at an eligibility hook; `trigger()` converts it into a result instead of propagating it as an unexpected failure | HIGH |
| Entry-relative timing that reflects transition mode | Makes “restart the state” versus “update inside the state” operationally meaningful | MEDIUM | External self-transition resets `after`/`within`; internal self-transition preserves the original entry epoch | HIGH |
| Explicit result and history mode | Same-state audit records remain interpretable | MEDIUM | Add comparison-neutral `internal` metadata to successful/faulting results and transition history | HIGH |
| Installed-artifact semantic and performance proof | Performance is part of the feature contract, not an unverified claim | HIGH | Prove pure-Python and compiled parity; benchmark untouched singleton, external self, internal self, final entry, and each rejection branch | HIGH |
| Progressive controller-owned drone guidance | Teaches the semantics without implying safety certification or hidden runtime ownership | MEDIUM | Extend one deterministic example from priority/timing through internal telemetry refresh, explicit landing finals, and controller handling of rejection codes | HIGH |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Infer final state from no outgoing edges | Looks configuration-free | Confuses a deliberate completion state with an incomplete or trapped graph and changes meaning when an edge is added | Require `final=True`; report non-final sinks as traps in diagnostics |
| Mutable final flags or a sticky termination latch | Seems useful for reopening workflows | Creates two sources of truth and mutation races | Derive termination from the immutable current-state definition; use existing `force_state()`, `reset()`, or `restore()` for explicit control |
| Ordinary transitions out of final states | Supports “reopen” with one event | Contradicts completion and weakens validation | Model “closed but reopenable” as non-final; reserve direct-control APIs for administrative reset/restore |
| Automatic completion events or `on_terminated` callback family | Mirrors full statechart engines | Introduces implicit processing and redundant callback ordering questions | Query `is_terminated`; use existing destination entry, trigger callback, or after-transition observation |
| Machine-wide self-transition behavior switch | Offers compatibility modes | The same machine commonly needs both restart and in-state update semantics; a global flag makes topology context-dependent | Store `internal` on each transition; default to current external behavior |
| `to_state=None` as internal-transition shorthand | Used by another Python FSM library | Removes an explicit graph target and complicates serialization, validation, and declarative matching | Require the same explicit source and target plus `internal=True` |
| Internal transitions to another flat state | “Internal” can be confused with “private” | Skipping exit/entry while changing active state violates the flat lifecycle model | Reject construction unless source and target are identical |
| Treat all self-transitions as internal | Avoids callback repetition | Breaks current behavior and prevents intentional state restart or timing reset | Preserve external default; opt in per transition |
| Treat all guard exceptions as expected rejection | Avoids defining a control signal | Hides defects and may route to an unsafe lower-priority fallback | Catch only `TransitionRejected`; keep all other exceptions as unexpected failures |
| Represent expected rejection as `False` | Reuses the guard API | Loses the caller-visible reason and wrongly permits lower-priority fallthrough | Use a structured control signal converted into an uncommitted result |
| Add a parallel `validators=` callback family | Copies competitor vocabulary | Duplicates eligibility APIs and adds resolution, ordering, builder, and reflection surface | Allow `TransitionRejected` from existing conditions and state-permission hooks |
| Reject after commit and roll back | Makes action code look transactional | External side effects and callbacks are not reversible; rollback would lie about observed work | Expected rejection is pre-commit only; post-commit exceptions remain committed failures |
| Hierarchical states or parallel regions | Provides richer modeling | Replaces one current state with an active configuration and changes selection/lifecycle complexity | Keep v0.5.0 flat; make statecharts a separate product decision |
| Eventless stabilization | Automates follow-up movement | Requires repeated discovery, cycle limits, and macrostep semantics | Require explicit controller-supplied events |
| Deferred/reentrant event queues | Reduces controller code | Changes ownership, callback reentry, fairness, and cancellation contracts | Retain direct callback-reentry rejection; research bounded deferral separately |
| Scheduler ownership or delayed events | Makes workflows self-running | Turns the FSM into a timer/task supervisor | Keep `after`/`within` as passive eligibility and let the controller schedule events |
| Automatic sync/async selection at dispatch | Appears convenient | Makes return types and event-loop ownership implicit | Keep separate machine types and existing builder-time detection |
| Lazy event context, state-store adapters, or reflection-heavy injection | Adds ergonomic flexibility | Allocates or reflects on paths unrelated to these semantics and broadens v0.5.0 | Keep callback arguments and in-memory state ownership unchanged |

## Detailed Behavioral Contract

### 1. Explicit Final States and Termination

#### Declaration and construction

- Add a keyword-only exact boolean `final=False` to `State` and state subclasses.
  Reject non-booleans rather than accepting truthy values across the mypyc
  boundary.
- Preserve `State("name")` and every existing constructor call unchanged.
  `State.create()` should forward the same keyword, and builder/declarative
  states should retain it on the canonical `State` object.
- Permit a final state as the initial state. The newly constructed machine is
  immediately terminated, but construction does not invent an entry event,
  callback run, or history record.
- Reject an outgoing transition whose canonical source is final. The rule
  covers ordinary edges, external self-transitions, internal self-transitions,
  priority candidates, multi-source expansion, and batch/config loading.
- Validation must be atomic. If any expanded source is final, no transition in
  that registration operation and no graph-version change is published.
- Keep global reachability and “every non-final can reach a final” checks in
  opt-in validation, not registration. Incremental graph construction must not
  perform whole-graph scans.

#### Runtime and commit boundary

- `is_terminated` is an O(1) property derived from the current state's final
  flag. It means “the active state is explicitly final now,” not “the machine
  once visited a final state.”
- Entering a final state follows the same external lifecycle as any other
  destination. At the commit seam, current state and optional history update;
  `is_terminated` is therefore already true inside final-state entry callbacks.
- A pre-commit failure leaves the source active and does not terminate. A
  destination-entry, declarative-handler, trigger-callback, after-listener, or
  async cancellation failure after commit leaves the final destination active,
  so the result is unsuccessful but `committed=True` and `is_terminated=True`.
- An ordinary trigger attempted while final has no legal registered edge. It
  returns a cold-path resolution failure that identifies termination, runs no
  transition lifecycle, appends no history, and causes `can_trigger()` to return
  false.
- Do not make final states administratively irreversible. Existing direct
  controls intentionally bypass topology and guards: `force_state()`, `reset()`,
  and `restore()` may move from a final to a non-final state and run their
  established full lifecycle. The termination query changes with the committed
  current state.
- `clone()` starts at the declared initial state as it does today. A clone is
  terminated immediately only when that initial state is final.

#### Tooling and persistence

- Preserve the existing string-only `states` list in topology dictionaries and
  add an optional top-level `final_states` list. This is less disruptive than
  changing every state string into a heterogeneous object. Old dictionaries
  without `final_states` reconstruct all states as non-final.
- Validate that every `final_states` name is a unique member of `states` and
  reject outgoing transition rows from those names during `from_dict()` before
  publishing a partial machine.
- Snapshot version 1 needs no topology field. Restoring a state name uses the
  receiving machine's final metadata, so `is_terminated` is immediately
  truthful after the existing control commit.
- Render explicit finals with standard final markers. Stop labeling every sink
  as terminal. Diagnostics should distinguish `final`, `non-final trap`, and
  ordinary state; final reachability is an analysis result, not a runtime rule.

### 2. External and Internal Self-Transitions

The recommended public spelling is a keyword-only `internal: bool = False` on
the canonical transition registration. The default preserves Fast FSM's current
same-state lifecycle.

| Lifecycle boundary | External self-transition (`internal=False`) | Internal self-transition (`internal=True`) |
|--------------------|---------------------------------------------|--------------------------------------------|
| Resolution, timing, guards, state permission | Evaluate normally | Evaluate normally |
| Before-transition listeners | Run | Run |
| `State.on_exit` and registered exit callbacks | Run | Skip |
| Exit-state listeners | Run | Skip |
| Logical commit and optional history | Commit | Commit |
| Current state object | Reassign same canonical state | Remain same canonical state |
| State-entry timestamp | Reset at commit | Preserve original entry timestamp |
| `State.on_enter` and registered entry callbacks | Run | Skip |
| Enter-state listeners | Run | Skip |
| Declarative handler / transition action | Run | Run |
| Trigger callbacks | Run | Run |
| After-transition listeners | Run | Run |
| Result | Success, `committed=True`, `internal=False` | Success, `committed=True`, `internal=True` |

Additional rules:

- Validate `internal` as an exact boolean during registration. It is immutable
  transition topology and participates in duplicate/candidate identity.
- `internal=True` requires every canonical source to be the same object as the
  canonical target. A multi-source request that violates this for one source is
  rejected atomically.
- Internal transition history records source and target as the same state and
  carries `internal=True`; the record timestamp describes when the event
  committed, not a new state-entry epoch.
- The selected mode should be comparison-neutral metadata on
  `TransitionResult` and `TransitionRecord`. This makes two same-state routes
  auditable without changing callback argument conventions or injecting an
  `internal` keyword that might collide with application payload.
- If an internal transition's before listener fails, nothing commits. If its
  declarative handler, trigger callback, or after listener fails, history remains
  and the failure is `committed=True`, exactly like other post-commit failures.
- `after` and `within` remain relative to the most recent actual state entry.
  Repeated internal refresh events cannot extend a deadline; an external self
  transition intentionally restarts it.
- Direct-control APIs retain external lifecycle and do not gain an `internal`
  option. They are control operations, not registered transition entries.
- Serialize internal mode on transition rows only when true; absence means the
  backward-compatible external default. Diagrams should visibly distinguish an
  internal in-state event from an external loop, and JSON adjacency must retain
  the boolean.

### 3. Expected Domain Rejection

Use one public `TransitionRejected` control exception with a required stable,
non-empty string `code`. It may be raised only as an expected signal from
existing pre-commit eligibility surfaces: transition/declarative conditions and
`State.can_transition` or its async equivalent. The engine catches it separately
from all other exceptions.

| Outcome | Selection Behavior | Result Shape | Lifecycle / History |
|---------|--------------------|--------------|---------------------|
| Guard, timing, or state permission is false | Candidate is ineligible; continue lower priorities | No rejection code and no cause; singleton reports its existing guard/selection/permission failure if no candidate remains | No lifecycle; no history |
| Eligibility hook raises `TransitionRejected(code)` | Abort the entire candidate group immediately | `success=False`, `committed=False`, original stage retained, stable `rejection_code=code`, `cause=None` | No lifecycle; no history |
| Eligibility hook raises another `Exception` | Abort as an unexpected defect | `success=False`, `committed=False`, original stage retained, `rejection_code=None`, original `cause` retained | No lifecycle; no history |
| Async eligibility is cancelled | Abort and re-raise cancellation under existing ownership rules | Failure observer sees truthful stage/priority before cancellation propagates | No lower candidate; commit status remains truthful |
| Any lifecycle callback raises, including `TransitionRejected` | Treat as unexpected execution failure because selection already ended | Existing stage/cause/commit semantics | Never fall through; never roll back |

Recommended result contract:

- Add comparison-neutral `rejection_code: str | None` and a derived
  `rejected` property to `TransitionResult`. A stable code is sufficient for
  application mapping, localization, and tests; do not default-log arbitrary
  domain text or object representations.
- Keep `stage` as the location where rejection occurred (`guard` or
  `state-permission`) rather than inventing a lifecycle stage that loses origin.
  `rejection_code`, `cause`, and existing success/commit fields classify the
  outcome orthogonally.
- `raise_if_failed()` may continue to raise `TransitionError`; callers inspect
  `error.result.rejected` and `rejection_code`. Existing catches remain valid,
  and expected rejection is not chained from an unexpected cause.
- `can_trigger()` and `can_trigger_async()` return false for expected rejection
  because their public contract is boolean. They continue to surface unexpected
  evaluation exceptions according to the existing advisory-query behavior.
  Call `trigger()` when the rejection code is required.
- Notify existing failure observers once for the overall rejected attempt. Do
  not add `on_rejected`. Trace output may use the fixed result category
  `rejected`, but default metadata must not reveal payloads or arbitrary reason
  strings.
- In composed `AndCondition`, `OrCondition`, `NotCondition`, or compatibility
  wrappers, `TransitionRejected` propagates through boolean composition to the
  machine boundary; it is never coerced to false.

### 4. Construction, Runtime, and Tooling Parity

| Surface | Required v0.5.0 Behavior |
|---------|--------------------------|
| Direct `StateMachine` / `AsyncStateMachine` | Canonical reference behavior for all three semantics |
| `State.create` / callback states | Preserve `final`; lifecycle skip applies to both state hooks and registered callbacks |
| `FSMBuilder` | Stage and validate `final` states and `internal` edges before build; failed build publishes no cached partial machine |
| Batch addition and helper factories | Accept additive final/internal metadata without changing legacy tuple meanings; multi-source validation remains atomic |
| Declarative states | Preserve final metadata; match internal mode against the canonical edge; execute the selected handler once without inferring mode from method name |
| Priority candidates | Candidate identity includes internal mode; rejection and unexpected failure stop selection; false remains fallthrough |
| `clone()` | Preserve shared immutable state/transition metadata and existing reset-to-initial behavior |
| `to_dict()` / `from_dict()` | Roundtrip `final_states` and true `internal` flags; reject malformed or contradictory topology before publication |
| Snapshot / restore | Keep snapshot v1 current-state-only; derive termination from receiving topology after restore |
| Results and history | Carry selected `internal` and expected `rejection_code` where applicable; final status remains a current-state query |
| Validation | Reject final-source and non-self internal edges locally; report traps and final reachability through bounded graph analysis |
| Mermaid / PlantUML / JSON | Render finals and internal transitions without losing priority, timing, or condition references |
| Pure and compiled artifacts | Same exceptions, results, callback order, timing epoch, history, and construction failures |

### 5. Edge-Case Oracle

| Case | Required Outcome |
|------|------------------|
| Initial state is final | `is_terminated=True`; no implicit entry callback or history |
| Final state has an internal self-transition request | Construction fails atomically; final means no ordinary outgoing edge |
| Entering final state then destination entry raises | Failure is post-commit; current state remains final and termination is true |
| Async cancellation after commit into final | Cancellation re-raises; failure observation reports committed; termination remains true |
| Reset from final to non-final initial | Full direct-control lifecycle runs; after commit termination is false |
| Restore snapshot naming a final state | Full direct-control lifecycle runs; after commit termination is true |
| Non-final state has no outgoing edge | `is_terminated=False`; diagnostics call it a trap/sink, not final |
| External self-transition | Exit and entry surfaces run in order; history appends; entry timestamp resets |
| Internal self-transition | Exit and entry surfaces do not run; transition actions/observers and history do; entry timestamp is unchanged |
| Internal transition action fails | Result is committed failure; state and entry timestamp remain unchanged; history record remains |
| Internal request from `a` to `b` | Construction fails before topology mutation |
| False guard at priority 0, eligible candidate at 10 | Priority 10 may commit |
| Expected rejection at priority 0 | Priority 10 is not evaluated; rejection result identifies priority 0 and code |
| Unexpected guard exception at priority 0 | Priority 10 is not evaluated; failure retains cause |
| All candidates false | Existing candidate-exhaustion result; not an expected domain rejection |
| `TransitionRejected` raised by an entry callback | Unexpected post-commit callback failure, not expected rejection |
| `can_trigger()` encounters expected rejection | Returns false without mutation; `trigger()` is required to retrieve the code |
| Old topology dictionary lacks new fields | All states non-final and all transitions external, preserving legacy behavior |

## Feature Dependencies

```text
[Immutable State.final metadata]
    ├──enables──> [O(1) is_terminated]
    ├──guards───> [Final-source registration rejection]
    └──feeds────> [Serialization + validation + final renderers]

[Immutable Transition.internal metadata]
    ├──requires─> [Canonical source/target identity]
    ├──branches─> [Lifecycle execution seam]
    ├──controls─> [Entry-relative timestamp reset/preservation]
    └──feeds────> [Result + history + serialization + diagrams]

[TransitionRejected control signal]
    ├──requires─> [Existing eligibility/candidate-selection seam]
    ├──aborts───> [Priority fallthrough]
    └──feeds────> [TransitionResult + failure observation + trace category]

[Canonical sync semantics]
    └──requires-parity──> [Async execution + pure Python + compiled artifact]

[All canonical metadata]
    └──requires──> [Construction/tooling parity]
                       └──requires──> [Installed-artifact proof + tutorial]
```

### Dependency Notes

- **Final-source rejection requires canonical final metadata:** inferencing from
  outgoing-edge count cannot enforce the invariant during incremental build.
- **Internal lifecycle requires canonical source/target identity:** compare
  registered `State` identities after name resolution, not caller spelling.
- **Internal mode requires timing integration:** the existing entry timestamp is
  updated at commit today; internal commit must deliberately preserve it.
- **Expected rejection requires selection integration before lifecycle:** once
  before/exit work begins, fallback or rejection is no longer safe.
- **Observability requires the runtime contract first:** result/history/schema
  fields should describe a settled lifecycle rather than drive it.
- **Artifact proof depends on complete parity:** benchmark numbers are not
  meaningful until pure and compiled artifacts pass the same behavior oracle.

## v0.5.0 Definition

### Launch With

1. Explicit `final` state metadata, final-source rejection, and O(1)
   `is_terminated` with commit-boundary tests.
2. Per-transition external/internal self semantics with external as the default,
   full callback-order tests, history mode, and entry-timing preservation.
3. Structured expected rejection at existing eligibility hooks, with the
   false/rejected/unexpected priority oracle tested in sync and async machines.
4. Direct, builder, batch, factory, declarative, clone, dictionary, validator,
   JSON, Mermaid, and PlantUML parity.
5. Fresh pure/compiled installed-artifact tests, a current
   `python-statemachine` 3.2.1 comparison beside the locked 2.5.0 historical
   baseline, and progressive drone guidance.

### Add After Validation

- A dedicated completion observer only if real users cannot express the need
  with final-state entry or existing after-transition observation.
- Richer localized rejection details only if stable codes plus application-side
  mapping prove insufficient; keep such text out of default traces.
- Administrative “restart” convenience only if repeated use justifies a thin
  wrapper around existing reset/control semantics.

### Future Consideration

- Bounded deferred events, with their own ownership, cancellation, cycle, and
  performance research.
- A separate statechart engine if demand warrants hierarchical or parallel
  active configurations.
- Lazy context or external state-store adapters only after concrete consumers
  demonstrate a stable interface.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Confidence |
|---------|------------|---------------------|----------|------------|
| Explicit finals and O(1) termination | HIGH | MEDIUM | P1 | HIGH |
| Final-source invariant and lifecycle edge cases | HIGH | MEDIUM | P1 | HIGH |
| External/internal self semantics | HIGH | HIGH | P1 | HIGH |
| Expected domain rejection triad | HIGH | HIGH | P1 | HIGH |
| Sync/async and priority parity | HIGH | HIGH | P1 | HIGH |
| Construction/serialization/tooling parity | HIGH | HIGH | P1 | HIGH |
| Installed-artifact semantic/performance proof | HIGH | HIGH | P1 | HIGH |
| Progressive drone tutorial | MEDIUM | MEDIUM | P1 | HIGH |
| Completion-specific callback | LOW | MEDIUM | P3 | MEDIUM |
| Deferred queue, hierarchy, eventless, scheduler, lazy context, state store | OUT OF SCOPE | VERY HIGH | EXCLUDE | HIGH |

**Priority key:** P1 is required for the semantic milestone; P3 requires
post-release evidence; EXCLUDE conflicts with v0.5.0's flat deterministic scope.

## Competitor and Standards Analysis

| Feature | `python-statemachine` 3.2.1 | `transitions` 0.9.3 | W3C SCXML 1.0 | Fast FSM v0.5.0 Recommendation |
|---------|-----------------------------|---------------------|---------------|-------------------------------|
| Final state | Explicit `final=True`, no outgoing transitions, `is_terminated` query | State `final=True` and `on_final` callbacks | Top-level final terminates processing | Explicit immutable final, no ordinary outgoing edges, O(1) current-state query; no automatic completion event |
| External self-transition | Exits and re-enters under current statechart semantics | Reflexive source/destination executes state lifecycle | Targeted self-transition exits and re-enters source | Preserve current full lifecycle and timing reset as default |
| Internal transition | `internal=True`; skips state exit/entry and runs transition action | Destination `None`; transition callbacks run, state callbacks skip | Targetless transition preserves configuration while executing content; internal type has statechart-specific descendant rules | Require explicit same source/target plus `internal=True`; keep flat scope and explicit target |
| False guard | Silently skips candidate and tries the next | Condition prevents that transition; event processing may try registered candidates | False condition disables transition | Preserve priority fallthrough |
| Expected rejection | Validator raises before state change and propagates directly | No equivalent structured domain-rejection contract documented in the core README | Not the source of Fast FSM's application-level result API | Catch one narrow signal and return a structured uncommitted result with stable code |
| Unexpected callback failure | Separate execution/error behavior | Exceptions abort remaining callbacks; post-state-change failures do not roll back | Execution errors follow SCXML processing rules | Preserve existing stage, cause, commit, observer, and cancellation contracts |
| Scope | General statechart runtime in 3.x | Extensible machine with hierarchical/async extensions | Full statechart standard | Deliberately flat, explicit-event, direct-dispatch FSM |

The comparison is a vocabulary and behavior check, not a mandate to implement
SCXML. In particular, SCXML's compound-state transition domain, completion
events, queues, and macrosteps do not belong in this milestone.

## Sources

### Primary external sources (MEDIUM confidence under the research-provider seam)

- [`python-statemachine` 3.2.1 on PyPI](https://pypi.org/project/python-statemachine/) — current release identity and upload date, accessed 2026-09-15.
- [`python-statemachine` states](https://python-statemachine.readthedocs.io/en/latest/states.html) — explicit final states, prohibition on outgoing transitions, and termination query.
- [`python-statemachine` validations](https://python-statemachine.readthedocs.io/en/latest/validations.html) — final-source rejection, traps, final reachability, and internal-target validation.
- [`python-statemachine` transitions](https://python-statemachine.readthedocs.io/en/develop/transitions.html#self-transitions-and-internal-transitions) — current external self-transition and internal-transition lifecycle behavior.
- [`python-statemachine` conditions and validators](https://python-statemachine.readthedocs.io/en/stable/guards.html) — false-condition fallthrough versus validator rejection before state change.
- [W3C SCXML 1.0 Recommendation](https://www.w3.org/TR/scxml/) — normative final-state and transition lifecycle vocabulary.
- [`transitions` official repository documentation](https://github.com/pytransitions/transitions) — reflexive/internal lifecycle, invalid-trigger behavior, final flags, and callback order.
- [`transitions` release history on PyPI](https://pypi.org/project/transitions/) — current 0.9.3 release identity.

### Project evidence (HIGH confidence)

- `.planning/PROJECT.md` — v0.5.0 scope, performance identity, exclusions, and artifact-parity requirements.
- `.planning/research/python-statemachine-gap-assessment.md` — scoped recommendation and current-versus-historical comparison gap.
- `.planning/seeds/SEED-001-evaluate-performance-compatible-fsm-semantics.md` — milestone boundary and deferred-feature warning.
- `README.md` — current callback order, commit boundary, result, history, ownership, timing, construction, and tooling contracts.
- `src/fast_fsm/core.py` — canonical selection, priority fallthrough, commit timestamp, lifecycle execution, and result implementation inspected 2026-09-15.
- `tests/test_transition_timing.py`, `tests/test_priority_selection.py`, and `tests/test_boundary_negative.py` — executable current behavior for entry timing, candidate failures, and self-transitions.

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Final-state API and lifecycle recommendation | HIGH | Directly constrained by existing commit/control contracts and cross-checked against current official competitor docs |
| Internal/external lifecycle and timing recommendation | HIGH | Existing external behavior and timestamp seam are visible in source/tests; ecosystem meaning is consistent across three primary sources |
| Expected rejection recommendation | HIGH | Existing candidate and stage-aware result seams make the three-way behavior testable without a new callback family |
| Current competitor details | MEDIUM | Verified through official docs/repositories and PyPI, but documentation channels mix stable/latest/develop labels |
| Deferred and excluded features | HIGH | Explicitly fixed by milestone scope and project decisions |

---
*Feature research for: Fast FSM v0.5.0 Explicit Flat-FSM Semantics*
*Researched: 2026-09-15*
