# Directory Structure

## Top-Level Layout

```
fast_fsm/                          # Repository root
├── src/
│   └── fast_fsm/                  # Installable package (src-layout)
│       ├── __init__.py            # Public API re-exports, __all__
│       ├── core.py                # Main module (2626 lines) — StateMachine, State, FSMBuilder
│       ├── conditions.py          # Condition ABC + FuncCondition + AsyncCondition (158 lines)
│       ├── condition_templates.py # Reusable condition patterns (232 lines)
│       ├── validation.py          # FSMValidator, EnhancedFSMValidator (1313 lines)
│       └── visualization.py       # Mermaid diagram generation (225 lines)
├── tests/                         # Test suite (8778 lines total, 16 files)
│   ├── test_basic_functionality.py      # Core FSM operations (501 lines)
│   ├── test_advanced_functionality.py   # Advanced transitions, callbacks, clone (1736 lines)
│   ├── test_async.py                    # AsyncStateMachine + async conditions (568 lines)
│   ├── test_boundary_negative.py        # Edge cases and error paths (377 lines)
│   ├── test_builder.py                  # FSMBuilder tests (977 lines)
│   ├── test_condition_templates.py      # Condition template tests (551 lines)
│   ├── test_hypothesis.py              # Property-based tests (188 lines)
│   ├── test_listeners.py               # Listener/observer tests (456 lines)
│   ├── test_logging_config.py           # Logging configuration tests (104 lines)
│   ├── test_mypyc_guard.py             # mypyc subclassing safety tests (168 lines)
│   ├── test_performance_benchmarks.py   # Performance threshold tests (449 lines)
│   ├── test_readme_examples.py          # README code example tests (460 lines)
│   ├── test_safety_kwargs.py            # *args/**kwargs forwarding tests (579 lines)
│   ├── test_state_machine_utils.py      # Utility method tests (296 lines)
│   ├── test_validation.py              # Validation module tests (1041 lines)
│   └── test_visualization.py           # Visualization output tests (327 lines)
├── examples/                      # Runnable demo scripts (1202 lines total)
│   ├── async_sensor_example.py    # Async FSM with sensor simulation (224 lines)
│   ├── cross_fsm_demo.py         # Multi-FSM coordination patterns (231 lines)
│   ├── declarative_state_example.py  # DeclarativeState usage (253 lines)
│   ├── enhanced_builder_example.py   # FSMBuilder fluent API (270 lines)
│   ├── order_processing.py       # E-commerce order workflow (141 lines)
│   └── traffic_light.py          # Simple traffic light FSM (83 lines)
├── benchmarks/                    # Performance benchmarking (3178 lines total)
│   ├── benchmark_fast_fsm.py     # Fast FSM standalone benchmark (296 lines)
│   ├── benchmark_my_fsm.py       # Legacy benchmark variant (787 lines)
│   ├── benchmark_py_fsm.py       # python-statemachine comparison (549 lines)
│   ├── benchmark_transitions_fsm.py  # transitions lib comparison (663 lines)
│   ├── benchmark.py              # Unified comparison runner (600 lines)
│   └── performance_demo.py       # Performance demo script (283 lines)
├── docs/                          # Sphinx documentation source
│   ├── conf.py                   # Sphinx configuration
│   ├── index.rst                 # Root toctree
│   ├── QUICK_START.md            # Getting Started guide
│   ├── TUTORIAL.md               # Tutorial
│   ├── FSM_LINKING_TECHNIQUES.md # Multi-FSM patterns (User Guide)
│   ├── Makefile / make.bat       # Sphinx build scripts
│   ├── api/                      # Autodoc API stubs
│   │   ├── core.md
│   │   ├── conditions.md
│   │   ├── validation.md
│   │   └── visualization.md
│   ├── dev/                      # Developer guide
│   │   ├── architecture.md
│   │   ├── contributing.md
│   │   └── testing.md
│   └── examples/                 # Examples gallery
│       └── index.md
├── .specify/                     # Project memory & decisions
│   ├── memory/                   # SPR files (AI-optimized knowledge)
│   │   ├── spr-core-api.md
│   │   ├── spr-validation.md
│   │   └── spr-visualization.md
│   └── decisions/                # Architecture Decision Records
│       ├── ADR-001-sparse-dense-scoring.md
│       ├── ADR-002-trigger-result-not-exception.md
│       └── ADR-003-mypyc-compilation-boundary.md
├── .github/
│   └── copilot-instructions.md   # Copilot coding conventions
├── pyproject.toml                # Project metadata + tool config
├── setup.py                      # mypyc ext_modules only
├── Taskfile.yml                  # Task runner commands
├── AGENTS.md                     # Agent instructions reference
├── CHANGELOG.md                  # Release changelog
└── README.md                     # Project documentation
```

## Key Locations

| What you're looking for             | Where to find it                            |
|--------------------------------------|---------------------------------------------|
| Public API                          | `src/fast_fsm/__init__.py`                  |
| StateMachine class                  | `src/fast_fsm/core.py` (line 238)           |
| AsyncStateMachine class             | `src/fast_fsm/core.py` (line 1483)          |
| FSMBuilder class                    | `src/fast_fsm/core.py` (line 2036)          |
| Condition ABC                       | `src/fast_fsm/conditions.py` (line 15)      |
| Condition templates                 | `src/fast_fsm/condition_templates.py`       |
| Validation / scoring                | `src/fast_fsm/validation.py`                |
| Mermaid visualization               | `src/fast_fsm/visualization.py`             |
| Project dependencies                | `pyproject.toml`                            |
| mypyc build config                  | `setup.py`                                  |
| Task runner commands                | `Taskfile.yml`                              |
| Test configuration                  | `pyproject.toml` `[tool.pytest.ini_options]` |
| Ruff config                         | `pyproject.toml` (inherited defaults)       |
| ADRs                                | `.specify/decisions/ADR-*.md`               |
| SPR memory files                    | `.specify/memory/spr-*.md`                  |
| Copilot conventions                 | `.github/copilot-instructions.md`           |

## Naming Conventions

### Files
- **Source modules:** lowercase, snake_case (`condition_templates.py`)
- **Test files:** `test_<description>.py` (pytest discovery pattern)
- **Example scripts:** descriptive snake_case (`order_processing.py`)
- **Documentation:** UPPER_CASE.md for guides, lowercase for API stubs

### Classes
- PascalCase: `StateMachine`, `CallbackState`, `FSMBuilder`, `TransitionResult`
- Condition subclasses suffix with `Condition`: `AlwaysCondition`, `RegexCondition`
- Validator suffix with `Validator`: `FSMValidator`, `EnhancedFSMValidator`

### Methods & Functions
- snake_case for all methods and functions
- Private methods prefixed with `_`: `_resolve_trigger()`, `_execute_transition()`
- Factory classmethods: `from_states()`, `from_dict()`, `quick_build()`
- Convenience module-level: `simple_fsm()`, `quick_fsm()`, `condition_builder()`

### Constants
- No module-level constants (library values are instance-bound)
- Logging level presets: string keys (`"quiet"`, `"detailed"`, `"ultra"`)

## Source File Sizes (by lines)

| File                      | Lines | Role                              |
|---------------------------|-------|-----------------------------------|
| `core.py`                 | 2,626 | Core FSM runtime (largest module) |
| `validation.py`           | 1,313 | Design-time validation & scoring  |
| `condition_templates.py`  |   232 | Reusable condition patterns       |
| `visualization.py`        |   225 | Mermaid diagram generation        |
| `conditions.py`           |   158 | Condition ABC hierarchy           |
| `__init__.py`             |    89 | Public API re-exports             |
| **Total source**          | **4,643** |                              |
| **Total tests**           | **8,778** | 16 test files                |
| **Total examples**        | **1,202** | 6 example scripts            |
| **Total benchmarks**      | **3,178** | 6 benchmark scripts          |
