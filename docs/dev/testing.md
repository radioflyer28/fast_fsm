# Testing

## Quick Reference

```bash
# Full test suite (merge gate)
uv run pytest tests/ -x -q

# Single test file
uv run pytest tests/test_basic_functionality.py -x -q

# Run by marker
uv run pytest -m "unit" -v
uv run pytest -m "not slow" -v

# Performance benchmarks
uv run python benchmarks/benchmark_fast_fsm.py
```

## Test Files

```text
tests/
├── test_basic_functionality.py     # Core FSM: states, transitions, errors
├── test_advanced_functionality.py  # Builder, callbacks, introspection
├── test_safety_kwargs.py           # Kwargs sanitization, exception handling
├── test_validation.py              # Validation module: validators, scoring, export
├── test_performance_benchmarks.py  # Throughput and memory thresholds
└── test_readme_examples.py         # Verify README code samples work
```

## Source → Test Mapping

When you change a source file, run the corresponding tests first (Tier 1),
then the full suite once before merge.

| Source file changed | Primary test files |
|---------------------|-------------------|
| `core.py` | `test_basic_functionality.py`, `test_advanced_functionality.py` |
| `validation.py` | `test_validation.py` |
| `conditions.py` | `test_safety_kwargs.py` |
| `condition_templates.py` | `test_safety_kwargs.py` |
| README / examples | `test_readme_examples.py` |
| Performance-sensitive | `test_performance_benchmarks.py` |

## Test Markers

Defined in `pytest.ini`:

| Marker | Meaning |
|--------|---------|
| `@pytest.mark.unit` | Fast, isolated unit tests |
| `@pytest.mark.integration` | May be slower, tests component interaction |
| `@pytest.mark.slow` | Skip with `-m "not slow"` for fast iteration |

## Writing Tests

### Guidelines

1. **Use composition, not inheritance.** Do not subclass `StateMachine` or
   `State` in tests — create instances and call methods. This is required
   for compatibility with the mypyc-compiled build (compiled classes cannot
   be subclassed from interpreted Python).
2. **No logic mocking.** Never mock `trigger()`, `check()`, or state
   callbacks. Mock the *environment* (clock, RNG, I/O), not the logic
   being tested.
3. **Every bug fix needs a regression test.** The test must fail before the
   fix and pass after.
4. **Use tolerances for timing-sensitive tests.** Statistical or
   performance assertions must be wide enough to avoid flakiness across
   hardware.
5. **Hypothesis is encouraged** for combinatorial state-space exploration.

### Example

```python
import pytest
from fast_fsm import State, StateMachine, CallbackState

class TestTrafficLight:
    """Test a simple traffic light FSM."""

    def test_basic_cycle(self):
        red = State("red")
        yellow = State("yellow")
        green = State("green")

        fsm = StateMachine("traffic", initial_state=red)
        fsm.add_state(yellow)
        fsm.add_state(green)
        fsm.add_transition("next", "red", "green")
        fsm.add_transition("next", "green", "yellow")
        fsm.add_transition("next", "yellow", "red")

        assert fsm.current_state.name == "red"
        fsm.trigger("next")
        assert fsm.current_state.name == "green"
```

## Performance Benchmarks

The benchmark suite verifies Fast FSM meets its performance thresholds:

```bash
uv run python benchmarks/benchmark_fast_fsm.py
```

| Metric | Threshold |
|--------|-----------|
| `trigger()` throughput | ≥ 200,000 ops/sec |
| `can_trigger()` throughput | ≥ 400,000 ops/sec |
| Base FSM memory | ≤ 0.5 KB |

Benchmark results are hardware-dependent. Do not commit results as
"official" without noting the hardware/OS context.

## Baseline

- **62 tests passing** on `main`
- **0 failures** expected
- Full suite is the merge gate: `uv run pytest tests/ -x -q`
