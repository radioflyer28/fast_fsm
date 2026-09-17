---
phase: 28
slug: same-state-transition-modes
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-16
verified: 2026-09-16
---

# Phase 28 — Security

> Threat verification for explicit external and internal same-state transition modes.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| caller → public registration API | Untrusted objects cross endpoint, exact-bool, priority, and ownership validation. | State references, trigger, condition, priority, and `internal` mode |
| immutable request → published topology | A complete local construction plan must validate before shared topology changes. | Canonical transition requests and graph-version state |
| selected entry → lifecycle | The selected immutable mode and priority become authoritative execution metadata. | Candidate metadata and commit state |
| caller payload → callbacks/results/history | Library metadata must remain observable without colliding with application payload. | Application args/kwargs, bounded results, and history records |
| async task → machine ownership | Cancellation may interrupt before or after commit without stranding ownership. | Task-local selection state and cancellation |
| Python runtime → mypyc extension | Native field layout and coercion must preserve pure-Python validation and behavior. | Carrier fields, dispatch state, and public results |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Evidence | Status |
|-----------|----------|-----------|----------|-------------|---------------------|--------|
| T-28-01 | Tampering | `internal` public boundary | high | mitigate | Exact-bool validation and pure/native structural tests in `tests/test_transition_modes.py` and `tests/test_mypyc_guard.py`. | closed |
| T-28-02 | Tampering | canonical request transaction | high | mitigate | Canonical identity, prepare-all/publish-once behavior, fingerprints, and interruption tests in graph, property, and builder suites. | closed |
| T-28-03 | Tampering / Information Disclosure | callback/result boundary | medium | mitigate | Immutable mode metadata, unchanged payload assertions, and bounded error checks in transition-mode tests. | closed |
| T-28-04 | Denial of Service | registration ownership | high | mitigate | Single-owner `finally` release, deterministic contention/interruption, and reuse tests. | closed |
| T-28-05 | Denial of Service | singleton/group dispatch | high | mitigate | Selected-entry scalar plus structural guards rejecting scans, sorting, reflection, and dispatch-time collection copies. | closed |
| T-28-06 | Tampering | selected mode scalar | high | mitigate | Runtime consumes the validated selected entry's immutable `internal` value; priority and failure tests cover selection. | closed |
| T-28-07 | Tampering | commit/history publication | high | mitigate | Pre/post-commit failure matrices prove coherent state, history, and `committed` publication. | closed |
| T-28-08 | Tampering / Information Disclosure | callbacks and failure results | medium | mitigate | Payload preservation, bounded public errors, and exactly-once failure observation are covered synchronously. | closed |
| T-28-09 | Denial of Service | lifecycle ownership | high | mitigate | One public ownership/finalization boundary with synchronous and asynchronous reuse proof. | closed |
| T-28-10 | Denial of Service | priority dispatch | high | mitigate | Singleton lookup/local candidate-loop structural guards and mixed-mode priority tests. | closed |
| T-28-11 | Tampering | pure/native exact-bool boundary | high | mitigate | Object-typed compiled boundary, exact runtime validation, mutation fingerprints, and dual-origin tests. | closed |
| T-28-12 | Tampering | compiled carrier publication | high | mitigate | Exact carrier field/order guards and native prepare-all/publish-once regression coverage. | closed |
| T-28-13 | Tampering / Information Disclosure | async callbacks/results | medium | mitigate | Async tests prove mode stays in library metadata while application payload remains unchanged and errors stay bounded. | closed |
| T-28-14 | Denial of Service | cancellation and async ownership | high | mitigate | Single finalizer, bare re-raise, `finally` release, event-handshake cancellation, and successful reuse tests. | closed |
| T-28-15 | Denial of Service | compiled dispatch complexity | high | mitigate | AST/semantic guards require direct lookup or a local candidate loop and reject unbounded dispatch work. | closed |

All threats in the plan-time register are mitigated. No accepted or transferred risks are required.

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-16 | 15 | 15 | 0 | Codex orchestration, ASVS L1 |

The audit used the plan-time STRIDE registers from all three Phase 28 plans, their execution summaries, the clean code-review result, and the validated requirement/test map. Because the register was authored during planning, all mitigations were closed by direct implementation or automated evidence, and the configured depth is ASVS L1, the security workflow's clean-register short circuit applied without a deeper auditor pass.

---

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented (none).
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-16
