# GitHub Copilot Instructions for Fast FSM

> **This document operationalizes the [Fast FSM Constitution](../.specify/memory/constitution.md).**
> For the rationale behind any standard — testing methodology, documentation requirements,
> architecture decisions — consult the constitution first. This document owns *how* to
> comply; the constitution owns *why* and *what*.

## Project Overview

**Fast FSM** is a high-performance, memory-efficient finite state machine library for Python. It outperforms popular alternatives (python-statemachine, transitions) by 5–20× in speed and ~1000× in memory usage through `__slots__` optimization, direct dictionary lookups, and minimal abstraction layers.

**Layout:** `src/fast_fsm/` is the installable package. Key modules:
- `core.py` — `StateMachine`, `AsyncStateMachine`, `State`, `CallbackState`, `FSMBuilder`, `TransitionResult`
- `conditions.py` — `Condition`, `FuncCondition`, `AsyncCondition`
- `condition_templates.py` — reusable condition builders
- `validation.py` — `FSMValidator`, `EnhancedFSMValidator`, scoring, batch validation

**Other directories:**
- `tests/` — pytest suite
- `examples/` — runnable demo scripts
- `benchmarks/` — performance benchmarking scripts
- `docs/` — Sphinx documentation source (Markdown via myst-parser + autodoc API stubs)

**Task runner:** [`Taskfile.yml`](../Taskfile.yml) provides `task` commands that wrap the workflows below. Use `task --list` to see all available tasks.

**Detailed docs:** See [`README.md`](../README.md) for installation, API reference, and benchmarks.


## Golden Rules

These constraints apply to EVERY task. Violating any of them is a bug.

**Package manager:**
- **ALWAYS use `uv`** — never `python`, `pip`, or `python -m pytest` directly
- `uv run pytest ...` / `uv run python ...` / `uv sync` / `uv add <pkg>`

**Performance:**
- All core classes MUST use `__slots__` — no `__dict__` on hot-path objects
- `trigger()` throughput MUST stay ≥ 200,000 ops/sec
- Core operations (`trigger()`, `can_trigger()`, `add_state()`, `add_transition()`) MUST be O(1)
- Verify with: `uv run python benchmarks/benchmark_fast_fsm.py`

**Backward compatibility:**
- All condition and callback signatures accept `*args, **kwargs`
- Do NOT change existing constructor behavior — new convenience methods are additive only
- Deprecation cycle required before removing any public symbol

**Testing:**
- **Full suite:** `uv run pytest tests/ -x -q` (or `task test`)
- **Baseline (main branch):** 290 passed, 0 failures
- **No parallel execution:** tests run sequentially
- **Incremental testing:** During development, run only targeted tests. Full suite once before push.

**Branch model:**
- Default branch: `main`
- Feature branches: `feat/<desc>`, `fix/<desc>`, `docs/<desc>`
- Remote: `origin` → `https://github.com/radioflyer28/fast_fsm.git`
- All feature work is tracked in **beads** (`bd`) — see [Issue Tracking](#issue-tracking)


## Development Workflow

### Workflow A: Feature/Fix Work (branch-based)

1. **Claim work in beads:**
   ```bash
   bd ready                              # Find unblocked work
   bd update <id> --status in_progress   # Claim the issue
   ```
2. **Create branch:**
   ```bash
   git checkout main
   git checkout -b feat/<desc>           # e.g., feat/async-guards
   ```
3. **Do the work** — code, tests, docs updates
4. **Quality gates** (if .py files changed):
   ```powershell
   # PowerShell (Windows)
   $files = git diff --name-only --diff-filter=ACMR HEAD -- '*.py'
   uv run ruff format $files; uv run ruff check --fix $files   # Phase 1: auto-fix
   uv run ruff check $files; uv run ty check $files            # Phase 2: validate
   ```
5. **Incremental tests** (after each code change):
   ```bash
   uv run pytest tests/test_<relevant>.py -x -q
   ```
6. **Full test suite** (once, right before merge):
   `uv run pytest tests/ -x -q`
7. **Update docs** if changing public API (see [Documentation](#documentation) section)
8. **Merge to main and close:**
   ```bash
   git checkout main
   git merge feat/<desc>
   git branch -d feat/<desc>
   bd close <id> --reason "Merged feat/<desc>"
   git push
   ```

### Workflow B: Direct-to-main (no feature branch)

Use for docs-only changes, config tweaks, or trivial fixes.
Beads tracking is optional for Workflow B — use your judgment.

1. Ensure you're on `main`: `git checkout main`
2. Make changes, commit directly, push


## Issue Tracking

**Primary tracker:** beads (`bd`) — all work items live here.
**Mirror:** GitHub Issues — for visibility and long-term records.

### Beads (bd) — Day-to-Day Tracking

All work is tracked in beads. Use `bd` for ALL task tracking — do NOT use
markdown TODOs, task lists, or other tracking methods.

```bash
bd ready                              # Find unblocked work
bd create "Title" -t task -p 2        # Create a task
bd create "Epic title" -t epic -p 1   # Create an epic (groups related work)
bd update <id> --status in_progress   # Claim work
bd close <id> --reason "Done"         # Complete work
```

**Issue types:**

| Type | Use for |
|------|---------|
| `bug` | Something broken |
| `feature` | New functionality |
| `task` | Work item (tests, docs, refactoring) |
| `epic` | Large feature with subtasks |
| `chore` | Maintenance (dependencies, tooling) |

**Priorities:**

| Priority | Meaning |
|----------|---------|
| `0` | Critical (security, data loss, broken builds) |
| `1` | High (major features, important bugs) |
| `2` | Medium (default, nice-to-have) |
| `3` | Low (polish, optimization) |
| `4` | Backlog (future ideas) |

**Discovered work:** When you find new issues while working, link them:
```bash
bd create "Found bug" -p 1 --deps discovered-from:<parent-id>
```

**Granularity:** Create fine-grained beads issues freely — individual bug fixes, small refactors,
test additions. Group related items under **epics** when they form a coherent feature or initiative.

### GitHub Issues — Coarse-Grained Mirror

GitHub Issues mirror beads **at the epic level** (or bundled related tasks).
The goal is clean project history without noise from trivial items.

**When to create a GitHub Issue:**
- A beads epic is created (feature, major refactor, milestone)
- A cluster of related beads tasks warrants external visibility
- A bug is user-facing or significant enough to track publicly

**When NOT to create a GitHub Issue:**
- Individual small tasks within an epic (tracked only in beads)
- Docs typo fixes, config tweaks, trivial chores
- Discovered sub-tasks that roll up into an existing GitHub Issue

**Convention:** Reference the GitHub Issue in beads epic descriptions and vice versa:
```bash
# In beads epic description, reference the GH issue
bd create "Async guard conditions" -t epic -p 1 --description="GH #12"

# In GitHub Issue body, reference the beads epic
# "Tracked in beads as bd-a1b2"
```

**Closing:** When all child beads tasks under an epic are closed, close the corresponding
GitHub Issue with a summary of what was delivered.


## Code Quality & Formatting

**Two-phase quality gates:** Phase 1 auto-fixes (never fails), Phase 2 validates (may fail).

```powershell
# PowerShell (Windows) — run on changed files
$files = git diff --name-only --diff-filter=ACMR HEAD -- '*.py'
uv run ruff format $files; uv run ruff check --fix $files   # Phase 1
uv run ruff check $files; uv run ty check $files            # Phase 2
```

**Config:** Ruff settings in `pyproject.toml`, Python ≥ 3.10, line length 88.


## Test Suite

**Full command:** `uv run pytest tests/ -x -q`

### Incremental Testing Strategy

| Tier | When | What to run |
|------|------|-------------|
| **Tier 1** | After each code change | Tests that directly exercise modified code |
| **Full suite** | Once before merge/push | All tests |

**Source file → test file mapping:**

> Source files are in `src/fast_fsm/`, test files are in `tests/`.

| Source file changed | Primary test files |
|---------------------|-------------------|
| `core.py` (StateMachine, State) | `test_basic_functionality.py`, `test_advanced_functionality.py`, `test_boundary_negative.py`, `test_state_machine_utils.py`, `test_listeners.py` |
| `core.py` (FSMBuilder, Declarative) | `test_builder.py` |
| `core.py` (AsyncStateMachine) | `test_async.py` |
| `core.py` (logging helpers) | `test_logging_config.py` |
| `validation.py` | `test_validation.py` |
| `conditions.py` | `test_safety_kwargs.py`, `test_async.py` |
| `condition_templates.py` | `test_condition_templates.py`, `test_safety_kwargs.py` |
| README / examples | `test_readme_examples.py` |
| Performance-sensitive | `test_performance_benchmarks.py` |
| Cross-cutting invariants | `test_hypothesis.py` |


## Documentation

**Stack:** Sphinx 9 + myst-parser (Markdown) + furo theme + sphinx-autodoc-typehints.

**Install docs deps:**
```bash
uv sync --group docs
```

**Build HTML docs:**
```bash
uv run sphinx-build -b html docs docs/_build/html
```
Or on Windows: `docs\make.bat html` (after `uv sync --group docs`).

**Build with warnings-as-errors** (CI-ready):
```bash
uv run sphinx-build -b html docs docs/_build/html -W --keep-going
```

**Where things live:**
- `docs/conf.py` — Sphinx configuration (extensions, theme, intersphinx)
- `docs/index.rst` — root toctree connecting all sections
- `docs/QUICK_START.md`, `docs/TUTORIAL.md` — Getting Started guides
- `docs/FSM_LINKING_TECHNIQUES.md` — User Guide (multi-FSM patterns)
- `docs/api/` — autodoc stubs for `core`, `conditions`, `validation` modules
- `docs/examples/` — examples gallery page with `literalinclude`
- `docs/dev/` — developer guide (architecture, testing, contributing)
- `docs/_build/` — generated output (gitignored)

**Sidebar sections (in order):**
1. Getting Started — Quick Start, Tutorial
2. User Guide — FSM Linking Techniques
3. API Reference — Core, Conditions, Validation
4. Examples — gallery with runnable script descriptions
5. Developer Guide — Architecture, Testing, Contributing

**When to rebuild:** After changing any public docstring, adding/removing a public symbol, or editing `docs/` files.

**Docstring format:** Google-style (parsed by `napoleon`). Type annotations go in signatures only — `sphinx-autodoc-typehints` renders them. Do NOT duplicate types in docstrings.


## Architecture & Coding Gotchas

1. **Slots optimization is mandatory.** All classes in `src/fast_fsm/` use `__slots__`. You CANNOT add dynamic attributes to `State`, `StateMachine`, etc. Use `CallbackState` (which has dedicated `_on_enter` / `_on_exit` slots) when you need callback storage on a state.

2. **Argument passing convention.** Every condition `.check()` and state callback (`on_enter`, `on_exit`, `can_transition`) receives `*args, **kwargs`. This MUST be preserved for forward compatibility.

3. **`AsyncStateMachine` vs `StateMachine`.** `AsyncCondition` instances require `AsyncStateMachine` and `trigger_async()`. The sync `StateMachine` will not await async conditions.

4. **`FSMBuilder` auto-detects async.** If any condition is an `AsyncCondition`, `FSMBuilder.build()` returns an `AsyncStateMachine` automatically.

5. **Validation is optional.** `validation.py` is a design-time analysis tool — it adds zero runtime overhead to FSMs that don't use it. Keep it that way.

6. **PowerShell `2>&1` is broken:** Do NOT use `2>&1` in PowerShell. Many programs write informational messages to stderr, and `2>&1` causes PowerShell to wrap them as `ErrorRecord` objects, producing false failures. Just run commands normally.

7. **Dependencies:** The library has a single runtime dependency: `mypy-extensions` (for `@mypyc_attr`). Everything else is in dependency groups: `dev` (pytest, hypothesis, mypy, ruff, ty), `benchmarks` (matplotlib, networkx, python-statemachine, transitions), `docs` (sphinx, furo, myst-parser). Use `uv sync --all-groups` to install everything.

8. **mypyc selective compilation.** Only `core.py` is compiled via mypyc (configured in `setup.py`). `conditions.py` and `condition_templates.py` MUST stay uncompiled — users subclass `Condition` from interpreted Python, and mypyc-compiled classes cannot be subclassed from interpreted code. Build with: `uv run python setup.py build_ext --inplace`. The library MUST work correctly both compiled and uncompiled.


## Landing the Plane (Session Completion)

**When ending a work session**, complete ALL steps below. Work is NOT complete until `git push` succeeds.

1. **File issues for remaining work** — `bd create` for anything that needs follow-up
2. **Run quality gates** (if .py files changed) — tests, linters, docs build
3. **Update issue status** — `bd close` finished work, update in-progress items
4. **Push to remote** — this is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Verify** — all changes committed AND pushed
6. **Hand off** — provide context for next session

**Critical:** Work is NOT complete until `git push` succeeds. Never stop before pushing.


## Maintaining This Document

**When to update:** workflows change, test baselines shift, new patterns emerge, instructions cause confusion.

**How to update:**
1. Edit `.github/copilot-instructions.md` directly
2. Commit: `docs: update copilot instructions - <reason>`
3. Push (can use Workflow B)
