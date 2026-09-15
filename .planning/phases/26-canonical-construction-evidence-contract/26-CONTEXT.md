# Phase 26: Canonical Construction & Evidence Contract - Context

**Gathered:** 2026-09-15
**Status:** Ready for planning
**Mode:** Auto-generated (pure infrastructure phase)

<domain>
## Phase Boundary

Establish one atomic topology normalization, validation, and publication seam
for every retained construction adapter, and establish reproducible,
semantically preflighted comparison lanes for exact `python-statemachine`
2.5.0 and 3.2.1 installations. This phase creates the foundation and evidence
contract; final-state, internal-transition, and expected-rejection runtime
semantics belong to later phases.

</domain>

<decisions>
## Implementation Decisions

### the agent's Discretion

All implementation choices are at the agent's discretion because this is a
pure infrastructure phase. Preserve the approved constraints: `core.py`
remains the single mypyc compilation unit, topology publication is atomic,
the direct singleton dispatch path is untouched, competitor dependencies stay
outside ordinary CI, and evidence records exact versions, origins, semantic
preflight outcomes, and unsupported cells.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `StateMachine._normalize_transition_request()`, `_PreparedTransition`, and
  `_commit_transition_plan()` already form the closest normalization and
  immutable-publication pipeline in `src/fast_fsm/core.py`.
- Existing direct, batch, builder, factory, declarative, clone, and dictionary
  construction paths provide the adapter inventory that must converge on the
  canonical seam.
- `tools/artifact_conformance.py`, `tools/release_evidence.py`, and the existing
  `benchmarks/` runners provide established bounded evidence formats and
  environment-labelled reporting patterns.

### Established Patterns

- Normalize exact public values and canonical endpoints before mutation, merge
  into immutable local transition slots, and publish once with one graph-version
  increment.
- Keep design-time and evidence scans off `trigger()` and `can_trigger()`; direct
  singleton lookup and dispatch remain O(1).
- Construction failures raise bounded public input errors and leave machine and
  reusable builder state unchanged.
- Third-party benchmark results are observations, not release or ordinary CI
  gates.

### Integration Points

- `src/fast_fsm/core.py` owns runtime topology normalization and publication.
- `FSMBuilder`, convenience factories, declarative replay, cloning, and
  `from_dict()` must delegate to the same private construction contract.
- `benchmarks/`, `Taskfile.yml`, and release-evidence tooling own isolated
  competitor setup, semantic preflight, and labelled result capture.
- Focused construction-atomicity, benchmark-schema, and CI-isolation tests
  provide the phase verification surface.

</code_context>

<specifics>
## Specific Ideas

Use the existing `_PreparedTransition` pipeline as the deep-module seam rather
than adding a public registrar abstraction or splitting the compiled core.
Comparison lanes must install and identify exact competitor versions in
isolated environments before timing equivalent scenarios.

</specifics>

<deferred>
## Deferred Ideas

- Final-state fields and invariants — Phase 27.
- Internal/external self-transition semantics — Phase 28.
- Expected domain rejection — Phase 29.
- Public builder-first deprecations and persistence metadata — Phase 30.

</deferred>
