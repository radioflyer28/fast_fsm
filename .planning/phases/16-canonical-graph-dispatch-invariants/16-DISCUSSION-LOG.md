# Phase 16: Canonical Graph & Dispatch Invariants - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-29
**Phase:** 16-canonical-graph-dispatch-invariants
**Mode:** Auto-selected recommended defaults under the user's standing authorization
**Areas discussed:** Canonical registry and graph snapshot, builder freeze and recursive async detection, guard-context parity, declarative single dispatch, bounded history

---

## Canonical Registry and Graph Snapshot

| Option | Description | Selected |
|--------|-------------|----------|
| Identity-canonical and fail closed | Same object is idempotent; different object with the name and every unknown/noncanonical endpoint fail before mutation. Immutable deterministic internal snapshot carries initial state and graph version. | ✓ |
| Name-only replacement | Let later objects silently replace earlier objects with the same name. | |
| Implicit endpoint registration | Automatically register transition endpoint objects/names during addition. | |

**User's choice:** Identity-canonical and fail closed (recommended default).
**Notes:** Avoids divergent object identity while keeping direct dictionary lookup and no new runtime dependency. Public topology snapshot v2 remains out of scope.

---

## Builder Freeze and Recursive Async Detection

| Option | Description | Selected |
|--------|-------------|----------|
| Successful-build freeze and cached identity | Cache only after full success, return the same machine repeatedly, reject every later mutator, and recursively detect wrapped async requirements. | ✓ |
| Freeze at build entry | A failed build permanently freezes the builder with no recovery path. | |
| Rebuild a fresh machine | Repeated build calls create separate machines from mutable builder state. | |

**User's choice:** Successful-build freeze and cached identity (recommended default).
**Notes:** Explicit sync fails rather than warning and silently omitting async behavior. Recursive inspection must be cycle-safe.

---

## Guard-Context Parity

| Option | Description | Selected |
|--------|-------------|----------|
| One shared sanitized context | Pass positional arguments unchanged and one deterministic sanitized keyword copy through the same sync/async can/trigger seam. | ✓ |
| Sanitize trigger only | Permit `can_trigger*()` and `trigger*()` to observe different guard inputs. | |
| Pass raw context | Remove the current private/size safety policy. | |

**User's choice:** One shared sanitized context (recommended default).
**Notes:** The caller mapping is never mutated; raw payload values are not added to logs.

---

## Declarative Single Dispatch

| Option | Description | Selected |
|--------|-------------|----------|
| One shared dispatch invocation | Ordinary sync/async trigger dispatch invokes the matched declarative handler once; compatibility helpers delegate to the same seam. | ✓ |
| Leave handlers manual-only | Decorated handlers remain disconnected from ordinary machine dispatch. | |
| Multiple compatibility hooks | Invoke from both state event handling and transition dispatch, risking duplicate execution. | |

**User's choice:** One shared dispatch invocation (recommended default).
**Notes:** Phase 16 locks exactly-once participation only. Phase 17 decides precise callback stage and failure semantics.

---

## Bounded History

| Option | Description | Selected |
|--------|-------------|----------|
| Positive bounded deque | Reject non-positive capacity, reset on enable, evict oldest in O(1), preserve chronological list-copy reads. | ✓ |
| Keep list front-deletion | Preserve O(n) deletion on every full-buffer append. | |
| Silently coerce invalid capacity | Turn zero/negative input into a hidden default or minimum. | |

**User's choice:** Positive bounded deque (recommended default).
**Notes:** Maintains the public `history` list-copy contract and disabled zero-cost path.

---

## Agent's Discretion

- Private snapshot/container and seam names, graph-version starting value, and mypyc-compatible annotations.
- Test file grouping and exact recursive-wrapper traversal implementation.

## Deferred Ideas

- Callback ordering and atomic failure stages — Phase 17.
- Ownership/locking — Phase 18.
- Diagnostic snapshot consumers and budgets — Phase 19.
- Public snapshot format and installed-artifact proof — future/Phase 20.
