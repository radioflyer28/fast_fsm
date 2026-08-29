# Codebase Structure

**Analysis Date:** 2026-08-29

## Directory Layout

```text
fast_fsm/
├── src/fast_fsm/             # Installable package (src layout)
│   ├── __init__.py           # Public exports and package version
│   ├── core.py               # Runtime FSM, states, builder, factories
│   ├── conditions.py         # Condition abstractions and callable wrappers
│   ├── condition_templates.py # Reusable concrete guards
│   ├── validation.py          # Design-time analysis and linting
│   ├── visualization.py       # Mermaid/PlantUML/JSON output
│   └── py.typed               # PEP 561 typing marker
├── tests/                    # Pytest suite, one file per feature area
├── examples/                 # Runnable usage examples
├── benchmarks/               # Throughput and comparative benchmarks
├── docs/                     # Sphinx/MyST documentation source
│   ├── api/                   # API reference pages
│   ├── dev/                   # Architecture, testing, contributing
│   └── examples/              # Example documentation
├── .github/                  # CI, release/docs workflows, GSD agents/skills
├── .planning/                # GSD project state, milestones, phases, maps
├── .specify/                 # Constitution, ADRs, and specification memory
├── pyproject.toml             # Package, dependency, pytest, mypyc metadata
├── setup.py                   # Optional selective mypyc extension build
├── Taskfile.yml               # Developer task aliases
└── uv.lock                   # Locked dependency resolution
```

Generated/local directories such as `build/`, `src/fast_fsm/__pycache__/`,
`.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.hypothesis/`, and
`docs/_build/` are build or test artifacts, not source locations for new code.

## Directory Purposes

**`src/fast_fsm/`:**

- Purpose: Installable library implementation under the configured setuptools
  `src` package root (`pyproject.toml`, `setup.py`).
- Contains: Runtime classes, guards, analysis, output helpers, and typing marker.
- Key files: `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`,
  `src/fast_fsm/condition_templates.py`, `src/fast_fsm/validation.py`,
  `src/fast_fsm/visualization.py`.

**`tests/`:**

- Purpose: Sequential pytest verification of public behavior, boundaries, and
  performance.
- Contains: `test_basic_functionality.py`, `test_advanced_functionality.py`,
  `test_async.py`, `test_builder.py`, `test_validation.py`,
  `test_visualization.py`, plus focused safety, callback, serialization,
  property-based, and benchmark tests.
- Key files: `tests/test_basic_functionality.py`,
  `tests/test_advanced_functionality.py`, `tests/test_async.py`,
  `tests/test_hypothesis.py`.

**`examples/`:**

- Purpose: Runnable demonstrations and executable API examples.
- Contains: Basic traffic light/order flows, async sensors, declarative states,
  cross-FSM coordination, and enhanced builder usage.
- Key files: `examples/traffic_light.py`, `examples/async_sensor_example.py`,
  `examples/declarative_state_example.py`,
  `examples/enhanced_builder_example.py`.

**`benchmarks/`:**

- Purpose: Measure Fast FSM throughput/memory and compare alternative FSM
  libraries.
- Contains: Fast FSM, Python baseline, `transitions`, and
  `python-statemachine` benchmark runners.
- Key files: `benchmarks/benchmark_fast_fsm.py`,
  `benchmarks/benchmark.py`, `benchmarks/performance_demo.py`.

**`docs/`:**

- Purpose: Sphinx documentation source built by `.github/workflows/docs.yml`.
- Contains: MyST Markdown user guides, API pages, developer guides, examples,
  Sphinx configuration, and Make targets.
- Key files: `docs/index.rst`, `docs/conf.py`, `docs/api/core.md`,
  `docs/dev/architecture.md`, `docs/dev/testing.md`.

**`.github/`:**

- Purpose: Repository automation and GSD workflow metadata.
- Contains: `workflows/ci.yml` for lint/tests/build/benchmarks,
  `workflows/docs.yml` for GitHub Pages docs, `workflows/release.yml` for
  wheels/sdist releases, and agent/skill instructions under `agents/`,
  `skills/`, and `get-shit-done/`.

**`.planning/`:**

- Purpose: Project-level GSD planning state and generated codebase intelligence.
- Contains: `PROJECT.md`, `STATE.md`, `ROADMAP.md`, milestone/phase artifacts,
  and `.planning/codebase/` mapping documents.
- Generated status: `.planning/codebase/ARCHITECTURE.md` and
  `.planning/codebase/STRUCTURE.md` are generated analysis artifacts intended to
  be refreshed when the implementation structure changes.

**`.specify/`:**

- Purpose: Durable engineering rules and architecture decisions.
- Contains: `.specify/memory/constitution.md`, SPRs, ADRs under
  `.specify/decisions/`, and specification scripts/templates.

## Key File Locations

**Entry Points:**

- `src/fast_fsm/__init__.py`: User-facing import surface and `__all__`.
- `src/fast_fsm/core.py`: `StateMachine`, `AsyncStateMachine`, `FSMBuilder`,
  `simple_fsm()`, and `quick_fsm()` construction/dispatch entry points.
- `examples/*.py`: Standalone demonstration entry points.

**Configuration:**

- `pyproject.toml`: Package metadata, Python requirement, dependencies, pytest
  options, and mypyc file selection.
- `setup.py`: Optional `core.py` mypyc compilation and pure-Python fallback.
- `Taskfile.yml`: Named developer commands.
- `.github/workflows/ci.yml`: CI matrix and quality gates.
- `docs/conf.py`: Sphinx/MyST/autodoc configuration.

**Core Logic:**

- `src/fast_fsm/core.py`: State graph, transition entries, dispatch lifecycle,
  async dispatch, declarative handlers, builder, logging, and factories.
- `src/fast_fsm/conditions.py`: Extension-friendly condition base classes.
- `src/fast_fsm/condition_templates.py`: Reusable concrete guard patterns.

**Design-Time Logic:**

- `src/fast_fsm/validation.py`: Reachability, completeness, determinism,
  scoring, recommendations, reports, and lint helpers.
- `src/fast_fsm/visualization.py`: Diagram renderers and topology/analysis JSON.

**Testing:**

- `tests/`: Feature-oriented test modules configured by `pyproject.toml`.
- `tests/test_performance_benchmarks.py`: Throughput regression gate.
- `tests/test_mypyc_guard.py`: Compiled/pure-Python compatibility boundary.
- `tests/test_readme_examples.py`: README/API example coverage.

## Naming Conventions

**Files:**

- Python modules use lowercase `snake_case.py`, e.g.
  `condition_templates.py` and `visualization.py`.
- Test modules use `test_<feature>.py`, e.g. `tests/test_async.py` and
  `tests/test_state_machine_utils.py`.
- Documentation uses descriptive lowercase Markdown names; API/developer pages
  are grouped in `docs/api/` and `docs/dev/`.
- Planning map documents use uppercase names, e.g.
  `.planning/codebase/ARCHITECTURE.md`.

**Directories:**

- Source and test directories use lowercase names (`src/fast_fsm/`, `tests/`,
  `examples/`, `benchmarks/`).
- Feature-specific tests stay flat under `tests/`; do not create a parallel
  package hierarchy unless the test surface materially requires it.
- Documentation is grouped by audience (`docs/api/`, `docs/dev/`,
  `docs/examples/`).

**Symbols:**

- Classes use `PascalCase` (`StateMachine`, `AsyncDeclarativeState`).
- Functions/methods and variables use `snake_case` (`trigger_async`,
  `validate_fsm`).
- Private implementation state uses a leading underscore (`_states`,
  `_transitions`, `_execute_transition`).
- Constants use uppercase names (`DEFAULT_COMPLETENESS_WEIGHT` in
  `src/fast_fsm/validation.py`).

## Where to Add New Code

**New Runtime Feature:**

- Primary code: Add to `src/fast_fsm/core.py` when it changes state, transition,
  builder, lifecycle, or dispatch semantics. Preserve `__slots__` and the
  direct dictionary lookup path.
- Tests: Add focused coverage to the matching module under `tests/`; core
  dispatch changes generally also need `tests/test_basic_functionality.py`,
  `tests/test_advanced_functionality.py`, or
  `tests/test_state_machine_utils.py`.
- Public symbol: Re-export from `src/fast_fsm/__init__.py` and update the
  appropriate API page under `docs/api/`.

**New Condition:**

- Implementation: Put extension-friendly base/wrapper types in
  `src/fast_fsm/conditions.py`; put reusable concrete guards in
  `src/fast_fsm/condition_templates.py`.
- Tests: Use `tests/test_safety_kwargs.py`, `tests/test_async.py`, or add a
  focused `tests/test_<condition>.py`.
- Compilation rule: Keep user-subclassable condition modules interpreted; do not
  add them to the mypyc list in `pyproject.toml`/`setup.py`.

**New Validation or Analysis:**

- Implementation: Add structural checks/scoring to
  `src/fast_fsm/validation.py`; add diagram/topology representation to
  `src/fast_fsm/visualization.py`.
- Tests: Use `tests/test_validation.py` or `tests/test_visualization.py`.
- Boundary: Keep design-time walks out of `StateMachine.trigger()` and
  `can_trigger()`.

**New Documentation or Example:**

- User guide: Add to `docs/QUICK_START.md`, `docs/TUTORIAL.md`, or
  `docs/FSM_LINKING_TECHNIQUES.md` according to audience, then link it from
  `docs/index.rst`.
- API details: Add to the matching `docs/api/*.md` page.
- Developer guidance: Add to `docs/dev/architecture.md`,
  `docs/dev/testing.md`, or `docs/dev/contributing.md`.
- Runnable example: Add a script under `examples/` and cover its public behavior
  in `tests/test_readme_examples.py` when it is presented as a documented API
  example.

**Utilities:**

- Shared runtime helpers: Keep them in `src/fast_fsm/core.py` only when they
  belong to the runtime API; otherwise prefer a dedicated package module with a
  narrow dependency direction.
- Test-only helpers: Keep them in the relevant `tests/` module or a clearly
  named test helper; do not import test utilities into `src/`.

## Special Directories

**`build/`:**

- Purpose: Setuptools/mypyc extension and wheel build output.
- Generated: Yes.
- Committed: No; do not edit or add source here.

**`src/fast_fsm.egg-info/`:**

- Purpose: Setuptools package metadata generated from the source distribution.
- Generated: Yes.
- Committed: Present in the working tree; treat as generated metadata and do
  not use it as the source of implementation truth.

**`.planning/codebase/`:**

- Purpose: GSD codebase map consumed by planning/execution workflows.
- Generated: Yes, by mapper workflows.
- Committed: Intended to be committed as planning artifacts; refresh documents
  when architecture or structure changes.

**`.github/get-shit-done/`:**

- Purpose: Repository-local GSD workflow implementation, templates, and helper
  scripts.
- Generated: No; repository workflow support files.
- Committed: Yes.

**`.specify/decisions/`:**

- Purpose: Architecture decision records such as sparse/dense validation scoring,
  result-vs-exception behavior, and mypyc compilation boundaries.
- Generated: No, aside from project tooling output.
- Committed: Yes.

---

*Structure analysis: 2026-08-29*
