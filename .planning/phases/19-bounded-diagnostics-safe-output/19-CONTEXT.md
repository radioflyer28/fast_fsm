# Phase 19: Bounded Diagnostics & Safe Output - Context

**Gathered:** 2026-09-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Make validation, comparison, JSON analysis, Mermaid/PlantUML rendering, and
trace logging consume one stable graph view and produce correct, bounded,
explicitly safe results. This phase may add diagnostic limits, result metadata,
escaping helpers, and reversible logging configuration, but it does not change
runtime transition semantics, add a public topology serialization format, or
perform the installed wheel/sdist parity work reserved for Phase 20.

</domain>

<decisions>
## Implementation Decisions

### Snapshot Identity and Batch Results
- **D-01:** Every top-level validation, comparison, JSON-analysis, and diagram call captures exactly one immutable internal graph snapshot and passes that snapshot through all nested analysis/rendering. No nested helper may reread `_states`, `_transitions`, current runtime state, or graph version independently.
- **D-02:** Reachability always starts from the snapshot's declared initial state. The current runtime state may be reported separately, but it never substitutes for the initial state in structural analysis.
- **D-03:** Batch and comparison results preserve input cardinality and order with stable positional identities even when machine display names are duplicated. Names remain labels, not dictionary keys. — **Reversibility:** costly — changing identity after publishing the Phase 19 comparison schema would require downstream result consumers to migrate.
- **D-04:** Comparing zero machines succeeds with a documented empty structured result: empty entries/rankings, no best machine, and aggregate counts of zero. Undefined numeric aggregates are represented explicitly as `None`, never invented as zero and never computed by division.

### Deterministic Budgets and Graph Semantics
- **D-05:** Potentially expanding diagnostic work has a finite deterministic default budget based on counted graph operations/results, not wall-clock time. Public top-level diagnostic APIs accept additive keyword-only limit overrides; exact public helper/type names remain the planner's discretion.
- **D-06:** Structured diagnostic results expose whether analysis is complete, which budget was exhausted, and deterministic work/result counts. APIs whose established return type cannot safely carry partial metadata fail with one documented redacted diagnostic-budget exception; no API silently returns partial output. — **Reversibility:** costly — callers will rely on the complete/incomplete contract and stable failure boundary.
- **D-07:** Cycle membership is defined by strongly connected components: every state in every cyclic SCC is reported, including self-loops and cycles longer than two states. Output is deterministic and deduplicated; representative cycle paths may be additional evidence but are not the membership oracle.
- **D-08:** Longest-path diagnostics use memoized dynamic programming on a DAG. Cyclic graphs are condensed to an SCC DAG and report structural depth plus the interpretation used; the library does not promise the NP-hard exact longest simple path through a cyclic graph.
- **D-09:** Sparse adjacency/edge data is the default analysis representation. Dense N×N matrices remain an explicit compatibility/opt-in output and must be budget-checked before allocation. Generated test paths are separately bounded by both path count and expansion work.
- **D-10:** Budget defaults must complete ordinary existing test/doc examples while remaining small enough to make adversarial generated graphs deterministic in CI. Tests use exact counted-work boundaries, never timing sleeps or machine-speed assumptions.

### Collision-Free, Grammar-Safe Output
- **D-11:** Mermaid and PlantUML assign deterministic opaque node identifiers (for example, snapshot-order IDs) independently of labels. Distinct state names can never collide merely because punctuation sanitizes to the same text.
- **D-12:** Labels, triggers, conditions, titles, Unicode, newlines/control characters, quotes, brackets, comment markers, and directive-like text pass through separate Mermaid- and PlantUML-specific escaping functions. User text is always inert data and never emitted into identifier, directive, comment, or fence syntax unescaped. — **Reversibility:** costly — rendered text is a user-visible output contract and downstream snapshots may depend on deterministic encoding.
- **D-13:** Diagram and JSON ordering follows the immutable snapshot's deterministic ordering. Repeated calls on the same snapshot are byte-stable; live graph changes can affect only a subsequently captured snapshot.

### Redacted and Reversible Logging
- **D-14:** Default trace logging is metadata-only: fixed operation/stage/result categories, positional argument count, and sanitized keyword names may be emitted; trigger names, state names, positional values, keyword values, exception payloads, and object representations are redacted by default.
- **D-15:** Applications may provide an explicit redactor that receives the minimum structured event needed to produce safe logging fields. Redactor failure is fail-closed: emit a fixed redaction-failure category or suppress the event, and never fall back to raw values.
- **D-16:** `configure_fsm_logging()` never clears or mutates application-owned handlers. Library-created handlers are explicitly identifiable, repeated configuration replaces only library-owned configuration, propagation is deliberate and caller-selectable, and the call returns or exposes a reversible library-owned configuration handle that restores only library changes. — **Reversibility:** costly — application logging ownership and restoration become part of the public safety contract.
- **D-17:** `set_fsm_logging_level()` delegates to the same ownership-preserving configuration seam; no alternate helper may reintroduce handler clearing or raw trace formatting.

### Agent's Discretion
- Exact names and slot-backed shapes for private snapshot consumers, budget counters, structured analysis records, and reversible logging handles.
- Exact deterministic default limit values after adversarial tests calibrate them, provided limits are documented and do not depend on elapsed time.
- Whether legacy list/scalar helpers gain additive sibling APIs or keyword-only options, provided compatibility is preserved and exhaustion is never silent.
- Internal SCC implementation and grammar-escape tables, provided they are dependency-free, deterministic, and covered by hostile-input tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase Contract
- `.planning/ROADMAP.md` § Phase 19 — goal, dependency, and five success criteria.
- `.planning/REQUIREMENTS.md` — DIAG-01 through DIAG-08, OUT-01 through OUT-05, and TEST-07.
- `.planning/PROJECT.md` — safe-default posture, public compatibility, one-runtime-dependency limit, O(1) hot-path requirement, and compiled throughput floor.
- `.github/copilot-instructions.md` — repository workflow, compatibility, quality, documentation, mypyc, and performance gates.

### Upstream Contracts
- `.planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md` — immutable internal graph snapshot, declared initial state, deterministic ordering, and Phase 19 migration boundary.
- `.planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md` — redacted lifecycle result/log semantics and stable failure stages.
- `.planning/phases/18-safe-ownership-concurrency/18-CONTEXT.md` — one-snapshot ownership boundary, nonblocking async contract, redaction, and no automatic offload.
- `.planning/phases/18-safe-ownership-concurrency/18-VERIFICATION.md` — verified ownership/snapshot behavior Phase 19 must preserve.

### Current Diagnostic and Output Surfaces
- `.planning/codebase/ARCHITECTURE.md` — design-time tooling boundaries and current direct coupling to private dictionaries.
- `.planning/codebase/CONVENTIONS.md` — public compatibility, type, slots, testing, and documentation conventions.
- `.planning/codebase/CONCERNS.md` — reproduced diagnostic, visualization, and logging failure modes that sourced this phase.
- `src/fast_fsm/core.py` — `_GraphSnapshot`, graph-versioning seam, logger use, `configure_fsm_logging()`, and `set_fsm_logging_level()`.
- `src/fast_fsm/validation.py` — reachability, comparison, cycle, longest-path, dense-matrix, and path-generation behavior.
- `src/fast_fsm/visualization.py` — Mermaid, PlantUML, JSON-analysis, and document rendering behavior.
- `tests/test_validation.py` — established validation/score/comparison coverage.
- `tests/test_visualization.py` — established rendering and JSON-analysis coverage.
- `evidence/release-baseline.json` — current all-tests and coverage baseline to refresh after Phase 19.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StateMachine._graph_snapshot()` and slot-backed `_GraphSnapshot`/`_GraphTransition` already provide the canonical immutable tool-facing view Phase 19 should consume.
- `FSMValidator` and `EnhancedFSMValidator` centralize most analysis and export behavior, making a snapshot-backed constructor/factory the natural migration seam.
- `tools/phase16_isolated_verify.py` and the release baseline provide fresh pure/compiled and full-suite evidence without touching checkout-native shadows.
- Existing per-machine loggers and standard-library `logging` are sufficient; no new runtime dependency is needed.

### Established Patterns
- Runtime dispatch stays dictionary-indexed and O(1); all diagnostic traversal/allocation remains opt-in and outside the trigger hot path.
- Public behavior can be made safer before production, but existing imports/signatures remain available and additions should be keyword-only or sibling APIs.
- Results and errors use stable, redacted categories rather than embedding caller values.
- Tests use real machines, exact call/order/content assertions, generated adversarial graphs, and fresh pure/compiled origins rather than mocks or timing assumptions.

### Integration Points
- Snapshot capture connects `StateMachine._graph_snapshot()` to validators, comparison/batch helpers, `to_json()`, `to_mermaid()`, `to_plantuml()`, and Mermaid document helpers.
- One shared graph-analysis seam should provide reachability, SCC membership, condensed depth, sparse edges, and budget metadata to both validation and JSON output.
- Grammar-specific encoders sit between snapshot labels/edges and Mermaid/PlantUML line generation; opaque IDs are allocated once per render.
- Logging ownership connects trigger trace call sites, per-machine loggers, `configure_fsm_logging()`, `set_fsm_logging_level()`, and application-supplied handlers/redactors.

</code_context>

<specifics>
## Specific Ideas

- Count work deterministically (visited vertices, examined edges, emitted paths/cells) so boundary tests can assert exact exhaustion behavior.
- Treat SCC membership as the canonical answer and condensation depth as the documented cyclic-graph longest-path interpretation.
- Keep opaque node IDs boring and stable; preserve human-readable names only in escaped labels.
- Mark library-owned handlers rather than inferring ownership from handler type or formatter equality.

</specifics>

<deferred>
## Deferred Ideas

- A public versioned topology snapshot serialization contract remains FUTR-05.
- Installed wheel/sdist pure/native parity and final release publication evidence remain Phase 20.
- New graph query/product features, interactive diagram tooling, logging backends, and scheduler/offload behavior remain outside this milestone.

</deferred>

---

*Phase: 19-bounded-diagnostics-safe-output*
*Context gathered: 2026-09-02*
