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

### Technical Debt Tracking

| Item | Introduced | Resolved | Milestone |
|------|-----------|---------|-----------|
| `__version__` hardcoded to `"0.1.0"` | pre-audit | ✓ | v0.2.1 |
| `condition_templates.py` absolute import | pre-audit | ✓ | v0.2.1 |
| `State` inherits from `ABC` misleadingly | pre-audit | ✓ | v0.2.1 |
| `except Exception` catches undocumented | pre-audit | ✓ | v0.2.1 |
| Missing `py.typed` marker | pre-audit | ✓ | v0.2.1 |
| Low-value/redundant tests (4) | pre-audit | ✓ | v0.2.1 |
| `core.py` shows 0% in coverage (mypyc artifact) | v0.2.1 audit | Open | v0.2.2 |
