# Milestones

## v0.2.3 Timing Condition Helpers (Shipped: 2026-04-05)

**Phases completed:** 3 phases (12–14), 15/15 requirements satisfied, 722 tests passing

**Key accomplishments:**

- `TimeoutCondition(seconds)` — allows transitions within a time window, blocks after timeout (Phase 12)
- `CooldownCondition(seconds)` — enforces minimum interval between successful triggers (Phase 12)
- `ElapsedCondition(seconds)` — gates transitions until elapsed time threshold is met (Phase 12)
- All timing conditions use `time.monotonic()`, `__slots__`, `reset()`, and `**kwargs` in `check()` (Phase 12)
- 27 new tests: unit tests (18), FSM integration tests (8), throughput benchmark (1) (Phase 13)
- Timing condition throughput verified ≥ 200k ops/sec compiled, ≥ 30k pure Python (Phase 13)
- README updated with timing condition examples; Sphinx autodoc covers all three (Phase 14)

---

## v0.2.2 Introspection & Agent Tooling (Shipped: 2026-04-05)

**Phases completed:** 6 phases (7–11.1), 21/21 requirements satisfied, 695 tests passing, 1.2M ops/sec

**Key accomplishments:**

- `StateMachine.to_dict()` / `from_dict()` topology serialization roundtrip (Phase 7)
- Opt-in transition history with `TransitionRecord`, bounded buffer, zero-cost when disabled (Phase 8)
- `to_plantuml()` state diagram visualization in `visualization.py` (Phase 9)
- `to_json()` machine-readable FSM export with topology + reachability + cycle + quality analysis (Phase 10)
- Performance verification & README documentation updates (Phase 11)
- History-enabled throughput benchmark — gap closure for PERF-02, ≤ 2× degradation verified (Phase 11.1)

---

## v0.2.1 Code Health & Quality (Shipped: 2026-04-04)

**Phases completed:** 6 phases, 1 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---
