---
phase: 26-canonical-construction-evidence-contract
reviewed: 2026-09-15T21:25:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - .specify/memory/spr-core-api.md
  - Taskfile.yml
  - benchmarks/benchmark.py
  - benchmarks/comparison/common.py
  - benchmarks/comparison/fast_fsm_runner.py
  - benchmarks/comparison/python_statemachine_2_5.py
  - benchmarks/comparison/python_statemachine_2_5.py.lock
  - benchmarks/comparison/python_statemachine_3_2.py
  - benchmarks/comparison/python_statemachine_3_2.py.lock
  - benchmarks/comparison/run_comparison.py
  - pyproject.toml
  - src/fast_fsm/core.py
  - tests/test_async.py
  - tests/test_builder.py
  - tests/test_competitor_benchmark_contract.py
  - tests/test_graph_invariants.py
  - tests/test_mypyc_guard.py
  - tests/test_ownership_concurrency.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 26: Code Review Report

**Reviewed:** 2026-09-15T21:25:00Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

The canonical construction transaction, builder/clone reconstruction, strict comparison records, exact adjacent locks, and ordinary-CI isolation are coherent and extensively tested. Three robustness defects remain: one diagnostic regression in dictionary construction and two gaps in the manual runner's reproducibility/fail-closed process boundary.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `from_dict()` can blame the wrong transition for canonical validation failures

**File:** `src/fast_fsm/core.py:1536-1543`

**Issue:** All requests are normalized inside `_apply_transition_requests_owned()`, but the outer exception wrapper always labels a normalization failure with `parsed_rows[-1][0]`. If an earlier row references an unregistered source/target, duplicates a canonical source, or fails another machine-owned validation while a later row is valid, the public error reports the later row. This regresses the prior row-specific diagnostic and can send users to repair the wrong serialized transition.

**Fix:** Allow the canonical transaction to receive an optional tuple of per-request error prefixes (or return a typed request-index failure), wrap each normalization attempt with its matching prefix, and keep whole-plan conflict errors separate. Add a two-row regression where row 0 fails canonical endpoint validation and row 1 is valid.

### WR-02: The Fast FSM observation lane is not lock-frozen

**File:** `benchmarks/comparison/run_comparison.py:72-80`

**Issue:** Both competitor lanes use `uv run --locked`, but the Fast FSM lane uses only `uv run --project`. If `pyproject.toml` and `uv.lock` drift, this ostensibly observational command may resolve/update the project lock or run against a newly resolved dependency graph. That weakens reproducibility and conflicts with the command's no-implicit-repository-write contract.

**Fix:** Add `--locked` to the Fast FSM child command and strengthen the command-shape contract test so all three lanes fail rather than update a stale lock.

### WR-03: The claimed hard child boundary does not fail closed for launch errors or pipe-holding descendants

**File:** `benchmarks/comparison/run_comparison.py:100-185`

**Issue:** `subprocess.Popen()` errors escape as raw tracebacks instead of the runner's bounded/redacted `ComparisonContractError`. After the deadline, reader threads are not rejoined and the code calls `BufferedReader.close()` directly; if a descendant retains a copied pipe or tree termination fails, `close()` can contend with a reader blocked in `read()` and outlive the advertised hard timeout. The repository's release-evidence runner already avoids this lock interaction by closing descriptors directly, rejoining briefly, and converting launch failures to bounded domain errors.

**Fix:** Catch `OSError` around process creation and raise a generic comparison error without embedding the exception. Port the descriptor-close/rejoin sequence from `_run_installed_command()`, and add regression tests for a missing executable and a POSIX child that exits after spawning a pipe-holding descendant.

---

_Reviewed: 2026-09-15T21:25:00Z_
_Reviewer: Codex inline fallback for gsd-code-reviewer (subagent dispatch restricted)_
_Depth: standard_
