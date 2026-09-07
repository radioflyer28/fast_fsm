# Phase 23: Construction, Declarative & Serialization Parity - Context

**Gathered:** 2026-09-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Make every existing construction and identity-preserving surface faithfully
carry the finite ordered candidate topology established in Phases 21–22.
This includes builders, declarative-state metadata and handlers, factories and
helpers, cloning, query/snapshot seams, and callable-safe dictionary
round-tripping. It does not add dynamic priorities, diagnostic rendering, or
drone documentation.

</domain>

<decisions>
## Implementation Decisions

### One topology across construction paths
- **D-01:** Existing construction APIs remain the public surface. Builders,
  `quick_build`, factory helpers, batch/bidirectional/emergency helpers, and
  declarative setup must replay priority-bearing candidate declarations through
  the same atomic registrar rather than maintain an adapter-specific transition
  model. Their row/declaration forms may gain an optional priority value without
  changing the ordinary default (`0`). — **Reversibility:** costly — divergent
  adapter topology would give callers different winner semantics for the same
  declared machine.
- **D-02:** A failed builder or factory construction remains unpublished and
  retryable: priority conflicts, malformed candidate data, and async preflight
  failures cannot overwrite staged handlers, freeze the builder, or expose a
  partial candidate group.

### Declarative candidate identity
- **D-03:** Declarative metadata must retain more than one handler declaration
  for a trigger. Handler resolution is candidate-specific: after Phase 22 has
  identified an entry, resolve only the matching target/priority declaration;
  never use a trigger-wide handler or guard that could be attached to a lower
  or different candidate. — **Reversibility:** costly — handler identity is an
  observable safety contract for priority groups.
- **D-04:** Sync and async declarative paths follow the same candidate identity
  rule and preserve their existing one-handler lifecycle behavior. Decorator
  and registration order must not decide precedence; stored numeric priority
  does.

### Callable-safe serialized identity
- **D-05:** `to_dict()` emits one explicit transition record per candidate in
  deterministic source/trigger/priority order. Each record preserves source,
  trigger, target, numeric priority, and an optional opaque condition reference;
  it never serializes a callable or condition implementation.
- **D-06:** `from_dict()` attaches supplied guards by the record's explicit
  opaque condition reference. Legacy bare-trigger condition mappings remain
  usable only when exactly one candidate matches; any ambiguous mapping raises
  clearly rather than reusing a guard across candidates. The condition-reference
  spelling and validation details may follow existing configuration conventions.
  — **Reversibility:** one-way — a wrong attachment can silently change a
  fail-safe winner, while explicit references make JSON/YAML topology portable
  and auditable.

### Coherent read and clone seams
- **D-07:** Clones preserve immutable candidate entries/groups and their
  priority/guard identities while retaining independent table ownership. Query
  helpers keep their documented high-level semantics (for example, trigger
  availability remains deduplicated), but target checks, topology snapshots,
  and serialization must inspect all candidates rather than require a singleton
  or silently collapse a group.
- **D-08:** Keep callback signatures and caller payloads unchanged. Priority
  remains candidate-derived metadata in results, history, and tracing; public
  construction/parity work must not smuggle it through callback kwargs.

### the agent's Discretion
- Choose private projection/helper names, exact typed row aliases, and focused
  test-file placement consistent with `core.py`'s mypyc and slots constraints.
- Preserve legacy serialized shapes whenever they are unambiguous; use explicit
  errors instead of heuristic attachment when a legacy shape is ambiguous.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope and contracts
- `.planning/ROADMAP.md` §Phase 23 — normative goal and four success criteria.
- `.planning/REQUIREMENTS.md` §Complete Library Parity — PAR-01 through PAR-03.
- `.planning/PROJECT.md` §Current Milestone, §Context, and §Constraints —
  one-file mypyc boundary, compatibility posture, and hot-path constraints.
- `.planning/research/SUMMARY.md` §Phase 23 — parity deliverables, avoidances,
  and the exact declarative/condition-key research flags.

### Locked priority behavior
- `.planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md`
  — registration, immutable groups, clone isolation, and phase boundaries.
- `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md`
  — ordered eligibility, one-lifecycle handoff, priority metadata, and
  singleton O(1)/group O(k) rules.
- `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md`
  — verified runtime selection/failure/query behavior to preserve.
- `.specify/decisions/ADR-007-priority-topology.md` — accepted topology,
  duplicate identity, and complexity contract.
- `.specify/memory/spr-core-api.md` — living API/priority/trace contract.

### Construction and topology seams
- `src/fast_fsm/core.py` — factories, `from_dict`/`to_dict`, clone, query
  helpers, `_GraphSnapshot`, declarative states, decorators, and `FSMBuilder`.
- `src/fast_fsm/conditions.py` — serializable-reference boundary around
  condition objects and sync/async guard types.
- `tests/test_builder.py`, `tests/test_async.py`, `tests/test_graph_invariants.py`,
  `tests/test_transition_lifecycle.py`, `tests/test_advanced_functionality.py`,
  and `tests/test_mypyc_guard.py` — public construction, clone, lifecycle, and
  compiled-boundary regression patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StateMachine.add_transitions()` and `_commit_transition_plan()` in
  `src/fast_fsm/core.py` already provide the atomic materialization seam for
  builder/factory rows.
- `TransitionEntry | _TransitionGroup`, Phase 22 selectors, and their
  result/history/trace metadata provide the canonical candidate identity.
- `FSMBuilder` already stages priority values and materializes through one
  batch registrar; declarative `_handlers` and `from_dict()` still encode the
  singular assumptions this phase must remove.

### Established Patterns
- `core.py` is the sole selectively compiled module. New records/helpers must
  remain explicitly typed, slotted where appropriate, and native-tested.
- Constructors collect topology before publication, and clone copies mappings
  while sharing immutable values; preserve those atomicity/ownership envelopes.
- `to_dict()` is topology-oriented and callables are supplied separately at
  `from_dict()` time; condition serialization remains forbidden.

### Integration Points
- Phase 24 will consume a candidate-complete topology snapshot rather than
  inspect singleton/group storage directly.
- Phase 25 will use the completed public construction semantics in the drone
  example and installed-artifact conformance evidence.

</code_context>

<specifics>
## Specific Ideas

The motivating drone controller must be able to declare or load several
`telemetry_tick` safety candidates without an external priority dispatcher.
Telemetry facts may be represented by guards, but serialized configuration may
name those guards only by opaque references; the live callable stays with the
application.

</specifics>

<deferred>
## Deferred Ideas

None — candidate-aware validation/rendering belongs to Phase 24, and the
drone example, documentation, benchmarks, and installed-artifact proof belong
to Phase 25. Dynamic priorities, equal-priority policies, runtime candidate
mutation, and callable serialization remain future scope.

</deferred>

---

*Phase: 23-Construction, Declarative & Serialization Parity*
*Context gathered: 2026-09-07*
