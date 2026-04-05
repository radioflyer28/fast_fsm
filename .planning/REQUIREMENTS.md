# Requirements: Fast FSM v0.2.3

**Defined:** 2026-04-05
**Core Value:** Blazing-fast, zero-overhead FSM transitions — `trigger()` ≥200,000 ops/sec, all core ops O(1).

## v0.2.3 Requirements

Goal: Add reusable, platform-safe time-based condition classes so users can express timeout, cooldown, and elapsed-time guards without writing clock logic.

### Timing Conditions

- [ ] **TIME-01**: `TimeoutCondition(seconds)` — blocks a transition after elapsed time exceeds threshold since a reference point; reference set on construction or via `reset()`
- [ ] **TIME-02**: `CooldownCondition(seconds)` — blocks a transition until N seconds have passed since its last successful check; first check always passes
- [ ] **TIME-03**: `ElapsedCondition(seconds)` — passes when ≥ N seconds have elapsed since a reference timestamp; reference set on construction or via `reset()`
- [ ] **TIME-04**: All timing conditions use `time.monotonic()` — immune to NTP jumps and wall-clock adjustments across macOS, Linux, and Windows
- [ ] **TIME-05**: All timing conditions provide `reset()` method to restart their internal clock reference
- [ ] **TIME-06**: All timing conditions accept `**kwargs` in `check()` (forward-compat signature per `Condition` ABC contract)
- [ ] **TIME-07**: All timing conditions use `__slots__` — consistent with library memory model

### Integration

- [ ] **INT-01**: Timing conditions added to `condition_templates.py` alongside existing helpers (AlwaysCondition, NeverCondition, etc.)
- [ ] **INT-02**: `TimeoutCondition`, `CooldownCondition`, `ElapsedCondition` exported from `fast_fsm.__init__`
- [ ] **INT-03**: Timing conditions work as guards on both `StateMachine` and `AsyncStateMachine` via standard `condition=` parameter
- [ ] **INT-04**: `FSMBuilder` supports timing conditions via `.add_transition()` `condition=` parameter (no special handling needed — they're `Condition` subclasses)

### Non-Functional

- [ ] **PERF-01**: `trigger()` throughput with a timing condition guard ≥ 200,000 ops/sec (single `time.monotonic()` call in hot path)
- [ ] **COMPAT-01**: All existing tests pass (694 baseline)
- [ ] **DOC-01**: README updated with timing condition examples (timeout, cooldown, elapsed)
- [ ] **DOC-02**: Sphinx docs updated — timing conditions documented in API reference

## Future Requirements (deferred)

### Additional Timing Conditions
- `ThrottleCondition(max_count, window_seconds)` — limits to max N transitions per time window (rate limiter)
- `TimeWindowCondition(start_offset, end_offset)` — only allows transitions within a time window

### Timed Transitions
- `add_timeout(state, timeout_seconds, trigger)` — fires trigger automatically after N seconds in state (requires async scheduler; separate milestone)

### Coverage
- `core.py` 0% in coverage reports (mypyc artifact) — add `FAST_FSM_PURE_PYTHON=1` coverage run configuration

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-fire/scheduler timers | Conditions are passive guards; scheduling belongs one layer up (user's event loop) |
| Wall-clock / calendar-aware conditions | `time.monotonic()` only — wall clock introduces NTP drift, timezone, and DST issues |
| Thread-safe timer management | No locks in hot path; thread safety is the caller's responsibility |
| `core.py` changes | Timing conditions live in `condition_templates.py` (interpreted); no mypyc rebuild needed |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TIME-01     | TBD   | Pending |
| TIME-02     | TBD   | Pending |
| TIME-03     | TBD   | Pending |
| TIME-04     | TBD   | Pending |
| TIME-05     | TBD   | Pending |
| TIME-06     | TBD   | Pending |
| TIME-07     | TBD   | Pending |
| INT-01      | TBD   | Pending |
| INT-02      | TBD   | Pending |
| INT-03      | TBD   | Pending |
| INT-04      | TBD   | Pending |
| PERF-01     | TBD   | Pending |
| COMPAT-01   | TBD   | Pending |
| DOC-01      | TBD   | Pending |
| DOC-02      | TBD   | Pending |

**Coverage:**
- v0.2.3 requirements: 15 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 15

---
*Requirements defined: 2026-04-05*
*Last updated: 2026-04-05 after v0.2.3 initialization*
