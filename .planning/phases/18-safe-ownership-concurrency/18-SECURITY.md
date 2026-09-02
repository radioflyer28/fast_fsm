---
phase: 18
slug: safe-ownership-concurrency
status: blocked
threats_open: 2
asvs_level: 1
block_on: high
created: 2026-09-02
---

# Phase 18 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Public writer admission | Public sync and async mutations enter per-machine ownership before preparation or mutation | Trigger names, graph topology, callbacks, state, and history |
| Async execution ownership | A machine binds permanently to one event loop/thread and distinguishes owner task/root from independent tasks | Loop identity, task identity, causal-root metadata |
| Declarative guard marker | Context-local prepared-guard state must apply only to the exact machine and transition that produced it | Machine identity and source/trigger/target tuple |
| Hosted native evidence | Local release gating relies on GitHub Actions evidence for the exact candidate SHA | Commit SHA, Python-version matrix, job conclusions, native module origin |
| Error and log boundary | Ownership failures cross to callers and observers without exposing supplied values | Stable operation/category text only |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-18-01 | Tampering | Reentry admission and public writers | high | mitigate | Pre-acquisition same-owner/root rejection; complete writer-entry AST and behavioral coverage in both origins | closed |
| T-18-02 | Denial of Service | Sync/async primitive and owner cleanup | high | mitigate | Per-instance primitives and unconditional `finally` cleanup with bounded reuse/cancellation regressions | closed |
| T-18-03 | Tampering/DoS | Cross-loop state and hosted native evidence | high | mitigate | Permanent loop/thread binding plus a successful exact-current-SHA Python 3.10–3.14 native matrix | open |
| T-18-04 | Denial of Service | Causal child task reentry | high | mitigate | Context-root rejection before lock acquisition; independent-machine progress regression | closed |
| T-18-05 | Tampering | Declarative prepared marker | high | mitigate | Validate the stored machine identity as well as source/trigger/target at consumption; add cross-machine collision regression | open |
| T-18-06 | Repudiation/Tampering | `safe_trigger()` ownership downgrade | high | mitigate | Ownership admission occurs outside ordinary exception conversion; boundary regressions require ownership errors to escape | closed |
| T-18-07 | Denial of Service/Tampering | Cancellation windows | high | mitigate | Exactly-once failure finalization, bare cancellation propagation, unconditional cleanup, bounded waiting/owning reuse tests | closed |
| T-18-08 | Information Disclosure | Ownership errors and logs | high | mitigate | Fixed payload-free categories with error/result/log secret-sentinel assertions | closed |
| T-18-09 | Denial of Service | Fairness, timeout, queue-order, and offload expectations | medium | accept | Public docs and ADR-005 promise mutual exclusion and loop progress only; no fairness, timeout, queue-order, or automatic-offload guarantee | closed |

*Only open threats at or above the configured `high` threshold count toward `threats_open`.*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-18-01 | T-18-09 | Queue fairness, acquisition timeouts, ordering, and automatic callback offload are intentionally outside the Phase 18 contract; promising them would require a different scheduler/API design. The non-promises are explicit in README, Quick Start, architecture guidance, and ADR-005. | Project decision D-06 / Phase 18 plan | 2026-09-02 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-02 | 9 | 7 | 2 blocking | gsd-security-auditor |

The initial audit verified fresh pure/native focused suites and the compiled performance gate. It blocked advancement because the current candidate SHA lacked hosted matrix evidence and declarative marker consumption did not compare its stored machine identity.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed
- [ ] `status: verified` set in frontmatter

**Approval:** blocked pending T-18-03 and T-18-05 mitigation verification
