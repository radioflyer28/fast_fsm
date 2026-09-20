# Phase 31: Semantic Diagnostics & Visualization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-19
**Phase:** 31-semantic-diagnostics-visualization
**Areas discussed:** Completion versus graph shape, semantic diagnostic projection, diagram distinction

---

The active milestone-completion goal called for the remaining GSD steps to proceed. This discussion used the `--auto` path and auto-selected the recommendations already supported by the approved roadmap, requirements, research, and Phases 27–30. No new user answer was claimed.

## Completion Versus Graph Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve topology output and add explicit completion/sink facts | Keeps existing keys truthful while making `State.final` the only completion fact. | ✓ |
| Reinterpret all no-outgoing states as final | Conflates incomplete topology with intentional completion. | |
| Remove legacy dead/terminal output | Breaks existing diagnostic consumers unnecessarily. | |

**Selection:** Auto-selected approved explicit-final and compatibility contract.
**Notes:** Final states must not be scored as accidental dead ends merely because they have no outgoing transitions.

## Semantic Diagnostic Projection

| Option | Description | Selected |
|--------|-------------|----------|
| Extend one scalar snapshot-backed cold projection | Reuses the bounded graph and keeps diagnostic work off dispatch. | ✓ |
| Reinspect mutable runtime tables separately per output | Risks inconsistent reads and duplicate work. | |
| Add derived finality to every public runtime record | Creates redundant state that can misrepresent restore/direct control. | |

**Selection:** Auto-selected existing snapshot and bounded-output architecture.
**Notes:** Trace fields remain metadata-only by default; only validated rejection codes may be emitted.

## Diagram Distinction

| Option | Description | Selected |
|--------|-------------|----------|
| Final-only completion marker plus explicit internal/self labels | Makes completion and lifecycle mode visible without changing runtime semantics. | ✓ |
| Draw completion from every sink | Misstates non-final dead-end topology. | |
| Use identical self-edge notation for internal and external modes | Hides lifecycle behavior from the reader. | |

**Selection:** Auto-selected roadmap's required distinction and current opaque-ID/escaping pattern.
**Notes:** Mermaid and PlantUML use the same semantic information with language-specific safe encoding.

## the agent's Discretion

- Exact additive JSON key names, diagram label wording, and validator method/report names remain implementation details for research and planning.

## Deferred Ideas

- Phase 32 tutorial and installed-artifact evidence; richer rejection detail and statechart features remain out of scope.
