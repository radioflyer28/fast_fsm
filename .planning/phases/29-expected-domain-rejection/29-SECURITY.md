---
phase: 29
slug: expected-domain-rejection
status: verified
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-17
verified: 2026-09-17
---

# Phase 29 — Security

> Threat verification for bounded expected-domain rejection across synchronous,
> asynchronous, lifecycle, logging, observer, and native-runtime boundaries.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Caller → `TransitionRejected` | Caller-controlled rejection codes become public transition metadata. | Exact built-in string constrained to the bounded ASCII grammar |
| Eligibility checks → selector | A guard, declarative guard, or state permission may reject without becoming an implementation failure. | Rejection signal, selected priority, mode, and stage |
| Candidate group → dispatch result | A rejection must terminate finite priority resolution rather than fall through. | Terminal `TransitionResult` with no state mutation |
| Selector → lifecycle | Conversion authority ends before callbacks, handlers, observers, and post-selection lifecycle work. | Failure identity, commit state, current state, and history |
| Library metadata → logs and results | Public diagnostics must not expose arbitrary exception or caller payloads. | Validated scalar code and fixed bounded text |
| Async task → machine ownership | Cancellation must retain its identity and release all ownership/context state. | Task cancellation, finalization, and machine reuse |
| Python source → mypyc extension | Native compilation must preserve validation, catch placement, slots, and hot-path behavior. | Runtime layout and pure/native semantic parity |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Evidence | Status |
|-----------|----------|-----------|----------|-------------|---------------------|--------|
| T-29-01 | Spoofing | rejection-code input | high | mitigate | Exact built-in string, 1–64 length-before-scan validation, positive ASCII grammar, conversion-time revalidation, and boundary tests in `src/fast_fsm/core.py` and `tests/test_expected_rejection.py`. | closed |
| T-29-02 | Tampering / Elevation of Privilege | priority-group selection | high | mitigate | Sync and async groups stop on every non-`None` result; rejection returns a terminal result, and lower-candidate sentinels prove no fallback. | closed |
| T-29-03 | Repudiation | outcome classification and catch placement | high | mitigate | Bounded code, `cause=None`, stage, priority, and mode identify expected rejection; structural tests require exactly the approved sync/async conversion sites. | closed |
| T-29-04 | Information Disclosure | results, logs, and policy text | high | mitigate | Only the validated scalar reaches fixed result/debug text; hostile-representation tests forbid arbitrary payloads, warnings, tracebacks, and exception representations. | closed |
| T-29-05 | Denial of Service | validation and hot selectors | high | mitigate | Length is rejected before scanning; AST checks forbid sorting, candidate copying, topology scans, reflection, and async task fan-out while retaining the singleton throughput floor. | closed |
| T-29-06 | Denial of Service / Repudiation | observer finalization | medium | mitigate | The single failure finalizer snapshots observers once and isolates failures; query paths remain observer-free and reentry remains usable. | closed |
| T-29-07 | Tampering / Repudiation | lifecycle boundary | high | mitigate | Structural guards forbid lifecycle/trigger conversion, while pre/post-commit matrices preserve exact cause, stage, state, destination, and history truth. | closed |
| T-29-08 | Denial of Service | async cancellation and ownership | high | mitigate | Eligibility conversion catches `Exception` only; dedicated cancellation finalization, bare re-raise, context reset, ownership release, and deterministic reuse tests preserve cancellation identity. | closed |

All eight plan-time threats are mitigated. No accepted or transferred risks are required.

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-17 | 8 | 8 | 0 | Codex orchestration with GSD security auditor, ASVS L1 |

The auditor checked all plan and execution artifacts against the implementation
and tests. Its focused threat suite passed 88 tests; it found no unregistered
threat flags and no open threat at any severity.

---

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented (none).
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-17
