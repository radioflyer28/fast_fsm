# Phase 21: Priority Contract & Atomic Registration - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the public priority-registration contract and immutable finite
candidate topology for one `(source, trigger)` slot. This phase covers safe
construction and atomic publication only; sync/async winner selection,
adapters, diagnostics, and documentation land in Phases 22–25.

</domain>

<decisions>
## Implementation Decisions

### One coherent transition API
- **D-01:** Evolve `add_transition()` with a keyword-only `priority` argument;
  do not introduce a candidate-specific registration API. Priority is a normal
  attribute of a transition, so a second API would create two competing models.
  — **Reversibility:** one-way — changing a published registration API would
  require a compatibility migration.
- **D-02:** `priority` accepts only exact non-boolean integers. It defaults to
  `0`; lower numbers have higher precedence; signed values and gaps are valid.
  Reject `bool`, numeric subclasses, floats, strings, and other coercible
  values rather than normalizing them.

### Deterministic candidate identity
- **D-03:** Registration order never participates in semantics. Distinct
  candidates with equal source, trigger, and priority fail before any topology
  is changed. An exact duplicate—same canonical source, trigger, target,
  condition object identity, and priority—is a no-op.
- **D-04:** Preserve the singleton fast path: a slot with one candidate stores
  a direct slotted `TransitionEntry`; only competing candidates promote the
  slot to a private immutable, priority-sorted group. Published groups are
  replacement values, never mutable lists. — **Reversibility:** costly — this
  representation is the contract consumed by runtime selection and all later
  topology projections.

### Atomic fan-out registration
- **D-05:** Normalize and validate the complete operation before publishing it.
  `add_transition` multi-source, `add_transitions`, bidirectional, emergency,
  and builder registration must either publish all affected candidate groups
  with one graph-version increment or leave every group and graph version
  unchanged.
- **D-06:** Clones retain the same entry/group values at clone time but have
  independent outer and per-source tables. Later registration on either
  machine must replace only its own slot and never mutate a group visible to
  the other clone.

### Contract honesty and scope separation
- **D-07:** Amend the blanket O(1)/one-transition claim in the project policy
  before adding candidate iteration. Lookup and singleton dispatch remain
  O(1); local group construction and eventual selection are O(k), with no
  unrelated graph scan or dispatch-time sorting. The runtime selection
  behavior itself belongs to Phase 22.
- **D-08:** Helpers that accept a priority carry it unchanged; their candidate
  resolution, declarative mapping, serialization, output, and telemetry use
  remain intentionally deferred to their roadmap phases.

### the agent's Discretion
- Names and private helper boundaries may follow existing `core.py` and mypyc
  conventions, provided they preserve the locked public semantics above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone contract
- `.planning/ROADMAP.md` §Phase 21 — goal, requirements, success criteria, and
  dependency boundary for atomic registration.
- `.planning/REQUIREMENTS.md` §Priority Registration — normative PRIO-01,
  PRIO-02, and PRIO-03 requirements and explicit exclusions.
- `.planning/PROJECT.md` §Current Milestone and §Constraints — one-file mypyc
  boundary, pre-production compatibility posture, and throughput constraint.
- `.planning/STATE.md` §Blockers/Concerns — planned amendment of the old
  blanket O(1)/single-transition contract.
- `.planning/research/SUMMARY.md` §§Executive Summary, Reconciled Decisions,
  and Architecture Approach — approved feature design and cross-phase risks.

### Core topology and transaction seams
- `src/fast_fsm/core.py` — `TransitionEntry`, `_PreparedTransition`,
  `_commit_transition_plan`, `add_transition`, registration helpers, clone,
  `FSMBuilder`, and the mypyc/slots boundary.
- `tests/test_graph_invariants.py` — graph-version and atomic registration
  behavior.
- `tests/test_ownership_concurrency.py` — ownership and failed-mutation
  invariants for registrar methods.
- `tests/test_builder.py` — builder staging and graph materialization
  expectations.
- `tests/test_mypyc_guard.py` — compilation-compatible class and ownership
  constraints.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TransitionEntry` and `_PreparedTransition` in `src/fast_fsm/core.py`:
  existing slotted entry and all-or-nothing prepared-plan seam to extend.
- `_commit_transition_plan` and `_graph_version`: established single-commit
  mutation mechanism for fan-out helpers.
- `StateMachine.clone`: already copies outer and inner transition dictionaries,
  providing the seam for group-value isolation.

### Established Patterns
- `StateMachine._transitions` is currently a two-level dictionary keyed by
  source name and trigger; registration canonicalizes states before mutation.
- `core.py` is the sole selectively compiled module and uses `__slots__` plus
  explicit mypyc guard tests; do not split the module or introduce runtime
  dependencies.
- Registrar methods acquire machine ownership once and delegate to private
  owned/planning bodies; maintain that structure for atomicity.

### Integration Points
- Phase 22 will consume the slot representation at trigger resolution.
- Builders and factory adapters ultimately materialize through the registrar;
  this phase must give them a lossless priority carrier without adding their
  parity behavior prematurely.
- `_GraphSnapshot` is the future projection seam for diagnostics and exports;
  later phases will flatten candidate groups through it rather than inspect
  storage variants directly.

</code_context>

<specifics>
## Specific Ideas

The motivating drone workflow uses one `telemetry_tick` event and lets the FSM
resolve safety candidates. A telemetry service may expose facts such as
`heartbeat_older_than(5)`, but it must not choose or dispatch a transition.
That example integration is deliberately Phase 25 work.

</specifics>

<deferred>
## Deferred Ideas

None — dynamic priorities, equal-priority tie breaks, runtime candidate
mutation, parallel async guard evaluation, serialization parity, and telemetry
event routing are already assigned to later or future scope.

</deferred>

---

*Phase: 21-Priority Contract & Atomic Registration*
*Context gathered: 2026-09-06*
