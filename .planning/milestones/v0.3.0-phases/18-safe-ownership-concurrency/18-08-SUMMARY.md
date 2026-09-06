---
phase: 18-safe-ownership-concurrency
plan: 08
subsystem: concurrency-safety
tags: [contextvars, declarative-guards, mypyc, pytest, github-actions, security]

requires:
  - phase: 18-07
    provides: Ownership/concurrency behavior, isolation harnesses, and the initial gap evidence.
provides:
  - Machine-qualified declarative prepared-marker consumption at public dispatch boundaries.
  - Fresh pure/native, release-baseline, exact-SHA hosted-matrix, and independent-security evidence.
  - A compliant Plan 18-08 Nyquist map for OWN-01 through OWN-07.
affects: [phase-18-verification, release-evidence, declarative-state-dispatch]

actuals:
  tokens: 13335
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - Separate ContextVar provenance production from public-boundary consumer identity.
    - Treat the post-evidence implementation/baseline SHA as immutable through hosted proof and audit.

key-files:
  created:
    - .planning/phases/18-safe-ownership-concurrency/18-08-SUMMARY.md
  modified:
    - src/fast_fsm/core.py
    - tests/test_ownership_concurrency.py
    - tests/test_mypyc_guard.py
    - evidence/release-baseline.json
    - .planning/phases/18-safe-ownership-concurrency/18-SECURITY.md
    - .planning/phases/18-safe-ownership-concurrency/18-VALIDATION.md

key-decisions:
  - "Preparation provenance stays in the prepared-marker ContextVar while public dispatch independently installs and restores the consuming machine identity."
  - "The baseline commit `78650eaf6adcbc1432c9ee9ae970017285ac267b` remains the audit and hosted-evidence candidate; later documentation commits do not replace it."
  - "All implementation and evidence work remains in a dedicated clean worktree so the dirty source checkout is preserved."

patterns-established:
  - "Cross-machine declarative regressions must reach marker consumption through nested public sync/async dispatch, not by manipulating ContextVars."
  - "Hosted native evidence is accepted only after an explicit exact-SHA assertion across CPython 3.10 through 3.14."

requirements-completed: [OWN-01, OWN-02, OWN-03, OWN-04, OWN-05, OWN-06, OWN-07]

coverage:
  - id: D1
    description: "Machine-qualified declarative marker consumption preserves same-machine behavior and rejects shared-State cross-machine collisions."
    requirement: OWN-05
    verification:
      - kind: integration
        ref: "tests/test_ownership_concurrency.py#test_sync_cross_machine_consumer_rejects_outer_preparation_marker; tests/test_ownership_concurrency.py#test_async_cross_machine_consumer_rejects_outer_preparation_marker"
        status: pass
      - kind: unit
        ref: "tests/test_mypyc_guard.py#test_prepared_declarative_marker_compares_independent_consumer_identity"
        status: pass
    human_judgment: false
  - id: D2
    description: "Refreshed release evidence proves the Phase 18 ownership contract from asserted pure and freshly compiled origins."
    requirement: OWN-01
    verification:
      - kind: integration
        ref: "uv run python tools/phase16_isolated_verify.py --suite phase18"
        status: pass
      - kind: other
        ref: "evidence/release-baseline.json (1,379/1,379; 97.89% total; 97.28% core.py)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The immutable candidate received exact-SHA hosted native-matrix and independent-security-audit proof."
    requirement: OWN-07
    verification:
      - kind: e2e
        ref: "uv run python tools/phase18_native_probe.py --assert-hosted-ci-sha 78650eaf6adcbc1432c9ee9ae970017285ac267b"
        status: pass
      - kind: other
        ref: "18-SECURITY.md independent gsd-security-auditor verdict: SECURED"
        status: pass
    human_judgment: false

duration: 44min
completed: 2026-09-02
status: complete
---

# Phase 18 Plan 08: Machine-Qualified Declarative Marker Evidence Summary

**Declarative prepared-guard consumption now compares independently sourced producer and consumer machine identities, with fresh-origin, exact-SHA hosted-native, and independent-audit proof.**

## Execution Evidence

- **Execution branch:** `fix/phase18-security-gap-20260902195848`
- **Clean worktree:** `/private/tmp/fast-fsm-phase18-gap.nFW19F`
- **Audited implementation/evidence candidate:** `78650eaf6adcbc1432c9ee9ae970017285ac267b`
- **Hosted CI:** [run 33678546626](https://github.com/radioflyer28/fast_fsm/actions/runs/33678546626) — completed `success` for the same candidate SHA.
- **Hosted native matrix:** `tools/phase18_native_probe.py --assert-hosted-ci-sha 78650eaf6adcbc1432c9ee9ae970017285ac267b` passed after successful CPython 3.10, 3.11, 3.12, 3.13, and 3.14 ownership-native jobs.
- **Candidate integrity:** the candidate is an ancestor of the security and validation documentation commits; its runtime, test, harness, probe, and baseline paths have a zero diff from the candidate.

## Accomplishments

- Added the private `_declarative_consumer_machine_id` ContextVar and installed/restored it at all five public sync/async machine-dispatch boundaries. Marker helpers remain preparation-only, and consumption now requires the marker producer to match the active consumer machine.
- Added production-reachable sync and async shared-State collision regressions plus an AST guard proving the distinct ContextVar seams, all public-boundary coverage, preserved hook signatures, and absence of shared mutable registries or hidden caller parameters.
- Regenerated and reviewed the release baseline, then recorded the independent `SECURED` result in `18-SECURITY.md` and a three-task, `nyquist_compliant: true` map in `18-VALIDATION.md`.

## Local Verification

- RED evidence: the two nested cross-machine dispatch regressions initially observed two guard calls on unqualified consumption; the correction produces the required three.
- Fresh focused suites: 8 selected assertions passed from both asserted pure and freshly compiled origins.
- Bounded precheck: 4 selected assertions passed in 0.38 seconds, below the 30-second limit.
- Static quality: targeted Ruff check passed.
- Baseline: `baseline-write` was reviewed and `baseline-check` passed with 1,379/1,379 tests, 97.89% total coverage, and 97.28% `core.py` coverage.
- Full gate: `uv run python tools/phase16_isolated_verify.py --suite phase18` passed, including pure/compiled semantics, release evidence, slots, Ruff, blocking mypy, advisory ty, Sphinx warnings-as-errors, doctests, and the compiled performance gate.

## Task Commits

1. **Task 1: Prove and fix independently qualified declarative marker consumption**
   - `ace64af` — `test(18-08): expose cross-machine declarative marker consumption`
   - `111c91a` — `test(18-08): correct marker isolation AST traversal`
   - `0be4422` — `fix(18-08): qualify declarative marker consumption by machine`
2. **Task 2: Refresh fresh-origin evidence and require the exact-SHA hosted native matrix**
   - `78650ea` — `chore(18-08): refresh marker isolation release baseline` (the immutable candidate)
3. **Task 3: Reaudit the exact candidate, refresh Nyquist mapping, and land**
   - `2dac3c4` — `docs(18-08): record independent ownership security reaudit`
   - `e81a251` — `docs(18-08): refresh Nyquist validation map`
   - This summary is committed separately as the Task 3 landing record.

## Independent Audit and Validation

The read-only `gsd-security-auditor` returned `SECURED` for exactly `78650eaf6adcbc1432c9ee9ae970017285ac267b`; the secure-phase orchestrator mechanically persisted that returned candidate and verdict. `18-SECURITY.md` consequently records `status: verified`, `threats_open: 0`, and T-18-03/T-18-05 as closed. `18-VALIDATION.md` records passing rows `18-08-01`, `18-08-02`, and `18-08-03`, with `status: validated`, `wave_0_complete: true`, and `nyquist_compliant: true`.

## Source Checkout Preservation

The source checkout at `/Users/akriz/code/fast_fsm` began dirty and was never stashed, reset, cleaned, staged, committed, or used for implementation/evidence commands by this plan. All plan work occurred on the registered clean worktree above. The one required Beads fallback was performed by the root orchestrator in the canonical source checkout after candidate capture: bd 1.0.4 has no `bd sync`, so `bd dolt pull && bd dolt push` succeeded locally and each command skipped remote synchronization because no Dolt remote is configured.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test bug] Corrected the AST traversal type guard**
- **Found during:** Task 1 RED test construction.
- **Issue:** The new AST assertion read a node name before establishing that the node was a named expression.
- **Fix:** Guarded the AST node type before reading its name.
- **Files modified:** `tests/test_mypyc_guard.py`
- **Committed in:** `111c91a`

### Versioned Command Deviation

`bd sync` is not available in installed bd 1.0.4. The root orchestrator used the supported canonical-source fallback (`bd dolt pull && bd dolt push`), both of which succeeded locally and reported no configured Dolt remote. No redirected Beads operation was attempted from the execution worktree.

**Impact on plan:** The required Beads synchronization intent was satisfied by the version-supported fallback without touching implementation, evidence, security, or validation content.

## Known Stubs

None. The modified production and test paths contain no placeholder or stub behavior.

## Next Phase Readiness

Phase 18's Plan 08 gap closure is fully evidenced and auditable. The clean worktree remains registered for root-orchestrator verification and removal; no source-checkout cleanup is required.

---
*Phase: 18-safe-ownership-concurrency*
*Completed: 2026-09-02*
