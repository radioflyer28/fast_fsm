---
phase: 25-performance-artifact-proof-drone-guidance
plan: "05"
subsystem: release-evidence
tags: [release-evidence, uv-lock, guarded-baseline, security]
requires:
  - phase: 25-04
    provides: Baseline/artifact evidence and the original release-proof audit
provides:
  - Guarded tracked-baseline refreshes with candidate validation before writing
  - Lockfile-governed release evidence that records, but does not gate on, the invoking uv version
affects: [release-evidence, release-readiness, security-audit]
actuals:
  tasks: 2
  commits: 3
key-files:
  created:
    - .planning/phases/25-performance-artifact-proof-drone-guidance/25-05-SUMMARY.md
  modified:
    - Taskfile.yml
    - tools/release_evidence.py
    - tests/test_release_evidence.py
    - evidence/release-baseline.json
    - .planning/phases/25-performance-artifact-proof-drone-guidance/25-SECURITY.md
key-decisions:
  - "Use uv.lock plus uv sync --locked as the dependency-resolution authority; do not require a particular uv executable version, offline mode, or custom cache path."
  - "Treat toolchain.uv as environment evidence that may refresh in the guarded baseline, not as a freshness or security-gate field."
  - "Retain the protected baseline writer and its constrained semantic/raw-diff validation."
requirements-completed: [PERF-02]
completed: 2026-09-07
status: complete
---

# Phase 25 Plan 05: Release Evidence Guard Summary

**Release evidence now uses ordinary locked `uv` workflows while still preventing a tracked baseline refresh from changing any durable release contract field.**

## Accomplishments

- Preserved the private guarded baseline writer, canonical protected-path routing, candidate validation, and byte preservation after rejected writes.
- Restored normal `uv sync --locked --all-groups` workflows: no mandatory `UV_OFFLINE`, custom `UV_CACHE_DIR`, or exact `uv` binary version is required.
- Made the `uv` version an environment observation; `uv.lock` is the dependency-resolution authority and a changed observed version is an allowed guarded-baseline refresh.
- Regenerated the baseline through the guarded writer with `uv 0.12.9`: 1,806 passed of 1,812 collected, six skipped, zero errors/failures, and only approved counts/observations/tool-version metadata changed.
- Re-ran the complete release-readiness proof successfully from the normal user environment.

## Task Commits

1. `8fae114` — restore normal `uv` release workflow.
2. `ebcb510` — let `uv.lock` govern release evidence rather than an exact executable pin.
3. `515b0a3` — refresh the guarded locked release baseline.

## Verification

- Ruff format/check and `tests/test_release_evidence.py` — pass (including guarded writer allowlist and rejection coverage).
- `task release-baseline-write` — pass with `uv 0.12.9`.
- `task release-baseline-check` — pass with the regenerated manifest unchanged.
- `task release-readiness-check` — pass: format, lint, mypy, 1,806 passed / 6 skipped tests, HTML docs, doctests, baseline freshness, release identity, installed pure/compiled artifact proof, installed performance, slots policy, and advisory `ty` all succeeded.

## Deviation from the Original Plan

The original plan proposed enforcing `UV_OFFLINE=1` and exact `uv 0.12.6`. The user explicitly rejected that as unnecessary complexity for a pre-production library. This implementation follows the approved policy instead: `uv.lock` plus `uv sync --locked` controls dependency resolution, while the local `uv` version is recorded without being a gate. The durable-baseline guard remains in force.

## Security Outcome

T-25-G01, T-25-G02, and T-25-SC are closed under the user-approved policy. The security record retains only non-blocking accepted availability and simulation risks; `threats_open` is now zero.

## Self-Check: PASSED

- The guarded baseline refresh and read-only checks passed under the normal locked `uv` environment.
- The full release-readiness command completed successfully.
- No runtime FSM API, dependency, lockfile, or release threshold changed in this closure.
