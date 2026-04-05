# Roadmap: Fast FSM

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- � **v0.2.2 Introspection & Agent Tooling** — Phases 7–11 (in progress)

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

---

# Roadmap: Fast FSM v0.2.2

**Milestone:** v0.2.2 Introspection & Agent Tooling
**Goal:** Add structured, machine-readable access to FSM topology, transition history, and quality analysis so coding agents and users can understand, debug, and tune state machines programmatically.
**Defined:** 2026-04-05
**Phase numbering:** continues from v0.2.1 (last phase was Phase 6)

---

## v0.2.2 Phases

- [ ] **Phase 7: Serialization (`to_dict()`)** — topology roundtrip via `StateMachine.to_dict()`
- [ ] **Phase 8: Transition History** — opt-in `enable_history()` / `disable_history()` with `TransitionRecord`
- [ ] **Phase 9: PlantUML Output** — `to_plantuml()` in `visualization.py`
- [ ] **Phase 10: Machine-Readable JSON Export** — `to_json()` with topology + analysis + quality signals
- [ ] **Phase 11: Performance Verification & Docs** — benchmark gate, README updates, milestone wrap-up

---

## Phase Details

---

### Phase 7: Serialization (`to_dict()`)

**Goal:** `StateMachine.to_dict()` returns a plain dict that roundtrips losslessly through `StateMachine.from_dict()`.

**Requirements covered:** SERIAL-01, SERIAL-02, SERIAL-03

**Dependencies:** None (pure addition to `core.py`; no new `__slots__` needed)

**Tasks:**
1. Implement `StateMachine.to_dict()` in `core.py` — returns `{"name": ..., "initial": ..., "states": [...], "transitions": [{"trigger": ..., "from": ..., "to": ...}, ...]}` matching the `from_dict()` input schema exactly
2. Verify roundtrip: `StateMachine.from_dict(fsm.to_dict())` produces an equivalent machine (same states, same transitions)
3. Confirm guards are NOT included in output (callables are not serialisable — by design per SERIAL-02)
4. Rebuild compiled extension: `uv run python setup.py build_ext --inplace -q`
5. Run targeted tests: `uv run pytest tests/test_basic_functionality.py tests/test_advanced_functionality.py tests/test_builder.py -x -q`
6. Add tests for `to_dict()` roundtrip, empty machine, and multi-state machine in `test_basic_functionality.py`

**Verification:**
- [ ] `fsm.to_dict()` returns a dict with keys `name`, `initial`, `states`, `transitions`
- [ ] `StateMachine.from_dict(fsm.to_dict())` has identical state names and trigger graph to original
- [ ] Guards on transitions do not appear in `to_dict()` output
- [ ] Full test suite passes: `uv run pytest tests/ -x -q`
- [ ] `uv run mypy src/fast_fsm/core.py` passes (mypyc compat)

**UAT Criteria:**
- A user can serialize a `StateMachine` to a plain Python dict, pass it through `json.dumps` / `json.loads`, rebuild the topology via `from_dict()`, and trigger the same transitions without error

---

### Phase 8: Transition History

**Goal:** Users can opt in to recording every transition in a bounded buffer; the hot path is unaffected when history is disabled.

**Requirements covered:** HIST-01, HIST-02, HIST-03, HIST-04, HIST-05, HIST-06, HIST-07

**Dependencies:** Phase 7 (core.py already modified; avoids a second cold mypyc rebuild cycle)

**Core.py changes required (mypyc-sensitive):**
- Add `TransitionRecord` class with `__slots__ = ("from_state", "trigger", "to_state", "timestamp")` near the top of `core.py` (before `StateMachine`)
- Add `"_history"` and `"_history_max"` to `StateMachine.__slots__` (currently at line ~243)
- `_history: Optional[List[TransitionRecord]]` — `None` when disabled, list when enabled
- `_history_max: int` — capacity limit (default 1000)
- Initialize both to `None` / `1000` in `StateMachine.__init__`
- Add `enable_history(max_entries: int = 1000)`, `disable_history()`, `history` property to `StateMachine`
- In `_execute_transition()` hot path: single `if self._history is not None:` check to append; drop oldest when at capacity
- `AsyncStateMachine.trigger_async()` records via same `_execute_transition()` path or explicit append

**Tasks:**
1. Add `TransitionRecord` (`__slots__`, `from_state: str`, `trigger: str`, `to_state: str`, `timestamp: float`) to `core.py` — use `time.monotonic()` for timestamp
2. Extend `StateMachine.__slots__` with `"_history"` and `"_history_max"`
3. Initialize `self._history = None` and `self._history_max = 1000` in `__init__`
4. Implement `enable_history(max_entries=1000)`: sets `_history_max`, (re-)initializes `_history` to `[]`
5. Implement `disable_history()`: sets `_history = None`
6. Implement `history` property: returns `list(self._history)` if enabled, else `[]`
7. Add history recording to `_execute_transition()` with bounded drop of oldest entry (`del self._history[0]` before append when `len == _history_max`)
8. Verify `AsyncStateMachine` inherits history recording through the shared `_execute_transition()` code path (or patch `trigger_async()` if needed)
9. Add `TransitionRecord`, `enable_history`, `disable_history` to `__init__.py` imports and `__all__`
10. Rebuild compiled extension: `uv run python setup.py build_ext --inplace -q`
11. Run targeted tests: `uv run pytest tests/test_basic_functionality.py tests/test_advanced_functionality.py tests/test_async.py tests/test_performance_benchmarks.py -x -q`
12. Add tests: enable/disable toggle, max_entries boundary (5-entry cap with 7 triggers), chronological order, `history` returns `[]` when disabled, async machine records, performance: history-disabled throughput ≥ 200k

**Verification:**
- [ ] `fsm.enable_history(max_entries=5)` + 7 triggers → exactly 5 records (2 oldest dropped)
- [ ] `fsm.disable_history()` → `fsm.history` returns `[]`
- [ ] Each `TransitionRecord` has `from_state`, `trigger`, `to_state`, `timestamp` attributes
- [ ] `trigger()` throughput with history disabled ≥ 200,000 ops/sec
- [ ] `trigger()` throughput with history enabled measured and documented (≤ 2× slower target)
- [ ] `AsyncStateMachine` records appear after `await fsm.trigger_async(...)`
- [ ] `uv run mypy src/fast_fsm/core.py` passes
- [ ] Full test suite passes: `uv run pytest tests/ -x -q`

**UAT Criteria:**
- A user enables history, runs 10 transitions, calls `fsm.history`, and receives a list of 10 `TransitionRecord` objects in chronological order with correct `from_state`, `to_state`, and `trigger` values
- After `disable_history()`, `fsm.history` is `[]` and a subsequent `trigger()` benchmark shows no throughput regression

---

### Phase 9: PlantUML Output

**Goal:** `to_plantuml(fsm)` in `visualization.py` produces a valid PlantUML `@startuml` / `@enduml` state diagram string representing all states, transitions, and terminal states.

**Requirements covered:** VIS-01, VIS-02, VIS-03, VIS-04

**Dependencies:** None (pure `visualization.py` addition — no `core.py` changes, no mypyc rebuild needed)

**Tasks:**
1. Implement `to_plantuml(fsm)` in `visualization.py`, following the existing `to_mermaid()` pattern
2. Include `@startuml` / `@enduml` wrapper lines
3. Emit `[*] --> <initial_state>` for the initial state marker (first key in `fsm._states`)
4. Emit one `<from> --> <to> : <trigger>` line per transition in `fsm._transitions`
5. Detect terminal states (states in `fsm._states` with no entry in `fsm._transitions`, or with an empty trigger dict) and emit `<state> --> [*]` for each
6. Add `to_plantuml` to `__init__.py` imports (from `.visualization`) and to `__all__`
7. Run targeted tests: `uv run pytest tests/test_visualization.py -x -q`
8. Add tests: basic output structure, `@startuml`/`@enduml` presence, initial state marker, terminal state arrow, multi-state machine, state with no special chars

**Verification:**
- [ ] `to_plantuml(fsm)` output starts with `@startuml` and ends with `@enduml`
- [ ] Output contains `[*] --> <initial_state_name>` line
- [ ] Each transition appears as `<from> --> <to> : <trigger>`
- [ ] Terminal states (no outgoing transitions) emit `<state> --> [*]`
- [ ] `from fast_fsm import to_plantuml` works without error
- [ ] Full test suite passes: `uv run pytest tests/ -x -q`

**UAT Criteria:**
- A user calls `to_plantuml(fsm)` on a traffic-light FSM, pastes the output into a PlantUML renderer, and sees a correct state diagram with initial star marker and terminal state arrow

---

### Phase 10: Machine-Readable JSON Export

**Goal:** `to_json(fsm)` returns a JSON-serialisable dict covering topology, reachability, cycle detection, and `EnhancedFSMValidator` quality signals — the primary agent interface for reasoning about FSMs.

**Requirements covered:** VIS-05, VIS-06, VIS-07

**Dependencies:** Phase 9 (both are `visualization.py` additions; batch to minimize context switches). `validation.py` imported lazily inside function body per VIS-06.

**Output structure:**
```python
{
    "topology": {
        "states": ["idle", "running", "stopped"],
        "initial": "idle",
        "transitions": [
            {"trigger": "start", "from": "idle", "to": "running", "has_guard": False},
            ...
        ]
    },
    "analysis": {
        "reachability": {
            "reachable": ["idle", "running"],
            "unreachable": ["stopped"],
            "terminal": ["stopped"]
        },
        "cycles": {
            "has_cycles": True,
            "states_in_cycles": ["idle", "running"]
        },
        "quality": {  # null if EnhancedFSMValidator unavailable
            "completeness_score": 0.85,
            "warnings": [...],
            "issues": [...]
        }
    }
}
```

**Tasks:**
1. Implement `to_json(fsm)` in `visualization.py`
2. Build topology section: `fsm._states` for states list + initial; `fsm._transitions` for transitions with `has_guard = entry.condition is not None`
3. BFS/DFS from `fsm._initial_state.name` through `fsm._transitions` to compute `reachable` set
4. Compute `unreachable = set(fsm._states) - reachable`
5. Compute `terminal = {s for s in fsm._states if s not in fsm._transitions or not fsm._transitions[s]}`
6. DFS with visited+stack sets to detect cycles; collect states involved in back-edges
7. Populate quality section: `try: from .validation import EnhancedFSMValidator` inside the function body; run validator; map output to dict; `except ImportError: quality = None`
8. Add `to_json` to `__init__.py` imports (from `.visualization`) and to `__all__`
9. Run targeted tests: `uv run pytest tests/test_visualization.py tests/test_validation.py -x -q`
10. Add tests: all required keys present, `has_guard` True/False, reachable/unreachable classification, cycle detection (cyclic machine → `True`; DAG → `False`), quality section populated, `json.dumps(to_json(fsm))` succeeds, quality `null` when validation mocked as unavailable

**Verification:**
- [ ] `to_json(fsm)` returns dict with `topology` and `analysis` keys
- [ ] `json.dumps(to_json(fsm))` succeeds without `TypeError`
- [ ] `topology.transitions` entries each have `trigger`, `from`, `to`, `has_guard` fields
- [ ] Unreachable states correctly appear in `analysis.reachability.unreachable`
- [ ] Terminal states correctly appear in `analysis.reachability.terminal`
- [ ] `analysis.cycles.has_cycles` is `True` for a machine with a loop, `False` for a DAG
- [ ] `analysis.quality` is `null` when validation module patched as unavailable
- [ ] `from fast_fsm import to_json` works without error
- [ ] Full test suite passes: `uv run pytest tests/ -x -q`

**UAT Criteria:**
- A coding agent calls `to_json(fsm)` on an unknown FSM, parses the result, and can programmatically answer: "which states are unreachable?", "does this machine have cycles?", "what is the completeness score?" — all from the single returned dict

---

### Phase 11: Performance Verification & Docs

**Goal:** Confirm all performance contracts hold for v0.2.2 features, document measured history overhead, and update README/docs so v0.2.2 is correctly represented.

**Requirements covered:** PERF-01, PERF-02, COMPAT-01, COMPAT-02

**Dependencies:** Phases 7–10 complete

**Tasks:**
1. Run full benchmark with history disabled: `uv run python benchmarks/benchmark_fast_fsm.py` — verify ≥ 200,000 ops/sec (PERF-01)
2. Run benchmark with history enabled (1000-entry buffer): measure throughput delta; record in README benchmarks table or `docs/dev/architecture.md` (PERF-02)
3. Run `uv run mypy src/fast_fsm/core.py` — must pass cleanly (COMPAT-02)
4. Run `uv run pytest tests/ -x -q` — full suite green with all new tests included (COMPAT-01)
5. Update `README.md`: add `to_dict()`, `enable_history()` / `history`, `to_plantuml()`, `to_json()` to the API reference section with brief examples; add history timing note
6. Update `docs/api/core.md` — add docstring-linked entries for `to_dict`, `TransitionRecord`, `enable_history`, `disable_history`, `history`
7. Update `docs/api/visualization.md` — add `to_plantuml`, `to_json`
8. Verify Sphinx build: `uv run sphinx-build -b html docs docs/_build/html -W --keep-going`
9. Run doctest: `uv run sphinx-build -b doctest docs docs/_build/doctest`; fix any broken `{testcode}` blocks
10. Update `CHANGELOG.md` with v0.2.2 entry (all four new APIs)
11. Bump version in `pyproject.toml` to `0.2.2`

**Verification:**
- [ ] `trigger()` throughput (history disabled) ≥ 200,000 ops/sec confirmed
- [ ] History-enabled throughput measured and documented
- [ ] `uv run mypy src/fast_fsm/core.py` exits 0
- [ ] `uv run pytest tests/ -x -q` — 0 failures
- [ ] README includes all four new APIs with code examples
- [ ] Sphinx HTML build completes with 0 warnings (`-W` flag)
- [ ] `CHANGELOG.md` has v0.2.2 entry
- [ ] `pyproject.toml` version is `0.2.2`

**UAT Criteria:**
- A user upgrades from v0.2.1 and all existing code runs unchanged (no API breakage)
- A user installs v0.2.2, reads the README, and can successfully call `to_dict()`, `enable_history()`, `to_plantuml()`, and `to_json()` within 5 minutes

---

## Requirements Traceability

| Requirement | Phase | Notes |
|-------------|-------|-------|
| SERIAL-01   | 7     | `to_dict()` roundtrip via `from_dict()` |
| SERIAL-02   | 7     | Output schema: `name`, `initial`, `states`, `transitions`; no guards |
| SERIAL-03   | 7     | Already a `StateMachine` method — needs implementation |
| HIST-01     | 8     | `enable_history(max_entries)` — replaces buffer on repeat call |
| HIST-02     | 8     | `disable_history()` + `history` property returns `[]` |
| HIST-03     | 8     | `TransitionRecord` with `__slots__`; chronological list |
| HIST-04     | 8     | Bounded buffer — oldest entry dropped at capacity |
| HIST-05     | 8     | Zero-cost when disabled via `None` check in hot path |
| HIST-06     | 8     | `TransitionRecord`, `enable_history`, `disable_history` exported from `__init__` |
| HIST-07     | 8     | `AsyncStateMachine.trigger_async()` records to same buffer |
| VIS-01      | 9     | `to_plantuml(fsm)` in `visualization.py` |
| VIS-02      | 9     | All states + labeled transitions + `[*] --> initial` |
| VIS-03      | 9     | Terminal states marked with `<state> --> [*]` |
| VIS-04      | 9     | `to_plantuml` exported from `fast_fsm.__init__` |
| VIS-05      | 10    | `to_json(fsm)` — topology + reachability + cycles + quality |
| VIS-06      | 10    | Lazy import of `validation.py`; `quality = null` if unavailable |
| VIS-07      | 10    | `to_json` exported from `fast_fsm.__init__` |
| PERF-01     | 11    | Throughput ≥ 200k ops/sec (history disabled) verified |
| PERF-02     | 11    | History-enabled throughput measured and documented |
| COMPAT-01   | 11    | All existing APIs unchanged — full test suite green |
| COMPAT-02   | 11    | `mypy src/fast_fsm/core.py` passes; `TransitionRecord` uses `__slots__` |

**Coverage:** 21/21 requirements mapped ✓

---

## Build Notes (for phases touching `core.py`)

After any edit to `core.py`, rebuild before running tests:
```bash
uv run python setup.py build_ext --inplace -q
```

Type-check after `core.py` edits (mypyc compat):
```bash
uv run mypy src/fast_fsm/core.py
```

Full test suite:
```bash
uv run pytest tests/ -x -q
```

Targeted tests per phase:
- Phase 7: `uv run pytest tests/test_basic_functionality.py tests/test_advanced_functionality.py tests/test_builder.py -x -q`
- Phase 8: `uv run pytest tests/test_basic_functionality.py tests/test_advanced_functionality.py tests/test_async.py tests/test_performance_benchmarks.py -x -q`
- Phase 9: `uv run pytest tests/test_visualization.py -x -q`
- Phase 10: `uv run pytest tests/test_visualization.py tests/test_validation.py -x -q`
- Phase 11: `uv run pytest tests/ -x -q` (full suite)

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. Serialization (`to_dict()`) | 0/1 | Not started | - |
| 8. Transition History | 0/1 | Not started | - |
| 9. PlantUML Output | 0/1 | Not started | - |
| 10. Machine-Readable JSON Export | 0/1 | Not started | - |
| 11. Performance Verification & Docs | 0/1 | Not started | - |

---
*v0.2.2 roadmap defined: 2026-04-05*
