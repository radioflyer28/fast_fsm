---
phase: 23-construction-declarative-serialization-parity
plan: 02
subsystem: core declarative dispatch and builder preflight
tags: [python, mypyc, priority, declarative, async, builder]
requires:
  - phase: 23-01
    provides: immutable candidate topology with selected-entry priority identity
provides:
  - immutable plural declarative candidate metadata with exact selected-handler resolution
  - complete async declarative preflight across stacked and same-trigger declarations
affects: [23-03, 24-candidate-aware-diagnostics, 25-release-guidance]
actuals:
  tokens: 8124
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns:
    - frozen slotted metadata captured by transition decorators before state binding
    - exact source-trigger-target-priority handler matching after runtime selection
key-files:
  created:
    - .planning/phases/23-construction-declarative-serialization-parity/23-02-SUMMARY.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_builder.py
    - tests/test_transition_lifecycle.py
    - tests/test_async.py
key-decisions:
  - "Plural declarations require exact source, trigger, target, and priority identity; discovery order has no candidate-selection meaning."
  - "A single legacy declaration may serve an otherwise unambiguous manually nonzero-priority edge, while plural declarations never use that compatibility fallback."
patterns-established:
  - "Declarative tables publish immutable tuples only after full discovery and duplicate-identity validation."
  - "Builder detection and preflight flatten every declarative tuple before candidate-machine publication."
requirements-completed: [PAR-01, PAR-02]
coverage:
  - id: D1
    description: "Sync declarative metadata retains every candidate and invokes exactly the selected priority-qualified handler without changing callback payloads."
    requirement: PAR-01
    verification:
      - kind: integration
        ref: "tests/test_builder.py tests/test_transition_lifecycle.py tests/test_priority_selection.py -k declarative-and-priority-or-candidate-or-handler-or-lifecycle-or-ambiguous"
        status: pass
    human_judgment: false
  - id: D2
    description: "Async declarative resolution and builder preflight inspect plural declarations sequentially and leave rejected explicit-sync builders unpublished."
    requirement: PAR-02
    verification:
      - kind: integration
        ref: "tests/test_builder.py tests/test_async.py tests/test_transition_lifecycle.py tests/test_priority_selection.py -k declarative-or-preflight-or-priority-or-candidate-or-cancellation"
        status: pass
    human_judgment: false
duration: 50 min
completed: 2026-09-07
status: complete
---

# Phase 23 Plan 02: Declarative Candidate Identity Summary

**Declarative FSM states now retain immutable same-trigger candidates and run only the source/target/priority-selected handler in sync or async lifecycles.**

## Performance

- **Duration:** 50 min
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added frozen, slotted decorator and bound-handler records so multiple and stacked declarations survive discovery without trigger-key overwrites.
- Bound runtime declarative guards and handlers to the Phase 22-selected source, trigger, target, and priority; direct helpers fail closed when candidate metadata is ambiguous and retain one-declaration compatibility.
- Flattened every declaration during builder async detection and preflight, keeping failed explicit-sync construction unpublished and retryable.

## Task Commits

1. **Task 1: Preserve plural declarations and resolve the exact sync handler** — `def4b92` (RED contract tests), `a5ba82b` (implementation)
2. **Task 2: Mirror declarative identity through async dispatch and full builder preflight** — `def4b92` (contract tests), `a5ba82b` (implementation)

## Files Created/Modified

- `src/fast_fsm/core.py` — immutable declaration records, priority-aware resolver, sync/async lifecycle binding, direct ambiguity behavior, and full builder preflight traversal.
- `tests/test_builder.py` — decorator priority, plural/stacked discovery, same-target ambiguity, direct behavior, and retryable preflight coverage.
- `tests/test_transition_lifecycle.py` — selected declarative handler cardinality inside the normal lifecycle.
- `tests/test_async.py` — async selected-handler identity and direct ambiguity coverage.

## Decisions Made

- One declaration remains backward-compatible with manual nonzero registration when its source/target match is unambiguous; plural tables require exact priority matching.
- Candidate priority stays internal metadata: the caller's own `priority` keyword continues to reach its handler unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Type compatibility] Completed the frozen-handler annotation through the async lifecycle seam**
- **Found during:** Task 2 mypy gate
- **Issue:** Two async lifecycle annotations still described the former dictionary-shaped handler data.
- **Fix:** Replaced the stale annotations with the slotted `_DeclarativeHandler` type.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `task typecheck-mypy`, `task typecheck-ty`, and focused pure/native suites passed.
- **Committed in:** `a5ba82b`

**2. [Rule 1 - Advisory type compatibility] Made handler diagnostic names callable-safe**
- **Found during:** Task 2 ty gate
- **Issue:** The frozen handler method type does not guarantee a `__name__` attribute.
- **Fix:** Used the existing safe attribute lookup pattern with a redacted fallback name.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `task typecheck-ty` passed.
- **Committed in:** `a5ba82b`

**Total deviations:** 2 auto-fixed Rule 1 type-compatibility corrections. No public architecture or phase boundary changed.

## Issues Encountered

- The local beads Dolt service was unavailable during commits. Git commits succeeded; no beads, pull, rebase, sync, or remote operation was attempted.
- Native build shadows were moved recoverably to `/private/tmp/fast-fsm-phase23-native-shadows/wave2/` after the compiled focused suite, and pure-source preflight passed afterward.

## User Setup Required

None - no external service configuration required.

## Verification

- Focused pure sync/async declarative, priority, lifecycle, preflight, and cancellation suite: passed.
- Focused compiled suite and compiled smoke build: passed (only existing asyncio deprecation warnings).
- `task pure-source-check`, Ruff, `task typecheck-mypy`, `task typecheck-ty`, and slots-policy audit: passed.

## Next Phase Readiness

Wave 3 can apply the canonical registrar to quick/factory construction and complete broad phase proof without reimplementing declarative selection or async classification.

## Self-Check: PASSED

- `src/fast_fsm/core.py`, all three scoped test files, and commits `def4b92` and `a5ba82b` exist locally.

---
*Phase: 23-construction-declarative-serialization-parity*
*Completed: 2026-09-07*
