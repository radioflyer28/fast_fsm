# Phase 31: Semantic Diagnostics & Visualization - Research

**Researched:** 2026-09-19
**Domain:** Python FSM semantic diagnostics, logging, and text diagrams
**Confidence:** HIGH for repository seams; MEDIUM for renderer syntax

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Explicit `State.final` is the only completion fact. A state with no outgoing edge but `final=False` remains a non-final sink; do not infer termination from topology.
- **D-02:** Preserve the existing topology-oriented dead/terminal outputs for compatibility, but label their meaning clearly and add separately named explicit-final and non-final-sink facts. Validator warnings and quality scoring should not penalize an intentional explicit final merely for lacking outgoing edges. — **Reversibility:** costly — validation and JSON output are public diagnostic contracts consumed by callers and evidence.
- **D-03:** The current-state termination query remains authoritative at runtime. Do not store a second derived finality flag in a result, history record, or public state snapshot where it could become stale after restore or direct control. Results/history retain their selected `internal` and rejection facts from Phases 28–29.
- **D-04:** Carry `final` state metadata and per-edge `internal` mode as scalars through the existing immutable graph snapshot and interpreted diagnostic graph. Derive all cold validation/diagram/JSON facts from one captured graph rather than reading mutable runtime tables again.
- **D-05:** Diagnostic JSON adds explicit, JSON-native final and transition-mode fields without replacing existing topology/analysis keys. The per-transition mode must be directly intelligible, including external self-transitions; JSON must preserve deterministic ordering and the one-operation diagnostic budget.
- **D-06:** Trace expected rejection with its already validated bounded code, selected mode/priority when known, and finality only where known. Default trace fields must remain metadata-only; no exception message, raw payload, trigger text, callback object, or unvalidated redactor value leaks. Avoid additional work when tracing is disabled. — **Reversibility:** costly — diagnostic field names and confidentiality behavior are observed by log consumers.
- **D-07:** In both Mermaid and PlantUML, draw a completion marker only for an explicit final state. A non-final sink receives no completion arrow, so graph shape cannot masquerade as intentional termination.
- **D-08:** Label internal self-transitions distinctly from external self-transitions while preserving trigger, guard-name visibility, and priority. Non-self external edges keep their established notation. Use the existing opaque state IDs and language-specific escaping for all caller-controlled text.
- **D-09:** Keep renderer work and result accounting reserve-before-output. A budget failure raises the existing bounded exception rather than returning a partial diagram or JSON payload.

### the agent's Discretion
- Exact additive JSON field names, stable diagram label wording, and validator method/report names may be chosen during research/planning, provided the distinctions above are explicit and legacy keys remain truthful.
- Choose targeted tests and docs for each surface; Phase 32 owns the progressive drone tutorial and installed-artifact performance evidence.

### Deferred Ideas (OUT OF SCOPE)
- Phase 32 owns installed-artifact benchmarks, release evidence, and the progressive controller-owned drone tutorial.
- Rich localized rejection details, new observer families, and statechart/scheduler behavior remain outside this milestone scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DIAG-01 | Users can interpret finality, transition mode, and expected rejection consistently in results, history, validation, tracing, and JSON output wherever each concept applies. | Existing result/history carriers, graph projection, validator scoring, and trace finalizers. [VERIFIED: `.planning/REQUIREMENTS.md:51-53`; `src/fast_fsm/core.py:633-655,678-708,307-367`] |
| DIAG-02 | Users can distinguish final states, internal transitions, and non-final sink states in Mermaid and PlantUML output. | Both renderers already use opaque IDs and escaped scalar labels; PlantUML currently marks sinks as final. [VERIFIED: `.planning/REQUIREMENTS.md:51-53`; `src/fast_fsm/visualization.py:47-70,115-234`] |
| DIAG-03 | Users receive deterministic, bounded diagnostic fields suitable for logs, tests, and serialized evidence. | One snapshot, one budget, reserved rendered rows, and fixed trace metadata are present. [VERIFIED: `.planning/REQUIREMENTS.md:51-53`; `src/fast_fsm/_diagnostics.py:107-227`; `src/fast_fsm/visualization.py:84-113,399-503`] |
</phase_requirements>

## Summary

The implementation should extend the existing scalar diagnostic projection and consume it across validators and renderers. The core snapshot already carries transition mode, but `_DiagnosticEdge` drops it; the snapshot also holds `State` objects whose `final` marker is immutable, but the diagnostic graph has no copied final flags. Add these scalars at the capture/projection seam, then derive explicit finals and non-final sinks from the same graph. [VERIFIED: `src/fast_fsm/core.py:821-856,1921-1958,944-971`; `src/fast_fsm/_diagnostics.py:80-105,197-227`]

The principal compatibility correction is semantic: `find_dead_states()` and JSON `analysis.reachability.terminal` currently mean no outgoing edge and must keep that meaning. Enhanced validation additionally warns and scores no-outgoing states as defects; explicit finals must be exempt from no-outgoing penalties while non-final sinks remain reportable. PlantUML currently draws a completion arrow for every sink, and Mermaid currently draws none; both should draw it only for `final=True`. [VERIFIED: `src/fast_fsm/validation.py:220-232,307-362,810-858,991-1064`; `src/fast_fsm/visualization.py:115-234,399-479`; locked D-01/D-02/D-07 in `31-CONTEXT.md:16-29`]

Results expose selected `internal`, priority, and rejection code; successful history records expose selected `internal` and priority. `is_terminated` reads current `State.final`. Trace has a fixed metadata-only envelope and currently emits priority but not these newer semantic facts. Extend the existing trace finalizers with scalar code/mode and known finality, including the redaction-failure fallback; preserve the early disabled-trace return and do not add a result/history finality cache. [VERIFIED: `src/fast_fsm/core.py:307-367,633-655,678-708,2534-2540,4450-4507,5572-5603`; locked D-03/D-06 in `31-CONTEXT.md:19-24`]

**Primary recommendation:** plan a scalar capture/projection change first, then validator/JSON and diagrams, then trace and a cross-surface parity/safety gate. [VERIFIED: `src/fast_fsm/_diagnostics.py:197-227`; `src/fast_fsm/visualization.py:84-113`; locked D-04–D-09 in `31-CONTEXT.md:21-29`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Final/mode capture | Canonical core snapshot | Interpreted diagnostic graph | Capture scalar truth under the existing ownership boundary; project once after capture. [VERIFIED: `src/fast_fsm/core.py:1900-1958`; `src/fast_fsm/_diagnostics.py:197-227`] |
| Reachability, sinks, quality | Interpreted validation | Canonical snapshot | Cold analysis already consumes one `_DiagnosticGraph` and shared ledger. [VERIFIED: `src/fast_fsm/validation.py:141-173,307-362,709-720`] |
| JSON and diagrams | Interpreted visualization | Diagnostic graph | All public renderers enter via `_capture_diagnostic_graph()`. [VERIFIED: `src/fast_fsm/visualization.py:84-89,115-234,399-503`] |
| Result/history/termination | Compiled-capable runtime core | — | Existing per-attempt carriers hold selected facts; current-state finality stays an O(1) query. [VERIFIED: `src/fast_fsm/core.py:633-655,678-708,2534-2540`] |
| Trace confidentiality | Compiled-capable runtime core | Application logger | `_emit_fsm_trace()` owns the fixed log record and optional validated redactor. [VERIFIED: `src/fast_fsm/core.py:250-267,307-367`] |

## Project Constraints (from AGENTS.md)

- Follow `.github/copilot-instructions.md` for all project workflows and gates; use GSD phase artifacts for GSD work and create/update GitHub Issues only on explicit request. [VERIFIED: `AGENTS.md:1-13`]
- Use `uv` for Python/package/test commands; maintain the direct O(1) singleton path, slots policy, and the four documented exceptions; preserve `*args, **kwargs`, constructor behavior, and the selective `core.py` mypyc boundary. [VERIFIED: `.github/copilot-instructions.md:31-68,273-303`]
- Run targeted tests during implementation, the full sequential suite once before push, blocking mypy, advisory ty, and relevant Ruff/docs gates. [VERIFIED: `.github/copilot-instructions.md:70-84,98-119,192-237`]
- Keep design-time validation outside dispatch and maintain pure/compiled parity. [VERIFIED: `.github/copilot-instructions.md:273-303`]
- Update public API docs and relevant SPR memory for public/behavior changes; merged ADRs are historical and append-only. [VERIFIED: `.github/copilot-instructions.md:214-237,295-303,310-345`]
- AGENTS.md normally requires an intended-work commit, safe pull/rebase, push, and up-to-date status at session end; the orchestrator explicitly owns those steps for this research task. [VERIFIED: `AGENTS.md:15-26`; parent task]

## Standard Stack

| Component | Version / authority | Purpose |
|-----------|---------------------|---------|
| Repository `core.py`, `_diagnostics.py`, `validation.py`, `visualization.py` | Current checkout | Reuse canonical capture, interpreted graph, ledger, validators, and renderers. [VERIFIED: `src/fast_fsm/core.py:1900-1958`; `src/fast_fsm/_diagnostics.py:80-227`; `src/fast_fsm/visualization.py:84-89`] |
| Python standard `logging`, `json`, `dataclasses` | Project Python `>=3.10` | Existing trace and JSON-native diagnostic output. [VERIFIED: `pyproject.toml:6-9`; `src/fast_fsm/core.py:307-367`; `src/fast_fsm/validation.py:1075-1107`] |
| `pytest` and `pytest-asyncio` | Existing dev dependencies, minimum `>=8.4.1` and `>=1.3.0` | Sync/async, safety, and exact budget tests. [VERIFIED: `pyproject.toml:12-21`] |

No new package installation is needed for this phase. [VERIFIED: `pyproject.toml:6-35`; locked D-04–D-09 in `31-CONTEXT.md:21-29`] **Package Legitimacy Audit:** not applicable; no external package is recommended. [VERIFIED: `pyproject.toml:6-35`]

## Architecture Patterns

### Data flow

```text
canonical state/entry tables
  -> one owned _graph_snapshot() capture
  -> scalar _DiagnosticGraph (state final flags, edge internal flags)
  -> one _DiagnosticBudget per top-level operation
     -> validation/report/quality
     -> JSON topology + analysis
     -> Mermaid / PlantUML / composed Markdown

selected runtime attempt -> existing TransitionResult / TransitionRecord
                         -> fixed trace metadata at public trigger boundary
```

This is the current on-demand capture boundary with the proposed scalar extensions; no diagnostic module is imported by `core.py`. [VERIFIED: `src/fast_fsm/core.py:1900-1958`; `src/fast_fsm/_diagnostics.py:1-15,197-227`; `src/fast_fsm/visualization.py:84-89`]

### Recommended implementation seams

1. Add a `tuple[bool, ...]` of final flags beside `state_names` in `_GraphSnapshot` and `_DiagnosticGraph`, populated while `_graph_snapshot_owned()` holds the ownership boundary. Add `internal: bool` to `_DiagnosticEdge`, copied from existing `_GraphTransition.internal`. This prevents post-capture `State` rereads from observing renamed/mutated objects and gives every consumer the same ordered scalar view. [VERIFIED: `src/fast_fsm/core.py:821-856,1921-1958`; `src/fast_fsm/_diagnostics.py:80-105,197-227`; `tests/test_diagnostic_contracts.py:203-243`]
2. Define cold graph predicates once: explicit final indices from captured flags; topology sinks from empty `forward`; non-final sinks from their set difference. Retain the legacy `dead_states` and `terminal` sets as topology sets. Expose named final/non-final-sink facts in `validate_completeness()` and `to_json()`; reserve work/results for each new traversal or emitted collection. [VERIFIED: `src/fast_fsm/_diagnostics.py:94-105`; `src/fast_fsm/validation.py:220-232,307-362`; `src/fast_fsm/visualization.py:408-419`; locked D-01/D-02 in `31-CONTEXT.md:16-19`]
3. Recommend diagnostic JSON keys `topology.final_states`, `topology.transitions[*].mode` with string values `internal`/`external_self`/`external`, and `analysis.reachability.non_final_sinks`. Keep `analysis.reachability.terminal` as the existing topological sink list. The three-value mode distinguishes an external self edge directly; keep `from`, `to`, `priority`, `has_guard`, and all existing keys. These names are Phase 31 design choices under discretion, not existing schema values. [VERIFIED: `src/fast_fsm/visualization.py:399-479`; locked D-02/D-05 and discretion in `31-CONTEXT.md:18,23,31-33`]
4. For validator scoring, skip no-outgoing warnings/errors and missing-transition scoring for an explicit final. Also inspect `_analyze_reachability()`'s "cannot return to initial" info and `_analyze_structure()`'s no-events/single-state warnings: an intentional initial final with no edges should not lose quality merely because it completes immediately. Preserve topology-oriented `find_dead_states()` and genuine unreachable warnings for compatibility. [VERIFIED: `src/fast_fsm/validation.py:722-858,991-1064`; locked D-02 in `31-CONTEXT.md:18`]
5. In Mermaid and PlantUML, emit `sN --> [*]` only for explicit final flags. Keep `sN` opaque IDs, original edge arrow, escaped trigger/guard labels, and priority; append a fixed `internal` or `external self` tag only to same-state edges. Every new marker must call `_append_rendered_line()` and reserve work before output. [VERIFIED: `src/fast_fsm/visualization.py:47-70,92-113,115-234`; locked D-07–D-09 in `31-CONTEXT.md:26-29`] [CITED: https://mermaid.js.org/syntax/stateDiagram.html] [CITED: https://plantuml.com/state-diagram]
6. Keep result and history dataclasses as they are. Add trace-only scalar fields at `_emit_fsm_trace()` and both public trigger call sites, using `TransitionResult.rejection_code`, `internal`, and `priority`. Derive finality from the canonical current state only where an attempt has reached a known state/commit boundary; represent unknown as `None` rather than guessing from a destination name. The trace event/stub and redaction-failure fallback must remain synchronized if the public redactor sees added scalars. [VERIFIED: `src/fast_fsm/core.py:182-202,307-367,633-655,678-708,2534-2540,4450-4492,5572-5603`; `src/fast_fsm/core.pyi:103-116`; locked D-03/D-06 in `31-CONTEXT.md:19-24`]

### Don't Hand-Roll

| Problem | Use existing seam | Why |
|---------|-------------------|-----|
| Finality inference | `State.final` copied at snapshot capture | Topological sinks are not completion. [VERIFIED: `src/fast_fsm/core.py:944-971`; locked D-01 in `31-CONTEXT.md:17`] |
| New event/status or result history flag | Existing `TransitionResult`, `TransitionRecord`, `is_terminated` | Carriers already hold selected mode/rejection, and derived finality can stale. [VERIFIED: `src/fast_fsm/core.py:633-655,678-708,2534-2540`; locked D-03 in `31-CONTEXT.md:19`] |
| Renderer-specific topology scan or budget | `_DiagnosticGraph` and `_DiagnosticBudget` | One snapshot/ledger already enforces deterministic bounded output. [VERIFIED: `src/fast_fsm/_diagnostics.py:94-227`; `src/fast_fsm/visualization.py:84-113`] |
| New trace logger or payload formatter | `_emit_fsm_trace()` and validated redactor | Fixed metadata envelope already limits disclosure. [VERIFIED: `src/fast_fsm/core.py:235-267,307-367`] |

## Common Pitfalls

| Failure | Prevention / verification |
|---------|---------------------------|
| PlantUML sink arrows pretend every no-outgoing state completed. | Replace the `has_outgoing` based completion loop with captured explicit final flags; test reachable and orphan non-final sinks. [VERIFIED: `src/fast_fsm/visualization.py:208-234`; locked D-01/D-07 in `31-CONTEXT.md:17,27`] |
| Mermaid lacks completion markers even for explicit finals. | Add final marker rows after state declarations or edges in stable snapshot order, with result/work reservation. [VERIFIED: `src/fast_fsm/visualization.py:135-168`; locked D-07/D-09 in `31-CONTEXT.md:27-29`] |
| Final-state absence of outgoing transitions lowers structural and completeness scores through several issue paths. | Exempt intentional finals in `_analyze_completeness()` and no-return reachability info; check single-final/no-events structure handling, dense blended score, and JSON quality. [VERIFIED: `src/fast_fsm/validation.py:722-858,991-1064`; `src/fast_fsm/visualization.py:338-396`] |
| A later live `State.final` read mixes graph epochs. | Copy final flags in `_graph_snapshot_owned()`; extend the existing post-capture mutation tests. [VERIFIED: `src/fast_fsm/core.py:1900-1958`; `tests/test_diagnostic_contracts.py:203-243`; `tests/test_output_safety.py:196-235`] |
| Adding mode to dense transition records breaks supplied-matrix exact comparison or existing exact-shape tests. | Treat adjacency representations as compatibility contracts; if enriched, update `_validate_adjacency_matrix()` and document input compatibility, or keep the canonical JSON transition row as the mode-bearing surface. [VERIFIED: `src/fast_fsm/_diagnostics.py:438-532`; `src/fast_fsm/visualization.py:586-652`; `tests/test_diagnostic_contracts.py:832-849`] |
| Extra diagrams/JSON fields bypass exact result budgets. | Reserve every new collection entry and physical line before append; test exact limit and one less, including composed Mermaid document. [VERIFIED: `src/fast_fsm/_diagnostics.py:144-194`; `src/fast_fsm/visualization.py:107-113,560-578`; `tests/test_output_safety.py:480-516`] |
| A fixed mode label is safe, but interpolated caller text can inject diagram syntax; a redactor can return unsafe values. | Keep `_escape_mermaid_text()`/`_escape_plantuml_text()`, opaque IDs, and `_validate_fsm_trace_output()`; add hostile labels and secret-bearing exception/payload tests. [VERIFIED: `src/fast_fsm/visualization.py:47-70`; `src/fast_fsm/core.py:250-267`; `tests/test_output_safety.py:150-170`] |
| Redaction failure leaks new fields or missing trace facts differ in sync/async paths. | Update fixed fallback and both trigger sites together; assert LogRecord key set and no payload/exception text. [VERIFIED: `src/fast_fsm/core.py:307-367,4450-4492,5572-5603`; `tests/test_logging_config.py:735-788`] |

## Code Examples

Current safe output pattern to extend; line names below are existing source values, not a proposed new schema. [VERIFIED: `src/fast_fsm/visualization.py:107-113,152-166`]

```python
budget.reserve_work(stage="mermaid.edge")
_append_rendered_line(
    lines, budget, stage="mermaid.edge",
    line=f"    {state_ids[edge.from_index]} --> {state_ids[edge.to_index]} : {label}",
)
```

The existing trace function returns before constructing its fields when disabled, then constructs only fixed metadata and validates optional redactor output. [VERIFIED: `src/fast_fsm/core.py:307-367`]

```python
if not logger.isEnabledFor(_FSM_TRACE_LEVEL):
    return
trace_fields: Dict[str, object] = {
    "trace_operation": operation,
    "trace_stage": stage,
    "trace_result": result,
    "trace_arg_count": len(positional_args),
    "trace_keyword_names": _trace_keyword_names(keyword_args),
    "trace_priority": priority,
}
```

## State of the Art

| Existing behavior | Phase 31 behavior | Evidence |
|-------------------|-------------------|----------|
| PlantUML completion arrow means no outgoing edge; Mermaid has no completion arrow. | Both mean explicit final only. | [VERIFIED: `src/fast_fsm/visualization.py:115-234`; locked D-07 in `31-CONTEXT.md:27`] [CITED: https://mermaid.js.org/syntax/stateDiagram.html] [CITED: https://plantuml.com/state-diagram] |
| Diagnostics know source/target/priority but omit edge mode and copied final flags. | One scalar graph carries both semantics. | [VERIFIED: `src/fast_fsm/_diagnostics.py:80-105,197-227`; locked D-04 in `31-CONTEXT.md:22`] |
| Trace contains selected priority but omits rejection code, mode, and finality. | Fixed scalar metadata adds known facts without raw text. | [VERIFIED: `src/fast_fsm/core.py:307-367,4450-4492`; locked D-06 in `31-CONTEXT.md:24`] |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| — | No training-only factual claims were used. Proposed additive names and label wording are explicitly recommendations under Phase 31 discretion. | Architecture Patterns | Planner may choose alternate names if all distinctions remain explicit. |

## Open Questions (RESOLVED)

1. **RESOLVED — mode metadata stays on canonical diagnostic JSON transition rows.** Plan 31-01 adds `topology.transitions[*].mode` with `internal`/`external_self`/`external` values. Sparse and dense adjacency remain topology-only compatibility projections; this avoids changing supplied-matrix validation or exact adjacency row shape. [VERIFIED: `src/fast_fsm/visualization.py:426-454,586-652`; `src/fast_fsm/_diagnostics.py:438-532`; locked D-05 in `31-CONTEXT.md:23`]
2. **RESOLVED — trace finality means the authoritative current state, not the uncommitted destination.** Plan 31-04 uses `trace_current_final`, derived at the owned trigger boundary; a rejection never claims that a proposed destination committed. [VERIFIED: `src/fast_fsm/core.py:3932-3956,4450-4492,5572-5603`; locked D-03/D-06 in `31-CONTEXT.md:19,24`]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | Python test/typecheck/doc commands | yes | 0.12.17 on research host | — [VERIFIED: `uv --version` executed 2026-09-19] |
| Python and pytest | Implementation and verification | yes | Python 3.12.10; pytest 8.4.1 | `uv sync --locked --all-groups` if environment changes. [VERIFIED: `uv run python --version` and `uv run pytest --version` executed 2026-09-19; `pyproject.toml:6-21`] |
| Mermaid / PlantUML CLI | Syntax rendering | Not required by existing test suite | — | Assert generated text and escaping; optional visual inspection [VERIFIED: `tests/test_visualization.py:409-575`; `tests/test_output_safety.py:150-170`] |

## Validation Architecture

### Test framework

| Property | Value |
|----------|-------|
| Framework | Existing pytest with pytest-asyncio. [VERIFIED: `pyproject.toml:12-21,54-60`] |
| Quick command | `uv run pytest tests/test_diagnostic_contracts.py tests/test_visualization.py tests/test_validation.py tests/test_output_safety.py tests/test_logging_config.py -x -q` [VERIFIED: `.github/copilot-instructions.md:70-84,182-209`; `tests/test_output_safety.py:480-516`] |
| Full command | `uv run pytest tests/ -x -q` sequential. [VERIFIED: `AGENTS.md:7-11`; `.github/copilot-instructions.md:70-84`] |

### Requirements to tests

| Requirement | Behavior and edge cases | Test type / location | Existing coverage |
|-------------|-------------------------|----------------------|-------------------|
| DIAG-01 | Explicit final versus non-final sink; topology legacy `dead_states`/`terminal` still truthful; ordinary and initial-only finals not penalized in structural/completeness/dense blended score; results/history retain their selected facts. | Unit: `tests/test_validation.py`, `tests/test_diagnostic_contracts.py`, `tests/test_final_states.py`, `tests/test_transition_modes.py`, `tests/test_expected_rejection.py` | Existing framework and carriers; semantic projection assertions need Wave 0 additions. [VERIFIED: `src/fast_fsm/validation.py:307-362,722-858,991-1064`; `src/fast_fsm/core.py:633-655,678-708`] |
| DIAG-01 | Sync/async trace success, unknown selection, expected rejection, guard failure/cancellation; code/mode/priority/finality fields, disabled trace, redactor fail closed. | Unit/async: `tests/test_logging_config.py`, `tests/test_expected_rejection.py` | Existing confidentiality and priority tests; new field matrix needed. [VERIFIED: `tests/test_logging_config.py:415-477,735-790`; `src/fast_fsm/core.py:307-367,4450-4492,5572-5603`] |
| DIAG-02 | Both diagrams: explicit landing final marker, non-final sink without marker, internal and external self labels, guard/priority, hostile text. | Unit: `tests/test_visualization.py`, `tests/test_output_safety.py` | Existing PlantUML sink expectation must change; new semantic matrix needed. [VERIFIED: `tests/test_visualization.py:409-475`; `tests/test_output_safety.py:150-170,480-516`] |
| DIAG-03 | One snapshot under late mutation; deterministic bytes/order; exact and one-less work/result limits, composed document, JSON serializability; pure/native scalar parity. | Unit/integration: `tests/test_diagnostic_contracts.py`, `tests/test_output_safety.py`, `tests/test_mypyc_guard.py` | Existing capture/budget/native harness; extend with final/mode/code truth. [VERIFIED: `tests/test_diagnostic_contracts.py:203-260,814-865`; `tests/test_output_safety.py:196-235,480-516`; `tests/test_mypyc_guard.py:738-748`] |

### Sampling and Wave 0 gaps

- Per implementation task: run the touched file's targeted pytest module(s). Per wave: the quick command above. Phase gate: full suite, Ruff on changed Python, blocking `task typecheck-mypy`, advisory `task typecheck-ty`, slots policy, and docs build if public docs changed. [VERIFIED: `.github/copilot-instructions.md:40-84,98-119,192-237`]
- Wave 0: add focused semantic tests to the existing modules above before changing behavior; no new test framework or fixture file is needed. Include a pure/compiled oracle for snapshot final flags and edge mode, and update existing exact PlantUML/budget expectations. [VERIFIED: `tests/test_visualization.py:409-475`; `tests/test_output_safety.py:480-516`; `tests/test_mypyc_guard.py:738-748`]

## Security Domain

`security_enforcement` is not explicitly false in `.planning/config.json`, so this section applies. [VERIFIED: `.planning/config.json:1-36`] Use ASVS 5.0 chapter names as a threat-model lens for this library phase; this is not a claim of ASVS certification. [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json]

| ASVS category | Applies | Control |
|---------------|---------|---------|
| V1 Encoding and Sanitization | yes | Use sink-specific Mermaid, PlantUML, and Markdown escaping immediately before output. [VERIFIED: `src/fast_fsm/visualization.py:47-82`] [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x10-V1-Encoding-and-Sanitization.md] |
| V2 Validation and Business Logic | yes | Enforce exact finite diagnostic limits and validated bounded rejection codes; do not infer finality from graph shape. [VERIFIED: `src/fast_fsm/_diagnostics.py:31-54,164-194`; `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md:27-37`; locked D-01 in `31-CONTEXT.md:17`] [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.json] |
| V16 Security Logging and Error Handling | yes | Keep fixed metadata-only trace, validated redactor output, and redacted budget failures. [VERIFIED: `src/fast_fsm/core.py:250-267,307-367`; `src/fast_fsm/_diagnostics.py:70-77`] [CITED: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md] |
| Authentication, session, access control, cryptography | no direct phase interface | Inspected diagnostic functions operate on caller-supplied in-process FSM objects and add no such interface. [VERIFIED: `src/fast_fsm/visualization.py:84-89,240-337,482-503`; `src/fast_fsm/validation.py:118-173`] |

| Threat pattern | STRIDE | Mitigation |
|----------------|--------|------------|
| Mermaid/PlantUML/Markdown syntax injection through state, trigger, guard, or title | Tampering | Reuse each language's existing scalar escaper and opaque positional ID; test hostile corpus. [VERIFIED: `src/fast_fsm/visualization.py:47-82`; `tests/test_output_safety.py:150-170`] |
| Exception/payload/trigger leakage via new trace metadata | Information disclosure | Emit only validated code and fixed scalar facts; preserve early trace return and fallback field whitelist. [VERIFIED: `src/fast_fsm/core.py:235-267,307-367`; locked D-06 in `31-CONTEXT.md:24`] [CITED: https://docs.python.org/3.12/library/logging.html] |
| Large graph or dense output consumes unbounded memory | Denial of service | Reserve work/results/dense cells before construction; raise `DiagnosticBudgetExceeded` with scalar-only status. [VERIFIED: `src/fast_fsm/_diagnostics.py:31-77,144-194`; `src/fast_fsm/visualization.py:107-113,399-479`] |

## Sources

### Primary (HIGH confidence)
- Repository source of truth: `src/fast_fsm/core.py`, `_diagnostics.py`, `validation.py`, `visualization.py`, `core.pyi`; read 2026-09-19.
- Project contracts: `AGENTS.md`, `.github/copilot-instructions.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, Phase 31 `CONTEXT.md`; read 2026-09-19.
- Existing tests: diagnostic, output safety, visualization, validation, logging, final-state, mode, rejection, and mypyc guard modules; read 2026-09-19.

### Official documentation (MEDIUM confidence)
- https://mermaid.js.org/syntax/stateDiagram.html — start/end marker syntax; checked 2026-09-19, publication date not shown.
- https://plantuml.com/state-diagram — state/final/self-arrow syntax; checked 2026-09-19, publication date not shown.
- https://docs.python.org/3.12/library/logging.html — `extra` field collision guidance; checked 2026-09-19, versioned documentation.
- https://github.com/OWASP/ASVS/blob/master/5.0/en/0x10-V1-Encoding-and-Sanitization.md — versioned output encoding chapter; checked 2026-09-19.
- https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.json — versioned validation chapter; checked 2026-09-19.
- https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md — versioned logging/error chapter; checked 2026-09-19.

## Metadata

**Confidence breakdown:** Standard stack HIGH (repository dependencies), architecture HIGH (read implementation), renderer syntax MEDIUM (official documentation), pitfalls HIGH (source and tests).
**Research date:** 2026-09-19
**Valid until:** 2026-10-19 for repository-local planning; recheck after implementation changes.
**Research seam note:** `research-plan` and `classify-confidence` were run. Context7 tools/CLI were unavailable; official documentation was found through web search. The optional `research-store put` cache write failed because the configured global cache lies outside the writable sandbox; this does not affect this file's cited findings.
