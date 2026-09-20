---
phase: 32-performance-artifact-progressive-guidance-proof
verified: 2026-09-20T03:09:38Z
status: human_needed
score: 14/14 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 11
  total: 11
  not_honored: []
human_verification:
  - test: "Review the Plan 02 local-release-claim prohibition"
    expected: "Accept that local candidates and older published artifacts are not represented as a published v0.5.0 release."
    why_human: "Judgment-tier prohibition is still flagged-unverified in the approved plan; the automated verifier's favorable reading is non-authoritative."
  - test: "Review the Plan 02 competitor-performance-claim prohibition"
    expected: "Accept that environment-specific competitor observations are not marketed as universal product speed claims."
    why_human: "Judgment-tier prohibition requires explicit human resolution."
  - test: "Review the Plan 03 feature-timing-claim prohibition"
    expected: "Accept that optional-feature timings are descriptive observations, not a hardware-independent speed guarantee."
    why_human: "Judgment-tier prohibition requires explicit human resolution."
  - test: "Review the Plan 04 drone-safety-claim prohibition"
    expected: "Accept that the deterministic drone example is described only as training software, never certified flight control or live hardware integration."
    why_human: "Judgment-tier prohibition requires explicit human resolution."
---

# Phase 32: Performance, Artifact & Progressive Guidance Proof Verification

**Phase goal:** Users can install any supported artifact, retain Fast FSM's direct-path performance, and learn the complete flat-FSM workflow progressively.

**Verdict:** The implementation and automated evidence meet the phase's five roadmap success criteria and nine additional plan-specific truths. Four judgment-tier prohibitions remain explicitly flagged for human review, so the workflow status is `human_needed`, not `passed`. No implementation blocker was found.

## Goal achievement

| # | Observable truth | Status | Independent evidence |
|---|---|---|---|
| 1 | Fresh installed compiled singleton dispatch is direct O(1), at least 200,000/s, without unrelated scans/reflection/allocation. | VERIFIED | `src/fast_fsm/core.py:2981-2982` performs two local dictionary lookups; `tests/test_performance_benchmarks.py:157,1616` checks the selector; installed-wheel performance gate remains in `tools/release_evidence.py:3423`. Latest reviewed installed observation was 619,518/s, above the unchanged floor. |
| 2 | Separate, environment-labelled final-entry, internal-self, external-self and rejection observations show local work independent of unrelated topology. | VERIFIED | `benchmarks/performance_demo.py:286-350` emits four distinct median rows with environment and runtime labels; `tests/test_performance_benchmarks.py:422` passed independently here. Priority rows also carry the label after review fix. Structural/count tests cover unrelated topology without inferring complexity from timings. |
| 3 | Pure source, fresh native, installed pure/compiled wheels and local release-intent artifacts meet one fixed semantic oracle after exact-origin checks. | VERIFIED | `tools/artifact_conformance.py:42-557,2081-2250` defines/validates the fixed rows; `tools/release_evidence.py:3423-3515` verifies artifact snapshot, mode, loader/origin before comparison. `tests/test_installed_artifacts.py:482,511` exercises wheel and native paths. Reviewed `task release-baseline-check`, local evidence and installed-artifact gates passed. This is local proof, not hosted publication. |
| 4 | Controller-owned drone teaches FSM-prioritized telemetry, both self modes, final landings, rejection and committed aircraft commands without a scheduler. | VERIFIED | `examples/drone_failsafes.py:290-405` registers candidates and entry-bound commands; each sample calls one `telemetry_tick`. Named priority/command, self-mode and rejection tests passed independently (3/3); `tests/test_drone_failsafes_example.py:312` also covers final landings. |
| 5 | README and Sphinx progress builder-first to advanced use, migration and exact semantic distinctions. | VERIFIED | First README/Quick Start/Tutorial recipes use `FSMBuilder`; `docs/TUTORIAL.md:236-260` gives advanced roles and four migrations; `docs/api/core.md:176-315` has executable final/mode/rejection contrasts. `tests/test_readme_examples.py:145` migration test passed independently; documented Sphinx HTML/doctest gates passed. |
| 6 | Rehashed wrong, missing, reordered, duplicate or type-equivalent artifact facts fail closed. | VERIFIED | `tools/artifact_conformance.py:2117-2250` enforces exact inventory, field order, required type and value; `tests/test_artifact_conformance.py:108,149` mutation coverage. Exact-type named test passed independently. |
| 7 | Baseline writes are deliberate and guarded; normal `uv.lock`/locked sync is used without patch-version, offline or custom-cache requirements. | VERIFIED | `Taskfile.yml:127-145` separates write/check; `tools/release_evidence.py` limits refreshed facts; `tests/test_release_evidence.py:4794-4875` tests immutable paths and regression rejection. `uv.lock` is tracked and standard `uv sync --locked --all-groups` remains the task path. |
| 8 | Competitor 2.5.0/3.2.1 lanes remain exact, semantically preflighted, labelled, and non-gating. | VERIFIED | Existing isolated comparator and `tests/test_competitor_benchmark_contract.py` remain wired; Phase 32 did not move these rows into the CI release floor. |
| 9 | Local release-candidate evidence is non-authorizing. | VERIFIED | `tools/release_evidence.py:1002-1004,5760` emits `local-non-authorizing` and `authorizes_release=false`; `tests/test_release_evidence.py:4305` checks scope. No tag, Release, or PyPI claim follows from this phase. |
| 10 | One normalized drone sample maps to one FSM event; policy supplies facts, not state routing. | VERIFIED | `examples/drone_failsafes.py:384-403` has a single `trigger("telemetry_tick", ...)`; `tests/test_drone_failsafes_example.py:93,145` checks fact-only policy and one-event dispatch. |
| 11 | Drone self modes and landing finality have distinct lifecycle and no restart edge. | VERIFIED | Builder registrations and final states are present; `tests/test_drone_failsafes_example.py:270,312` checks residency, callback command and post-final failed action. Named self-mode test passed independently. |
| 12 | False eligibility and terminal rejection have distinct results and no uncommitted command. | VERIFIED | `examples/drone_failsafes.py` registers the false/reject candidates; `tests/test_drone_failsafes_example.py:372,392,424` asserts fallthrough, terminal suppression and safety precedence. Named rejection test passed independently. |
| 13 | All four convenience APIs have actionable builder replacements and the correct v0.5.x/v0.6.0 warning window. | VERIFIED | `README.md:143-156`, `docs/QUICK_START.md:62-75`, `docs/TUTORIAL.md:250-260`; `tests/test_readme_examples.py:131,145` checks wording and executes replacements. Direct constructors/from_dict/declarative states are not described as deprecated. |
| 14 | New Sphinx examples are runnable/doctested or backed by an independent smoke test. | VERIFIED | `docs/api/core.md` and `docs/TUTORIAL.md` use MyST `testcode`/`testoutput`; gallery `literalinclude` points to `examples/drone_failsafes.py` and explicitly names `tests/test_drone_failsafes_example.py`; reported `task docs-check` and `task docs-test` passed. |

**Score:** 14/14 verified; 0 behavior-unverified. The earlier full sequential suite was run once by the orchestrator and passed; this verifier ran only focused named tests.

## Artifact and wiring checks

All 18 artifact declarations across the six plans pass the GSD existence/substance query. The actual code confirms their wiring: collector → release evidence → installed probe; benchmark reporter → labelled Taskfile commands; `DroneController.update_from_telemetry` → FSM trigger → bound destination-entry aircraft adapter; README/Quick Start → tutorial/gallery → script; Sphinx `literalinclude` → independently tested script. The key-link query reported three false negatives solely because three `from:` entries are symbols rather than relative file paths (`_SCENARIO_DEFINITIONS`, `DroneController.update_from_telemetry`, `FSMBuilder.on_enter`); manual source tracing verified those links. No dynamic UI/database data-flow trace applies.

## Behavioral spot-checks and test quality

| Check | Result |
|---|---|
| Exact scalar-type mutation, feature-cost reporter, executable migration replacements | 4 tests passed, one existing deprecation warning. |
| Simultaneous failsafe/command order, self-mode lifecycle, command-free rejection | 3 tests passed. |
| Full suite, read-only baseline, installed artifacts/performance, Sphinx HTML/doctest, mypy | Previously passed in this phase's orchestrator run; not re-run as a second full suite here. |

Requirement-linked tests are active and assert values or multi-step behavior, not mere existence. The Phase 32 mutation tests construct altered expected records but do not regenerate their own golden values from the system under test. No Phase 32 requirement depends solely on a skipped test. No phase-declared probe script or deferred `<human-check>` block was found. No unreferenced `TBD`, `FIXME`, or `XXX` marker was found in the modified implementation/docs/tests.

## Requirements and decision coverage

| Requirement | Status | Proof |
|---|---|---|
| PERF-01 | SATISFIED | Direct selector and installed compiled ≥200,000/s gate. |
| PERF-02 | SATISFIED | Local lookup/guard-count and disabled-TRACE tests. |
| PERF-03 | SATISFIED | Four separate labelled observations and provenance checks. |
| PERF-04 | SATISFIED | Fixed oracle, exact origin, local artifact matrix, guarded baseline. |
| DOC-01 | SATISFIED | Runnable controller-owned drone and behavior tests. |
| DOC-02 | SATISFIED | Builder-first public entry guides and order tests. |
| DOC-03 | SATISFIED | Four executable migrations and compatibility timing. |
| DOC-04 | SATISFIED | Executable distinctions in README, Quick Start and Sphinx. |

Decision-coverage gate: 11/11 CONTEXT decisions honored; advisory, no missing decisions. REQUIREMENTS.md still marks PERF-01–04 pending and the roadmap phase/plan boxes unchecked because phase-completion bookkeeping has not yet run; these are not implementation gaps.

## Human verification required

The four plan prohibitions (Plans 02, 03 and 04) are judgment-tier and remain `flagged-unverified`. Source/docs inspection supports each prohibition, but this autonomous verdict is **non-authoritative**. Explicit human review should resolve: (1) local candidates are not presented as published v0.5.0; (2) competitor comparisons are not universal speed claims; (3) feature timings are not hardware-independent guarantees; (4) the drone simulation is not presented as certified or live flight control. These flags, not missing implementation, cause `human_needed`.

## Residual risks and gaps

No must-have failed. A subsequent Phase 32 security follow-up closed T-32-07 by bounding the local build/probe paths; `32-SECURITY.md` records the re-audit and passing evidence tasks. This does not resolve the four judgment-tier human UAT items, so the report remains `human_needed`. Hosted publication/cross-platform matrix is future, separately authorized work; the present local candidate must not be represented as a released v0.5.0 artifact.

---

_Verified: 2026-09-20T03:09:38Z_  
_Verifier: independent Phase 32 GSD verifier_
