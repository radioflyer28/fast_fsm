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

| Mode | Module origin | Interpreter / platform | Command | Observation | Policy status |
| --- | --- | --- | --- | --- | --- |
| asserted pure | fresh temporary `src/fast_fsm/core.py` | CPython 3.12.10 / macOS arm64 | `phase16_isolated_verify.py --mode task --build-mode pure` with 50,000-toggle batch | 523,659 ops/sec | observation |
| freshly compiled | fresh temporary `src/fast_fsm/core.cpython-312-darwin.so` | CPython 3.12.10 / macOS arm64 | `phase16_isolated_verify.py --mode task --build-mode compiled` with 50,000-toggle batch | 687,997 ops/sec | observation; above 200,000 floor |

The fixed-batch performance test retains the same origin-sensitive compiled
floor. The ownership-overhead delta is observational; it is not a portable
performance claim or a new scheduling guarantee.
