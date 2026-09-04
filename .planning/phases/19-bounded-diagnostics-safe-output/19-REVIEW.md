---
phase: 19-bounded-diagnostics-safe-output
reviewed: 2026-09-04T15:41:09Z
depth: standard
files_reviewed: 26
files_reviewed_list:
  - .specify/decisions/ADR-006-bounded-diagnostics-safe-output.md
  - .specify/memory/spr-core-api.md
  - .specify/memory/spr-validation.md
  - .specify/memory/spr-visualization.md
  - README.md
  - docs/api/core.md
  - docs/api/validation.md
  - docs/api/visualization.md
  - docs/dev/architecture.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/__init__.py
  - src/fast_fsm/_diagnostics.py
  - src/fast_fsm/core.py
  - src/fast_fsm/validation.py
  - src/fast_fsm/visualization.py
  - tests/test_diagnostic_contracts.py
  - tests/test_logging_config.py
  - tests/test_mypyc_guard.py
  - tests/test_output_safety.py
  - tests/test_performance_benchmarks.py
  - tests/test_release_evidence.py
  - tests/test_validation.py
  - tests/test_visualization.py
  - tools/phase16_isolated_verify.py
  - tools/release_evidence.py
findings:
  critical: 4
  warning: 1
  info: 0
  total: 5
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-09-04T15:41:09Z
**Depth:** standard
**Files Reviewed:** 26
**Status:** issues_found

## Summary

The persisted 26-file scope was re-reviewed after the final two fix commits.
The earlier Markdown injection, renderer result accounting, dense-status,
parent-redactor, async-warning, stale renderer docstring, trigger-helper, and
explicit-child propagation findings are corrected. Focused Phase 19 tests,
Ruff lint, mypy, ty, Sphinx warnings-as-errors, doctests, and the recursive
slots audit pass. The implementation is still not shippable: ordinary Python
TRACE activation bypasses the new confidentiality guard, custom redactors
swallow process-control `BaseException` values, the full suite fails its scoped
logging-marker contract, and the committed release evidence predates the
current tests and source positions. The formatter gate also rejects the two
latest fix files.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: TRACE confidentiality depends on using the library configuration helper

**File:** `src/fast_fsm/core.py:275-303`

**Issue:** The legacy DEBUG/INFO/WARNING/ERROR helpers suppress caller-bearing
records only when `_has_reachable_trace_configuration()` finds a marked
library handler. TRACE itself is enabled through the ordinary
`logger.isEnabledFor(5)` check, so applications that configure Python logging
directly (for example `logger.setLevel(logging.DEBUG - 5)` plus an application
handler) receive both the metadata-only `fsm_trace` records and raw legacy
records. A guarded transition reproduced
`MACHINE-SECRET: Evaluating condition '<lambda>' for 'STATE-SECRET' -> 'dest'`
and `MACHINE-SECRET: FAILED guard type=ValueError`. This violates the published
level-based promise that TRACE output contains no machine/state/trigger names
or caller payload, and it leaves standard logging configuration as a security
bypass around the new helper-specific protection.

**Fix:** Treat either an effective TRACE level or a reachable library-owned
TRACE handler as TRACE-active. For example, suppress legacy records when
`logger.isEnabledFor(_FSM_TRACE_LEVEL) or
_has_reachable_trace_configuration(logger)`; retain the reachable-handler
branch for explicitly leveled children. Add exact and parent application-only
logger tests (no `configure_fsm_logging()` call) that scan every record surface
for machine, state, trigger, key, value, and exception sentinels.

### CR-02: A trace redactor can swallow `KeyboardInterrupt`, `SystemExit`, and cancellation

**File:** `src/fast_fsm/core.py:242-259`

**Issue:** `_emit_fsm_trace()` catches `BaseException` around the application
redactor and converts it to fixed `redaction_failure` metadata. That includes
process-control exceptions that must remain observable. A redactor raising
`KeyboardInterrupt("stop")` was swallowed and a successful transition returned
normally. In an async trigger the same pattern can consume cancellation raised
inside the synchronous redactor callback. The Phase 19 research explicitly
requires ordinary redactor exceptions to fail closed while `BaseException`
emits nothing and is re-raised, so the implementation breaks both interrupt
and cancellation semantics.

**Fix:** Catch `Exception` for fixed-category redactor failure and allow
`BaseException` subclasses to propagate without emitting a record. Add sync
`KeyboardInterrupt`/`SystemExit` and async cancellation regressions that also
verify no raw or partial trace record is delivered.

### CR-03: The full test suite fails after the handler marker schema changed

**File:** `tests/test_mypyc_guard.py:502-530`

**Issue:** Commit `668ed9d` added `configured_level` to
`_FSMStreamHandler`, but the scoped AST contract still requires exactly
`["generation", "redactor"]`. Both `uv run pytest tests/ -x -q` and the
release-baseline check stop at
`test_phase19_logging_marker_and_handle_stay_slotted_and_owned` with this
assertion failure. The focused logging suite misses the regression, so the
repository's mandatory full-suite and Phase 19 authoritative gates are red.

**Fix:** Update the structural expectation to include `configured_level` and
assert its intended role/type, then rerun the complete pure and compiled Phase
19 semantic gates rather than only `tests/test_logging_config.py`.

### CR-04: Release evidence is stale relative to the post-review fixes

**File:** `evidence/release-baseline.json:68-71`

**Issue:** The manifest still records 1,476 collected/passing tests, while the
current checkout collects 1,487. Its slots inventory also records pre-fix
source locations (for example `DiagnosticBudgetExceeded` at line 57 instead of
the current line 70, and the logging marker/handle before their current
locations). The baseline was refreshed before the subsequent review-fix
commits added tests and source lines. Even after CR-03 is repaired, the
read-only evidence comparison will reject these stable-field differences, so
the checked-in artifact does not describe the submitted implementation.

**Fix:** After all source/test fixes are complete and the full suite passes,
regenerate the pure release baseline through the repository's isolated
baseline-write workflow, review the manifest diff, and rerun
`task release-baseline-check`.

## Warnings

### WR-01: The latest TRACE fixes fail the repository formatting gate

**File:** `src/fast_fsm/core.py:275-279`

**Issue:** `uv run ruff format --check` reports that both
`src/fast_fsm/core.py` and `tests/test_logging_config.py` would be reformatted.
The diff includes the helper condition at lines 275-279, new diagnostic calls
around lines 2140-2150 and 4149-4600, and the new logging tests around lines
385-410. Phase 19's authoritative verifier runs this check before the full
suite, so the current fixes do not satisfy the project's quality gate.

**Fix:** Run Ruff formatting on the two files, inspect the formatting-only
diff, and rerun the format and lint checks.

---

_Reviewed: 2026-09-04T15:41:09Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
