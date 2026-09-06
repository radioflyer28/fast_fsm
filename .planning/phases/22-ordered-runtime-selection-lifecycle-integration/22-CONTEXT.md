# Phase 22: Ordered Runtime Selection & Lifecycle Integration - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Consume Phase 21's direct-singleton or immutable ordered candidate group at
the synchronous and asynchronous dispatch boundary. Select exactly one fully
eligible candidate before any lifecycle work; preserve current pre-commit
failure, ownership, history, listener, and cancellation contracts. This phase
does not add construction/serialization/public-inspection parity, diagnostics,
or drone documentation.

</domain>

<decisions>
## Implementation Decisions

### Ordered eligibility and short-circuiting
- **D-01:** For a group, evaluate candidates in their already stored ascending
  numeric priority order. A candidate is eligible only when its transition
  guard, declarative guard (when applicable), and target-state permission all
  pass in that order. The first fully eligible candidate wins; later
  candidates must not be inspected after a winner. — **Reversibility:**
  costly — priority ordering and the three-stage eligibility model are the
  public semantics on which later constructors and diagnostic surfaces depend.
- **D-02:** A normal false/rejection at any eligibility stage falls through to
  the next candidate. Guard/declarative/permission exceptions terminate
  selection immediately using the established pre-commit failure-result path;
  they never fall through to a lower-priority candidate. The async path treats
  cancellation as a bare re-raise and also never evaluates a lower candidate.

### One selection before one lifecycle
- **D-03:** Resolve selection once per `trigger()` / `trigger_async()` attempt,
  before listeners, state callbacks, history, trace, or current-state
  mutation. Only the selected candidate enters the existing lifecycle, so an
  attempt has at most one lifecycle, committed history record, and
  success-observer sequence.
- **D-04:** Thread the selected candidate's priority through the existing
  internal result/history/trace path where Phase 22 owns that metadata, without
  adding a new public topology-inspection API. An exhausted group returns one
  uncommitted `selection`-stage failure and sends failure observers once; a
  missing trigger remains the distinct existing resolution failure.

### Sync/async and performance parity
- **D-05:** `can_trigger()` and `can_trigger_async()` apply the same ordered
  eligibility rules as dispatch but perform no lifecycle work or failure
  observation. Async candidates are awaited sequentially; parallel guard
  evaluation is out of scope because it would violate deterministic
  short-circuiting and user-code side-effect ordering. — **Reversibility:**
  costly — asynchronous ordering and cancellation behavior are an observable
  contract.
- **D-06:** Preserve direct O(1) singleton lookup/dispatch. Group selection is
  explicit local O(k), makes no copy or sort at dispatch time, and has an early
  performance proof separate from the existing singleton throughput floor.

### the agent's Discretion
- Private selection helper names, result-field plumbing, and exact test-file
  placement may follow existing `core.py`/mypyc conventions, provided they
  honor the fixed eligibility ordering, failure boundaries, and Phase 21 slot
  representation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone requirements and decisions
- `.planning/ROADMAP.md` §Phase 22 — normative goal and the four success
  criteria for ordered sync/async selection.
- `.planning/REQUIREMENTS.md` §Deterministic Resolution — SEL-01 through
  SEL-04 acceptance requirements.
- `.planning/PROJECT.md` §Current Milestone and §Constraints — existing API,
  single-file mypyc boundary, pre-production compatibility posture, and
  singleton throughput constraint.
- `.planning/research/SUMMARY.md` §Phase 22 — approved deliverables,
  avoidances, and cross-phase boundaries.

### Phase 21 storage and runtime contracts
- `.planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md`
  — D-01 through D-08 priority storage, atomicity, clone, and scope contracts.
- `.planning/phases/21-priority-contract-atomic-registration/21-RESEARCH.md`
  — resolved canonical-condition identity and fail-closed grouped-consumer
  boundary.
- `.planning/phases/21-priority-contract-atomic-registration/21-VERIFICATION.md`
  — verified singleton-or-group representation and intentional current
  fail-closed dispatch behavior.
- `.specify/decisions/ADR-007-priority-topology.md` — accepted topology and
  complexity decisions consumed by selection.
- `.specify/memory/constitution.md` and `.specify/memory/spr-core-api.md` —
  O(1) singleton/O(k) group and compiled API constraints.

### Core lifecycle and test seams
- `src/fast_fsm/core.py` — `StateMachine` and `AsyncStateMachine` trigger,
  resolution, condition/declarative/permission, lifecycle, result/history,
  listener, ownership, and mypyc boundaries.
- `src/fast_fsm/conditions.py` — sync/async condition contracts and exception
  behavior.
- `tests/test_graph_invariants.py`, `tests/test_async.py`,
  `tests/test_lifecycle_results.py`, `tests/test_ownership_concurrency.py`,
  `tests/test_mypyc_guard.py`, and `tests/test_performance_benchmarks.py` —
  selection, failure, ordering, native, and performance regression patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 21's `TransitionEntry | _TransitionGroup` slot union and frozen
  priority-ordered group in `src/fast_fsm/core.py` provide the only selection
  input representation.
- Existing sync/async resolution and lifecycle paths already centralize
  `TransitionResult`, failure observation, ownership, callbacks, and history;
  selection should feed those seams rather than duplicate lifecycle logic.
- Condition strategy types in `src/fast_fsm/conditions.py` expose the sync and
  awaitable guard boundaries needed for sequential evaluation.

### Established Patterns
- `core.py` is the sole selectively compiled module; new runtime helpers must
  remain explicit, slotted/type-safe, and compatible with mypyc.
- Phase 17–18 contracts distinguish pre-commit failures, one-time observer
  finalization, and bare async cancellation propagation.
- Tests favor real FSMs and observable result/state/callback order rather than
  mocking dispatch internals.

### Integration Points
- `StateMachine.trigger`, `AsyncStateMachine.trigger_async`, and their
  `can_trigger*` counterparts consume a lookup slot and are the Phase 22
  integration boundary.
- The existing execution/lifecycle runner accepts one resolved transition;
  selection must return exactly that winner or one failure, leaving public
  construction/projection seams for Phase 23.

</code_context>

<specifics>
## Specific Ideas

The motivating drone flow remains one telemetry event with priority candidates
such as critical fault, lost link, and low battery. The state machine—not an
external telemetry dispatcher—must determine the first eligible transition.
The simulated aircraft command example belongs to Phase 25 after the runtime
contract is proven.

</specifics>

<deferred>
## Deferred Ideas

None — public construction/declarative/serialization parity is Phase 23;
diagnostics/output is Phase 24; installed-artifact performance proof and drone
guidance are Phase 25. Dynamic priorities, equal-priority tie-breaking, and
parallel async guard evaluation remain out of scope.

</deferred>

---

*Phase: 22-Ordered Runtime Selection & Lifecycle Integration*
*Context gathered: 2026-09-06*
