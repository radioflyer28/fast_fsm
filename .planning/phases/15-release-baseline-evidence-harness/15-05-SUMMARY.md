---
phase: 15-release-baseline-evidence-harness
plan: 05
subsystem: release-evidence
tags: [github-actions, github-release, release-correction, uv, supported-python]
requires:
  - phase: 15-08
    provides: Pinned Task bootstrap in every Taskfile-consuming CI job
  - phase: 15-09
    provides: Portable Python freshness comparison and refreshed 794-test manifest
provides:
  - Terminal exact-SHA GitHub Actions evidence for every Phase 15 remote gate
  - Additive authenticated v0.2.3 release correction with immutable tag and assets preserved
  - Closed CI-gap tracking records for Task provisioning and portable freshness
affects: [phase-15-verification, rel-02, rel-05, rel-06, release-runbook]
actuals:
  tokens: 4919
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns: [exact-SHA hosted evidence, additive release-note correction, pre-post immutable identity comparison]
key-files:
  created: [.planning/phases/15-release-baseline-evidence-harness/15-05-SUMMARY.md]
  modified: [.beads/issues.jsonl]
key-decisions:
  - "Treat the terminal 29-job Actions table for the pushed SHA, not local YAML or partial matrices, as hosted-gate proof."
  - "Append the normalized canonical correction to the existing release body and require unchanged URL, tag refs, and asset identities."
patterns-established:
  - "Capture release body and remote tag refs privately before an authorized public edit, then record only redacted public identity facts and booleans."
requirements-completed: [REL-02, REL-05, REL-06]
coverage:
  - id: D1
    description: "Exact pushed Phase 15 commit passed every hosted blocking gate, all 15 OS/Python test jobs, and all five Python 3.10-3.14 pure-sdist jobs."
    requirement: REL-05
    verification:
      - kind: e2e
        ref: "GitHub Actions run 33276980655 at beca82ae2099c107fbf4f317e61968c0f3d8c1bb"
        status: pass
    human_judgment: false
  - id: D2
    description: "The existing GitHub v0.2.3 notice contains the canonical additive correction while its URL, tag refs, and 25 asset identities are unchanged."
    requirement: REL-02
    verification:
      - kind: other
        ref: "gh release view v0.2.3 canonical-body assertion plus private pre/post identity comparison"
        status: pass
    human_judgment: false
duration: 20m
completed: 2026-08-29
status: complete
---

# Phase 15 Plan 05: Hosted Gates and v0.2.3 Correction Summary

**The exact Phase 15 corrective SHA passed all hosted CI gates, and the existing v0.2.3 GitHub release now carries the canonical additive metadata correction without changing its tag or 25 published assets.**

## Performance

- **Duration:** 20m across checkpoint resumptions
- **Completed:** 2026-08-29T21:57:09Z
- **Tasks:** 2/2
- **Files modified:** 5 scoped planning/tracking records; external GitHub release body

## Accomplishments

- Pushed `feat/release-baseline-evidence` and proved local and remote refs resolve to exact SHA `beca82ae2099c107fbf4f317e61968c0f3d8c1bb`.
- Watched terminal GitHub Actions run [33276980655](https://github.com/radioflyer28/fast_fsm/actions/runs/33276980655): all 29 jobs passed, including 15 OS/Python tests, five Python 3.10-3.14 pure-sdist jobs, all blocking checks, and advisory `ty`.
- Confirmed the exact hosted workflow pins uv `0.12.6` and uses `uv sync --locked`; the successful evidence-freshness job validates the refreshed 794-test manifest and same-minor Python portability contract.
- Added the canonical correction to the existing GitHub v0.2.3 release notice after explicit maintainer authorization; the live URL, tag refs, and all 25 normalized asset identities compare unchanged before and after.
- Closed `fast_fsm-6yg` and `fast_fsm-bhn` against the successful exact-SHA run; parent Phase 15 bead `fast_fsm-lw2` remains in progress for final verification.

## Hosted Actions Evidence

- **Run URL:** https://github.com/radioflyer28/fast_fsm/actions/runs/33276980655
- **Event:** `workflow_dispatch`
- **Head SHA:** `beca82ae2099c107fbf4f317e61968c0f3d8c1bb`
- **Conclusion:** `success` (29 of 29 jobs)

| Job | Conclusion |
| --- | --- |
| Tests · Python 3.14 · ubuntu-latest | success |
| Verify mypyc build | success |
| Tests · Python 3.13 · windows-latest | success |
| Sphinx HTML | success |
| Tests · Python 3.14 · windows-latest | success |
| Ty compatibility (advisory) | success |
| Pure coverage and release evidence freshness | success |
| Ruff format | success |
| Tests · Python 3.12 · ubuntu-latest | success |
| Sphinx doctest | success |
| Tests · Python 3.13 · macos-latest | success |
| Tests · Python 3.12 · windows-latest | success |
| Mypy compatibility (blocking) | success |
| Tests · Python 3.12 · macos-latest | success |
| Benchmark throughput gate | success |
| Tests · Python 3.13 · ubuntu-latest | success |
| Pure sdist build · Python 3.12 | success |
| Pure sdist build · Python 3.11 | success |
| Pure sdist build · Python 3.10 | success |
| Pure sdist build · Python 3.14 | success |
| Tests · Python 3.14 · macos-latest | success |
| Ruff lint | success |
| Pure sdist build · Python 3.13 | success |
| Tests · Python 3.11 · macos-latest | success |
| Tests · Python 3.10 · macos-latest | success |
| Tests · Python 3.10 · ubuntu-latest | success |
| Tests · Python 3.10 · windows-latest | success |
| Tests · Python 3.11 · ubuntu-latest | success |
| Tests · Python 3.11 · windows-latest | success |

## Live Release Evidence

- **Release URL:** https://github.com/radioflyer28/fast_fsm/releases/tag/v0.2.3
- **Tag:** `v0.2.3`
- **Tag object:** `88d0259d0fce87c088febca10e6669abe0bdbd7a`
- **Peeled target SHA:** `a1d02b1540e8c45eaba6a2f5eb1b6475b26624e2`
- **Asset count:** 25

| Comparison | Result |
| --- | --- |
| Existing release notes retained | true |
| Canonical correction contained in live normalized body | true |
| Release URL unchanged | true |
| Tag name unchanged | true |
| Tag object and peeled target unchanged | true |
| Normalized asset identities unchanged | true |

The record intentionally excludes the release body, authentication details, and private capture paths.

## Task Commits

The two plan tasks changed external state or evidence only; no source commit was made for either task. The scoped metadata commits are `d7534c0` (summary, state, roadmap, requirements) and `e927f9f` (closed CI-gap Beads records).

## Files Created/Modified

- `.planning/phases/15-release-baseline-evidence-harness/15-05-SUMMARY.md` - Redacted durable evidence for the exact hosted run and externally verified release correction.
- `.beads/issues.jsonl` - Closed `fast_fsm-6yg` and `fast_fsm-bhn` with exact-SHA run URLs and retained the parent bead in progress.

## Decisions Made

- Used only terminal Actions results whose `headSha` exactly equals the pushed branch SHA; partial or nearby runs were not accepted.
- Preserved the existing release body and appended the whitespace-normalized canonical paragraph only after explicit authorization.
- Compared public release identity fields before and after the edit, treating tag or artifact drift as a hard stop.

## Deviations from Plan

None - plan executed as specified.

## Issues Encountered

- The first private post-edit comparison attempted to sort asset dictionaries directly and raised a local `TypeError`. The verifier was immediately rerun with an explicit stable sort key before any success claim. No repository file or additional external state changed during that correction.

## Authentication Gates

GitHub Actions read access and release-edit authority were available. The public release edit was performed only after the maintainer's explicit `approved` authorization.

## Known Stubs

None.

## Next Phase Readiness

- REL-02, REL-05, and REL-06 have hosted and live-release evidence; `fast_fsm-6yg` and `fast_fsm-bhn` are closed.
- Parent bead `fast_fsm-lw2` remains in progress for the root orchestrator and final Phase 15 verifier.

## Self-Check: PASSED

The summary exists and passes whitespace and stub scans; the exact-SHA run reached terminal success, the canonical live-body assertion passed, and the post-edit URL, tag-ref, and asset comparisons all passed.

---
*Phase: 15-release-baseline-evidence-harness*
*Plan: 05*
*Completed: 2026-08-29*
