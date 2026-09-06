---
status: complete
phase: 20-installed-artifact-parity-release-proof
source:
  - 20-01-SUMMARY.md
  - 20-02-SUMMARY.md
  - 20-03-SUMMARY.md
  - 20-04-SUMMARY.md
  - 20-05-SUMMARY.md
  - 20-06-SUMMARY.md
started: 2026-09-05T23:39:36Z
updated: 2026-09-06T04:42:01Z
---

## Tests

### 1. Shared hardened-behavior oracle
expected: Deterministic shared hardened-behavior oracle with a payload-safe lifecycle tracer and complete scenario inventory.
result: pass
source: automated
coverage_id: 20-01-D1

### 2. Fresh pure and compiled wheel parity
expected: Exact local pure and compiled wheels install into neutral fresh environments and match source semantic records.
result: pass
source: automated
coverage_id: 20-01-D2

### 3. Runtime and artifact identity binding
expected: Runtime origin, distribution version, build intent, loader class, archive SHA-256, and native architecture are fail-closed before semantic acceptance.
result: pass
source: automated
coverage_id: 20-01-D3

### 4. Substantive installed compiled oracle
expected: Installed compiled wheels execute the substantive shared oracle rather than an import smoke test.
result: pass
source: automated
coverage_id: 20-01-D4

### 5. Explicit compiled intent
expected: Explicit compiled builds reject compiler failures and archives without a native fast_fsm.core member while AUTO and PURE retain their distinct contracts.
result: pass
source: automated
coverage_id: 20-02-D1

### 6. Sdist derivation lineage
expected: A bounded sdist archive produces explicit pure and compiled wheels whose installed evidence is tied to one parent filename and SHA-256.
result: pass
source: automated
coverage_id: 20-02-D2

### 7. Unsafe sdist rejection
expected: Unsafe sdist paths, member types, duplicate destinations, size limits, native residue, and invalid child lineage fail before artifact acceptance.
result: pass
source: automated
coverage_id: 20-02-D3

### 8. Canonical evidence matrix
expected: Canonical release/local artifact matrix projection rejects substituted and incomplete evidence while preserving deterministic output.
result: pass
source: automated
coverage_id: 20-03-D1

### 9. Static and tag-time identity checks
expected: Static v0.3.0 identity and non-mutating tag-time commit equality are fail-closed.
result: pass
source: automated
coverage_id: 20-03-D2

### 10. Historical evidence provenance
expected: Historical Phase 16-19 evidence uses complete recorded/unavailable provenance with no release-gate substitution.
result: pass
source: automated
coverage_id: 20-04-D1

### 11. Slots evidence
expected: Static and recursive runtime slots evidence agree with contributor instructions and SPR on exactly three exceptions.
result: pass
source: automated
coverage_id: 20-04-D2

### 12. Core-operation invariants
expected: Four core runtime operations have direct-registry invariant tests over small, medium, and large unrelated topologies, with coarse scaling only as a regression backstop.
result: pass
source: automated
coverage_id: 20-05-D1

### 13. Diagnostic budget boundaries
expected: Work, result, dense-cell, and path-expansion diagnostics retain exact-limit success and one-less reserve-before-work failure evidence outside runtime benchmarks.
result: pass
source: automated
coverage_id: 20-05-D2

### 14. Installed compiled performance
expected: An exact installed compiled wheel asserts native origin before recording warmup, at least three samples, and a passing 200000 ops/sec median.
result: pass
source: automated
coverage_id: 20-05-D3

### 15. Historical performance prerequisites
expected: Categorical Phase 16-19 history is required before release-authorizing installed performance, while historical and pure records cannot populate the compiled key.
result: pass
source: automated
coverage_id: 20-05-D4

### 16. Evidence-only workflow
expected: Exact-SHA evidence-only workflow and structural no-publish contract.
result: pass
source: automated
coverage_id: 20-06-D1

### 17. Tag-only release topology
expected: Tag-only aggregate, identity, and final release dependency graph.
result: pass
source: automated
coverage_id: 20-06-D2

### 18. Local non-authorizing readiness
expected: Local non-authorizing artifact/readiness projection.
result: pass
source: automated
coverage_id: 20-06-D3

### 19. Hosted native release-evidence checkpoint
expected: Release Evidence is dispatched for the intended exact commit, and the read-only pre-tag inspection succeeds for that run and its 40-character SHA. The terminal release-profile aggregate must confirm the complete hosted native matrix, exact record/artifact SHA bindings, semantic parity, native origins, and installed compiled performance before any tag is created.
result: pass
source: hosted-and-automated
coverage_id: 20-06-D4
rationale: Read-only Release Evidence run [34010662876](https://github.com/radioflyer28/fast_fsm/actions/runs/34010662876) passed its terminal aggregate for exact SHA `84d86cd2b91f8042f0a6a15945f4be10035e1329`; the independent `release-hosted-prerelease-check` downloaded and recomputed the same release-profile manifest. No tag, release, or publication was created.

## Summary

total: 19
passed: 19
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
