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

## Final Plan 05 isolated proof — 2026-09-01

| Artifact mode | Origin assertion | Selection | Result |
| --- | --- | --- | --- |
| Pure | `fast_fsm.core` resolved to `src/fast_fsm/core.py` in a clean export | lifecycle, advanced, listener, builder, async, boundary, and mypyc-guard tests | Passed. |
| Fresh compiled | A mypyc extension built in a separate temporary export | the same lifecycle selection | Passed. |
| Fresh compiled | A mypyc extension built in a separate temporary export | `lifecycle_success or trigger_min_throughput` performance selection | 2 passed; the fixed 200,000 ops/sec floor held. |
| Pure | `fast_fsm.core` resolved to `src/fast_fsm/core.py` in a clean export | slots-policy audit and the full sequential release gate | Passed: 1,267 tests, Ruff format/lint, mypy, Sphinx HTML, doctests, and baseline freshness. |

The final gate ran through the Phase 17 harness, which exports `HEAD`, overlays
the reviewed lifecycle files, and asserts the imported module origin for each
mode. It did not use, mutate, or remove checkout-native shadows. The tracked
baseline records a pure-source, environment-labelled microbenchmark separately;
the release contract here is only the compiled 200,000 ops/sec floor, not an
exact throughput promise.

The compiled lifecycle selection emitted the already-tracked mypyc
`throw(type, exc, tb)` deprecation warnings (`fast_fsm-2fh`). They are
non-failing and outside this phase's lifecycle/evidence scope.

## Categorical Historical Provenance

This block preserves source-tree evidence only. The parent verifier computes
this file's SHA-256 and keeps this record out of installed-artifact, parity,
and compiled-throughput release gates.

<!-- fast-fsm-historical-evidence:start -->
```json
{
  "fields": {
    "build_mode": {
      "reason": "The record aggregates separate pure and freshly compiled checks.",
      "searched_sources": ["original Phase 17 evidence narrative", "git log --follow -- .planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md"],
      "status": "unavailable"
    },
    "command": {
      "citation": "Before Wave 0 tracer Commands",
      "status": "recorded",
      "value": "uv run python tools/phase16_isolated_verify.py --mode task --build-mode compiled --include src/fast_fsm/core.py --include tests/test_performance_benchmarks.py --include tools/phase16_isolated_verify.py -- uv run pytest tests/test_performance_benchmarks.py -x -q -k test_trigger_min_throughput"
    },
    "environment": {
      "reason": "The original record asserts fresh temporary exports but does not identify an exact interpreter, operating system, and architecture tuple.",
      "searched_sources": ["original Phase 17 evidence narrative", "git log --follow -- .planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md"],
      "status": "unavailable"
    },
    "measurement_outcome": {
      "citation": "Final Plan 05 isolated proof results table",
      "status": "recorded",
      "value": "2 passed; the fixed 200,000 ops/sec floor held."
    },
    "original_evidence_commit": {
      "reason": "The original record does not name the commit that captured this evidence file.",
      "searched_sources": ["original Phase 17 evidence narrative", "git log --follow -- .planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md"],
      "status": "unavailable"
    },
    "phase": {
      "citation": "Phase 20 fixed historical allowlist",
      "status": "recorded",
      "value": "17"
    },
    "source_path": {
      "citation": "Phase 20 fixed historical allowlist",
      "status": "recorded",
      "value": ".planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md"
    },
    "threshold_outcome": {
      "citation": "Final Plan 05 isolated proof results table",
      "status": "recorded",
      "value": "the fixed 200,000 ops/sec floor held."
    }
  },
  "kind": "historical_phase_performance",
  "schema_version": 1
}
```
<!-- fast-fsm-historical-evidence:end -->
