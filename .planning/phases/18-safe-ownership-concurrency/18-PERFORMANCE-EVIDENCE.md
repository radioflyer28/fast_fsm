# Phase 18 Ownership Performance Evidence

**Scope:** Wave 0 sync-trigger tracer. Exact rates are environment-labelled
observations, not portable policy claims. The compiled `trigger()` floor remains
200,000 operations/second.

## Before sync ownership tracer

| Mode | Module origin | Interpreter / platform | Command | Observation | Policy status |
| --- | --- | --- | --- | --- | --- |
| asserted pure | fresh temporary `src/fast_fsm/core.py` | CPython 3.12.10 / macOS arm64 | `phase16_isolated_verify.py --mode task --build-mode pure` with 50,000-toggle batch | 646,914 ops/sec | observation |
| freshly compiled | fresh temporary `src/fast_fsm/core.cpython-312-darwin.so` | CPython 3.12.10 / macOS arm64 | `phase16_isolated_verify.py --mode task --build-mode compiled` with 50,000-toggle batch | 811,704 ops/sec | observation; above 200,000 floor |

The temporary verification helper asserted module origin before each batch and
did not delete or load a checkout-native shadow.

## Sync ownership tracer

Pending Task 3 measurements. This section will record the same fixed 50,000
toggle batch after the tracer lands, with exact origin and environment labels.
