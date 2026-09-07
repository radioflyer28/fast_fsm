# Phase 21: Priority Contract & Atomic Registration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-06
**Phase:** 21-Priority Contract & Atomic Registration
**Areas discussed:** transition API, candidate identity, atomic fan-out, complexity contract

---

## Transition API

| Option | Description | Selected |
|--------|-------------|----------|
| Evolve `add_transition()` | Add keyword-only priority to the ordinary transition API. | ✓ |
| Add a candidate API | Keep ordinary transitions singular and add a second registrar. | |

**User's choice:** Evolve the existing API.
**Notes:** The user explicitly rejected unnecessary second APIs and approved
priority as transition behavior.

---

## Candidate Identity

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit numeric order | Exact non-boolean integer priorities; lower wins; ties fail. | ✓ |
| Registration order | Allow setup order to resolve overlaps. | |

**User's choice:** Explicit numeric order.
**Notes:** Exact duplicates remain idempotent; distinct equal-priority
candidates reject atomically.

---

## Atomic Fan-out

| Option | Description | Selected |
|--------|-------------|----------|
| Plan then publish | Validate every affected slot, then make one graph commit. | ✓ |
| Incremental mutation | Update slots as helpers traverse their inputs. | |

**User's choice:** Plan then publish.
**Notes:** Applies to multi-source, batch, bidirectional, emergency, and
builder-backed registration, including graph version and clone isolation.

---

## Complexity Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Honest singleton/group split | Preserve O(1) singleton lookup/dispatch and disclose O(k) local group work. | ✓ |
| Retain blanket O(1) claim | Describe all transition work as constant-time. | |

**User's choice:** Honest singleton/group split.
**Notes:** Candidate selection mechanics are Phase 22; this phase establishes
the storage and policy prerequisite.

---

## the agent's Discretion

Private helper and type names follow current core.py/mypyc patterns while
preserving the recorded public contract.

## Deferred Ideas

None.
