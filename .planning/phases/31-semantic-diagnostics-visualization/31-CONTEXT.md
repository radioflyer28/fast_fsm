# Phase 31: Semantic Diagnostics & Visualization - Context

**Gathered:** 2026-09-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Project the already-implemented final-state, transition-mode, and expected-rejection semantics through existing results, history, validation, tracing, JSON, Mermaid, and PlantUML. Keep every diagnostic deterministic, bounded, escaped, and separate from dispatch. Do not redesign runtime selection or construction, add a new event/status model, or do Phase 32's release benchmarking and progressive tutorial.

</domain>

<decisions>
## Implementation Decisions

### Completion Versus Graph Shape
- **D-01:** Explicit `State.final` is the only completion fact. A state with no outgoing edge but `final=False` remains a non-final sink; do not infer termination from topology.
- **D-02:** Preserve the existing topology-oriented dead/terminal outputs for compatibility, but label their meaning clearly and add separately named explicit-final and non-final-sink facts. Validator warnings and quality scoring should not penalize an intentional explicit final merely for lacking outgoing edges. — **Reversibility:** costly — validation and JSON output are public diagnostic contracts consumed by callers and evidence.
- **D-03:** The current-state termination query remains authoritative at runtime. Do not store a second derived finality flag in a result, history record, or public state snapshot where it could become stale after restore or direct control. Results/history retain their selected `internal` and rejection facts from Phases 28–29.

### Transition and Rejection Projection
- **D-04:** Carry `final` state metadata and per-edge `internal` mode as scalars through the existing immutable graph snapshot and interpreted diagnostic graph. Derive all cold validation/diagram/JSON facts from one captured graph rather than reading mutable runtime tables again.
- **D-05:** Diagnostic JSON adds explicit, JSON-native final and transition-mode fields without replacing existing topology/analysis keys. The per-transition mode must be directly intelligible, including external self-transitions; JSON must preserve deterministic ordering and the one-operation diagnostic budget.
- **D-06:** Trace expected rejection with its already validated bounded code, selected mode/priority when known, and finality only where known. Default trace fields must remain metadata-only; no exception message, raw payload, trigger text, callback object, or unvalidated redactor value leaks. Avoid additional work when tracing is disabled. — **Reversibility:** costly — diagnostic field names and confidentiality behavior are observed by log consumers.

### Diagram Semantics
- **D-07:** In both Mermaid and PlantUML, draw a completion marker only for an explicit final state. A non-final sink receives no completion arrow, so graph shape cannot masquerade as intentional termination.
- **D-08:** Label internal self-transitions distinctly from external self-transitions while preserving trigger, guard-name visibility, and priority. Non-self external edges keep their established notation. Use the existing opaque state IDs and language-specific escaping for all caller-controlled text.
- **D-09:** Keep renderer work and result accounting reserve-before-output. A budget failure raises the existing bounded exception rather than returning a partial diagram or JSON payload.

### the agent's Discretion
- Exact additive JSON field names, stable diagram label wording, and validator method/report names may be chosen during research/planning, provided the distinctions above are explicit and legacy keys remain truthful.
- Choose targeted tests and docs for each surface; Phase 32 owns the progressive drone tutorial and installed-artifact performance evidence.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase Contract
- `.planning/ROADMAP.md` §Phase 31 — goal, dependencies, and three success criteria.
- `.planning/REQUIREMENTS.md` §DIAG-01–DIAG-03 — required diagnostic and visualization outcomes.
- `.planning/PROJECT.md` — flat deterministic scope, performance boundary, and milestone decisions.

### Approved Research and Prior Semantics
- `.planning/research/FEATURES.md` §Construction, Runtime, and Tooling Parity — explicit finality versus traps, and diagnostics rendering without losing priority/timing/condition references.
- `.planning/research/ARCHITECTURE.md` — canonical scalar snapshot and cold diagnostic ownership.
- `.planning/phases/27-explicit-final-states/27-CONTEXT.md` — finality metadata, termination, and non-final sink distinction.
- `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md` — immutable selected mode, result/history, timing, and self-transition lifecycle.
- `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md` — bounded rejection code, result semantics, and safe observer behavior.
- `.planning/phases/30-builder-first-construction-persistence-parity/30-CONTEXT.md` — builder-primary and dictionary/snapshot compatibility boundaries.

### Existing Output Safeguards
- `.specify/memory/constitution.md` — project invariants for correctness, diagnostics, and performance.
- `.github/copilot-instructions.md` — authoritative quality gates and source/compiled parity requirements.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StateMachine._graph_snapshot()` and `_GraphTransition` in `src/fast_fsm/core.py` already capture deterministic transition order and `internal`; `State.final` is available on captured states.
- `_DiagnosticGraph`, `_DiagnosticBudget`, and `DiagnosticLimits` in `src/fast_fsm/_diagnostics.py` provide one interpreted, bounded projection.
- `FSMValidator` and `EnhancedFSMValidator` in `src/fast_fsm/validation.py` already analyze reachability, topology-only dead states, and quality; these must distinguish intentional finals.
- `to_json()`, `to_mermaid()`, and `to_plantuml()` in `src/fast_fsm/visualization.py` share one snapshot capture, opaque state IDs, escaping, and reserve-before-output budget checks.
- `TransitionResult`, `TransitionRecord`, and `_emit_fsm_trace()` in `src/fast_fsm/core.py` are the existing runtime-facing diagnostic surfaces.

### Established Patterns
- `core.py` does not import interpreted diagnostics; snapshot capture is on demand and dispatch remains direct.
- Existing JSON keeps topology and analysis separate, with snapshot order and optional preflighted dense adjacency.
- Default trace emits metadata-only fields, while any configured redactor output is validated before logging.

### Integration Points
- Add final indices/names and edge mode to the private scalar diagnostic graph, then consume that one projection in validators, JSON, and diagram renderers.
- Keep legacy dead-state APIs topology-oriented while introducing explicit final/non-final-sink reporting.
- Extend existing trace finalization sites only at established trace boundaries; keep pure and compiled behavior aligned.

</code_context>

<specifics>
## Specific Ideas

The user previously emphasized that the FSM library should own transition rules without external dispatch logic and preserve its decisive speed advantage. Diagnostic output should make the distinction between an explicit landing final, an internal telemetry self-update, an external self-transition, and an ordinary sink obvious without changing that runtime model.

</specifics>

<deferred>
## Deferred Ideas

- Phase 32 owns installed-artifact benchmarks, release evidence, and the progressive controller-owned drone tutorial.
- Rich localized rejection details, new observer families, and statechart/scheduler behavior remain outside this milestone scope.

</deferred>

---

*Phase: 31-semantic-diagnostics-visualization*
*Context gathered: 2026-09-19*
