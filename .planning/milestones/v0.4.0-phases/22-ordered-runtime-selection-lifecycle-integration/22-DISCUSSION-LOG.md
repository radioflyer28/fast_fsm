# Phase 22: Ordered Runtime Selection & Lifecycle Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-06
**Phase:** 22-ordered-runtime-selection-lifecycle-integration
**Areas discussed:** Ordered eligibility, failure and cancellation boundary, lifecycle and observability, sync/async parity

---

## Ordered eligibility

| Option | Description | Selected |
|--------|-------------|----------|
| Registration order | Evaluate candidates in call order. | |
| Ascending priority | Evaluate the frozen group from lowest numeric priority upward and stop at the first fully eligible candidate. | ✓ |

**User's choice:** Ascending priority (recommended default under autonomous discussion).
**Notes:** Preserves the prior milestone decision that registration order never has semantic effect.

---

## Rejection, exception, and cancellation boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Fall through every non-success | Continue after false, exception, or cancellation. | |
| Fail closed on exceptional control flow | False eligibility falls through; exceptions stop selection; async cancellation re-raises. | ✓ |

**User's choice:** Fail closed on exceptional control flow (recommended default under autonomous discussion).
**Notes:** Preserves Phase 17–18 one-time pre-commit failure and cancellation contracts.

---

## Lifecycle and observability

| Option | Description | Selected |
|--------|-------------|----------|
| Per-candidate lifecycle | Run callbacks/observers while considering each candidate. | |
| Select before lifecycle | Complete selection first; only one winning candidate can enter the existing lifecycle. | ✓ |

**User's choice:** Select before lifecycle (recommended default under autonomous discussion).
**Notes:** Exhaustion reports one selection failure and failure observers run once.

---

## Sync/async parity

| Option | Description | Selected |
|--------|-------------|----------|
| Parallel async guards | Evaluate guards concurrently and reconcile a winner. | |
| Sequential async guards | Await candidates in priority order with the same short-circuit semantics as sync. | ✓ |

**User's choice:** Sequential async guards (recommended default under autonomous discussion).
**Notes:** Keeps side-effect ordering deterministic and makes lower-priority guards unobserved after a winner, exception, or cancellation.

---

## the agent's Discretion

- Private helper names, result/history metadata plumbing, and test placement follow existing `core.py` and mypyc patterns.

## Deferred Ideas

- Public constructor/declarative/serialization parity, candidate-aware diagnostics, installed-artifact proof, and the drone example remain in Phases 23–25.
