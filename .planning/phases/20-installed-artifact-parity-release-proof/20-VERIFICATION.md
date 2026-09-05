---
phase: 20-installed-artifact-parity-release-proof
verified: 2026-09-05T23:25:00Z
status: human_needed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "The tracked baseline now has v0.3.0 identity, current schema, and a populated local expected matrix."
  gaps_remaining: []
  regressions: []
decision_coverage:
  honored: 14
  total: 14
  not_honored: []
human_verification:
  - test: "Dispatch Release Evidence for the exact intended commit, then run release-hosted-prerelease-check with that run ID and 40-character SHA."
    expected: "A terminal release-profile aggregate confirms the exact SHA, complete hosted native matrix, record/artifact SHA bindings, semantic parity, and native performance before any tag."
    why_human: "No hosted workflow was dispatched during this phase; local proof and YAML cannot establish actual runner availability or native execution on every hosted target."
---

# Phase 20: Installed Artifact Parity & Release Proof Verification Report

**Phase Goal:** Maintainers can publish v0.3.0 only when installed pure and compiled artifacts prove the same hardened behavior, identity, and performance.

**Status:** human_needed
**Re-verification:** Yes — baseline gap closed at `457f2c3`

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Explicit compiled builds fail closed and CI is wired to verify installed pure/compiled artifacts, not checkout imports. | ✓ VERIFIED | `setup.py` propagates compiled-mode errors; `verify_installed_wheel()` snapshots exact bytes, installs to a neutral fresh environment, checks archive/origin/architecture, then runs the oracle. |
| 2 | One deterministic oracle covers hardened sync, async, builder, declarative, pure, and installed compiled behavior. | ✓ VERIFIED | `tools/artifact_conformance.py` has allowlisted records for graph/guards, lifecycle, dispatch, ownership, diagnostics, output safety, logging, and sync/async semantics; the local direct and sdist-derived artifacts execute it. |
| 3 | Accepted artifact records bind bytes, metadata/version, module origin, architecture, intended type, and semantic parity. | ✓ VERIFIED | `release_evidence.py` validates all before accepting conformance/performance, then exact matrix aggregation rejects missing, mixed, duplicate, detached, or non-parity records. |
| 4 | Core operations have O(1) proof, diagnostic budgets remain separate, and installed compiled `trigger()` enforces the three-sample ≥200,000 ops/s median after native-origin checks. | ✓ VERIFIED | The non-authorizing local projection passed with fresh compiled wheel evidence; performance and diagnostic tests cover the named contracts. |
| 5 | Current release identity and baseline evidence substantiate v0.3.0 without representing hosted proof as complete. | ✓ VERIFIED | With `/private/tmp/fast-fsm-uv-0.12.6/uv-aarch64-apple-darwin/uv`, `task release-baseline-check` passes. The baseline now holds v0.3.0 wheel metadata and current schema/matrix data; no tag or hosted result is fabricated. |

**Score:** 5/5 truths verified (0 behavior-unverified)

### Required Artifacts

| Artifact | Status | Evidence |
| --- | --- | --- |
| `tools/artifact_conformance.py` | ✓ VERIFIED | Standalone oracle is copied into and executed by isolated installed environments. |
| `tools/release_evidence.py` | ✓ VERIFIED | Central artifact, identity, historical, matrix, performance, and slots authority used by Taskfile and workflows. |
| `setup.py` / `MANIFEST.in` | ✓ VERIFIED | Explicit compiled intent, `core.py`-only boundary, and sdist derivation inputs are implemented. |
| `evidence/release-baseline.json` | ✓ VERIFIED | Regenerated for v0.3.0 at `457f2c3`; pinned-toolchain freshness check passes. |
| `release-evidence.yml` | ✓ VERIFIED | Read-only exact-SHA evidence graph with terminal release-profile aggregate and no release job. |
| `release.yml` | ✓ VERIFIED | Tag-only route; final `github_release` is the sole `contents: write` job and has aggregate/tag-identity dependencies. |
| `Taskfile.yml` and runbooks | ✓ VERIFIED | Local projection is explicitly non-authorizing; hosted inspection is a separate read-only pre-tag command. |

### Key Link Verification

| From | To | Status | Details |
| --- | --- | --- | --- |
| Exact wheel path | Installed child oracle | ✓ WIRED | Private snapshot → neutral venv → copied probe → parent-validated evidence. |
| Explicit compiled intent | Native `fast_fsm.core` | ✓ WIRED | Compiler/native archive and runtime checks prevent AUTO fallback from certifying compiled evidence. |
| Native evidence records | Release aggregate | ✓ WIRED | Normal workflow dependencies deliver SHA-keyed records to `aggregate-matrix --profile release`. |
| Aggregate plus tag identity | `github_release` | ✓ WIRED | Only aggregate-approved, re-hashed assets can be staged by the sole write-capable job. |
| Local aggregate | Release authorization | ✓ WIRED | `build_release_authorization()` rejects non-`release` profiles. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Pinned baseline freshness | `PATH=/private/tmp/fast-fsm-uv-0.12.6/uv-aarch64-apple-darwin:$PATH task release-baseline-check` | Passed with `uv 0.12.6` | ✓ PASS |
| Full local readiness | Same PATH prefix with `task release-readiness-check` | Fresh run passed format, lint, mypy, full tests, docs, source/baseline checks, all local artifact/lineage/parity/origin/performance/slots checks; `ty` was separately advisory. | ✓ PASS |
| Release evidence regression | Same PATH prefix with `uv run pytest tests/test_release_evidence.py -q -x` | 201 passed | ✓ PASS |
| Historical provenance and slots | Same PATH prefix with `historical-evidence --check` and `slots-policy` | Both passed | ✓ PASS |

### Requirements Coverage

| Requirement | Status | Evidence |
| --- | --- | --- |
| REL-01 | ✓ SATISFIED (local) | Static v0.3.0 identity and fresh baseline pass; tag equality remains correctly tag-time. |
| REL-03 | ✓ SATISFIED | Compiled intent fails on compiler/native-output failure. |
| REL-07 | ✓ SATISFIED (local) | Direct and sdist-derived pure/compiled artifacts pass isolated proof. |
| TEST-01 | ✓ SATISFIED | Shared installed-capable deterministic oracle is active. |
| TEST-03 | ✓ SATISFIED (local) | Compiled installed wheel runs substantive oracle. |
| TEST-04 | ✓ SATISFIED | SHA, identity, origin, architecture, type, and parity validate before acceptance. |
| TEST-05 | ✓ SATISFIED | Historical evidence remains categorical/non-gating; fresh installed evidence and baseline are current. |
| TEST-06 | ✓ SATISFIED (local) | Native-origin-first installed compiled floor passed locally. |
| TEST-07 | ✓ SATISFIED | Four core-operation and separate diagnostic-boundary contracts are active. |

### Test Quality and Anti-Patterns

`tests/test_artifact_conformance.py`, `test_installed_artifacts.py`, `test_release_evidence.py`, `test_performance_benchmarks.py`, and `test_diagnostic_contracts.py` supply behavioral/value assertions. No requirement-linked test is disabled as its sole proof; compiler/platform fixture skips are supplementary. No unresolved `TBD`, `FIXME`, or `XXX` markers were found in Phase 20 implementation, workflows, tests, Taskfile, or runbooks.

### Decision Coverage

All 14 trackable CONTEXT decisions are represented in shipped artifacts (`check.decision-coverage-verify`: 14/14).

## Human Verification Required

### 1. Hosted native release-evidence checkpoint

**Test:** Dispatch the read-only **Release Evidence** workflow for the intended exact SHA. Before creating a tag, run:

`task release-hosted-prerelease-check FAST_FSM_HOSTED_RUN_ID=<id> FAST_FSM_EXPECTED_SHA=<40-char-sha>`

**Expected:** A successful terminal aggregate for the complete authoritative `release` matrix, with the exact SHA, full native runner records, downloaded artifact/evidence SHA bindings, parity, origin, and installed-performance proof.

**Why human:** Phase scope intentionally performed no remote dispatch, tag, release, or publication. The local projection and structural workflow tests cannot prove actual hosted runner availability or successful execution.

## Verdict

All locally executable Phase 20 proof now passes with the mandated uv 0.12.6 toolchain. The only remaining item is the intentional, pre-tag hosted evidence UAT; it is not a code gap and must not be reported as a passed hosted result.

---

_Verified: 2026-09-05T23:25:00Z_
_Verifier: the agent (gsd-verifier)_
