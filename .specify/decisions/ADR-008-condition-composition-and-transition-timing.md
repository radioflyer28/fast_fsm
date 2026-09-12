# ADR-008: Condition composition and transition-entry timing

**Status**: Accepted
**Date**: 2026-09-11
**Deciders**: project maintainer + AI pair

---

## Context

The previous public guard story mixed the small FSM decision algebra with
application validation helpers and mutable, free-floating timers. That made it
too easy for a `can_trigger()` query to consume a cooldown and left timeout
reference points unrelated to an FSM's committed state lifecycle. It also kept
two equivalent negation shapes and presented a compiled bridge as an ordinary
caller-facing choice.

## Decision

1. The recommended guard vocabulary is `Condition`, `FuncCondition`,
   `AsyncCondition`, `AndCondition`, `OrCondition`, and `NotCondition`.
   `&`, `|`, and `~` construct the three composition wrappers; evaluation stays
   left-to-right and short-circuiting.
2. `NotCondition` is the canonical negation representation. `unless=` creates
   it directly. `NegatedCondition` remains a deprecated compatibility wrapper,
   including its historic `_inner` seam.
3. `CompiledFuncCondition`, validation-style leaves, and old timer leaves stay
   importable and behavior-compatible for a deprecation cycle ending no earlier
   than the next major release. New applications own payload interpretation in
   `FuncCondition` or a domain `Condition` subclass.
4. `after` and `within` are immutable transition metadata, not mutable
   conditions. They define the entry-relative half-open interval
   `[after, within)`, use a supplied monotonic clock, and are checked before any
   caller guard.
5. A selection attempt samples the clock once when timing is present and shares
   that value across its local priority group. Queries are observational. The
   commit boundary records one validated timestamp before destination callbacks,
   so the destination observes its committed entry time even if a later callback
   fails.

## Consequences

The public interface is smaller while compatibility remains explicit. Timing
does not create a second registrar, a global scheduler, or an FSM-managed
cooldown. Singleton dispatch remains direct when no timing metadata is stored;
timed singleton selection is O(1), and candidate-group work remains local O(k).

## Considered Alternatives

### Retain generic validation leaves as the preferred interface — Rejected

Regex, membership, comparison, and payload-key policy belong to an application's
domain, not a general FSM package. Keeping them as deprecated imports protects
callers without expanding the recommended interface.

### Make a stateful cooldown commit-aware — Rejected

Cooldown semantics require a product-specific choice about attempts, commits,
failures, restoration, and reset. Entry-relative eligibility solves the current
transition timing need without silently choosing that lifecycle policy.

### Sample time per guard or candidate — Rejected

That makes priority ordering timing-dependent and can allow a later candidate
to observe a different instant. One sample makes selection deterministic and
keeps async selection stable before its first await.
