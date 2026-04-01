# Technology Stack

## Language & Runtime

| Property         | Value                                              |
|------------------|----------------------------------------------------|
| Language         | Python                                             |
| Min version      | 3.10                                               |
| Package manager  | `uv` (exclusively — never `pip` directly)          |
| Build system     | setuptools + wheel + mypy[mypyc]                   |
| Task runner      | [Taskfile.yml](../../Taskfile.yml) (`task` commands)|
| Entry point      | `src/fast_fsm/__init__.py`                         |

## Package Layout

```
src/fast_fsm/              # installable package (src-layout)
    __init__.py             # public API re-exports
    core.py                 # StateMachine, AsyncStateMachine, State, FSMBuilder, etc.
    conditions.py           # Condition ABC, FuncCondition, AsyncCondition, NegatedCondition
    condition_templates.py  # Reusable condition builders (Always, Never, Comparison, etc.)
    validation.py           # FSMValidator, EnhancedFSMValidator, scoring, batch validation
    visualization.py        # to_mermaid, to_mermaid_fenced, to_mermaid_document
```

## Runtime Dependencies

| Dependency        | Version    | Purpose                                    |
|-------------------|------------|--------------------------------------------|
| `mypy-extensions` | >=1.0      | `@mypyc_attr` decorator for selective compilation |

**Note:** This is the _only_ runtime dependency. The library is extremely lightweight.

## Development Dependencies (dev group)

| Dependency       | Version     | Purpose                          |
|------------------|-------------|----------------------------------|
| `pytest`         | >=8.4.1     | Test framework                   |
| `pytest-asyncio` | >=1.3.0     | Async test support               |
| `pytest-cov`     | >=6.2.1     | Coverage reporting               |
| `hypothesis`     | >=6.136.6   | Property-based testing           |
| `mypy[mypyc]`    | >=1.11.2    | Type checking + C extension compilation |
| `ruff`           | >=0.12.11   | Linter + formatter               |
| `ty`             | >=0.0.1a19  | Type checker (primary)           |

## Benchmarks Dependencies (benchmarks group)

| Dependency           | Version   | Purpose                              |
|----------------------|-----------|--------------------------------------|
| `matplotlib`         | >=3.10.3  | Benchmark visualization              |
| `networkx`           | >=3.2     | Graph representation for benchmarks  |
| `python-statemachine` | >=2.5.0  | Competitor FSM lib for comparison    |
| `transitions`        | >=0.9.3   | Competitor FSM lib for comparison    |

## Docs Dependencies (docs group)

| Dependency                   | Version | Purpose                        |
|------------------------------|---------|--------------------------------|
| `sphinx`                     | >=8.0   | Documentation builder          |
| `sphinx-autodoc-typehints`   | >=2.0   | Auto type hints in docs        |
| `myst-parser`                | >=4.0   | Markdown source support        |
| `furo`                       | >=2024.1| Documentation theme            |

## Build & Compilation

- **mypyc compilation** is selective: only `core.py` is compiled to C extension
  via mypyc (`setup.py` configures `mypycify(["src/fast_fsm/core.py"])`)
- `conditions.py` and `condition_templates.py` are deliberately **uncompiled** —
  users subclass `Condition` from interpreted Python
- The C extension is **optional**: set `FAST_FSM_PURE_PYTHON=1` to skip, or it
  falls back gracefully if mypyc/C compiler unavailable
- Build command: `uv run python setup.py build_ext --inplace`
- Build optimization: `opt_level="3"`, `debug_level="1"`, `separate=False`, `multi_file=False`

## Configuration Files

| File              | Purpose                                                  |
|-------------------|----------------------------------------------------------|
| `pyproject.toml`  | Project metadata, dependencies, tool config (ruff, pytest, uv) |
| `setup.py`        | mypyc ext_modules only (all other metadata in pyproject.toml)  |
| `Taskfile.yml`    | Task runner commands (test, quality, build, benchmark, docs)   |

## Quality Gates

Two-phase quality gate:
1. **Phase 1 (auto-fix):** `uv run ruff format . && uv run ruff check --fix .`
2. **Phase 2 (validate):** `uv run ruff format --check . && uv run ruff check . && uv run ty check src/fast_fsm/`

## Key Technical Constraints

- All core classes **must** use `__slots__` — no `__dict__` on hot-path objects
- `trigger()` throughput must stay ≥200,000 ops/sec
- Core operations (`trigger()`, `can_trigger()`, `add_state()`, `add_transition()`) must be O(1)
- Python target: >=3.10 (uses `match`-era features, type union syntax)
