---
phase: 20-installed-artifact-parity-release-proof
plan: "04"
subsystem: release-evidence
tags: [provenance, historical-evidence, sha256, slots, mypyc, adr-006]
requires:
  - phase: 20-installed-artifact-parity-release-proof
    provides: strict release matrix aggregation and the Phase 20 provenance seam from Plans 20-01 through 20-03
provides:
  - complete categorical Phase 16-19 evidence inventory with parent-computed source digests
  - isolated retrospective-rerun identity that cannot rewrite original evidence or release gates
  - one executable and documented three-exception slots policy
affects: [20-05, 20-06, release-manifest, contributor-guidance]
actuals:
  tokens: 10281
  tasks: 3
  commits: 5
tech-stack:
  added: []
  patterns:
    - closed recorded/unavailable provenance objects with citations or searched-source reasons
    - separate non-gating historical and retrospective evidence namespaces
    - executable slots registry reconciled with ADR-backed narrative authorities
key-files:
  created:
    - .planning/phases/20-installed-artifact-parity-release-proof/20-04-SUMMARY.md
  modified:
    - tools/release_evidence.py
    - tests/test_release_evidence.py
    - .github/copilot-instructions.md
    - .specify/memory/spr-core-api.md
    - .planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md
    - .planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md
    - .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md
    - .planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md
key-decisions:
  - "Treat original detail that was not recorded as valid unavailable provenance, never as a value to reconstruct."
  - "Keep retrospective observations in a separately identified namespace that cannot satisfy installed-artifact, parity, or throughput gates."
  - "Keep the executable three-entry slots registry authoritative without changing runtime layout or the core.py-only mypyc boundary."
requirements-completed: [TEST-05]
coverage:
  - id: D1
    description: Historical Phase 16-19 evidence uses complete recorded/unavailable provenance with no release-gate substitution.
    requirement: TEST-05
    verification:
      - kind: unit
        ref: tests/test_release_evidence.py#test_historical_evidence_preserves_unavailable_original_precision
        status: pass
      - kind: other
        ref: uv run python tools/release_evidence.py historical-evidence --check --json
        status: pass
    human_judgment: false
  - id: D2
    description: Static and recursive runtime slots evidence agree with contributor instructions and SPR on exactly three exceptions.
    requirement: TEST-05
    verification:
      - kind: unit
        ref: tests/test_release_evidence.py#test_slots_policy_authorities_name_the_same_three_exceptions
        status: pass
      - kind: other
        ref: uv run python tools/release_evidence.py slots-policy --json
        status: pass
    human_judgment: false
duration: 14m
completed: 2026-09-05
status: complete
---

# Phase 20 Plan 04: Historical Provenance and Slots Policy Summary

**Truthful categorical Phase 16-19 provenance with non-gating retrospective observations and one ADR-backed three-exception slots policy.**

## Performance

- **Duration:** 14m
- **Started:** 2026-09-05T02:19:04Z
- **Completed:** 2026-09-05T02:33:02Z
- **Tasks:** 3/3
- **Files modified:** 8

## Accomplishments

- Replaced loose historical string extraction with a closed `recorded`/`unavailable` schema, fixed four-path inventory, parent-computed SHA-256, strict citations, and retrospective-rerun identity requirements.
- Added machine-readable categorical provenance to every Phase 16-19 evidence file without inventing an original command, build mode, environment, rate, or evidence commit.
- Reconciled `CompiledFuncCondition`, `TransitionError`, and ADR-006-accepted `DiagnosticBudgetExceeded` across the executable registry, recursive audit, contributor guidance, and core SPR.

## Task Commits

1. **Task 1: Define truthful categorical historical provenance** — `a5bae49` (RED tests), `8c276b6` (schema and CLI)
2. **Task 2: Repair all four historical evidence records from authoritative facts** — `6b1a0d2`
3. **Task 3: Reconcile the measured slots registry across authorities** — `1555152` (RED tests), `b994616` (registry and documentation)

## Verification

- `uv run pytest tests/test_release_evidence.py -x -q` — passed
- `uv run python tools/release_evidence.py historical-evidence --check --json` — passed
- `uv run pytest tests/test_release_evidence.py -x -q -k 'slots or registry'` — passed
- `uv run python tools/release_evidence.py slots-policy --json` — passed

## Decisions Made

- Original records can be complete even when an exact fact is unavailable; each unavailable field identifies why and which sources were searched.
- A later rerun has its own command, full commit, environment, UTC timestamp, and observations, and cannot fill an original field or enter installed evidence keys.
- The three measured instance-`__dict__` exceptions have distinct rationales: interpreted condition subclassing, the compiled built-in-exception boundary, and ADR-006 bounded-diagnostic status.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

The linked worktree required local sandbox approval to update its Git index; each task still committed only its owned paths. No external actions were performed.

## Next Phase Readiness

Plans 20-05 and 20-06 can consume the non-gating historical inventory and its digests without treating it as installed proof. The Plan 20-03 uv 0.12.6-versus-0.12.9 baseline gap remains open: this plan did not relax pins or download a replacement.

## Self-Check: PASSED

Verified all eight implementation/documentation files, the summary, and all five
task commits (`a5bae49`, `8c276b6`, `6b1a0d2`, `1555152`, `b994616`) exist.
