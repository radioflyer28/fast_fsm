---
phase: 32-performance-artifact-progressive-guidance-proof
plan: 01
subsystem: artifact-conformance
tags: [release-evidence, installed-wheel, final-state, transition-mode, expected-rejection]
requires:
  - phase: 27-explicit-final-states
    provides: immutable final-state termination semantics
  - phase: 28-same-state-transition-modes
    provides: internal and external self-transition lifecycle semantics
  - phase: 29-expected-domain-rejection
    provides: terminal guard-rejection result semantics
provides:
  - strict portable finality, self-mode, and expected-rejection oracle rows
  - exact-origin installed pure-wheel tracer for final-versus-sink semantics
  - per-field required-value mutation coverage that fails closed after rehashing
affects: [32-02, release-evidence, installed-artifacts]
actuals:
  tokens: 4501
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [allowlisted scalar semantic rows, independently checked required values, source-to-wheel provenance tracer]
key-files:
  created: []
  modified: [tools/artifact_conformance.py, tests/test_artifact_conformance.py, tests/test_installed_artifacts.py]
key-decisions:
  - "Model explicit finality and a non-final sink as two separately committed machines so identical no-outgoing topology cannot imply termination."
  - "Keep internal and external self modes as separate collector entries while sharing only fixture mechanics."
  - "Make every semantic scalar a required value, so recomputing the semantic digest cannot legitimize a changed fact."
patterns-established:
  - "Artifact conformance scenarios are fixed, payload-free records with complete expected rows and a required-value mutation test."
  - "Installed-wheel claims reuse verify_installed_wheel() and assert archive build intent plus runtime origin before semantic comparison."
requirements-completed: []
coverage:
  - id: D1
    description: Explicit finality is distinguished from a non-final sink in the portable collector and a fresh exact-origin pure wheel.
    requirement: PERF-04
    verification:
      - kind: integration
        ref: tests/test_installed_artifacts.py#test_phase32_final_pure_wheel_preserves_exact_origin_finality_oracle
        status: pass
      - kind: unit
        ref: tests/test_artifact_conformance.py#test_phase32_final_rehashed_required_value_mutation_fails_closed
        status: pass
    human_judgment: false
  - id: D2
    description: Internal/external self lifecycle and false-guard versus terminal rejection selection are strict, bounded semantic records.
    requirement: PERF-04
    verification:
      - kind: unit
        ref: tests/test_artifact_conformance.py#test_phase32_mode_and_rejection_rows_are_exact_and_payload_safe
        status: pass
      - kind: unit
        ref: tests/test_artifact_conformance.py#test_phase32_each_semantic_required_value_rejects_rehashed_mutation
        status: pass
    human_judgment: false
duration: 9min
completed: 2026-09-19
status: complete
---

# Phase 32 Plan 01: Strict Semantic Artifact Oracle Summary

**The shared artifact oracle now proves finality, self-transition lifecycle, and expected-rejection selection through fixed scalar facts rather than artifact agreement alone.**

## Performance

- **Duration:** approximately 9 minutes
- **Started:** 2026-09-19T23:15:00Z
- **Completed:** 2026-09-19T23:23:42Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `final.explicit-versus-sink`, proving a committed `final=True` state terminates while an equivalent non-final sink does not.
- Added deterministic internal-self, external-self, and false-guard-versus-terminal-rejection records, each limited to allowlisted scalar observations.
- Bound every new semantic field to `required_values`; missing, duplicate, reordered, changed, and payload-bearing records remain fail closed even if a caller rebuilds the semantic digest.
- Added the source-to-exact-origin-pure-wheel finality tracer through the existing installed-artifact verifier, not a second harness.

## Task Commits

1. **Task 1: Prove explicit-final versus sink truth through an installed artifact**
   - `12c6e67` — `test(32-01): add finality artifact oracle tests` (RED)
   - `766e29f` — `feat(32-01): prove explicit finality in artifact oracle` (GREEN)
2. **Task 2: Expand the oracle to both self modes and rejection selection**
   - `f44bbc8` — `test(32-01): add self-mode and rejection oracle tests` (RED)
   - `42464ca` — `feat(32-01): extend artifact oracle semantics` (GREEN)

## Verification

- `uv run pytest tests/test_artifact_conformance.py -k 'phase32_final' -x -q` — 2 passed.
- `uv run pytest tests/test_installed_artifacts.py -k 'phase32_final' -x -q` — 1 passed; fresh pure wheel passed archive, build-intent, and runtime-origin proof before comparison.
- `uv run pytest tests/test_artifact_conformance.py -x -q` — 63 passed.
- `uv run pytest tests/test_artifact_conformance.py tests/test_installed_artifacts.py -x -q` — 82 passed, including fresh pure/compiled wheel parity and compiled-floor coverage.
- `uv run ruff check tools/artifact_conformance.py tests/test_artifact_conformance.py tests/test_installed_artifacts.py` — passed.

## Decisions Made

- Finality uses an explicit `State(..., final=True)` and an independently constructed non-final sink, so the record observes semantic termination rather than inferring it from graph shape.
- The collector records callbacks and public `TransitionResult`/history values, with no caller object or exception text in its portable output.
- `PERF-04` remains open for Plan 02, which will extend this fixed oracle to the remaining required runtime forms and reviewed release evidence.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The restricted sandbox cannot initialize the ordinary uv cache for linting and tests. Approved standard `uv run` execution was used without a custom cache, offline setting, or toolchain pin.

## User Setup Required

None.

## Next Phase Readiness

Plan 02 can now compare the fixed rows across clean native, installed compiled, and local release-intent forms without mistaking matching digests for semantic proof.

## Self-Check: PASSED

- Confirmed all three modified implementation/test files exist.
- Confirmed all four Task 1/2 TDD commits are present in Git history.
- No stubs, TODOs, or additional trust-boundary surfaces were introduced.

---
*Phase: 32-performance-artifact-progressive-guidance-proof*
*Completed: 2026-09-19*
