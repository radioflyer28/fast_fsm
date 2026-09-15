# Architecture Research: v0.5.0 Explicit Flat-FSM Semantics

**Project:** Fast FSM
**Domain:** High-performance, in-process, flat deterministic finite state machines
**Milestone:** v0.5.0 Explicit Flat-FSM Semantics
**Researched:** 2026-09-15
**Confidence:** HIGH for codebase integration and ordering; MEDIUM for external competitor semantics and the final compiled performance envelope until installed artifacts are measured

## Executive Recommendation

Put finality on the state, self-transition mode on the immutable transition
entry, and expected domain rejection at the existing pre-commit selection
boundary. Do not introduce a second engine, validator callback hierarchy,
runtime context object, or public middleware abstraction.

The concrete shape should be:

- State(name, *, final=False) owns a construction-time, read-only final marker.
  StateMachine.is_terminated reads the current state's marker in O(1).
- TransitionEntry(..., internal=False) owns an exact Boolean mode. internal=True
  is valid only when every canonical source is the canonical target. The existing
  external behavior remains the default.
- TransitionRejected is a small typed exception that application code may raise
  only from selection-time policy (guard, declarative guard, or state permission).
  The selector catches it and returns a structured, uncommitted
  TransitionResult; it never falls through to a lower-priority candidate.
- The existing _PreparedTransition → immutable slot → _PreparedDispatch
  pipeline carries the new scalars. The sync and async lifecycle runners consume
  the same contract, while remaining separate implementations.
- Final and internal metadata fan out from the canonical graph snapshot to
  serialization, history, tracing, validation, diagrams, and structured JSON.
  Those cold paths may scan the snapshot; dispatch must not.

This design adds one read-only state slot, one transition-entry Boolean, and one
predictable lifecycle branch. An untouched unguarded singleton still performs
the same current-source and trigger dictionary lookups and does no reflection,
topology scan, sorting, or feature-object allocation. Internal transition cost is
feature-local O(1); priority groups remain local O(k). Rejection allocates only
when an application intentionally raises it.

## Standard Architecture

### System Overview

~~~text
┌──────────────────────────────────────────────────────────────────────┐
│ Public construction and control                                     │
│ State / CallbackState / DeclarativeState / transition decorator     │
│ StateMachine / AsyncStateMachine / FSMBuilder / factories           │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ normalize exact public values
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Compiled runtime unit: src/fast_fsm/core.py                         │
│                                                                      │
│  registration       selection             lifecycle                 │
│  ┌──────────────┐   ┌────────────────┐    ┌──────────────────────┐   │
│  │ State.final  │   │ direct slot or │    │ external: exit →     │   │
│  │ Entry.mode   │──▶│ local O(k)     │───▶│ commit → enter       │   │
│  │ staged merge │   │ guard/policy   │    │ internal: commit only│   │
│  └──────────────┘   └───────┬────────┘    └──────────┬───────────┘   │
│                              │ rejection/failure                   │
│                              ▼                                     │
│                    TransitionResult / history / trace              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ immutable scalar snapshot
             ┌─────────────────┴──────────────────┐
             ▼                                    ▼
┌─────────────────────────────┐      ┌───────────────────────────────┐
│ Interpreted diagnostics     │      │ Build and release evidence    │
│ _diagnostics.py             │      │ artifact_conformance.py       │
│ validation.py               │      │ release_evidence.py           │
│ visualization.py            │      │ benchmarks/                   │
└─────────────────────────────┘      └───────────────────────────────┘
~~~

The physical compilation boundary does not change: core.py remains one mypyc
unit. The boxes inside it are conceptual private seams, not proposed modules or
public base classes.

### Component Responsibilities

| Component | Status | v0.5.0 responsibility | Implementation direction |
|-----------|--------|------------------------|--------------------------|
| State and state subclasses | Modified | Own explicit final intent | Add a validated read-only marker in slots; thread it through CallbackState, declarative states, and State.create() |
| TransitionEntry | Modified | Own internal/external semantics | Add exact Boolean internal; include it in duplicate identity and immutable groups |
| _PreparedTransition | Modified | Hold a fully validated registration request | Carry internal; reject outgoing finals and non-self internal transitions before any table write |
| _commit_transition_plan() | Modified | Publish topology atomically | Preserve merge-before-publication and one graph-version increment; include mode in equality |
| _PreparedDispatch | Modified only by carried entry | Carry the selected canonical entry to lifecycle | No new context allocation or callback reflection |
| Sync/async selectors | Modified | Convert typed expected rejection to an uncommitted result | Guard false/state veto still fall through in groups; rejection and unexpected exceptions abort |
| Sync/async lifecycle runners | Modified | Apply lifecycle mode | External uses current full lifecycle; internal skips every exit/enter surface but retains transition-level work and one commit/history seam |
| _commit_transition() | Modified | Commit state/history/timing consistently | External transitions update _state_entered_at; internal self-transitions do not reset entry-relative time |
| TransitionResult | Modified | Expose selected mode and expected rejection distinctly | Add comparison-neutral fields such as internal and rejection_code; preserve legacy equality and raise_if_failed() |
| TransitionRecord | Modified | Make history semantically complete | Record internal; a successful internal event is still an audited committed transition |
| TransitionRejected | New | Typed selection-only application signal | Define in core.py with mypyc native_class=False; validate a bounded stable code and keep raw detail out of default logs |
| _GraphSnapshot / _GraphTransition | Modified | Canonical immutable hand-off to cold tooling | Copy final names and transition mode as scalars at capture time |
| _DiagnosticGraph / _DiagnosticEdge | Modified | Interpreted scalar projection | Add final indices/names and internal mode; remain bounded and snapshot-backed |
| Construction adapters | Modified | Preserve semantics from every supported input | Extend existing APIs and row/config shapes; do not add a parallel registrar |
| Validation and visualization | Modified | Distinguish explicit finals from topology dead ends and render mode | Keep legacy terminal/no-outgoing observations, add explicit final facts, and label internal edges |
| Artifact oracle and benchmarks | Modified | Prove source/pure/compiled parity and cost isolation | Add semantic scenarios, untouched singleton measurement, and feature-local measurements |

## Recommended Project Structure

No new runtime module is warranted. Preserve the current structure and extend
the existing owners:

~~~text
src/fast_fsm/
├── core.py                 # runtime values, registration, selection,
│                           # lifecycle, results, builder, declarative adapters
├── conditions.py           # unchanged interpreted subclassing boundary
├── condition_templates.py  # unchanged; no validator/rejection hierarchy here
├── _diagnostics.py         # scalar snapshot adapter gains final/internal facts
├── validation.py           # final-aware structural analysis
├── visualization.py        # final markers and internal edge labels
└── __init__.py             # re-export only genuine public runtime symbols

tools/
├── artifact_conformance.py # deterministic semantic proof across artifacts
└── release_evidence.py     # installed identity, mode, and performance proof

benchmarks/
├── performance_demo.py     # untouched plus feature-local Fast FSM observations
└── benchmark.py            # manual historical/current competitor comparison

examples/                   # progressive controller-owned drone stages
tests/                      # contract, parity, projection, security, performance
~~~

### Structure Rationale

- **core.py:** Finality, transition mode, rejection conversion, and lifecycle
  are runtime semantics on the compiled path. Splitting them out would violate
  ADR-003 and create cross-module hot-path calls.
- **conditions.py:** TransitionRejected is not a condition type. Keeping it out
  of the interpreted condition hierarchy avoids presenting domain rejection as
  another compositional Boolean leaf.
- **_diagnostics.py:** It remains the sole scalar adapter from the canonical
  runtime snapshot. Validation and visualization should not rediscover private
  state markers independently.
- **tools/ and benchmarks/:** Artifact truth and comparative timing remain
  offline evidence, never dispatch dependencies or competitor-powered CI gates.

## Immutable Representation

### State finality

Use a read-only construction-time marker on State:

~~~python
class State:
    __slots__ = ("name", "_final")

    def __init__(self, name: str, *, final: bool = False) -> None:
        self.name = name
        self._final = _normalize_exact_bool(final, name="final")

    @property
    def final(self) -> bool:
        return self._final
~~~

The machine should read the private canonical marker rather than infer
termination from _transitions[current_name]. An immediately-final one-state
machine is valid. reset(), restore(), and force_state() remain explicit
administrative control operations and may move into or out of a final state;
the no-outgoing rule applies to registered event transitions.

Do not add a mutable mark_final() operation. Late mutation would require
scanning for existing outgoing edges, coordinating clones, invalidating graph
snapshots, and deciding whether a currently active machine terminates
retroactively.

### Transition mode

Extend the existing slotted entry and every immutable carrier with an exact
Boolean internal field. The public default is False, preserving today's
external behavior. In this flat machine, internal means exactly a self-edge with
suppressed state exit and entry lifecycle; it is not a targetless transition or
a descendant-state transition.

The duplicate identity for one equal-priority candidate becomes:

~~~text
(canonical target identity,
 normalized condition identity,
 condition_ref,
 after,
 within,
 internal)
~~~

Changing only internal is semantically distinct and must not be treated as an
idempotent re-registration. Because equal priorities cannot tie, it fails
atomically like any other equal-priority conflict.

### Expected rejection

Use one typed signal as input and comparison-neutral scalar fields as output:

~~~python
raise TransitionRejected("inventory.insufficient")

result = machine.trigger("confirm")
assert not result.success
assert result.rejected
assert result.rejection_code == "inventory.insufficient"
assert not result.committed
~~~

TransitionRejected should accept an exact, bounded non-empty code. Optional
human detail may remain on the exception for the direct caller, but the default
TransitionResult.error, log record, trace record, and failure observer should
use fixed text plus the validated code—not arbitrary exception text. This keeps
payloads and secrets out of diagnostics while still allowing applications to
map stable codes to user-facing messages.

Do not serialize rejection declarations into topology. Rejection is a runtime
outcome of application policy, not graph structure.

## Architectural Patterns

### Pattern 1: Normalize, validate, then publish once

**What:** Extend _normalize_transition_request() and _PreparedTransition so all
sources, targets, timing, priority, and mode are canonical before
_commit_transition_plan() touches _transitions.

**When to use:** Every direct registrar, fan-out helper, batch, builder build,
declarative replay, quick factory, and dictionary loader.

**Trade-offs:** Registration performs feature-local validation up front, but
runtime stays simple. For s source states and local candidate depth k, a fan-out
merge is local O(s·k), never a global graph scan.

Required atomic failures include:

- any source is final;
- internal is not an exact bool;
- an internal source is not the canonical target;
- any equal-priority candidate conflicts after mode normalization;
- any batch row or serialized field is malformed.

No affected slot, builder cache, machine-type decision, or graph version may
change on these failures.

### Pattern 2: One selector outcome algebra

**What:** Keep the current selector return shape—prepared dispatch or failed
result—and add a private _build_rejection_result() helper. Catch
TransitionRejected before broad Exception at every selection-time user-code
seam.

**When to use:** Sync and async guard evaluation, declarative guard evaluation,
and state permission.

**Trade-offs:** Catch sites are duplicated across explicit sync/async engines,
but the semantic table remains identical and mypyc-friendly. A new callback
family would reduce neither duplication nor runtime cost.

| Selection outcome | Singleton | Priority group | Commit? | Result category |
|-------------------|-----------|----------------|---------|-----------------|
| timing/guard/state policy returns false | failed result | continue locally | No | ordinary ineligibility |
| TransitionRejected | stop | stop; suppress lower candidates | No | expected domain rejection |
| ordinary exception | stop | stop; suppress lower candidates | No | unexpected selection failure |
| async cancellation | n/a | stop; suppress lower candidates | No | re-raise after one failure observation |
| fully eligible | dispatch | first eligible wins | lifecycle decides | prepared dispatch |

For can_trigger() and can_trigger_async(), expected rejection should produce
False without observer notification or mutation. Unexpected error and
cancellation behavior should preserve the established query contract.

### Pattern 3: Lifecycle specialization at one seam

**What:** Branch once at the beginning of lifecycle execution:

~~~text
if entry.internal:
    before-transition
    commit/history without re-entry timestamp reset
    declarative transition handler
    trigger callbacks
    after-transition
else:
    existing lifecycle unchanged
~~~

**When to use:** Only after selection has returned a canonical prepared
dispatch. Do not let guards or builders choose lifecycle behavior dynamically.

**Trade-offs:** The default path pays one predictable Boolean branch. It avoids
multiple mode checks around every callback collection and makes it testable that
all exit/enter surfaces are skipped together.

An internal transition skips:

- State.on_exit();
- registered synchronous and asynchronous source-exit callbacks;
- exit-state listeners;
- destination State.on_enter();
- registered synchronous and asynchronous destination-enter callbacks;
- enter-state listeners.

It retains before-transition listeners, the declarative handler, trigger
callbacks, after-transition listeners, result production, tracing, and optional
history. It is committed=True on success even though the state identity does
not change. A post-selection TransitionRejected raised by a lifecycle callback
is too late to be a domain rejection and remains an unexpected lifecycle
failure.

### Pattern 4: Scalar snapshot fan-out

**What:** Capture final_state_names and internal in _GraphSnapshot /
_GraphTransition, then adapt once into _DiagnosticGraph / _DiagnosticEdge.

**When to use:** Serialization, validation, diagram rendering, comparison,
structured JSON, and tooling.

**Trade-offs:** Snapshot capture is O(V+E) and allocates immutable tuples, as it
already does. This remains explicit cold-path work under the ownership boundary;
no snapshot is cached or created by dispatch.

## Data Flow

### Registration Flow

~~~text
public registrar / builder / factory / from_dict / decorator metadata
    ↓
exact scalar validation
  final: exact bool
  internal: exact bool
  priority: exact int
  timing: finite built-in number or None
    ↓
canonical source and target identity resolution
    ↓
reject any final source
reject internal unless source is target (for every fan-out source)
    ↓
normalize guard/unless and async requirement
    ↓
_PreparedTransition tuple (no table writes)
    ↓
merge each local slot off-table; include internal in duplicate identity
    ↓
publish all changed slot values together
    ↓
advance graph version once, or remain version-neutral for exact duplicates
~~~

add_emergency_transition() should mean all currently registered **non-final**
states once finals exist. This preserves the helper's emergency intent without
creating illegal outgoing edges. add_bidirectional_transition() must reject the
complete operation if either direction starts at a final state. An internal
fan-out with more than one distinct source is invalid by construction.

### Trigger Flow

~~~text
trigger / trigger_async
    ↓ acquire existing per-machine ownership
current state name → source row → trigger slot       O(1), two lookups
    ↓
singleton direct branch OR immutable local group     O(1) / O(k)
    ↓ optional timing test → guard → declarative guard → state permission
    ├── false/veto ───────────▶ singleton failure or group fallthrough
    ├── TransitionRejected ───▶ structured uncommitted rejection, stop
    ├── exception/cancel ─────▶ established staged failure policy, stop
    └── eligible ─────────────▶ _PreparedDispatch
                                   ↓
                             branch on entry.internal
                              ├── external lifecycle
                              └── internal lifecycle
                                   ↓
                             no-user-code commit seam
                                   ↓
                      result / optional history / optional trace
                                   ↓
                         release ownership in all cases
~~~

### Commit and Timing Flow

External transitions, including external self-transitions, keep today's commit
contract: validate one monotonic timestamp, prepare history if enabled, publish
the current state and entry timestamp together, then run destination-entry
surfaces. An external self-transition therefore restarts after/within
eligibility relative to that re-entry.

Internal self-transitions do not represent a new state entry. They must preserve
_state_entered_at. If history is enabled, capture a timestamp for the record;
otherwise the internal commit need not read the clock merely to reassign the
same state. This is both semantically correct and feature-local. History append
and the successful committed=True result remain aligned.

### Projection Flow

~~~text
authoritative State / TransitionEntry values
    ├── to_dict() ───────────────▶ final_states + transition.internal
    ├── clone() ─────────────────▶ shared immutable values, independent tables
    ├── TransitionResult ────────▶ internal + rejection facts
    ├── TransitionRecord ────────▶ internal audit fact
    ├── FSMTraceEvent ───────────▶ bounded scalar mode/rejection category
    └── _GraphSnapshot
          ↓
        _DiagnosticGraph
          ├── validator: final vs non-final trap; reachability
          ├── Mermaid/PlantUML: final marker, internal edge label
          ├── JSON: explicit finals, internal per edge
          └── comparison/path tools: preserve edge identity and mode
~~~

Keep the existing topology-derived terminal observation for compatibility, but
add explicit final facts rather than redefining terminal. A non-final state with
no outgoing transition is a trap/dead end; a final state is an intentional
completion state. Validators should stop warning that finals need exit
transitions and may separately report unreachable finals or non-final states
with no path to any final.

## Construction and Persistence Parity

### State construction

| Surface | Required propagation |
|---------|----------------------|
| State | keyword-only final=False |
| CallbackState | accept and pass final to State |
| State.create() | accept final and create matching CallbackState |
| DeclarativeState / AsyncDeclarativeState | accept and pass final; handler discovery unchanged |
| StateMachine.from_states() / simple_fsm() | accept a validated final_states collection of names |
| quick_build() / quick_fsm() | preserve supplied State(final=True) and optionally accept final_states for string shorthand |
| FSMBuilder | preserve final markers on staged State identities; no add_final_state() API |

### Transition construction

| Surface | Required propagation |
|---------|----------------------|
| add_transition() | keyword-only internal=False |
| add_transitions() row | extend the existing row schema once and validate exact arity/type |
| bidirectional/emergency helpers | pass mode only where semantically valid; retain one atomic plan |
| transition() decorator | store normalized mode in immutable metadata and bound handler identity |
| FSMBuilder.add_transition() | stage mode before publishing builder state and replay it at build |
| quick_build() | collect endpoints, then replay through canonical batch registration |

### Dictionary serialization

Keep "states" as the existing list of names and add a top-level
"final_states": [...]. Changing "states" to objects would break existing
consumers. Each transition row adds "internal": true|false. from_dict() must
parse and validate the complete scalar input before creating or publishing a
machine, including unique non-empty final names and exact Booleans. Callable
implementation remains outside the document and is reattached only through the
existing condition registry.

The public runtime snapshot() remains current-state/version data. It does not
need a v2 topology schema: to_dict() owns topology and state finality;
snapshot() plus an already reconstructed topology still restores a final
current state correctly.

## Sync/Async Parity Contract

Keep separate explicit machine types. Share constants, normalizers, immutable
carriers, rejection-result builders, and projection code; duplicate the small
selection and lifecycle control flow so awaits and cancellation remain visible.

The parity matrix must cover:

| Scenario | Sync | Async |
|----------|------|-------|
| enter explicit final | same committed result and termination query | same after awaited lifecycle |
| trigger from final | impossible to register; missing event is resolution failure | identical |
| external self-transition | all exit/enter surfaces run; entry time resets | sync then async callbacks at matching slots; time resets |
| internal self-transition | no exit/enter surfaces; transition-level surfaces run | no sync or async exit/enter surfaces; transition-level surfaces run |
| internal callback failure before logical commit | uncommitted staged failure | identical ordinary-exception result |
| internal callback failure after commit | committed staged failure | identical plus cancellation-stage fidelity |
| expected rejection in guard/policy | uncommitted structured rejection; no fallthrough | identical; lower candidates suppressed |
| unexpected guard error | existing staged failure | existing staged failure |
| cancellation during selection/lifecycle | not applicable | observed once, truthful stage/priority/commit, then re-raised |

## Performance Isolation

| Path | Required complexity | Allowed v0.5.0 cost | Forbidden cost |
|------|---------------------|---------------------|----------------|
| untouched unguarded singleton | O(1) | one mode branch at lifecycle seam; existing result/prepared values | new context allocation, reflection, sort, graph scan, final-state scan |
| termination query | O(1) | one current-state Boolean read | inspect outgoing transitions |
| external self-transition | O(1) | existing lifecycle and timestamp update | topology analysis |
| internal self-transition | O(1) | feature-local lifecycle specialization; history allocation only if enabled | exit/enter callback traversal, entry-time reset |
| priority group | local O(k) | rejection can stop at active candidate | scan unrelated states/transitions |
| registration fan-out | local O(s·k) | off-table merge and exact validation | partial publication or dispatch-time normalization |
| projection/validation | bounded O(V+E) or documented algorithmic cost | immutable snapshot allocation on explicit call | dispatch invocation of diagnostics |
| rejection | exceptional feature path | typed exception plus one result | allocation on successful or ordinary guard-false paths |

Performance proof must separate:

1. untouched compiled singleton throughput (still at least 200,000 ops/sec);
2. final-state query and entering-final cost;
3. internal versus external self-transition cost;
4. expected rejection cost and lower-candidate suppression;
5. local group depth versus unrelated topology size;
6. pure-source, installed pure wheel, and installed compiled wheel semantics.

Manual competitor reporting should label the locked historical
python-statemachine 2.5.0 baseline separately from the current installed 3.2.x
release. Resolve and print actual package versions and artifact origins at
runtime; do not silently update one lock and call the numbers comparable. Keep
competitor work out of the required CI path.

## Validation and Security Boundaries

### Construction boundary

- Validate final and internal as exact built-in Booleans; do not accept 0/1,
  truthy strings, NumPy booleans, or coercible objects.
- Resolve endpoints to canonical registered state identities before comparing a
  self-edge or enforcing final-source rules.
- Stage all rows before committing. Invalid late rows leave topology, graph
  version, builder cache, and mode detection unchanged.
- Treat from_dict() as untrusted data: exact container/scalar checks,
  duplicates rejected, no callable import/evaluation, and no executable
  transition action in serialized input.

### Runtime rejection boundary

- Catch TransitionRejected only around pre-commit application policy.
- Validate and cap the rejection code; use fixed default diagnostic text.
- Do not interpolate arbitrary exception messages, payload representations,
  state names, or trigger names into metadata-only trace records.
- Failure observers run once and cannot replace the original outcome. Their
  established signature remains unchanged.
- BaseException, especially asyncio.CancelledError, retains existing
  ownership-release and re-raise behavior.

### Projection boundary

- Snapshot state finality and mode as scalars while holding the existing graph
  ownership boundary; do not let tools read mutable runtime objects later.
- Continue escaping all caller-controlled diagram/Markdown text and using
  bounded diagnostic ledgers.
- Add only scalar internal, final, and rejection-category fields to tracing and
  artifact evidence. Raw application detail is opt-in through the existing
  redactor boundary.

## Dependency-Aware Build Order

### Phase 1 — Semantic contract and evidence baseline

Freeze exact public meanings, callback order, entry-time behavior, rejection
taxonomy, serialization shape, and sync/async matrix. Add failing contract tests
and extend benchmark/oracle schemas before runtime changes. Capture the locked
historical and current competitor versions as labeled evidence.

**Why first:** Internal transitions alter callback and timing semantics; expected
rejection alters priority fallthrough. Ambiguity here would cause later rewrites.

### Phase 2 — Explicit final states in canonical topology

Implement the immutable State marker, final-aware construction, no-outgoing
registration rule, O(1) termination query, clone/control-operation behavior, and
snapshot scalar. Cover initial-final and atomic fan-out failures.

**Depends on:** Phase 1 contract.  
**Unblocks:** Construction adapters, validators, diagrams, tutorial completion.

### Phase 3 — Transition mode registration and runtime lifecycle

Add internal to immutable carriers and duplicate identity, validate canonical
self-edges atomically, then specialize sync and async lifecycle at one seam.
Preserve entry time for internal transitions and record mode in results/history.

**Depends on:** Phase 1; can proceed after the final-source invariant is stable.  
**Risk focus:** callback suppression completeness, pre/post-commit truth, async
cancellation, external-self backward compatibility, mypyc layout.

### Phase 4 — Expected domain rejection

Add the typed input signal and structured result fields, then catch it at every
selection-time user-code seam in both selectors. Prove no priority fallthrough,
no commit/history, query observation behavior, redaction, and late-lifecycle
misuse as ordinary failure.

**Depends on:** stable selector and lifecycle carrier from Phase 3.  
**Why separate:** It is locally small but cross-cuts guard, declarative, state
permission, tracing, result, and cancellation semantics.

### Phase 5 — Construction and persistence parity

Update State.create, state subclasses, factories, builder, tuple rows,
decorator metadata, from_dict()/to_dict(), clone, public exports, type
signatures, and round-trip tests. Reuse canonical normalization everywhere.

**Depends on:** Phases 2–4 canonical representations.  
**Risk focus:** tuple-position drift, partially published builders, ambiguous
serialized defaults, exact type validation.

### Phase 6 — Diagnostics and projection parity

Extend _GraphSnapshot → _DiagnosticGraph, final-aware validation, legacy
terminal compatibility, JSON schemas, Mermaid/PlantUML, comparison/path
adapters, debug info, and output containment tests.

**Depends on:** Phase 5 stable serialized and runtime facts.  
**Why after runtime:** Cold tools should consume one settled canonical model,
not drive or duplicate it.

### Phase 7 — Installed-artifact and progressive-guidance proof

Extend artifact_conformance.py, release-evidence tasks, slots/mypyc guards,
pure/compiled installed wheels, feature-local benchmark reports, current versus
historical competitor labels, and the progressive controller-owned drone
tutorial.

**Depends on:** all semantic and projection phases.  
**Exit criterion:** source, installed pure, and installed compiled artifacts
produce the same payload-safe scalar oracle; untouched compiled singleton meets
the floor; tutorial demonstrates final completion, external refresh/re-entry,
internal telemetry handling, and expected domain rejection without queues,
schedulers, or statecharts.

## Anti-Patterns

### Inferring finality from no outgoing transitions

**What people do:** Define is_terminated as an empty source row.

**Why it is wrong:** It conflates intentional completion with incomplete
topology, makes later registration change domain meaning, and forces topology
inspection for a runtime query.

**Do this instead:** Read the explicit current-state marker and let validation
report non-final traps separately.

### A machine-wide self-transition flag

**What people do:** Configure all self-transitions as internal or external on
the machine.

**Why it is wrong:** Different events in the same state often need different
lifecycle semantics; a global switch also hides mode from topology and history.

**Do this instead:** Store exact immutable mode per transition, defaulting to
external.

### Treating expected rejection as guard false

**What people do:** Catch TransitionRejected and continue to the next priority
candidate.

**Why it is wrong:** A domain validation failure would silently select a
lower-priority behavior, losing the caller-visible reason and potentially
committing unintended state.

**Do this instead:** Abort selection with a structured uncommitted rejection.

### Catching rejection around the entire trigger

**What people do:** Convert the same exception even when raised during exit,
entry, or after-transition callbacks.

**Why it is wrong:** After lifecycle begins, rollback is unavailable and commit
may already have happened. Calling that an expected precondition rejection lies
about state.

**Do this instead:** Catch only within selection-time policy seams; lifecycle
failures retain their truthful stage and commit flag.

### A public transition-context or validator abstraction

**What people do:** Add a context allocation and callback family for every
trigger to host the new semantics.

**Why it is wrong:** It adds unconditional allocation/reflection and widens the
API without substitution leverage.

**Do this instead:** Carry scalars in existing internal values and use the typed
exception only on the expected-rejection path.

### Updating runtime before projections

**What people do:** Ship internal/final behavior while serialization,
validation, diagrams, history, or installed oracles still omit it.

**Why it is wrong:** Tools and reconstructed machines then describe a different
FSM from the one that executed.

**Do this instead:** Phase the work, but do not declare the milestone complete
until every canonical projection consumes the new facts.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Contract |
|----------|---------------|----------|
| public API ↔ normalization | direct calls and immutable metadata | exact types, no mutation on failure |
| normalization ↔ topology commit | _PreparedTransition | all canonical invariants already true |
| topology slot ↔ selector | TransitionEntry or _TransitionGroup | singleton direct; group pre-sorted and local |
| selector ↔ lifecycle | _PreparedDispatch | one fully eligible canonical entry or a terminal result |
| lifecycle ↔ commit | direct private call | no user code; truthful history/state/timestamp publication |
| core ↔ diagnostics | _GraphSnapshot | scalar immutable facts captured under ownership |
| source ↔ installed artifacts | conformance oracle | checkout-independent, payload-free, exact scenario schema |

### External References

No runtime external service is introduced. The only external integration is
offline benchmark comparison with explicitly versioned competitor packages.
The single runtime dependency policy remains unchanged.

## Sources

### Primary project sources — HIGH confidence

- src/fast_fsm/core.py — current immutable candidate storage, atomic
  registration, sync/async selection, lifecycle/commit, builder, declarative,
  result/history, ownership, timing, and trace seams.
- src/fast_fsm/_diagnostics.py, src/fast_fsm/validation.py, and
  src/fast_fsm/visualization.py — canonical snapshot fan-out, bounded graph
  analysis, terminal inference, diagrams, and JSON.
- tools/artifact_conformance.py, tools/release_evidence.py, Taskfile.yml,
  benchmarks/performance_demo.py, and tests/test_performance_benchmarks.py —
  installed-artifact, payload-safety, complexity, and performance proof seams.
- .specify/decisions/ADR-002-trigger-result-not-exception.md — expected failure
  remains a result-value contract.
- .specify/decisions/ADR-003-mypyc-compilation-boundary.md — only core.py
  compiles; interpreted condition subclassing remains open.
- .specify/decisions/ADR-007-priority-topology.md — immutable local groups,
  exact normalization, and merge-before-publication.
- .specify/decisions/ADR-008-condition-composition-and-transition-timing.md —
  entry-relative timing and one timestamp at commit.
- .planning/PROJECT.md and
  .planning/research/python-statemachine-gap-assessment.md — milestone scope,
  product constraints, and explicit exclusions.

### External primary documentation — MEDIUM confidence

- [python-statemachine 3.2 states](https://python-statemachine.readthedocs.io/en/latest/states.html) — explicit final markers, no outgoing transitions, and is_terminated.
- [python-statemachine 3.2 validations](https://python-statemachine.readthedocs.io/en/latest/validations.html) — no transitions from finals, trap/final reachability checks, and internal target validation.
- [python-statemachine 3.2 transitions](https://python-statemachine.readthedocs.io/en/stable/transitions.html) — external self-transition exit/entry versus internal suppression.
- [python-statemachine 3.2 conditions and validators](https://python-statemachine.readthedocs.io/en/stable/guards.html) — guard-false candidate skipping versus caller-visible expected rejection before state change.

External confidence is MEDIUM because the research seam selected Context7 but
that MCP provider and its documented CLI fallback were unavailable; the claims
were cross-checked directly against current official documentation instead.

## Open Questions for Phase Discussion

- Exact public field names on TransitionResult: rejected plus rejection_code is
  the clearest low-allocation shape, but the phase contract should confirm
  naming before implementation.
- Whether TransitionRejected exposes optional human detail in addition to a
  stable code. If included, detail must remain out of default logs/traces and
  must not become serialized topology.
- Whether to_dict() always emits internal: false and an empty final_states, or
  omits defaults. Always emitting is more canonical; omitting is smaller.
  from_dict() must accept both either way.
- Whether final reachability is a warning or an opt-in informational analysis.
  The no-outgoing invariant is mandatory; global reachability should remain a
  cold diagnostic, never registration-time graph scanning.

---
*Architecture research for: Fast FSM v0.5.0 Explicit Flat-FSM Semantics*
*Researched: 2026-09-15*
