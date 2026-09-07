# Phase 24: Candidate-Aware Diagnostics & Output - Context

**Gathered:** 2026-09-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Make validation, graph analysis, adjacency data, and every existing structured
or human-readable diagnostic output faithfully represent the finite ordered
candidate topology from Phases 21–23. This phase does not change priority
selection, add a public topology API, relax output escaping or budget limits,
or add the drone documentation and installed-artifact proof reserved for Phase
25.

</domain>

<decisions>
## Implementation Decisions

### One immutable diagnostic projection
- **D-01:** Every validator, analysis helper, renderer, and export captures one
  immutable graph snapshot then derives its diagnostic graph solely from that
  snapshot. Consumers must not inspect private singleton-or-group runtime
  storage or recapture topology while producing one result. —
  **Reversibility:** costly — mixed projections would make reports internally
  inconsistent under mutation and violate the established snapshot/budget
  contract.

### Conservative candidate analysis
- **D-02:** A strictly increasing candidate group is deterministic. Equal or
  malformed priorities are validation errors. Shadow analysis must be
  conservative: report a lower candidate as provably shadowed only when the
  snapshot establishes that fact without evaluating user guards or permissions;
  otherwise distinguish a possible shadowing observation from a correctness
  error. — **Reversibility:** costly — false-positive safety diagnostics would
  cause users to distrust validation and may encourage removal of a live
  fallback.

### Candidate-complete output contract
- **D-03:** JSON, Mermaid, PlantUML, Markdown, generated paths, and adjacency
  data emit one edge/record per candidate in deterministic source, trigger,
  priority order. Numeric priority is explicit wherever a transition is shown;
  existing state, trigger, condition, title, Markdown, Mermaid, and PlantUML
  escaping remains the only text-encoding policy. — **Reversibility:** costly
  — output consumers need one stable, auditable representation of priority
  multiplicity rather than collapsed trigger pairs.

### Candidate-sized safety budgets
- **D-04:** Diagnostic edge counts, traversal work, result limits, and generated
  paths charge each candidate edge independently. On exhaustion, retain the
  current explicit incomplete-result/status behavior; never silently collapse
  candidates or emit an apparently complete partial projection. —
  **Reversibility:** costly — budgeting by collapsed slots would allow a large
  candidate group to evade the safety limits that protect diagnostics.

### the agent's Discretion
- Choose report field names and label punctuation that fit the established JSON,
  Mermaid, PlantUML, and Markdown contracts, provided priority is unambiguous,
  numeric, deterministic, and escaped only through the existing format-specific
  routines.
- Choose the narrowest static evidence for a provably shadowed candidate and
  place diagnostics-specific tests beside their existing validators/renderers.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and priority contracts
- `.planning/ROADMAP.md` §Phase 24 — normative goal and four diagnostic/output
  success criteria.
- `.planning/REQUIREMENTS.md` §Diagnostics and Output — DIAG-01 and DIAG-02.
- `.planning/PROJECT.md` §Current Milestone and §Constraints — compatibility,
  one-file mypyc boundary, and performance constraints.
- `.specify/decisions/ADR-007-priority-topology.md` — finite candidate
  representation, priority ordering, and explicit diagnostic/output boundary.
- `.specify/memory/spr-core-api.md` — living priority, serialization, query,
  and callback contract.

### Upstream topology and selection decisions
- `.planning/phases/21-priority-contract-atomic-registration/21-CONTEXT.md` —
  immutable singleton-or-group storage, exact priority validation, and
  complexity contract.
- `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-CONTEXT.md`
  and `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md`
  — ordered selection and truthful selected-priority metadata to preserve.
- `.planning/phases/23-construction-declarative-serialization-parity/23-CONTEXT.md`
  and `.planning/phases/23-construction-declarative-serialization-parity/23-VERIFICATION.md`
  — candidate-complete snapshot/projection boundary and verified construction
  parity.

### Diagnostic implementation seams
- `src/fast_fsm/core.py` — immutable `_graph_snapshot()` producer and candidate
  records; diagnostics must consume its projection rather than storage.
- `src/fast_fsm/_diagnostics.py` — diagnostic graph, budget ledger, adjacency,
  reachability, paths, and escaping primitives.
- `src/fast_fsm/validation.py` — validator, reports, adjacency exports, and
  structural analysis.
- `src/fast_fsm/visualization.py` — Mermaid, PlantUML, JSON, Markdown, and
  graph-analysis renderers.
- `tests/test_validation.py`, `tests/test_visualization.py`,
  `tests/test_diagnostic_budgets.py`, and `tests/test_graph_invariants.py` —
  output, escaping, limits, and snapshot regression patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StateMachine._graph_snapshot()` and `_graph_from_snapshot()` already form the
  immutable topology-to-diagnostic-graph seam.
- `_DiagnosticBudget`, `DiagnosticStatus`, `_dense_adjacency`,
  `_sparse_adjacency`, `_generate_paths`, and format-specific escaping helpers
  already provide bounded, fail-explicit diagnostic behavior.
- `FSMValidator` and the visualization module already capture a diagnostic
  graph once per top-level operation and render from its edge list.

### Established Patterns
- Diagnostic edges are snapshot-derived scalar records, while runtime dispatch
  retains its private direct-singleton/local-group selector shape.
- Renderers use opaque positional state identifiers plus format-specific
  escaping, never caller text as syntax.
- Existing limits account for work, result count, dense cells, and path
  expansion through one ledger and surface `DiagnosticStatus` when incomplete.

### Integration Points
- Phase 24 extends the snapshot edge metadata and diagnostic graph consumers;
  it must not reimplement construction or selection.
- Phase 25 will benchmark the completed candidate representation and document
  the drone controller against the truthful diagnostics/output behavior.

</code_context>

<specifics>
## Specific Ideas

The drone workflow’s priority choices must be inspectable in diagnostics and
diagrams, but the diagnostic surfaces remain read-only: they explain the
candidate topology and never become a telemetry policy or dispatcher.

</specifics>

<deferred>
## Deferred Ideas

None — performance claims, installed-artifact parity, public documentation,
and the complete drone example remain Phase 25 scope.

</deferred>

---

*Phase: 24-Candidate-Aware Diagnostics & Output*
*Context gathered: 2026-09-07*
