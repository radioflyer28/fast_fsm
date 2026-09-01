---
phase: 17-atomic-transition-lifecycle
plan: 05
subsystem: documentation-and-release-evidence
tags: [lifecycle, transition-result, mypyc, sphinx, release-evidence]
requires:
  - phase: 17-04
    provides: Async lifecycle behavior, cancellation semantics, and the initial Phase 17 harness
provides:
  - Public and maintainer lifecycle-contract documentation with an append-only ADR
  - Asserted fresh pure/native Phase 17 semantics and a refreshed pure-source baseline
affects: [phase-18-reentrancy, phase-19-diagnostics, phase-20-installed-wheel-parity, release]
actuals:
  tokens: 11136
  tasks: 3
  commits: 3
tech-stack:
  added: []
  patterns: [fresh export plus explicit import-origin assertion, fixed compiled performance floor]
key-files:
  created:
    - .specify/decisions/ADR-004-atomic-transition-lifecycle.md
  modified:
    - README.md
    - docs/QUICK_START.md
    - docs/dev/architecture.md
    - docs/dev/testing.md
    - tools/phase16_isolated_verify.py
    - evidence/release-baseline.json
key-decisions:
  - "Publish the lifecycle order and structured TransitionResult fields as a single redacted public contract."
  - "Treat fresh exported trees with asserted source/native origins as the authoritative Phase 17 proof; installed-wheel parity remains Phase 20."
  - "Keep a fixed compiled throughput floor while treating exact measurements as environment-labelled observations."
patterns-established:
  - "Phase-specific isolated suites overlay every uncommitted proof artifact before source/native verification."
  - "Lifecycle failures are asserted by stage and redacted public error, with cause identity inspected separately where required."
requirements-completed: [LIFE-01, LIFE-02, LIFE-03, LIFE-04, LIFE-05, LIFE-06]
coverage:
  - id: D1
    description: Public and maintainer lifecycle, result, cancellation, and phase-boundary contract
    requirement: LIFE-01
    verification:
      - kind: integration
        ref: "uv run python tools/phase16_isolated_verify.py --suite phase17"
        status: pass
      - kind: other
        ref: "fresh pure Sphinx HTML/doctest release gate"
        status: pass
    human_judgment: false
  - id: D2
    description: Fresh pure/native lifecycle semantics, origin checks, and fixed compiled floor
    requirement: LIFE-06
    verification:
      - kind: integration
        ref: "tools/phase16_isolated_verify.py#phase17 suite"
        status: pass
    human_judgment: false
  - id: D3
    description: Reviewed pure-source release baseline with slots policy and quality floors
    requirement: LIFE-05
    verification:
      - kind: other
        ref: "task release-baseline-check in asserted fresh pure export"
        status: pass
    human_judgment: false
duration: 20m
completed: 2026-09-01
status: complete
---

# Phase 17 Plan 05: Lifecycle Contract Documentation and Release Evidence Summary

**Published the atomic lifecycle contract, recorded ADR-004, and proved it through fresh pure/native source-tree gates with a current 1,261-test baseline.**

## Performance

- **Duration:** 20m
- **Started:** 2026-09-01T17:47:02Z
- **Completed:** 2026-09-01T18:07:29Z
- **Tasks:** 3/3
- **Files modified:** 11

## Accomplishments

- Documented the stable callback stages, structured result fields, redacted failure boundary, committed-only history, fail-fast behavior, and cancellation propagation for users and maintainers.
- Added accepted ADR-004 without changing accepted ADR-002/ADR-003 or the behavior-owning SPR; Phase 18 reentrancy, Phase 19 diagnostics, and Phase 20 installed-wheel parity remain explicit boundaries.
- Finalized the Phase 17 isolated harness, refreshed the reviewed pure-source baseline to 1,261 passing tests and 97.14% total / 96.04% core coverage, and passed the fresh compiled 200,000 ops/sec floor.

## Task Commits

1. **Task 1: Publish the user-facing lifecycle and result contract** — `be32e4e` (docs)
2. **Task 2: Record the maintainer architecture and append-only decision** — `8dcf671` (docs)
3. **Task 3: Close pure/native semantics, throughput, slots, and baseline evidence** — `be719e3` (test)

## Files Created/Modified

- `README.md` and `docs/QUICK_START.md` — public lifecycle/result usage and cancellation guidance.
- `docs/dev/architecture.md`, `docs/dev/testing.md`, and `.specify/decisions/ADR-004-atomic-transition-lifecycle.md` — maintainer architecture, test matrix, and durable decision record.
- `tools/phase16_isolated_verify.py` — Phase 17 fresh origin matrix, compiled floor selection, slots audit, and pure release gate.
- `tests/test_boundary_negative.py`, `tests/test_async.py`, and `tests/test_basic_functionality.py` — lifecycle-contract assertions that do not expect redacted guard details in public errors.
- `evidence/release-baseline.json` and `17-PERFORMANCE-EVIDENCE.md` — current pure-source quality record and before/tracer/final evidence.

## Decisions Made

- Public errors stay redacted; tests inspect `stage` and, where needed, `cause` identity instead of expecting callback text.
- Fresh exports with asserted import origins are the Phase 17 authority. This proves source-tree pure/native parity only, not installed-wheel parity.
- The only durable performance contract is the compiled 200,000 ops/sec floor; exact benchmark values remain environment-labelled observations.

## Verification

- `uv run python tools/phase16_isolated_verify.py --suite baseline-write --manifest-output evidence/release-baseline.json` — passed; published a 1,261-test pure baseline.
- `uv run python tools/phase16_isolated_verify.py --suite phase17` — passed fresh pure/native semantic matrices, two compiled floor selections, slots policy, full pure tests, Ruff, mypy, Sphinx HTML/doctests, and baseline freshness.
- `task typecheck-ty` — passed.
- Fresh pure Sphinx HTML check after recording final performance evidence — passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test contract drift] Corrected legacy expectations of raw guard details.**
- **Found during:** Tasks 2 and 3 while running asserted fresh pure-source matrices.
- **Issue:** Boundary, async, and basic tests expected callback exception text or pre-lifecycle rejection wording in `TransitionResult.error`, contradicting the implemented redacted guard-result contract.
- **Fix:** Asserted the stable guard stage and redacted public error instead; retained cause identity checks where the public API provides it.
- **Files modified:** `tests/test_boundary_negative.py`, `tests/test_async.py`, `tests/test_basic_functionality.py`.
- **Verification:** Fresh pure full suite passed 1,261 tests and the full fresh pure/native Phase 17 suite passed.
- **Committed in:** `8dcf671`, `be719e3`.

**Total deviations:** 1 auto-fixed issue (Rule 1).

**Impact on plan:** Required to make the existing test matrix faithfully verify the Phase 17 contract; no behavior, ownership, diagnostics, or installed-artifact scope expanded.

## Issues Encountered

- The direct checkout contains stale native shadows, so direct lifecycle tests are not authoritative. All lifecycle proof used fresh exported trees with asserted origins; no native shadows were changed.
- The compiled lifecycle selection emitted the known non-failing mypyc deprecation warnings tracked by `fast_fsm-2fh`; that linked follow-up remains out of scope.

## Known Stubs

None. The changed files were scanned for placeholder and TODO/FIXME patterns.

## User Setup Required

None.

## Next Phase Readiness

Phase 17 documentation and source-tree evidence are complete. Phase 18 owns reentrancy/concurrency, Phase 19 owns diagnostics/logging architecture, and Phase 20 owns installed-wheel parity; none are claimed here.

## Self-Check: PASSED

- Confirmed all documented public, maintainer, ADR, harness, evidence, and summary files exist.
- Confirmed task commits `be32e4e`, `8dcf671`, and `be719e3` exist in repository history.
