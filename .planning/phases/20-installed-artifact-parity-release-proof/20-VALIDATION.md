---
phase: 20
slug: installed-artifact-parity-release-proof
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-04
updated: 2026-09-04
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. All 15 planned tasks have runnable automated verification. `wave_0_complete` remains false until Plan 20-01 Task 1 creates the two new test modules; planned Nyquist coverage is nevertheless complete.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4.1, pytest-asyncio >=1.3.0, Hypothesis >=6.136.6 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py tests/test_artifact_conformance.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Final local readiness command** | `task release-readiness-check` |
| **Estimated runtime** | ~30–60 seconds for quick source checks; installed/native matrices run as explicit slower gates |

---

## Sampling Rate

- **After every task commit:** Run the exact targeted command in that task's `<verify><automated>` block.
- **After every plan wave:** Run `uv run pytest tests/ -x -q` plus the wave's artifact verifier when packaging or workflow contracts changed.
- **Before `$gsd-verify-work`:** Run `task release-readiness-check`; it covers every locally executable blocking quality/docs/artifact/provenance/performance/slots gate through the non-authorizing canonical `local` projection. Full `release` aggregation remains hosted evidence and is inspected separately before tagging.
- **Max feedback latency:** 60 seconds for source quick loops. Installed builds and benchmarks are named slower gates and do not replace per-task quick feedback.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirements | Threat Ref | Secure Behavior | Automated Command | Test/Artifact State | Status |
|---------|------|------|--------------|------------|-----------------|-------------------|---------------------|--------|
| 20-01-01 | 20-01 | 1 | REL-07, TEST-01, TEST-03, TEST-04 | T-20-01, T-20-02, T-20-03 | Exact artifact bytes, isolated origins, and redacted lifecycle parity are proven end to end. | `uv run pytest tests/test_artifact_conformance.py tests/test_installed_artifacts.py -x -q -k 'tracer or lifecycle or isolation or origin'` | Creates both Wave 0 test modules in this task, then turns the tracer green. | pending |
| 20-01-02 | 20-01 | 1 | TEST-01, TEST-03 | T-20-03, T-20-05 | Every hardened family is deterministic, digest-bound, and payload-safe. | `uv run pytest tests/test_artifact_conformance.py -x -q` | Uses test module created by 20-01-01 and expands it. | pending |
| 20-01-03 | 20-01 | 1 | REL-07, TEST-04 | T-20-01, T-20-02, T-20-04 | Origin spoofing, schema tampering, and bounded parser failures are rejected. | `uv run pytest tests/test_installed_artifacts.py tests/test_artifact_conformance.py -x -q` | Uses both modules created by 20-01-01 and completes their negative matrix. | pending |
| 20-02-01 | 20-02 | 2 | REL-03, REL-07, TEST-04 | T-20-06, T-20-10 | Explicit compiled failure cannot silently become pure output. | `uv run pytest tests/test_build_modes.py tests/test_installed_artifacts.py -x -q -k 'compiled or mypyc or native or pure'` | Extends existing build tests and the Wave 1 installed test module. | pending |
| 20-02-02 | 20-02 | 2 | REL-03, REL-07, TEST-04 | T-20-07, T-20-08, T-20-09 | Bounded sdist inspection and exact pure/compiled lineage both fail closed. | `uv run pytest tests/test_build_modes.py tests/test_installed_artifacts.py -x -q -k 'sdist or archive or derivation or lineage'` | Extends existing/Wave 1 modules; no missing scaffold remains. | pending |
| 20-03-01 | 20-03 | 3 | REL-01, TEST-04 | T-20-11, T-20-13, T-20-14 | Canonical release/local projections reject substitution; local remains non-authorizing. | `uv run pytest tests/test_release_evidence.py -x -q -k 'matrix or aggregate or duplicate or parity or deterministic or malformed'` | Extends existing test module. | pending |
| 20-03-02 | 20-03 | 3 | REL-01, TEST-04 | T-20-12 | Static identity and non-mutating tag-time equality fail closed independently. | `uv run pytest tests/test_release_evidence.py tests/test_readme_examples.py -x -q -k 'identity or version or tag or readme' && uv run sphinx-build -b html docs docs/_build/html -W --keep-going && uv run sphinx-build -b doctest docs docs/_build/doctest` | Existing tests/docs extended. | pending |
| 20-04-01 | 20-04 | 4 | TEST-05 | T-20-15, T-20-16 | Historical schema accepts explicit unavailable detail, rejects unsupported precision, and isolates retrospective runs. | `uv run pytest tests/test_release_evidence.py -x -q -k 'historical or provenance or unavailable or retrospective'` | Extends existing test module. | pending |
| 20-04-02 | 20-04 | 4 | TEST-05 | T-20-15, T-20-16 | Four Phase 16-19 records contain only recorded facts or explicit unavailable states. | `uv run python tools/release_evidence.py historical-evidence --check --json` | Repairs four existing evidence files without retrospective execution. | pending |
| 20-04-03 | 20-04 | 4 | TEST-05 | T-20-17 | Executable slots facts and narrative authorities reconcile without runtime layout changes. | `uv run pytest tests/test_release_evidence.py -x -q -k 'slots or registry' && uv run python tools/release_evidence.py slots-policy --json` | Extends existing tests/docs. | pending |
| 20-05-01 | 20-05 | 5 | TEST-07 | T-20-21 | Four O(1) invariants and separate deterministic diagnostic budgets remain observable. | `uv run pytest tests/test_performance_benchmarks.py tests/test_diagnostic_contracts.py -x -q -k 'constant or scaling or complexity or budget or exact_limit'` | Extends existing tests. | pending |
| 20-05-02 | 20-05 | 5 | TEST-05, TEST-06 | T-20-18, T-20-19, T-20-20, T-20-22 | Only a new exact-command/environment/time installed native compiled record can satisfy the median floor. | `uv run pytest tests/test_installed_artifacts.py tests/test_performance_benchmarks.py tests/test_release_evidence.py -x -q -k 'installed and (compiled or performance or benchmark or median or historical)'` | Uses Wave 1 installed tests and existing performance/evidence tests. | pending |
| 20-06-01 | 20-06 | 6 | REL-07, TEST-01, TEST-03, TEST-04 | T-20-23, T-20-24, T-20-25 | Exact-SHA evidence-only manual/reusable CI routes every artifact to matching-native conformance and exposes terminal artifacts without publication capability. | `uv run pytest tests/test_release_evidence.py -x -q -k 'workflow and (evidence_only or exact_sha or matrix or native or action or cibuildwheel or artifact)'` | Creates and contract-tests the reusable workflow. | pending |
| 20-06-02 | 20-06 | 6 | REL-01, TEST-04, TEST-06 | T-20-26, T-20-27, T-20-29 | Only tag-triggered full release aggregate plus identity can reach release; dispatch/call/local paths cannot. | `uv run pytest tests/test_release_evidence.py -x -q -k 'workflow and (aggregate or identity or release or permission or bypass)'` | Extends workflow graph mutation tests. | pending |
| 20-06-03 | 20-06 | 6 | REL-01, REL-07, TEST-01, TEST-03, TEST-04, TEST-06 | T-20-28, T-20-29 | Local readiness validates only the complete local projection; hosted exact-SHA terminal evidence has a separate read-only inspection path. | `task release-readiness-check` | Extends Taskfile/tests/docs and does not dispatch or inspect hosted CI during implementation. | pending |

*Status vocabulary: pending → red (where TDD applies) → green. Hosted-native success is never inferred from a local green row.*

---

## Wave 0 Creation and Completion

| Artifact/Fixture | Creation Owner | Creation Wave | Completion Owner | Completion Wave |
|------------------|----------------|---------------|------------------|-----------------|
| `tests/test_artifact_conformance.py` | 20-01-01 tracer | 1 | 20-01-02 full oracle inventory | 1 |
| `tests/test_installed_artifacts.py` | 20-01-01 tracer | 1 | 20-01-03 isolation/schema negatives, 20-02-02 sdist lineage, 20-05-02 performance linkage | 1–5 |
| Aggregate-matrix negative fixtures in `tests/test_release_evidence.py` | 20-03-01 | 3 | 20-06-02 release-path mutation coverage | 6 |
| Historical categorical/unavailable/retrospective fixtures | 20-04-01 | 4 | 20-04-02 four-file read-only check | 4 |
| Four-operation invariant/scaling fixtures | 20-05-01 | 5 | 20-05-01 | 5 |
| Exact-SHA evidence-only workflow and release-bypass fixtures | 20-06-01 | 6 | 20-06-02 | 6 |
| Local projection/readiness/hosted-inspection fixtures | 20-06-03 | 6 | 20-06-03 | 6 |

Wave 0 is a scaffold classification, not a separate execution plan. The two missing modules are created by the Wave 1 tracer before their dependent task assertions run. Therefore `wave_0_complete` is correctly `false` now and changes to `true` only after 20-01-01 lands and both creation commands pass.

---

## External Pre-Release Checkpoint

| Checkpoint | Requirements | Why External | Fail-Closed Procedure |
|------------|--------------|--------------|-----------------------|
| Hosted native runner availability and exact-SHA terminal evidence | REL-07, TEST-03, D-03, D-14 | Runner entitlement, quota, and live capacity are account state and cannot be established by YAML inspection. | A maintainer separately dispatches the evidence-only workflow with a chosen ref. After it resolves the ref to one SHA and reaches terminal state, execute `task release-hosted-prerelease-check FAST_FSM_HOSTED_RUN_ID=<authorized-run-id> FAST_FSM_EXPECTED_SHA=<40-char-sha>`. The check reads run metadata, requires successful `aggregate_release_evidence`, downloads SHA-keyed evidence to a temporary directory, and validates the full canonical `release` matrix/digest/artifact bindings. Unavailable, queued, skipped, missing, mismatched, or non-evidence runs block tagging. Implementation does not dispatch or inspect the run. |
| Final public tag target and attached release artifacts | REL-01, D-10 | Tag/release mutation is outside implementation authorization. | Only after the hosted checkpoint passes, supply the concrete changelog date, verify `v0.3.0` resolves to the aggregated commit, and verify release assets match the accepted SHA-256 set before the separately authorized release operation. |

---

## Validation Sign-Off

| Check | Result |
|-------|--------|
| All planned tasks have `<automated>` verification | PASS — 15/15 mapped above |
| Real plan and wave IDs replace placeholders | PASS — plans 20-01 through 20-06, waves 1 through 6 |
| Sampling continuity | PASS — no task lacks an automated command |
| Wave 0 lifecycle is accurate | PASS — missing files are explicitly created in 20-01-01; later expansion/completion owners are distinct |
| No watch-mode flags | PASS |
| Source quick-loop target is under 60 seconds | PASS; slower installed/native gates are isolated named checks |
| Local/hosted authorization boundary | PASS — local readiness uses only non-authorizing `local`; full `release` evidence is exact-SHA hosted and separately inspected before tagging |
| Hosted runner availability is fail-closed | PASS as a planned evidence-only run plus read-only external checkpoint; not executed or claimed |
| `nyquist_compliant` frontmatter | PASS — `true` |

**Approval:** ready for execution. Wave 0 artifacts and all task statuses remain pending until their owning tasks run.
