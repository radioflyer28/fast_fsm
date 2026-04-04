---
gsd_state_version: 1.0
milestone: v0.2.1
milestone_name: milestone
status: completed
last_updated: "2026-04-04T14:18:14.900Z"
last_activity: 2026-04-04
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 1
  completed_plans: 0
---

# State: Fast FSM

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: v0.2.1 milestone complete
Last activity: 2026-04-04 - Completed quick task 260404-exx: Fill callback/hook gaps

## Milestone

**v0.2.1 Code Health & Quality**
Goal: Resolve technical debt from codebase audit without touching public API.
Phases: 6 (see ROADMAP.md)

## Accumulated Context

### Project facts

- Library: pure Python package, src-layout, `uv` as package manager
- mypyc compiles `core.py` only — `conditions.py` stays interpreted
- Single runtime dep: `mypy-extensions`
- CI: `.github/workflows/ci.yml` (lint + test 3.10–3.13 × 3 OSes), `docs.yml`, `release.yml`
- No benchmark CI job yet

### v0.2.0 shipped 2026-03-06

Major API additions: per-state callbacks, `from_dict`, `snapshot/restore/clone`, `unless=`, async per-state callbacks, `CompiledFuncCondition`, `NegatedCondition`, `TransitionError`, `raise_if_failed`.

### Known constraints

- `except Exception` swallow-and-log in all callback/listener paths is intentional
- `State(ABC)` with no abstract methods is a design quirk to fix this milestone
- `condition_templates.py` import inconsistency: uses absolute `from fast_fsm import` vs relative elsewhere
- `__version__` in `__init__.py` was `"0.1.0"` while `pyproject.toml` was `"0.2.0"` — this milestone automates sync

## Blockers

None.

## Pending Decisions

- Exact mechanism for version sync: `importlib.metadata.version()` at import time (preferred) vs build-time injection
- Whether `py.typed` requires any changes to `setup.py` or just a file addition
- How many tests in the suite are genuinely low-value (audit will tell)

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260404-exx | Fill callback/hook gaps: before_transition, after_transition convenience, on_failed, on_trigger | 2026-04-04 | b3e6955 | Verified | [260404-exx-fill-callback-hook-gaps-before-transitio](./quick/260404-exx-fill-callback-hook-gaps-before-transitio/) |
