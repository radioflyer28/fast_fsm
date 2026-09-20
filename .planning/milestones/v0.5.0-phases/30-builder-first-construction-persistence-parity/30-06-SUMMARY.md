---
phase: 30-builder-first-construction-persistence-parity
plan: 06
subsystem: construction-parity-closure
tags: [fsm-builder, mypyc, pure-native-parity, deprecation, release-evidence]
requires:
  - phase: 30-05
    provides: Builder-first user guidance and executable construction examples
provides:
  - Synchronized normative contract and structural construction authority proof
  - Identical retained-adapter behavior across asserted pure and fresh native origins
  - Caller-attributed deprecation compatibility boundaries that work in both artifacts
  - Verified native-shadow restoration, throughput, and full-suite closure evidence
affects: [phase-30-audit, native-builds, compatibility-guidance, release-readiness]
actuals:
  tokens: 8036
  tasks: 3
  commits: 3
tech-stack:
  added: []
  patterns:
    - Interpreted cold compatibility wrapper around compiled topology workers
    - Fail-closed native-shadow inventory with recoverable restoration
key-files:
  created:
    - src/fast_fsm/_construction_compat.py
  modified:
    - .specify/memory/spr-core-api.md
    - src/fast_fsm/core.py
    - tests/test_builder.py
    - tests/test_construction_parity.py
    - tests/test_mypyc_guard.py
key-decisions:
  - Retained constructors use interpreted cold wrappers so user warning locations remain exact in pure and native builds.
  - StateMachine explicitly permits interpreted subclasses because retained classmethod factories promise subclass result types.
patterns-established:
  - Native-only compatibility failures require asserted extension evidence and exact source restoration before they are closed.
requirements-completed: [BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, BUILD-08]
coverage:
  - id: D1
    description: Complete construction, declarative, adapter, finality, mode, clone, persistence, and snapshot parity remains identical across pure and freshly compiled origins.
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: FAST_FSM_BUILD_MODE=pure|compiled pytest focused Phase 30 oracle
        status: pass
    human_judgment: false
  - id: D2
    description: Retained construction helpers issue one fixed caller-attributed warning, preserve subclass construction, and keep modern construction silent in both artifacts.
    requirement: BUILD-03
    verification:
      - kind: unit
        ref: tests/test_builder.py#test_deprecated_construction_boundaries_warn_once_at_the_user_call_site
        status: pass
      - kind: unit
        ref: tests/test_builder.py#test_deprecated_construction_public_surface_remains_typed_exported_and_subclass_safe
        status: pass
    human_judgment: false
  - id: D3
    description: Construction authorities stay cold and route every adapter to the one canonical request transaction without entering dispatch.
    requirement: BUILD-06
    verification:
      - kind: unit
        ref: tests/test_mypyc_guard.py#test_phase30_construction_authorities_stay_canonical_and_cold
        status: pass
    human_judgment: false
  - id: D4
    description: The source tree ends in pure mode after a fresh native build, exact extension inventory, compiled throughput check, and full sequential regression suite.
    requirement: BUILD-08
    verification:
      - kind: integration
        ref: task build-check + verified shadow restoration + FAST_FSM_BUILD_MODE=pure pytest tests/ -x -q
        status: pass
    human_judgment: false
duration: 36 min
completed: 2026-09-17
status: complete
---

# Phase 30 Plan 06: Construction Parity Closure Summary

**Fast FSM's builder-first construction, persistence, and compatibility contracts now have synchronized pure/native evidence, exact warning attribution, and a restored pure source tree after native verification.**

## Performance

- **Duration:** 36 min
- **Started:** 2026-09-17T20:29:33Z
- **Completed:** 2026-09-17T21:05:20Z
- **Tasks:** 3/3
- **Files modified:** 6

## Accomplishments

- Synchronized the SPR with all Phase 30 constructor, adapter, persistence, clone, snapshot, and compatibility rules.
- Added an async-inclusive shared observable parity oracle and static authority guard that protects canonical construction and dispatch isolation.
- Closed strict documentation, formatting, mypy, slots, pure/native origin, compiled throughput, and full sequential-suite gates; only verified core extension shadows were moved to `/private/var/folders/34/yzc9zf6903x_8krb7b8s6tlr0000gn/T/fast-fsm-phase30-native-backup.tVsGUL`.

## Task Commits

1. **Task 1: Synchronize the normative construction contract** — `c3aa48e` (`docs`)
2. **Task 2: Lock the complete structural and parity oracle** — `9193289` (`test`)
3. **Task 3: Execute pure/native, restoration, performance, and full-regression closure** — `11b5774` (`fix`)

## Files Created/Modified

- `.specify/memory/spr-core-api.md` — authoritative Phase 30 construction and native-compatible warning contract.
- `src/fast_fsm/_construction_compat.py` — interpreted cold compatibility boundaries retaining exact caller warning attribution.
- `src/fast_fsm/core.py` — installs those boundaries and enables interpreted `StateMachine` subclasses in mypyc builds.
- `tests/test_construction_parity.py` — shared sync/async adapter parity and atomic late-row evidence.
- `tests/test_builder.py` — direct user-call-line warning assertions for valid and invalid retained constructor calls.
- `tests/test_mypyc_guard.py` — structural proof for compatibility installation and the canonical construction seam.

## Decisions Made

- Kept the canonical topology transaction and private compatibility workers intact; the added wrapper is cold-path warning/reporting only and does not enter direct dispatch.
- Used standard `warnings.warn(..., stacklevel=3)` from an interpreted wrapper rather than runtime frame inspection, satisfying both exact attribution and the source auditability policy.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Native warning parity] MypyC native frames could not report the direct public warning call site.**

- **Found during:** Task 3 native semantic oracle.
- **Issue:** The compiled implementation either attributed a retained-constructor warning to pytest internals or could not expose a captureable warning at the test call site.
- **Fix:** Installed typed, interpreted cold wrappers for the four retained compatibility constructors; they emit the fixed warning and delegate to the existing private canonical workers.
- **Files modified:** `src/fast_fsm/_construction_compat.py`, `src/fast_fsm/core.py`, `tests/test_builder.py`, `tests/test_mypyc_guard.py`, `.specify/memory/spr-core-api.md`.
- **Verification:** Exact count/category/message/file/line tests passed in pure and fresh compiled modes; strict Sphinx and slots checks also passed.
- **Committed in:** `11b5774`

**2. [Rule 1 - Compiled subclass contract] The compiled `StateMachine` rejected an interpreted subclass despite retained classmethod factories preserving subclass result type.**

- **Found during:** Task 3 native semantic oracle.
- **Issue:** `DerivedMachine.from_states()` failed only after fresh mypyc compilation.
- **Fix:** Applied Fast FSM's existing `@mypyc_attr(allow_interpreted_subclasses=True)` pattern to `StateMachine`.
- **Files modified:** `src/fast_fsm/core.py`, `tests/test_builder.py`.
- **Verification:** The native warning/subclass focused gate and the complete native oracle passed.
- **Committed in:** `11b5774`

**3. [Rule 1 - Structural test precision] The batch adapter reaches the canonical request type through its normalization helper rather than spelling the type directly.**

- **Found during:** Task 3 focused structural check.
- **Issue:** The new static assertion falsely rejected `_add_transitions_owned` even though it invoked the canonical transaction exactly once.
- **Fix:** Accepted either direct request construction or the one canonical batch-normalization helper while retaining the exact transaction-count and hot-path exclusions.
- **Files modified:** `tests/test_mypyc_guard.py`.
- **Verification:** Focused structural guard and full pure/native oracle passed.
- **Committed in:** `11b5774`

**Total deviations:** 3 Rule 1 corrections.
**Impact on plan:** All repairs were required to make the planned dual-origin oracle truthful; no second topology engine, new dependency, or dispatch-path policy was introduced.

## Issues Encountered

- `task typecheck-ty` remains advisory and reports unresolved relative imports for both the pre-existing `.conditions` import and the new interpreted compatibility module. Mypy is the blocking type gate and passed; ty output was retained visibly as required.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 30 has complete implementation and closure evidence. The repository is on exact pure `src/fast_fsm/core.py` origin with no compiled shadow left in `src/fast_fsm`; it is ready for the milestone/phase audit.

## Self-Check: PASSED

- `30-06-SUMMARY.md` exists and task commits `c3aa48e`, `9193289`, and `11b5774` are present.
- The final `task pure-source-check` and exact Python origin assertion passed after native-shadow restoration.
