---
phase: 17
slug: atomic-transition-lifecycle
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-01
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, transfers, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Caller → transition runtime | Public trigger, callback, guard, handler, and observer inputs enter the compiled lifecycle core | Trigger/state identifiers, positional args, kwargs, user code, exceptions |
| Runtime → user callbacks | The machine invokes registered user code in a documented staged order | State objects, trigger, caller payload |
| Runtime → result/diagnostics | Failures become structured results and redacted diagnostics | Stage, committed flag, safe error text, private cause identity |
| Source tree → native evidence | mypyc compilation can shadow Python source during verification | Compiled extension, import origin, performance and semantic observations |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-17-01 | Tampering / Repudiation | Lifecycle outcomes | high | mitigate | Fail-fast staged failures and suffix-suppression/state/result matrix | closed |
| T-17-02 | Tampering | Commit and history | high | mitigate | History record prepared before mutation; no callback/await in commit; sync/async commit-fault tests | closed |
| T-17-03 | Denial of Service / Tampering | Failure observers | high | mitigate | Snapshot registry and isolate one ordered observer pass across `BaseException` failures | closed |
| T-17-04 | Information Disclosure | Results and logs | high | mitigate | Cause excluded from repr/equality; stage/type metadata only; secret-sentinel tests | closed |
| T-17-05 | Denial of Service / Tampering | Async cancellation | high | mitigate | Finalize once then bare re-raise; event-synchronized identity/state/history/suffix tests | closed |
| T-17-06 | Tampering | Sync/async parity | high | mitigate | One stage catalog, paired runners, and shared order/parity matrices | closed |
| T-17-07 | Spoofing | Native verification | high | mitigate | Explicit overlay inventory, pure shadow rejection, fresh build, and asserted import origin | closed |
| T-17-08 | Denial of Service | Hot path | high | mitigate | Slots guard and fresh compiled lifecycle/trigger performance floors at 200,000 ops/sec | closed |
| T-17-09 | Tampering | Reentrancy/concurrency | high | transfer | Phase 18 owns rejection/serialization; Phase 17 makes no closure claim | closed |
| T-17-10 | Spoofing / Tampering | Installed artifacts | high | transfer | Phase 20 owns installed wheel/sdist parity; Phase 17 claims source-tree parity only | closed |

---

## Accepted Risks Log

No accepted risks. T-17-09 and T-17-10 are explicit milestone-phase transfers, not accepted omissions.

---

## Verification Evidence

The independent ASVS L1 audit verified all 10 threats against final code, tests, documentation, and evidence after the converged review fixes. `uv run python tools/phase16_isolated_verify.py --suite phase17` exited 0 with asserted pure and freshly compiled semantic matrices, compiled lifecycle/trigger throughput, slots policy, 1,267/1,267 pure tests, Ruff, mypy, Sphinx HTML, three doctests, and baseline freshness.

Known non-failing mypyc cancellation deprecation warnings are tracked in bead `fast_fsm-2fh`; they do not weaken a threat mitigation.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-01 | 10 | 10 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks reviewed; none recorded.
- [x] Transfers are assigned to Phases 18 and 20 without false closure claims.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-01
