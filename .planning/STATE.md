---
gsd_state_version: 1.0
milestone: v0.2.3
milestone_name: Phases
status: Not started
last_updated: "2026-04-05T16:58:07.289Z"
last_activity: 2026-04-05
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 1
---

# State: Fast FSM

## Current Position

Phase: 12 — Timing Condition Implementation
Plan: —
Status: Not started
Last activity: 2026-04-05

## Milestone

**v0.2.3 Timing Condition Helpers**
Goal: Add reusable, platform-safe time-based condition classes (timeout, cooldown, elapsed) so users can express timing guards without writing clock logic.
Phases: 12–14 (3 phases, see ROADMAP.md)

## Accumulated Context

### Project facts

- Library: pure Python package, src-layout, `uv` as package manager
- mypyc compiles `core.py` only — `conditions.py` and `condition_templates.py` stay interpreted
- Single runtime dep: `mypy-extensions`
- CI: `.github/workflows/ci.yml` (lint + test 3.10–3.13 × 3 OSes), `docs.yml`, `release.yml`
- Benchmark CI job with 200k ops/sec throughput gate

### v0.2.2 shipped 2026-04-05

Introspection & agent tooling: `to_dict()`, `TransitionRecord` history, `to_plantuml()`, `to_json()`. 694 tests, 1.2M ops/sec.

### v0.2.1 shipped 2026-04-04

Code health: version sync, py.typed, ABC removal, exception annotation, test triage, benchmark CI.

### Clock source decision

All timing conditions use `time.monotonic()` — monotonic clock immune to NTP jumps and wall-clock adjustments across macOS/Linux/Windows. This is a passive guard approach — conditions are checked on trigger(), no auto-fire scheduler.

## Blockers

None.

## Pending Decisions

None.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260404-exx | Fill callback/hook gaps: before_transition, after_transition convenience, on_failed, on_trigger | 2026-04-04 | b3e6955 | Verified | [260404-exx-fill-callback-hook-gaps-before-transitio](./quick/260404-exx-fill-callback-hook-gaps-before-transitio/) |
