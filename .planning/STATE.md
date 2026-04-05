---
gsd_state_version: 1.0
milestone: null
milestone_name: null
status: Complete
last_updated: "2026-04-05T00:00:00.000Z"
last_activity: 2026-04-05
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# State: Fast FSM

## Current Position

Phase: —
Plan: —
Status: No active milestone
Last activity: 2026-04-05

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-05)

**Core value:** Blazing-fast, zero-overhead FSM transitions — `trigger()` ≥200,000 ops/sec, all core ops O(1).
**Current focus:** Planning next milestone

## Accumulated Context

### Project facts

- Library: pure Python package, src-layout, `uv` as package manager
- mypyc compiles `core.py` only — `conditions.py` and `condition_templates.py` stay interpreted
- Single runtime dep: `mypy-extensions`
- CI: `.github/workflows/ci.yml` (lint + test 3.10–3.13 × 3 OSes), `docs.yml`, `release.yml`
- Benchmark CI job with 200k ops/sec throughput gate
- 722 tests passing (post-v0.2.3)

### v0.2.3 shipped 2026-04-05

Timing condition helpers: `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition`. 27 new tests, 722 total.

### v0.2.2 shipped 2026-04-05

Introspection & agent tooling: `to_dict()`, `TransitionRecord` history, `to_plantuml()`, `to_json()`. 694 tests, 1.2M ops/sec.

### v0.2.1 shipped 2026-04-04

Code health: version sync, py.typed, ABC removal, exception annotation, test triage, benchmark CI.

## Blockers

None.

## Pending Decisions

None.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260404-exx | Fill callback/hook gaps: before_transition, after_transition convenience, on_failed, on_trigger | 2026-04-04 | b3e6955 | Verified | [260404-exx-fill-callback-hook-gaps-before-transitio](./quick/260404-exx-fill-callback-hook-gaps-before-transitio/) |
