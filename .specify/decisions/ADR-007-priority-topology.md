# ADR-007: Priority topology and atomic registration

**Status**: Accepted
**Date**: 2026-09-06
**Deciders**: project maintainer + AI pair

---

## Context

One source/trigger slot must become a finite, deterministic set of guarded
transition candidates without weakening the singleton dispatch path, creating a
second registration API, or publishing an intermediate graph while a fan-out
operation is still being validated. The selective mypyc boundary remains
`core.py`; all candidates must retain its slots policy and no new runtime
dependency is permitted.

## Decision

1. **D-01 — one public registrar.** `add_transition(..., *, priority=0)` is
   the only candidate-registration API; priority is keyword-only and defaults
   to zero.
2. **D-02 — exact priority boundary.** Priority remains `object` until
   `type(priority) is int` passes. Booleans, integer subclasses, `IntEnum`,
   floats, strings, and coercible objects are rejected before any mutation.
3. **D-03 — post-normalization identity defines duplicates.** Equal-priority
   candidates are exact duplicates only when canonical target and normalized
   `Condition` object identities match. Other equal-priority candidates fail
   atomically; repeated raw callables and `unless=` values create fresh wrappers
   and therefore conflict.
4. **D-04 — preserve the singleton fast path.** A one-candidate slot is a
   direct slotted `TransitionEntry`. A second distinct priority replaces that
   value with a private frozen, slotted, tuple-backed group sorted ascending by
   priority.
5. **D-05 — merge before publication.** Every affected slot is merged off-table
   against its staged replacement, then all identity-changing replacements are
   published together. One changing public operation advances graph version once;
   duplicate-only operations are version-neutral.
6. **D-06 — clones share values, not tables.** Clone copies preserve immutable
   entry/group values while making outer and per-source mapping tables independent;
   later registration replaces only the receiving machine's slot.
7. **D-07 — complexity is local and truthful.** Source/trigger lookup and
   singleton dispatch remain O(1). Finite-group construction and ordered
   selection are local O(k), with no unrelated graph scan or dispatch-time sort.
   The compiled singleton floor remains 200,000 operations/second.
8. **D-08 — phase boundaries are explicit.** Phase 21 only registers immutable
   topology. Grouped runtime dispatch fails closed until Phase 22; construction,
   clone/query/serialization parity belongs to Phase 23; diagnostics and output
   parity belong to Phase 24; broader performance and user guidance belong to
   Phase 25.

## Consequences

Registration order cannot influence candidate precedence. A grouped slot is
never silently flattened or treated as its first candidate, so callers receive a
fixed failure until ordered runtime selection is deliberately introduced. The
private representation is intentionally not a public inspection API.

## Considered Alternatives

### Last-write singleton storage — Rejected

It collapses same-slot candidates and makes setup order observable.

### Mutable list per slot — Rejected

It permits mutation after publication and undermines clone isolation.

### Runtime sorting or first-candidate dispatch — Rejected

It moves registration work to the hot path and would implement Phase 22 winner
semantics before their lifecycle contract is specified.
