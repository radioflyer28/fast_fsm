# Roadmap: Fast FSM

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- ✅ **v0.2.2 Introspection & Agent Tooling** — Phases 7–11.1 (shipped 2026-04-05)
- ✅ **v0.2.3 Timing Condition Helpers** — Phases 12–14 (shipped 2026-04-05)

## Phases

<details>
<summary>✅ v0.2.1 Code Health & Quality (Phases 1–6) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Quick Wins — version sync + import fix
- [x] Phase 2: State ABC Cleanup — remove misleading `ABC` base
- [x] Phase 3: Exception Handling Audit — annotate all 16 broad catches
- [x] Phase 4: py.typed Marker — PEP 561 typed package declaration
- [x] Phase 5: Test Suite Triage — audit and prune 4 low-value tests
- [x] Phase 6: Benchmark CI — 200k ops/sec throughput gate + CI job

**14/14 requirements satisfied.** Full details: `.planning/milestones/v0.2.1-ROADMAP.md`

</details>

<details>
<summary>✅ v0.2.2 Introspection & Agent Tooling (Phases 7–11.1) — SHIPPED 2026-04-05</summary>

- [x] Phase 7: Serialization (`to_dict()`) — topology roundtrip via `StateMachine.to_dict()`
- [x] Phase 8: Transition History — opt-in `enable_history()` / `disable_history()` with `TransitionRecord`
- [x] Phase 9: PlantUML Output — `to_plantuml()` in `visualization.py`
- [x] Phase 10: Machine-Readable JSON Export — `to_json()` with topology + analysis + quality signals
- [x] Phase 11: Performance Verification & Docs — benchmark gate, README updates, milestone wrap-up
- [x] Phase 11.1: History-Enabled Performance Benchmark — gap closure for PERF-02 (2026-04-05)

**21/21 requirements satisfied.** 695 tests, 1.2M ops/sec.

</details>

<details>
<summary>✅ v0.2.3 Timing Condition Helpers (Phases 12–14) — SHIPPED 2026-04-05</summary>

- [x] Phase 12: Timing Condition Implementation — `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition`
- [x] Phase 13: Testing & Integration Verification — 27 new tests, 722 total, 200k+ ops/sec
- [x] Phase 14: Documentation — README examples, Sphinx API reference

**15/15 requirements satisfied.** 722 tests, no mypyc rebuild needed.

</details>

---
