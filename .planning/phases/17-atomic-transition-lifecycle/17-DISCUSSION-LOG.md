# Phase 17: Atomic Transition Lifecycle - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-01
**Phase:** 17-atomic-transition-lifecycle
**Areas discussed:** Lifecycle stage order, failure result contract, failure observer semantics, cancellation and history
**Selection mode:** Recommended options auto-selected under the user's standing milestone instruction.

---

## Lifecycle Stage Order

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Commit boundary | Before callbacks; between exit and enter work; after every callback | Between exit and enter work ✓ |
| Async placement | Same logical slots; one async tail; separate lifecycle | Same logical slots ✓ |
| Declarative handler | Pre-commit action; post-commit before observers; outside lifecycle | Post-commit before trigger/after observers ✓ |
| Later callbacks after failure | Continue; stop at first failure; collect all | Stop at first failure ✓ |

**User's choice:** Recommended lifecycle contract.
**Notes:** The selected order makes the source/destination state truthful at every failure boundary and removes the current async-tail mismatch.

---

## Failure Result Contract

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Callback exception surface | Structured failed result; always raise; log and report success | Structured failed result ✓ |
| Result metadata | Error string only; stage+committed; stage+committed+cause | Stage + committed + original cause ✓ |
| Stage identifiers | Stable documented strings; public enum; free-form messages | Stable documented strings ✓ |
| Exception-style use | Remove; default raises; retain `raise_if_failed()` with chaining | Retain and chain cause ✓ |

**User's choice:** Recommended additive result fields while preserving value-returning transitions.
**Notes:** This follows ADR-002 and avoids a breaking default-exception change.

---

## Failure Observer Semantics

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Dispatch seam | Existing scattered calls; one failure finalizer; observer-owned dispatch | One failure finalizer ✓ |
| Observer exception | Replace cause; recurse; isolate and continue | Isolate and continue ✓ |
| Observer signature | Add positional fields; inject reserved kwargs; preserve signature | Preserve signature ✓ |
| Cardinality | Best effort; first observer only; every observer once | Every observer once ✓ |

**User's choice:** Recommended once-only, non-recursive observer finalization.
**Notes:** The transition's original cause remains authoritative even if observer code also fails.

---

## Cancellation and History

| Decision | Alternatives considered | Selected |
|----------|-------------------------|----------|
| Cancellation surface | Convert to result; shield callbacks; notify then re-raise | Notify then re-raise ✓ |
| Pre-commit cancellation | Roll forward; preserve source/no history; rollback callbacks | Preserve source/no history ✓ |
| Post-commit cancellation | Roll back; preserve destination/history; suppress | Preserve destination/history ✓ |
| Commit/history timing | History after all callbacks; history with state commit; record attempts | History with state commit ✓ |

**User's choice:** Recommended native cancellation semantics with an atomic non-awaiting commit section.
**Notes:** Event-controlled async tests should prove each cancellation boundary without sleeps.

---

## Agent's Discretion

- Private helper and slot-backed context types.
- Exact stable stage-string spelling and concise error wording.
- Exact state-assignment/history-append statement order inside the non-awaiting commit helper.
- Test module/helper layout and hot-path optimization details.

## Deferred Ideas

- Reentrancy and concurrency ownership — Phase 18.
- Safe trace/logging and bounded diagnostics — Phase 19.
- Installed artifact release parity — Phase 20.
