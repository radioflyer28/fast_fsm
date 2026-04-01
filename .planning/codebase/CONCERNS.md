# Concerns

## Version Mismatch

**Severity: Medium**

`pyproject.toml` declares `version = "0.2.0"` but `src/fast_fsm/__init__.py` has
`__version__ = "0.1.0"`. These should be synchronized. Users who check
`fast_fsm.__version__` at runtime will see a stale version.

- `pyproject.toml` line 3: `version = "0.2.0"`
- `src/fast_fsm/__init__.py` line 45: `__version__ = "0.1.0"`

## `core.py` Module Size (2,626 lines)

**Severity: Low (informational)**

`core.py` contains the entire FSM runtime: `State`, `CallbackState`, `StateMachine`,
`AsyncStateMachine`, `DeclarativeState`, `AsyncDeclarativeState`, `FSMBuilder`,
`TransitionResult`, `TransitionEntry`, `TransitionError`, `CompiledFuncCondition`,
plus helper functions (`configure_fsm_logging`, `simple_fsm`, `quick_fsm`,
`condition_builder`).

This is a deliberate design choice — keeping everything in one file keeps the mypyc
compilation unit simple (only `core.py` is compiled). However, the file is large enough
that navigation requires IDE symbol search.

**Not a blocker** — the module is well-organized with clear class boundaries.

## Broad Exception Handling (16 bare `except Exception` catches)

**Severity: Low**

`core.py` has 16 `except Exception as e` catches, all in callback/listener execution
paths (`_execute_transition`, `trigger`, `safe_trigger`, etc.). These deliberately
catch all exceptions from user-provided callbacks and log them as warnings, preventing
user code from crashing the FSM.

This is an intentional design decision (documented in conventions), but it means:
- Bugs in user callbacks are silently swallowed (only logged)
- `safe_trigger()` catches exceptions at an even broader level

Users who want strict error propagation should check logs or use `trigger()` with
explicit error handling in their callbacks.

## No CI/CD Pipeline

**Severity: Medium**

No GitHub Actions, CircleCI, or other CI configuration was found. Quality gates
(tests, linting, type checking) are run locally via `Taskfile.yml`. This means:
- No automated verification on push/PR
- No build matrix for multiple Python versions
- No automated benchmark regression detection

## No `py.typed` Marker

**Severity: Low**

The package does not include a `py.typed` marker file in `src/fast_fsm/`. PEP 561
recommends this for packages that provide inline type annotations, so that type
checkers (mypy, pyright) recognize the package as typed.

## `condition_templates.py` Import Style

**Severity: Low (minor inconsistency)**

`condition_templates.py` imports `Condition` via `from fast_fsm import Condition`
(through `__init__.py`), while all other modules use relative imports
(`from .conditions import Condition`). This works but creates a subtle dependency
on the package being installed/importable.

## Security Considerations

**No concerns identified.** The library:
- Has no network I/O, no file I/O, no database access
- Processes no user input beyond Python function arguments
- Has a single dependency (`mypy-extensions`) with minimal attack surface
- Does not execute arbitrary code (conditions are user-provided callables, but this
  is by design — users control what gets executed)

## Performance Fragility

**Severity: Low**

Performance claims (≥200,000 ops/sec, 5-20× faster than alternatives) are verified
by `test_performance_benchmarks.py` (marked `@pytest.mark.slow`). However:
- Benchmarks are timing-sensitive and may fail on slow machines or under load
- No automated benchmark regression tracking (runs are manual)
- mypyc compilation is optional — pure Python fallback is slower but functional

## `State` is an ABC but Instantiable

**Severity: Low (design quirk)**

`State` is declared as `ABC` (inherits from `abc.ABC`) but has no abstract methods
(the base implementations are all no-ops). This means `State` can be instantiated
directly despite being "abstract." The ABC inheritance is used to signal intent
(users should consider subclassing) rather than to enforce it.

## Potential Future Concerns

- **mypyc upgrade risk:** The library depends on mypyc's `@mypyc_attr(native_class=False)`
  behavior. Changes to mypyc internals could break the compilation boundary.
- **Hypothesis test flakiness:** Property-based tests with generated FSM topologies
  occasionally produce edge cases that are timing-sensitive.
- **Large test-to-source ratio:** 8,778 lines of tests vs 4,643 lines of source
  (1.9:1 ratio). This is generally positive but means test maintenance cost is
  significant for any refactor.
