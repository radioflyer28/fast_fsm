---
phase: 15-release-baseline-evidence-harness
verified: 2026-08-30T02:18:54Z
status: passed
score: 16/16 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
---

# Phase 15: Release Baseline & Evidence Harness Verification Report

**Phase Goal:** Maintainers can trust the repository's version, quality-gate,
toolchain, and pure-source evidence before runtime semantics change.

**Verified:** 2026-08-30T02:18:54Z  
**Status:** passed  
**Re-verification:** No — initial verification

## Goal Achievement

Phase 15 achieves its goal. The repository contains a fail-closed, tested
release-evidence implementation; the source-bearing revision is bound to a
successful 29-job hosted run; and the public v0.2.3 correction, tag, and assets
were independently re-read during this verification.

### Observable Truths

The four roadmap success criteria and the additional PLAN frontmatter truths
were deduplicated into the following sixteen observable contracts.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The immutable v0.2.3 metadata mismatch is auditable locally and in the live release without moving the tag or replacing assets. | ✓ VERIFIED | `verify-history` reports tag metadata `0.2.2` and peeled target `a1d02b...`; the live release contains the canonical correction, has 25 assets, and remote refs remain tag object `88d025...` / target `a1d02b...`. |
| 2 | The changelog and canonical correction record state the same shipped-release facts, while README carries no persistent historical warning. | ✓ VERIFIED | `CHANGELOG.md` has dated v0.2.2/v0.2.3 sections and the correction; `docs/release-corrections/v0.2.3.md` contains the canonical paragraph; README contains no v0.2.3 warning. |
| 3 | A clean source-bearing revision has independently visible formatting, lint, mypy, tests, HTML docs, doctest, coverage/evidence, build, and benchmark results with at least 722 passing tests. | ✓ VERIFIED | Hosted run `33286906906` at exact SHA `8c1abd...` completed successfully with 29/29 jobs; the tracked manifest records 879 collected/passing, zero failures/errors/skips, 95.75% total and 92.95% `core.py` coverage. |
| 4 | Maintainers can select auto, pure, or compiled build intent and the legacy pure alias remains compatible. | ✓ VERIFIED | `BuildMode`/`resolve_build_mode` are wired from `setup.py`; focused selector tests passed 10 cases, including pure suppression and conflict handling. |
| 5 | Pure-source verification fails before import on every native `core` shadow, names the paths, and performs no deletion. | ✓ VERIFIED | `verify_source()` calls `find_native_core_shadows()` before `import_module`; the focused non-mutation shadow test passed. |
| 6 | A universal pure wheel and multiple compiled platform wheels can be classified independently by filename, tags, metadata, native members, and mode. | ✓ VERIFIED | `inspect_wheel()` uses central-directory `ZipFile` inspection and cross-checks all identity surfaces; the mixed sorted collection test passed. |
| 7 | Evidence can be intentionally written or checked read-only, with deterministic serialization and actionable stable-field differences. | ✓ VERIFIED | `evidence --write/--check` is wrapped by separate Task targets; manifest comparison is recursive and tested for staleness without rewriting. |
| 8 | The manifest records real pure-source test, coverage, origin, wheel, toolchain, slots, and environment-labeled performance evidence. | ✓ VERIFIED | `evidence/release-baseline.json` contains 879/879 results, `.py` core origin, universal wheel identity, exact tool versions, complete slots inventory, and a `performance_contract` observation excluded only from freshness equality. |
| 9 | Mypy is blocking, ty is separately visible and advisory, and quality categories do not fail fast as one shell chain. | ✓ VERIFIED | `ci.yml` defines separate `typecheck_mypy` and `typecheck_ty` jobs; only ty has `continue-on-error: true`; tests verify the complete independent job set. |
| 10 | Release-producing tools are reproducibly pinned and supported Python 3.10–3.14 locked builds are proven. | ✓ VERIFIED | Build-system/release dependencies are exact pins, setup-uv is pinned to 0.12.6, Task to 3.53.1/full action SHA, and hosted CI reports five successful pure-sdist jobs plus fifteen OS/Python test jobs. |
| 11 | Slots policy recursively accounts for production classes and measures exactly the deliberate `CompiledFuncCondition` and `TransitionError` exceptions. | ✓ VERIFIED | Static inventory and isolated runtime reconciliation are substantive and fail closed; focused static/runtime tests passed; manifest lists 31 classes and exactly two registered exceptions with measured dictionaries and sizes. |
| 12 | Narrative documentation uses durable claims and sends exact observations to the manifest. | ✓ VERIFIED | README/contributor/testing policy uses `700+` and the stable compiled 200,000 ops/sec floor, links the manifest, and documents both exceptions. |
| 13 | The scoped Ruff repairs are behavior-preserving and included in the authoritative clean gate. | ✓ VERIFIED | Ruff format/lint hosted jobs passed at the exact source SHA; code review found no residual finding and the relevant test remained active. |
| 14 | The five public docstring repairs render with Sphinx 9 under warnings-as-errors without changing executable semantics. | ✓ VERIFIED | Exact-SHA Sphinx HTML and doctest jobs passed; review verified the normalized non-docstring AST and focused runtime behavior. |
| 15 | Every CI job invoking Task provisions the exact pinned runner first, and structural tests detect missing, late, or disguised invocations. | ✓ VERIFIED | Nine consumers have the full `arduino/setup-task` SHA and Task 3.53.1 before invocation; focused structural/mutation and workflow tests passed. |
| 16 | Python patch versions remain exact audit observations while freshness normalizes only major/minor; test, coverage, pin, source, artifact, and slots drift stays strict. | ✓ VERIFIED | `_stable_manifest()` deep-copies then normalizes only `toolchain.python` (plus explicitly volatile measurements); focused same-minor, exact inventory, and coverage/pin tests passed. |

**Score:** 16/16 truths verified (0 present, behavior-unverified)

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/build_modes.py` | Shared build-intent parser | ✓ VERIFIED | Substantive Python 3.10-compatible enum/parser; imported and used by setup. |
| `setup.py` and `MANIFEST.in` | Pure/auto/compiled selection and sdist inclusion | ✓ VERIFIED | Selector resolves before optional mypyc path; only `src/fast_fsm/core.py` is compiled; tools are included in sdist. |
| `tools/release_evidence.py` | Source, wheel, history, slots, manifest CLI | ✓ VERIFIED | Substantive implementation with fail-closed checks, archive inspection, static/runtime reconciliation, and deterministic comparison. |
| `tests/test_build_modes.py` | Selector and isolated sdist/wheel behavior | ✓ VERIFIED | 20 collected cases; focused selector behavior passed. |
| `tests/test_release_evidence.py` | Evidence, security, workflow, history, and regression behavior | ✓ VERIFIED | 137 collected cases; eight highest-risk focused behaviors passed in ten parameterized cases. |
| `evidence/release-baseline.json` | Authoritative tracked clean baseline | ✓ VERIFIED | 879/879, pure `.py` origin, meaningful coverage, exact toolchain, deterministic wheel record, and complete slots evidence. |
| `Taskfile.yml` | Canonical local write/check and release gates | ✓ VERIFIED | Thin `uv`-based wrappers establish pure mode, sync locked, preflight, then collect/check. |
| `.github/workflows/ci.yml` | Independent hosted quality and supported-version gates | ✓ VERIFIED | Full-SHA actions, least privilege, exact uv/Task versions, independent jobs, 3.10–3.14 and three-OS matrices. |
| `.github/workflows/release.yml` | Reuse of complete quality gate before artifacts | ✓ VERIFIED | `quality_gate` calls local reusable CI workflow and artifact jobs depend on it; Phase 20 retains strict installed-artifact publication proof. |
| Release-history and maintainer docs | Auditable correction and operating procedure | ✓ VERIFIED | Changelog, correction, releasing/testing/contributing docs, README, and project instructions agree. |
| GitHub Actions run `33286906906` | Exact-SHA remote execution evidence | ✓ VERIFIED | Direct `gh run view`: completed/success, SHA `8c1abd...`, 29 jobs, no failures. |
| GitHub release `v0.2.3` | Live additive correction with immutable identity | ✓ VERIFIED | Direct `gh release view` and `git ls-remote`: canonical text present, 25 assets, tag refs preserved. |

All file artifacts passed GSD existence/substance checks. The generic artifact
checker reported the two external artifacts as files-not-found; direct live
queries above are the authoritative Level 1–4 evidence for those artifacts.

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `setup.py` | `tools/build_modes.py` | `resolve_build_mode(os.environ)` | ✓ WIRED | Build intent selects the sole mypyc branch before compiler fallback. |
| `release_evidence.py` | `src/fast_fsm/core.py` | pre-import shadow scan then source-origin assertion | ✓ WIRED | Focused non-mutation test passed. |
| `release_evidence.py` | wheel archives | `ZipFile` metadata/member inspection | ✓ WIRED | Mixed pure/compiled collection test passed. |
| `release_evidence.py` | baseline manifest | write/check, regression validation, stable comparison | ✓ WIRED | Exact fields flow from tool/test results into JSON and back into a read-only comparison. |
| `Taskfile.yml` | evidence CLI | pure-mode uv wrappers | ✓ WIRED | Sync and preflight precede collection/check. |
| `ci.yml` | `Taskfile.yml` | nine pinned, ordered Task consumers | ✓ WIRED | Structural contract and hosted execution both passed. |
| `release.yml` | `ci.yml` | local reusable `quality_gate` dependency | ✓ WIRED | Artifact jobs cannot begin before the reusable gate succeeds. |
| Canonical correction | live GitHub release | authenticated additive edit and re-read | ✓ WIRED | Current normalized body contains the exact canonical paragraph. |

The generic key-link query's remaining false negatives were conceptual labels
or `file::symbol` identifiers rather than relative paths. Manual code, commit,
and live-state traces above verify each connection.

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Source verifier | `core_origin` | filesystem preflight plus imported module `__file__` | Yes | ✓ FLOWING |
| Wheel verifier | tags, metadata, native members, classified mode | actual ZIP central directory and METADATA/WHEEL files | Yes | ✓ FLOWING |
| Quality baseline | test outcomes and coverage | parsed pytest JUnit and coverage JSON subprocess artifacts | Yes | ✓ FLOWING |
| Slots evidence | inventory/runtime layouts | repository AST plus isolated source runtime audit | Yes | ✓ FLOWING |
| Toolchain evidence | exact versions | locked environment and tool version APIs/commands | Yes | ✓ FLOWING |
| Hosted evidence | conclusions/job matrix | GitHub Actions run API for exact SHA | Yes | ✓ FLOWING |
| Release correction | body/tag/assets | live GitHub release and remote Git refs | Yes | ✓ FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Build selector and pure suppression | focused `pytest tests/test_build_modes.py -k ...` | 10 passed | ✓ PASS |
| Shadow, wheel, slots, manifest, and CI behavior | focused `pytest tests/test_release_evidence.py -k ...` | 10 passed | ✓ PASS |
| Requirement test enumeration | `pytest --collect-only` on the two Phase 15 files | 20 + 137 collected | ✓ PASS |
| Immutable local release history | `release_evidence.py verify-history --tag v0.2.3 ...` | metadata 0.2.2; target `a1d02b...` | ✓ PASS |
| Exact-SHA hosted run | compact `gh run view 33286906906 ...` | completed/success, 29 jobs, 0 failed, 15 matrix tests, 5 pure-sdist jobs | ✓ PASS |
| Live correction | compact `gh release view v0.2.3 ...` | canonical correction true; 25 assets | ✓ PASS |
| Remote immutable refs | `git ls-remote origin refs/tags/v0.2.3{,^\{\}}` | tag object and peeled target unchanged | ✓ PASS |

The full workspace suite was not rerun: the authoritative exact-SHA hosted run
already executed it across all supported OS/Python combinations, and verifier
spot-check policy calls for single named tests instead of repeating the suite.

## Probe Execution

Step 7c: SKIPPED — no Phase 15 probe script is declared and no conventional
`scripts/*/tests/probe-*.sh` exists. The phase uses the tested evidence CLI and
Task/CI gates instead.

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| REL-02 | 15-03, 15-05 | Audit historical v0.2.3 mismatch without moving/replacing tag | ✓ SATISFIED | Local history check plus direct live release/tag/asset verification. |
| REL-04 | 15-01, 15-02 | Intentionally build and identify a pure-Python wheel | ✓ SATISFIED | Explicit pure selector, isolated sdist-to-wheel tests, universal-wheel identity and hosted 3.10–3.14 builds. |
| REL-05 | 15-02 through 15-09 | Clean independent quality gates with documented baseline | ✓ SATISFIED | Manifest 879/879 and exact-SHA 29/29 hosted run. |
| REL-06 | 15-01, 15-02, 15-05, 15-08, 15-09 | Pinned release tools and stable compatibility authority | ✓ SATISFIED | Exact build pins, locked uv, full-SHA Task/action pins, blocking mypy/advisory ty, supported-version run. |
| REL-08 | 15-01 through 15-04 | Document and measure deliberate slots exceptions | ✓ SATISFIED | Recursive static/runtime inventory and exactly two measured registered exceptions. |
| TEST-02 | 15-01, 15-02, 15-03, 15-09 | Prove no native shadow and record meaningful pure coverage | ✓ SATISFIED | Pre-import non-destructive scan, `.py` origin, shadow regression test, 95.75% total / 92.95% core coverage. |

No Phase 15 requirement is orphaned: all six appear in PLAN frontmatter and map
to implementation/tests. `REQUIREMENTS.md` still labels REL-08 and TEST-02 as
pending in its tracking table; this is phase-completion bookkeeping, not a
missing implementation, and should be updated by the orchestrator's canonical
phase-complete transition.

## Decision Coverage

All 16 trackable `15-CONTEXT.md` decisions are honored by shipped artifacts.
The non-blocking decision-coverage query returned `honored: 16`, `total: 16`,
with no unhonored decisions.

## Test Quality Audit

| Test File | Linked Requirements | Active Coverage | Conditional Skips | Circular | Assertion Level | Verdict |
|-----------|---------------------|-----------------|-------------------|----------|-----------------|---------|
| `tests/test_build_modes.py` | REL-04, REL-06 | 20 collected cases | 0 | No | Behavioral/subprocess/value | ✓ STRONG |
| `tests/test_release_evidence.py` | REL-02, REL-04, REL-05, REL-06, REL-08, TEST-02 | 137 collected cases | TryStar only on Python <3.11; native-fixture only if no C compiler | No | Behavioral/mutation/value | ✓ STRONG |

The writes found in these tests create temporary source/archive/manifest
fixtures; they do not generate expected baselines by importing the system under
test. Expected release, wheel, slots, workflow, and manifest facts are explicit
independent assertions. The Python 3.10 TryStar skip is parameter-level, while
portable loop/control-flow cases remain active; it is not the sole evidence for
any requirement.

**Disabled tests on requirements:** 0 requirement gaps  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/fast_fsm/core.py` | 631 | `return []` | ℹ️ Info | Legitimate empty-history result in pre-existing runtime code, not a Phase 15 stub or user-visible placeholder. |
| `15-05-SUMMARY.md` | several | Earlier successful run/count retained | ℹ️ Info | Historical plan evidence is superseded by review/validation/security and direct verification of run `33286906906` / 879 tests. |

No unreferenced TBD/FIXME/XXX debt marker, placeholder implementation, hollow
prop, or console-only handler was found in Phase 15 modified files.

## Structured Disconfirmation Pass

1. **Potential partial requirement:** pure-wheel publication is not performed by
   the current release workflow. This does not fail REL-04: Phase 15 proves
   intentional pure-wheel construction and identity; strict installed-artifact
   publication/parity is explicitly assigned to Phase 20 (REL-03, REL-07,
   TEST-03/04).
2. **Potential misleading test:** slots policy could have passed on static AST
   declarations while runtime layouts differed. It does not: the implementation
   performs isolated runtime reconciliation and the focused runtime-exception
   test passed.
3. **Potential uncovered error path:** a Python 3.10 parser could receive the
   Python 3.11-only `except*` fixture. The final source guards only that parameter;
   exact-SHA hosted Python 3.10 jobs passed on all three operating systems.

## Human Verification Required

N/A — infrastructure/release-evidence phase with no user-facing UI or runtime
flow to test manually. The four deferred PLAN human-checks were already resolved
by scoped review, reviewed clean-manifest generation, explicit authenticated
maintainer authorization, and direct live/exact-SHA evidence. No behavior-
unverified or non-inferable truth remains.

## Gaps Summary

No gaps. All roadmap truths, consolidated PLAN must-haves, artifacts, key links,
data flows, requirement mappings, behavioral checks, threat mitigations, and
external evidence are verified. Later commits after `8c1abd...` change only
planning/security/validation records (plus restoration of pre-existing beads
runtime files), so the successful hosted source revision remains authoritative.

---

_Verified: 2026-08-30T02:18:54Z_  
_Verifier: the agent (gsd-verifier)_
