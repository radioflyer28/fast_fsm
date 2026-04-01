# Testing

## Framework & Configuration

| Property          | Value                                               |
|-------------------|-----------------------------------------------------|
| Framework         | pytest (>=8.4.1)                                    |
| Async support     | pytest-asyncio (>=1.3.0, auto mode)                 |
| Coverage          | pytest-cov (>=6.2.1)                                |
| Property testing  | hypothesis (>=6.136.6)                              |
| Test location     | `tests/` directory                                  |
| Config            | `pyproject.toml` `[tool.pytest.ini_options]`        |
| Default options   | `-x -q --tb=short --strict-markers`                 |
| Run command       | `uv run pytest tests/ -x -q` (or `task test`)      |
| Baseline          | 290 passed, 0 failures                              |

## Test Organization

16 test files organized by feature area:

| Test file                          | Lines | Coverage area                        |
|------------------------------------|-------|--------------------------------------|
| `test_advanced_functionality.py`   | 1,736 | Advanced transitions, callbacks, clone, from_dict |
| `test_builder.py`                  |   977 | FSMBuilder fluent API                |
| `test_validation.py`              | 1,041 | FSMValidator, EnhancedFSMValidator, scoring |
| `test_safety_kwargs.py`           |   579 | *args/**kwargs forwarding integrity  |
| `test_async.py`                   |   568 | AsyncStateMachine, async conditions  |
| `test_condition_templates.py`     |   551 | All condition template classes       |
| `test_basic_functionality.py`     |   501 | Core FSM operations                  |
| `test_readme_examples.py`         |   460 | README code examples (golden tests)  |
| `test_listeners.py`               |   456 | Listener/observer pattern            |
| `test_performance_benchmarks.py`  |   449 | Performance threshold verification   |
| `test_boundary_negative.py`       |   377 | Edge cases and error paths           |
| `test_visualization.py`           |   327 | Mermaid diagram generation           |
| `test_state_machine_utils.py`     |   296 | Utility methods (snapshot, clone, etc.) |
| `test_hypothesis.py`              |   188 | Property-based invariant testing     |
| `test_mypyc_guard.py`            |   168 | mypyc subclassing safety             |
| `test_logging_config.py`         |   104 | Logging configuration                |

## Test Style & Patterns

### No Mocking
All tests use **real FSM components** — no mocking frameworks. Tests exercise actual
`StateMachine`, `State`, `Condition` objects. This is a deliberate design choice for
a library with no external dependencies to mock.

### Test Class Organization
Tests are grouped by feature in classes with the `Test` prefix:
```python
class TestBasicFunctionality:
    def test_state_creation(self): ...
    def test_simple_transition(self): ...

class TestAdvancedTransitions:
    def test_conditional_transition(self): ...
```

### Helper Patterns
Test files define module-level helpers for common FSM construction:
```python
def _make_fsm():
    """Simple 2-state FSM: idle -[start]-> running -[stop]-> idle."""
    return StateMachine.quick_build(
        "idle",
        [("start", "idle", "running"), ("stop", "running", "idle")],
        name="Test",
    )
```

### Recorder/Tracker Pattern
State tracking uses lightweight listener objects:
```python
class _Recorder:
    def __init__(self):
        self.exits = []
        self.enters = []
        self.afters = []

    def on_exit_state(self, source, target, trigger, **kwargs):
        self.exits.append((source.name, target.name, trigger))
```

## Test Markers

| Marker         | Purpose                                    |
|----------------|--------------------------------------------|
| `@pytest.mark.slow` | Long-running benchmarks (skip with `-m "not slow"`) |
| `@pytest.mark.integration` | Integration tests                |
| `@pytest.mark.unit` | Unit tests                               |

## Incremental Testing Strategy

| Source file changed          | Primary test files to run                      |
|------------------------------|-------------------------------------------------|
| `core.py` (StateMachine)    | `test_basic_functionality.py`, `test_advanced_functionality.py`, `test_boundary_negative.py`, `test_state_machine_utils.py`, `test_listeners.py` |
| `core.py` (FSMBuilder)      | `test_builder.py`                               |
| `core.py` (AsyncStateMachine)| `test_async.py`                                |
| `core.py` (logging)         | `test_logging_config.py`                        |
| `validation.py`             | `test_validation.py`                            |
| `conditions.py`             | `test_safety_kwargs.py`, `test_async.py`        |
| `condition_templates.py`    | `test_condition_templates.py`, `test_safety_kwargs.py` |
| README / examples           | `test_readme_examples.py`                       |
| Performance-sensitive        | `test_performance_benchmarks.py`                |
| Cross-cutting invariants    | `test_hypothesis.py`                            |
| mypyc subclassing           | `test_mypyc_guard.py`                           |

## Property-Based Testing (Hypothesis)

`test_hypothesis.py` uses Hypothesis strategies to generate random FSM topologies and
verify structural invariants:

- **Strategies:** Random state names, random transition lists, composite FSM builder
- **Invariants tested:**
  - Current state is always a registered state
  - Trigger from unknown state returns failure
  - All registered states appear in `fsm.states`
  - Snapshot/restore round-trip preserves state
- **Settings:** Suppresses `HealthCheck.too_slow` for generated FSMs

## Performance Verification Tests

`test_performance_benchmarks.py` (marked `@pytest.mark.slow`):
- Benchmarks basic state transition throughput
- Validates ≥200,000 ops/sec threshold
- Tests memory efficiency via `__slots__` verification
- Measures condition evaluation overhead
- Tests FSM creation speed for large state counts

## Async Testing

- `asyncio_mode = "auto"` in pytest config — async tests run without explicit markers
- `test_async.py` covers `AsyncStateMachine.trigger_async()`, async conditions,
  async callbacks, async listener integration
- Uses `asyncio.sleep()` for realistic async condition simulation

## Parallel Execution

**Not supported.** Tests run sequentially. This is a deliberate choice — some tests
modify shared logging state or measure timing-sensitive performance thresholds.
