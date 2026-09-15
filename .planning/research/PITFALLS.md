# Pitfalls Research: v0.5.0 Explicit Flat-FSM Semantics

**Domain:** High-performance flat Python FSM adding explicit completion,
same-state lifecycle modes, and expected domain rejection
**Project:** Fast FSM v0.5.0
**Researched:** 2026-09-15
**Confidence:** HIGH for repository-specific risks; MEDIUM for external
ecosystem guidance under the GSD confidence seam

## Risk Model and Recommended Phase Vocabulary

This document uses the following proposed roadmap phases. The roadmap may rename
them, but it should preserve these ownership boundaries.

1. **Semantic Contract and Benchmark Baselines** — freeze vocabulary, defaults,
   result categories, lifecycle matrices, serialization compatibility, and fair
   measurement shapes before runtime changes.
2. **Explicit Final States** — immutable final metadata, construction
   invariants, termination queries, and commit-relative truth.
3. **Same-State Transition Modes** — per-transition internal versus external
   semantics, including timing, history, failure, sync, and async rules.
4. **Expected Domain Rejection** — narrow signal, structured result,
   priority-selection behavior, redaction, query, and cancellation rules.
5. **Construction and Persistence Parity** — factories, builder, declarative
   path, clone, serialization, exports, and type signatures.
6. **Diagnostics and Projection Parity** — validators, immutable diagnostic
   graph, JSON projections, Mermaid/PlantUML, and containment budgets.
7. **Installed Artifact, Benchmark, and Guidance Proof** — source, pure-wheel,
   and compiled-wheel conformance; version-locked comparisons; progressive
   drone guidance.

The release-blocking risks are semantic corruption, lifecycle/post-commit lies,
priority fallthrough after a terminal outcome, silent persistence loss, and a
regression in the direct installed compiled singleton path.

## Critical Pitfalls

### Pitfall 1: Finality Is Still Inferred From Missing Outgoing Edges

**What goes wrong:** A state with no outgoing edge is reported as final even
when it is merely an incomplete graph, while an explicitly final state acquires
an outgoing edge through a batch, builder, deserializer, bidirectional helper,
or later mutation. Runtime, validation, and figures disagree about completion.

**Why it happens:** Existing diagnostics use the structural notion “terminal”
for a sink node. Adding a flag to one constructor without moving the invariant
into the canonical topology registrar leaves several bypasses.

**How to avoid:**

- Store immutable, exact-boolean final metadata on the canonical `State`; never
  derive it from `_transitions`.
- Enforce zero ordinary outgoing topology transitions from a final state in the
  normalize-before-publish registrar used by every construction path.
- Reject a whole fan-out, bulk, or bidirectional operation if any source is
  final. Never publish a valid prefix.
- Decide explicitly whether an initial state may also be final. If allowed, it
  is terminated immediately; if rejected, reject consistently everywhere.
- Keep `reset`, `restore`, and `force_state` outside the outgoing-edge rule;
  they are direct controls, not graph edges.

**Warning signs:** Validators still call every sink final; finality is mutable
after registration; graph version changes before a failed batch returns;
`from_dict()` accepts a final source; tests cover only `add_transition()`.

**Verification evidence:** Property tests generate direct, fan-out, bulk,
bidirectional, builder, and deserialized graphs and prove no committed snapshot
contains an edge from a final state. Failed operations leave topology, graph
version, clone behavior, and current state unchanged.

**Phase to address:** Phase 2 owns the invariant; Phases 5–6 prove all adapters
and projections.

---

### Pitfall 2: Termination Truth Changes at the Wrong Lifecycle Point

**What goes wrong:** `is_terminated` becomes true only after entry callbacks
finish, becomes false after a post-commit failure, or is cached separately from
current state. A callback or cancelled async caller sees a final current state
while the query/result claims the machine did not terminate.

**Why it happens:** “Successful trigger” and “committed transition” are easy to
conflate. ADR-004 permits post-commit failure/cancellation with destination and
history retained.

**How to avoid:**

- Make termination an O(1) read of the current state's immutable final flag;
  do not maintain a second mutable bit or scan topology.
- Change truth at the existing no-user-code commit seam, not after callbacks.
- Post-commit failure/cancellation keeps destination finality, one history
  record, `committed=True`, and the reached stage.
- Pre-commit failure/rejection/cancellation retains the source and prior truth.
- Do not emit automatic completion callbacks or events.

**Warning signs:** A `_terminated` slot exists; destination `on_enter` sees
false; post-commit failure has `committed=False`; cancellation rolls back.

**Verification evidence:** Probes read termination at every ADR-004 stage.
Failure and cancellation injection proves state/result/history/query truth for
both machine types.

**Phase to address:** Phase 2, with the truth table frozen in Phase 1.

---

### Pitfall 3: Internal Self-Transitions Become No-Ops or External Re-entry

**What goes wrong:** Internal events fire exit/entry hooks, reset state-owned
resources, and restart entry-relative timers; or they are treated as guard-only
no-ops and skip transition actions, before/after observers, history, failure
finalization, and committed result.

**Why it happens:** Equal source/destination identity can erase lifecycle intent.
Reusing the whole executor preserves external behavior where internal behavior
must omit only state exit/re-entry surfaces.

**How to avoid:**

- Store exact immutable mode metadata per transition. Default to existing
  external behavior; never use a machine-wide flag.
- In a flat FSM, reject `internal=True` unless canonical source and target are
  the same object. Descendant semantics are out of scope.
- External self order remains ADR-004: before; exit surfaces; commit; enter
  surfaces; declarative transition handler; trigger callbacks; after.
- Internal order keeps before, a no-user-code logical commit, declarative
  handler, trigger callbacks, and after, but omits every exit/enter surface.
- The internal commit may append one history record and returns
  `committed=True`, but preserves `_state_entered_at`. External self resets it.
- Freeze whether result/history expose mode and extend additively without
  changing legacy positional/equality behavior.

**Warning signs:** Code branches on `old_state is to_state` instead of metadata;
internal calls `_commit_transition()` unchanged and resets entry time; external
self stops callbacks; internal success has no history or is uncommitted.

**Verification evidence:** Exact ordered sentinels cover every hook family for
both modes. Fake-clock tests prove only external re-entry resets `after=` and
`within=` residency. Stage failures prove prefix suppression and commit truth.

**Phase to address:** Phase 3.

---

### Pitfall 4: Expected Rejection Is Treated as Candidate Ineligibility

**What goes wrong:** A high-priority candidate intentionally rejects a domain
operation, but the selector treats it as false eligibility and runs a lower
candidate. A forbidden operation succeeds through fallback.

**Why it happens:** Candidate evaluation already uses `None` for the sole
fallthrough outcome, so mapping every expected negative there is tempting.

**How to avoid:**

- Keep three disjoint outcomes: false guard/timing/permission may continue;
  narrow expected rejection aborts the group with a structured value result;
  unexpected exception aborts with existing stage/cause semantics.
- Catch rejection before generic `Exception` only at approved pre-commit seams.
- Never start lifecycle or inspect a lower candidate after rejection.
- Extend `TransitionResult` additively: preserve the legacy first five
  positional fields and equality, use a stable machine-readable category/code,
  keep `success=False` and `committed=False`, and avoid making callers parse
  prose to distinguish rejection.
- Finalize one public trigger failure exactly once; fallthrough candidates and
  queries remain observer-free.
- Freeze `can_trigger*()` behavior. Recommended: expected rejection maps to
  false for the boolean query, while actual trigger returns structured reason;
  unexpected query exceptions retain the existing contract.

**Warning signs:** Rejection returns `None`; lower guard counters increment;
`on_failed` fires per candidate; a query mutates history or notifies observers.

**Verification evidence:** A three-candidate counter matrix proves false guard
advances, rejection stops, and exception stops across sync/async,
singleton/group, and `can_trigger*()`.

**Phase to address:** Phase 4, after Phase 1 freezes result/query semantics.

---

### Pitfall 5: Post-Commit Rejection Is Relabeled as Harmless Refusal

**What goes wrong:** Entry hook, declarative action, trigger callback, or after
listener raises the new rejection type. A broad outer catch reports a clean
precondition refusal or `committed=False` although state/history and possibly
external side effects already changed.

**Why it happens:** A public exception can be raised from any user code, but its
meaning depends on catch location. One catch around all of `trigger()` erases
ADR-004 stage and commit truth.

**How to avoid:**

- Specify allowed rejection seams before coding; prefer pre-commit guard or
  state-permission validation only.
- At lifecycle callback stages, treat the same type as established lifecycle
  failure or at minimum preserve `committed` and `stage`.
- Never roll back, compensate, shield, or continue the suffix.
- Keep cause available only at the intentional inspection/exception boundary;
  result text and default logs remain concise and redacted.

**Warning signs:** One rejection catch surrounds selection plus lifecycle;
destination is current but result says uncommitted; history disappears; later
callbacks execute after the signal.

**Verification evidence:** Raise the signal from every guard, permission, and
lifecycle slot. Only approved pre-commit slots produce expected rejection;
later slots preserve ADR-004 failure truth.

**Phase to address:** Phase 4.

---

### Pitfall 6: Async Cancellation Is Swallowed by New Branches

**What goes wrong:** `CancelledError` becomes rejection, internal cancellation
skips failure finalization, ownership stays busy, or cancellation gets assigned
to the wrong side of the logical commit.

**Why it happens:** Nested catches and a second lifecycle runner can bypass the
dedicated outer async boundary. Python cancellation is `BaseException` control
flow and ADR-004 requires exactly-once observation then bare re-raise.

**How to avoid:**

- Catch only the narrow rejection type at approved seams; never use
  `BaseException` for domain rejection.
- Keep one outer cancellation finalizer and ownership release in `finally` for
  internal and external branches.
- Pre-commit cancellation retains source/no history; post-commit cancellation
  retains destination or internal logical commit/one history record.
- Await candidates sequentially and callbacks at matching lifecycle slots;
  never launch candidate guards concurrently.
- Prove machine reuse after cancellation from every await point.

**Warning signs:** `except BaseException` returns a result; cancellation reaches
a lower candidate; leaked guard tasks remain; next trigger reports busy.

**Verification evidence:** Deterministic cancellation injection covers each
candidate and lifecycle await for internal, external-self, and final entry,
asserting identity, one observer, ownership release, state/history, and no leak.

**Phase to address:** Phases 3–4; Phase 7 repeats against installed artifacts.

---

### Pitfall 7: New Semantics Tax the Untouched Singleton Fast Path

**What goes wrong:** Every trigger allocates context/rejection data, wraps a
singleton in a tuple, scans finality, snapshots topology, reflects on callbacks,
or dispatches through strategy objects. Behavior is right but product identity
is lost.

**Why it happens:** One generic pipeline makes cross-cutting code tidy while
turning optional features into unconditional hot-path work.

**How to avoid:**

- Keep a direct slotted `TransitionEntry`; fixed mode metadata must not promote
  it into a group or strategy wrapper.
- Normalize exact values, invariants, and serialized fields at construction.
- Read finality from current state in O(1); do not precheck it on every trigger
  when missing outgoing topology already fails resolution.
- Allocate rejection data only on rejection. Keep diagnostics and
  serialization outside dispatch.
- Preserve the installed compiled 200,000 ops/sec singleton floor and prove
  unrelated topology cannot change its work shape.

**Warning signs:** Singleton dispatch calls `_transition_entries()` or
`_graph_snapshot()`; unrelated state count affects latency; benchmark imports
source checkout.

**Verification evidence:** Structural tests assert direct representation and no
tuple iteration/snapshot. Fresh installed compiled samples retain the floor;
feature-local paths get separate labelled ratios.

**Phase to address:** Phase 1 baseline; Phases 2–4 protect; Phase 7 proves.

---

### Pitfall 8: Serialization Silently Erases Final or Internal Meaning

**What goes wrong:** `to_dict()` reconstructs as non-final or external mode, or
changing `states: list[str]` to object records breaks consumers. An older Fast
FSM may accept new output while silently ignoring new semantics.

**Why it happens:** The topology has no schema version and current readers
tolerate unknown top-level keys. Additive fields support old-input/new-reader
compatibility but cannot make new-input/old-reader safe.

**How to avoid:**

- Freeze a directional compatibility matrix in Phase 1: old→new, new→new, and
  new→old. Label the last semantically lossy unless a fail-closed boundary is
  enforceable.
- Preserve legacy `states` shape; prefer additive final-state metadata and an
  `internal` field omitted/false by default.
- Validate exact types, duplicate/unknown final names, internal non-self
  targets, and final outgoing edges before graph publication.
- Serialize opaque condition references only—never callback code, validators,
  exceptions, or causes.
- Keep `snapshot()/restore()` runtime-state scope unchanged absent a separate
  versioned decision.

**Warning signs:** Round-trip changes callbacks; missing `internal` means true;
legacy sink nodes become final; deserializer applies final flags after edges;
docs claim symmetric cross-version round-trip.

**Verification evidence:** Golden legacy/v0.5/malformed payloads plus semantic
round-trip assertions, not merely dictionary equality.

**Phase to address:** Phase 1 policy; Phase 5 implementation.

---

### Pitfall 9: Construction and Diagnostics Disagree With Runtime

**What goes wrong:** Direct construction works but builder, decorators,
factories, clone, deserialization, validators, Mermaid, PlantUML, or JSON drops
or mislabels final/mode metadata.

**Why it happens:** `core.py` concentrates duplicated paths and diagnostics use
a private immutable graph snapshot. Updating one public surface does not update
all projections.

**How to avoid:**

- Extend canonical normalization and immutable graph snapshots once; route
  every adapter through them.
- Preserve clone table independence and established immutable-value sharing.
- Keep structural sink (`terminal`) separate from explicit finality. Do not
  silently repurpose an existing JSON key or figure marker.
- Render internal/external self-edges distinctly without exposing private
  storage; retain escaping and diagnostic budgets.
- Cover builder auto-async and post-build immutability for new metadata.

**Warning signs:** Only direct-machine tests exist; clones lose mode; figures
mark every sink final; JSON and topology serialization disagree on “terminal.”

**Verification evidence:** Replay one scenario through every construction route
and compare runtime, snapshot, serialization, validation, and renderings,
including hostile identifiers and budget exhaustion.

**Phase to address:** Phase 5 for constructors/persistence and Phase 6 for
diagnostics/projections.

---

### Pitfall 10: Pure and Native Builds Share the Same Wrong Behavior

**What goes wrong:** Source and compiled tests agree on a bug, or a “pure” run
loads a stale extension. Users get missing fields, coerced booleans, divergent
exception behavior, or incorrect callback order despite parity claims.

**Why it happens:** mypyc native classes require fixed attributes and distinct
exception/subclass handling. Mode-to-mode equality does not prove correctness;
an environment flag does not prove loader origin.

**How to avoid:**

- Declare final/mode fields in slots/native attributes and exactly validate
  object-typed inputs before mutation.
- Use the reviewed non-native built-in-exception pattern for public rejection;
  update slots-policy authority deliberately.
- Use an independent required-value oracle covering callback order,
  result/stage/commit, timing, history, serialization, and invalid input.
- Install fresh pure and compiled wheels in neutral directories and verify SHA,
  version, origin, loader, architecture, and asserted mode first.

**Warning signs:** `FAST_FSM_PURE_PYTHON=1` is treated as origin proof; parity
tests lack fixed expected values; compiled CI only imports; exception repr/cause
identity differs.

**Verification evidence:** Contract-versioned artifact records match required
values for source, pure wheel, and compiled wheel; validators reject stale,
shadowed, detached, or malformed evidence.

**Phase to address:** Phase 7, with mypyc/type checks in each code phase.

---

### Pitfall 11: Completion Grows Into a Hidden Statechart Engine

**What goes wrong:** Final entry emits automatic events, drains a queue, fires
eventless transitions, invokes background work, or stabilizes a macrostep.
Internal mode expands to hierarchy; callback reentry is quietly queued.

**Why it happens:** SCXML and current `python-statemachine` combine final states
with completion events, queues, eventless microsteps, hierarchy, invocation,
and run-to-completion. Shared vocabulary can import the processing model.

**How to avoid:**

- Finality is flat state metadata, a query, and an outgoing-edge invariant.
- Preserve one caller-owned explicit trigger per attempt. No automatic done
  event, queue, scheduler, task supervisor, macrostep, or eventless loop.
- Keep callback reentry rejection and ownership rules unchanged.
- Restrict internal transitions to canonical self-targets.
- Treat bounded deferred events as a future milestone with its own threat model.

**Warning signs:** `_queue`, `done.state`, `stabilize`, `microstep`, or background
task concepts enter core; final tests await a second transition; internal mode
accepts another target.

**Verification evidence:** API/architecture diff has no queue/task storage or
automatic dispatch; final entry performs exactly one transition; reentry still
gets the established ownership error.

**Phase to address:** Phase 1 declares non-goals; all phases enforce; Phase 7
teaches the controller-owned alternative.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Add `final` only to `State.__init__` | Quick demo | Factory, serializer, clone, validator, figure drift | Never for release |
| Infer finality from empty outgoing table | No new metadata | Confuses completion with incomplete topology | Never |
| Branch on `source is target` | No new field | Mixed internal/external self-events impossible | Never |
| Reuse external commit unchanged internally | Less code | Restarts entry timing and misstates residency | Never |
| Catch rejection around all of `trigger()` | One handler | Hides post-commit truth and side effects | Never |
| Put new fields only in `to_dict()` | Visible export | Reader/runtime semantic loss | Throwaway spike only |
| Generalize into strategy objects | Tidy pipeline | Indirection/allocation and mypyc complexity | Never without evidence |
| Compare source checkouts | Easy timing | No installed/native proof | Exploratory only |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Priority selection | Expected rejection falls through | Only false eligibility falls through; rejection/exception terminate |
| Entry timing | Internal event resets clock | Preserve internal residency; reset at external self/final commit |
| History | Record only if state name changes | Record logical commit per frozen contract and expose mode truth additively |
| Failure observers | Notify per candidate or query | Notify once at failed-trigger boundary; queries remain observer-free |
| Builder/declarative | Bypass canonical normalization | Normalize exact values once and replay through registrar |
| Validation/visualization | Rename structural sinks final | Expose structural terminality and explicit finality separately |
| Serialization | Change state element type in place | Add fields/defaults and publish directional compatibility |
| `safe_trigger()` / `raise_if_failed()` | Expose raw cause text | Reuse structured result and opt-in redacted exception boundary |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Topology scan for termination | Query slows with graph | Current-state flag read | Large graphs/tight controller loops |
| Generic group path for singleton | Baseline rate drops | Direct `TransitionEntry` | Every ordinary trigger |
| Unconditional context allocation | GC/allocation rise | Failure-only allocation | High-frequency dispatch |
| Dispatch-time metadata validation | Latency depends on topology | Registration-time normalization | Every feature path |
| Final benchmark includes construction | Misleading slow result | Preconstruct pools; time trigger only | First report |
| Callback-unequal competitor fixture | Meaningless attractive ratio | Semantic preflight | Every mode comparison |
| Floating competitor package | “Current” silently means old | Exact isolated 2.5.0/3.2.1 lanes | Lock refresh/upstream release |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Log user rejection reason/cause by default | Tokens, PII, domain data leak | Stable safe code/message; cause hidden from text |
| Deserialize validators/callback code | Config becomes executable input | Inert flags and opaque condition references only |
| Accept truthy/coercible flags | Malformed input weakens native invariants | Exact-type validation before mutation |
| Bypass diagnostic budgets | Adversarial graphs consume resources | Existing immutable snapshot and budgets |
| Convert unexpected exceptions to rejection | Defects look like normal refusal | Catch narrow signal; preserve other causes/stages |
| Swallow cancellation | Cancelled work continues/falls back | Dedicated finalizer and bare re-raise |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Conflate terminal/final/terminated | Graph shape, intent, and runtime status blur | Final = metadata; terminal = sink; terminated = current is final |
| Change self-transition default | Existing resource lifecycle changes | Preserve external default; explicit per-edge internal mode |
| Say internal means “nothing happens” | Actions/history/errors get omitted | List exactly skipped and retained surfaces |
| Make rejection exception-only | Value-result callers need broad catches | Structured category; `raise_if_failed()` remains opt-in |
| Promise symmetric version compatibility | Older reader silently loses meaning | Directional matrix and minimum reader version |
| Start tutorial with async complexity | Core semantics look harder | Progressive controller-owned drone; async last |
| Imply final schedules shutdown | Application waits for nonexistent work | Controller checks query and stops its own resources |

## “Looks Done But Isn’t” Evidence Checklist

- **Final states:** Verify atomic rejection through every registration and load path.
- **Termination:** Verify inside entry and after every post-commit failure/cancellation.
- **Internal:** Verify omitted state hooks, retained transition surfaces/history,
  logical commit, and unchanged residency clock.
- **External self:** Verify full exit/commit/enter order and timer reset.
- **Rejection:** Verify no lower candidate/lifecycle, one observer, redacted text,
  and structured reason.
- **Queries:** Verify observer/history-free behavior and frozen exception policy.
- **Serialization:** Verify semantic round-trip, malformed input, and directional
  cross-version behavior.
- **Tooling:** Verify builder, declarative, clone, validators, JSON, figures,
  history, and graph snapshots.
- **Async:** Verify cancellation identity, commit/stage truth, ownership release,
  slot parity, and no leaked tasks.
- **Artifacts:** Verify independent required values in fresh installed pure and
  compiled wheels.
- **Performance:** Verify direct representation, topology independence, raw
  samples, and installed compiled floor.
- **Competitors:** Verify exact version/lock/adapter and semantics before ratios.
- **Scope:** Verify no queue, eventless, scheduler, completion-event, hierarchy,
  invocation, or task-supervision machinery.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Final edge published | HIGH | Stop release; centralize atomic invariant; rebuild adapters/fixtures |
| Internal mode resets timer/callbacks | HIGH after release | Freeze corrected lifecycle; mode-specific commit; migration note |
| Rejection falls through | HIGH | Treat as safety bug; stop selector; audit group/query/async paths |
| Committed outcome reported uncommitted | HIGH | Restore ADR-004 truth; audit history/state; never simulate rollback |
| Serialization loses semantics | HIGH | Version/document format; migration or fail-closed reader; regenerate fixtures |
| Fast path regresses | MEDIUM | Remove unconditional wrappers/allocations/scans; rerun installed proof |
| Diagnostic terms drift | MEDIUM | Restore legacy structural fact; add explicit final field |
| Tutorial owns runtime work | LOW before release | Move scheduling/shutdown to controller and smoke test |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Finality inferred / outgoing final edge | Phase 2 + Phases 5–6 | Generated construction matrix; atomic version/topology |
| Termination after callback suffix | Phase 2 | Stage-by-stage state/result/history/query truth |
| Internal/external collapse | Phase 3 | Callback order, timer, history, mixed-mode tests |
| Rejection falls through | Phase 4 | Singleton/group/query lower-candidate counters |
| Post-commit rejection mislabeled | Phase 4 | Injection at every lifecycle seam |
| Cancellation swallowed | Phases 3–4 + Phase 7 | Identity, ownership reuse, no fallback/leak |
| Singleton overhead | Phase 1 + Phase 7 | Structural assertion and fresh installed floor |
| Serialization loss | Phase 1 + Phase 5 | Golden payloads and directional matrix |
| Factory/tooling drift | Phases 5–6 | Cross-construction/projection conformance |
| Pure/native shared-wrong parity | Phase 7 | Required values plus origin/hash identity |
| Unfair/stale competitor | Phases 1 and 7 | Exact locks, semantic preflight, raw labels |
| Statechart drift | Phase 1 and every review | API/architecture diff proves flat explicit scope |
| Confusing guidance | Phase 7 | Sphinx doctest and drone smoke tests |

## Research Flags for Roadmap Planning

- **Phase 1:** Decide which pre-commit seams may raise expected rejection and
  what `can_trigger*()` does with it before implementation.
- **Phase 3:** Design the internal logical commit so history and
  `committed=True` stay truthful while `_state_entered_at` remains unchanged.
- **Phase 5:** Decide serialization compatibility explicitly; the unversioned
  old reader cannot be forced to honor fields it does not know.
- **Phase 6:** Preserve legacy structural-terminal outputs while adding explicit
  final and transition-mode projections through one settled snapshot.
- **Phase 7:** Keep installed singleton release policy separate from labelled
  feature-local and competitor observations until stable evidence exists.

## Sources

### Repository and Decision Sources — HIGH Confidence

- `.planning/PROJECT.md` — scope, performance identity, exclusions, and parity.
- `.planning/research/python-statemachine-gap-assessment.md` — semantic choices,
  non-goals, and phase order.
- `.planning/research/STACK.md` — integration seams, artifacts, benchmarks, pins.
- `.planning/codebase/CONCERNS.md` — adapter, async, diagnostic, security, and
  stale-native-shadow failure history.
- `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` — callback order,
  commit truth, finalization, history, and cancellation.
- `.specify/decisions/ADR-007-priority-topology.md` — direct singleton, atomic
  registration, ordered groups, and fallthrough boundary.
- `src/fast_fsm/core.py` — current slots, registrar, selector, lifecycle,
  history/clock, serialization, ownership, and query behavior.

### Primary External Sources — MEDIUM Confidence

- [python-statemachine 3.2.1 transitions](https://python-statemachine.readthedocs.io/en/v3.2.1/transitions.html)
  — external self versus internal behavior.
- [python-statemachine 3.2.1 guards](https://python-statemachine.readthedocs.io/en/v3.2.1/guards.html)
  — false conditions skip while validators raise before state change.
- [python-statemachine states](https://python-statemachine.readthedocs.io/en/v3.2.1/states.html)
  and [validations](https://python-statemachine.readthedocs.io/en/v3.2.1/validations.html)
  — finality, termination, outgoing-edge prohibition, and graph checks.
- [W3C SCXML](https://www.w3.org/TR/scxml/) — larger queue, completion-event,
  hierarchy, invocation, and run-to-completion processing model.
- [Python asyncio cancellation](https://docs.python.org/3/library/asyncio-exceptions.html#asyncio.CancelledError)
  — `BaseException` control flow that normally must be re-raised.
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html)
  and [compilation units](https://mypyc.readthedocs.io/en/stable/compilation_units.html)
  — fixed native fields and cross-boundary constraints.
- [JSON Schema object guidance](https://json-schema.org/understanding-json-schema/reference/object)
  — extension/unknown-property compatibility considerations.

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Final/lifecycle risks | HIGH | Canonical registrar plus accepted ADR-004 |
| Transition-mode risks | HIGH | Existing lifecycle, history, and clock seams |
| Rejection/fallthrough risks | HIGH | Explicit selector fallthrough and terminal paths |
| Tooling/serialization risks | HIGH | Current adapters and unversioned shape |
| Pure/native/performance risks | HIGH | Established artifact and mypyc contracts |
| External semantic benchmark | MEDIUM | Cross-checked primary docs; seam classification |
| Exact feature performance | LOW until implemented | Phase 7 must measure; no rates invented |

---
*Pitfalls research for: Fast FSM v0.5.0 Explicit Flat-FSM Semantics*
*Researched: 2026-09-15*
