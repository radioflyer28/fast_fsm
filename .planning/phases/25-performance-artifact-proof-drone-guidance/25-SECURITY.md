---
phase: 25
slug: performance-artifact-proof-drone-guidance
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-07
---

# Phase 25 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Reviewed toolchain to baseline writer | The writer consumes `uv.lock` and local package/build inputs. | Executable identity, lockfile-pinned dependencies, generated manifest |
| Generated manifest to release proof | The tracked baseline carries quality, artifact, and performance assertions. | JSON evidence and generator-owned observations |
| Source tree to installed artifacts | Clean source and newly built pure/native wheels must remain distinguishable. | Wheel archives, import origins, conformance records |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-25-01 | Tampering | transition-slot insertion | high | mitigate | Immutable one-pass merge plus priority tests and artifact conformance proof. | closed |
| T-25-02 | Tampering | release-baseline manifest | high | mitigate | Strict JSON, static contract, freshness projection, and read-only checks. | closed |
| T-25-03 | Tampering | source and installed artifact identity | high | mitigate | Pure-source preflight, neutral install, origin, loader, hash, and conformance checks. | closed |
| T-25-04 | Safety | drone example | medium | mitigate | Prominent non-hardware/non-certified disclaimer and deterministic simulation only. | closed |
| T-25-05 | Integrity | complexity guidance | medium | mitigate | Documentation distinguishes O(1) lookup/singleton work from local O(k) candidate selection. | closed |
| T-25-06 | Availability | benchmark variance | low | accept | Observations are environment-labelled and never release thresholds. | open — below high threshold |
| T-25-07 | Tampering | dependency resolution | high | mitigate | `uv sync --locked` binds the reviewed dependency graph to `uv.lock`; the invoking `uv` version is retained only as environment metadata. | closed |
| T-25-08 | Tampering | evidence JSON inputs | high | mitigate | Bounded, strict parsing and static schema/identity checks. | closed |
| T-25-09 | Tampering | transition priority resolution | high | mitigate | Fixed ordered candidate selection with deterministic tie behavior and pure/native parity tests. | closed |
| T-25-10 | Safety | aircraft command timing | high | mitigate | Controller invokes commands only after a successful committed transition. | closed |
| T-25-11 | Information disclosure | simulated telemetry output | low | accept | Example emits scalar simulated facts only; real telemetry integration is excluded. | open — below high threshold |
| T-25-G01 | Tampering | baseline writer and verification children | high | mitigate | Standard locked synchronization precedes evidence collection; a particular package-manager binary is not a release gate. | closed |
| T-25-G02 | Tampering / Repudiation | baseline regeneration | high | mitigate | A pre-write snapshot plus constrained semantic/raw diff allowlist validates a candidate before any protected bytes change. | closed |
| T-25-G03 | Tampering | installed artifact provenance | high | mitigate | Archive, origin, loader, conformance, and installed-performance gates. | closed |
| T-25-G04 | Denial of service | dependency/cache availability | medium | accept | Normal `uv` cache and registry availability apply; an unavailable local cache may require an ordinary locked sync. | open — below high threshold |
| T-25-SC | Tampering | lockfile inputs | high | mitigate | `uv sync --locked` refuses lockfile resolution drift; no custom cache location or offline-only setting is required. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above the workflow security threshold count toward `threats_open`.*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-25-01 | T-25-06 | Host performance is recorded as non-gating observation data; a bounded local benchmark matrix cannot represent every deployment environment. | Project policy | 2026-09-07 |
| R-25-02 | T-25-11 | The simulation deliberately avoids hardware control and real telemetry persistence. | Project policy | 2026-09-07 |
| R-25-03 | T-25-G04 | Standard `uv` cache and registry availability remain an operational dependency. `uv.lock` and `--locked` protect resolution integrity without treating cache transport as a security boundary. | User-approved project policy | 2026-09-07 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-07 | 16 | 10 | 6 (3 blocking) | Phase 25 security auditor |
| 2026-09-07 | 16 | 13 | 3 (0 blocking) | Follow-up after user-approved lockfile-based policy and passing full readiness proof |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified. The remaining open items are documented accepted availability or simulation risks below the security threshold.

## Security Audit 2026-09-07

| Metric | Count |
|--------|-------|
| Threats found | 16 |
| Closed | 13 |
| Open | 3 (0 blocking) |

The mitigations were reclassified against the user-approved `uv.lock` plus
`uv sync --locked` policy. The full `task release-readiness-check` proof passed
with the normal local `uv 0.12.9` environment; protected baseline refresh tests
and the constrained writer remain in place.
