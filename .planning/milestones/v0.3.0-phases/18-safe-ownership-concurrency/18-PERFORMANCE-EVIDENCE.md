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

## Final ownership release observations

These measurements were taken from fresh temporary source trees.  The helper
asserted the imported module origin for every run, so neither result can load,
delete, or replace a checkout-native shadow.  They establish release evidence,
not installed-artifact parity (that remains a later phase's concern).

| Mode | Module origin | Interpreter / platform | Workload | Observation | Policy status |
| --- | --- | --- | --- | --- | --- |
| asserted pure | fresh temporary `src/fast_fsm/core.py` | CPython 3.12.10 / macOS arm64 | 50,000 sync ownership toggles; 20,000 async toggles | 510,068.54 sync ops/sec; 352,612.42 async ops/sec | observation |
| freshly compiled | fresh temporary `src/fast_fsm/core.cpython-312-darwin.so` | CPython 3.12.10 / macOS arm64 | 50,000 sync ownership toggles; 20,000 async toggles | 686,116.94 sync ops/sec; 346,573.40 async ops/sec | compiled sync result is above the 200,000 ops/sec floor |

Each row used `phase16_isolated_verify.py --mode task --build-mode <mode>` to
create the fresh origin, then ran the stated ownership-toggle batch with the
same interpreter.  Async rates intentionally have no durable floor: they are
recorded to make the ownership path observable without inventing a scheduling
guarantee.

The regenerated release baseline records 1,379 passing pure tests, 97.89%
total source coverage, and 97.28% `core.py` coverage.  Those are fresh
baseline observations captured after the direct-control exception paths,
the async ownership observation, and the Plan 18-08 marker-isolation paths
were covered.

## Categorical Historical Provenance

This categorical summary preserves the observed source-tree facts without
reconstructing an exact invocation from the recorded command template. The
parent verifier computes the file digest and treats the entry as non-gating.

<!-- fast-fsm-historical-evidence:start -->
```json
{
  "fields": {
    "build_mode": {
      "reason": "The record contains separate asserted-pure and freshly compiled observations.",
      "searched_sources": ["original Phase 18 evidence narrative", "git log --follow -- .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md"],
      "status": "unavailable"
    },
    "command": {
      "reason": "The original evidence records a <mode> command template, not an exact executed command line and arguments.",
      "searched_sources": ["original Phase 18 evidence narrative", "git log --follow -- .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md"],
      "status": "unavailable"
    },
    "environment": {
      "citation": "Final ownership release observations results table",
      "status": "recorded",
      "value": "CPython 3.12.10 / macOS arm64"
    },
    "measurement_outcome": {
      "citation": "Final ownership release observations results table",
      "status": "recorded",
      "value": "686,116.94 sync ops/sec; 346,573.40 async ops/sec"
    },
    "original_evidence_commit": {
      "reason": "The original record does not name the commit that captured this evidence file.",
      "searched_sources": ["original Phase 18 evidence narrative", "git log --follow -- .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md"],
      "status": "unavailable"
    },
    "phase": {
      "citation": "Phase 20 fixed historical allowlist",
      "status": "recorded",
      "value": "18"
    },
    "source_path": {
      "citation": "Phase 20 fixed historical allowlist",
      "status": "recorded",
      "value": ".planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md"
    },
    "threshold_outcome": {
      "citation": "Final ownership release observations results table",
      "status": "recorded",
      "value": "compiled sync result is above the 200,000 ops/sec floor"
    }
  },
  "kind": "historical_phase_performance",
  "schema_version": 1
}
```
<!-- fast-fsm-historical-evidence:end -->
