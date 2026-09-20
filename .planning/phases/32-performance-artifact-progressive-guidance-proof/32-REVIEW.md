---
phase: 32-performance-artifact-progressive-guidance-proof
reviewed: 2026-09-20T02:19:02Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - README.md
  - Taskfile.yml
  - benchmarks/performance_demo.py
  - docs/QUICK_START.md
  - docs/TUTORIAL.md
  - docs/api/core.md
  - docs/examples/index.md
  - evidence/release-baseline.json
  - examples/drone_failsafes.py
  - tests/test_artifact_conformance.py
  - tests/test_drone_failsafes_example.py
  - tests/test_installed_artifacts.py
  - tests/test_performance_benchmarks.py
  - tests/test_readme_examples.py
  - tests/test_release_evidence.py
  - tools/artifact_conformance.py
  - tools/release_evidence.py
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 32: Code Review Report

**Reviewed:** 2026-09-20T02:19:02Z  
**Depth:** standard  
**Files Reviewed:** 17  
**Status:** issues_found

## Summary

The new fixed artifact oracle and descriptive benchmark path have two actionable defects. The oracle accepts a rehashed malformed semantic fact despite its fail-closed contract. The benchmark CLI's required environment label is omitted from priority-group rows, making half of its emitted observations less identifiable than advertised.

## Narrative Findings (AI reviewer)

### Critical Issues

#### CR-01 — Rehashed boolean-as-integer fact passes the strict artifact oracle

**Classification:** BLOCKER  
**File:** `/Users/akriz/code/fast_fsm/tools/artifact_conformance.py:2230`  
**Issue:** New Phase 32 `required_values` include booleans such as `final_terminated`, `result_internal`, `history_internal`, and `rejected`, but the validation compares them with `!=`. In Python, `1 == True` and `0 == False`; these fields are not covered by the earlier explicit boolean checks. A child can replace `final_terminated: true` with `final_terminated: 1`, recompute `semantic_sha256`, and pass `validate_conformance()`. I reproduced this with `uv run python`: it printed `accepted integer 1 for final_terminated`. Numeric count fields can similarly accept equal floats. Thus the promised exact typed scalar contract is not fail-closed, and artifact agreement can accept malformed evidence.

**Fix:** Compare exact types as well as values for every required scalar (for example `type(observed) is type(required_value) and observed == required_value`), then add mutation tests that substitute `1`/`0` for required booleans and `1.0` for required integer counts with recomputed digests.

### Warnings

#### WR-01 — Priority observations omit the required environment label

**Classification:** WARNING  
**File:** `/Users/akriz/code/fast_fsm/benchmarks/performance_demo.py:381`  
**Issue:** The CLI now requires `--environment-label` and says all rows are environment-labelled, but passes that value only to `collect_semantic_observations()`. The `PRIORITY_GROUP_OBSERVATION` records returned by `collect_priority_group_observations()` contain runtime/platform fields but no `environment_label`. Runs from `task benchmark` and `task benchmark-compiled` therefore cannot associate those priority rows with their explicit run label, even though their semantic rows have it. This also makes the advertised CLI argument only partially effective.

**Fix:** Accept and validate `environment_label` in the priority collector, put it in each priority row, pass the CLI argument at this call site, and assert both emitted row families carry the same label.

---

_Reviewed: 2026-09-20T02:19:02Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
