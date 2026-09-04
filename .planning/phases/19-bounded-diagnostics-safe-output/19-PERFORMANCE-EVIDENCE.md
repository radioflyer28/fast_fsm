# Phase 19 Performance and Complexity Evidence

> Status: authoritative local gate complete. Timing and throughput observations are
> environment-labelled; deterministic operation counters establish diagnostic
> complexity boundaries. This document intentionally contains no caller payloads,
> trace values, exception values, or object representations.

## Environment

| Property | Observation |
| --- | --- |
| Collection timestamp (UTC) | `2026-09-04T03:02:00Z` |
| Host operating system / architecture | `Darwin 25.5.0 arm64` (`macOS-26.5-arm64-arm-64bit`) |
| Python executable and version | `.venv/bin/python3`; CPython `3.12.10` (Clang `20.1.0`) |
| `uv` version | `0.12.6` |
| pytest / Ruff / mypy / ty / Sphinx versions | `8.4.1` / `0.12.11` / `1.17.1` / `0.0.1-alpha.19` / `9.1.0` |
| Build intent for baseline collection | isolated `pure`; exported module origin reported as `src/fast_fsm/core.py` |
| Build intent for asserted-pure phase gate | isolated `pure`; temporary export asserted `src/fast_fsm/core.py` |
| Build intent for fresh-compiled phase gate | isolated `compiled`; temporary export asserted a freshly built `src/fast_fsm/core.*.so` |
| `PYTHONHASHSEED` values for deterministic counter fixtures | `0` and `1`; identical observed counter payloads |

## Commands

| Order | Command | Purpose | Status |
| ---: | --- | --- | --- |
| 1 | `git show HEAD:.planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md >/dev/null` | Assert the committed evidence skeleton exists before isolation preparation. | passed |
| 2 | `rg -n '19-PERFORMANCE-EVIDENCE.md' tools/phase16_isolated_verify.py` | Prove the exact skeleton path is present in `PHASE19_INVENTORY`. | passed; exact entry at line 139 |
| 3 | `rg -n 'RED until 19-' tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py tests/test_performance_benchmarks.py` | Require that no Phase 19 strict-RED marker remains. | passed; no matches |
| 4 | `uv run pytest tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py -x -q` | Run the complete diagnostic, output, and logging selection. | passed |
| 5 | `uv run pytest tests/test_validation.py tests/test_visualization.py tests/test_graph_invariants.py -x -q` | Run legacy validation, rendering, and graph regressions. | passed |
| 6 | `uv run pytest tests/ -x -q` | Run the sequential repository suite before baseline generation. | passed in the isolated pure collector; 1,476 tests, 0 failures |
| 7 | `uv run python tools/phase16_isolated_verify.py --suite baseline-write --manifest-output evidence/release-baseline.json` | Regenerate the baseline exclusively through the isolated pure writer and atomic export. | passed; isolated pure atomic export completed for 1,476 tests |
| 8 | `git diff --check -- evidence/release-baseline.json` | Reject malformed generated manifest changes. | passed; no whitespace errors |
| 9 | `git diff -- evidence/release-baseline.json` | Review the exact generated test, coverage, toolchain, and source-origin diff. | reviewed; expected Phase 19 test/coverage facts, benchmark observation, and slots inventory changed; pure source origin and toolchain stayed current |
| 10 | `FAST_FSM_BUILD_MODE=pure uv run python tools/release_evidence.py evidence --check --manifest evidence/release-baseline.json --build-wheel` | Run the read-only pure-source baseline freshness check. | passed; reported 1,476 tests, 98.00% total / 97.33% core coverage, and `src/fast_fsm/core.py` |
| 11 | `PYTHONHASHSEED=0 uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'budget or sparse or dense or path or depth or cycle'` | Measure exact deterministic diagnostic boundary counters with seed 0. | passed; 7 selected tests |
| 12 | `PYTHONHASHSEED=1 uv run pytest tests/test_diagnostic_contracts.py -x -q -k 'budget or sparse or dense or path or depth or cycle'` | Confirm the same deterministic boundary behavior with seed 1. | passed; 7 selected tests and identical counter payload |
| 13 | `uv run python tools/release_evidence.py slots-policy --json` | Audit registered slot protection and measured exceptions. | passed; three registered exceptions only; `State=40 B`, `TransitionResult=96 B` |
| 14 | `uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or trace'` | Prove disabled trace behavior and the compiled trigger floor selection. | passed; 3 selected tests from checkout pure-source origin |
| 15 | `uv run python benchmarks/benchmark_fast_fsm.py` | Collect repository benchmark observations. | passed; exited 0 without separate stdout |
| 16 | `uv run python tools/phase16_isolated_verify.py --suite phase19` | Run the authoritative asserted-pure and freshly compiled Phase 19 gate. | passed; pure and freshly compiled semantic selections, compiled trace/throughput, slots, quality, docs, full suites, and freshness all completed |
| 17 | `uv run ruff format --check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py` | Check formatting for all Phase 19 implementation and focused test surfaces. | passed in the asserted-pure gate |
| 18 | `uv run ruff check src/fast_fsm/core.py src/fast_fsm/_diagnostics.py src/fast_fsm/validation.py src/fast_fsm/visualization.py src/fast_fsm/__init__.py tests/test_diagnostic_contracts.py tests/test_output_safety.py tests/test_logging_config.py` | Check Phase 19 linting. | passed in the asserted-pure gate |
| 19 | `task typecheck-mypy` | Run the blocking mypy/mypyc compatibility gate. | passed; no issues in seven source files |
| 20 | `task typecheck-ty` | Run independently visible advisory type feedback. | passed in the asserted-pure gate |
| 21 | `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` | Build Sphinx HTML with warnings treated as errors. | passed |
| 22 | `uv run sphinx-build -b doctest docs docs/_build/doctest` | Execute documentation doctests. | passed; three doctests, zero failures |

## Module Origins

| Origin assertion | Module origin observation | Semantic selection | Status |
| --- | --- | --- | --- |
| Isolated pure baseline writer | `src/fast_fsm/core.py` in the temporary pure export | baseline-write | passed |
| Read-only pure baseline freshness check | `src/fast_fsm/core.py` in the temporary pure export | baseline-check | passed |
| Asserted pure Phase 19 temporary tree | `src/fast_fsm/core.py` in a fresh isolated export | diagnostics, output, logging, performance, legacy, documentation, and full suite | passed |
| Freshly compiled Phase 19 temporary tree | freshly built `src/fast_fsm/core.cpython-312-darwin.so` in a fresh isolated export | diagnostics, output, logging, performance, legacy, and compiled trigger floor | passed |
| Checkout native shadow | deliberately not used as Phase 19 proof | none | non-claim |

## Deterministic Budget Boundaries

All counter values are supplied by exact counted fixtures. Each pass boundary is
the observed required count; the corresponding one-less boundary must fail closed
before the forbidden work, allocation, or emission. Counts are compared across the
recorded hash seeds; timing is not used as a correctness assertion.

| Graph family / boundary | Counter or result dimension | Exact-pass observation | One-less fail-closed observation | Dense-cell / path-expansion observation | Status |
| --- | --- | --- | --- | --- | --- |
| Declared-initial reachability / snapshot capture | graph work, result count | `max_work=3`; two reachable results; one snapshot | `max_work=2` exhausts at `reachability.visit` with work/result counts `2/2` | not applicable | passed under both hash seeds |
| Self-loop, multi-member, and bridged SCCs | graph work, cycle-member results | two ordered cyclic SCCs / four members at `max_work=22` | `max_work=21` exhausts at `scc.reverse.edge` with work `21` | not applicable | passed under both hash seeds |
| DAG and SCC-condensation depth | graph work, structural depth results | 1,100-state chain has depth `1099` at `max_work=10994` | `max_work=10993` exhausts at `depth.memo.edge` | not applicable | passed under both hash seeds |
| Many-state zero-edge sparse graph | graph work, sparse representation | 128 states, 0 edges, and work `0`; no dense allocation | not applicable: this sparse projection performs no charged traversal | dense allocation not requested | passed under both hash seeds |
| Dense adjacency and transition compatibility output | graph work and dense cells | adjacency exact pass is `1089` cells; transition exact pass is `1056` cells | `1088` fails at `dense.adjacency.preflight`; `1055` at `dense.transition.preflight`, both before allocation | `1089` / `1056` cells | passed under both hash seeds |
| Generated branching paths | graph work, result count, path expansion | 32 generated paths at 32 result and 32 expansion units | `max_path_expansions=31` fails at `path.expand`; `max_results=31` fails at `path.result` | expansion/result boundaries are both `32` | passed under both hash seeds |
| Structured report / JSON aggregate analysis | shared aggregate top-level work | aggregate report exact pass at `max_work=55` | `max_work=54` exhausts at `sparse.edge` after 22 emitted results | no dense allocation in this probe | passed |
| Duplicate-name batch and empty comparison | positional entries and aggregate results | three ordered duplicate-name entries; empty result has zero counts and explicit `None` aggregates | not applicable: cardinality/schema fixtures do not exhaust a budget | not applicable | passed |

## Slots and Disabled Trace

| Structural or allocation contract | Command / fixture | Observation | Status |
| --- | --- | --- | --- |
| Recursive slots policy, including only registered mypyc exceptions | `uv run python tools/release_evidence.py slots-policy --json` | passed; `DiagnosticBudgetExceeded`, `CompiledFuncCondition`, and `TransitionError` are the three registered exceptions; all other audited production classes are slot-protected | passed |
| Disabled trace keeps the trigger path O(1) | `uv run pytest tests/test_performance_benchmarks.py -x -q -k 'trigger_min_throughput or trace'` | passed; disabled trace did not call the redactor or hostile `repr` / `str` hooks | passed from checkout pure source |
| Default trace is metadata-only and does not expose payloads | Phase 19 logging selection and isolated Phase 19 suite | focused selection and asserted-pure/fresh-compiled suites passed without payload exposure | passed |
| Custom redactor fails closed and handler ownership remains reversible | Phase 19 logging selection and isolated Phase 19 suite | focused selection and asserted-pure/fresh-compiled suites passed with fail-closed redaction and reversible handlers | passed |

## Performance Observations

| Observation | Command / origin | Result | Status |
| --- | --- | --- | --- |
| Compiled `trigger()` floor | focused performance selection from fresh compiled origin | `trigger_min_throughput` passed with its fixed minimum of `200000` operations/second | passed |
| Disabled-trace behavior | focused performance selection from fresh compiled origin | trace/redaction/payload/handler selection passed; separate checkout selection also passed three tests | passed |
| Repository benchmark | `uv run python benchmarks/benchmark_fast_fsm.py` | command exited 0 without stdout; current isolated pure baseline records `455324.16` ops/sec for 40,000 alternating `trigger()` operations | environment-labelled observation |
| Authoritative asserted-pure gate | `uv run python tools/phase16_isolated_verify.py --suite phase19` | semantic selection, slots, quality gates, docs, full suite, and freshness passed from `core.py` | passed |
| Authoritative freshly compiled gate | `uv run python tools/phase16_isolated_verify.py --suite phase19` | semantic and focused performance selections passed from a freshly built `core.*.so` | passed |

## Baseline Provenance

The manifest is generated only by the isolated pure `baseline-write` suite and
atomically exported to `evidence/release-baseline.json`. It is never hand-edited.

| Check | Observation | Status |
| --- | --- | --- |
| Committed inventory skeleton proved before overlay preparation | `git show HEAD` succeeded and the exact inventory entry is at runner line 139 | passed |
| Isolated pure writer completed | `baseline-write` exported the candidate manifest atomically | passed |
| Exact manifest diff reviewed for expected tests, coverage, toolchain, and source origins | generated diff contains 1,476 passed, 98.00% total coverage, 97.33% core coverage, the environment-labelled pure benchmark, and Phase 19 slots inventory additions; CPython 3.12.10, uv 0.12.6, and pure `src/fast_fsm/core.py` origin remain current | passed |
| Read-only freshness check passed after regeneration | direct uv freshness check completed after the write with the tracked floors satisfied | passed |
| Final post-gate freshness check passed | authoritative gate repeated the isolated read-only check at 1,476 tests, 98.00% total, 97.33% core, and `src/fast_fsm/core.py` | passed |

## Phase 20 Non-Claims

- This Phase 19 evidence does not prove any installed wheel or sdist behavior.
- This Phase 19 evidence does not prove a hosted CI run or supported-version matrix.
- This Phase 19 evidence does not prove package metadata, a release tag, release assets, or publication state.
- This Phase 19 evidence does not accept a checkout native shadow as compiled proof.
- Installed-artifact parity, hosted evidence, version/tag identity, and publication remain Phase 20 work.
