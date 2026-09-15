---
phase: 26-canonical-construction-evidence-contract
plan: 05
subsystem: performance-evidence
tags: [uv, isolation, benchmarks, subprocess, supply-chain]
requires:
  - phase: 26-02
    provides: strict comparison schema and isolated exact-version child adapters
  - phase: 26-04
    provides: human approval of both package versions and upstream provenance
provides:
  - Exact adjacent uv locks for python-statemachine 2.5.0 and 3.2.1
  - One bounded manual observation command with canonical stdout output
  - Comparator-free ordinary dependencies, lock, CI, tests, and release paths
  - Runtime identity and semantic-preflight proof for all three comparison lanes
affects: [performance-evidence, release-gates, ci-dependencies]
actuals:
  tasks: 2
  commits: 5
tech-stack:
  added: []
  removed:
    - python-statemachine from ordinary benchmark dependencies
    - transitions from ordinary benchmark dependencies
  patterns:
    - exact PEP 723 dependencies with adjacent uv-generated locks
    - incremental per-stream subprocess limits and hard process-tree timeout
    - observational ratios that never determine CI or release success
key-files:
  created:
    - benchmarks/comparison/python_statemachine_2_5.py.lock
    - benchmarks/comparison/python_statemachine_3_2.py.lock
  modified:
    - pyproject.toml
    - uv.lock
    - Taskfile.yml
    - benchmarks/benchmark.py
    - benchmarks/comparison/run_comparison.py
    - benchmarks/comparison/python_statemachine_2_5.py
    - benchmarks/comparison/python_statemachine_3_2.py
    - tests/test_competitor_benchmark_contract.py
key-decisions:
  - "Competitor distributions exist only in their exact adjacent script locks and never in the project dependency graph."
  - "task benchmark-compare is the sole maintained manual entry point; it prints canonical JSON and writes only to an explicit --output path."
  - "Child stdout and stderr are capped while they are read, and a flooding or timed-out process tree is terminated without exposing raw diagnostics."
  - "The Phase 26 Beads item remains in_progress until phase-level verification succeeds."
requirements-completed: [PERF-05, PERF-06]
coverage:
  - id: D1
    description: Both approved comparator versions resolve exactly in isolated script environments with distinct runtime origins.
    requirement: PERF-05
    verification:
      - kind: integration
        ref: task benchmark-compare -- --warmup 10 --operations 100 --samples 1
        status: pass
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_adjacent_script_lock_resolves_exact_approved_version
        status: pass
    human_judgment: false
  - id: D2
    description: Required flat scenarios have identical preflight semantics in every lane before timing.
    requirement: PERF-05
    verification:
      - kind: integration
        ref: task benchmark-compare -- --warmup 10 --operations 100 --samples 1
        status: pass
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_parent_report_requires_shared_semantics_and_omits_unsupported_ratios
        status: pass
    human_judgment: false
  - id: D3
    description: Comparator installation and execution are absent from ordinary project, CI, quality, and release paths.
    requirement: PERF-06
    verification:
      - kind: contract
        ref: tests/test_competitor_benchmark_contract.py#test_ordinary_ci_and_release_paths_exclude_comparison_execution
        status: pass
      - kind: contract
        ref: tests/test_competitor_benchmark_contract.py#test_project_lock_excludes_comparator_packages
        status: pass
    human_judgment: false
phase_bead_id: fast_fsm-qj4
phase_bead_status: in_progress
completed: 2026-09-15
status: complete
---

# Phase 26 Plan 05: Exact Manual Comparison Evidence Summary

**Maintainers can now deliberately collect bounded, exact-version comparison observations while every ordinary CI and release path remains competitor-free.**

## Accomplishments

- Generated adjacent uv locks containing exactly `python-statemachine==2.5.0` and `python-statemachine==3.2.1` after the recorded human provenance approval.
- Removed both comparator distributions from project dependency groups and `uv.lock`.
- Replaced the legacy in-process benchmark with a thin compatibility delegate to the strict isolated parent.
- Added canonical observation metadata, shared-scenario comparisons, explicit unsupported cells, and stdout/output-path equivalence.
- Enforced bounded counts, a hard child timeout, incremental per-stream output caps, neutral child working directories, and redacted failures.
- Statically proved that normal CI, quality, release-evidence, and release-readiness graphs cannot execute comparison children or gate on ratios.

## Task Commits

1. **RED: Define competitor dependency isolation** — `e68856b` (test)
2. **GREEN: Isolate exact competitor locks** — `d815ff3` (build)
3. **RED: Define manual observation contract** — `41e6a68` (test)
4. **RED: Require incremental child output bounds** — `32b7fb3` (test)
5. **GREEN: Wire bounded manual comparison** — `319e569` (feat)

**Plan metadata:** this summary commit

## Live Observation

The required low-count command completed successfully:

`task benchmark-compare -- --warmup 10 --operations 100 --samples 1`

It proved:

- Requested and resolved comparator versions are exactly 2.5.0 and 3.2.1.
- Fast FSM and both comparator module origins are distinct.
- `flat-alternating-cycle` matches the required initial/first/second state values in every lane.
- `false-guard-no-transition` records one guard evaluation, unchanged `idle` state, and zero transition callbacks in every lane.
- `final-state-rejection` remains explicitly unsupported with empty measurements and ratios.
- The report is labelled `observation_only: true`; no ratio is a quality threshold.

## Verification

- Focused topology, builder, and benchmark-contract suites passed.
- Focused performance-path tests passed.
- Full sequential repository suite passed in the pure-source environment.
- Ruff, mypy, advisory ty, slots policy, pure-source origin, and `uv lock --check` passed.
- The two explicitly reported generated mypyc artifacts were removed because they shadowed `core.py` and correctly caused `task pure-source-check` to fail closed.

## Deviations from Plan

- The original parent used `subprocess.run(capture_output=True)`, which rejected oversized output only after buffering it. The implementation was strengthened with incremental pipe readers and a regression test that proves a flooding child is killed before the longer timeout.
- `python-statemachine` 3.2.1 rejects non-final trap states during class construction. Both comparator adapters now give the guarded target an unused outgoing reset transition, preserving the measured false-guard semantics while satisfying the upstream topology validator.

## Beads Status

- `fast_fsm-qj4` remains claimed by `radioflyer28` with status `in_progress` and priority 1.
- It is intentionally not closed during plan execution. The phase verifier owns closure after all phase gates and any gap cycle succeed.

## User Setup Required

None.

## Next Phase Readiness

Phase 26 plan execution is complete. The phase-wide code review and goal-backward verifier can now audit BUILD-04, BUILD-05, PERF-05, and PERF-06 before closing the single phase bead.

## Self-Check: PASSED

- Exact approved locks and runtime identities pass.
- Required semantic preflights pass in all three lanes.
- Manual observation output is bounded, canonical, and non-gating.
- Ordinary dependency and execution graphs are comparator-free.

---
*Phase: 26-canonical-construction-evidence-contract*
*Completed: 2026-09-15*
