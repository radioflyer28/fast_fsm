# Phase 29: Expected Domain Rejection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-17
**Phase:** 29-expected-domain-rejection
**Areas discussed:** Rejection-code contract, result and exception API, condition composition, observer and query details

---

## Rejection-Code Contract

| Question | Options Considered | Selected |
|----------|--------------------|----------|
| Accepted input type | Exact `str`; `str` or `Enum`; any string-convertible object | Exact `str` |
| Maximum length | 64; 128; 32 characters | 64 characters |
| Character format | Lowercase ASCII identifier; printable ASCII; non-control Unicode | `[a-z][a-z0-9_.-]*` |
| Invalid input | Reject eagerly; normalize; defer until FSM boundary | Reject eagerly without normalization |

**User's choice:** The recommended strict contract in all four questions.
**Notes:** Non-strings use `TypeError`; empty, oversized, or malformed strings use `ValueError`.

---

## Result and Exception API

| Question | Options Considered | Selected |
|----------|--------------------|----------|
| Result representation | Stored code + derived property; stored bool + code; status enum | Stored `rejection_code` + derived `rejected` |
| Failure fields | No cause + code in bounded error; fixed error; signal in cause | `cause=None`, bounded error includes code |
| `raise_if_failed()` | Existing `TransitionError`; `TransitionRejected`; new specialized error | Existing `TransitionError` |
| Compatibility | Comparison-neutral/repr-visible; equality-visible; fully hidden | `compare=False`, repr-visible |

**User's choice:** Add rejection metadata without replacing or fragmenting the existing result/exception contract.
**Notes:** The signal exception is an eligibility input; `TransitionError` remains the failed-result consumption API.

---

## Condition Composition

| Question | Options Considered | Selected |
|----------|--------------------|----------|
| `And` / `Or` behavior | Propagate terminally; operator-dependent conversion; ordinary false | Propagate immediately |
| Negation behavior | Propagate; invert to true; convert to false | Propagate unchanged |
| Async/nested behavior | Recursive parity; top-level only; sync only | Recursive sync/async parity |
| Direct evaluation | Propagate signal; return special value; convert to false | Propagate outside FSM |

**User's choice:** Boolean composition operates only on boolean eligibility and never consumes expected rejection.
**Notes:** Cancellation retains its existing identity and is never converted into rejection.

---

## Observer and Query Details

| Question | Options Considered | Selected |
|----------|--------------------|----------|
| Failure observers | Existing signature once; extra code argument; no notification | Existing signature exactly once |
| `can_trigger*()` | False without observation; structured query result; re-raise | False without observation |
| Runtime logging | Metadata-only debug; warning; none | Metadata-only debug |
| Selected metadata | Existing pre-commit fields; minimal code only; include destination | Existing pre-commit fields |

**User's choice:** Reuse existing failure/query machinery while exposing the safe scalar code only where the current API already carries result metadata.
**Notes:** Rejected triggers create no history record and queries produce no trace event.

---

## the agent's Discretion

- Private helper names, carrier layout, constants, and test partitioning.

## Deferred Ideas

- None. Richer localized rejection payloads remain a future requirement rather than Phase 29 scope.
