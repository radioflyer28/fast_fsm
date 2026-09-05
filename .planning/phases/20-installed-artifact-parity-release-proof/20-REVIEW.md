---
phase: 20-installed-artifact-parity-release-proof
reviewed: 2026-09-05T22:30:33Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - tools/artifact_conformance.py
  - tools/release_evidence.py
  - tests/test_artifact_conformance.py
  - tests/test_installed_artifacts.py
  - setup.py
  - MANIFEST.in
  - tests/test_build_modes.py
  - tests/test_release_evidence.py
  - evidence/release-baseline.json
  - pyproject.toml
  - docs/conf.py
  - CHANGELOG.md
  - README.md
  - uv.lock
  - .github/copilot-instructions.md
  - .specify/memory/spr-core-api.md
  - tests/test_performance_benchmarks.py
  - tests/test_diagnostic_contracts.py
  - .github/workflows/release-evidence.yml
  - .github/workflows/release.yml
  - .github/workflows/ci.yml
  - Taskfile.yml
  - docs/dev/releasing.md
  - docs/dev/testing.md
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-09-05T22:30:33Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

The second fix iteration materially repaired the record producers, provenance envelope, native-suffix matching, subprocess tree deadline, and suite-byte identity. I exercised the real local record-producing path: `task --silent release-evidence-local-check` completed successfully and produced the non-authorizing aggregate, rather than merely passing YAML/fixture checks. The focused Phase 20 conformance/evidence suite also ran through its artifact scenarios.

However, Phase 20 still cannot claim the required complete hardened-behavior oracle: its fixed inventory omits multiple Phase 18 ownership contracts and most diagnostic budget dimensions, even though the aggregate treats that limited suite as the semantic proof for every artifact mode. Separately, the tracked baseline is objectively stale. Its correction requires the deliberate baseline-write operation under exact `uv 0.12.6`; the current host's `uv 0.12.9` is a legitimate environment constraint, but it does not explain away the contradictory checked-in v0.2.2 bytes and legacy schema.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: [BLOCKER] The shared conformance oracle still does not prove all hardened contracts it represents

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/artifact_conformance.py:41-165, 533-661, 863-875`

**Issue:** The Phase 20 plan requires a single installed-artifact oracle across the hardened Phase 16–19 contract families, not merely one smoke scenario per broad family. The actual fixed inventory contains only two ownership records: direct synchronous reentry plus an unrelated-machine call (lines 583–628), and cancellation/reuse (lines 533–580). It has no same-machine independent thread serialization, same-loop task serialization, cross-event-loop rejection, mutator ownership, or `BaseException` cleanup observation. Likewise, the only diagnostic proof is `max_dense_cells` at 4/3 (lines 631–661); it does not cover the remaining deterministic limits or their incomplete/error boundary. `_scenario_collectors()` at lines 863–875 proves these omissions are not only unasserted—they are never executed in source, pure, or compiled artifact evidence.

Consequently, a regression shared by pure and compiled wheels in any omitted contract still yields matching semantic digests and can authorize the release matrix. That contradicts the Phase 20 requirement that the shared oracle prove matching hardened behavior rather than only parity for a selected subset.

**Fix:** Expand the immutable scenario manifest and collectors with deterministic, payload-free records for every omitted ownership and diagnostic contract. In particular, use barriers/events to prove independent same-machine thread and task serialization, an explicit cross-loop failure, mutator admission/release after `BaseException`, and each diagnostic budget's exact-limit and one-less outcome. Add mutation tests that remove or falsify each contract-specific observation; checking a family label or record count is insufficient.

### CR-02: [BLOCKER] The tracked v0.3.0 release baseline is stale and cannot pass the pinned freshness gate

**File:** `/private/tmp/fast-fsm-phase20-resume/evidence/release-baseline.json:6-72`

**Issue:** The checked-in baseline identifies its only wheel and metadata as v0.2.2 (lines 12–25), has an empty `expected_matrix` (line 33), retains the obsolete `historical_phase_performance_observations` key (line 34), and uses the obsolete mapping form for `installed_compiled_performance` (lines 68–72). Those facts conflict with the current v0.3.0 generator schema and with the Phase 20 release contract. `.github/workflows/ci.yml` installs exact `uv 0.12.6` before running `release-baseline-check`; therefore a pin-matching runner will expose these stale bytes rather than repair them.

The local absence of exact `uv 0.12.6` is not itself a code defect and must not be worked around by weakening the pin. The blocker is the committed baseline artifact, which is already demonstrably inconsistent before any command is run.

**Fix:** In an environment running exactly `uv 0.12.6`, use the intentional baseline-write path, review the deterministic v0.3.0 diff, and commit the regenerated file. Add a static regression test for baseline artifact identity and the current Phase 20 top-level schema so an old wheel version or legacy key fails immediately without relying on a full evidence collection.

---

_Reviewed: 2026-09-05T22:30:33Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
