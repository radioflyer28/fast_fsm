# Phase 1: Quick Wins — Plan

**Created:** 2026-04-04
**Requirements:** VERSION-01, IMPORTS-01

## Plan 1: Version Sync + Import Fix

### Tasks

#### Task 1: Replace hardcoded `__version__` with `importlib.metadata`
- **File:** `src/fast_fsm/__init__.py`
- **Change:** Replace `__version__ = "0.1.0"` with dynamic `importlib.metadata.version("fast_fsm")` with fallback
- **Verification:** `uv run python -c "import fast_fsm; print(fast_fsm.__version__)"` returns current version

#### Task 2: Fix absolute import in `condition_templates.py`
- **File:** `src/fast_fsm/condition_templates.py`
- **Change:** `from fast_fsm import Condition` → `from .conditions import Condition`
- **Verification:** `uv run python -c "from fast_fsm.condition_templates import AlwaysCondition; print('OK')"`

#### Task 3: Run tests
- **Command:** `uv run pytest tests/ -x -q`
- **Verification:** All tests pass

## Success Criteria
1. `fast_fsm.__version__` matches `pyproject.toml` version
2. `condition_templates.py` uses relative import
3. Full test suite passes
