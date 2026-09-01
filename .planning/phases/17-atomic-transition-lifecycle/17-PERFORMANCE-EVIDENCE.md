# Phase 17 Performance Evidence

Environment-labelled lifecycle measurements captured while the checkout contains
intentional native shadows. The commands below export `HEAD`, overlay only the
named working-tree files, and assert module origin before running the benchmark;
they do not use or remove checkout `.so` artifacts.

## Before Wave 0 tracer — 2026-09-01

| Artifact mode | Origin assertion | Selection | Result |
| --- | --- | --- | --- |
| Pure | `fast_fsm.core` resolved to `src/fast_fsm/core.py` in a clean export | `tests/test_performance_benchmarks.py -k test_trigger_min_throughput` | Passed the pure-Python floor. |
| Fresh compiled | A mypyc extension built in a separate temporary export | `tests/test_performance_benchmarks.py -k test_trigger_min_throughput` | Passed the compiled 200,000 ops/sec floor. |

Commands:

```bash
uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure --include src/fast_fsm/core.py --include tests/test_performance_benchmarks.py --include tools/phase16_isolated_verify.py -- uv run pytest tests/test_performance_benchmarks.py -x -q -k test_trigger_min_throughput
uv run python tools/phase16_isolated_verify.py --mode task --build-mode compiled --include src/fast_fsm/core.py --include tests/test_performance_benchmarks.py --include tools/phase16_isolated_verify.py -- uv run pytest tests/test_performance_benchmarks.py -x -q -k test_trigger_min_throughput
```

The benchmark emits pass/fail against a fixed floor rather than a durable exact
rate; this record intentionally makes no unstated throughput claim. Post-tracer
measurements are recorded below after the lifecycle-success selection exists.

## Wave 0 tracer and compatibility guard — 2026-09-01

| Artifact mode | Origin assertion | Selection | Result |
| --- | --- | --- | --- |
| Pure | `fast_fsm.core` resolved to `src/fast_fsm/core.py` in a clean export | lifecycle tracer, `TransitionResult`, observer, and isolation-guard selection | 8 passed. |
| Fresh compiled | A mypyc extension built in a separate temporary export | lifecycle tracer plus `lifecycle_success` and `trigger_min_throughput` | 4 passed; the compiled 200,000 ops/sec floor held. |

The compiled result is a fresh extension produced from the Wave 0 source and
not any native shadow in the developer checkout.
