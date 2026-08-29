# Phase 7: Serialization (`to_dict()`) - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

`StateMachine.to_dict()` returns a plain dict that roundtrips losslessly through `StateMachine.from_dict()`. Output includes `"name"`, `"initial"`, `"states"`, and `"transitions"` (each as `{"trigger", "from", "to"}`). Guards are NOT included (callables are not serialisable).

Requirements: SERIAL-01, SERIAL-02, SERIAL-03

</domain>

<decisions>
## Implementation Decisions

### the agent's Discretion
All implementation choices are at the agent's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
