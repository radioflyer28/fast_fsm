---
phase: 20
slug: installed-artifact-parity-release-proof
status: partial
nyquist_compliant: false
wave_0_complete: true
created: 2026-09-04
updated: 2026-09-05
---

# Phase 20 — Nyquist Validation Audit

This is the post-execution validation result, replacing the pre-execution
strategy. Tests are behavioral: the artifact checks build and run real pure
and compiled wheels outside the checkout; workflow tests mutate parsed graphs;
and complexity tests observe direct registry work at multiple topology sizes.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest via `uv run pytest` |
| Full suite | `uv run pytest tests/ -x -q` |
| Local release projection | `task release-readiness-check` |
| Hosted release projection | Evidence-only workflow plus `task release-hosted-prerelease-check FAST_FSM_HOSTED_RUN_ID=<id> FAST_FSM_EXPECTED_SHA=<sha>` |

## Requirement Coverage

| Requirement | Behavioral evidence | Command run in this audit | Result |
|---|---|---|---|
| REL-01 | Static v0.3.0 identity, tag graph, local-vs-release authorization, and stale-baseline schema rejection. | `uv run pytest tests/test_release_evidence.py -q -k 'phase20_baseline_static_contract_rejects_stale_identity_and_schema or static_release_identity_requires_every_v030_surface or tag_identity_is_non_mutating'`; `task --silent release-identity-check` | **BLOCKER** — tests pass, but the actual tracked baseline fails the identity gate as stale. |
| REL-03 | Explicit compiled intent propagates compiler failure and rejects a non-native compiled artifact. | `uv run pytest tests/test_build_modes.py -x -q -k 'compiled_intent_propagates_mypyc_failures or compiled_wheel'` | green |
| REL-07 | Exact pure and compiled wheels are installed in fresh environments, reject checkout/provenance escapes, and share the complete oracle. | `uv run pytest tests/test_installed_artifacts.py -q -k 'tracer_installs_exact_artifact_and_matches_source_lifecycle and pure'`; same command with `compiled` | green locally; hosted native matrix remains external. |
| TEST-01 | The fixed hardened oracle records graph, lifecycle, sync/async, builder/declarative, ownership, diagnostics, output, and logging contracts; any required observation mutation fails closed. | `uv run pytest tests/test_artifact_conformance.py -q -k 'hardened_oracle_observes_each_phase_contract or each_ownership_observation or each_diagnostic_boundary'` | green |
| TEST-03 | The real compiled wheel invokes the shared substantive oracle, not an import-only smoke test. | compiled REL-07 tracer command above | green locally; each hosted native cell is manual-only. |
| TEST-04 | Artifact SHA, archive tags, installed metadata/version, package/core origin, mode, architecture, and semantic parity are checked before acceptance. | `uv run pytest tests/test_release_evidence.py -x -q`; pure and compiled tracer commands above | green |
| TEST-05 | Historical evidence schema and installed-performance evidence keep categorical history separate from the final native rerun. | `uv run pytest tests/test_release_evidence.py -x -q` | green for schema/guard behavior; new pinned-toolchain baseline collection is blocked below. |
| TEST-06 | Real installed compiled-wheel tracer asserts native loader plus at least three samples and median at or above 200,000 ops/sec; malformed/below-floor records are rejected. | compiled REL-07 tracer command above; `uv run pytest tests/test_release_evidence.py -x -q` | green locally; hosted matching-native evidence remains manual-only. |
| TEST-07 | `trigger`, `can_trigger`, `add_state`, and `add_transition` keep direct-registry work constant across 4/64/512 unrelated states; diagnostics retain separate exact-limit/one-less tests. | `uv run pytest tests/test_performance_benchmarks.py -q -k 'constant_lookup or constant_registry or coarse_scaling or installed_benchmark_child'` | green |

## Tests Added During This Audit

None. Existing Phase 20 tests already exercise every locally automatable
behavioral edge; adding a duplicate test would not improve coverage. The audit
did run the real pure/compiled artifact tests rather than treating their
fixtures as proof.

## Blocking and Manual-Only Evidence

1. **Baseline regeneration is blocked.** `task --silent release-identity-check`
   actually failed with `release baseline top-level schema is stale.` The
   repository's `evidence/release-baseline.json` still carries legacy v0.2.2
   / schema bytes. Its correction must be generated and reviewed in an
   environment running exactly `uv 0.12.6`; this host has `uv 0.12.9`. The pin
   was not weakened and no baseline was fabricated.
2. **Hosted native matrix evidence is intentionally external.** No workflow was
   dispatched, no tag was created, and no release was published. Before any
   tag operation, a maintainer must run the evidence-only workflow against an
   exact SHA and perform the documented read-only hosted pre-release check.

## Sign-off

| Check | Result |
|---|---|
| Locally automatable hardened-contract coverage | PASS |
| Real installed pure-wheel proof | PASS |
| Real installed compiled-wheel and native-floor proof | PASS (local native runner) |
| Exact uv 0.12.6 baseline freshness | BLOCKED by stale tracked baseline and unavailable exact executable |
| Hosted complete release matrix | MANUAL-ONLY, not dispatched |

Phase 20 therefore remains **partial** and is not Nyquist-compliant until the
exact-toolchain baseline is regenerated and the separately authorized hosted
evidence checkpoint is completed.
