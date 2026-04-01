# Integrations

## External API Integrations

**None.** Fast FSM is a self-contained library with no external API calls, network
dependencies, database connections, or auth providers. It is a pure computational
library for finite state machine logic.

## Internal Integration Points

### mypyc Compilation Boundary

The most significant integration boundary is between **compiled** and **uncompiled** code:

| Module                  | Compiled? | Why                                          |
|-------------------------|-----------|----------------------------------------------|
| `core.py`               | Yes       | Hot path — StateMachine, trigger(), State     |
| `conditions.py`         | No        | Users subclass Condition from interpreted code|
| `condition_templates.py`| No        | Inherits from Condition (same reason)         |
| `validation.py`         | No        | Design-time only — no runtime overhead needed |
| `visualization.py`      | No        | Output generation only — not performance-critical |

**Critical constraint:** mypyc-compiled classes cannot be subclassed from interpreted
Python. This is why `conditions.py` must stay uncompiled.

### Cross-Module Dependencies

```
__init__.py
    ├── core.py ─────────────── imports from conditions.py (Condition, FuncCondition, AsyncCondition, NegatedCondition)
    ├── conditions.py ────────── standalone (no fast_fsm imports)
    ├── condition_templates.py ─ imports from fast_fsm (via __init__.py — uses Condition)
    ├── validation.py ────────── imports from core.py (StateMachine)
    └── visualization.py ─────── imports from core.py (StateMachine, TYPE_CHECKING only)
```

### Logging Integration

- Uses Python's standard `logging` module (no third-party logging)
- Logger per FSM instance: `fast_fsm.{name}`
- Configurable via `configure_fsm_logging()` and `set_fsm_logging_level()`
- Custom ultra-verbose level at `logging.DEBUG - 5` (level 5)
- Level presets: `"quiet"`, `"normal"`, `"verbose"`, `"detailed"`, `"ultra"`

### Testing Framework Integration

- **pytest** with `pytest-asyncio` (auto mode) for async test support
- **hypothesis** for property-based/fuzz testing of FSM invariants
- No mocking frameworks used — tests use real FSM components exclusively

### Documentation Integration

- **Sphinx** with `myst-parser` for Markdown sources
- `sphinx.ext.autodoc` for API docs from docstrings (Google-style via napoleon)
- `sphinx.ext.doctest` for testable code examples in docs
- `sphinx-autodoc-typehints` for type annotation rendering
- `furo` theme

### Benchmark Comparisons

The benchmarks suite compares Fast FSM against two competitor libraries:
- `python-statemachine` (>=2.5.0) — benchmarked in `benchmarks/benchmark_py_fsm.py`
- `transitions` (>=0.9.3) — benchmarked in `benchmarks/benchmark_transitions_fsm.py`
- Unified comparison: `benchmarks/benchmark.py`

## Webhooks / Event Systems

**None external.** However, Fast FSM provides an internal listener/observer pattern:
- `StateMachine.add_listener()` — register objects with `on_enter_state()`, `on_exit_state()`, `after_transition()` methods
- `StateMachine.on_enter()` / `StateMachine.on_exit()` — per-state callback registration
- `AsyncStateMachine.on_enter_async()` / `on_exit_async()` — async callback variants

These are internal extension points, not external integrations.

## CI/CD

No CI/CD configuration files were found in the repository (no `.github/workflows/`,
no `Makefile` for CI). Quality gates are run locally via `Taskfile.yml` commands.
