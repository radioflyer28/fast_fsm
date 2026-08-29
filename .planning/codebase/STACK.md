<!-- refreshed: 2026-08-29 -->
# Technology Stack

**Analysis Date:** 2026-08-29

## Languages

**Primary:**
- Python 3.10+ - The installable library, tests, examples, benchmarks, and documentation configuration are Python-based under `src/fast_fsm/`, `tests/`, `examples/`, `benchmarks/`, and `docs/conf.py`.

**Secondary:**
- C (generated extension code) - Optional mypyc compilation of the hot-path module configured by `setup.py`; generated binaries are placed beside `src/fast_fsm/core.py` and are ignored by `.gitignore`.
- Markdown and reStructuredText - User and API documentation in `README.md`, `docs/*.md`, and `docs/index.rst`, processed by Sphinx.
- YAML - GitHub Actions workflow configuration in `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, and `.github/workflows/release.yml`; it is not a runtime configuration format for the package.

## Runtime

**Environment:**
- CPython 3.10–3.14 - The supported range is declared in `pyproject.toml`; the CI matrix in `.github/workflows/ci.yml` tests every version in that range on Ubuntu, Windows, and macOS. Local development is pinned to Python 3.12 by `.python-version`.

**Package Manager:**
- uv - Dependency resolution, virtual-environment execution, packaging, and lockfile management are standardized in `pyproject.toml`, `uv.lock`, and `docs/dev/contributing.md`.
- Lockfile: present - `uv.lock` records the editable `fast-fsm` package and resolved dependency versions for the supported Python markers.

**Build backend:**
- setuptools with wheel - The build requirements and `setuptools.build_meta` backend are declared in `pyproject.toml`.
- Optional C extension build - `setup.py` invokes `mypyc.build.mypycify` for `src/fast_fsm/core.py` when a compiler and mypyc are available; `FAST_FSM_PURE_PYTHON=1` disables compilation.

## Frameworks

**Core:**
- None - Fast FSM is a standalone finite-state-machine library, not an application framework. Public runtime classes and helpers are exported from `src/fast_fsm/__init__.py` and implemented in `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`, `src/fast_fsm/condition_templates.py`, `src/fast_fsm/validation.py`, and `src/fast_fsm/visualization.py`.

**Testing:**
- pytest 8.4.1 (locked) - Test runner configured in `pyproject.toml` and used by `tests/` and `.github/workflows/ci.yml`.
- pytest-asyncio 1.3.0 (locked) - Async test support for `AsyncStateMachine` and `AsyncCondition` tests in `tests/test_async.py` and `tests/test_listeners.py`.
- Hypothesis 6.138.8 (locked) - Property-based FSM invariant testing in `tests/test_hypothesis.py`.
- pytest-cov 6.2.1 (locked) - Optional coverage reporting exposed by the `test-coverage` task in `Taskfile.yml`.

**Build/Dev:**
- mypy 1.17.1 with the `mypyc` extra (locked) - Type checking and the optional C compilation toolchain configured in `pyproject.toml`, `setup.py`, and `Taskfile.yml`.
- ty 0.0.1a19 (locked) - Primary static type checker run by `Taskfile.yml` and `.github/workflows/ci.yml`.
- Ruff 0.12.11 (locked) - Formatting and linting for `src/` and `tests/`, configured through commands in `Taskfile.yml`.
- Task - Shell task runner described by `Taskfile.yml`; it wraps test, quality, build, benchmark, and docs workflows.

**Documentation:**
- Sphinx (9.1.0 on Python 3.12+, with Python-specific locked variants) - Documentation builder configured in `docs/conf.py` and `.github/workflows/docs.yml`.
- MyST parser 5.0.0 on Python 3.11+ (4.0.1 on older supported Python) - Markdown support for `docs/*.md`, configured in `docs/conf.py`.
- furo 2025.12.19 (locked) - HTML theme configured in `docs/conf.py`.
- sphinx-autodoc-typehints 3.9.5 on Python 3.12+ (Python-specific locked variants) - Typed API rendering configured in `docs/conf.py`.

## Key Dependencies

**Critical:**
- `mypy-extensions>=1.0` (1.1.0 locked) - Supplies `mypy_extensions.mypyc_attr`, imported by `src/fast_fsm/core.py`; this is the sole runtime dependency in `pyproject.toml`.
- Python standard library - `asyncio`, `dataclasses`, `logging`, `time`, `typing`, `json`, `collections`, `abc`, and `re` provide runtime behavior without a web, database, or serialization framework. Imports are visible in `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`, `src/fast_fsm/validation.py`, and `src/fast_fsm/visualization.py`.

**Infrastructure:**
- `matplotlib>=3.10.3` (3.10.6 locked) - Optional benchmark plotting in the `benchmarks` dependency group, used by benchmark tooling rather than package runtime.
- `networkx>=3.2` (3.4.2/3.5 locked by Python marker) - Optional benchmark comparison dependency in `pyproject.toml` and `uv.lock`.
- `python-statemachine>=2.5.0` (2.5.0 locked) and `transitions>=0.9.3` (0.9.3 locked) - Optional comparison implementations imported only by `benchmarks/benchmark_py_fsm.py`, `benchmarks/benchmark_transitions_fsm.py`, and `benchmarks/benchmark.py`.
- `sphinx`, `myst-parser`, `furo`, and `sphinx-autodoc-typehints` - Optional docs group in `pyproject.toml`; these are not needed to import `fast_fsm`.

## Configuration

**Environment:**
- Runtime has no required environment variables, service URLs, or credentials; package behavior is configured through Python constructors and objects in `src/fast_fsm/core.py` and `src/fast_fsm/conditions.py`.
- `FAST_FSM_PURE_PYTHON=1` is an optional build/test switch read by `setup.py` and set for pure-Python test/docs tasks in `Taskfile.yml` and GitHub workflows.
- No `.env*` files are detected in the repository. Secrets must not be added to source or documentation.

**Build:**
- `pyproject.toml` - Project metadata, Python requirement, runtime dependency, optional dependency groups, setuptools discovery, package data, pytest configuration, and mypyc file selection.
- `setup.py` - Optional mypyc extension generation for `src/fast_fsm/core.py`, with pure-Python fallback when compilation is unavailable.
- `uv.lock` - Reproducible dependency resolution, including Python-version markers.
- `Taskfile.yml` - Canonical commands for tests, lint/type checks, mypyc builds, benchmarks, and Sphinx.
- `docs/conf.py` - Sphinx extensions, MyST settings, autodoc behavior, doctest setup, and Furo HTML output.
- `.github/workflows/ci.yml` - CI matrix and quality/build gates; `.github/workflows/release.yml` - wheel/sdist packaging; `.github/workflows/docs.yml` - docs build/deployment.

## Platform Requirements

**Development:**
- Python 3.10–3.14 and uv are required for the supported matrix; use Python 3.12 by default as specified in `.python-version`.
- A C compiler and mypyc build dependencies are required only for compiled extension checks (`uv run python setup.py build_ext --inplace` in `Taskfile.yml`); pure-Python operation is the supported fallback.
- Task is optional convenience tooling; equivalent `uv run` commands are documented in `docs/dev/contributing.md`.

**Production:**
- Any supported CPython 3.10–3.14 environment that can install the package from its wheel or source distribution. Compiled wheels are built for Linux, Windows, and macOS by `.github/workflows/release.yml`; source distributions support the pure-Python fallback.
- No server process, container, database, or cloud runtime is required by `fast_fsm` itself.

---

*Stack analysis: 2026-08-29*
