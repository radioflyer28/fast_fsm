---
phase: 26-canonical-construction-evidence-contract
plan: 02
subsystem: benchmarking
tags: [comparison, provenance, preflight, subprocess, python-statemachine]
requires:
  - phase: 26-01
    provides: canonical Fast FSM construction seam and current source baseline
provides:
  - Strict bounded semantic-first comparison record and sampler contract
  - Fast FSM observation child with required untimed preflight
  - Exact pinned 2.5.0 and 3.2.1 competitor script definitions
  - Non-importing parent command, validation, contradiction, and ratio protocol
affects: [26-04, 26-05, performance-evidence, taskfile, ci-isolation]
actuals:
  tokens: 12400
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - semantic preflight before any warmup or timing
    - exact isolated PEP 723 competitor children with parent-side acceptance
key-files:
  created:
    - benchmarks/comparison/common.py
    - benchmarks/comparison/fast_fsm_runner.py
    - benchmarks/comparison/python_statemachine_2_5.py
    - benchmarks/comparison/python_statemachine_3_2.py
    - benchmarks/comparison/run_comparison.py
    - tests/test_competitor_benchmark_contract.py
  modified: []
key-decisions:
  - "Required flat-cycle and false-guard scenarios are contradictions when semantics differ; only the optional final-state cell may be unsupported."
  - "The parent imports no FSM implementation and computes descriptive ratios only after exact record, identity, origin, and preflight validation."
patterns-established:
  - "Comparison evidence: validate identity and untimed required facts before accepting finite samples or calculating ratios."
  - "Ordinary tests inspect competitor scripts and fake subprocesses; the sole live smoke launches only Fast FSM from a neutral directory."
requirements-completed: [PERF-05, PERF-06]
coverage:
  - id: D1
    description: Exact Fast FSM and competitor lanes share a strict semantic-first record with contradiction-safe ratio construction.
    requirement: PERF-05
    verification:
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_schema_rejects_malformed_or_contradictory_records
        status: pass
      - kind: integration
        ref: tests/test_competitor_benchmark_contract.py#test_neutral_cwd_fast_child_smoke_resolves_repository_origin
        status: pass
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_parent_builds_ratios_only_after_identity_and_required_semantics
        status: pass
    human_judgment: false
  - id: D2
    description: Ordinary contract tests validate exact child commands, pins, output bounds, and unsupported cells without importing or running a competitor.
    requirement: PERF-06
    verification:
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_exact_version_children_have_distinct_locked_script_commands
        status: pass
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_exact_version_child_metadata_is_self_contained
        status: pass
      - kind: unit
        ref: tests/test_competitor_benchmark_contract.py#test_run_child_bounds_and_validates_subprocess_output
        status: pass
    human_judgment: false
duration: 17min
completed: 2026-09-15
status: complete
---

# Phase 26 Plan 02: Isolated Comparison Contract Summary

**Exact isolated comparison lanes now require validated identity and matching untimed semantics before producing any descriptive timing ratio.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-15T17:59:00Z
- **Completed:** 2026-09-15T18:16:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added a strict stdlib-only record validator, canonical JSON serializer, bounded sampler, and explicit supported/unsupported scenario model.
- Added a Fast FSM child plus exact PEP 723 definitions for `python-statemachine` 2.5.0 and 3.2.1; both required scenarios must preflight before sampling.
- Added a neutral-directory parent that constructs isolated commands, bounds child results, rejects identity/origin/semantic contradictions, and emits no ratio for unsupported optional cells.

## Task Commits

1. **RED: Define strict comparison record behavior** — `9bef616` (test)
2. **GREEN: Implement common schema and Fast FSM child** — `221c712` (feat)
3. **RED: Define exact child and parent behavior** — `0c1344f` (test)
4. **GREEN: Implement exact child definitions and parent protocol** — `eb5d28a` (feat)
5. **Contract hardening: Cover excessive child output** — `3d5a374` (test)

**Plan metadata:** this summary commit

## Files Created/Modified

- `benchmarks/comparison/common.py` — Exact schema, preflight constants, bounds, canonical JSON, and sampler.
- `benchmarks/comparison/fast_fsm_runner.py` — Fast FSM semantic and observation child.
- `benchmarks/comparison/python_statemachine_2_5.py` — Exact 2.5.0 isolated child definition.
- `benchmarks/comparison/python_statemachine_3_2.py` — Exact 3.2.1 isolated child definition.
- `benchmarks/comparison/run_comparison.py` — Neutral subprocess orchestration and report acceptance.
- `tests/test_competitor_benchmark_contract.py` — Offline fixture, contradiction, command, bounds, and Fast-only smoke coverage.

## Decisions Made

- `final-state-rejection` is the explicit optional capability cell. It is visible as unsupported with no measurement fields or ratios until final-state semantics exist.
- Required preflight dictionaries are exact shared values, preventing similarly named but behaviorally different operations from entering comparison results.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- The first command-construction assertion derived `2.5` from the filename token instead of the exact `2.5.0` implementation ID. The fixture mapping was corrected before the GREEN commit; production behavior was unaffected.

## User Setup Required

None — the competitor scripts are definitions only. Their locks and execution remain blocked on the plan 26-04 provenance checkpoint.

## Next Phase Readiness

- Plan 26-05 can generate adjacent locks and expose the manual comparison command after human provenance approval.
- Plan 26-03 can independently propagate the canonical construction transaction through retained adapters.

## Self-Check: PASSED

- All 19 comparison contract tests pass.
- Ruff formatting/checking and Python compilation pass for all comparison files.
- Tests never import or execute `statemachine`; the only real subprocess smoke launches the Fast FSM child from a neutral directory.

---
*Phase: 26-canonical-construction-evidence-contract*
*Completed: 2026-09-15*
