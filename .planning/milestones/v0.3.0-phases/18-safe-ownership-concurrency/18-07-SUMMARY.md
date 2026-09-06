---
phase: 18-safe-ownership-concurrency
plan: 07
subsystem: release-verification
tags: [ownership, concurrency, mypyc, github-actions, release-evidence, performance]
requires:
  - phase: 18-06
    provides: documented ownership contract, fresh-origin protocol, and exact-SHA hosted gate
provides:
  - asserted fresh pure/native Phase 18 release evidence
  - Python 3.10-3.14 native ownership CI matrix with exact-SHA closure
  - reviewed baseline and environment-labelled ownership performance evidence
affects: [phase19, phase20, release-verification]
actuals:
  tokens: 127441
  tasks: 3
  commits: 7
tech-stack:
  added: []
  patterns: [fresh-origin-verification, exact-sha-hosted-assertion, uninstrumented-throughput-gates]
key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - tools/phase18_native_probe.py
    - tools/phase16_isolated_verify.py
    - src/fast_fsm/core.py
    - tests/test_performance_benchmarks.py
    - evidence/release-baseline.json
    - .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md
key-decisions:
  - "Accept hosted ownership proof only when the workflow head SHA and every Python 3.10-3.14 native-probe job are successful."
  - "Keep durable trigger throughput floors in uninstrumented benchmark and native ownership jobs; coverage runs retain semantic hot-path checks."
  - "Use explicit generic ContextVar RHS annotations to satisfy ty without changing ownership runtime behavior or mypyc compilation."
patterns-established:
  - "Fresh pure/native suites are authoritative; checkout native shadows are never altered to make a direct test pass."
  - "Hosted CI helper must reject stale, incomplete, or non-success ownership matrices."
requirements-completed: [OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07]
coverage:
  - id: D1
    description: "Fresh pure and freshly compiled source exports satisfy the complete ownership, lifecycle, type, slots, documentation, performance, and baseline contract."
    requirement: OWN-01
    verification:
      - kind: integration
        ref: "uv run python tools/phase16_isolated_verify.py --suite phase18"
        status: pass
    human_judgment: false
  - id: D2
    description: "The Python 3.10-3.14 hosted matrix compiles actual core.py, asserts native origin, and runs ownership semantics for the exact implementation SHA."
    requirement: OWN-04
    verification:
      - kind: e2e
        ref: "uv run python tools/phase18_native_probe.py --assert-hosted-ci-sha ef1832371dc95820966ae23c684cedd806770a79"
        status: pass
    human_judgment: false
  - id: D3
    description: "The reviewed pure-source baseline is current and uninstrumented compiled throughput retains its fixed policy floor."
    requirement: OWN-07
    verification:
      - kind: integration
        ref: "task release-baseline-check via fresh phase18 suite; hosted Benchmark throughput gate"
        status: pass
    human_judgment: false
metrics:
  duration: 1h 25m
  completed: 2026-09-02
  tasks: 3
  files: 10
status: complete
---

# Phase 18 Plan 07: Release Evidence and Exact-SHA Native Closure Summary

**Closed the ownership phase with asserted fresh source evidence, reviewed release baseline and performance observations, and a successful exact-SHA Python 3.10-3.14 native ownership matrix.**

## Performance

- **Duration:** 1h 25m
- **Started:** 2026-09-02T03:40:25Z
- **Completed:** 2026-09-02T05:05:20Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Expanded CI to compile actual `core.py`, assert native module origin, and execute the ownership/lifecycle selection on every supported Python 3.10-3.14 interpreter.
- Made the `phase18` isolation suite cover the complete runtime, test, documentation, workflow, and evidence inventory in asserted pure and freshly compiled source modes.
- Regenerated and checked the pure release baseline: 1358/1358 tests passed with 97.87% total source coverage and 97.26% for `core.py`.
- Recorded final environment-labelled sync/async ownership observations and preserved the 200,000 operations/second compiled trigger floor in uninstrumented native benchmark work.
- Verified the hosted CI run for `ef1832371dc95820966ae23c684cedd806770a79`; all five ownership-native probe jobs and the entire workflow succeeded.

## Task Commits

Each repository change was committed with exact-path isolation:

1. **Task 1: Finalize supported-Python native ownership proof and the Phase 18 harness** — `26bb1a8` (feat)
2. **Task 2: Refresh performance, baseline, and complete local release evidence** — `d59bd2a` (fix)
3. **Release-gate repairs discovered during Task 3 hosted verification** — `2e53959`, `444a37d`, `b3cd5f6`, `6d1161b`, `ef18323` (fix)
4. **Task 3: Require the exact-SHA hosted Python 3.10-3.14 matrix** — hosted verification only; no repository artifact commit

## Verification

- `uv run python tools/phase16_isolated_verify.py --suite phase18`: passed from fresh pure and freshly compiled source trees.
- Fresh release baseline: 1358/1358 passed; total coverage 97.87%; `core.py` coverage 97.26%.
- Blocking mypy and advisory ty: passed; Ruff, slots, Sphinx HTML warnings-as-errors, and doctests: passed.
- `uv run python tools/phase18_native_probe.py --assert-hosted-ci-sha ef1832371dc95820966ae23c684cedd806770a79`: passed.
- GitHub Actions CI run `33593089071`: success, including every `Ownership native probe · Python 3.10` through `3.14` job.

## Decisions Made

- Treat coverage-instrumented throughput loops as semantic observations; maintain durable floors only in uninstrumented source/native benchmark jobs so release coverage measures behavior rather than tracer overhead.
- Preserve runtime behavior while adding explicit generic right-hand-side `ContextVar` annotations required by `ty` and supported by mypyc.
- Require exact workflow head-SHA equality and success for all five native ownership jobs before treating hosted evidence as phase closure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Harness correctness] Completed the Phase 18 artifact inventory and writer-baseline scope.**
- **Found during:** Task 2.
- **Issue:** The isolated release baseline did not initially account for every Phase 18 verification artifact.
- **Fix:** Made the authoritative inventory drive fresh overlay and baseline checks.
- **Files modified:** `tools/phase16_isolated_verify.py`, `evidence/release-baseline.json`.
- **Verification:** Fresh phase18 suite and read-only baseline check passed.
- **Committed in:** `d59bd2a`.

**2. [Rule 1 - Type compatibility] Annotated the ownership ContextVar generic RHS values.**
- **Found during:** Task 2.
- **Issue:** `ty` could not infer two ownership `ContextVar` generic values, despite correct runtime semantics.
- **Fix:** Added explicit type arguments without changing ContextVar values or ownership control flow.
- **Files modified:** `src/fast_fsm/core.py`.
- **Verification:** Blocking mypy, advisory ty, and fresh pure/native suites passed.
- **Committed in:** `d59bd2a`.

**3. [Rule 1 - Cross-version and platform stability] Normalized supported-version cancellation observation and descriptor-publication tests.**
- **Found during:** Task 3 hosted verification.
- **Issue:** Python 3.10 may materialize a cancellation at a task boundary, and Windows intentionally lacks descriptor-publication support.
- **Fix:** Asserted propagation/finalization rather than exception identity, and skipped only publication tests unavailable on descriptor-less platforms while retaining the intentional fail-closed case.
- **Files modified:** `tests/test_transition_lifecycle.py`, `tests/test_mypyc_guard.py`.
- **Verification:** Final full GitHub CI run passed on all Linux, macOS, and Windows jobs.
- **Committed in:** `2e53959`, `444a37d`.

**4. [Rule 2 - Diagnostic observability] Reported captured evidence-subprocess stdout with failures.**
- **Found during:** Task 3 hosted verification.
- **Issue:** The evidence gate hid its failing pytest assertion because only stderr was surfaced.
- **Fix:** Included captured stdout in the structured failure message.
- **Files modified:** `tools/release_evidence.py`.
- **Verification:** Hosted failure diagnosis became actionable; final evidence job passed.
- **Committed in:** `b3cd5f6`.

**5. [Rule 1 - Coverage-compatible performance verification] Kept performance floors out of coverage tracing.**
- **Found during:** Task 3 hosted verification.
- **Issue:** pytest-cov tracing reduced pure-path timing observations below uninstrumented policy floors, causing release evidence failures without a source/native performance regression.
- **Fix:** Made timing, raw, ownership, and lifecycle tests assert semantic completion under coverage while preserving their floors in uninstrumented and hosted native benchmark jobs.
- **Files modified:** `tests/test_performance_benchmarks.py`.
- **Verification:** Focused covered and uncovered selections, fresh phase18 suite, hosted benchmark gate, and final evidence job passed.
- **Committed in:** `6d1161b`, `ef18323`.

**Total deviations:** 5 auto-fixed (4 Rule 1, 1 Rule 2).
**Impact on plan:** All repairs were necessary to make the stated cross-version and release-evidence gates truthful; runtime ownership semantics and artifact scope remain unchanged.

## Issues Encountered

- Direct checkout tests can import a stale native shadow. The fresh-origin helper was therefore used for every release artifact verification; no checkout `.so` file was removed or replaced.
- Two hosted evidence runs revealed timing assertions that measured coverage instrumentation rather than the release benchmark. The final candidate keeps the performance policy in uninstrumented benchmark/native jobs and passes the coverage evidence job.

## Known Stubs

None.

## Self-Check: PASSED

The summary and all seven exact-path task commits are present, and `git diff --check` passes for this record.

## Next Phase Readiness

Phase 18 source-tree ownership evidence is closed. Phase 19 can depend on the complete safe ownership contract; Phase 20 remains responsible for installed wheel and sdist parity and was not claimed by this plan.

---
*Phase: 18-safe-ownership-concurrency*
*Completed: 2026-09-02*
