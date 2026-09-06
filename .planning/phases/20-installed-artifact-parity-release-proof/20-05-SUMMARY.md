---
phase: 20-installed-artifact-parity-release-proof
plan: "05"
subsystem: release-evidence
tags: [complexity, diagnostics, installed-wheel, native-origin, benchmark, median, uv]
requires:
  - phase: 20-installed-artifact-parity-release-proof
    provides: exact installed-wheel provenance, categorical Phase 16-19 history, and matrix aggregation
provides:
  - topology-size-independent operation-count proof plus coarse scaling backstop for trigger, can_trigger, add_state, and add_transition
  - separate deterministic exact-limit diagnostic budget evidence for work, results, dense cells, and path expansions
  - native-origin-first installed compiled trigger benchmark records with warmup, three fixed samples, and a 200000 ops/sec median gate
  - release aggregation that validates categorical historical evidence before accepting release-authorizing installed performance
affects: [20-06, release-workflow, release-baseline]
actuals:
  tokens: 10334.5
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns:
    - test-local counting dictionaries establish direct registry work without adding runtime hooks
    - a stdlib-only installed child is rendered from the shared sampler to avoid checkout and development-dependency imports
    - release-authorizing aggregation distinguishes fresh installed native records from historical and pure observations
key-files:
  created:
    - .planning/phases/20-installed-artifact-parity-release-proof/20-05-SUMMARY.md
  modified:
    - tools/release_evidence.py
    - tests/test_performance_benchmarks.py
    - tests/test_diagnostic_contracts.py
    - tests/test_installed_artifacts.py
    - evidence/release-baseline.json
key-decisions:
  - "Use counted mapping operations as primary O(1) evidence and retain timing only as a loose regression backstop."
  - "Require a native extension origin and accepted archive/runtime identity before the installed compiled sampler can execute."
  - "Treat historical categorical provenance as a prerequisite while keeping it, pure observations, and diagnostics incapable of satisfying the installed compiled floor."
patterns-established:
  - "Installed benchmark proof: archive SHA and native origin acceptance → copied stdlib-only sampler → warmup → three equal samples → recomputed median gate."
  - "Diagnostic proof: reserve exact deterministic budgets at each boundary rather than mixing graph diagnostic work into runtime timing."
requirements-completed: [TEST-05, TEST-06, TEST-07]
coverage:
  - id: D1
    description: Four core runtime operations have direct-registry invariant tests over small, medium, and large unrelated topologies, with coarse scaling only as a regression backstop.
    requirement: TEST-07
    verification:
      - kind: unit
        ref: uv run pytest tests/test_performance_benchmarks.py tests/test_diagnostic_contracts.py -x -q
        status: pass
    human_judgment: false
  - id: D2
    description: Work, result, dense-cell, and path-expansion diagnostics retain exact-limit success and one-less reserve-before-work failure evidence outside runtime benchmarks.
    requirement: TEST-07
    verification:
      - kind: unit
        ref: tests/test_diagnostic_contracts.py#test_diagnostic_exact_limit_boundaries_are_separate_from_runtime_complexity
        status: pass
    human_judgment: false
  - id: D3
    description: An exact installed compiled wheel asserts native origin before recording warmup, at least three samples, and a passing 200000 ops/sec median.
    requirement: TEST-06
    verification:
      - kind: integration
        ref: uv run pytest tests/test_installed_artifacts.py tests/test_performance_benchmarks.py tests/test_release_evidence.py -x -q -k 'installed and (compiled or performance or benchmark or median or historical)'
        status: pass
    human_judgment: false
  - id: D4
    description: Categorical Phase 16-19 history is required before release-authorizing installed performance, while historical and pure records cannot populate the compiled key.
    requirement: TEST-05
    verification:
      - kind: unit
        ref: tests/test_installed_artifacts.py#test_installed_performance_evidence_validates_history_before_new_native_run
        status: pass
    human_judgment: false
duration: 21m
completed: 2026-09-05
status: complete
---

# Phase 20 Plan 05: Installed Artifact Parity & Release Proof Summary

**Four-operation O(1) evidence and a native-origin-first installed-wheel benchmark now gate a three-sample 200,000 ops/sec median without allowing historical or pure observations to substitute.**

## Performance

- **Duration:** 21m
- **Started:** 2026-09-05T02:36:33Z
- **Completed:** 2026-09-05T02:57:49Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added test-local mapping instrumentation for `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()` across three unrelated topology sizes, with a deliberately loose coarse-scaling ratio as a secondary check.
- Consolidated deterministic exact/one-less diagnostic budget evidence for work, results, dense cells, and path expansions without placing diagnostics on the hot path.
- Added a compiled installed-artifact collector that validates archive SHA, native extension origin, runtime architecture, and provenance before warmup and three fixed-iteration samples; it gates their recomputed median at 200,000 operations/sec.
- Separated categorical history, pure observations, installed compiled evidence, and deterministic diagnostic complexity in the manifest and release aggregation.

## Task Commits

1. **Task 1: Pin O(1) invariants for four core operations and separate diagnostic budgets** — `05af6ae` (test)
2. **Task 2: Gate installed native compiled throughput with stable samples** — `7dccaf8` (RED test), `133bd42` (GREEN implementation)

## Files Created/Modified

- `tests/test_performance_benchmarks.py` — direct-registry invariant/scaling coverage and child-sampler contract coverage.
- `tests/test_diagnostic_contracts.py` — consolidated exact deterministic diagnostic boundary test.
- `tools/release_evidence.py` — native-origin-first installed sampler, strict median record validation, historical prerequisite, and aggregate integration.
- `tests/test_installed_artifacts.py` — malformed/nonblocking performance rejection and real compiled-wheel median assertions.
- `evidence/release-baseline.json` — distinct historical, pure, installed compiled, and deterministic diagnostic evidence sections.

## Decisions Made

- Operation counts over concrete dict seams are the primary asymptotic evidence; measured timing is intentionally a coarse regression detector rather than an asymptotic proof.
- The installed benchmark child is generated from the shared sampler and uses only the standard library plus the installed package, preventing checkout or development-tool imports from contaminating the proof.
- A release-authorizing matrix accepts only structured fresh installed compiled records after its canonical Phase 16-19 history, never a retrospective, pure, source-tree, or status-only substitute.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored deterministic local aggregate performance ordering**
- **Found during:** Task 2
- **Issue:** Reversing local matrix inputs changed the emitted installed-performance order.
- **Fix:** Sort the non-authorizing local summary by matrix cell before serializing it.
- **Files modified:** `tools/release_evidence.py`
- **Verification:** `tests/test_release_evidence.py#test_aggregate_matrix_records_reconciles_exact_local_projection_deterministically` passed.
- **Committed in:** `133bd42`

**2. [Rule 3 - Blocking] Removed development-tool imports from the installed benchmark child**
- **Found during:** Task 2
- **Issue:** Copying the full evidence tool into a fresh artifact environment failed because its development-only `packaging` import is not a wheel runtime dependency.
- **Fix:** Render a stdlib-only child from the shared alternating-trigger sampler source and import only the installed `fast_fsm` package there.
- **Files modified:** `tools/release_evidence.py`
- **Verification:** Real compiled-wheel tracer passed with native origin and a three-sample median.
- **Committed in:** `133bd42`

**3. [Rule 1 - Bug] Made the performance test module independently import its tool seam**
- **Found during:** Task 2 verification
- **Issue:** Running the performance/diagnostic suite alone did not put the repository root on `sys.path`, so its tool-level sampler test could not import `tools`.
- **Fix:** Add the test-local repository-root path setup used by installed-artifact tests.
- **Files modified:** `tests/test_performance_benchmarks.py`
- **Verification:** Full performance and diagnostic suites passed standalone.
- **Committed in:** `133bd42`

**Total deviations:** 3 auto-fixed (2 Rule 1, 1 Rule 3). All preserve proof integrity and task scope.

## Issues Encountered

- The host provides `uv 0.12.9`; the reviewed baseline contract remains pinned to `uv 0.12.6`. The baseline write/check was intentionally not run and the manifest remains non-authorizing. No pin was relaxed or replacement binary installed.
- The local beads Dolt service was unreachable, so no issue-status mutation was attempted.

## Known Stubs

None. The empty installed compiled baseline section is an explicit non-authorizing `not-collected` evidence state, not a runtime or UI stub.

## Threat Flags

None - this plan adds no network endpoint, authentication path, file-access boundary, or schema migration beyond the planned local evidence files.

## Self-Check: PASSED

- Confirmed the summary and all five owned implementation/test/evidence files exist.
- Confirmed Task 1, Task 2 RED, and Task 2 GREEN commits (`05af6ae`, `7dccaf8`, `133bd42`) exist in repository history.

## Next Phase Readiness

- Plan 20-06 can consume a fail-closed release aggregate with native compiled median evidence and categorical historical prerequisites.
- A maintainer still needs the reviewed `uv 0.12.6` host binary before the separate baseline freshness workflow can be asserted locally; hosted release evidence remains outside this plan's authorization.

---
*Phase: 20-installed-artifact-parity-release-proof*
*Completed: 2026-09-05*
