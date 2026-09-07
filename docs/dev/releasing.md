# Releasing and Evidence

This runbook separates local source proof from the hosted release proof. Use
only [uv](https://docs.astral.sh/uv/) commands:

```bash
uv --version
```

The executing version is recorded as evidence for review, but local evidence
does not require one exact uv release. Reproducible dependency selection is
governed by the checked-in `uv.lock` and `uv sync --locked`; neither
`UV_OFFLINE` nor a repository-specific `UV_CACHE_DIR` is required. Hosted
workflows may pin uv to keep their runner environment stable.

Run the procedure from a clean committed checkout, not a developer tree that
may contain ignored native build output or unrelated changes. Use a disposable
Git worktree/archive at the commit being reviewed when local artifacts are
present.

## Pure-Source Evidence Procedure

Set pure mode before creating the environment and keep it set for every later
sync, build, Taskfile, and `uv run` command:

```bash
export FAST_FSM_BUILD_MODE=pure
uv sync --locked --all-groups
uv run python tools/release_evidence.py verify-source --json
```

The source-origin preflight must run immediately after the locked sync and
before tests, coverage, builds, installs, or artifact collection. It proves
that `fast_fsm.core` resolves to `core.py`. If it reports a native shadow, stop:
the command does not delete or move files. Review the exact reported path and,
only if it is an intentionally stale artifact, remove that single file
explicitly before starting again. Never use broad cleanup for release evidence.

After the preflight succeeds, run the blocking gates independently:

```bash
task format-check
task lint
task typecheck-mypy
task test
task docs-check
task docs-test
```

`task typecheck-ty` remains independently visible advisory feedback. It is
valuable to run and resolve, but it is not the blocking release verdict.

Regenerate exact evidence only after the blocking gates succeed:

```bash
task release-baseline-write
git diff -- evidence/release-baseline.json
task release-gate
```

Review the generated manifest diff before committing it. `release-gate` repeats
the named blocking gates and the read-only freshness check; run it after the
intentional write so the current committed source can prove freshness. In a
second equivalent clean checkout, repeat the pure-mode locked-sync and immediate
source-origin preflight, then run:

```bash
task release-baseline-check
```

The baseline records exact test and coverage outcomes, the pure `.py` module
origin, reviewed toolchain versions, a universal pure-wheel identity, and the
recursively discovered slots inventory. The only registered instance-`__dict__`
exceptions are `CompiledFuncCondition`, `TransitionError`, and
`DiagnosticBudgetExceeded`; their independent measurements and rationales are
part of the evidence.

## Release History and Hosted Proof

Before publication, audit the local immutable history:

```bash
task release-history-check
```

Version 0.2.3 shipped with defective 0.2.2 package metadata. The existing tag
and published artifacts stay unchanged; the additive correction record is
[`v0.2.3.md`](../release-corrections/v0.2.3.md). Correct metadata is released
with v0.4.0, not by rewriting historical identity.

Local evidence does not replace hosted proof. After pushing the exact reviewed
SHA, wait for the independent GitHub Actions jobs, including the supported
Python 3.10–3.14 build matrix. Finally, use authenticated GitHub tooling to
compare the v0.2.3 release URL, tag target, and assets before/after publishing
the canonical correction paragraph. Preserve those immutable fields and record
the terminal job and release-check evidence in the release summary.

## Phase 20 Local Installed-Artifact Projection

Phase 20 separates a useful local proof from release authority. Each of the
following commands builds only temporary artifacts and may read repository
state, but does not change tracked evidence, create a ref, contact GitHub, or
authorize a release:

```bash
task release-identity-check
task release-installed-artifacts-check
task release-sdist-check
task release-evidence-local-check
task release-installed-performance-check
task release-slots-check
```

The local projection proves the executing interpreter/platform's direct pure
and compiled wheels, source-distribution pure/compiled children, installed
semantic parity, installed origin, source lineage, and the installed compiled
performance measurement. It emits the explicit `local-non-authorizing` scope;
it cannot stand in for the full CPython 3.10–3.14 hosted platform matrix.

`task release-readiness-check` runs the blocking local sequence in this order:
formatting, lint, mypy, full sequential tests, documentation HTML/doctests,
pure-source origin, baseline freshness, then the six checks above. It records
`task typecheck-ty` separately as advisory feedback; its exit status is not a
release verdict. The compiled installed floor is 200,000 operations/second.
The O(1) runtime and bounded diagnostic-work contracts are independent of that
timing check. Historical Phase 16–19 observations remain categorical context,
not a replacement for a fresh installed compiled measurement.

## Authorized Hosted-Native Evidence Before Tagging

Do not infer native-runner availability from workflow YAML or a local result.
Before any tag operation, an authorized maintainer must manually run the
read-only **Release Evidence** workflow for one reviewed full SHA, then obtain
its run ID from GitHub Actions. Its `ref` input must be that SHA and its `tag`
input must be `v0.4.0`; the workflow itself has read-only contents permission
and contains no release job.

After the run is terminal and successful, inspect it without mutation:

```bash
FAST_FSM_HOSTED_RUN_ID=<authorized-run-id> \
FAST_FSM_EXPECTED_SHA=<40-character-reviewed-sha> \
task release-hosted-prerelease-check
```

This check reads run metadata, requires the `Release Evidence` workflow and
successful terminal `aggregate_release_evidence` job, downloads the exact
SHA-keyed manifest/summary/per-cell records to a temporary directory, and
recomputes the complete `release` matrix. Missing cells, an unavailable native
runner, a queued/cancelled/non-evidence run, wrong head SHA, or a detached
record fails closed. This repository has not treated that external checkpoint
as passed merely because its local workflow contract tests pass.

Only after that inspection passes may a separately authorized `v0.4.0` tag be
created. The tag-only release workflow then independently peels the tag and
requires it, the checkout, and the aggregate commit to be identical before its
sole `contents: write` GitHub-release job can run. The evidence workflow and
the local readiness task can never reach that job.
