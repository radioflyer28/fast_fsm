---
phase: 20-installed-artifact-parity-release-proof
plan: "06"
subsystem: release-evidence
tags: [github-actions, exact-sha, native-artifacts, release-gate, taskfile, uv]
requires:
  - phase: 20-05
    provides: installed compiled performance and diagnostic-budget evidence used by the release aggregate
provides:
  - Exact-SHA, evidence-only hosted native matrix workflow with a terminal aggregate
  - Tag-only v0.3.0 release path whose sole write-capable job depends on aggregate and peeled-tag identity
  - Non-authorizing local release-readiness projection plus read-only hosted evidence inspection procedure
affects: [v0.3.0-release, CI, release-maintenance, UAT]
actuals:
  tokens: 28936
  tasks: 3
  commits: 11
tech-stack:
  added: []
  patterns: [resolved-SHA workflow fan-out, aggregate-approved artifact hash attachment, profile-scoped release evidence, non-authorizing local projection]
key-files:
  created: [.github/workflows/release-evidence.yml]
  modified: [.github/workflows/release.yml, .github/workflows/ci.yml, tests/test_release_evidence.py, Taskfile.yml, docs/dev/releasing.md, docs/dev/testing.md]
key-decisions:
  - "Keep the reviewed uv 0.12.6 pin fail-closed; a host with uv 0.12.9 cannot pass readiness by substitution."
  - "Scope contents: write exclusively to the final tag-only release job after exact aggregate and peeled-tag checks."
  - "Treat local profile evidence as explicitly non-authorizing and require a later authorized, read-only hosted inspection before tagging."
patterns-established:
  - "Release evidence: resolve the input ref once and carry the emitted full SHA through every checkout, artifact, record, and aggregate."
  - "Artifact release: attach only bytes whose SHA-256 is uniquely listed in the successful aggregate manifest."
requirements-completed: [REL-01, REL-07, TEST-01, TEST-03, TEST-04, TEST-06]
coverage:
  - id: D1
    description: "Exact-SHA evidence-only workflow and structural no-publish contract"
    requirement: REL-07
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_release_evidence.py -x -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Tag-only aggregate, identity, and final release dependency graph"
    requirement: REL-01
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_release_evidence.py -x -q -k 'workflow and (aggregate or identity or release or permission or bypass)'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Local non-authorizing artifact/readiness projection"
    requirement: TEST-06
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_release_evidence.py -x -q -k 'phase20_taskfile or hosted_evidence_metadata or workflow and (aggregate or identity or release or permission or bypass)'"
        status: pass
      - kind: integration
        ref: "task release-readiness-check"
        status: unknown
    human_judgment: true
    rationale: "The reviewed uv 0.12.6 pin correctly rejects the host's uv 0.12.9, so the complete readiness command remains unverified on a pin-matching host."
  - id: D4
    description: "Authorized exact-SHA hosted native evidence inspection before tag creation"
    requirement: TEST-03
    verification:
      - kind: manual_procedural
        ref: "task release-hosted-prerelease-check FAST_FSM_HOSTED_RUN_ID=<authorized-run-id> FAST_FSM_EXPECTED_SHA=<40-char-sha>"
        status: unknown
    human_judgment: true
    rationale: "Hosted runner availability and terminal release-matrix evidence are external state; this plan intentionally did not dispatch a workflow or create a tag."
duration: 16h 44m
completed: 2026-09-05
status: complete
---

# Phase 20 Plan 06: Installed Artifact Parity Release Proof Summary

**Exact-SHA native release evidence, a v0.3.0 tag-only aggregate-and-identity release gate, and a non-authorizing local readiness projection.**

## Performance

- **Duration:** 16h 44m across the recovered execution
- **Started:** 2026-09-05T03:05:17Z
- **Completed:** 2026-09-05T19:48:49Z
- **Tasks:** 3
- **Files modified:** 7 implementation files

## Accomplishments

- Added a read-only manual/reusable `release-evidence.yml` workflow that resolves one full SHA, verifies the complete native release matrix, and emits a strict terminal aggregate plus machine-readable evidence.
- Replaced the prior release workflow with the sole tag-only `v0.3.0` route: successful reusable evidence, exact peeled-tag identity, then the only `contents: write` GitHub Release job.
- Added `uv`-backed local readiness and read-only hosted-evidence commands, semantic workflow/task contracts, and maintainer runbooks that distinguish local, hosted, and public-release proof.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build an exact-SHA evidence-only native workflow** - `1ffc74c` (test), `9c669be` (feat), `eec35ae` (fix)
2. **Task 2: Make exact aggregation and tag identity the only release path** - `a2693a9` (test), `da08b4d` (feat), `e0afcd6` (fix), `4011db5` (fix)
3. **Task 3: Publish local projection and read-only hosted evidence checks** - `77b5f24` (test), `bfe9ca0` (feat)

## Files Created/Modified

- `.github/workflows/release-evidence.yml` - immutable-SHA evidence-only native matrix and aggregate contract.
- `.github/workflows/release.yml` - tag-only aggregate/identity path with final scoped release permission.
- `.github/workflows/ci.yml` - ordinary static v0.3.0 identity gate.
- `tests/test_release_evidence.py` - semantic workflow, asset-hash, Taskfile, and hosted-metadata contract tests.
- `Taskfile.yml` - local profile projection, full readiness ordering, and read-only hosted inspection commands.
- `docs/dev/releasing.md` and `docs/dev/testing.md` - evidence boundaries, pre-tag hosted checkpoint, and validation runbooks.

## Decisions Made

- Preserved the exact reviewed `uv 0.12.6` requirement. The local host's `uv 0.12.9` is rejected rather than silently substituting a different tool version.
- The final release job validates every selected asset against one unique aggregate-manifest SHA-256 record before attaching it.
- Direct/manual reusable evidence is structurally non-publishing. A distinct tag-only caller must prove the `v0.3.0` peeled commit equals the successful aggregate checkout.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Repaired stale release-workflow test assumptions**
- **Found during:** Task 2 (Make exact aggregation and tag identity the only release path)
- **Issue:** Existing contract tests expected source-preflight builders in `release.yml`, although the task correctly moved those operations into the reusable evidence workflow.
- **Fix:** Targeted the source-preflight contract at `release-evidence.yml` and corrected the literal tag matcher.
- **Files modified:** `tests/test_release_evidence.py`
- **Verification:** Focused aggregate/identity/release contract tests passed.
- **Committed in:** `da08b4d`

**2. [Rule 1 - Bug] Kept static identity explicitly pre-tag**
- **Found during:** Task 2 (Make exact aggregation and tag identity the only release path)
- **Issue:** Static identity inherited the release caller's v0.3.0 tag value, which would make ordinary CI depend on a tag that does not yet exist.
- **Fix:** Kept synthetic static identity at `unreleased`; only reusable evidence records carry the caller tag.
- **Files modified:** `.github/workflows/release-evidence.yml`
- **Verification:** Release-evidence tests passed.
- **Committed in:** `e0afcd6`

**3. [Rule 2 - Missing critical functionality] Bound attached release assets to the accepted aggregate**
- **Found during:** Task 2 (Make exact aggregation and tag identity the only release path)
- **Issue:** Manifest success alone did not prove that the byte-identical assets attached to the release matched its records.
- **Fix:** Downloaded each expected artifact, required one unique manifest record, and compared SHA-256 before attachment.
- **Files modified:** `.github/workflows/release.yml`, `tests/test_release_evidence.py`
- **Verification:** Focused release contract tests passed.
- **Committed in:** `4011db5`

**4. [Rule 3 - Blocking] Restored local documentation test dependencies**
- **Found during:** Task 3 (Publish local projection and read-only hosted evidence checks)
- **Issue:** `task docs-check` could not run because the existing local virtual environment lacked the documentation dependency group.
- **Fix:** Ran `uv sync --locked --all-groups` against the existing lockfile; no dependency definition or pin changed.
- **Files modified:** None tracked
- **Verification:** `task docs-check` and `task docs-test` passed.

---

**Total deviations:** 4 auto-fixed (2 Rule 1, 1 Rule 2, 1 Rule 3)
**Impact on plan:** All fixes preserve the intended release topology and exact pins; no public or remote operation was performed.

## Verification

- `uv run pytest tests/test_release_evidence.py -x -q` — passed.
- `uv run pytest tests/test_release_evidence.py -x -q -k 'workflow and (aggregate or identity or release or permission or bypass)'` — 9 passed.
- `uv run pytest tests/test_release_evidence.py -x -q -k 'phase20_taskfile or hosted_evidence_metadata or workflow and (aggregate or identity or release or permission or bypass)'` — 11 passed.
- `uv run ruff format --check src/ tests/` — passed (32 files already formatted).
- `uv run ruff check src/ tests/` — passed.
- `task typecheck-mypy` — passed: `Success: no issues found in 7 source files.`
- `task typecheck-ty` (advisory) — exit 0, output: `WARN ty is pre-release software and not ready for production use. Expect to encounter bugs, missing features, and fatal errors.` followed by `All checks passed!`
- `task docs-check` and `task docs-test` — passed after the locked local environment sync; doctest reported `3 tests, 0 failures`.
- `task release-identity-check`, `task release-installed-artifacts-check`, `task release-sdist-check`, `task release-evidence-local-check`, `task release-installed-performance-check`, and `task release-slots-check` — passed.
- `task pure-source-check` — passed after local artifact checks; no generated source-tree extension remains.
- `uv run pytest tests/ -x -q` — passed.

## External Verification Gaps

- `task release-readiness-check` intentionally remains incomplete on this host: the exact gate rejects `uv 0.12.9` because the reviewed release evidence requires `uv 0.12.6`. The pin was not weakened or substituted. Run it on a host with exactly `uv 0.12.6` before treating the local readiness result as passed.
- `task release-hosted-prerelease-check` was not run. It requires an explicitly authorized, completed `release-evidence.yml` run and exact SHA, then performs only read-only inspection. Hosted runner availability and the full native matrix remain a pre-tag external UAT requirement.
- No hosted workflow was dispatched; no branch was pushed or fetched; no tag, release, or artifact publication was created.

## Known Stubs

None.

## User Setup Required

None - no service setup is required. The pre-tag hosted evidence inspection requires only an explicitly authorized evidence run ID and its expected full SHA.

## Next Phase Readiness

- The code and contracts are ready for a pin-matching local readiness run and the documented authorized hosted-native checkpoint.
- The two external gaps above must remain blocking before any v0.3.0 tag or release operation.

## Self-Check: PASSED

- Confirmed the summary exists and all nine task commits are reachable in the worktree history.

---
*Phase: 20-installed-artifact-parity-release-proof*
*Completed: 2026-09-05*
