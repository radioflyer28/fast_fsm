# Phase 28: Same-State Transition Modes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-16
**Phase:** 28-same-state-transition-modes
**Areas discussed:** Transition mode ownership, lifecycle boundary, commit and timing truth, failure and cancellation parity, construction scope
**Selection source:** Previously approved v0.5.0 milestone research and roadmap; no unresolved gray area remained after codebase scouting.

---

## Transition Mode Ownership

| Option | Description | Selected |
|--------|-------------|----------|
| Per-transition immutable mode | Keyword-only exact `internal=False` stored on each canonical transition | ✓ |
| Machine-wide mode | One compatibility switch changes every self-transition | |
| Infer from equal endpoints | Every same-state edge is implicitly internal | |

**Inherited approved choice:** Per-transition immutable mode.
**Notes:** One state may intentionally support both restart and in-state update events; existing same-state behavior remains external by default.

## Lifecycle Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Skip only state lifecycle surfaces | Retain before/action/trigger/after/history/result; omit all exit and entry hooks, callbacks, and listeners | ✓ |
| Treat internal as no-op | Evaluate eligibility but omit commit, actions, history, and observers | |
| Reuse external lifecycle | Execute exit and entry despite `internal=True` | |

**Inherited approved choice:** Skip only state lifecycle surfaces.
**Notes:** The approved lifecycle truth table names every retained and suppressed surface for both synchronous and asynchronous machines.

## Commit and Timing Truth

| Option | Description | Selected |
|--------|-------------|----------|
| Logical commit, preserved residency | Return committed truth and optional history while preserving entry epoch | ✓ |
| Silent action | Run action without a committed result or history | |
| Reset timing | Record a commit and restart entry-relative timing | |

**Inherited approved choice:** Logical commit with preserved residency.
**Notes:** External self-transition remains the explicit mechanism for restarting state-owned behavior and timing windows.

## Failure and Cancellation Parity

| Option | Description | Selected |
|--------|-------------|----------|
| Existing stage/commit contract | Before failures are uncommitted; retained post-commit failures and cancellation preserve commit truth | ✓ |
| Internal-specific error model | Introduce separate stages or rollback behavior | |
| Best-effort callbacks | Continue after callback failures | |

**Inherited approved choice:** Existing stage and commit contract.
**Notes:** Mode changes which state lifecycle surfaces exist, not the meaning of lifecycle stages, ownership, finalization, or cancellation.

## Construction Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical spine now, parity fan-out later | Add carriers, validation, direct/builder authoring, runtime, result/history, clone/snapshot preservation; finish every adapter/persistence path in Phase 30 | ✓ |
| Adapter-specific implementation | Teach each constructor its own mode rules | |
| Pull Phase 30 forward | Combine runtime semantics with every deprecation and persistence change | |

**Inherited approved choice:** Canonical spine now, parity fan-out later.
**Notes:** This preserves the approved roadmap boundary while preventing Phase 30 from needing to redesign runtime semantics.

## the agent's Discretion

- Private helper names, bounded error wording, test organization, and the exact internal representation of false defaults.
- Whether lifecycle specialization is a private internal runner or one bounded branch, provided the external hot path remains feature-local and predictable.

## Deferred Ideas

- Expected domain rejection — Phase 29.
- Full construction/persistence parity and deprecations — Phase 30.
- Diagnostics and visualization — Phase 31.
- Tutorial, documentation, release, and performance evidence — Phase 32.
- Hierarchy, targetless transitions, queued reentry, and global mode switches remain out of milestone scope.
