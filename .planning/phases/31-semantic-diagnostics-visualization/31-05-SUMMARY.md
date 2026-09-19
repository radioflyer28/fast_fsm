---
phase: 31-semantic-diagnostics-visualization
plan: 05
subsystem: conformance
tags: [diagnostics, final-state, transition-mode, rejection, native, performance]
requires:
  - phase: 31-semantic-diagnostics-visualization
    provides: runtime and cold diagnostic surfaces from plans 01 through 04
provides:
  - cross-surface semantic oracle for results, history, validation, JSON, diagrams, and TRACE
  - focused pure/native parity with exact module-origin assertions
  - restored pure source and passing sequential quality gate
affects: [phase-32]
actuals:
  tokens: 17000
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns: [assert one semantic graph across surfaces, skip disabled TRACE projection at the caller]
key-files:
  created: []
  modified: [tests/test_mypyc_guard.py, tests/test_final_states.py, tests/test_transition_modes.py, tests/test_expected_rejection.py, tests/test_logging_config.py, src/fast_fsm/core.py]
key-decisions:
  - "Both trigger entry points check TRACE enablement before preparing semantic trace arguments; the trace helper still guards itself."
  - "The installed compiled throughput floor remains unchanged; the disabled-path optimization repaired the full-suite failure."
patterns-established:
  - "Run identical focused semantics under asserted source and fresh native origins, then recoverably relocate only exact core extension shadows."
requirements-completed: [DIAG-01, DIAG-02, DIAG-03]
coverage:
  - id: D1
    description: Current-state finality and selected mode/rejection facts agree across runtime results, history, validation, JSON, diagrams, and TRACE.
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: tests/test_final_states.py
        status: pass
      - kind: integration
        ref: tests/test_transition_modes.py
        status: pass
      - kind: integration
        ref: tests/test_expected_rejection.py
        status: pass
    human_judgment: false
  - id: D2
    description: Explicit final and self-transition mode are consistent in both diagram projections.
    requirement: DIAG-02
    verification:
      - kind: integration
        ref: tests/test_mypyc_guard.py
        status: pass
    human_judgment: false
  - id: D3
    description: Diagnostic output remains bounded, escaped, metadata-only, and absent from the disabled TRACE hot path in pure and native execution.
    requirement: DIAG-03
    verification:
      - kind: integration
        ref: tests/test_mypyc_guard.py
        status: pass
      - kind: integration
        ref: tests/test_logging_config.py
        status: pass
    human_judgment: false
duration: 45min
completed: 2026-09-19
status: complete
---

# Phase 31 Plan 05: Cross-Surface Conformance Summary

**One semantic oracle now connects runtime outcomes to bounded diagnostic projections, and both pure and freshly compiled execution pass the focused matrix.**

## Accomplishments

- Extended final-state, transition-mode, expected-rejection, and structural tests to check current-state authority, result/history continuity, shared cold snapshot use, disabled TRACE, and unchanged singleton selection structure.
- Asserted pure `src/fast_fsm/core.py` origin, ran the nine-module focused matrix, built a fresh compiled extension, asserted `src/fast_fsm/core.cpython-312-darwin.so` origin, and ran the identical matrix. The native shadow was moved to a recoverable backup at `/var/folders/34/yzc9zf6903x_8krb7b8s6tlr0000gn/T//fast-fsm-phase31-native-backup.LgI3wP`; pure source origin was reasserted afterward.
- Kept the installed compiled throughput floor at 200,000 ops/sec and removed unnecessary disabled-TRACE argument projection at both trigger call sites after the full suite exposed a load-sensitive floor miss.

## Task Commits

- `c28d51f` — cross-surface structural and runtime tests.
- `4646136` — use actual typed machine/result values in the native TRACE early-return test.
- `764d29a` — skip TRACE projection at sync/async callers when disabled.

## Verification

- Ruff check/format on the Phase 31 Python set, blocking `task typecheck-mypy`, and slots policy — passed; focused Ruff and mypy passed again after the hot-path fix.
- `task docs-check` and `task docs-test` — passed (four doctests).
- `task typecheck-ty` — advisory failure on unresolved `._construction_compat` and `.conditions` imports in `core.py`; those source modules exist and mypy passed.
- Pure and fresh native focused suites (`test_diagnostic_contracts`, `test_validation`, `test_visualization`, `test_output_safety`, `test_logging_config`, `test_mypyc_guard`, `test_final_states`, `test_transition_modes`, `test_expected_rejection`) — passed; pure mode had six expected native-only skips.
- The first two full-suite attempts failed at the installed compiled throughput floor; the exact compiled installed-artifact test passed in isolation. After the caller-side disabled-TRACE optimization, `FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q --disable-warnings` passed in full, including the installed-wheel gate.
- Exact pure origin and `task pure-source-check` passed after native shadow relocation. No release evidence baseline was written.

## Deviations from Plan

The full regression gate found a load-sensitive installed-wheel performance regression. Plan 31-05 therefore included a narrow production hot-path fix and an additional TRACE test correction before closure. Native test failure was caused by passing non-native fake objects to a mypyc-typed helper, not by the library's TRACE behavior.

## Issues Encountered

The installed performance error reports only that the median is below the floor, not the measured value, so this run proves gate pass after the optimization but does not quantify the margin. The existing advisory ty import-resolution issue remains visible.

## User Setup Required

None.

## Next Phase Readiness

Phase 31 is ready for goal-backward verification. Phase 32 owns installed-wheel benchmarking and release-baseline work.

---
*Phase: 31-semantic-diagnostics-visualization*
*Completed: 2026-09-19*
