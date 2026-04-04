# Phase 1: Quick Wins - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship the two lowest-risk, highest-value fixes: automated version sync via `importlib.metadata` and the absolute import fix in `condition_templates.py`.

</domain>

<decisions>
## Implementation Decisions

### Agent's Discretion
All implementation choices are at the agent's discretion — pure infrastructure phase.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `importlib.metadata` is stdlib ≥3.8, no new dependency needed
- `__init__.py` already imports from `.core` using relative imports

### Established Patterns
- All other modules use relative imports (`from .core import ...`, `from .conditions import ...`)
- `condition_templates.py` is the only file using absolute `from fast_fsm import Condition`

### Integration Points
- `__init__.py` line 46: `__version__ = "0.1.0"` — replace with dynamic lookup
- `condition_templates.py` line 6: `from fast_fsm import Condition` — change to relative

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
