# Domain Pitfalls: Priority-Aware Guarded Transitions

**Domain:** High-performance Python finite state machine with ordered guarded alternatives
**Project:** Fast FSM v0.4.0
**Researched:** 2026-09-06
**Overall confidence:** MEDIUM — codebase-specific risks are HIGH-confidence direct findings; external specification and runtime guidance is primary-source but MEDIUM under the research seam

## Risk Model

| Severity | Meaning for v0.4.0 | Release posture |
|----------|--------------------|-----------------|
| Critical | Can choose or report the wrong transition, become nondeterministic, corrupt lifecycle state, or leave an async machine unusable | Must be prevented before priority groups are exposed publicly |
| Moderate | Produces misleading topology, diagnostics, serialization, history, or performance claims without immediately committing the wrong state | Must be corrected before milestone verification |
| Minor | Creates avoidable API ambiguity, documentation debt, or cold-path inefficiency | Fix during integration/documentation unless evidence raises severity |

The defining safety boundary is **selection before lifecycle**. Candidate guards
and state permission determine one winner. Only after that winner is fixed may
Fast FSM execute before/exit/commit/enter/handler/listener stages. A false guard
is normal candidate elimination; a selected candidate's lifecycle failure is
not permission to try another transition.

## Critical Pitfalls

### Pitfall 1: Equal priorities quietly fall back to registration order

**What goes wrong:** Two candidates share one `(source, trigger, priority)`, and
the winner depends on which `add_transition()` call happened first, how a dict
was reconstructed, method discovery order, or how serialized rows were sorted.
The machine appears deterministic in one process while changing behavior after
refactoring or round-trip serialization.

**Why it happens:** Python dictionaries preserve insertion order and sorting is
stable, so registration order is an easy accidental tie-break. The W3C SCXML
specification and other state-machine libraries use document/declaration order,
but Fast FSM has explicitly chosen numeric priority because its graph can be
built through several adapters with no single source-document order.

**Consequences:** Safety rules can invert silently; pure and compiled artifacts
can expose different ordering bugs; graph version and diagrams may look valid
while runtime precedence is ambiguous.

**Prevention:**

- Define one scalar type and direction: non-boolean `int`, lower value wins.
- Reject a conflicting equal priority within each source/trigger group before
  any topology mutation.
- Decide explicitly whether an exactly identical repeated registration is an
  idempotent no-op; never let identity or insertion order decide a conflict.
- Sort once during the atomic topology commit and preserve the numeric priority
  in snapshots and serialized rows.
- Generate the same candidates in many registration orders and assert identical
  selection and export order.

**Detection:** Reversing registration order changes the selected target;
round-tripping through `to_dict()` changes behavior; tests use only already
sorted registrations.

**Phase:** Phase 21 — Priority Contract and Atomic Registration.

---

### Pitfall 2: An unconditional candidate makes lower rules unreachable

**What goes wrong:** A higher-priority transition has no condition, so it always
wins and every lower candidate is dead. A default-priority ordinary transition
can unintentionally shadow later safety rules, particularly when an existing
single edge is promoted into a candidate group.

**Why it happens:** An unconditional edge was harmless when it was the only
transition for a trigger. Once candidates are grouped, its position becomes an
implicit `else` branch. Default priority `0` can also outrank explicitly added
positive priorities.

**Consequences:** Guards are registered and rendered but never evaluated;
telemetry failsafes or exceptional paths cannot fire; users mistake topology
presence for reachability.

**Prevention:**

- Treat an unconditional transition as a catch-all candidate, not merely an edge
  with a missing condition.
- Validation must flag every lower-priority candidate following an unconditional
  candidate as unreachable.
- Documentation should place fallback candidates last and assign them the least
  preferred numeric priority.
- Consider rejecting rather than merely warning when an unconditional candidate
  is not last; resolve that policy before implementation.
- Include a specific migration example showing why an existing unguarded default
  must receive a lower precedence when competitors are added.

**Detection:** A guard call counter stays at zero; changing telemetry never
changes the target; a diagram shows multiple candidates while the validator
reports no shadowing.

**Phase:** Phase 21 for registration rules; Phase 24 for unreachable-candidate validation.

---

### Pitfall 3: Candidate rejection is confused with transition failure

**What goes wrong:** Each false guard fires `on_failed`, logs a failed
transition, or returns immediately. Lower candidates are never considered, or
observers see several failures followed by one success from a single trigger.

**Why it happens:** Current Fast FSM has exactly one candidate, so a false guard
is necessarily the trigger's final guard-stage failure. Reusing that helper
inside a candidate loop preserves the wrong abstraction level.

**Consequences:** Priority fallback does not work; observers overcount failures;
logs and audit trails contradict the final result; callbacks can mutate the
machine while selection is incomplete.

**Prevention:**

- Split private candidate evaluation from public failure finalization.
- A false transition/declarative guard or false `State.can_transition()` removes
  only that candidate and continues to the next priority.
- If all candidates reject, construct one overall guard-stage failure and notify
  failure observers exactly once.
- Preserve `can_trigger*()` as observer-free probing.
- Define guard/state-permission exceptions separately: the recommended contract
  is fail closed at the raising candidate and stop, retaining the cause; do not
  silently reinterpret broken safety logic as false.

**Detection:** `on_failed` receives one call per candidate; the error names only
the first false guard; a lower passing candidate is never reached.

**Phase:** Phase 22 — Sync/Async Selection and Lifecycle Integration.

---

### Pitfall 4: Lifecycle work begins before the winning candidate is fixed

**What goes wrong:** Before-transition listeners or source-exit callbacks run
for a high-priority candidate, then its later eligibility check fails and the
machine tries a lower candidate. User code observes lifecycle work for a
transition that was never selected. Worse, a post-commit or destination callback
failure can cause fallback into a second transition from a state that has
already changed.

**Why it happens:** It is tempting to reuse the existing full
`_trigger_owned()` body once per candidate instead of extracting a pre-lifecycle
selection seam.

**Consequences:** Duplicate external commands, impossible callback order,
history/state disagreement, two commits for one trigger, or a callback receiving
the wrong destination.

**Prevention:**

- Complete every candidate's transition guard, declarative guard, and
  target-specific state permission before entering the Phase 17 lifecycle.
- Invoke before/exit/commit/enter/declarative-handler/trigger/after callbacks
  exactly once for the selected candidate.
- Once lifecycle execution starts, any callback or commit failure returns that
  candidate's existing staged result. Never evaluate a lower candidate.
- Add a test matrix with failures at every lifecycle stage and counters on all
  lower candidate guards and callbacks; all must remain untouched after
  selection.
- Keep commit and optional history append in the existing no-user-code boundary.

**Detection:** a rejected candidate appears in callback logs; history contains
more than one record for one trigger; a lower guard runs after destination entry
or callback failure.

**Phase:** Phase 22 — Sync/Async Selection and Lifecycle Integration.

---

### Pitfall 5: Side-effecting guards make priority behavior unstable

**What goes wrong:** Guards consume queues, increment counters, update telemetry,
perform I/O, or depend on another guard having run. The result changes between
`can_trigger()` and `trigger()`, between candidate orders, or after adding an
unrelated higher-priority candidate.

**Why it happens:** `FuncCondition` deliberately accepts arbitrary user code.
Fast FSM cannot enforce referential transparency, and ordered alternatives make
evaluation order more visible than the current one-guard model.

**Consequences:** A preflight check can consume the only passing signal;
retries select another target; diagnostics or logging accidentally become
behavioral; users assume all guards run when first-match semantics short-circuit.

**Prevention:**

- Document guards as predicates that should be pure, idempotent, and cheap.
  Derived-fact providers may maintain external state, but checking a fact should
  not command the system or choose a transition outside the FSM.
- Guarantee each candidate guard is evaluated at most once within one public
  `can_trigger*()` or `trigger*()` call and only until the first eligible winner.
- Do not cache guard results across public calls; telemetry and time-derived
  facts may legitimately change.
- Sanitize kwargs once per trigger attempt and provide the same mapping content
  to every candidate so candidates do not receive order-dependent filtering.
- Use explicit counter-based tests to prove left-to-right short-circuiting.

**Detection:** calling `can_trigger()` changes the next `trigger()` result;
lower-priority counters increment after a winner; a guard issues aircraft or
network commands.

**Phase:** Phase 22 for runtime guarantees; Phase 25 for public guidance and examples.

---

### Pitfall 6: Async guards are launched concurrently or cancellation becomes fallback

**What goes wrong:** Competing async guards run through `gather()`, tasks, or
`as_completed()`. A lower-priority fast guard wins before a higher-priority slow
guard, losing explicit precedence. Alternatively, cancellation of an awaited
guard is caught as rejection and the next candidate runs.

**Why it happens:** Parallel guard evaluation looks like a latency optimization,
and broad exception handling obscures that cancellation is control flow. Python
documents that task cancellation injects `CancelledError` at an await point and
cleanup belongs in `finally` before propagation.

**Consequences:** nondeterministic target selection, leaked background tasks,
lower guards continuing after commit/cancellation, stuck ownership, or pure and
compiled async behavior drifting.

**Prevention:**

- Await candidates sequentially in priority order. Do not create tasks for
  candidate guards.
- On `CancelledError`, finalize the reached pre-commit cancellation boundary
  once, release ownership in `finally`, and re-raise the same cancellation.
- Never evaluate a lower candidate after cancellation or a raising guard.
- Test cancellation while waiting for each candidate position, including guards
  that delay or suppress cancellation; assert machine reuse afterward and no
  leaked tasks.
- Retain the existing event-loop/thread binding and causal reentrancy checks
  around the whole selection plus lifecycle operation.

**Detection:** `asyncio.all_tasks()` shows orphan candidate tasks; fastest guard
wins rather than lowest numeric priority; cancellation yields an ordinary false
result or leaves the machine busy.

**Phase:** Phase 22 — Sync/Async Selection and Lifecycle Integration.

---

### Pitfall 7: The selected candidate is absent from results, history, and observers

**What goes wrong:** Two candidates can share the same source, trigger, and even
destination while differing only in guard and priority. Existing
`TransitionResult`, `TransitionRecord`, and listener arguments identify only
state/trigger/target, so an audit cannot tell which rule won. A final all-rejected
failure likewise cannot explain that resolution found a group but no candidate
qualified.

**Why it happens:** Candidate identity did not exist in earlier milestones, and
adding priority only to registration/storage appears sufficient for state
movement.

**Consequences:** misleading telemetry/debug output, inability to reproduce a
safety decision, and observers attributing a command to the wrong rule.

**Prevention:**

- Decide whether selected priority is appended to `TransitionResult` and
  `TransitionRecord`, or exposed through another existing structured result
  surface. Prefer a nullable scalar field over changing callback signatures.
- Preserve the five existing positional result fields and append metadata with a
  default if compatibility is still desired outside duplicate semantics.
- Notify failure observers once for the overall attempt; do not expose condition
  object representations or telemetry values in error strings.
- Keep trace logging metadata-only. Candidate count/selected priority are safe
  bounded scalars, but condition and payload values remain excluded.
- Ensure listeners receive only the selected target and still run in Phase 17
  order.

**Detection:** two differently prioritized transitions produce identical history
records; a guard exception result cannot identify the candidate priority; trace
formatting logs condition repr or telemetry.

**Phase:** Phase 21 freezes structured identity; Phase 22 implements lifecycle/observer accuracy.

## Moderate Pitfalls

### Pitfall 8: Batch and fan-out registration silently collapse candidates

**What goes wrong:** `_commit_transition_plan()` continues using one
`Dict[(source, trigger), entry]`, so multiple candidates in one
`add_transitions()` batch overwrite each other before commit. An emergency
fan-out may update some sources and fail on a priority conflict in a later source.

**Prevention:** Build a complete per-key candidate plan, validate all priority
conflicts and endpoints, and publish all replacement groups plus one graph-version
advance atomically. Cover `add_transition`, batch, bidirectional, emergency,
builder construction, factories, and deserialization.

**Phase:** Phase 21 — Priority Contract and Atomic Registration.

---

### Pitfall 9: Builder and declarative adapters retain a single-transition model

**What goes wrong:** Direct registration works, but `FSMBuilder` drops priority,
auto-detects async from only one guard, or freezes after a partially failed build.
`DeclarativeState._handlers[trigger]` keeps only one method, so discovery order
overwrites candidate-specific conditions and handlers.

**Prevention:** Carry priority in every builder staging row and preflight every
candidate before publication. Extend the existing `@transition` decorator rather
than adding another decorator. Store a finite handler collection per trigger and
resolve it by canonical source/target/priority; include candidate identity in the
prepared declarative-guard marker. Test reversed method names/discovery order and
mixed sync/async candidates.

**Phase:** Phase 23 — Builder, Declarative, and Serialization Parity.

---

### Pitfall 10: Serialization cannot reattach the right condition

**What goes wrong:** `to_dict()` emits duplicate source/trigger rows without
priority, or `from_dict(..., conditions={trigger: guard})` applies one guard to
every candidate sharing that trigger. A round trip changes precedence or makes
every candidate test the same predicate.

**Prevention:** Serialize integer priority on every row and sort rows
deterministically. Define an exact candidate condition key such as
`(from_state, trigger, priority)`, with any trigger-only fallback documented as
applying broadly. Reject ambiguous mappings rather than guessing. Test JSON
round trips with several candidates sharing source, trigger, and target.

**Phase:** Phase 23 — Builder, Declarative, and Serialization Parity.

---

### Pitfall 11: Snapshot and clone flatten or share candidate groups

**What goes wrong:** `_graph_snapshot()` emits only a group's first candidate,
or `clone()` shallow-copies a mutable list so later registration in the clone
changes the original. Graph version may fail to advance when a group's order or
membership changes.

**Prevention:** Publish one immutable `_GraphTransition` row per candidate,
including priority, in deterministic order. Store candidate sequences as
immutable tuples or copy them on clone/mutation. Treat membership, priority,
target, and guard identity changes as topology changes; preserve exact no-op
behavior only for an explicitly identical registration.

**Phase:** Phase 23 — Builder, Declarative, and Serialization Parity.

---

### Pitfall 12: Diagnostics collapse candidates or call them nondeterministic

**What goes wrong:** `_DiagnosticGraph` or validators store targets in a set,
losing two candidates that share a destination. The current determinism check
reports multiple targets for one state/event as nondeterministic even when unique
priorities define one deterministic first-match decision. Diagrams omit priority
and make overlapping arrows indistinguishable.

**Prevention:** Preserve candidate multiplicity and priority in diagnostic edges.
Redefine structural determinism around unique priorities and ordered selection;
separately report overlapping guards as runtime-dependent but priority-resolved.
Render priority in JSON, Mermaid, PlantUML, Markdown, and reports using existing
escaping/budgets. Add shadowing and duplicate-priority diagnostics without
evaluating user guards during analysis.

**Phase:** Phase 24 — Candidate-Aware Diagnostics and Visualization.

---

### Pitfall 13: The group representation violates mypyc or slots policy

**What goes wrong:** A dynamic/dataclass-heavy group works in pure Python but
becomes a slower non-native class, fails mypyc, gains an instance `__dict__`, or
changes runtime type enforcement. A generic clever abstraction expands the
compiled boundary or breaks interpreted `Condition` subclasses.

**Prevention:** Keep hot candidate containers as explicit classes in `core.py`
with complete `__slots__` and concrete annotations. Keep `Condition` objects in
interpreted `conditions.py`; do not compile that module. Avoid metaclasses,
dynamic attributes, custom descriptors, or a generalized public candidate
protocol. Run mypy, native compilation, recursive slots audit, and identical
semantic tests against clean pure and compiled artifacts.

**Phase:** Phase 21 for a native representation probe; Phase 25 for installed-artifact proof.

---

### Pitfall 14: Performance claims hide local candidate complexity

**What goes wrong:** Documentation continues to call all triggers and transition
registrations O(1), benchmarks measure only a singleton whose first guard passes,
or candidates are sorted on every trigger. A last-match group can become much
slower while the existing throughput gate stays green.

**Prevention:** Preserve the two direct dictionary lookups, preorder on mutation,
and keep singleton storage as the fast path unless measurements justify a uniform
group. Document `O(1)` topology lookup plus `O(k)` candidate evaluation and local
group insertion. Benchmark first-match, last-match, and all-rejected groups at
2/4/8 candidates in pure and compiled modes. Retain the 200,000 ops/sec compiled
singleton floor and add environment-labelled candidate-count curves plus memory
measurements.

**Phase:** Phase 25 — Performance, Documentation, and Artifact Proof.

## Minor Pitfalls

### Pitfall 15: Priority accepts booleans, floats, or arbitrary comparables

**What goes wrong:** `True` aliases integer `1`, NaN breaks total ordering, and
objects serialize or compare differently across modes.

**Prevention:** Validate with `type(priority) is int`; allow signed integers but
document lower-wins semantics. Do not add enums or wrapper objects merely to
represent precedence.

**Phase:** Phase 21.

### Pitfall 16: Default priority creates an undocumented migration trap

**What goes wrong:** A legacy unguarded edge implicitly receives priority `0`,
then shadows explicitly numbered positive candidates, or two unannotated
duplicates collide unexpectedly.

**Prevention:** State the default prominently. Reject equal defaults visibly and
show how to renumber the existing edge as the fallback. Do not silently assign
monotonic registration-order priorities.

**Phase:** Phase 21 contract; Phase 25 migration documentation.

### Pitfall 17: Candidate count becomes an accidental denial-of-service vector

**What goes wrong:** Configuration-generated machines attach thousands of
expensive guards to one trigger. The graph is finite, but one dispatch is
effectively unbounded for a latency-sensitive caller.

**Prevention:** Do not impose an arbitrary runtime cap in v0.4 unless requirements
call for it, but expose group size in diagnostics and document O(k). Diagnostic
budgets must count every candidate edge. Users with strict latency requirements
should validate a project-specific maximum group size before deployment.

**Phase:** Phase 24 diagnostics; Phase 25 performance guidance.

## Phase-Specific Warnings

| Proposed Phase | Primary Pitfalls | Exit Evidence |
|----------------|------------------|---------------|
| **21. Priority Contract and Atomic Registration** | ties, implicit order, unconditional shadowing, batch collapse, invalid types, mypyc layout | Contract tests; reversed-order property tests; atomic batch/fan-out tests; native compile probe; graph-version assertions |
| **22. Sync/Async Selection and Lifecycle Integration** | false guards finalized too early, lifecycle-before-selection, side effects, parallel awaits, cancellation fallback, observer overcount | Sync/async conformance matrix; per-candidate counters; every-stage lifecycle fault injection; cancellation and machine-reuse tests |
| **23. Builder, Declarative, and Serialization Parity** | dropped priority, singular handler registry, ambiguous condition reattachment, mutable clone sharing | Direct/builder/declarative parity; failed-build repair; JSON round trip; clone independence; candidate-specific handler tests |
| **24. Candidate-Aware Diagnostics and Visualization** | edge collapse, false nondeterminism, hidden shadowing, missing diagram priority, diagnostic budget undercount | Snapshot multiplicity tests; deterministic validation; shadow warnings; escaped bounded Mermaid/PlantUML/JSON golden tests |
| **25. Performance, Documentation, and Artifact Proof** | singleton regressions, hidden O(k), stale complexity claims, pure/native divergence | Singleton floor; candidate curves; memory/slots evidence; full suite/docs; installed pure and compiled priority oracle |

## Cross-Phase Invariants

- One `(source, trigger)` dictionary lookup yields a finite, statically
  registered candidate set.
- Numeric priority—not registration order, condition timing, hash order, or
  target name—defines evaluation order.
- Candidate elimination performs no transition lifecycle or failure-observer
  work.
- Exactly one candidate can enter lifecycle for one public trigger attempt.
- False eligibility may continue; raised guard/state-policy errors and
  cancellation fail closed unless the requirements explicitly choose otherwise.
- Rejected candidates do not appear in history as transitions; the selected
  candidate remains auditable without exposing condition/payload data.
- Sync and async machines share topology/order semantics; async differs only by
  awaiting supported guards/callbacks sequentially.
- Snapshots, clones, serializers, validators, and renderers preserve every
  candidate and its priority.
- Singleton dispatch remains the measured fast path; priority groups are
  `O(k)` only in local candidate count and independent of total graph size.

## Sources

### Repository evidence (HIGH confidence)

- `src/fast_fsm/core.py` — current single-entry storage, atomic transition-plan
  commit, sync/async dispatch, lifecycle finalization, ownership, clone,
  serialization, builder, and singular declarative-handler registry
- `src/fast_fsm/_diagnostics.py`, `validation.py`, and `visualization.py` —
  snapshot projection, target-set collapse, current determinism definition, and
  bounded rendering
- `tests/test_transition_lifecycle.py`, `test_ownership_concurrency.py`,
  `test_graph_invariants.py`, `test_builder.py`, `test_async.py`, and
  `test_performance_benchmarks.py` — existing failure, cancellation, topology,
  parity, complexity, and throughput contracts
- `.specify/decisions/ADR-004-atomic-transition-lifecycle.md`,
  `ADR-005-safe-ownership-concurrency.md`, and `.specify/memory/spr-core-api.md`
  — accepted state-commit, observer, cancellation, ownership, snapshot, and
  compiled-boundary behavior

### External primary sources (MEDIUM confidence via research seam)

- [W3C SCXML Recommendation](https://www.w3.org/TR/scxml/) — enabled-transition
  conditions, ordered first-match selection, conflict filtering, and selection
  before execution
- [Python 3.10 asyncio tasks](https://docs.python.org/3.10/library/asyncio-task.html)
  — cancellation injection, cleanup in `finally`, propagation, and concurrent
  task behavior
- [Python 3.10 bisect](https://docs.python.org/3.10/library/bisect.html) — ordered
  insertion complexity and concurrent-mutation warning
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html)
  — fixed native attributes, interpreted subclass boundary, and dataclass
  efficiency caveat
- [mypyc differences from Python](https://mypyc.readthedocs.io/en/stable/differences_from_python.html)
  — compile-time typing, runtime enforcement, early binding, and explicit
  synchronization guidance

## Open Decisions That Block Safe Implementation

1. Is an exact repeated candidate registration idempotent, or does every equal
   priority raise? Conflicting equal priorities must always raise.
2. Does false `State.can_transition()` continue to the next candidate? The
   recommended answer is yes because it is pre-lifecycle eligibility.
3. Do guard/state-permission exceptions stop selection? The recommended answer
   is yes, preserving Fast FSM's current fail-closed error result.
4. Is a non-final unconditional candidate rejected or only reported by
   validation? Rejection gives the strongest safety guarantee; validation is
   less disruptive for programmatically assembled graphs.
5. Where is selected priority exposed for auditability—`TransitionResult`,
   `TransitionRecord`, both, or only snapshots/traces?
6. How does `from_dict(..., conditions=...)` uniquely address a candidate when
   several rows share one trigger?
