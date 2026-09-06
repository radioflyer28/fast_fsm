# Phase 20: Installed Artifact Parity & Release Proof - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-04
**Phase:** 20-installed-artifact-parity-release-proof
**Areas discussed:** Artifact matrix and isolation, Shared hardened conformance, Identity and provenance evidence, Performance and publish gate

---

## Artifact Matrix and Isolation

| Option | Description | Selected |
|--------|-------------|----------|
| Installed explicit-mode matrix | Build concrete pure wheel, sdist-derived outcomes, and compiled wheels; install each in a clean environment and fail closed on compiled intent | ✓ |
| Source-export proxy | Treat fresh source and in-place compiled exports as release artifacts | |
| Build-only inspection | Inspect archive contents without executing substantive installed behavior | |

**User's choice:** Recommended default auto-selected under the user's standing authorization.
**Notes:** Installed origins must exclude checkout/editable paths; cross-built artifacts require native verification before publication.

---

## Shared Hardened Conformance

| Option | Description | Selected |
|--------|-------------|----------|
| One structured parity oracle | Run the same deterministic scenario suite across source, artifact, sync/async, builder, and declarative modes | ✓ |
| Mode-specific independent suites | Let each mode prove unrelated subsets of behavior | |
| Smoke tests plus source suite | Import and trigger installed artifacts, relying on source tests for deeper behavior | |

**User's choice:** Recommended default auto-selected under the user's standing authorization.
**Notes:** Mode differences are restricted to declared identity and performance fields; semantic records must otherwise match.

---

## Identity and Provenance Evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Per-artifact records plus strict aggregation | Record hashes, tags, origins, versions, architecture, intent, and conformance, then require a complete exact matrix | ✓ |
| One release-level summary | Record only aggregate pass/fail and artifact filenames | |
| Human checklist | Rely on maintainer inspection of wheel names and job logs | |

**User's choice:** Recommended default auto-selected under the user's standing authorization.
**Notes:** v0.3.0 identity must agree across tag, commit, metadata, docs, changelog, and installed artifacts.

---

## Performance and Publish Gate

| Option | Description | Selected |
|--------|-------------|----------|
| Native installed blocking gate | Enforce the 200k floor on an installed compiled wheel and make release creation depend on all evidence aggregation | ✓ |
| Source-tree benchmark gate | Keep the current in-place compiled benchmark as final proof | |
| Advisory artifact benchmark | Record installed performance without blocking release | |

**User's choice:** Recommended default auto-selected under the user's standing authorization.
**Notes:** Pure rates remain observations; diagnostic complexity uses deterministic budgets while runtime O(1) claims receive separate proof.

## the agent's Discretion

- Verifier module names and internal record types.
- CI job decomposition and local-versus-hosted matrix split.
- Stable benchmark warmup and sampling details.

## Deferred Ideas

- PyPI publication/trusted-publisher configuration, additional platforms, musllinux, PyPy, and a public runtime build-info API.
