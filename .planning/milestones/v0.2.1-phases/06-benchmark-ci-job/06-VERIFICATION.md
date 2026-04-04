# Phase 6 Verification — Benchmark CI Job

**Date:** 2026-04-04  
**Commit:** b671e96

## Requirements Verified

### CI-01 — Benchmark job in ci.yml runs on push to main
- `.github/workflows/ci.yml` now has a `benchmark` job
- Condition: `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`
- Does NOT run on PRs (scope-limited as required)
- Steps: checkout → setup-uv → `uv sync --group dev` → `build_ext --inplace -q` → `pytest -m slow`
- ✅ CONFIRMED

### CI-02 — Assertable 200k ops/sec threshold enforced in CI
- `tests/test_performance_benchmarks.py::TestAdvancedPerformance::test_trigger_min_throughput`
  added with `@pytest.mark.slow`
- Detects compiled mode by checking `fast_fsm.core` module file suffix (`.so`/`.pyd`)
- Compiled floor: 200,000 ops/sec
- Pure-Python floor: 30,000 ops/sec (guards against catastrophic regressions locally)
- Logging suppressed during timed section (prevents measurement noise)
- ✅ CONFIRMED

## Test Results

```
uv run pytest tests/ --tb=no
634 passed in 2.45s
```

Slow benchmarks specifically:
```
uv run pytest tests/test_performance_benchmarks.py -m slow -x -q
7 passed
```

## Key Design Decision

Mode detection uses `importlib.util.find_spec("fast_fsm.core").origin` suffix instead of the
`FAST_FSM_PURE_PYTHON` env var. The env var suppresses compilation at *build time* but has no
bearing on what is loaded at runtime — the compiled `.so` may or may not be present regardless
of the env var state. File-suffix detection is accurate in all cases.
