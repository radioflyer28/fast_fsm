---
phase: 16
slug: canonical-graph-dispatch-invariants
status: verified
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-01
verified: 2026-09-01
---

# Phase 16 — Security

> ASVS Level 1 verification of the plan-time STRIDE register for canonical graph, dispatch, builder, history, and evidence boundaries.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Caller objects → canonical registry | Names, identities, endpoints, batches, capacities, and trigger context enter mutable runtime state. | Untrusted in-process objects and payload metadata |
| Mutation request → graph/history commit | Validation must complete before authoritative dictionaries, versions, caches, or bounded history change. | Topology and lifecycle state |
| Wrapper/declarative metadata → evaluator | Nested guards and selected handlers may hide async work, cycles, or side effects. | User-defined executable behavior |
| Mutable runtime → public/tool snapshots | Observers need coherent structural data without mutation authority or internal buffer access. | Topology and history records |
| Developer checkout → pure/compiled evidence | Native shadows, dirty files, and migration records must not spoof the implementation or authorize weaker floors. | Build provenance and quality evidence |
| Phase 16 → later lifecycle/ownership work | Phase 16 must not claim callback ordering or concurrent ownership contracts assigned to Phases 17 and 18. | Deferred behavioral guarantees |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-16-01 | Spoofing / Tampering | State and endpoint identity | high | mitigate | Canonical registry resolution and exact identity checks precede commit; foreign/equality/Unicode fingerprint tests prove rejection is atomic. | closed |
| T-16-02 | Tampering | Batch mutation and topology wiring | high | mitigate | Whole requests and builder candidates are materialized and validated before a single publish step; later-invalid and repair tests prove no partial state. | closed |
| T-16-03 | Repudiation / Tampering | Graph version and snapshot | medium | mitigate | Versions advance only on topology changes; fresh immutable, deterministically sorted snapshot records come from canonical dictionaries. | closed |
| T-16-04 | Denial of Service | Wrapper traversal and async detection | high | mitigate | Identity-aware iterative traversal rejects active cycles, supports shared DAGs, and is covered at depth in pure and compiled modes. | closed |
| T-16-05 | Information Disclosure / Denial of Service | Kwarg preparation and logging | high | mitigate | Context is filtered before the 50-entry cap, copied per evaluation, and never logged with raw values; flood, mutation, order, and caplog tests pass. | closed |
| T-16-06 | Tampering | Sync/async guard parity | medium | mitigate | Shared preparation and child classification drive all four public paths; positional, sanitized keyword, result, and awaitable matrices pass. | closed |
| T-16-07 | Tampering | Builder publication and cache | high | mitigate | Preflight, local candidate construction, cache-last publication, and complete post-build freezing are covered by failure/repair and every-mutator tests. | closed |
| T-16-08 | Tampering | Declarative side effects | high | mitigate | Canonical metadata dispatches through one ordinary seam; sync/async counters prove each selected handler runs exactly once. | closed |
| T-16-09 | Denial of Service / Tampering | History capacity and eviction | medium | mitigate | Positive non-bool integer validation occurs before assignment and bounded `deque` storage provides O(1) FIFO eviction and copy-on-read. | closed |
| T-16-10 | Tampering | Lifecycle failure ordering | low | accept | Phase 16 deliberately preserves existing relative placement and asserts only successful exactly-once behavior; Phase 17 owns failure and ordering hardening. | closed |
| T-16-11 | Spoofing | Module and artifact origin | high | mitigate | Fresh exports overlay explicit files, reject developer native shadows, select build mode explicitly, and assert `.py` or freshly built native origin before tests. | closed |
| T-16-12 | Denial of Service | Dispatch, slots, and history performance | high | mitigate | Hot paths retain dictionary/deque/slot layouts; fresh compiled gates preserve the 200,000 ops/sec trigger floor and bounded history ratio. | closed |
| T-16-13 | Repudiation / Tampering | Evidence and documentation drift | medium | mitigate | Reviewed writes, no-follow migration authorization, read-only freshness checks, Sphinx/doctests, and exact environment-labelled measurements keep claims auditable. | closed |
| T-16-14 | Tampering | Concurrent snapshot interpretation | medium | transfer | Documentation limits Phase 16 to single-owner structural semantics; Phase 18 owns explicit ownership and locking behavior. | closed |

*Only open threats at or above `high` count toward `threats_open`; none remain.*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-16-01 | T-16-10 | Callback failure and commit ordering are intentionally unchanged here so Phase 16 does not pre-empt the explicit Phase 17 lifecycle contract. The project is pre-production, and Phase 17 is a blocking milestone phase. | Milestone context / plan approval | 2026-09-01 |

Transferred risk T-16-14 remains tracked by Phase 18 and is not represented as a Phase 16 security gap.

---

## Verification Evidence

- Clean Phase 16 code review: cycle 5, iteration 3, zero findings.
- `uv run python tools/phase16_isolated_verify.py --suite phase16`: exit 0.
- Asserted pure and freshly compiled semantic matrices: passed.
- Compiled trigger/history performance selection: passed, including the 200,000 ops/sec floor.
- Pure release gate: 1,221/1,221 tests, 96.64% total coverage, 95.13% `core.py` coverage.
- Ruff, strict mypy, Sphinx HTML warnings-as-errors, three doctests, slot policy, source-origin checks, and read-only baseline freshness: passed.
- Summary threat flags: none unresolved.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-01 | 14 | 14 | 0 | GSD secure-phase (ASVS L1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-01
