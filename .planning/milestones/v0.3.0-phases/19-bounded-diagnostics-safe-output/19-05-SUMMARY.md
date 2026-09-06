---
phase: 19-bounded-diagnostics-safe-output
plan: "05"
subsystem: logging-safety
tags: [logging, trace-redaction, mypyc, slots, performance, restoration]
requires:
  - phase: 19-01
    provides: stable lifecycle stages and bounded diagnostic contracts
  - phase: 19-02
    provides: strict hostile logging and disabled-trace contract tests
provides:
  - metadata-only sync and async trace records with explicit bounded redaction
  - reversible library-owned logging configuration with generation-safe restore
  - disabled-trace structural, slots-policy, and fresh-compiled proof
affects: [phase19, phase20, core-api, release-verification]
actuals:
  tokens: 10084
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - trace-level guard before trace allocation, key traversal, handler lookup, or redactor invocation
    - explicit slotted marker on library-owned logging handlers
    - identity-plus-generation-plus-value restoration for application logger safety
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - src/fast_fsm/__init__.py
    - tests/test_logging_config.py
    - tests/test_performance_benchmarks.py
    - tests/test_mypyc_guard.py
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Default trace uses fixed record fields only; caller data exists solely in an ephemeral FSMTraceEvent sent to an explicit redactor."
  - "A frozen slotted _FSMStreamHandler marker is attached to a standard stream handler, avoiding inherited handler dictionaries while retaining explicit ownership."
  - "Restore is current-generation and compare-before-restore, so stale handles and later application changes cannot overwrite logger state."
patterns-established:
  - "Hot-path logging safety starts with isEnabledFor(DEBUG - 5), before inspecting values or calling user-controlled representations."
  - "Library logging may remove or close only handlers carrying its identity marker; application handler order and configuration are never inferred or mutated."
requirements-completed: [OUT-03, OUT-04, OUT-05]
coverage:
  - id: D1
    description: Metadata-only sync/async trace records, bounded custom redactor output, and fixed fail-closed redaction failures.
    requirement: OUT-03
    verification:
      - kind: unit
        ref: tests/test_logging_config.py and tests/test_mypyc_guard.py trace/redactor selections
        status: pass
    human_judgment: false
  - id: D2
    description: Disabled trace performs no raw-event, redactor, or hostile representation work while the compiled trigger floor remains selected.
    requirement: OUT-04
    verification:
      - kind: integration
        ref: tests/test_performance_benchmarks.py and fresh compiled selected pytest run
        status: pass
    human_judgment: false
  - id: D3
    description: Marked library handlers, propagation selection, generation-safe restore, and set_fsm_logging_level delegation preserve application ownership.
    requirement: OUT-05
    verification:
      - kind: unit
        ref: tests/test_logging_config.py handler/restore/propagation/delegate selection
        status: pass
    human_judgment: false
metrics:
  duration: 19 min
  completed: 2026-09-03
  tasks: 2
  files: 6
status: complete
---

# Phase 19 Plan 05: Safe Trace Logging and Reversible Configuration Summary

**Metadata-only sync/async tracing with explicit bounded redaction and a generation-safe logging handle that preserves application-owned handlers.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-09-03T23:49:36Z
- **Completed:** 2026-09-04T00:08:26Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added public `FSMTraceEvent`, `FSMTraceRedactor`, and `FSMLoggingHandle` contracts; default trace records carry only fixed metadata while custom redaction is allowlisted, bounded, and fail-closed.
- Added a marked library-handler seam that preserves application handlers, filters, formatters, order, levels, and propagation unless a caller explicitly asks the library to change a value.
- Proved the disabled path avoids event/redactor/representation work, passes slots and type gates, retains the selected throughput gate, and works in a fresh compiled extension checkout.

## Task Commits

1. **Task 1 RED: activate trace redaction contracts** — `2ea048d` (test)
2. **Task 1: emit metadata-only trace records with an explicit fail-closed redactor** — `fc6a6bb` (feat)
3. **Task 2 RED: activate logging ownership contracts** — `437388d` (test)
4. **Task 2: preserve application handlers with generation-safe reversible configuration** — `12bbcc6` (feat)
5. **Post-task disabled-trace regression fix** — `86173d2` (fix)

## Files Created/Modified

- `src/fast_fsm/core.py` — trace event/redaction seam, marked handler configuration, restore handle, and disabled-formatting guards.
- `src/fast_fsm/__init__.py` — public logging-safety exports.
- `tests/test_logging_config.py` — full-record leak, redactor, handler ownership, restore, propagation, and delegation evidence.
- `tests/test_performance_benchmarks.py` — hostile payload and condition structural proof for disabled trace.
- `tests/test_mypyc_guard.py` — frozen-slot and AST assertions for trace and logging ownership seams.
- `.specify/memory/spr-core-api.md` — current public trace, redactor, handler, propagation, and restoration contract.

## Decisions Made

- Store raw values only in the one ephemeral `FSMTraceEvent` supplied to an explicit redactor; never in a record or default format string.
- Use a slotted marker attached to a standard-library stream handler instead of subclassing it, so handler identity/generation remains explicit without violating the project slots audit.
- Treat application changes after configuration as authoritative by restoring only still-current library values.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test contract] Aligned staged redactor assertions with the plan's published surface**
- **Found during:** Task 1
- **Issue:** The strict-RED test expected a dictionary with legacy field names and a forbidden `category` output key, conflicting with the plan's exact `FSMTraceEvent` and `operation`/`stage`/`result`/`detail` allowlist.
- **Fix:** Updated the test to assert the frozen event fields and an allowlisted `trace_operation` result.
- **Files modified:** `tests/test_logging_config.py`
- **Verification:** Targeted redactor and hostile full-record tests passed.
- **Committed in:** `fc6a6bb`

**2. [Rule 2 - Missing critical functionality] Kept the owned handler marker slots-safe**
- **Found during:** Task 1 slots-policy verification
- **Issue:** Subclassing `logging.StreamHandler` retains the standard-library base instance dictionary and failed the mandatory slots audit.
- **Fix:** Replaced the subclass with a frozen slotted `_FSMStreamHandler` identity/generation marker attached to an ordinary stream handler.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `uv run python tools/release_evidence.py slots-policy --json` passed.
- **Committed in:** `fc6a6bb`

**3. [Rule 2 - Missing critical functionality] Prevented disabled trace from formatting a condition**
- **Found during:** Final disabled-path audit
- **Issue:** Legacy DEBUG formatting could call `str(condition)` before its disabled logger record was suppressed.
- **Fix:** Gated legacy condition formatting on enabled safe DEBUG output and added a hostile-condition regression test.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_performance_benchmarks.py`
- **Verification:** Targeted tests and the fresh compiled selection passed.
- **Committed in:** `86173d2`

**Total deviations:** 3 auto-fixed (1 Rule 1, 2 Rule 2).

## Issues Encountered

- The local sandbox initially blocked uv's shared cache and the linked-worktree Git index; approved commands completed all required checks and commits without touching unrelated worktree artifacts.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 19-08 can include this trace, handler, and compiled-performance evidence in the complete Phase 19 isolated suite after the remaining output plans land.

## Self-Check: PASSED

- All six declared implementation, test, and SPR files plus this summary exist.
- TDD RED/GREEN and disabled-trace correction commits (`2ea048d`, `fc6a6bb`, `437388d`, `12bbcc6`, `86173d2`) exist in history.

---
*Phase: 19-bounded-diagnostics-safe-output*
*Completed: 2026-09-03*
