# Phase 18: Safe Ownership & Concurrency - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-01
**Phase:** 18-safe-ownership-concurrency
**Mode:** `--auto`; recommended defaults previously authorized by the user
**Areas discussed:** Ownership violation contract, Synchronous serialization, Async loop and task ownership, Coverage cleanup and performance

---

## Ownership Violation Contract

| Question | Options considered | Selected |
|----------|--------------------|----------|
| Failure surface | `RuntimeError`; failed `TransitionResult`; new public exception | `RuntimeError` ✓ |
| Detection point | Before lock; after acquisition; queue | Before lock ✓ |
| Nested callback interaction | Existing Phase 17 stage; new stage; ignore | Existing stage ✓ |
| Error disclosure | Redacted metadata; payload-rich; empty | Redacted metadata ✓ |

**Auto-selection:** Recommended immediate operational error with no new public API type. This prevents a nested call from being silently ignored while preserving Phase 17's outer callback classification.

## Synchronous Serialization

| Question | Options considered | Selected |
|----------|--------------------|----------|
| Lock scope | Per machine; global; caller supplied | Per machine ✓ |
| Contention | Serialize; fail if busy; fair queue | Serialize ✓ |
| Ownership envelope | Whole operation; commit only; callbacks outside | Whole operation ✓ |
| Release | `finally` for `BaseException`; ordinary exceptions only; manual paths | `finally` ✓ |

**Auto-selection:** Recommended per-instance full-operation ownership, with same-thread reentry rejected before acquisition and no fairness promise.

## Async Loop and Task Ownership

| Question | Options considered | Selected |
|----------|--------------------|----------|
| Loop binding | Permanent on first async use; construction-time; idle rebinding | First async use ✓ |
| Same-loop contention | `asyncio` lock; threading lock; fail if busy | `asyncio` lock ✓ |
| Child-task reentry | Reject inherited context; treat independent; timeout | Reject inherited context ✓ |
| Waiter cancellation | Propagate; shield; failed result | Propagate ✓ |

**Auto-selection:** Recommended loop-native serialization and causal ownership propagation. Permanent binding makes unsupported cross-loop use explicit; inherited context prevents parent/child callback deadlocks.

## Coverage, Cleanup, and Performance

| Question | Options considered | Selected |
|----------|--------------------|----------|
| Write coverage | All machine writes; triggers only; omit registries | All machine writes ✓ |
| Read contract | Defer snapshot consistency; lock every read; reject reads | Defer to Phase 19 ✓ |
| Sync callbacks on async machine | Inline; always offload; configurable | Inline ✓ |
| Performance | Preserve O(1) and 200k floor; relax; defer measurement | Preserve gates ✓ |

**Auto-selection:** Recommended one policy across runtime, graph, history, and callback/listener writes, deterministic concurrency tests, and fresh pure/compiled performance evidence.

## the agent's Discretion

- Private helper and token names, slot ordering, and test table organization.
- Internal use of decorators, context managers, or explicit helper calls, subject to auditable pre-acquisition checks and `finally` release.
- Exact redacted `RuntimeError` wording.

## Deferred Ideas

- Queued reentry (FUTR-01).
- Cross-loop ownership transfer (FUTR-03).
- Automatic callback thread offload (FUTR-04).
- Diagnostic snapshot consistency (Phase 19) and installed-artifact proof (Phase 20).
