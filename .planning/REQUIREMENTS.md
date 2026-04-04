# Requirements: Fast FSM v0.2.1

**Defined:** 2026-04-04
**Core Value:** Blazing-fast, zero-overhead FSM transitions — `trigger()` ≥200,000 ops/sec, all core ops O(1).

## v0.2.1 Requirements

All items below are maintenance/quality — no new public API.

### Version Hygiene

- [ ] **VERSION-01**: `__version__` in `__init__.py` is derived from `pyproject.toml` at import time (via `importlib.metadata`) so the two can never drift

### Exception Handling

- [ ] **EXCEPT-01**: Every `except Exception` catch in `core.py` has an inline comment explaining why the broad catch is intentional (callback isolation vs. incorrect broad catch)
- [ ] **EXCEPT-02**: Any `except Exception` in construction or validation paths (not callback execution) narrowed to specific exception types where appropriate
- [ ] **EXCEPT-03**: `safe_trigger()` vs `trigger()` exception semantics are clearly documented in the `safe_trigger()` docstring

### Type Annotations

- [ ] **TYPES-01**: `py.typed` marker file (empty) present at `src/fast_fsm/py.typed`
- [ ] **TYPES-02**: Package is recognized as typed by mypy/pyright after `pip install` without breaking pure-Python fallback (`FAST_FSM_PURE_PYTHON=1`)

### Import Consistency

- [ ] **IMPORTS-01**: `condition_templates.py` imports `Condition` via `from .conditions import Condition` (relative) instead of `from fast_fsm import Condition` (absolute)

### State API Cleanup

- [ ] **STATE-01**: `State` class no longer inherits from `abc.ABC` — direct instantiation is the primary usage pattern and `ABC` provided no enforcement
- [ ] **STATE-02**: All existing `State` subclasses and direct instantiation (`State("name")`) continue to work identically after the change; test suite passes with zero changes to test code

### Test Suite

- [ ] **TESTS-01**: Written audit of the test suite identifying: (a) redundant tests that overlap another test's coverage, (b) over-specified tests that test implementation details rather than behaviour, (c) low-value tests that provide little signal (trivial assertions, copy-paste variants)
- [ ] **TESTS-02**: Confirmed-redundant and low-value tests removed or consolidated; total test count reduced without losing meaningful behavioural coverage
- [ ] **TESTS-03**: Any meaningful coverage gaps identified and recorded (in CONCERNS.md or inline) — filling gaps is deferred to v0.2.2

### CI / Benchmarks

- [ ] **CI-01**: A dedicated `benchmark` job in `ci.yml` runs `@pytest.mark.slow` performance tests on every push to `main`
- [ ] **CI-02**: The benchmark job asserts a minimum threshold (≥200,000 ops/sec for `trigger()`) so performance regressions fail the build

## Future Requirements (deferred)

### Test Coverage Gaps
- Fill any coverage gaps identified by TESTS-03 (v0.2.2)

### Exception Handling — Strict Mode
- Opt-in `strict=True` on `StateMachine.__init__` that re-raises callback exceptions instead of swallowing (future API addition, not this maintenance milestone)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Refactoring `core.py` into mixins or sub-modules | mypyc single-file compilation is a hard constraint |
| New public API | Maintenance milestone — API freeze |
| Filling test coverage gaps | Audit only; filling is v0.2.2 |
| Competitor benchmark comparison in CI | Too slow for CI; manual via `task benchmark` |
| `State` adding actual `@abstractmethod` | Direct instantiation is the primary usage pattern — enforcement would be a breaking change |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| VERSION-01  | Phase 1 | Pending |
| IMPORTS-01  | Phase 1 | Pending |
| STATE-01    | Phase 2 | Pending |
| STATE-02    | Phase 2 | Pending |
| EXCEPT-01   | Phase 3 | Pending |
| EXCEPT-02   | Phase 3 | Pending |
| EXCEPT-03   | Phase 3 | Pending |
| TYPES-01    | Phase 4 | Pending |
| TYPES-02    | Phase 4 | Pending |
| TESTS-01    | Phase 5 | Pending |
| TESTS-02    | Phase 5 | Pending |
| TESTS-03    | Phase 5 | Pending |
| CI-01       | Phase 6 | Pending |
| CI-02       | Phase 6 | Pending |

**Coverage:**
- v0.2.1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-04*
*Last updated: 2026-04-04 after v0.2.1 initialization*
