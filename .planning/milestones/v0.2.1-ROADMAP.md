# Roadmap: Fast FSM v0.2.1 Code Health & Quality

**Milestone:** v0.2.1
**Goal:** Resolve technical debt from codebase audit — version hygiene, exception handling, type annotations, import consistency, `State` ABC cleanup, test suite quality, benchmark CI.
**Phases:** 6
**Requirements coverage:** 14/14 ✓

---

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|-----------------|
| 1 | Quick Wins | Ship version sync + import fix | VERSION-01, IMPORTS-01 | `__version__` matches `pyproject.toml`; relative import works |
| 2 | State ABC Cleanup | Remove misleading `ABC` base | STATE-01, STATE-02 | `State` works identically; tests pass; no ABC in MRO |
| 3 | Exception Handling Audit | Document and tighten exception catches | EXCEPT-01, EXCEPT-02, EXCEPT-03 | All 16 catches annotated; construction-path catches narrowed |
| 4 | py.typed Marker | PEP 561 typed package declaration | TYPES-01, TYPES-02 | mypy/pyright recognize package as typed; pure-Python mode works |
| 5 | Test Suite Triage | Audit and prune the test suite | TESTS-01, TESTS-02, TESTS-03 | Written audit; dead tests removed; coverage does not decrease |
| 6 | Benchmark CI | Add performance regression gate to CI | CI-01, CI-02 | Slow benchmark job in CI passes; threshold assertion works |

---

## Phase Details

---

### Phase 1: Quick Wins

**Goal:** Ship the two lowest-risk, highest-value fixes — version sync automation and the import inconsistency in `condition_templates.py`.

**Requirements:** VERSION-01, IMPORTS-01

**Tasks:**
1. Replace hardcoded `__version__ = "0.1.0"` in `__init__.py` with `importlib.metadata.version("fast_fsm")` (fallback to `"unknown"` if package not installed)
2. Update `condition_templates.py` line 1: `from fast_fsm import Condition` → `from .conditions import Condition`
3. Verify CI passes (both changes are trivially safe)

**Success criteria:**
1. `import fast_fsm; fast_fsm.__version__` returns `"0.2.0"` (matches `pyproject.toml`)
2. Importing `from fast_fsm.condition_templates import AlwaysCondition` works when running from source without the package installed
3. Full test suite passes (`uv run pytest tests/ -x -q`)
4. `condition_templates.py` has no absolute `fast_fsm` imports

**Risks:** Low. `importlib.metadata` is stdlib ≥3.8. Fallback handles editable/source installs.

---

### Phase 2: State ABC Cleanup

**Goal:** Remove the misleading `ABC` base class from `State`. The class has no abstract methods; direct instantiation (`State("name")`) is the primary usage pattern throughout the library and tests.

**Requirements:** STATE-01, STATE-02

**Tasks:**
1. Remove `ABC` from `State`'s base classes in `core.py`
2. Remove `ABC` from the `abc` import if no longer used elsewhere in `core.py`
3. Run full test suite — zero tolerance for failures
4. Verify `State` is no longer in `ABCMeta` hierarchy (i.e., `type(State("x"))` is `State` not `ABCMeta`)
5. Check `test_mypyc_guard.py` — ensure no tests rely on `State` being an ABC

**Success criteria:**
1. `class State:` (no `ABC` base) in `core.py`
2. `isinstance(State("x"), ABC)` → `False`
3. Full test suite passes with **zero** changes to test code
4. `abc` import removed from `core.py` (or confirmed still needed for another class)
5. `CallbackState`, `DeclarativeState`, `AsyncDeclarativeState` subclassing still works

**Risks:** Low. Removing `ABC` from a class with no abstract methods has no behavioural effect — Python treats both identically at instantiation time. `@mypyc_attr(allow_interpreted_subclasses=True)` on `CallbackState` is unaffected.

---

### Phase 3: Exception Handling Audit

**Goal:** Make the exception handling posture explicit. Every `except Exception` catch should either be justified by a comment or narrowed to a more specific type.

**Requirements:** EXCEPT-01, EXCEPT-02, EXCEPT-03

**Tasks:**
1. Enumerate all 16 `except Exception` catches in `core.py` (run `grep -n "except Exception"`)
2. Categorize each into: (a) **callback isolation** — intentional broad catch to prevent user code crashing the FSM, (b) **construction/validation** — potentially too broad
3. For category (a): add inline comment `# broad catch intentional — isolates user callback exceptions from FSM control flow`
4. For category (b): narrow to specific exception types (`TypeError`, `ValueError`, etc.) where possible
5. Update `safe_trigger()` docstring to clearly explain: (a) it swallows `TransitionError`, (b) it does NOT swallow exceptions from conditions/callbacks (those are caught and logged earlier in `_execute_transition`)
6. Run full test suite after each narrowing to catch regressions

**Success criteria:**
1. Every `except Exception` in `core.py` has either: a justifying comment, or is replaced with a narrower exception type
2. `safe_trigger()` docstring explicitly documents what exceptions it catches vs. what propagates
3. Full test suite passes
4. `test_boundary_negative.py` and `test_listeners.py` still pass (error isolation tests)
5. No new `# type: ignore` or `# noqa` comments introduced

**Risks:** Medium. Narrowing catches in non-callback paths could expose exceptions that were previously swallowed silently. Each narrowing must be tested.

---

### Phase 4: py.typed Marker

**Goal:** Add PEP 561 `py.typed` marker so mypy, pyright, and other type checkers recognize Fast FSM as a typed package — without breaking the pure-Python fallback.

**Requirements:** TYPES-01, TYPES-02

**Tasks:**
1. Create empty `src/fast_fsm/py.typed` file
2. Verify `py.typed` is included in the installed package: check `pyproject.toml` `[tool.setuptools.packages.find]` and `[tool.setuptools.package-data]` — add `"fast_fsm": ["py.typed"]` if needed
3. Test with `FAST_FSM_PURE_PYTHON=1 pip install -e .` that the marker is present in the installed location
4. Run `uv run mypy --strict src/fast_fsm/` to confirm no new errors introduced by typed declaration
5. Verify `uv run ty check src/fast_fsm/` still passes
6. Check if `setup.py` needs updating (since it only handles `ext_modules`, likely no change needed)
7. Document in `CONCERNS.md` whether mypyc-compiled and pure-Python installs both correctly expose the typed marker

**Success criteria:**
1. `src/fast_fsm/py.typed` exists (empty file)
2. `fast_fsm-*.dist-info/RECORD` includes `fast_fsm/py.typed` after install
3. A test project with `import fast_fsm; reveal_type(fast_fsm.StateMachine)` resolves correctly under mypy
4. `FAST_FSM_PURE_PYTHON=1` install still works; no import errors
5. CI lint job passes unchanged

**Risks:** Low. `py.typed` is just an empty marker file. The only risk is forgetting to include it in the package manifest (step 2).

---

### Phase 5: Test Suite Triage

**Goal:** Honest audit of the test suite. Identify and remove tests that don't pull their weight — excessive copy-paste variants, implementation-detail tests, tests that duplicate another test's coverage 1:1.

**Requirements:** TESTS-01, TESTS-02, TESTS-03

**Tasks:**
1. **Audit pass** — Read all 16 test files (8,778 lines) and for each test, classify:
   - **Keep:** Tests a real behaviour, provides unique signal
   - **Redundant:** Another test covers the exact same path with the same assertions
   - **Over-specified:** Tests internal state or implementation details (e.g., `_transitions` dict structure) rather than observable behaviour
   - **Low-value:** Trivial assertions (e.g., `assert True`), zero-failure-mode tests, copy-paste variants with no variation in behaviour
2. Write audit findings to `.planning/TEST-AUDIT.md`
3. Remove or consolidate confirmed-redundant tests (get approval per batch if needed)
4. Run coverage report before and after: `uv run pytest tests/ --cov=src/fast_fsm --cov-report=term`
5. Document any coverage gaps found in `CONCERNS.md`

**Success criteria:**
1. `.planning/TEST-AUDIT.md` exists with per-file findings
2. Total test count reduced by at least 10% (starting baseline: 290 tests)
3. Code coverage does not decrease (measure with `--cov` before and after)
4. Test suite runtime improves or stays the same
5. Full test suite still passes at final count

**Risks:** Medium. Risk of accidentally removing tests that cover subtle edge cases. Mitigation: coverage diff before/after each removal batch; keep the "keep/redundant/low-value" classification conservative.

---

### Phase 6: Benchmark CI Job

**Goal:** Add a dedicated performance benchmark job to CI that runs on every push to `main` and fails if `trigger()` throughput drops below the documented 200,000 ops/sec threshold.

**Requirements:** CI-01, CI-02

**Tasks:**
1. Add `benchmark` job to `.github/workflows/ci.yml`:
   - Runs on `ubuntu-latest`, Python 3.12 only (single platform is sufficient for regression detection)
   - Triggers only on push to `main` (not PRs — too slow for review feedback)
   - Runs: `uv run pytest tests/test_performance_benchmarks.py -x -q` (these are already `@pytest.mark.slow`)
2. Ensure the existing `TestPerformanceBenchmarks` tests have an assertable threshold (currently they measure but may not assert a minimum — verify and add assertion if missing)
3. Add `if: github.ref == 'refs/heads/main'` condition to benchmark job
4. Verify the job completes in <5 minutes on ubuntu (check current benchmark runtime)
5. Add `benchmark` to the CI status badge in README.md if desired

**Success criteria:**
1. `ci.yml` has a `benchmark` job that runs `@pytest.mark.slow` tests
2. The job only runs on push to `main` (not PRs)
3. Intentionally degrading `trigger()` by 10× causes the benchmark job to fail
4. The benchmark job passes on the current codebase
5. CI status visible in repository

**Risks:** Low. Adding a new job does not affect existing jobs. The `@pytest.mark.slow` tests already exist and pass locally.

---

## Milestone Completion Criteria

All 14 requirements in REQUIREMENTS.md checked off AND:
- [ ] Full test suite passes on main branch
- [ ] CI green on all 6 jobs (lint, test matrix, docs, release, benchmark)
- [ ] CHANGELOG.md updated with v0.2.1 entry
- [ ] `pyproject.toml` version bumped to `0.2.1`
- [ ] Git tag `v0.2.1` created

---
*Roadmap created: 2026-04-04*
*Milestone: v0.2.1 Code Health & Quality*
