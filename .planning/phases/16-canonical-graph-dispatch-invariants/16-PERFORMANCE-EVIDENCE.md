---
phase: 16
plan: 01
status: before-change
---

# Phase 16 Plan 01 — Before-Change Performance Evidence

This record captures environment-labelled observations before canonical graph
semantics change. Each observation is collected by
`tools/phase16_isolated_verify.py` from a fresh export of committed `HEAD` plus
only the listed working-tree overlays. The developer checkout's native shadows
are not imported, deleted, or used as evidence.

## Environment

- Collected: 2026-08-30
- Committed baseline tree: `31f90e5` (`docs(16): create phase plan`)
- Python: CPython 3.12.10 (arm64 macOS)
- Runner: `tools/phase16_isolated_verify.py` task mode, with only this evidence
  record and the runner overlaid onto the exported committed tree.

## Observations

| Build mode | Asserted `fast_fsm.core` origin | Targeted transition baseline | `trigger()` observation | History disabled |
| --- | --- | --- | ---: | --- |
| pure | `src/fast_fsm/core.py` | pass | 851,576 ops/s | yes |
| compiled | `src/fast_fsm/core.cpython-312-darwin.so` | pass | 1,054,438 ops/s | yes |

The two-state `quick_build()` toggle was warmed for 1,000 transitions and then
measured across 100,000 alternating `trigger()` calls. These are labelled local
observations, not a new policy threshold. The selected contexts created distinct
temporary repositories; the developer checkout's native artifacts were neither
deleted nor imported.

## Post-Semantic Clean Pure Baseline

- Collected: 2026-08-30
- Committed tree: `07b655e` (`fix(16-05): isolate full phase evidence inventory`)
- Context: a committed-HEAD export with the explicit Phase 16 overlay inventory
  in `tools/phase16_isolated_verify.py`: `core.py`, interpreted condition
  modules, graph/builder/async/guard/template/history/performance/mypyc tests,
  the core SPR, both maintainer guides, baseline manifest, and this evidence
  record.
- Build intent and asserted origin: `FAST_FSM_BUILD_MODE=pure` selected before
  locked setup; `fast_fsm.core` resolved to `src/fast_fsm/core.py` before
  release evidence collection.

### Commands and Results

```bash
uv run python tools/phase16_isolated_verify.py \
  --suite baseline-write --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
```

The write suite completed from the asserted pure temporary archive and copied
only the generated manifest back atomically. The second command created a new
asserted-pure archive, overlaid the committed manifest, and passed read-only
freshness without changing it.

| Observation | Result |
| --- | --- |
| Pure semantic inventory | 985 collected / 985 passed / 0 failed / 0 errors / 0 skipped |
| Source coverage | 96.01% total; 93.94% `core.py` |
| Source origin | `src/fast_fsm/core.py` |
| Wheel evidence | `fast_fsm-0.2.2-py3-none-any.whl`; pure tags only; no native members |
| Slots audit | Passed; added slot-protected `_GraphTransition`, `_GraphSnapshot`, `_PreparedTransition`, and `_PreparedDispatch` to the reviewed inventory |
| Pure trigger observation | 795,843.04 ops/s across 40,000 operations after 2,000 warmups (CPython 3.12.10, arm64 macOS) |

### Reviewed Manifest Delta

Compared with the prior Phase 15 baseline, the exact suite grew from 879 to
985 passing tests and coverage moved from 95.75% total / 92.95% core to
96.01% total / 93.94% core. The pure source origin, wheel identity,
schema, package/build pins, zero failures/errors, and 200,000 ops/s compiled
policy floor stayed unchanged. The timing observation changed only as an
environment-labelled measurement, from 951,787.04 to 795,843.04 ops/s; it is
not a freshness field.

### Evidence-Integrity Correction

Plan text referred to `--export-baseline`, but the committed helper exposes
`--manifest-output`; the current interface was used. During this task the
helper was also corrected to overlay both Phase 16 maintainer guides and the
baseline manifest during isolated collection. This closes the working-tree
docs/evidence provenance gap without importing or deleting developer native
shadows.

## Final Pure/Compiled Parity and Freeze Gate

- Collected: 2026-08-30
- Exact committed source tree: `08e1bc1b3ec39775f5af1a191d4efeb4cd9e5832`
  (`docs(16-05): record clean pure baseline evidence`)
- Environment: CPython 3.12.10; arm64; macOS 26.5 arm64; `uv` 0.12.6.
- Isolation: each mode exported that committed `HEAD` into its own temporary
  archive and overlaid the inventory below. Pure mode asserted `.py` origin
  before imports; compiled mode built native code successfully and asserted the
  native module origin before imports. No developer native shadow was removed
  or imported.

### Blocking Commands

```bash
uv run python tools/phase16_isolated_verify.py --suite phase16
task typecheck-mypy
```

The canonical suite passed its identical graph, builder, async, guard,
condition-template, declarative/history, and mypyc semantic command in both
asserted modes. It then passed the compiled trigger/history performance command
and, in a separate asserted-pure archive, the full release gate: source-origin
preflight, Ruff formatting/lint, mypy, all 985 tests, Sphinx HTML, Sphinx
doctests, and read-only release-baseline freshness. The separate blocking mypy
command also passed with no issues in six source files.

| Mode | Asserted `fast_fsm.core` origin | Operations / warmup / repeats | Elapsed | Observed `trigger()` rate | Result |
| --- | --- | --- | ---: | ---: | --- |
| pure | `src/fast_fsm/core.py` | 100,000 / 1,000 / 1 | 0.134195 s | 745,186.56 ops/s | semantic suite + release gate passed |
| compiled | `src/fast_fsm/core.cpython-312-darwin.so` | 100,000 / 1,000 / 1 | 0.104330 s | 958,497.84 ops/s | semantic/performance suite passed; ≥200,000 floor |

The microbenchmark constructed the same two-state `quick_build()` toggle in
each asserted context, performed the warmup, collected garbage, and timed only
the alternating `trigger("toggle")` loop. Relative to the before-change local
observation, the pure value is -12.49% and the compiled value is -9.10%; both
remain environment-labelled observations rather than new policy values. The
only durable performance contract is the compiled 200,000 ops/s floor, which
the native performance tests and direct observation both clear.

### Advisory Typecheck Evidence

The advisory command was intentionally invoked through `subprocess.run` with
captured stdout/stderr and `check=False`; it did not control task completion.

```text
command: task typecheck-ty
exit status: 0
stdout:
All checks passed!

stderr:
task: [typecheck-ty] uv run ty check src/fast_fsm/
WARN ty is pre-release software and not ready for production use. Expect to encounter bugs, missing features, and fatal errors.
```

### Overlay Inventory SHA-256

```text
288d6344e905b0724c87c33f8af39d87b09d2d1397e72d190e4971fb68318252  tools/phase16_isolated_verify.py
a6a1affc32cb3dc7cbfdff87bbd8d00054f4ba5c7ffa3155beda0fc357ad984b  src/fast_fsm/core.py
9c1cdafb6d9837b41e053a492d1706a43059828ba21b0bdc1813f10d6f9b489f  src/fast_fsm/conditions.py
5e6f32fb96e9ccadc2235668a07ee78add09372d497fa22ae06e4cf09ff32a64  src/fast_fsm/condition_templates.py
9055c4f3e64169254781f657d4612ee6983a423e5dbc00b1043c583346936e22  tests/test_graph_invariants.py
bd3cfdd5532bbdc19f6cfa1a50010d535b32d336486e62244f1cb3c78e05484c  tests/test_builder.py
37ff078106f2150d5bdf1bdea2273c2655e54463e86b817c77d216f4f56d7de8  tests/test_async.py
b09ef1af5aef7982c7129ed05638a91a4ca9d247ec0d5f876c254f837cc2d310  tests/test_safety_kwargs.py
fa0065fe6d7e487acb4e76d7cb6425ed8885858d64b99bb5bbe747e8e14ed806  tests/test_condition_templates.py
1e87ca686e06d7cdf877fb7a375ffda77a360d061a53d927bdbc7641cfed2c5e  tests/test_advanced_functionality.py
80843df82b821a661c657a996827ecac6959ccb595bc6b81a20655671f5fc8b6  tests/test_mypyc_guard.py
0ec0e484cbdf436c3256da966b7517ce7b3b463005ce12196e51360918e92f8a  tests/test_performance_benchmarks.py
c8c0a942628bbd95817fb8977fe2ab8fbc5c30221b0789881e4486f827a7f6af  .specify/memory/spr-core-api.md
8a59b42ffb63cdc6cf46fd926440e0725e27cb4d1487a08eb30662c4b58fdb7a  docs/dev/architecture.md
ee0d5cb49a57dddca17fcf8408bfa2fda157b1e897f0b6e3b7c8af3f84e45a13  docs/dev/testing.md
1e34958020f064941581b186dc778b6760665e931250e1a0eb51956220eb7eb7  evidence/release-baseline.json
2fa5c720a38ea04560b80ac02aa3c2363279a66e9b94062eedcb51c7c875b433  .planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md
```

This is source-tree proof only. It does not make an installed-wheel or
publication-parity claim (Phase 20), publish a topology format (FUTR-05), or
define Phase 17 lifecycle, Phase 18 ownership, or Phase 19 diagnostics/output
contracts.

## Review-Remediation Parity Evidence

- Collected: 2026-08-30
- Committed source tree: `233fb65` (`docs(16): WR-03 correct builder architecture example`), with the refreshed release manifest overlaid for the final read-only check.
- Isolation: `tools/phase16_isolated_verify.py` exported a fresh temporary
  checkout for every context. Pure contexts asserted
  `src/fast_fsm/core.py`; compiled contexts built and asserted the native
  `fast_fsm.core` extension. No developer native shadow was imported or
  removed.

The review remediation added `tests/test_boundary_negative.py` to both the
Phase 16 fixed inventory and the identical pure/compiled semantic command.
The following final command passed:

```bash
uv run python tools/phase16_isolated_verify.py --suite phase16
```

It passed the expanded semantic matrix in both asserted origins, the compiled
trigger/history performance cases, and the asserted-pure release gate
(formatting, lint, mypy, full tests, Sphinx HTML/doctests, and freshness).
The regenerated pure release baseline independently passed in a second
temporary checkout with 1,007/1,007 tests passing, 96.08% total source
coverage, and 94.27% `core.py` coverage. The compiled performance contract
remains the existing 200,000 `trigger()` operations/second floor, which its
native test cases passed; timings remain environment-labelled rather than a
new policy threshold.

## Review-Fix Iteration 2 Evidence

- Collected: 2026-08-30
- Source commits: `d63e6c5` (CR-01), `8c804ce` (CR-02), and `c2d0c22`
  (CR-03).
- Verification environment: the isolated review-fix worktree. Every
  origin-sensitive command then exported its own fresh temporary repository;
  pure contexts asserted `src/fast_fsm/core.py`, while compiled contexts built
  and asserted the native `fast_fsm.core` extension. No developer native
  shadow was imported or removed.

The remediation preserves overridden declarative policy hooks after canonical
guard preparation, validates every supported graph before builder staging in
every mode, and classifies/awaits asynchronous callable guards. Focused pure
and compiled regression contexts passed the 16 combined CR-01/CR-03 cases,
including reject/raise/`super()` policies and true/false/raising callable
guards with exact-once and no-`RuntimeWarning` assertions.

```bash
uv run python tools/phase16_isolated_verify.py --suite baseline-write \
  --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
uv run python tools/phase16_isolated_verify.py --suite phase16
task typecheck-mypy
task typecheck-ty
```

The refreshed pure baseline and its separate freshness check passed with
1,053/1,053 tests, 95.68% total source coverage, and 93.75% `core.py`
coverage. The canonical Phase 16 suite also passed its identical semantic
matrix in fresh pure and compiled origins, the compiled performance/history
tests (including the existing 200,000 `trigger()` operations/second floor),
and the asserted-pure release gate: source-origin preflight, Ruff format/lint,
mypy, full tests, Sphinx HTML/doctests, and baseline freshness. The standalone
blocking mypy and advisory ty checks both passed.

## Review-Fix Iteration 3 Evidence

- Collected: 2026-08-30
- Context: the isolated review-fix worktree, followed by fresh temporary
  archives for every origin-sensitive command. Pure contexts asserted
  `src/fast_fsm/core.py`; compiled contexts built and asserted the native
  extension. No developer-checkout native shadow was imported, deleted, or
  used as evidence.

The baseline writer now reads the existing manifest's total and `core.py`
coverage values before copying a generated replacement. A lower value fails
closed without replacing the destination unless the invocation names an
explicit `--coverage-floor-migration` JSON record with matching old/new values
and non-empty review metadata. Regression tests prove both the no-replacement
failure path and the explicitly reviewed migration path.

After focused direct-guard, async-classification, builder-validation, and
factory-identity tests restored coverage above the previous floors, the
following commands regenerated and then independently checked the baseline:

```bash
uv run python tools/phase16_isolated_verify.py --suite baseline-write \
  --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
```

The asserted-pure baseline contains 1,067/1,067 passing tests, 96.16% total
source coverage, and 94.50% `core.py` coverage. Those values exceed the prior
96.08% total and 94.27% core floors; the subsequent read-only check verifies
that no fresh collection can change the committed manifest.

## Review-Fix Cycle 2 — Critical Manifest and Guard Corrections

- Collected: 2026-08-30
- Source commits: `0b92c25` (CR-01), `cdc8974` (CR-02), and `c68bab2`
  (CR-03), before the refreshed manifest was committed.
- Isolation: every import-bearing command created a fresh temporary archive
  from committed `HEAD`. Pure contexts asserted `src/fast_fsm/core.py` before
  tests; compiled contexts built and asserted the native
  `fast_fsm.core.cpython-312-darwin.so` extension. The developer checkout's
  native shadows were neither imported nor removed.

The async evaluator now retains the direct callable fast path only for the
exact built-in `FuncCondition`; public subclasses use their effective `check()`
method at a dynamic boundary so an override may reject, raise, or return an
awaitable under both interpreter and mypyc dispatch. The manifest publisher
uses an unpredictable exclusive same-directory temporary file, flushes and
fsyncs it before replacement, and cleans it up on all failure paths. Coverage
parsing now accepts only JSON `int`/`float` values that are non-boolean, finite,
and within the raw inclusive 0–100 range; the same rule applies to existing,
generated, and reviewed migration manifests before rounding or replacement.

| Evidence | Asserted pure | Asserted compiled |
| --- | ---: | ---: |
| CR-01 direct/machine subclass regressions (reject, raise, awaitable) | 7 passed | 7 passed |
| CR-02 predictable-symlink victim/replace-cleanup regressions | 4 passed | 4 passed |
| CR-03 malformed existing/generated/migration manifests and byte preservation | 59 passed | 59 passed |
| Full Phase 16 semantic matrix | passed | passed |
| Compiled trigger/history performance selection | n/a | 3 passed; existing ≥200,000 ops/s contract held |

The first full suite intentionally stopped at the read-only freshness check:
the expanded regression set changed the evidence observation from 1,067 to
1,129 passing tests and raised coverage from 96.16% / 94.50% to 96.21% /
94.57% (total / `core.py`). Its pure and compiled semantic matrices and the
compiled performance selection had already passed. Only after those semantic
and static gates, `task typecheck-mypy`, and advisory `task typecheck-ty` exited
successfully was the manifest regenerated through the isolated write command:

```bash
uv run python tools/phase16_isolated_verify.py --suite baseline-write \
  --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
uv run python tools/phase16_isolated_verify.py --mode task --build-mode pure \
  --include evidence/release-baseline.json -- task release-gate
```

The refreshed manifest records 1,129/1,129 tests, 96.21% total source
coverage, 94.57% `core.py` coverage, and a local pure `trigger()` observation
of 682,293.08 ops/s. Its independent asserted-pure freshness check and the
full pure release gate both passed (source-origin preflight, Ruff format/lint,
mypy, all tests, Sphinx HTML/doctests, and baseline freshness). Mypy reported
no source issues. Ty exited successfully with two non-blocking
redundant-`Any`-cast diagnostics at the intentionally dynamic mypyc
awaitability boundaries.

## Review-Fix Cycle 3 — Full Gate Evidence

- Collected: 2026-08-30
- Source commits: `1fbf93a` (CR-01), `c380603` (CR-02), `7085c43`
  (CR-03), `8ccf6b2` (CR-04), `bc058d9` / `13c02ca` / `1babec8` /
  `c96eff2` / `2fe4af4` (CR-05 follow-through), and `1bad2f0` (WR-01).
- Context: source changes were committed in the isolated review-fix worktree.
  Every import-bearing check exported a fresh archive; pure runs asserted
  `src/fast_fsm/core.py` and compiled runs built and asserted the temporary
  native extension. No checkout-native shadow was used as test evidence.

The manifest publisher now validates the generated JSON before *every* write,
including the first destination, rejects non-finite constants and malformed
test counters, rejects leaf symlinks without resolving the destination, and
restores either the prior mode or the repository umask-derived mode before
atomic replacement. Its durable floor tracks coverage and strict collected /
passed / failed / errors counts together, with a reviewed schema-v2 migration
record required for an intentional reduction.

After the strict writer and an independent read-only check both passed, the
final manifest records 1,164/1,164 pure tests, 96.29% total source coverage,
and 94.71% `core.py` coverage. The final suite completed with an explicit
`PHASE16_FULL_SUITE_EXIT=0`:

```bash
uv run python tools/phase16_isolated_verify.py --suite baseline-write \
  --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
uv run python tools/phase16_isolated_verify.py --suite phase16
task typecheck-mypy
task typecheck-ty
```

That final suite passed fresh pure and compiled semantic matrices, the compiled
performance selection (3 tests), and the asserted-pure release gate: source
origin, Ruff format/lint, mypy, 1,164 tests, Sphinx HTML/doctests, and
baseline freshness. Mypy passed without errors. Ty exited 0 with only its two
pre-existing redundant-`Any`-cast advisory diagnostics at the dynamic
awaitability boundaries.

## Review-Fix Cycle 3 — Iteration 2 Evidence

- Collected: 2026-08-30
- Source commits: `b5910ab` (CR-01 callable classification), `85eb72e`
  (CR-03 atomic builder mode publication), `26a8f35` / `7ce6c33` (CR-02
  descriptor-anchored manifest publication and its structural guard),
  `449750f` (WR-01 no-global-umask publication), and `fc53c36` (CR-01
  compiled sync-boundary follow-through).
- Context: fixes were committed in the isolated review-fix worktree. Every
  import-bearing semantic command exported a new temporary repository; pure
  contexts asserted `src/fast_fsm/core.py`, and compiled contexts built and
  asserted `fast_fsm.core.cpython-312-darwin.so`. Checkout-native shadows were
  neither imported nor removed.

The manifest publisher now anchors parent traversal, validation, temporary
creation, rename, and directory fsync to a single no-follow descriptor below
the repository root. Platforms without the required descriptor operations fail
closed. The adversarial parent-swap regression proves that publication remains
in the already-opened in-repository directory and leaves the outside victim
directory unchanged. New files keep their payload at mode `0600` while an
exclusive descriptor-anchored empty probe captures the caller's normal output
mode without mutating process-global `umask`; a synchronized concurrent-file
test covers that safety property.

The first baseline write correctly failed closed, without changing the tracked
manifest, when total coverage measured 96.28% below the reviewed 96.29% floor.
Additional CR-01 runtime coverage exercised the exact compiled callable and an
overridden asynchronous `check()` through sync dispatch; the latter now stays
at the dynamic mypyc boundary long enough to close and reject the coroutine.
The final write and independent read-only check passed with 1,175/1,175 tests,
96.37% total source coverage, and 94.85% `core.py` coverage.

```bash
uv run python tools/phase16_isolated_verify.py --suite phase16
task typecheck-mypy
task typecheck-ty
uv run python tools/phase16_isolated_verify.py --suite baseline-write \
  --manifest-output evidence/release-baseline.json
uv run python tools/phase16_isolated_verify.py --suite baseline-check
```

Fresh pure and compiled semantic matrices passed, as did the compiled
trigger/history selection (3 tests). Mypy passed with no errors. Ty exited 0
with four advisory redundant-`Any`-cast diagnostics at the intentional dynamic
awaitability boundaries. The asserted-pure release gate components also passed
from a retained fresh export: source-origin preflight, Ruff format/lint, mypy,
the full test suite, Sphinx HTML, three doctests, and a direct
`release_evidence.py evidence --check --build-wheel` freshness check. The
environment's 30-second command host cut off the monolithic task wrapper, so
the evidence records its independently successful component exits rather than
claiming an unobserved wrapper exit code.
