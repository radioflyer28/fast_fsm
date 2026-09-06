---
phase: 20
fixed_at: 2026-09-05T22:46:32Z
review_path: .planning/phases/20-installed-artifact-parity-release-proof/20-REVIEW.md
iteration: 3
findings_in_scope: 2
fixed: 1
skipped: 1
status: partial
---

# Phase 20: Code Review Fix Report

**Fixed at:** 2026-09-05T22:46:32Z  
**Source review:** `.planning/phases/20-installed-artifact-parity-release-proof/20-REVIEW.md`  
**Iteration:** 3

**Summary:**

- Findings in scope: 2
- Fixed: 1
- Skipped: 1
- No hosted workflow dispatch, remote operation, tag, release, publication, or baseline rewrite was performed.

## Fixed Issues

### CR-01: The shared conformance oracle did not prove all hardened contracts it represents

**Status:** fixed: requires human verification  
**Files modified:** `tools/artifact_conformance.py`, `tests/test_artifact_conformance.py`  
**Commit:** `a3f0467`  
**Applied fix:** Adds immutable, payload-safe installed-artifact observations for same-machine thread serialization, same-loop task serialization with a running heartbeat, foreign-loop rejection before guard evaluation, owned mutator rejection, and post-`BaseException` mutator admission. Replaces the single dense-only budget scenario with deterministic exact-limit/one-less records for work, results, dense cells, and path expansions. Mutation tests independently falsify every ownership observation and each dimension's exact/one-less outcome after recomputing the semantic digest, so the oracle cannot pass on a family label, record count, or stale hash alone.

## Skipped Issues

### CR-02: The tracked v0.3.0 release baseline is stale and cannot pass the pinned freshness gate

**File:** `evidence/release-baseline.json:6`  
**Reason:** The required exact `uv 0.12.6` executable is unavailable locally. Safe read-only discovery found one executable, `/Users/akriz/.local/share/cargo/bin/uv`, at `0.12.9`, and no cached or bundled `0.12.6` binary. The baseline was not fabricated, hand-edited, or regenerated, and the pin was not weakened. Commit `4c7f06f` adds a static current-schema/identity validator and regression fixtures that reject the tracked legacy top-level envelope, v0.2.2 identity, empty matrix, legacy historical key, and mapping-form installed-performance record. The read-only identity gate now explicitly reports the stale schema. Regeneration remains required in a genuine `uv 0.12.6` environment.

## Verification

All commands ran in `/private/tmp/fast-fsm-phase20-resume` after the corresponding fixes.

- `uv run ruff format tools/artifact_conformance.py tests/test_artifact_conformance.py tools/release_evidence.py tests/test_release_evidence.py` — passed.
- `uv run ruff check tools/artifact_conformance.py tests/test_artifact_conformance.py tools/release_evidence.py tests/test_release_evidence.py` — passed.
- `uv run pytest tests/test_artifact_conformance.py -q -x` — passed (31 tests).
- `uv run pytest tests/test_release_evidence.py -q -x` — passed (201 tests).
- `uv run pytest tests/test_artifact_conformance.py tests/test_release_evidence.py tests/test_installed_artifacts.py -q -x` — passed.
- `task typecheck-mypy` — passed.
- `task --silent release-evidence-local-check` — passed against freshly built local pure, compiled, and sdist-derived artifacts; its aggregate stayed `local-non-authorizing`.
- `task --silent release-identity-check` — correctly failed with `release baseline top-level schema is stale.`; the command did not alter tracked evidence.
- `uv --version` — `uv 0.12.9`; no exact `0.12.6` executable was found through safe local discovery.

---

_Fixed: 2026-09-05T22:46:32Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Iteration: 3_
