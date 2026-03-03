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
- **Baseline (main branch):** 101 passed, 0 failures
- **No parallel execution:** tests run sequentially
- **Incremental testing:** During development, run only targeted tests. Full suite once before push.

**Branch model:**
- Default branch: `main`
- Feature branches: `feat/<desc>`, `fix/<desc>`, `docs/<desc>`
- No remote is currently configured — push setup TBD


## Development Workflow

### Workflow A: Feature/Fix Work (branch-based)

1. **Create branch:**
   ```bash
   git checkout main
   git checkout -b feat/<desc>
   ```
2. **Do the work** — code, tests, docs updates
3. **Quality gates** (if .py files changed):
   ```powershell
   # PowerShell (Windows)
   $files = git diff --name-only --diff-filter=ACMR HEAD -- '*.py'
   uv run ruff format $files; uv run ruff check --fix $files   # Phase 1: auto-fix
   uv run ruff check $files; uv run ty check $files            # Phase 2: validate
   ```
4. **Incremental tests** (after each code change):
   ```bash
   uv run pytest tests/test_<relevant>.py -x -q
   ```
5. **Full test suite** (once, right before merge):
   `uv run pytest tests/ -x -q`
6. **Update docs** if changing public API (see [Documentation](#documentation) section)
7. **Merge to main:**
   ```bash
   git checkout main
   git merge feat/<desc>
   git branch -d feat/<desc>
   ```

### Workflow B: Direct-to-main (no feature branch)

Use for docs-only changes, config tweaks, or trivial fixes.

1. Ensure you're on `main`: `git checkout main`
2. Make changes, commit directly


## Code Quality & Formatting

**Two-phase quality gates:** Phase 1 auto-fixes (never fails), Phase 2 validates (may fail).

```powershell
# PowerShell (Windows) — run on changed files
$files = git diff --name-only --diff-filter=ACMR HEAD -- '*.py'
uv run ruff format $files; uv run ruff check --fix $files   # Phase 1
uv run ruff check $files; uv run ty check $files            # Phase 2
```

**Config:** Ruff settings in `pyproject.toml`, Python ≥ 3.12, line length 88.


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
| `core.py` | `test_basic_functionality.py`, `test_advanced_functionality.py` |
| `validation.py` | `test_validation.py` |
| `conditions.py` | `test_safety_kwargs.py` |
| `condition_templates.py` | `test_safety_kwargs.py` |
| README / examples | `test_readme_examples.py` |
| Performance-sensitive | `test_performance_benchmarks.py` |


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

7. **Dependencies:** `hypothesis`, `matplotlib`, `mypy[mypyc]`, `networkx`, `python-statemachine`, and `transitions` are in the main dependency group. The latter two are only for benchmarking comparisons — they are NOT used by the library itself.

8. **mypyc selective compilation.** Only `core.py` is compiled via mypyc (configured in `setup.py`). `conditions.py` and `condition_templates.py` MUST stay uncompiled — users subclass `Condition` from interpreted Python, and mypyc-compiled classes cannot be subclassed from interpreted code. Build with: `uv run python setup.py build_ext --inplace`. The library MUST work correctly both compiled and uncompiled.


## Maintaining This Document

**When to update:** workflows change, test baselines shift, new patterns emerge, instructions cause confusion.

**How to update:**
1. Edit `.github/copilot-instructions.md` directly
2. Commit: `docs: update copilot instructions - <reason>`
3. Push (can use Workflow B)
