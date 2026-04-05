# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.2.1 — Code Health & Quality

**Shipped:** 2026-04-04  
**Phases:** 6 | **Plans:** 6 | **Sessions:** 1 (autonomous)

### What Was Built

- Dynamic `__version__` via `importlib.metadata` — version string and `pyproject.toml` can no longer drift
- `State` ABC removal — cleaned up misleading inheritance with zero test changes required
- Full exception handling audit — all 16 broad catches annotated with intent comments; `safe_trigger()` semantics documented
- PEP 561 `py.typed` marker — fast_fsm is now formally a typed package for mypy/pyright
- Test suite triage — written audit document, 4 low-value tests removed (637 → 634 including new benchmark test)
- Benchmark CI job — 200k ops/sec throughput gate runs on every push to main

### What Worked

- **Autonomous mode was effective for infrastructure phases:** All 6 phases executed end-to-end without user intervention. Pure maintenance work is a good fit for autonomous execution.
- **Mode detection via file suffix:** Detecting mypyc compilation by checking `core.module.__file__` suffix (`.so`/`.pyd`) is robust and doesn't rely on env vars that only affect build time, not runtime.
- **Small, atomic commits per phase:** Each phase was committed independently, making the git log easy to read and each change easy to review or revert.
- **Inline annotation approach for exception audit (Phase 3):** Adding comments directly to the catch sites was simpler and more durable than creating a separate documentation file — the context lives where the code is.

### What Was Inefficient

- **Logging overhead masked as benchmark failure:** The benchmark test initially failed because every `trigger()` call emits INFO-level log messages — 400k log lines for a 200k-iteration batch. Had to add explicit logging suppression inside the timed section. This was a non-obvious interaction.
- **Benchmark mode detection used env var initially:** First attempt used `FAST_FSM_PURE_PYTHON` env var, which is a build-time flag (not runtime). Required a rethink to use file-suffix detection. Two iterations to get correct.
- **`uv sync --reinstall-package` required after version bump:** Editable install caches package metadata; reinstall is needed to update `importlib.metadata` response. Not obvious from the workflow.

### Patterns Established

- **Timing loop always suppresses logging:** Any benchmark that measures raw throughput MUST suppress the FSM logger during the timed region. Log I/O will otherwise dominate the measurement.
- **Compiled-mode detection:** Use `importlib.util.find_spec("fast_fsm.core").origin.endswith(".so")` — not `FAST_FSM_PURE_PYTHON`.
- **Phase verification as functional test:** Writing a VERIFICATION.md after each phase with specific evidence (pass/fail, test count, command outputs) provides a useful audit trail and CI substitute when running autonomously.

### Key Lessons

1. **env vars that gate build steps don't reflect runtime state.** `FAST_FSM_PURE_PYTHON=1` tells `setup.py` to skip compilation — it has no bearing on whether the compiled `.so` file is present at runtime. Always check actual module state to detect compiled vs interpreted mode.
2. **Logging is a hidden benchmark dependency.** Production logging that fires on every operation becomes the dominant cost in any tight loop. Suppress it explicitly in performance tests.
3. **`uv sync --reinstall-package <name>` is the correct way to refresh `importlib.metadata` from a bumped `pyproject.toml`.** Running `uv sync` alone is insufficient.
4. **6-phase maintenance milestone fits comfortably in 1 autonomous session.** Each phase was small and well-scoped; context never overflowed during execution.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Sessions | What Changed |
|-----------|--------|----------|-------------|
| v0.2.1 | 6 | 1 | First autonomous milestone run; all infrastructure/cleanup |
| v0.2.2 | 6 | 2 | Feature phases via autonomous + retroactive audit/gap closure; learned to audit after autonomous runs |
| v0.2.3 | 3 | 1 | Cleanest autonomous run yet; no blockers, no gaps, proactive enrichment |

### Technical Debt Tracking

| Item | Introduced | Resolved | Milestone |
|------|-----------|---------|-----------|
| `__version__` hardcoded to `"0.1.0"` | pre-audit | ✓ | v0.2.1 |
| `condition_templates.py` absolute import | pre-audit | ✓ | v0.2.1 |
| `State` inherits from `ABC` misleadingly | pre-audit | ✓ | v0.2.1 |
| `except Exception` catches undocumented | pre-audit | ✓ | v0.2.1 |
| Missing `py.typed` marker | pre-audit | ✓ | v0.2.1 |
| Low-value/redundant tests (4) | pre-audit | ✓ | v0.2.1 |
| `core.py` shows 0% in coverage (mypyc artifact) | v0.2.1 audit | Open | — |

---

## Milestone: v0.2.2 — Introspection & Agent Tooling

**Shipped:** 2026-04-05
**Phases:** 6 (7–11.1) | **Requirements:** 21/21 | **Sessions:** 2 (1 autonomous + 1 audit/gap closure)

### What Was Built

- `StateMachine.to_dict()` / `from_dict()` topology serialization roundtrip — machines can be serialized, stored, and reconstructed
- Opt-in transition history via `enable_history()` / `disable_history()` with `TransitionRecord` dataclass and bounded `deque` buffer
- `to_plantuml()` in `visualization.py` — generates valid PlantUML state diagrams with initial/terminal markers
- `to_json()` machine-readable export — topology + reachability analysis + cycle detection + quality scores from `EnhancedFSMValidator`
- History-enabled throughput benchmark (Phase 11.1 gap closure) — verified ≤ 2× degradation vs disabled baseline
- README updated with performance table and transition history documentation

### What Worked

- **Autonomous mode scaled well for feature phases:** 5 phases (7–11) executed end-to-end without intervention. Feature work that follows clear requirements is a good fit for autonomous execution.
- **`to_json()` lazy import of validation.py:** Quality section is populated only when `validation.py` is available — keeps the import-time dependency minimal.
- **Bounded deque for history:** Using `collections.deque(maxlen=N)` for the circular buffer is both performant and eliminates unbounded memory growth risk.
- **Zero-cost history when disabled:** Single `None` check in `trigger()` hot path means no measurable overhead when history is off.

### What Was Inefficient

- **Autonomous run skipped GSD closeout artifacts:** Phases 7–11 were executed with no SUMMARY.md files, which meant the `milestone complete` CLI couldn't extract accomplishments. Had to manually enrich the MILESTONES.md entry.
- **PERF-02 gap missed during autonomous execution:** The autonomous run declared the milestone done without measuring history-enabled throughput. Caught only during the retroactive audit (Phase 11.1 gap closure).
- **Archived REQUIREMENTS.md had wrong content:** The `milestone complete` CLI archived the current REQUIREMENTS.md which had already been replaced with v0.2.3 content. Had to manually restore from git history.

### Patterns Established

- **Always run `/gsd-audit-milestone` after autonomous execution:** Autonomous mode may skip verification steps. An explicit audit catches gaps before the milestone is archived.
- **Gap closure phases use decimal numbering (e.g., 11.1):** Inserted between completed phases to close audit-identified gaps without renumbering.
- **Archive REQUIREMENTS.md before creating new milestone:** When requirements are replaced via `/gsd-new-milestone`, the old content must be archived first — the CLI can't recover it later.

### Key Lessons

1. **Autonomous execution + GSD closeout require separate passes.** Autonomous mode prioritizes code delivery over GSD artifact creation. Closeout (audit, archive, tag) should be a deliberate follow-up step.
2. **The `milestone complete` CLI assumes SUMMARY.md exists for each phase.** If phases lack summaries (e.g., from autonomous runs), the CLI reports empty accomplishments. Manual enrichment is needed.
3. **REQUIREMENTS.md is a mutable file that gets overwritten by `new-milestone`.** Archive it before (or immediately after) creating a new milestone to avoid data loss.
4. **History-enabled throughput is a distinct metric from baseline throughput.** Both should be benchmarked explicitly — don't assume one covers the other.

---

## Milestone: v0.2.3 — Timing Condition Helpers

**Shipped:** 2026-04-05
**Phases:** 3 (12–14) | **Requirements:** 15/15 | **Sessions:** 1 (autonomous)

### What Was Built

- `TimeoutCondition(seconds)` — allows transitions within a time window, blocks after expiry
- `CooldownCondition(seconds)` — enforces minimum interval between successful triggers
- `ElapsedCondition(seconds)` — gates transitions until elapsed time threshold met
- All three use `time.monotonic()`, `__slots__`, `reset()`, `**kwargs` in `check()`
- 27 new tests: 18 unit, 8 FSM integration (sync + async + builder), 1 throughput benchmark
- README timing condition examples + Sphinx autodoc coverage

### What Worked

- **Autonomous mode handled the entire milestone cleanly.** 3 well-defined phases with precise requirements executed without user intervention. Lessons from v0.2.2 applied: audit ran inline, MILESTONES.md enriched proactively.
- **Infrastructure phase detection skipped unnecessary discuss steps.** Phases 13 (testing) and 14 (docs) were correctly identified as infrastructure and got minimal auto-generated context.
- **Deterministic tests via direct attribute manipulation.** Setting `_ref` and `_last_success` directly instead of using `time.sleep()` made all timing tests instant and non-flaky.
- **Purely additive to condition_templates.py.** Zero changes to `core.py` — no mypyc rebuild needed. The compilation boundary worked exactly as designed.

### What Was Inefficient

- Nothing noteworthy — this was a smooth, well-scoped milestone.

### Patterns Established

- **Timing tests manipulate internal attributes for determinism.** Never use `time.sleep()` in timing condition tests. Set `_ref = time.monotonic() - N` to simulate N seconds elapsed.
- **Condition classes follow a strict template:** `__slots__`, `super().__init__(auto_name, auto_desc)`, `check(**kwargs)`, `reset()`. Future conditions should follow this pattern.
- **Each milestone's throughput benchmark gets its own test.** `test_trigger_timing_condition_throughput` joins `test_trigger_min_throughput` and `test_trigger_history_enabled_throughput`.

### Key Lessons

1. **Well-scoped milestones with precise requirements execute fastest.** v0.2.3 had 15 non-ambiguous requirements across 3 phases — zero decisions needed from user, zero blockers encountered.
2. **condition_templates.py is the right home for timing conditions.** Stays interpreted (user-subclassable), doesn't touch the mypyc boundary, and autodoc picks them up automatically.
3. **Proactive MILESTONES.md enrichment after CLI archive avoids the v0.2.2 empty-accomplishments problem.**
