# Releasing and Evidence

This runbook separates local source proof from the hosted release proof. Use
only [uv](https://docs.astral.sh/uv/) commands; Phase 15 requires exactly uv
`0.12.6`:

```bash
uv --version
```

The command must report `uv 0.12.6`. Run the procedure from a clean committed
checkout, not a developer tree that may contain ignored native build output or
unrelated changes. Use a disposable Git worktree/archive at the commit being
reviewed when local artifacts are present.

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
exceptions are `CompiledFuncCondition` and `TransitionError`; their independent
measurements and rationales are part of the evidence.

## Release History and Hosted Proof

Before publication, audit the local immutable history:

```bash
task release-history-check
```

Version 0.2.3 shipped with defective 0.2.2 package metadata. The existing tag
and published artifacts stay unchanged; the additive correction record is
[`v0.2.3.md`](../release-corrections/v0.2.3.md). Correct metadata is released
with v0.3.0, not by rewriting historical identity.

Local evidence does not replace hosted proof. After pushing the exact reviewed
SHA, wait for the independent GitHub Actions jobs, including the supported
Python 3.10–3.14 build matrix. Finally, use authenticated GitHub tooling to
compare the v0.2.3 release URL, tag target, and assets before/after publishing
the canonical correction paragraph. Preserve those immutable fields and record
the terminal job and release-check evidence in the release summary.
