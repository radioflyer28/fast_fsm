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

Fast FSM maintains a durable baseline of **700+ tests**. The full suite is the
merge gate:

```bash
uv run pytest tests/ -x -q
```

Exact test counts, coverage, toolchain versions, source origin, artifact mode,
and collected environment-labeled trigger-throughput observations belong only in the tracked
[`evidence/release-baseline.json`](../../evidence/release-baseline.json)
manifest. Do not copy those changing observations into narrative documentation.

## Release Evidence Workflow

The checked-in manifest is produced from a clean pure-Python source collection.
The Taskfile is the canonical interface:

```bash
# Confirm that imports resolve to pure Python and fail on native source shadows.
task pure-source-check

# Intentionally regenerate the tracked evidence after a reviewed change.
task release-baseline-write

# Read-only freshness and regression check (the command CI runs).
task release-baseline-check
```

Use `FAST_FSM_BUILD_MODE=auto`, `pure`, or `compiled` to make a build intent
explicit. `FAST_FSM_PURE_PYTHON=1` remains a compatible alias for pure mode.
Before collecting evidence, select pure mode, run the source preflight, and
only then run the write command. Review a generated manifest diff before
committing it. CI runs the read-only check and never writes the baseline.

The source preflight is deliberately non-destructive: it reports a native
extension shadow before importing and leaves every file untouched. If a stale
artifact is intentional to remove, first review the exact reported path and
then explicitly remove only that artifact; rerun `task pure-source-check` to
prove the cleanup. Never use broad cleanup commands for this procedure.

## Type-Checking Authority

`task typecheck-mypy` is the blocking compatibility authority, including the
mypyc boundary. `task typecheck-ty` is separate advisory feedback: keep it
visible and address useful findings, but do not treat it as the release-gate
verdict.

## Measured Slots Policy

The canonical policy command recursively discovers every relevant production
class below `src/fast_fsm` and fails if an unregistered or omitted exception
would escape the audit:

```bash
uv run python tools/release_evidence.py slots-policy --json
```

Hot-path classes use `__slots__`. Two measured exceptions are deliberately
registered: `CompiledFuncCondition` uses `@mypyc_attr(native_class=False)` to
preserve the interpreted `Condition` subclass boundary, while `TransitionError`
uses it to preserve ordinary Python exception behavior. Both can therefore have
an instance `__dict__`; their environment-labeled measurements live in the
evidence manifest rather than this guide. This is the measured exception policy
recorded by ADR-003, not a relaxation of the general hot-path rule.
