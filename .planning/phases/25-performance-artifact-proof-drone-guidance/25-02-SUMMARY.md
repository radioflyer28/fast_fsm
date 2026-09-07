---
phase: 25-performance-artifact-proof-drone-guidance
plan: "02"
subsystem: testing
tags: [artifacts, conformance, performance, uv, mypyc]
requires:
  - phase: 25-01
    provides: shared conformance machinery and installed-artifact verifier foundations
provides:
  - Exact, fail-closed priority-selection conformance records for source and installed artifacts
  - A direct clean-source, pure-wheel, and compiled-wheel parity proof with retained native performance floor
  - A reviewed release baseline that records the durable clean-source conformance inventory
affects: [25-03, release-evidence, installed-artifact-proof]
actuals:
  tokens: 16773
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns:
    - Single shared semantic oracle with parent-side validation for neutral installed probes
    - Deterministically canonical child JSON is schema-checked before declaration-order validation
key-files:
  created: []
  modified:
    - tools/artifact_conformance.py
    - tools/release_evidence.py
    - tests/test_artifact_conformance.py
    - tests/test_installed_artifacts.py
    - tests/test_release_evidence.py
    - Taskfile.yml
    - evidence/release-baseline.json
key-decisions:
  - "Priority selection uses six independent exact-value scenarios without changing conformance schema version 1."
  - "Canonical installed-child JSON must pass exact-key validation before parent reconstruction of contract declaration order."
  - "The release baseline stores the clean-source contract under existing artifact evidence rather than weakening origin-bound wheel proof."
patterns-established:
  - "Artifact parity: capture source once after pure preflight, then compare each fresh neutral-install record to it."
  - "Performance isolation: keep compiled singleton throughput as a separate strict task from semantic parity."
requirements-completed: [PERF-02]
coverage:
  - id: D1
    description: Exact source and installed priority-selection oracle contract
    requirement: PERF-02
    verification:
      - kind: unit
        ref: tests/test_artifact_conformance.py
        status: pass
      - kind: integration
        ref: tests/test_installed_artifacts.py -m integration
        status: pass
    human_judgment: false
  - id: D2
    description: Fresh compiled-wheel identity and singleton throughput floor
    requirement: PERF-02
    verification:
      - kind: integration
        ref: task release-installed-artifacts-check
        status: pass
      - kind: integration
        ref: task release-installed-performance-check
        status: pass
    human_judgment: false
duration: 37m
completed: 2026-09-07
status: complete
---

# Phase 25 Plan 02: Three-Origin Priority Artifact Proof Summary

**One portable priority oracle now proves exact winner, guard, result/history, exhaustion, exception, and cancellation semantics across clean source plus fresh pure and compiled wheel installs.**

## Performance

- **Duration:** 37m
- **Started:** 2026-09-07T05:55:46Z
- **Completed:** 2026-09-07T06:32:52Z
- **Tasks:** 3/3
- **Files modified:** 7

## Accomplishments

- Added six bounded, deterministic priority-selection scenario records with independent expected values, digest coverage, and mutation/payload rejection tests.
- Bound one clean source record to fresh explicit pure and compiled wheel installs, retaining archive/origin/loader validation and a separate compiled performance gate.
- Regenerated and read-only verified durable evidence with reviewed `uv 0.12.6`; the compiled installed singleton median was 701,435.97 ops/sec from three samples, above the 200,000 floor.

## Task Commits

1. **Task 1: Carry one priority winner through the shared source/installed oracle** - `8979060` (test), `e7dc232` (feat)
2. **Task 2: Bind clean source, pure wheel, and compiled wheel workflow** - `6f31119` (test), `d32dfc4` (feat)
3. **Task 3: Run the final clean-origin artifact proof and regenerate reviewed evidence** - `b4160ac` (feat)

## Files Created/Modified

- `tools/artifact_conformance.py` - Defines and validates the six portable priority conformance scenarios.
- `tools/release_evidence.py` - Enforces parent-side canonical child validation and retains the source contract in release evidence.
- `tests/test_artifact_conformance.py` - Covers exact records, mutations, schema/digest integrity, and payload containment.
- `tests/test_installed_artifacts.py` - Proves three-origin record equality and strict native evidence rejection paths.
- `tests/test_release_evidence.py` - Regresses canonical JSON validation and baseline source-record binding.
- `Taskfile.yml` - Runs explicit pure/compiled builds against one captured clean-source record.
- `evidence/release-baseline.json` - Stores the regenerated source conformance suite and semantic digests.

## Decisions Made

- Kept `artifact_conformance.SCHEMA_VERSION = 1`; the new IDs intentionally alter suite/semantic digests without altering top-level shape.
- Treated child JSON as untrusted even after digest verification: exact field sets are required before reconstructing declaration order for shared validation.
- Kept the compiled singleton floor independent from the parity target, preserving its `ExtensionFileLoader`, three-sample, median >=200,000 ops/sec contract.

## Verification

- `uv run pytest tests/test_artifact_conformance.py -x -q` - pass (59 tests)
- `uv run pytest tests/test_release_evidence.py tests/test_artifact_conformance.py tests/test_installed_artifacts.py -m 'not integration' -x -q` - pass (295 tests)
- `uv run pytest tests/test_artifact_conformance.py tests/test_installed_artifacts.py -m integration -x -q` - pass (2 tests)
- `task release-installed-artifacts-check` - pass offline with clean source, fresh pure wheel, and fresh compiled wheel equality
- `task release-installed-performance-check` - pass offline; compiled `ExtensionFileLoader`, samples 709,844.43 / 701,435.97 / 701,053.85 ops/sec, median 701,435.97
- `task pure-source-check` - pass; `src/fast_fsm/core.py` origin
- `task release-baseline-check` with pinned `uv 0.12.6` and `UV_OFFLINE=1` - pass; 1792/1798 tests, 97.26% total and 96.15% core coverage
- `task typecheck-mypy` - pass; no issues in 7 source files
- `task typecheck-ty` - pass (advisory pre-release tool)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored contract declaration order after canonical child JSON encoding**
- **Found during:** Task 3 (final installed artifact proof)
- **Issue:** Deterministic child JSON sorts object keys, while the shared strict validator intentionally compares field declaration order; valid installed evidence was rejected despite an intact digest.
- **Fix:** Required each scenario's exact key set, then reconstructed only the trusted declared field order before invoking the shared validator.
- **Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`
- **Verification:** Canonicalized child-record regression, focused artifact suite, and direct installed proof all pass.
- **Committed in:** `b4160ac`

**2. [Rule 2 - Missing Critical Functionality] Retained source conformance in the generated baseline**
- **Found during:** Task 3 (reviewed baseline regeneration)
- **Issue:** The generated baseline lacked the required new suite inventory and digests, so a later freshness check could not prove what clean source had certified.
- **Fix:** Collected and parent-validated the clean-source record after pure preflight and stored it beneath existing `artifact_evidence`.
- **Files modified:** `tools/release_evidence.py`, `tests/test_release_evidence.py`, `evidence/release-baseline.json`
- **Verification:** The pinned offline write and read-only freshness check pass with all priority scenarios and both SHA-256 values present.
- **Committed in:** `b4160ac`

---

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2).
**Impact on plan:** Both changes preserve the planned strictness and durable proof; no public runtime API, dependency, remote operation, or Plan 25-03 work was added.

## Issues Encountered

- The phase-local uv cache did not contain the locked offline build inputs (`setuptools==80.9.0`, `wheel==0.45.1`, and `mypy[mypyc]==1.17.1`). The proof used the already-present default local cache with `UV_OFFLINE=1`; no package was downloaded or substituted.
- The first direct baseline comparison resolved ambient `uv 0.12.9` inside its subprocess and correctly failed the reviewed-toolchain guard. Re-running with the reviewed `uv 0.12.6` directory first on `PATH` passed the non-mutating freshness check.
- Generated baseline changes also reconciled current checked-out slot inventory, historical evidence paths, test/coverage counts, and local observations. They were produced only by the reviewed evidence writer and verified read-only afterward.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 25-03 may document the established proof commands and evidence interpretation. The D-02 implementation is complete with no native shadows in `src/fast_fsm`.

## Self-Check: PASSED

- All seven modified implementation/evidence files and this summary exist.
- All five task commits (`8979060`, `e7dc232`, `6f31119`, `d32dfc4`, `b4160ac`) exist in Git history.

---
*Phase: 25-performance-artifact-proof-drone-guidance*
*Completed: 2026-09-07*
