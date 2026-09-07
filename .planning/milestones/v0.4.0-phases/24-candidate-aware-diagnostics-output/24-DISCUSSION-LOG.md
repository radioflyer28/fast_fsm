# Phase 24: Candidate-Aware Diagnostics & Output - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-07
**Phase:** 24-candidate-aware-diagnostics-output
**Areas discussed:** diagnostic projection, shadow analysis, output identity, budget accounting

---

## Diagnostic Projection

| Option | Description | Selected |
|--------|-------------|----------|
| Inspect live runtime slots | Let each consumer understand singleton/group storage. | |
| One immutable snapshot projection | Capture once and derive every diagnostic consumer from it. | ✓ |

**User's choice:** One immutable snapshot projection (autonomous recommended default)
**Notes:** Preserves the established diagnostic concurrency and consistency boundary.

---

## Shadow Analysis

| Option | Description | Selected |
|--------|-------------|----------|
| Aggressive inference | Infer shadowing from arbitrary guards or permissions. | |
| Conservative proof | Flag only statically established shadowing; report uncertainty separately. | ✓ |

**User's choice:** Conservative proof (autonomous recommended default)
**Notes:** Avoids false-positive removal advice for safety fallbacks.

---

## Output Identity

| Option | Description | Selected |
|--------|-------------|----------|
| Collapse source/trigger pairs | Keep legacy diagrams compact but hide candidates. | |
| Emit one priority-bearing record per candidate | Preserve all candidates in stable deterministic order. | ✓ |

**User's choice:** Emit one priority-bearing record per candidate (autonomous recommended default)
**Notes:** Existing escaping remains unchanged; priority is numeric metadata.

---

## Budget Accounting

| Option | Description | Selected |
|--------|-------------|----------|
| Count collapsed slots | Treat a candidate group as one diagnostic edge. | |
| Count candidates | Charge every candidate edge to work and output budgets. | ✓ |

**User's choice:** Count candidates (autonomous recommended default)
**Notes:** Exhaustion must retain explicit incomplete-result behavior.

---

## the agent's Discretion

- Exact report-field names, textual label punctuation, narrow static shadow
  proof, and focused diagnostic test placement.

## Deferred Ideas

- Performance guidance, installed-artifact proof, public documentation, and
  the complete drone example remain Phase 25 scope.
