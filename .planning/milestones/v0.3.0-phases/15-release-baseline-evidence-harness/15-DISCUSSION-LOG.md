# Phase 15: Release Baseline & Evidence Harness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-29
**Phase:** 15-release-baseline-evidence-harness
**Areas discussed:** v0.2.3 correction record, quality-gate authority, published evidence claims, pure-build identity

---

## v0.2.3 Correction Record

### Release classification

| Option | Description | Selected |
|--------|-------------|----------|
| Shipped with defective metadata | Preserve the release while recording that package metadata reports 0.2.2 | ✓ |
| Withdrawn release | Declare v0.2.3 invalid and direct users to v0.3.0 | |
| Superseded release | Retain v0.2.3 but describe v0.3.0 as its corrective replacement | |

### Correction locations

| Option | Description | Selected |
|--------|-------------|----------|
| Changelog and GitHub release notice | Keep repository and public release records aligned | ✓ |
| Changelog only | Maintain one repository record | |
| Changelog, release notice, and README warning | Put the historical defect in the main user guide too | |

### Changelog organization

| Option | Description | Selected |
|--------|-------------|----------|
| Dated v0.2.2 and v0.2.3 sections | Assign features to actual milestones and annotate the defect | ✓ |
| Move everything into v0.3.0 | Treat features as first correctly packaged in the new release | |
| Keep entries under Unreleased | Add a note without repairing historical ownership | |

### Published artifact handling

| Option | Description | Selected |
|--------|-------------|----------|
| Keep available with defect notice | Preserve reproducibility and direct users to v0.3.0 | ✓ |
| Yank while preserving tag | Prevent new automatic resolution but retain pinned access | |
| No package-index action | Limit correction to repository records | |

**User's choice:** Preserve v0.2.3 as shipped, keep tag and artifacts, repair the changelog, and publish a matching release notice.
**Notes:** Do not add a persistent README warning or retag historical source.

---

## Quality-Gate Authority

### Type checking

| Option | Description | Selected |
|--------|-------------|----------|
| Mypy required, ty advisory | Stable checker blocks; pre-release checker gives feedback | ✓ |
| Both required | Both tools block merges and releases | |
| Split authority | Mypy covers compiled core and ty blocks elsewhere | |

### Coverage enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| Measured baseline with no regressions | Establish clean-source evidence, then prevent decline | ✓ |
| Fixed threshold | Impose an immediate percentage such as 90% | |
| Report only | Publish coverage without blocking | |

### Gate timing

| Option | Description | Selected |
|--------|-------------|----------|
| Every pull request and release | Reuse the complete canonical gate in both workflows | ✓ |
| Pull requests only | Releases trust prior CI | |
| Release only | Keep pull requests lighter | |

### Failure reporting

| Option | Description | Selected |
|--------|-------------|----------|
| Independent blocking checks | Report all formatting, typing, test, and docs failures | ✓ |
| Fail fast | Stop at the first failure | |
| Two-stage gate | Stop after fast checks before tests/docs | |

**User's choice:** Mypy is authoritative, coverage is baseline-regression gated, and the complete independently reported gate blocks pull requests and releases.
**Notes:** `ty` remains useful but advisory while pre-release.

---

## Published Evidence Claims

### Test-count presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Exact generated, rounded narrative | Store precise evidence while prose says “700+ tests” | ✓ |
| Exact everywhere | Automation updates every documented number | |
| No count claims | Publish pass/fail and coverage only | |

### Authoritative evidence location

| Option | Description | Selected |
|--------|-------------|----------|
| Tracked manifest plus CI summary | Keep machine-readable history and readable run output | ✓ |
| CI output only | Avoid a tracked evidence file | |
| Release notes only | Record evidence only at publication | |

### Manifest update workflow

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit generator, CI freshness check | Contributors review generated diffs; CI never commits | ✓ |
| CI updates automatically | Let CI mutate the repository | |
| Manual editing | Maintain evidence without a generator | |

### Performance claims

| Option | Description | Selected |
|--------|-------------|----------|
| Stable threshold in docs, exact results in manifest | Separate durable contract from environment-specific data | ✓ |
| Exact README headline | Advertise the latest benchmark prominently | |
| Defer all evidence to Phase 20 | Omit Phase 15 performance evidence | |

**User's choice:** Use durable rounded prose and stable thresholds, with exact generated data in a tracked manifest verified fresh by CI.
**Notes:** The manifest should include the environment for exact measurements.

---

## Pure-Build Identity

### Build intent

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit auto/pure/compiled modes | One selector with the legacy pure flag retained as an alias | ✓ |
| Legacy flag only | Keep opportunistic compiled fallback | |
| Separate distribution | Publish pure Python under another package name | |

### Installed-mode verification

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical verification command | Inspect wheel tags, metadata, and loaded module origin | ✓ |
| Public build-info API | Expose runtime build identity to applications | |
| Wheel filename only | Rely solely on compatibility tags | |

### Stale native shadowing

| Option | Description | Selected |
|--------|-------------|----------|
| Fail and report exact path | Keep pure verification non-destructive and fail-closed | ✓ |
| Delete automatically | Make verification self-healing by mutating the checkout | |
| Isolated wheel only | Ignore source-mode development shadowing | |

### v0.3.0 artifact set

| Option | Description | Selected |
|--------|-------------|----------|
| Compiled wheels plus universal pure wheel | Native artifacts are preferred; pure wheel is explicit fallback | ✓ |
| Compiled wheels plus source distribution | Unsupported platforms build from source | |
| Pure wheel for testing only | Do not publish the universal wheel | |

**User's choice:** Use explicit build modes, verify identity through a canonical command, fail non-destructively on stale native shadowing, and prepare for compiled plus universal-pure publication.
**Notes:** Actual installed-artifact proof and publication remain Phase 20 scope.

---

## Agent's Discretion

- Exact build-mode variable name and compatibility parsing.
- Evidence manifest name/schema and generator location.
- Exact compatible tool pins and CI job decomposition.
- Coverage-baseline comparison mechanics.
- Changelog/release-notice prose and slots-exception measurement method.

## Deferred Ideas

- Strict compiled-build enforcement, installed artifact parity, and publishing the final artifact set remain Phase 20 work.

