# Phase 30: Builder-First Construction & Persistence Parity - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-17
**Phase:** 30-builder-first-construction-persistence-parity
**Mode:** Autonomous recommended defaults, explicitly authorized by the active milestone-completion goal
**Areas discussed:** Construction hierarchy, Declarative integration, Compatibility deprecations, Persistence and reconstruction parity

---

## Construction Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Builder-first with advanced direct construction | Lead new programmatic users to `FSMBuilder`; retain direct machines for advanced control and `from_dict` for persisted data. | ✓ |
| Equal prominence | Continue presenting every constructor/helper as an equivalent starting point. | |
| Builder-only runtime | Remove or deprecate direct machine construction too. | |

**Selection:** Auto-selected recommended default under the authorized goal.
**Notes:** This matches the user's earlier direction to simplify construction around the builder while preserving composability and advanced control.

---

## Declarative Integration

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical builder import | Import decorator metadata into ordinary canonical transition requests through `FSMBuilder`. | ✓ |
| Separate declarative topology | Keep decorator-owned topology and machine topology as parallel implementations. | |
| Second declarative builder | Add a specialized construction API for decorated states. | |

**Selection:** Auto-selected recommended default under the authorized goal.
**Notes:** The selected option fulfills BUILD-02 without multiplying public construction mechanisms.

---

## Compatibility Deprecations

| Option | Description | Selected |
|--------|-------------|----------|
| One warned compatibility cycle | Emit actionable `DeprecationWarning`; retain helpers through v0.5.x; earliest removal v0.6.0. | ✓ |
| Documentation-only | Mark helpers deprecated in prose but emit no runtime signal. | |
| Immediate removal | Delete compatibility constructors in v0.5.0. | |

**Selection:** Auto-selected recommended default under the authorized goal.
**Notes:** This is the smallest policy satisfying BUILD-03 and the milestone's explicit no-immediate-removal constraint.

---

## Persistence and Reconstruction Parity

| Option | Description | Selected |
|--------|-------------|----------|
| Additive directional compatibility | Keep string states, use `final_states` and true-only `internal`, default missing fields safely, preserve snapshot v1. | ✓ |
| Breaking topology v2 | Replace existing dictionary shapes with a versioned incompatible schema. | |
| Snapshot topology | Add final and transition metadata to runtime snapshots. | |

**Selection:** Auto-selected recommended default under the authorized goal.
**Notes:** This follows the approved milestone research and avoids claiming unsafe new-payload/old-reader semantic parity.

---

## the agent's Discretion

- Private helper names and exact staging order inside the no-user-code construction transaction.
- Warning constant placement and bounded wording details.
- Test-file partitioning and deterministic dictionary key ordering.

## Deferred Ideas

- Diagnostic and visualization projection remains Phase 31.
- Progressive README/Sphinx tutorial and release-facing migration material remains Phase 32.
- Immediate helper removal, topology snapshot v2, and executable serialization remain out of scope.
