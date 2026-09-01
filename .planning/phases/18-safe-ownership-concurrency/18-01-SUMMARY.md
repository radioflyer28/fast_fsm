---
phase: 18-safe-ownership-concurrency
plan: 01
subsystem: runtime-concurrency
tags: [threading, mypyc, ownership, pytest, performance]
requires:
  - phase: 17-atomic-transition-lifecycle
    provides: staged atomic transition, failure finalization, history boundaries
provides:
  - per-machine synchronous trigger ownership tracer
  - compile-first native ownership representation and Python 3.10–3.14 CI matrix
  - deterministic Wave 0 ownership contract and fresh-origin suite support
affects: [18-02, 18-03, 18-04, 18-05, release-verification]
actuals:
  tokens: 9127
  tasks: 3
  commits: 5
tech-stack:
  added: []
  patterns:
    - private acquire/owned-body/release trigger envelope
    - strict-XFAIL ownership rows assigned to one downstream plan
    - asserted pure and freshly compiled temporary-export verification
key-files:
  created:
    - tests/test_ownership_concurrency.py
    - tools/phase18_native_probe.py
    - .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_mypyc_guard.py
    - tests/test_performance_benchmarks.py
    - tools/phase16_isolated_verify.py
    - .github/workflows/ci.yml
    - .specify/memory/spr-core-api.md
key-decisions:
  - "Sync trigger ownership is one private per-instance lock/owner envelope with pre-acquisition same-thread rejection."
  - "Native representation support is compile-first locally and matrix-enforced in CI before async expansion."
  - "Every unimplemented ownership case remains a strict XFAIL with exactly one owning plan."
patterns-established:
  - "Public trigger enters ownership once, invokes an already-owned body, and releases in finally."
  - "Fresh-origin tests preserve checkout native shadows and assert pure/native provenance instead of rebuilding in place."
requirements-completed: []
requirements-staged: [OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07]
coverage:
  - id: D1
    description: "Sync trigger rejects same-thread callback reentry, serializes independent threads, and releases after throwable exits."
    requirement: OWN-01
    verification:
      - kind: integration
        ref: "tests/test_ownership_concurrency.py#sync tracer cases"
        status: pass
      - kind: integration
        ref: "tools/phase16_isolated_verify.py --suite phase18"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ownership representation compiles natively and CI declares every supported Python version."
    requirement: OWN-04
    verification:
      - kind: integration
        ref: "tools/phase18_native_probe.py --build-mode compiled --assert-native"
        status: pass
      - kind: other
        ref: "tools/phase18_native_probe.py --check-ci .github/workflows/ci.yml"
        status: pass
    human_judgment: false
  - id: D3
    description: "Wave 0 inventory assigns every requirement and fallback probe while holding downstream behavior at strict RED."
    verification:
      - kind: unit
        ref: "tests/test_ownership_concurrency.py#test_contract_inventory_accounts_for_every_requirement_and_probe"
        status: pass
      - kind: unit
        ref: "tests/test_mypyc_guard.py#test_staged_writer_inventory_names_every_phase18_public_write"
        status: pass
    human_judgment: false
duration: 25min
completed: 2026-09-01
status: complete
---

# Phase 18 Plan 01: Safe Ownership & Concurrency Summary

**A per-machine synchronous trigger ownership tracer with native representation proof, deterministic future-contract inventory, and origin-labelled performance evidence.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-01T16:22:38-04:00
- **Completed:** 2026-09-01T16:47:45-04:00
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments

- Added slotted per-machine sync ownership state, pre-acquisition same-thread rejection, `_trigger_owned()`, and `finally` cleanup around the complete Phase 17 trigger lifecycle.
- Added deterministic Event/Barrier reentry, contention, and throwable-release tests; later ownership work is now explicit strict RED rather than silently omitted.
- Added a standalone native compilation probe, a Python 3.10–3.14 CI matrix contract, and fresh pure/native Phase 18 verification support.
- Recorded measured pure/native tracer observations while retaining the fixed compiled trigger floor as policy.

## Verification

- `uv run python tools/phase18_native_probe.py --build-mode compiled --assert-native` — passed.
- `uv run python tools/phase18_native_probe.py --check-ci .github/workflows/ci.yml` — passed for Python 3.10–3.14.
- `uv run ruff check ...`, `task typecheck-mypy`, and `uv run python tools/release_evidence.py slots-policy --json` — passed.
- `uv run python tools/phase16_isolated_verify.py --suite phase18` — passed in asserted pure and freshly compiled exports; expected strict-XFAIL rows remained RED.

## Task Commits

1. **Task 1: Tracer-first native representation and sync trigger lifecycle** — `03110a9` (RED tests), `226eb18` (GREEN implementation).
2. **Task 2: Build the staged strict-RED inventory and isolated Phase 18 seam** — `0c72033`.
3. **Task 3: Record tracer performance and the implemented SPR contract** — `22e8ac7`.
4. **Coverage correction: mark every future contract row strict RED** — `0c09b1b`.

## Files Created/Modified

- `src/fast_fsm/core.py` — private sync admission/release and owned trigger body.
- `tests/test_ownership_concurrency.py` — Wave 0 tracer, matrix, and downstream strict RED contracts.
- `tools/phase18_native_probe.py` and `.github/workflows/ci.yml` — local native probe and supported-Python CI contract.
- `tests/test_mypyc_guard.py` and `tools/phase16_isolated_verify.py` — structural writer inventory and phase18 origin-aware suite.
- `tests/test_performance_benchmarks.py`, `18-PERFORMANCE-EVIDENCE.md`, and `spr-core-api.md` — tracer floor check, observed measurements, and exact Wave 0 scope.

## Decisions Made

- Sync reentry raises a stable redacted `RuntimeError` before preparation; independent threads block only on the machine they share.
- Only the trigger tracer is implemented in this plan. Direct controls, async ownership, other writers, safe-trigger admission, and declarative-marker replacement remain explicit strict RED work for Plans 18-02 through 18-05.
- Requirements are staged rather than completed: this Wave 0 plan deliberately leaves downstream contract rows red.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Marked every deferred ownership row strict RED**
- **Found during:** Task 2
- **Issue:** The first inventory commit had strict-XFAIL tests for representative future behaviors, but individual contract rows were not all marked.
- **Fix:** Added parameterized strict-XFAIL coverage for every non-tracer row with exactly one owner plan.
- **Files modified:** `tests/test_ownership_concurrency.py`
- **Verification:** Asserted-pure and freshly compiled ownership matrices passed with all future rows remaining XFAIL.
- **Committed in:** `0c09b1b`

**Total deviations:** 1 auto-fixed (Rule 2).

## Issues Encountered

The checkout intentionally contains native `core` shadows. Direct `uv run pytest` imports that pre-existing extension instead of uncommitted source, so it cannot validate the new tracer without replacing user-owned artifacts. The plan's isolated helper was used for every semantic source/native gate; it exports HEAD, overlays exact files, and asserts the imported origin without deleting or rebuilding checkout shadows.

## User Setup Required

None.

## Next Phase Readiness

Plan 18-02 can remove only its `RED until Plan 18-02` rows and complete the remaining synchronous trigger/control envelope. Async, full writer, safe-trigger, and declarative-marker rows remain explicitly owned by later plans.

## Self-Check: PASSED

- All nine plan-owned runtime, test, tool, CI, evidence, and SPR files exist.
- All five task commits exist in repository history.
- No plan-owned stub or placeholder text was introduced.

---
*Phase: 18-safe-ownership-concurrency*
*Completed: 2026-09-01*
