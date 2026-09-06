---
phase: 20
slug: installed-artifact-parity-release-proof
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-05
---

# Phase 20 — Security

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Build artifact → native verifier | A cross-platform wheel must be bound to a matching native runtime before acceptance. | Wheel bytes, SHA-256, tags, runtime facts |
| Evidence records → aggregate | Downloaded records must exactly represent the declared release matrix. | Bounded JSON evidence and provenance |
| Evidence workflow → tag release workflow | Manual/reusable evidence cannot create a release. | Read-only aggregate outputs |
| Aggregate/tag identity → release job | The sole write-capable job must receive complete approved evidence and tag equality. | Aggregate manifest, exact SHA, approved asset hashes |
| Local projection → release authorization | Locally available proof cannot authorize a hosted/public release. | Non-authorizing local aggregate |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-20-23 | Tampering | Artifact routing/native evidence | high | mitigate | Canonical matrix, exact artifact/runtime matching, and exact-cell aggregate reconciliation. | closed |
| T-20-24 | Spoofing | Installed artifact origin | high | mitigate | Neutral fresh environment verifies provenance, containment, extension loader, and architecture before semantic acceptance. | closed |
| T-20-25 | Tampering | Third-party actions | high | mitigate | All executable actions use full immutable SHAs with adjacent version provenance and mutation-tested pins. | closed |
| T-20-26 | Elevation of privilege | Release-gate bypass | critical | mitigate | Evidence workflow is read-only and release-free; only tag-triggered final job has `contents: write` after aggregate and tag identity. | closed |
| T-20-27 | Tampering | Downloaded evidence | high | mitigate | Bounded strict parsing, exact cell set, uniqueness, coherent provenance, and sdist-lineage reconciliation. | closed |
| T-20-28 | Repudiation | Hosted execution claims | medium | mitigate | Explicit exact-SHA, terminal evidence-only run and read-only artifact inspection are required before tagging. | closed |
| T-20-29 | Elevation of privilege | Local projection authorization | high | mitigate | Local profile is non-authorizing; release consumers accept only the `release` profile and structural tests prohibit hosted/release calls from local readiness. | closed |

## Accepted Risks Log

No accepted risks.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-05 | 7 | 7 | 0 | gsd-security-auditor |

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks documented.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-05
