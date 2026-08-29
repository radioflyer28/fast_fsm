<!-- refreshed: 2026-08-29 -->
# Testing Patterns

**Analysis Date:** 2026-08-29

**Assessment Basis:** Independent test inventory plus executed pytest, coverage,
Ruff, ty, Sphinx HTML, and Sphinx doctest commands against the live checkout.

## Test Framework

**Runner:**
- `pytest` `>=8.4.1`, configured in `pyproject.toml` under `[tool.pytest.ini_options]`.
- Async support comes from `pytest-asyncio` `>=1.3.0`; `asyncio_mode = "auto"` is configured in `pyproject.toml`.
- Property-based tests use Hypothesis `>=6.136.6` in `tests/test_hypothesis.py`.

**Assertion Library:**
- Use native Python `assert` statements for values and state changes.
- Use `pytest.raises(..., match=...)` for expected exception types/messages, `pytest.approx` for numeric tolerances, and `caplog`/`capsys` for logging and console output.

**Run Commands:**
```bash
uv run pytest tests/ -x -q                 # Full merge-gate suite
uv run pytest tests/test_builder.py -x -q  # Targeted file during development
uv run pytest tests/ -v --tb=short         # Verbose diagnostics
uv run pytest tests/ -x -q -m "not slow and not integration"  # Fast subset
uv run pytest tests/ --cov=src/fast_fsm --cov-report=html --cov-report=term  # Coverage
task test                                  # Pure-Python full suite wrapper
task test-coverage                          # HTML + terminal coverage wrapper
```

The repository sets `FAST_FSM_PURE_PYTHON=1` in the `test` Taskfile task and in
fresh CI environments to prevent extension compilation. That variable does not
change Python's import precedence: an already-built `.so`/`.pyd` beside
`core.py` still loads. The 2026-08-29 local run collected and passed 722 tests,
but it loaded `src/fast_fsm/core.cpython-312-darwin.so`; it is therefore a
compiled-core run, not proof of a clean local pure-Python run.

## Verified Gate Snapshot

| Check | Result | Evidence |
|-------|--------|----------|
| Full pytest suite | PASS | 722 collected, 722 passed in 3.34s with coverage enabled |
| `ty check src/fast_fsm/` | PASS | All checks passed; tool emitted its pre-release warning |
| Ruff format check | FAIL | `src/fast_fsm/visualization.py` would be reformatted |
| Ruff lint | FAIL | F841 at `tests/test_advanced_functionality.py:1488` |
| Sphinx HTML with `-W` | PASS | Build completed without warnings |
| Sphinx doctest | PASS | 1 doctest passed |

This means tests are green while the repository's combined quality gate is not.
The README contains both 290- and 653-test claims, and
`.github/copilot-instructions.md` still cites a 290-test baseline; the actual
collected baseline is 722.

## Test File Organization

**Location:**
- Tests are separate from implementation in the flat `tests/` directory; there is no `tests/conftest.py` and no nested unit/integration directory.
- The suite currently has 16 modules covering core behavior, async behavior, conditions, validation, visualization, logging, performance, examples, and compilation safety. Source-to-test mappings are documented in `.github/copilot-instructions.md` and `docs/dev/testing.md`.

**Naming:**
- Name modules `test_<feature>.py`, classes `Test<Feature>`, and methods `test_<behavior>()`; this matches the discovery settings in `pyproject.toml`.
- Name fixtures after the reusable object/scenario they create (`traffic_light_fsm`, `well_designed_fsm`, `two_state_async_fsm`).

**Structure:**
```text
tests/
├── test_basic_functionality.py       # states, transitions, basic failures
├── test_advanced_functionality.py    # callbacks, history, snapshots, cloning
├── test_async.py                     # async machines, conditions, callbacks
├── test_builder.py                   # builder/declarative APIs
├── test_condition_templates.py       # reusable guards and unless shorthand
├── test_validation.py                # validators, scores, reports, exports
├── test_visualization.py             # Mermaid, PlantUML, JSON output
├── test_hypothesis.py                # generated FSM invariants
├── test_performance_benchmarks.py    # throughput/memory/stress checks
├── test_mypyc_guard.py               # static compilation-boundary checks
└── test_*.py                         # boundary, listeners, logging, examples
```

## Test Structure

**Suite Organization:**
```python
@pytest.fixture
def traffic_light_fsm():
    return StateMachine.quick_build(
        "red",
        [("timer", "red", "green"), ("timer", "green", "yellow")],
        name="TrafficLight",
    )


class TestProperties:
    def test_current_state_name_updates_after_trigger(self, traffic_light_fsm):
        traffic_light_fsm.trigger("timer")
        assert traffic_light_fsm.current_state_name == "green"
```

This pattern appears in `tests/test_state_machine_utils.py` and `tests/test_visualization.py`: define scenario fixtures/helpers near the top, group behavior in `Test*` classes, execute a real FSM, and assert observable state/result data.

**Patterns:**
- Prefer real `State`, `StateMachine`, `Condition`, and builder objects. Several modules explicitly state “no mocking,” including `tests/test_basic_functionality.py`, `tests/test_boundary_negative.py`, `tests/test_builder.py`, `tests/test_hypothesis.py`, and `tests/test_listeners.py`.
- Keep tests behavior-focused and arrange them by feature sections with divider comments. Use helper builders such as `_make_fsm()` in `tests/test_listeners.py` for repeated topologies.
- Cover both success and failure paths, and assert that failed transitions preserve state. Negative/boundary coverage is concentrated in `tests/test_boundary_negative.py` and `tests/test_advanced_functionality.py`.
- Test public API behavior through `fast_fsm` imports where possible; use focused imports from `fast_fsm.core`, `fast_fsm.conditions`, or `fast_fsm.visualization` when the module itself is under test.

## Mocking

**Framework:**
- `pytest` fixtures/capture facilities are primary. `unittest.mock.Mock` appears only in `tests/test_safety_kwargs.py` for arbitrary environment/object kwargs; there is no `pytest-mock` dependency and no broad patching framework.

**Patterns:**
```python
condition = MockCondition()
fsm.add_transition("test_trigger", "initial", "target", condition)
result = fsm.trigger("test_trigger", object_arg={"key": "value"})
assert result.success
assert condition.received_kwargs["object_arg"] == {"key": "value"}
```

Use test-specific real condition classes (`MockCondition`, `ExceptionCondition`, `AlwaysTrueCondition`) when behavior needs call recording or controlled failure. Do not mock `trigger()`, `check()`, state callbacks, or other logic under test; this rule is reinforced in `docs/dev/testing.md` and `.specify/memory/constitution.md`.

**What to Mock:**
- Mock only external/environment-shaped values when necessary, such as an arbitrary aircraft object in `tests/test_safety_kwargs.py`. For logging, use `caplog`; for output, use `capsys`; for deterministic time-sensitive guards, set the condition’s reference fields as the existing tests do.

**What NOT to Mock:**
- Do not replace FSM dispatch, condition evaluation, callback execution, serialization, validation, or visualization logic with mocks. Exercise those paths with real objects and inspect their returned result/output.

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def well_designed_fsm():
    return StateMachine.quick_build(
        "idle",
        [
            ("start", "idle", "running"),
            ("stop", "running", "idle"),
            ("error", "running", "error"),
        ],
        name="GoodFSM",
    )
```

Fixtures are local to modules and commonly return a configured FSM or a tuple of FSM plus state objects, as in `tests/test_safety_kwargs.py` and `tests/test_async.py`. Reuse `StateMachine.quick_build()` for compact topologies; construct `State` objects directly when identity/callback behavior matters.

**Location:**
- Shared fixture infrastructure is not present; place a fixture beside the tests that use it. Reusable test-only condition classes and topology helpers are also defined at module scope in the relevant `tests/test_*.py` file.
- Hypothesis strategies live in `tests/test_hypothesis.py`; do not put generated-data helpers into production modules.

## Coverage

**Requirements:**
- No numeric coverage threshold is configured in `pyproject.toml` or Taskfile. Coverage is available as an inspection/reporting tool, not a merge threshold.
- The suite uses `# pragma: no cover` for abstract methods, demos, interactive/reporting branches, and defensive branches in `src/fast_fsm/conditions.py`, `src/fast_fsm/condition_templates.py`, and `src/fast_fsm/validation.py`.

**View Coverage:**
```bash
uv run pytest tests/ --cov=src/fast_fsm --cov-report=html --cov-report=term
task test-coverage
```

The HTML report is written to `htmlcov/`, which is ignored by `.gitignore`.

**Observed coverage caveat (2026-08-29):**
- The local report showed 44% total: `validation.py` 99%, `visualization.py`
  98%, `__init__.py` 80%, and the two condition modules fully covered.
- `core.py` appeared as 0/922 statements because tests executed the compiled
  extension while coverage measured `core.py`. This is a measurement artifact,
  not evidence that core behavior was untested, but it also means this run gives
  no line-level Python-core coverage assurance.
- Run `task clean` (or otherwise remove ignored extension artifacts) before a
  true pure-Python coverage run; separately run the compiled suite to assess the
  mypyc path. The CI compiled job currently performs only a smoke test plus the
  slow performance file, not the complete suite.

## Test Types

**Unit Tests:**
- Most tests are fast, isolated unit tests around public FSM operations and domain objects. `tests/test_basic_functionality.py`, `tests/test_boundary_negative.py`, `tests/test_condition_templates.py`, `tests/test_logging_config.py`, and `tests/test_state_machine_utils.py` are representative.
- Mark explicitly fast microbenchmarks with `@pytest.mark.unit` when they belong in the unit subset; `tests/test_performance_benchmarks.py` uses this for `TestMicroBenchmarks`.

**Integration Tests:**
- Mark multi-component/example scenarios with `@pytest.mark.integration`, including the performance examples in `tests/test_readme_examples.py` and advanced performance checks in `tests/test_performance_benchmarks.py`.
- The configured `-x -q` suite remains the merge gate; use `-m "not slow and not integration"` for fast iteration.

**E2E Tests:**
- Not used. There is no browser, service, or external-system E2E harness; `tests/test_readme_examples.py` validates runnable documentation scenarios in-process.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_trigger_async_success(self, two_state_async_fsm):
    fsm, _, _ = two_state_async_fsm
    fsm.add_transition("go", "idle", "running")
    result = await fsm.trigger_async("go")
    assert result.success
```

Use `@pytest.mark.asyncio` and `async def` for async machine/condition/callback tests in `tests/test_async.py`, `tests/test_builder.py`, and `tests/test_condition_templates.py`; rely on `asyncio_mode = "auto"` rather than manually creating event loops.

**Error Testing:**
```python
with pytest.raises(ValueError, match="Unsupported operator"):
    ComparisonCondition("age", "???", 18)

result = fsm.trigger("unknown")
assert not result.success
assert "No transition" in result.error
```

Use `pytest.raises` for invalid setup/API contracts and inspect failed `TransitionResult` objects for expected runtime failures. Use `caplog.at_level(...)` to verify intentional warning/error logging, as in `tests/test_safety_kwargs.py` and `tests/test_logging_config.py`.

**Property-Based Testing:**
- Define reusable Hypothesis strategies near the top of `tests/test_hypothesis.py` (`state_name`, `state_names`, and `fsm_with_transitions`).
- Decorate invariant tests with `@given(...)` and bound runtime with `@settings(max_examples=...)`; use `assume(...)` to discard invalid generated cases. Keep generated assertions about universal FSM invariants such as valid current states, deterministic outcomes, and failed-transition idempotence.

**Timing and Performance:**
- Use `time.perf_counter()` for benchmark elapsed time, warm up hot paths, call `gc.collect()` where memory/throughput measurements require it, and use generous hardware-tolerant thresholds. These patterns are in `tests/test_performance_benchmarks.py`.
- Avoid `sleep()` in guard tests. `tests/test_condition_templates.py` adjusts monotonic reference fields to simulate elapsed time deterministically.

**Confirmed Missing Edge Coverage:**
- No test rejects or defines `enable_history(0)`, which currently raises
  `IndexError` on the next successful transition.
- No parity test covers positional context through guards or private/oversized
  kwargs through async guards.
- No integration test proves that `@transition` handlers execute during normal
  `StateMachine.trigger()`; they currently do not.
- No invariant test covers unknown source states, unregistered object targets,
  or duplicate state-name replacement.
- Cycle tests check only `has_cycles`; they do not require every state in a
  multi-node cycle to appear in `states_in_cycles`.
- Validation comparison tests do not cover zero inputs or duplicate FSM names.
- No release-consistency test reconciles `pyproject.toml`, `__version__`,
  `CHANGELOG.md`, and `.planning/PROJECT.md`.

---

*Testing analysis: 2026-08-29*
