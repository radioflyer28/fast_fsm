---
phase: 20-installed-artifact-parity-release-proof
plan: "03"
subsystem: release-evidence
tags: [release-matrix, artifact-evidence, identity, sphinx, uv, mypyc]
requires:
  - phase: 20-installed-artifact-parity-release-proof
    provides: exact installed-wheel and sdist child evidence with conformance and lineage
provides:
  - one canonical hosted release matrix and a derived non-authorizing local projection
  - strict deterministic evidence aggregation with provenance, parity, lineage, and identity rejection
  - static and tag-time v0.3.0 identity validation without tag mutation
affects: [20-04, 20-05, 20-06, release-workflow]
actuals:
  tokens: 13728
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - immutable canonical matrix definitions projected into release and local profiles
    - strict record reconciliation before deterministic aggregate or release authorization
    - separated static pre-tag identity and non-mutating peeled-tag equality checks
key-files:
  created: []
  modified:
    - tools/release_evidence.py
    - tests/test_release_evidence.py
    - evidence/release-baseline.json
    - pyproject.toml
    - docs/conf.py
    - CHANGELOG.md
    - README.md
    - uv.lock
key-decisions:
  - "The local matrix is filtered from immutable release definitions and can never authorize publication."
  - "Static identity requires v0.3.0 sources and installed values without requiring a tag; tag equality is a separate read-only gate."
  - "Historical Phase 16–19 evidence is represented by an exact SHA-256 allowlist with explicit unavailable fields rather than inferred facts."
patterns-established:
  - "Aggregate only strict JSON records after exact cell, artifact, runtime, provenance, conformance, and sdist-lineage validation."
  - "Generate text summaries only from accepted aggregate JSON."
requirements-completed: [REL-01, TEST-04]
coverage:
  - id: D1
    description: Canonical release/local artifact matrix projection rejects substituted and incomplete evidence while preserving deterministic output.
    requirement: TEST-04
    verification:
      - kind: unit
        ref: tests/test_release_evidence.py#test_aggregate_matrix_records_reconciles_exact_local_projection_deterministically
        status: pass
      - kind: unit
        ref: tests/test_release_evidence.py#test_aggregate_matrix_records_rejects_substituted_or_mixed_evidence
        status: pass
    human_judgment: false
  - id: D2
    description: Static v0.3.0 identity and non-mutating tag-time commit equality are fail-closed.
    requirement: REL-01
    verification:
      - kind: unit
        ref: tests/test_release_evidence.py#test_static_release_identity_requires_every_v030_surface
        status: pass
      - kind: unit
        ref: tests/test_release_evidence.py#test_tag_identity_is_non_mutating_and_requires_the_peeled_verified_commit
        status: pass
      - kind: other
        ref: uv run sphinx-build -b html docs docs/_build/html -W --keep-going
        status: pass
    human_judgment: false
duration: 37m
completed: 2026-09-05
status: complete
---

# Phase 20 Plan 03: Installed Artifact Parity & Release Proof Summary

**Canonical release evidence now enforces an exact artifact matrix, while v0.3.0 identity is verified statically and at tag time without creating a tag.**

## Performance

- **Duration:** 37m
- **Started:** 2026-09-05T01:39:07Z
- **Completed:** 2026-09-05T02:16:04Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Defined one immutable release matrix covering universal pure wheels, direct native wheels, universal2 dual-runtime proof, an sdist archive, and explicit sdist-derived children; local proof is its non-authorizing projection.
- Added strict deterministic aggregation that rejects malformed, duplicate, missing, unexpected, detached, architecture-incompatible, mixed-version, mixed-provenance, mode, parity, and sdist-lineage evidence.
- Aligned package metadata, installed metadata checks, Sphinx, changelog, README claims, baseline identity, and lockfile to v0.3.0; tag equality remains read-only and requires a peeled commit match.

## Task Commits

1. **Task 1: Reconcile canonical release and local matrix profiles** — `3c2fcfb` (RED), `2ade1fe` (initial projection), `09f2f83` (aggregate GREEN)
2. **Task 2: Align v0.3.0 static identity and separate tag-time proof** — `0eaa40e` (RED), `9fd71de` (GREEN)

## Files Created/Modified

- `tools/release_evidence.py` — canonical matrix, strict aggregation, historical allowlist, static/tag identity validators, and CLI seams.
- `tests/test_release_evidence.py` — matrix substitution, strict JSON, deterministic aggregate, static identity, and tag-time equality coverage.
- `evidence/release-baseline.json` — v2 non-authorizing matrix schema, v0.3.0 identity, and exact Phase 16–19 evidence hashes.
- `pyproject.toml`, `docs/conf.py`, `CHANGELOG.md`, `README.md` — coordinated v0.3.0 package and public documentation identity.
- `uv.lock` — synchronized only the editable package version from 0.2.2 to 0.3.0.

## Decisions Made

- Only `release` can carry a release-authorization marker; `local` is visibly scoped as non-authorizing.
- Universal2 accepts two distinct native-runtime cells for the same artifact digest, while incompatible artifact reuse is rejected.
- Static checks accept an explicitly unreleased changelog and no tag; tag mode requires `v0.3.0`, a dated changelog, and an existing peeled tag commit equal to checkout and aggregate evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Parsed static baseline identity independently of child-evidence numeric bounds**
- **Found during:** Task 2 final static identity verification
- **Issue:** Valid floating-point baseline observations were rejected by a child-evidence parser intended for integer-only subprocess output.
- **Fix:** Kept duplicate-key/non-standard-number rejection while removing the unrelated child bounds from static identity parsing.
- **Files modified:** `tools/release_evidence.py`
- **Verification:** Actual repository static identity and focused identity tests passed.
- **Committed in:** `9fd71de`

**2. [Rule 1 - Bug] Normalized README whitespace before durable-claim validation**
- **Found during:** Task 2 final static identity verification
- **Issue:** A valid line wrap split the required publisher-authenticity disclaimer and caused a false failure.
- **Fix:** Normalize whitespace before checking durable documentation claims.
- **Files modified:** `tools/release_evidence.py`
- **Verification:** Actual repository static identity passed.
- **Committed in:** `9fd71de`

**3. [Rule 3 - Blocking] Removed task-generated native source shadows before pure-source preflight**
- **Found during:** Task 2 baseline regeneration
- **Issue:** Two ignored `core*.so` outputs generated during this run blocked the deliberately non-destructive pure-source preflight.
- **Fix:** Reviewed and removed only those two generated artifacts; no tracked source was removed.
- **Verification:** `verify-source --json` reported `src/fast_fsm/core.py` and v0.3.0.

**4. [Rule 3 - Blocking] Synchronized the lockfile for the package version change**
- **Found during:** Task 2 offline dependency sync
- **Issue:** The editable package entry in `uv.lock` still declared 0.2.2.
- **Fix:** Accepted the exact one-line lockfile version change to 0.3.0; dependency count and build pins are unchanged.
- **Files modified:** `uv.lock`
- **Verification:** Reviewed diff shows only the editable package version changed.
- **Committed in:** `9fd71de`

**Total deviations:** 4 auto-fixed (2 Rule 1, 2 Rule 3). All strengthen the fail-closed proof boundary without expanding release scope.

## Verification

- Passed: `uv run pytest tests/ -x -q` (sequential full suite).
- Passed: `uv run pytest tests/test_release_evidence.py tests/test_readme_examples.py -x -q`.
- Passed: Sphinx HTML warnings-as-errors and doctest builds.
- Passed: Ruff format/check, mypy for `tools/release_evidence.py`, static v0.3.0 identity, and runtime dependency/core.py mypyc-boundary assertions.
- Not run to completion: `task release-baseline-write` and the corresponding read-only baseline freshness check. The local host has only `uv 0.12.9`; the reviewed contract requires `uv 0.12.6`, and no replacement binary was installed or pin relaxed. The manifest remains explicitly `not-collected` and non-authorizing.

## Known Stubs

None.

## Next Phase Readiness

- Plans 20-04 through 20-06 can consume a deterministic aggregate and an adjacent release identity projection without treating local proof as publication authority.
- Before release-baseline freshness can be asserted locally, run the approved task with the exact reviewed `uv 0.12.6` binary; do not weaken the version gate.

## Self-Check: PASSED

- Confirmed the modified evidence, implementation, test, metadata, documentation, and lockfile paths exist.
- Confirmed all five RED/GREEN/task commits exist in Git history.

---
*Phase: 20-installed-artifact-parity-release-proof*
*Completed: 2026-09-05*
