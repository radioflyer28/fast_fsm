---
phase: 19-bounded-diagnostics-safe-output
reviewed: 2026-09-04T03:14:54Z
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
  critical: 5
  warning: 1
  info: 0
  total: 6
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-09-04T03:14:54Z
**Depth:** standard
**Files Reviewed:** 26
**Status:** issues_found

## Summary

The bounded-diagnostics, renderer, logging, tests, evidence tooling, and public
documentation changes were reviewed at standard depth. The submitted targeted
test suite passes, but direct boundary reproductions expose five ship-blocking
correctness/security defects: validation Markdown remains injectable, async
TRACE failures emit caller text, parent logger redactors are ignored, renderer
result limits do not bound rendered edges, and dense validation reports publish
stale counters. One public docstring also demonstrates output that the new
renderer no longer produces.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Validation Markdown export permits caller-controlled grammar and raw HTML injection

**File:** `src/fast_fsm/validation.py:1004-1057`

**Issue:** `_export_markdown()` directly interpolates the caller-controlled FSM
name, state names, event names, issue descriptions, locations, and
recommendations into headings, tables, code spans, and list items. Newlines
create arbitrary Markdown blocks, `|` breaks table structure, and raw HTML such
as `<script>` is emitted verbatim. This contradicts ADR-006's final-sink
Markdown encoding decision and makes a generated report unsafe to render in a
Markdown host that permits HTML. A two-state reproduction with a report name of
`"report\n<script>alert(1)</script>"` emits the script tag on its own physical
line, while a state name containing `"\n# injected-heading"` creates a new
heading and splits multiple table rows.

**Fix:** Apply a dedicated Markdown heading/cell/text encoder at every final
sink in `_export_markdown()` (including issue and recommendation text), ensuring
all control characters and grammar punctuation are encoded and every caller
value remains on one physical line. Share a small private encoding module if
both validation and visualization need the same policy, and add the hostile
corpus to `EnhancedFSMValidator.export_report("markdown")` tests.

### CR-02: Async TRACE failures leak caller-controlled machine names through legacy warnings

**File:** `src/fast_fsm/core.py:3797-3853`

**Issue:** The async guard and state-permission exception paths call
`self._logger.warning()` directly. At TRACE (`DEBUG - 5`), these legacy records
are enabled alongside the metadata-only trace record and interpolate
`self._name`. A reproduction using `name="machine-secret"` and a raising guard
captures `"machine-secret: FAILED guard type=ValueError"` before `fsm_trace`.
The synchronous equivalents correctly route through `_emit_legacy_warning()`,
so this is an async-only fail-closed redaction bypass. It violates the documented
promise that TRACE output is metadata-only and contains no caller-controlled
names.

**Fix:** Route every async lifecycle warning through the same TRACE-aware safe
warning seam used by synchronous dispatch (including guard, declarative guard,
state permission, and any observer warnings reachable during the operation), or
replace them with fixed scalar trace categories. Add an async raising-guard test
that scans every emitted `LogRecord`, not only the final trace record, for
machine/state/trigger sentinels.

### CR-03: A redactor configured on `fast_fsm` is ignored by normal child machine loggers

**File:** `src/fast_fsm/core.py:185-191`

**Issue:** `_library_trace_redactor()` searches only `logger.handlers`. Normal
machines use child loggers such as `fast_fsm.FSM`, while the documented default
configuration installs the marked handler and redactor on the parent
`fast_fsm` logger. The record propagates to that handler, but the child logger
does not discover its redactor. A direct reproduction with
`configure_fsm_logging(5, "fast_fsm", redactor=...)` and a default-named machine
emits `fsm_trace` while invoking the redactor zero times. Thus the primary
documented configuration silently discards explicit redaction behavior.

**Fix:** Resolve the effective marked handler along the logging parent chain,
respecting `propagate=False`, or attach immutable redactor configuration at a
logger-independent library registry keyed by the effective configured logger.
Test both exact-logger and parent-logger configurations, plus an intervening
non-propagating logger.

### CR-04: `max_results` does not bound Mermaid or PlantUML transition output

**File:** `src/fast_fsm/visualization.py:120-146`

**Issue:** The Mermaid renderer reserves results only for state IDs and then
emits every transition without a result reservation. The PlantUML renderer has
the same defect at lines 160-192. Consequently `DiagnosticLimits(max_results=2)`
successfully returns a two-state Mermaid diagram containing five transition
rows, rather than raising before the first over-budget result. The finite
`max_results` ceiling therefore does not bound these legacy string outputs as
ADR-006 and the visualization API documentation promise.

**Fix:** Define and consistently count each emitted diagram result (state row,
initial/final marker, transition row, and any title/delimiter policy) before
appending it. Thread the same ledger through fenced/document composition and add
exact/one-less tests for transition-heavy Mermaid and PlantUML output.

### CR-05: Dense validation status is captured before dense work and reports false counters

**File:** `src/fast_fsm/validation.py:338-365`

**Issue:** `validate_completeness()` stores `budget.status` in the report at line
360, then performs optional dense allocation and edge/result accounting at
lines 362-365. On a successful two-state dense report, the returned status says
`dense_cell_count == 0` while the validator's actual ledger says `2` (for the
`V x events` transition matrix). The structured result therefore publishes
non-truthful completion counters, directly violating the diagnostic status
contract.

**Fix:** Build optional dense output first and assign
`report["diagnostic_status"] = budget.status` only after all report work
succeeds. Add a regression assertion
that the returned status equals `validator.diagnostic_status` and includes the
expected dense cell and result counts.

## Warnings

### WR-01: Renderer docstrings show obsolete, non-reproducible diagram output

**File:** `src/fast_fsm/visualization.py:223-234`

**Issue:** The `to_mermaid()` example still claims the renderer emits direct
state-name identifiers (`idle --> running`), while Phase 19 now emits explicit
state declarations and opaque IDs (`state "idle" as s0`, `s0 --> s1`). The
PlantUML and fenced examples repeat the stale shape at lines 266-278 and
482-495. These docstrings are surfaced by autodoc and teach consumers to expect
output that cannot be produced by the reviewed implementation.

**Fix:** Update all three examples to the exact opaque-ID output and keep them
under executable doctest or snapshot coverage so future renderer changes cannot
silently stale the public docs.

---

_Reviewed: 2026-09-04T03:14:54Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
