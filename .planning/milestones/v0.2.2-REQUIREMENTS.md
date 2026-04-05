# Requirements: Fast FSM v0.2.2

**Defined:** 2026-04-05
**Core Value:** Blazing-fast, zero-overhead FSM transitions — `trigger()` ≥200,000 ops/sec, all core ops O(1).

## v0.2.2 Requirements

Goal: Add structured, machine-readable access to FSM topology, transition history, and quality analysis so that coding agents and users can understand, debug, and tune state machines programmatically.

### Serialization

- [ ] **SERIAL-01**: `StateMachine.to_dict()` returns a plain dict that is structurally compatible with `from_dict()` — full topology roundtrip: `StateMachine.from_dict(fsm.to_dict())` produces an equivalent machine
- [ ] **SERIAL-02**: `to_dict()` output includes `"name"`, `"initial"`, `"states"`, and `"transitions"` (each transition as `{"trigger", "from", "to"}`); guard presence is NOT included (guards are callable, not serialisable)
- [ ] **SERIAL-03**: `to_dict()` is exported from `fast_fsm.__init__` as a `StateMachine` method (already part of the class — just needs implementation)

### Transition History

- [ ] **HIST-01**: `StateMachine.enable_history(max_entries: int = 1000)` activates opt-in transition recording; calling again with a different `max_entries` replaces the buffer
- [ ] **HIST-02**: `StateMachine.disable_history()` clears the buffer and stops recording; `history` returns `[]` after this call
- [ ] **HIST-03**: `StateMachine.history` property returns `list[TransitionRecord]` in chronological order; `TransitionRecord` is a simple `__slots__` dataclass with `from_state: str`, `trigger: str`, `to_state: str`, `timestamp: float` (Unix time from `time.monotonic()` — not wall clock, so no TZ issues)
- [ ] **HIST-04**: When `max_entries` is reached, oldest entries are dropped (circular/bounded buffer semantics); no unbounded memory growth
- [ ] **HIST-05**: History recording is **zero-cost when disabled** — the `trigger()` hot path branch is a single `None` check; throughput stays ≥200,000 ops/sec with history disabled
- [ ] **HIST-06**: `TransitionRecord` and `enable_history` / `disable_history` exported from `fast_fsm.__init__`
- [ ] **HIST-07**: `AsyncStateMachine` supports the same history API; `trigger_async()` records to the same buffer

### Visualization — PlantUML

- [ ] **VIS-01**: `to_plantuml(fsm)` in `visualization.py` returns a valid PlantUML `@startuml` / `@enduml` state diagram string
- [ ] **VIS-02**: PlantUML output includes: all states, all labeled transitions (trigger name on arrow), initial state marker (`[*] --> initial_state`)
- [ ] **VIS-03**: PlantUML output marks states with no outgoing transitions (terminal/sink states) using a `[*]` arrow from that state
- [ ] **VIS-04**: `to_plantuml` exported from `fast_fsm.__init__`

### Visualization — Machine-Readable JSON

- [ ] **VIS-05**: `to_json(fsm)` in `visualization.py` returns a structured dict (JSON-serialisable via `json.dumps`) covering:
  - `topology`: states list, transitions list (each with `trigger`, `from`, `to`, `has_guard: bool`)
  - `analysis.reachability`: which states are reachable from initial, which are unreachable (dead), which are terminal (no outgoing transitions)
  - `analysis.cycles`: whether any cycles exist (bool); list of states involved in cycles
  - `analysis.quality`: output from `EnhancedFSMValidator` — completeness score, warnings, issues
- [ ] **VIS-06**: `to_json()` does NOT require `validation.py` at import time — the quality section is populated lazily; if `validation.py` is unavailable, `analysis.quality` is `null`
- [ ] **VIS-07**: `to_json` exported from `fast_fsm.__init__`

### Non-Functional

- [ ] **PERF-01**: `trigger()` throughput with history **disabled** stays ≥200,000 ops/sec (verified by existing `test_performance_benchmarks.py`)
- [ ] **PERF-02**: `trigger()` throughput with history **enabled** is measured and documented (no hard floor — observable degradation is acceptable; must not be >50% slower than disabled)
- [ ] **COMPAT-01**: All existing public APIs remain unchanged — `to_dict`, `enable_history`, `to_plantuml`, `to_json` are purely additive
- [ ] **COMPAT-02**: mypyc compilation boundary respected — `TransitionRecord` and any new `core.py` slots must be mypyc-compatible (`__slots__`, no dynamic attrs)

## Future Requirements (deferred)

### Timed Transitions
- `add_timeout(state, timeout_seconds, trigger)` — fires trigger automatically after N seconds in state (requires async scheduler or threading.Timer; v0.2.3+)

### Coverage
- `core.py` 0% in coverage reports (mypyc artifact) — add `FAST_FSM_PURE_PYTHON=1` coverage run configuration (from RETROSPECTIVE.md deferred item)

## Out of Scope

| Feature | Reason |
|---------|--------|
| `core.py` refactoring | Hard constraint — single-file mypyc compilation unit |
| Timeout/timed transitions | Requires async scheduler — separate milestone |
| `snapshot()` topology version | `to_dict()` + `snapshot()` compose cleanly without a version bump |
| DOT/Graphviz output | Good candidate for v0.2.3; PlantUML has wider adoption |
| Breaking API changes | Backward compatibility contract upheld |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SERIAL-01   | TBD   | Pending |
| SERIAL-02   | TBD   | Pending |
| SERIAL-03   | TBD   | Pending |
| HIST-01     | TBD   | Pending |
| HIST-02     | TBD   | Pending |
| HIST-03     | TBD   | Pending |
| HIST-04     | TBD   | Pending |
| HIST-05     | TBD   | Pending |
| HIST-06     | TBD   | Pending |
| HIST-07     | TBD   | Pending |
| VIS-01      | TBD   | Pending |
| VIS-02      | TBD   | Pending |
| VIS-03      | TBD   | Pending |
| VIS-04      | TBD   | Pending |
| VIS-05      | TBD   | Pending |
| VIS-06      | TBD   | Pending |
| VIS-07      | TBD   | Pending |
| PERF-01     | TBD   | Pending |
| PERF-02     | TBD   | Pending |
| COMPAT-01   | TBD   | Pending |
| COMPAT-02   | TBD   | Pending |

**Coverage:**
- v0.2.2 requirements: 21 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 21

---
*Requirements defined: 2026-04-05*
*Last updated: 2026-04-05 after v0.2.2 initialization*
