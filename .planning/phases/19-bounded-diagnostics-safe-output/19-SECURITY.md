---
phase: 19
slug: bounded-diagnostics-safe-output
status: verified
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-04
---

# Phase 19 — Security

> Verified threat-mitigation record for bounded diagnostics, grammar-safe
> output, metadata-only tracing, application-owned logging, and trustworthy
> pure/compiled evidence.

---

## Trust Boundaries

| Boundary | Description | Data crossing |
|----------|-------------|---------------|
| Mutable machine → diagnostic snapshot | A diagnostic call must observe one ownership-consistent topology version. | State, transition, condition, and version scalars |
| Untrusted graph → diagnostic algorithms | Adversarial size, depth, cycles, and fan-out must remain bounded. | Graph topology and caller-selected limits |
| Caller text → output grammar | Labels and titles must remain inert data in Mermaid, PlantUML, and Markdown. | Untrusted text and control characters |
| Runtime payload → trace/redactor/record | Default tracing must not expose or inspect caller values. | Names, arguments, exceptions, and representations |
| Library logging → application logger | Library configuration must preserve host-owned handlers and state. | Handlers, filters, formatters, levels, propagation |
| Candidate checkout → evidence tree | Stale native artifacts or incomplete overlays must not certify a candidate. | Source inventory, compiled module, test evidence |
| Evidence writer → release manifest | Baselines must be generated atomically from the reviewed pure candidate. | Counts, coverage, origins, toolchain metadata |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Verified mitigation and evidence | Status |
|-----------|----------|-----------|----------|-------------|----------------------------------|--------|
| T-19-01 | Tampering | Snapshot capture | high | mitigate | One scalar ownership-consistent capture; mutation/call-count tests in `test_diagnostic_contracts.py`. | closed |
| T-19-02 | Denial of Service | Diagnostic budget | high | mitigate | Finite defaults and reserve-before-work accounting in `_diagnostics.py`; exact/one-less tests. | closed |
| T-19-03 | Information Disclosure | Budget exception | medium | mitigate | Fixed message and scalar-only status; hostile payload tests. | closed |
| T-19-04 | Repudiation | Counter/order evidence | medium | mitigate | Snapshot-index order and deterministic hash-seed assertions. | closed |
| T-19-05 | Tampering | Diagram/Markdown output | high | mitigate | Opaque IDs, final-sink encoders, and hostile grammar corpus. | closed |
| T-19-06 | Information Disclosure | Trace records | high | mitigate | Metadata-only records and complete sentinel scans in `test_logging_config.py`. | closed |
| T-19-07 | Information Disclosure | Redactor failure | high | mitigate | Strict output allowlist; ordinary failures become fixed categories without raw fallback; control-flow `BaseException` propagates before emission. | closed |
| T-19-08 | Tampering | Logging configuration | high | mitigate | Application objects preserved; transactional configuration and generation-safe restore tests. | closed |
| T-19-09 | Spoofing | Pure/compiled evidence | high | mitigate | Exact isolated overlays and asserted `.py`/native module origins. | closed |
| T-19-10 | Denial of Service | SCC/depth traversal | high | mitigate | Iterative O(V+E) algorithms with counted shared budget and long-chain/fan-out tests. | closed |
| T-19-11 | Denial of Service | Dense adapters | high | mitigate | Exact V²/V×events preflight before outer allocation. | closed |
| T-19-12 | Denial of Service | Path generation | high | mitigate | Iterative frames with independent length, result, and expansion limits. | closed |
| T-19-13 | Tampering | Legacy partial results | high | mitigate | Exhaustion raises before any partial legacy value escapes. | closed |
| T-19-14 | Repudiation | Set/hash traversal | medium | mitigate | Canonical snapshot ordering and two-hash-seed evidence. | closed |
| T-19-15 | Spoofing | Duplicate-name comparison | high | mitigate | Position-keyed ordered entries and stable tie-break tests. | closed |
| T-19-16 | Tampering | Empty aggregates | medium | mitigate | Exact zero-input schema with undefined values represented as `None`. | closed |
| T-19-17 | Tampering | Nested budget/status | high | mitigate | One ledger per top-level call and final status captured after all work. | closed |
| T-19-18 | Denial of Service | Dense reports | high | mitigate | Sparse default; explicit preflighted dense opt-in. | closed |
| T-19-19 | Information Disclosure | Diagnostic reports | medium | mitigate | Fixed categories and bounded scalar completion metadata. | closed |
| T-19-20 | Information Disclosure | Default trace | high | mitigate | Fixed metadata/count/key fields only; no caller payload or representation. | closed |
| T-19-21 | Information Disclosure | Custom redactor | high | mitigate | Minimum ephemeral event, bounded scalar allowlist, and fail-closed output handling. | closed |
| T-19-22 | Denial of Service | Disabled trace | high | mitigate | Level guard precedes allocation, traversal, representation, and redactor lookup. | closed |
| T-19-23 | Tampering | Application handlers | high | mitigate | Private owned-handler marker; only library-owned handlers are removed or closed. | closed |
| T-19-24 | Tampering | Restore handle | high | mitigate | Identity, generation, and current-value comparison with idempotent restore. | closed |
| T-19-25 | Tampering | Diagram directives | high | mitigate | Opaque identifiers and grammar-specific final-sink encoders. | closed |
| T-19-26 | Tampering | Markdown grammar | high | mitigate | Dedicated heading/cell encoding and already-rendered fenced composition. | closed |
| T-19-27 | Spoofing | Label-derived identity | high | mitigate | IDs derive solely from snapshot position; collision corpus passes. | closed |
| T-19-28 | Tampering | Mixed JSON/adjacency | high | mitigate | One captured graph; supplied adjacency is fully equivalence-checked or fixed-rejected. | closed |
| T-19-29 | Denial of Service | Dense JSON/document | high | mitigate | Sparse defaults and reserve-before-allocation dense opt-in. | closed |
| T-19-30 | Spoofing | Public complexity contract | high | mitigate | ADR/SPR/API docs publish exact fields, counters, and exhaustion semantics. | closed |
| T-19-31 | Information Disclosure | Logging documentation | high | mitigate | Safe default, explicit redactor boundary, failure behavior, and ownership are documented and tested. | closed |
| T-19-32 | Tampering | ADR/SPR history | medium | mitigate | Accepted append-only ADR-006 and same-task living SPR updates are present. | closed |
| T-19-33 | Denial of Service | Dense/path documentation | medium | mitigate | Sparse default, dense preflight units, and finite path controls are published. | closed |
| T-19-34 | Spoofing | Phase evidence | high | mitigate | Separate temporary exports, complete inventory overlays, and origin assertions. | closed |
| T-19-35 | Tampering | Release baseline | high | mitigate | Isolated pure writer, atomic fsync/rename export, reviewed diff, and read-only freshness gate. | closed |
| T-19-36 | Repudiation | Performance claims | medium | mitigate | Evidence records exact commands, origins, counts, operations, and environment; timing is observational. | closed |
| T-19-37 | Denial of Service | Regression scope | medium | mitigate | Focused selections plus one bounded closure suite; no watch or sleep loop. | closed |
| T-19-38 | Information Disclosure | Evidence/log capture | high | mitigate | Full-record sentinel tests run in pure and compiled origins; manifest stores categories/counts only. | closed |

## Accepted Risks Log

No accepted risks.

## Unregistered Threat Flags

None. No Phase 19 summary contains a `## Threat Flags` entry.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-04 | 38 | 38 | 0 | GSD security auditor |

The targeted diagnostic, output, logging, validation, visualization,
performance, and mypyc-guard suite passed during the audit. The clean code
review and Nyquist audit provide additional independent evidence; the
authoritative Phase 19 suite passes from asserted pure and fresh compiled
origins with the strict uninstrumented throughput gate enabled.

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented; none were accepted.
- [x] `threats_open: 0` confirmed at the configured `high` threshold.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-04.
