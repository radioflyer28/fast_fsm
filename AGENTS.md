# Agent Instructions

All project workflows, quality gates, Git conventions, and session-completion
rules live in [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Quick Reference

```bash
uv run pytest tests/ -x -q
task typecheck-mypy
task typecheck-ty
git status --short --branch
```

Use the active GSD milestone and phase artifacts under `.planning/` as the
execution plan when the user invokes a GSD workflow. Use GitHub Issues only
when the user explicitly asks to create or update externally tracked work.

## Landing the Plane

When ending a work session:

1. Run the quality gates appropriate to the files changed.
2. Commit all intended work without staging unrelated user files.
3. Pull/rebase safely, resolve any conflicts, and push the current branch.
4. Verify `git status` reports the branch is up to date with its remote.
5. Hand off remaining context and the next concrete action.

Work is not complete until the push succeeds. Never leave completed work only
in the local checkout.
