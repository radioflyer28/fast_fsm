---
phase: 26-canonical-construction-evidence-contract
plan: 04
subsystem: supply-chain
tags: [provenance, python-statemachine, checkpoint, uv-lock]
requires:
  - phase: 26-02
    provides: exact isolated PEP 723 comparison declarations
provides:
  - Human approval of python-statemachine 2.5.0 and 3.2.1 provenance
  - Narrow authority to generate adjacent uv locks for the two comparison scripts
affects: [26-05, comparison-locks, manual-benchmarks]
actuals:
  tokens: 1200
  tasks: 1
  commits: 0
tech-stack:
  added: []
  patterns:
    - blocking human supply-chain approval before dependency resolution
key-files:
  created: []
  modified: []
key-decisions:
  - "The user approved exactly python-statemachine 2.5.0 and 3.2.1 from fgmacedo/python-statemachine."
  - "Approval is limited to adjacent uv locks for the two isolated manual benchmark scripts."
patterns-established:
  - "External comparison dependencies require exact distribution, version, and upstream provenance approval before lock generation."
requirements-completed: []
coverage:
  - id: D1
    description: Exact external comparison package identities and upstream provenance received explicit human approval.
    requirement: PERF-05
    verification:
      - kind: human
        ref: "approved: python-statemachine 2.5.0 and 3.2.1 from fgmacedo/python-statemachine"
        status: pass
    human_judgment: true
duration: checkpoint
completed: 2026-09-15
status: complete
---

# Phase 26 Plan 04: External Package Provenance Summary

**The exact `python-statemachine` 2.5.0 and 3.2.1 releases were human-approved as originating from `fgmacedo/python-statemachine` before lock generation.**

## Approval Recorded

The user supplied the exact required signal:

> approved: python-statemachine 2.5.0 and 3.2.1 from fgmacedo/python-statemachine

This approval authorizes only generation and commit of adjacent uv lockfiles for:

- `benchmarks/comparison/python_statemachine_2_5.py`
- `benchmarks/comparison/python_statemachine_3_2.py`

It does not authorize adding either distribution to ordinary project dependencies, replacing the comparator, or broadening benchmark execution into normal CI.

## Provenance Compared

- PyPI distribution/version: `python-statemachine==2.5.0`
- PyPI distribution/version: `python-statemachine==3.2.1`
- Upstream repository: `fgmacedo/python-statemachine`
- Local PEP 723 declarations: exact matches in both isolated child scripts

## Lock State at Approval

No adjacent comparison lockfile existed or changed before the approval signal.

## Next Phase Readiness

Plan 26-05 may now generate the two exact adjacent uv locks, wire the manual comparison command, and prove ordinary dependency/CI isolation.

## Self-Check: PASSED

- Approval explicitly names both exact versions and the upstream repository.
- Approval scope is narrow and recorded.
- No lockfile was generated before approval.

---
*Phase: 26-canonical-construction-evidence-contract*
*Completed: 2026-09-15*
