---
phase: 20-installed-artifact-parity-release-proof
plan: "01"
subsystem: release-evidence
tags: [uv, wheel, artifact-isolation, conformance, provenance, mypyc]
requires:
  - phase: 16-canonical-graph-dispatch-invariants
    provides: graph and guard invariants represented by the shared oracle
  - phase: 17-atomic-transition-lifecycle
    provides: committed destination-enter failure lifecycle contract
  - phase: 18-safe-ownership-concurrency
    provides: cancellation and reuse contract
  - phase: 19-bounded-diagnostics-safe-output
    provides: bounded diagnostics, safe rendering, and metadata-only logging contracts
provides:
  - checkout-independent deterministic semantic oracle for hardened Fast FSM behavior
  - exact-path fresh-environment pure/compiled wheel proof with archive and runtime identity binding
  - bounded, redacted rejection of provenance, child-output, and architecture spoofing
affects: [20-02, 20-03, 20-04, 20-05, 20-06, release-workflow]
actuals:
  tokens: 15934
  tasks: 3
  commits: 8
tech-stack:
  added: []
  patterns:
    - parent-computed archive identity with a copied child probe in a neutral uv environment
    - canonical scenario records with suite and semantic SHA-256 digests
    - staged archive, provenance, architecture, then semantic acceptance gates
key-files:
  created:
    - tools/artifact_conformance.py
    - tests/test_artifact_conformance.py
    - tests/test_installed_artifacts.py
  modified:
    - tools/release_evidence.py
key-decisions:
  - "Use one deterministic, checkout-independent oracle for source, pure-wheel, and compiled-wheel semantics."
  - "Keep absolute origin and artifact facts outside the semantic digest while binding them before semantic acceptance."
  - "Treat the venv interpreter entrypoint as authoritative without resolving its intentional base-interpreter symlink."
patterns-established:
  - "Artifact proof: inspect and hash archive → install exact path in a neutral uv venv → assert provenance/mode/architecture → accept conformance."
  - "Child evidence: strict duplicate-key/non-finite/bounded JSON parsing with fixed public failures and test-only bounded diagnostics."
requirements-completed: [REL-07, TEST-01, TEST-03, TEST-04]
coverage:
  - id: D1
    description: Deterministic shared hardened-behavior oracle with a payload-safe lifecycle tracer and complete scenario inventory.
    requirement: TEST-01
    verification:
      - kind: unit
        ref: tests/test_artifact_conformance.py
        status: pass
    human_judgment: false
  - id: D2
    description: Exact local pure and compiled wheels install into neutral fresh environments and match source semantic records.
    requirement: REL-07
    verification:
      - kind: integration
        ref: tests/test_installed_artifacts.py#test_tracer_installs_exact_artifact_and_matches_source_lifecycle
        status: pass
    human_judgment: false
  - id: D3
    description: Runtime origin, distribution version, build intent, loader class, archive SHA-256, and native architecture are fail-closed before semantic acceptance.
    requirement: TEST-04
    verification:
      - kind: integration
        ref: tests/test_installed_artifacts.py
        status: pass
    human_judgment: false
  - id: D4
    description: Installed compiled wheels execute the substantive shared oracle rather than an import smoke test.
    requirement: TEST-03
    verification:
      - kind: integration
        ref: tests/test_installed_artifacts.py#test_tracer_installs_exact_artifact_and_matches_source_lifecycle
        status: pass
    human_judgment: false
duration: 32m
completed: 2026-09-05
status: complete
---

# Phase 20 Plan 01: Installed Artifact Parity & Release Proof Summary

**A deterministic hardened-behavior oracle now proves source, exact pure-wheel, and exact compiled-wheel lifecycle parity from isolated installed environments.**

## Performance

- **Duration:** 32m
- **Started:** 2026-09-05T00:36:39Z
- **Completed:** 2026-09-05T01:08:53Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Created a standalone collector covering graph/guard, lifecycle/history, sync/async, builder/declarative, ownership/cancellation, diagnostics, output containment, and logging redaction.
- Added fresh-environment verification that hashes and inspects an exact wheel before installing it by absolute path, runs the copied probe from a neutral directory, and validates installed origins and provenance.
- Hardened the evidence boundary against checkout/editable provenance, native shadows, symlink escape, malformed or oversized child JSON, payload leakage, SHA/suite/semantic drift, and native architecture mismatches.

## Task Commits

1. **Task 1: Prove one pure and compiled installed lifecycle slice end to end** — `12ce7db`, `2119a5d`
2. **Task 2: Expand the oracle across every hardened scenario family** — `c6aa7f9`, `0961279`
3. **Task 3: Harden artifact isolation and evidence schema rejection** — `2e3a88a`, `44998f2`, `813ff4a`, `28c3ba0`

_TDD commits are intentionally split into RED test and GREEN implementation gates._

## Files Created/Modified

- `tools/artifact_conformance.py` — standalone canonical scenario collector and installed-runtime child probe.
- `tools/release_evidence.py` — exact wheel installer, archive/runtime identity validation, and bounded child-evidence gate.
- `tests/test_artifact_conformance.py` — deterministic inventory, parity, payload safety, and hash-seed regression coverage.
- `tests/test_installed_artifacts.py` — local pure/compiled wheel tracer plus provenance and malformed-evidence adversarial tests.

## Decisions Made

- Parent evidence computes the archive SHA-256 and requires the child probe to echo it; the child never chooses accepted artifact identity.
- Semantic records deliberately exclude archive paths, origins, timings, exception text, arguments, and keyword values; those facts stay in the verified evidence envelope.
- Compiled proof requires both an extension loader/origin and a matching platform/architecture wheel tag.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed unsupported `uv pip install --no-project` invocation**
- **Found during:** Task 1
- **Issue:** The installed-artifact path could not install a wheel because this uv subcommand does not accept that flag.
- **Fix:** Kept project/config discovery disabled through the sanitized environment and supported `--no-config` flag.
- **Files modified:** `tools/release_evidence.py`
- **Verification:** Pure and compiled exact-wheel tracer passed.
- **Committed in:** `2119a5d`

**2. [Rule 1 - Bug] Preserved the environment interpreter symlink**
- **Found during:** Task 1
- **Issue:** Resolving the virtual-environment interpreter followed its symlink to uv's externally managed base interpreter, preventing local installation.
- **Fix:** Use the absolute venv entrypoint for installation/containment while still resolving module origins.
- **Files modified:** `tools/release_evidence.py`, `tools/artifact_conformance.py`
- **Verification:** Pure and compiled fresh installs passed from neutral directories.
- **Committed in:** `2119a5d`

**3. [Rule 1 - Bug] Restored static type safety for dynamic scenario adapters**
- **Found during:** Task 3 final type check
- **Issue:** Dynamically resolved base classes prevented mypy from validating async and declarative scenario definitions.
- **Fix:** Import only installed public Fast FSM base classes for adapter definitions and preserve runtime module discovery elsewhere.
- **Files modified:** `tools/artifact_conformance.py`
- **Verification:** `uv run mypy tools/artifact_conformance.py tools/release_evidence.py` passed.
- **Committed in:** `813ff4a`

**4. [Rule 2 - Missing Critical] Added runtime architecture-to-wheel-tag validation**
- **Found during:** Task 3 final evidence audit
- **Issue:** A platform wheel could be classified as compiled without proving that its tag matched the architecture which executed it.
- **Fix:** Reject compiled records whose wheel tags do not match the installed runtime platform/machine before semantic acceptance.
- **Files modified:** `tools/release_evidence.py`, `tests/test_installed_artifacts.py`
- **Verification:** Full source/pure/compiled artifact suite passed, including a cross-platform rejection regression.
- **Committed in:** `28c3ba0`

**Total deviations:** 4 auto-fixed (2 Rule 1, 1 Rule 2, 1 Rule 3). All were correctness or proof-integrity fixes within the planned artifact-verification boundary.

## Issues Encountered

- The local beads query could not connect to its Dolt service, so no issue status mutation was attempted. This did not affect repository implementation or verification.
- `state.advance-plan` could not parse the pre-existing `STATE.md` plan-counter format; the standard progress, metric, decision, session, roadmap, and requirement updates all succeeded.

## Known Stubs

None.

## Self-Check: PASSED

- Confirmed all four owned implementation/test files and this summary exist.
- Confirmed all eight Task 1–3 RED/GREEN/fix commits exist in repository history.

## Next Phase Readiness

- Plans 20-02 onward can call `verify-installed-wheel` as the common exact-path proof seam and use the conformance digests for release-matrix aggregation.
- The local macOS arm64 proof covers one native compiled slice; the remaining supported native matrix is still a hosted-release workflow responsibility.

---
*Phase: 20-installed-artifact-parity-release-proof*
*Completed: 2026-09-05*
