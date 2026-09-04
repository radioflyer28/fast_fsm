# Phase 19 Performance and Complexity Evidence

> Status: measurement collection in progress. Timing and throughput observations are
> environment-labelled; deterministic operation counters establish diagnostic
> complexity boundaries. This document intentionally contains no caller payloads,
> trace values, exception values, or object representations.

## Environment

| Property | Observation |
| --- | --- |
| Collection timestamp (UTC) | pending measurement |
| Host operating system / architecture | pending measurement |
| Python executable and version | pending measurement |
| `uv` version | pending measurement |
| pytest / Ruff / mypy / ty / Sphinx versions | pending measurement |
| Build intent for baseline collection | pending measurement |
| Build intent for asserted-pure phase gate | pending measurement |
| Build intent for fresh-compiled phase gate | pending measurement |
| `PYTHONHASHSEED` values for deterministic counter fixtures | pending measurement |

## Commands

| Order | Command | Purpose | Status |
| ---: | --- | --- | --- |
| 1 | `git show HEAD:.planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md >/dev/null` | Assert the committed evidence skeleton exists before isolation preparation. | pending measurement |
| 2 | `rg -n '19-PERFORMANCE-EVIDENCE.md' tools/phase16_isolated_verify.py` | Prove the exact skeleton path is present in `PHASE19_INVENTORY`. | pending measurement |
| 3 | `rg -n 'RED until 19-' tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py tests/test_performance_benchmarks.py` | Require that no Phase 19 strict-RED marker remains. | pending measurement |
| 4 | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q` | Run the complete diagnostic, output, and logging selection. | pending measurement |
| 5 | `uv run pytest tests/test_validation.py tests/test_visualization.py tests/test_graph_invariants.py -x -q` | Run legacy validation, rendering, and graph regressions. | pending measurement |
| 6 | `uv run pytest tests/ -x -q` | Run the sequential repository suite before baseline generation. | pending measurement |
| 7 | `uv run python tools/phase16_isolated_verify.py --suite baseline-write --manifest-output evidence/release-baseline.json` | Regenerate the baseline exclusively through the isolated pure writer and atomic export. | pending measurement |
| 8 | `git diff --check -- evidence/release-baseline.json` | Reject malformed generated manifest changes. | pending measurement |
| 9 | `git diff -- evidence/release-baseline.json` | Review the exact generated test, coverage, toolchain, and source-origin diff. | pending measurement |
| 10 | `task release-baseline-check` | Run the read-only pure-source baseline freshness check. | pending measurement |
| 11 | `PYTHONHASHSEED=0 uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'budget or sparse or dense or path or depth or cycle'` | Measure exact deterministic diagnostic boundary counters with seed 0. | pending measurement |
| 12 | `PYTHONHASHSEED=1 uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'budget or sparse or dense or path or depth or cycle'` | Confirm the same deterministic boundary behavior with seed 1. | pending measurement |
| 13 | `uv run python tools/release_evidence.py slots-policy --json` | Audit registered slot protection and measured exceptions. | pending measurement |
| 14 | `uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or trace'` | Prove disabled trace behavior and the compiled trigger floor selection. | pending measurement |
| 15 | `uv run python benchmarks/benchmark_fast_fsm.py` | Collect repository benchmark observations. | pending measurement |
| 16 | `uv run python tools/phase16_isolated_verify.py --suite phase19` | Run the authoritative asserted-pure and freshly compiled Phase 19 gate. | pending measurement |
| 17 | `uv run ruff format --check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py` | Check formatting for all Phase 19 implementation and focused test surfaces. | pending measurement |
| 18 | `uv run ruff check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py` | Check Phase 19 linting. | pending measurement |
| 19 | `task typecheck-mypy` | Run the blocking mypy/mypyc compatibility gate. | pending measurement |
| 20 | `task typecheck-ty` | Run independently visible advisory type feedback. | pending measurement |
| 21 | `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` | Build Sphinx HTML with warnings treated as errors. | pending measurement |
| 22 | `uv run sphinx-build -b doctest docs docs/_build/doctest` | Execute documentation doctests. | pending measurement |

## Module Origins

| Origin assertion | Module origin observation | Semantic selection | Status |
| --- | --- | --- | --- |
| Isolated pure baseline writer | pending measurement | baseline-write | pending measurement |
| Read-only pure baseline freshness check | pending measurement | baseline-check | pending measurement |
| Asserted pure Phase 19 temporary tree | pending measurement | diagnostics, output, logging, performance, legacy, documentation, and full suite | pending measurement |
| Freshly compiled Phase 19 temporary tree | pending measurement | diagnostics, output, logging, performance, legacy, and compiled trigger floor | pending measurement |
| Checkout native shadow | deliberately not used as Phase 19 proof | none | non-claim |

## Deterministic Budget Boundaries

All counter values are supplied by exact counted fixtures. Each pass boundary is
the observed required count; the corresponding one-less boundary must fail closed
before the forbidden work, allocation, or emission. Counts are compared across the
recorded hash seeds; timing is not used as a correctness assertion.

| Graph family / boundary | Counter or result dimension | Exact-pass observation | One-less fail-closed observation | Dense-cell / path-expansion observation | Status |
| --- | --- | --- | --- | --- | --- |
| Declared-initial reachability / snapshot capture | graph work, result count | pending measurement | pending measurement | not applicable | pending measurement |
| Self-loop, multi-member, and bridged SCCs | graph work, cycle-member results | pending measurement | pending measurement | not applicable | pending measurement |
| DAG and SCC-condensation depth | graph work, structural depth results | pending measurement | pending measurement | not applicable | pending measurement |
| Many-state zero-edge sparse graph | graph work, sparse representation | pending measurement | pending measurement | dense allocation not requested | pending measurement |
| Dense adjacency and transition compatibility output | graph work and dense cells | pending measurement | pending measurement | pending measurement | pending measurement |
| Generated branching paths | graph work, result count, path expansion | pending measurement | pending measurement | pending measurement | pending measurement |
| Structured report / JSON aggregate analysis | shared aggregate top-level work | pending measurement | pending measurement | pending measurement | pending measurement |
| Duplicate-name batch and empty comparison | positional entries and aggregate results | pending measurement | pending measurement | not applicable | pending measurement |

## Slots and Disabled Trace

| Structural or allocation contract | Command / fixture | Observation | Status |
| --- | --- | --- | --- |
| Recursive slots policy, including only registered mypyc exceptions | `uv run python tools/release_evidence.py slots-policy --json` | pending measurement | pending measurement |
| Disabled trace keeps the trigger path O(1) | `uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or trace'` | pending measurement | pending measurement |
| Default trace is metadata-only and does not expose payloads | Phase 19 logging selection and isolated Phase 19 suite | pending measurement | pending measurement |
| Custom redactor fails closed and handler ownership remains reversible | Phase 19 logging selection and isolated Phase 19 suite | pending measurement | pending measurement |

## Performance Observations

| Observation | Command / origin | Result | Status |
| --- | --- | --- | --- |
| Compiled `trigger()` floor | focused performance selection from fresh compiled origin | pending measurement; required minimum is `200000` operations/second | pending measurement |
| Disabled-trace behavior | focused performance selection from fresh compiled origin | pending measurement | pending measurement |
| Repository benchmark | `uv run python benchmarks/benchmark_fast_fsm.py` | pending measurement | pending measurement |
| Authoritative asserted-pure gate | `uv run python tools/phase16_isolated_verify.py --suite phase19` | pending measurement | pending measurement |
| Authoritative freshly compiled gate | `uv run python tools/phase16_isolated_verify.py --suite phase19` | pending measurement | pending measurement |

## Baseline Provenance

The manifest is generated only by the isolated pure `baseline-write` suite and
atomically exported to `evidence/release-baseline.json`. It is never hand-edited.

| Check | Observation | Status |
| --- | --- | --- |
| Committed inventory skeleton proved before overlay preparation | pending measurement | pending measurement |
| Isolated pure writer completed | pending measurement | pending measurement |
| Exact manifest diff reviewed for expected tests, coverage, toolchain, and source origins | pending measurement | pending measurement |
| Read-only freshness check passed after regeneration | pending measurement | pending measurement |
| Final post-gate freshness check passed | pending measurement | pending measurement |

## Phase 20 Non-Claims

- This Phase 19 evidence does not prove any installed wheel or sdist behavior.
- This Phase 19 evidence does not prove a hosted CI run or supported-version matrix.
- This Phase 19 evidence does not prove package metadata, a release tag, release assets, or publication state.
- This Phase 19 evidence does not accept a checkout native shadow as compiled proof.
- Installed-artifact parity, hosted evidence, version/tag identity, and publication remain Phase 20 work.
