# Phase 14: Documentation - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning
**Mode:** Auto-generated (docs phase — discuss skipped)

<domain>
## Phase Boundary

Update README and Sphinx docs with timing condition examples and API reference. Users should be able to learn about TimeoutCondition, CooldownCondition, and ElapsedCondition from the docs alone.

</domain>

<decisions>
## Implementation Decisions

### Agent's Discretion
All implementation choices are at the agent's discretion — documentation phase. Follow existing README and Sphinx conventions. Use concrete, runnable examples showing each condition as a transition guard.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `README.md` — has existing API reference, condition templates section, examples
- `docs/api/conditions.md` — Sphinx autodoc stub for conditions module
- `docs/QUICK_START.md`, `docs/TUTORIAL.md` — existing guides

### Established Patterns
- README uses fenced code blocks with `python` syntax highlighting
- Sphinx docs use myst-parser (Markdown) with autodoc directives
- `docs/api/conditions.md` has `automodule` directives

### Integration Points
- README: add timing conditions to the "Condition Templates" section
- Sphinx: update `docs/api/conditions.md` to include timing conditions (autodoc will pick them up automatically if the module is already imported)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow existing patterns.

</specifics>

<deferred>
## Deferred Ideas

None — documentation phase.

</deferred>
