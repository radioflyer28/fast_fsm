# Phase 27: Explicit Final States - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-15
**Phase:** 27-explicit-final-states
**Mode:** `--auto`
**Areas discussed:** State declaration, sink semantics, construction invariant, lifecycle truth, control and persistence

---

## State Declaration

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable State flag | Keyword-only `State(..., final=True)`, read-only property, false by default | ✓ |
| Dedicated subclass | Introduce a `FinalState` public type | |
| Machine registry | Keep State unchanged and store mutable final names on each machine | |

**Auto-selected choice:** Immutable State flag (recommended default).
**Notes:** This is the smallest representation of domain intent and naturally survives canonical State reuse.

## Sink Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit only | Only `final=True` means terminated; dead ends remain ordinary sinks | ✓ |
| Infer from topology | Every state without outgoing transitions is final | |
| Hybrid inference | Explicit marker plus implicit dead-end completion | |

**Auto-selected choice:** Explicit only (recommended default).
**Notes:** Avoids confusing incomplete topology with intentional completion.

## Construction Invariant

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical atomic rejection | Reject final-source edges during Phase 26 normalization before any publication | ✓ |
| Adapter-specific checks | Each builder/factory/helper rejects independently | |
| Runtime-only failure | Allow topology and reject only when triggered | |

**Auto-selected choice:** Canonical atomic rejection (recommended default).
**Notes:** Preserves one semantic boundary and prevents adapter drift or partial batches.

## Lifecycle Truth

| Option | Description | Selected |
|--------|-------------|----------|
| Commit-derived truth | `is_terminated` reads current State; post-commit failures do not undo it | ✓ |
| Separate flag | Mutate a machine termination flag during lifecycle | |
| Successful-lifecycle truth | Mark terminated only after every callback/observer succeeds | |

**Auto-selected choice:** Commit-derived truth (recommended default).
**Notes:** Matches the existing truthful commit boundary and avoids duplicated mutable state.

## Control and Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Derived controls + additive schema | Reset/restore/clone derive from State metadata; older dictionaries default non-final | ✓ |
| Snapshot flag | Persist a separate termination bit in runtime snapshots | |
| Defer persistence | Add runtime finality now and postpone dictionary preservation | |

**Auto-selected choice:** Derived controls + additive schema (recommended default).
**Notes:** Satisfies Phase 27 continuity while preserving snapshot v1 and backward compatibility.

## the agent's Discretion

- Exact internal helper names, bounded error wording, dictionary field spelling, and test placement.

## Deferred Ideas

- Transition modes, expected rejection, broad construction deprecations, diagnostic rendering, and release/tutorial proof remain assigned to Phases 28–32.
