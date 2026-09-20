---
phase: 26-canonical-construction-evidence-contract
reviewed: 2026-09-15T21:29:00Z
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
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 26: Code Review Report

**Reviewed:** 2026-09-15T21:29:00Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** clean

## Summary

The canonical construction transaction, builder/clone reconstruction, strict comparison records, exact adjacent locks, and ordinary-CI isolation are coherent and extensively tested. The three warning-level findings from the initial pass were fixed and passed focused regression, broader construction/evidence, type, source-origin, lock, and live-observation gates.

## Narrative Findings (AI reviewer)

## Resolved During Review Loop

### WR-01: `from_dict()` can blame the wrong transition for canonical validation failures

**File:** `src/fast_fsm/core.py:1536-1543`

**Issue:** All requests are normalized inside `_apply_transition_requests_owned()`, but the outer exception wrapper always labels a normalization failure with `parsed_rows[-1][0]`. If an earlier row references an unregistered source/target, duplicates a canonical source, or fails another machine-owned validation while a later row is valid, the public error reports the later row. This regresses the prior row-specific diagnostic and can send users to repair the wrong serialized transition.

**Resolution:** The canonical transaction now accepts validated per-request diagnostic contexts and wraps only normalization failures. A two-row regression proves the actual failing row is reported.

### WR-02: The Fast FSM observation lane is not lock-frozen

**File:** `benchmarks/comparison/run_comparison.py:72-80`

**Issue:** Both competitor lanes use `uv run --locked`, but the Fast FSM lane uses only `uv run --project`. If `pyproject.toml` and `uv.lock` drift, this ostensibly observational command may resolve/update the project lock or run against a newly resolved dependency graph. That weakens reproducibility and conflicts with the command's no-implicit-repository-write contract.

**Resolution:** The Fast FSM command now uses `uv run --locked --project`, and its command-shape contract requires the flag.

### WR-03: The claimed hard child boundary does not fail closed for launch errors or pipe-holding descendants

**File:** `benchmarks/comparison/run_comparison.py:100-185`

**Issue:** `subprocess.Popen()` errors escape as raw tracebacks instead of the runner's bounded/redacted `ComparisonContractError`. After the deadline, reader threads are not rejoined and the code calls `BufferedReader.close()` directly; if a descendant retains a copied pipe or tree termination fails, `close()` can contend with a reader blocked in `read()` and outlive the advertised hard timeout. The repository's release-evidence runner already avoids this lock interaction by closing descriptors directly, rejoining briefly, and converting launch failures to bounded domain errors.

**Resolution:** Launch errors are converted to a generic bounded domain error; blocked readers are woken by descriptor closure and briefly rejoined. Regressions cover a missing executable and a detached pipe-holding descendant.

## Re-review Result

No active Critical, Warning, or Info findings remain at standard depth.

---

_Reviewed: 2026-09-15T21:29:00Z_
_Reviewer: Codex inline fallback for gsd-code-reviewer (subagent dispatch restricted)_
_Depth: standard_
