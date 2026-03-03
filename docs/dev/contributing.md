# Contributing

This guide covers how to contribute code, tests, and documentation to
Fast FSM. For architecture details, see {doc}`architecture`.

## Prerequisites

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) — the **only** supported package manager
- [Task](https://taskfile.dev/) — task runner (optional but recommended)

```bash
# Clone and set up
git clone <repo-url>
cd fast_fsm
uv sync              # install all deps
uv sync --group docs # install docs deps too
```

## Branch Model

| Branch | Purpose |
|--------|---------|
| `main` | Default branch, always green |
| `feat/<desc>` | New features |
| `fix/<desc>` | Bug fixes |
| `docs/<desc>` | Documentation-only changes |

### Feature/Fix Workflow

```bash
git checkout main
git checkout -b feat/my-feature

# ... do the work ...

# Quality gates (see below)
# Tests pass
# Merge
git checkout main
git merge feat/my-feature
git branch -d feat/my-feature
```

### Docs-Only Changes

Commit directly to `main` — no feature branch needed.

## Quality Gates

All quality gates are available as `task` commands (see `Taskfile.yml`).
The raw `uv run` commands are shown below for reference.

### Phase 1: Auto-fix (never fails)

```bash
task fix
# equivalent to:
# uv run ruff format .
# uv run ruff check --fix .
```

### Phase 2: Validate (blocks merge)

```bash
task check
# equivalent to:
# uv run ruff format --check .
# uv run ruff check .
# uv run ty check src/fast_fsm/
```

### Phase 3: Tests

```bash
# Incremental — after each code change
uv run pytest tests/test_<relevant>.py -x -q

# Full suite — once before merge
task test
```

### Full Quality + Test Pipeline

```bash
task pre-commit   # fix → check → test-fast
task ci           # check → test → docs-check
```

## Coding Standards

### `__slots__` on Every Class

All classes in `src/fast_fsm/` MUST use `__slots__`. No exceptions.
If you need callback storage on a state, use `CallbackState`.

### `*args, **kwargs` Convention

Every condition `check()` and state callback (`on_enter`, `on_exit`)
MUST accept `*args, **kwargs`. This preserves forward compatibility.

### Import Rules

The import DAG is strict:

```text
conditions  →  core  →  validation
```

`validation` may import from `core`. `core` MUST NOT import `validation`.
No circular imports.

### Docstrings

Google-style docstrings, parsed by Napoleon. Type annotations go in
function signatures only — `sphinx-autodoc-typehints` renders them.
Do **not** duplicate types in docstring text.

```python
def trigger(self, trigger_name: str, *args: Any, **kwargs: Any) -> TransitionResult:
    """Fire a trigger on the FSM.

    Args:
        trigger_name: The name of the trigger to fire.
        *args: Positional arguments passed to conditions and callbacks.
        **kwargs: Keyword arguments passed to conditions and callbacks.

    Returns:
        Result of the transition attempt.

    Raises:
        KeyError: If the trigger does not exist.
    """
```

## Building Documentation

```bash
task docs          # Build HTML docs
task docs-check    # Build with warnings-as-errors (CI-ready)
task docs-serve    # Build and serve locally on port 8765
task docs-clean    # Remove generated output

# Or directly:
uv run sphinx-build -b html docs docs/_build/html
uv run sphinx-build -b html docs docs/_build/html -W --keep-going
```

On Windows: `docs\make.bat html` after `uv sync --group docs`.

Rebuild after changing any public docstring, adding/removing a public
symbol, or editing files under `docs/`.

## mypyc Compilation

`core.py` is compiled to a C extension via mypyc for additional
performance. `conditions.py` and `condition_templates.py` are
deliberately **not** compiled so users can subclass `Condition`.

```bash
# Build the compiled extension
uv run python setup.py build_ext --inplace
```

The library MUST work correctly both compiled and uncompiled. When
adding new classes to `core.py`, ensure they are mypyc-compatible
(use `__slots__`, avoid dynamic attributes, no metaclasses).

Do NOT move condition base classes into `core.py` — this would compile
them and break user subclassing.

## Performance Checklist

Before merging performance-sensitive changes:

- [ ] Run `uv run python benchmarks/benchmark_fast_fsm.py`
- [ ] `trigger()` throughput ≥ 200,000 ops/sec
- [ ] `can_trigger()` throughput ≥ 400,000 ops/sec
- [ ] No `__dict__` on hot-path classes
- [ ] Core operations remain O(1)
