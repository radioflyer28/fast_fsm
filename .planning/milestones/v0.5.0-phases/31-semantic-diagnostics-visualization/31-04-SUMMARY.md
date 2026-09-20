---
phase: 31-semantic-diagnostics-visualization
plan: 04
subsystem: tracing
tags: [trace, rejection, final-state, transition-mode, confidentiality]
requires:
  - phase: 28-same-state-transition-modes
    provides: selected internal and priority result metadata
  - phase: 29-expected-domain-rejection
    provides: validated bounded rejection codes
provides:
  - matched sync and async semantic TRACE fields
  - fail-closed redactor fallback and disabled-path evidence
affects: [31-05, phase-32]
actuals:
  tokens: 3300
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [derive semantic trace fields after level gate from owned result and canonical current state]
key-files:
  created: []
  modified: [src/fast_fsm/core.py, tests/test_logging_config.py, docs/api/core.md, .specify/memory/spr-core-api.md]
key-decisions:
  - "The fixed TRACE record reports current-state finality, never inferred destination finality on a pre-commit rejection."
  - "Redaction failure nulls all semantic fields; disabled TRACE returns before reading result or current state."
patterns-established:
  - "One shared trace helper projects the already materialized result symmetrically for sync and async triggers."
requirements-completed: [DIAG-01, DIAG-03]
coverage:
  - id: D1
    description: Sync and async TRACE expose selected mode/priority, bounded rejection code, and authoritative current-state finality.
    requirement: DIAG-01
    verification:
      - kind: integration
        ref: tests/test_logging_config.py#test_trace_semantics_reflect_selected_mode_rejection_and_current_final
        status: pass
    human_judgment: false
  - id: D2
    description: Default and failed-redactor records remain metadata-only, and disabled TRACE performs no semantic projection.
    requirement: DIAG-03
    verification:
      - kind: unit
        ref: tests/test_logging_config.py#test_redactor_failure_is_fixed_category_or_suppression_without_raw_fallback
        status: pass
      - kind: unit
        ref: tests/test_logging_config.py#test_disabled_trace_does_not_inspect_result_or_current_final
        status: pass
    human_judgment: false
duration: 10min
completed: 2026-09-19
status: complete
---

# Phase 31 Plan 04: Safe Semantic TRACE Summary

**One fixed TRACE record now conveys validated rejection, selected mode, and current completion for both sync and async attempts without exposing application data.**

## Performance

- **Duration:** approximately 10 minutes
- **Completed:** 2026-09-19T18:28:46Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `trace_mode`, `trace_rejection_code`, and `trace_current_final` alongside existing `trace_priority`, projecting only after the TRACE enablement guard.
- Covered internal/external-self/ordinary selected attempts, all three approved rejection seams, false and unexpected guard failures, post-commit failure, and unselected attempts across sync and async paths.
- Proved fixed null-semantic redactor failure, metadata-only records, disabled-path noninspection, and updated public/maintainer docs.

## Task Commits

The two related tasks were committed together as `5289d4d` after both focused suites passed.

## Verification

- `uv run pytest tests/test_logging_config.py tests/test_expected_rejection.py -x -q --disable-warnings` — passed.
- Ruff check/format and `task typecheck-mypy` — passed.

## Decisions Made

TRACE finality is the canonical current state after the owned attempt, not a cached result flag or pre-commit destination prediction. Rejection code is revalidated defensively before LogRecord publication.

## Deviations from Plan

The two tasks landed in one cohesive commit rather than separate task commits. No scope expansion.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

All three Phase 31 diagnostic surfaces are implemented; Plan 31-05 owns cross-surface, pure/native, docs, typing, and full-suite closure.

---
*Phase: 31-semantic-diagnostics-visualization*
*Completed: 2026-09-19*
