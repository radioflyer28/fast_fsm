---
phase: 15
slug: release-baseline-evidence-harness
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-08-29
verified: 2026-08-29
---

# Phase 15 — Security

> Post-execution verification of the complete plan-authored threat register. All mitigations are implemented; the five low-severity accepted risks are explicitly recorded below.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Build inputs | Build selectors, local filesystem/native shadows, archives, subprocess results, and exact dependency/tool pins | Environment intent, paths, wheel metadata, structured tool output |
| Evidence | Pure-source verification, clean-checkout provenance, manifest generation, and stable freshness projection | Repository facts, selected platform/tool observations, test and coverage results |
| CI | Workflow events, third-party actions, Task provisioning, pushed commits, and hosted job conclusions | Source revision, action inputs, build artifacts, terminal job evidence |
| Publication | Immutable Git history, maintainer credentials, and the live GitHub release | Tag identity, release notes, public assets, authenticated edit authority |
| Documentation and runtime source | Generated claims, policy instructions, slots inventory, formatting, and docstring-only edits | Public prose, source structure, runtime-layout observations |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|----------|-------------|-----------------------|--------|
| T-15-01 | Tampering | build-mode environment | high | mitigate | Selector rejects invalid/conflicting intent; subprocess tests pass. | closed |
| T-15-02 | Tampering | pure-source import resolution | high | mitigate | Pre-import native scan, `.py` origin requirement, and non-destructive shadow tests pass. | closed |
| T-15-03 | Tampering | wheel artifact identity | high | mitigate | Filename, tags, metadata, native members, duplicates, and deterministic ordering are verified. | closed |
| T-15-04 | Information Disclosure | verifier output | medium | mitigate | Repository-relative paths and selected structured facts only; no environment serialization. | closed |
| T-15-05 | Denial of Service | crafted archive | low | accept | Central-directory-only inspection avoids extraction; maintainer CLI resource exhaustion is accepted. | closed |
| T-15-06 | Tampering | evidence manifest | high | mitigate | Deterministic generation, read-only comparison, runtime reconciliation, and regression tests pass. | closed |
| T-15-07 | Spoofing | subprocess/tool output | high | mitigate | Argument arrays, return checks, structured JUnit/coverage parsing, and metadata APIs are used. | closed |
| T-15-08 | Tampering | dependency/build resolution | high | mitigate | Exact pins, lock check, pure locked sync, and immediate preflight pass across CI. | closed |
| T-15-09 | Elevation of Privilege | release workflow | high | mitigate | Read-only default permissions; write authority remains publication-only and gated. | closed |
| T-15-10 | Repudiation | advisory ty result | low | accept | `ty` remains separately visible and advisory; mypy is the blocking type-check authority. | closed |
| T-15-11 | Tampering | v0.2.3 history | high | mitigate | Read-only tag inspection and release-history check preserve immutable identity. | closed |
| T-15-12 | Spoofing | clean-checkout provenance | high | mitigate | Committed clean pure checkout, locked sync, immediate origin preflight, and manifest evidence pass. | closed |
| T-15-13 | Tampering | developer native artifacts | high | mitigate | Native shadows fail with exact paths and survive unchanged; clean proof uses isolation. | closed |
| T-15-14 | Repudiation | correction wording | medium | mitigate | One canonical correction file is tested against changelog/history and the live release. | closed |
| T-15-15 | Information Disclosure | baseline environment | low | accept | Coarse Python/platform/tool observations are intentionally public; paths and secrets are excluded. | closed |
| T-15-16 | Spoofing | narrative evidence claims | medium | mitigate | Durable rounded claims link to exact tracked evidence. | closed |
| T-15-17 | Tampering | agent workflow instructions | medium | mitigate | Task/CLI/source policy agrees across authoritative documentation surfaces. | closed |
| T-15-18 | Repudiation | slots exception policy | medium | mitigate | Both exceptions, rationales, recursive inventory, ADR, and executable audit are present. | closed |
| T-15-19 | Information Disclosure | documentation | low | accept | Reviewed public tool/platform facts are intentional; secrets and full environments remain excluded. | closed |
| T-15-20 | Elevation of Privilege | GitHub release edit | high | mitigate | Explicit user authorization, repository-scoped command, authenticated preflight, and no token capture. | closed |
| T-15-21 | Tampering | release body/tag/assets | high | mitigate | Pre/post comparison preserved tag identity and all 25 assets; only notes changed. | closed |
| T-15-22 | Repudiation | publication claim | medium | mitigate | Live URL and normalized canonical-body assertion are recorded in `15-05-SUMMARY.md`. | closed |
| T-15-23 | Information Disclosure | credentials/output | high | mitigate | Authentication details/body capture paths are excluded; credential-store token was never printed. | closed |
| T-15-24 | Tampering | visualization formatting | medium | mitigate | Scoped formatter-only diff, Ruff, focused tests, and review confirm behavior preservation. | closed |
| T-15-25 | Tampering | advanced test repair | medium | mitigate | Only the unused binding changed; assertions and focused tests remain intact. | closed |
| T-15-26 | Spoofing | Actions run selection | high | mitigate | Run 33286906906 matches exact SHA `8c1abdffa6f2d8b688be45472e54eec8b57d8c40`; 29/29 jobs succeeded. | closed |
| T-15-27 | Repudiation | supported-Python proof | high | mitigate | Named Python 3.10–3.14 pure-sdist jobs all reached terminal success. | closed |
| T-15-28 | Tampering | slots-policy inventory | high | mitigate | Fail-closed recursive static audit, runtime reconciliation, registry checks, and negative tests pass. | closed |
| T-15-29 | Tampering | runtime source semantics | high | mitigate | Five approved docstring regions only; normalized AST, runtime checks, focused tests, and review pass. | closed |
| T-15-30 | Repudiation | documentation gate | medium | mitigate | Strict HTML, rendered-name checks, doctest, focused tests, and hosted jobs pass. | closed |
| T-15-31 | Information Disclosure | public docstring examples | low | accept | Existing illustrative values are intentionally public and contain no paths, credentials, or secrets. | closed |
| T-15-32 | Tampering | Task runner supply chain | high | mitigate | Official action is full-SHA pinned and every consumer requests exact Task 3.53.1. | closed |
| T-15-33 | Denial of Service | Task-consuming CI jobs | high | mitigate | Structural/mutation tests require correct setup before every Task invocation; hosted CI passes. | closed |
| T-15-34 | Tampering | existing CI contracts | high | mitigate | Independent jobs, matrices, pure preflight, compiled smoke, and benchmark contracts remain intact. | closed |
| T-15-35 | Repudiation | CI repair claim | medium | mitigate | RED/GREEN evidence, scoped SHAs, and the exact terminal run are recorded. | closed |
| T-15-36 | Tampering | stable manifest comparison | high | mitigate | Fail-closed major/minor normalization preserves exact patches and strict comparison elsewhere. | closed |
| T-15-37 | Tampering | test/coverage baseline refresh | high | mitigate | Explicit write/check split, exact 879/879 baseline, coverage guard, and second-checkout gate pass. | closed |
| T-15-38 | Spoofing | pure-source baseline | high | mitigate | Pure mode and source preflight precede collection; manifest records `.py` origin. | closed |
| T-15-39 | Repudiation | hosted completion claim | high | mitigate | Diagnostic run is separated from final exact-SHA run 33286906906 and bead closure evidence. | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-15-01 | T-15-05 | The maintainer-only archive inspector never extracts members; possible excessive inspection time for a maliciously huge archive is outside this phase's service threat model. | Phase 15 plan approval | 2026-08-29 |
| AR-15-02 | T-15-10 | Advisory `ty` feedback may be ignored by design; blocking mypy and visible hosted job history retain authority and auditability. | Phase 15 plan approval | 2026-08-29 |
| AR-15-03 | T-15-15 | Coarse platform and tool facts are deliberately published as reproducibility evidence while paths, environment dumps, and secrets are excluded. | Phase 15 plan approval | 2026-08-29 |
| AR-15-04 | T-15-19 | Public documentation intentionally exposes reviewed tool/platform versions from the manifest and no sensitive environment detail. | Phase 15 plan approval | 2026-08-29 |
| AR-15-05 | T-15-31 | Illustrative public API values are intentionally published and contain no environment paths, credentials, or release secrets. | Phase 15 plan approval | 2026-08-29 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open at/above high | Run By |
|------------|---------------|--------|--------------------|--------|
| 2026-08-29 | 39 | 39 | 0 | gsd-security-auditor (ASVS L1) |

The auditor reran the focused build/evidence suite, `uv lock --check`, Ruff, release-history and slots-policy checks, and independently queried the live exact-SHA Actions run and v0.2.3 release. No unregistered threat flags were found.

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented in the Accepted Risks Log.
- [x] All 34 mitigated threats have implementation and executable evidence.
- [x] `threats_open: 0` confirmed at the configured `high` blocking threshold.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-08-29
