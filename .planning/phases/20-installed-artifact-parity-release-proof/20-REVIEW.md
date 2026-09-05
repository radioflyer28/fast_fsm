---
phase: 20-installed-artifact-parity-release-proof
reviewed: 2026-09-05T20:02:46Z
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
  critical: 12
  warning: 2
  info: 0
  total: 14
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-09-05T20:02:46Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Phase 20 is not release-ready. The checked-in hosted graph cannot complete: reusable-workflow outputs are not exported, downloaded evidence records overwrite one another, the release profile rejects its own status-only performance records, macOS verifier jobs use a Bash feature unavailable in the default macOS shell, and the final release job invokes an uninstalled tool. Even after those failures are repaired, the release attachment step can publish bytes not approved by the aggregate. The conformance and artifact evidence layers also contain proof-integrity gaps, and the tracked baseline still contradicts v0.3.0.

As direct confirmation of the performance-schema failure, invoking `aggregate_matrix_records()` with the repository's own complete release-profile fixture raises `EvidenceError: matrix evidence installed compiled performance has an invalid field set`; the tests only aggregate the local profile.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: [BLOCKER] Reusable workflow does not export any caller-visible outputs

**File:** `/private/tmp/fast-fsm-phase20-resume/.github/workflows/release-evidence.yml:15-25`

**Issue:** `workflow_call` declares inputs only. The outputs declared on `aggregate_release_evidence` at lines 611-618 are job-local and are not automatically exposed by a reusable workflow. Consequently every `${{ needs.release_evidence.outputs.* }}` reference in `release.yml` is empty, so `tag_identity` cannot check out the resolved SHA or download the manifest. The workflow contract tests inspect only the aggregate job's outputs (`tests/test_release_evidence.py:2959-2974`) and therefore miss the caller boundary.

**Fix:** Declare every required output under `on.workflow_call.outputs`, mapping each `value` to `jobs.aggregate_release_evidence.outputs.<name>`, and add a test that resolves the top-level callable-output mapping and checks every caller reference against it.

### CR-02: [BLOCKER] Evidence downloads overwrite nearly every matrix record

**File:** `/private/tmp/fast-fsm-phase20-resume/.github/workflows/release-evidence.yml:632-645`

**Issue:** Each pure/native verifier uploads a file named `evidence.json`, and every sdist verifier uploads `child.json` (plus one `archive.json`). The aggregate downloads all of those artifacts into one directory with `merge-multiple: true`. Same-named files from later artifacts overwrite earlier files, leaving only a handful of records for an 86-cell matrix. The subsequent recursive `find` therefore cannot assemble the exact matrix.

**Fix:** Preserve one subdirectory per artifact by removing `merge-multiple: true`, or name each record with its matrix cell and SHA before upload. Keep the recursive record discovery, reject duplicate normalized paths, and add an integration/fixture test that materializes all downloaded artifact layouts and proves the record count and cell set survive download without collisions.

### CR-03: [BLOCKER] Release aggregation rejects its own performance records and discards the actual proof

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/release_evidence.py:572-577`

**Issue:** Matrix validation permits only `{"status": "passed"}` for a performance cell. Later, release aggregation passes those same objects to `validate_installed_compiled_performance()`, which requires the full 19-field native performance record (`tools/release_evidence.py:674-682`). This makes every complete release profile fail. The workflows deliberately replace `raw["performance"]` with the status-only object at `.github/workflows/release-evidence.yml:431` and `:561`, while the tests build the same invalid fixture at `tests/test_release_evidence.py:3548` and never aggregate `profile="release"`. Even in local mode this throws away artifact SHA, native origin, commit, runtime, samples, and median, so a bare assertion can masquerade as installed proof.

**Fix:** Store the complete `raw["performance"]` record in each compiled matrix record. Validate it with `validate_installed_compiled_performance()`, then bind its artifact SHA, execution commit, asserted mode, platform, machine, Python version, core origin, and loader to the enclosing artifact/runtime/provenance fields. Add a complete release-profile aggregation test and mutations for every binding.

### CR-04: [BLOCKER] macOS verifier jobs call `mapfile`, which default macOS Bash lacks

**File:** `/private/tmp/fast-fsm-phase20-resume/.github/workflows/release-evidence.yml:391-398`

**Issue:** `verify_native` runs on `macos-15-intel` and `macos-14` but selects wheels with Bash `mapfile`. GitHub macOS jobs invoke the system Bash 3.2 by default, which has no `mapfile` builtin, so all macOS native and universal2 verification cells stop before the installed oracle. The tests merely search for the wheel-tag substring and never exercise the shell fragment on a Bash-3-compatible shell.

**Fix:** Replace `mapfile` with portable shell/Python selection (prefer a short `uv run python` script that enumerates, sorts, and requires exactly one matching wheel), or explicitly install and invoke a pinned Bash version. Add a portability test or execute the selector through POSIX shell semantics.

### CR-05: [BLOCKER] The write-capable release job invokes `uv` without installing it

**File:** `/private/tmp/fast-fsm-phase20-resume/.github/workflows/release.yml:70-92`

**Issue:** `github_release` checks out the repository and downloads artifacts, then immediately runs `uv run python`. Unlike `tag_identity`, it has no `astral-sh/setup-uv` step and no locked dependency setup. A clean `ubuntu-latest` runner is not contractually guaranteed to provide the reviewed uv binary, so the only publishing job fails before asset verification.

**Fix:** Add the same immutable `setup-uv` action with version `0.12.6`, then perform the minimum locked sync needed by the validation script; alternatively rewrite the asset verifier as a stdlib-only `python3` step and explicitly test that no project dependency is required. Extend workflow tests to require tool setup before the first use in every job.

### CR-06: [BLOCKER] Release attachment is not limited to aggregate-approved bytes

**File:** `/private/tmp/fast-fsm-phase20-resume/.github/workflows/release.yml:105-123`

**Issue:** The approval set excludes every cell whose name starts with `sdist-`, which also excludes `sdist-archive`; nevertheless `softprops/action-gh-release` uploads the unrestricted glob `release-artifacts/*`. The script checks that selected direct wheel files exist and match hashes, but it never rejects extra files and never validates the sdist that the glob publishes. A build artifact can therefore contain additional or substituted release assets that were never approved by the aggregate.

**Fix:** Derive the exact publishable filename/SHA allowlist (including the aggregate-approved sdist archive) from the manifest, reject any extra regular file/symlink/directory, copy only validated files into a fresh staging directory, and give only that staging directory to the release action. Add mutation tests for an extra file, an altered sdist, a symlink, and a derived child that must not be published.

### CR-07: [BLOCKER] Hosted prerelease recomputation omits all sdist evidence

**File:** `/private/tmp/fast-fsm-phase20-resume/Taskfile.yml:543-552`

**Issue:** The hosted inspection reconstructs arguments only from files named `evidence.json`. Sdist artifacts contain `child.json` and `archive.json`, so every sdist-derived cell and the sole archive record are omitted. Exact release aggregation must then fail with missing cells; the documented pre-tag checkpoint can never pass.

**Fix:** Discover all strict JSON record files beneath the downloaded evidence artifacts while explicitly excluding the manifest and run metadata, or standardize every uploaded record on a unique `evidence-<cell>.json` name. Add a fixture test that includes pure, native, sdist-child, and archive filenames and executes the actual argument-discovery path.

### CR-08: [BLOCKER] Suite identity does not bind scenario implementation bytes

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/artifact_conformance.py:41-155`

**Issue:** `_suite_sha256()` hashes only the hand-written IDs, families, and field names. Changing a scenario's setup, callbacks, assertions, synchronization, or even replacing it with constants leaves the suite digest unchanged as long as the output schema remains the same. An installed record can therefore claim the reviewed suite identity while executing materially different oracle code, contradicting the plan's requirement that the digest bind collector/scenario definition bytes.

**Fix:** Hash a canonical reviewed source payload for the collector and every scenario implementation (or a separately versioned immutable scenario-spec document plus executable source digest), include that digest in parent expectations, and add a test that modifies a scenario function body without changing its field schema and proves the suite digest changes.

### CR-09: [BLOCKER] The shared oracle does not cover the hardened contracts it claims

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/artifact_conformance.py:158-501`

**Issue:** Eight coarse scenarios are treated as complete Phase 16-19 conformance. The ownership scenario tests cancellation/reuse only, not reentry or independent serialization; graph coverage tests a false guard but not canonical endpoints, duplicate state identity, immutable snapshots, builder sealing, or recursive async detection; lifecycle covers one post-commit failure but not pre-commit failures, exact-once failure observation, or cancellation boundaries; sync/async checks only final success/state and omits callback order, history, guard context, failure stage, and commit equivalence. Output checks merely test a header/NUL and logging never exercises custom redactor behavior. The inventory test (`tests/test_artifact_conformance.py:85-93`) validates family labels, not required behaviors, so the complete installed oracle claim is false.

**Fix:** Add stable scenario IDs for each locked contract named in D-06, record the required scalar outcomes, and validate the exact scenario-ID set rather than one label per broad family. Add negative mutations that remove each contract-specific scenario and assertions that sync/async and builder/declarative pairs compare all promised fields.

### CR-10: [BLOCKER] Tracked v0.3.0 baseline still contains v0.2.2 artifacts and an obsolete schema shape

**File:** `/private/tmp/fast-fsm-phase20-resume/evidence/release-baseline.json:6-32`

**Issue:** The manifest's release identity is v0.3.0, but its only wheel is still `fast_fsm-0.2.2-py3-none-any.whl` with 0.2.2 metadata. It also records an empty expected matrix and old/non-generated Phase 20 section shapes (`historical_phase_performance_observations`, a dict-valued `installed_compiled_performance`) that differ from `_collect_manifest_after_preflight()` at `tools/release_evidence.py:5032-5072`. Thus `release-baseline-check` is guaranteed to report staleness on the pinned toolchain, and the checked-in evidence contradicts REL-01.

**Fix:** Run the intentional baseline-write path with the exact reviewed uv 0.12.6 environment, review the complete deterministic diff, and commit the regenerated v0.3.0 manifest. Add static identity assertions for the artifact-evidence versions and generated schema keys so changing only `release_identity` cannot conceal stale archive data.

### CR-11: [BLOCKER] “Bounded” subprocess capture is unbounded and has no timeout

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/release_evidence.py:2127-2148`

**Issue:** `subprocess.run(..., capture_output=True)` buffers unlimited stdout/stderr in memory and waits forever. The one-megabyte checks run only after the child exits, so a malformed installer/build/probe can exhaust memory, fill output indefinitely, or hang the evidence job. This is particularly exposed when the tool processes an artifact or sdist whose installed/built code is outside the verifier's trust boundary.

**Fix:** Add per-stage timeouts and stream stdout/stderr into bounded temporary/spooled files or use a capped reader that terminates the process as soon as either budget is exceeded. Convert timeout/output overflow to fixed redacted `EvidenceError` messages and add tests with a hanging child and an incrementally flooding child.

### CR-12: [BLOCKER] Wheel hash, inspection, and installation are vulnerable to artifact replacement

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/release_evidence.py:2744-2789`

**Issue:** The verifier hashes and inspects the caller-owned path, then later gives the same path to `uv pip install`. Nothing prevents another process from replacing or modifying the file between those operations. The recorded SHA can therefore describe different bytes from the installed artifact, breaking the exact-byte evidence boundary.

**Fix:** Copy the artifact into a private temporary directory through an opened file descriptor while hashing, verify the copied file's size/digest, then inspect and install only that immutable private copy. Recheck its digest immediately before installation and add an adversarial test that replaces the original path after initial resolution.

## Warnings

### WR-01: [WARNING] Native-core archive detection accepts unrelated module names

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/release_evidence.py:1319-1327`

**Issue:** `_native_core_members()` uses `name.startswith("fast_fsm/core")`, so `fast_fsm/core_backup.so` or `fast_fsm/core_evil.pyd` satisfies the archive-level native-core requirement even though it cannot load as `fast_fsm.core`. Installed verification later catches many cases, but `inspect_wheel()` and `verify-wheel` misclassify such an archive and the explicit compiled-output guard is weaker than documented.

**Fix:** Match an exact importable core basename: require the member's parent to be `fast_fsm` and its filename to be `core` followed immediately by one recognized extension suffix. Add negative archive fixtures for `core_backup.so`, nested paths, and similarly prefixed modules.

### WR-02: [WARNING] Wheel metadata parsing is not bounded against compressed expansion

**File:** `/private/tmp/fast-fsm-phase20-resume/tools/release_evidence.py:1506-1580`

**Issue:** `_archive_metadata()` calls `ZipFile.read()` on WHEEL and METADATA without checking `ZipInfo.file_size`, compression ratio, duplicate normalized members, or an aggregate uncompressed budget. The outer 128 MiB compressed-file cap does not prevent a small zip bomb from allocating a much larger metadata buffer. The direct `verify-wheel` command does not even apply that compressed-file cap.

**Fix:** Inspect `ZipInfo` entries first, enforce member-count/per-member/total-uncompressed limits and unique normalized paths, then read metadata through a capped stream. Apply the same archive-size/hash preflight to both `verify-wheel` and installed verification, with oversized/compression-bomb regression fixtures.

---

_Reviewed: 2026-09-05T20:02:46Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
