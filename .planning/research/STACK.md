# Stack Research

**Domain:** v0.5.0 explicit flat-FSM semantics and performance proof
**Researched:** 2026-09-15
**Confidence:** MEDIUM overall — repository-derived stack and integration findings are HIGH confidence; current external version and documentation findings are MEDIUM under the GSD confidence seam even though they were cross-checked against primary sources

## Recommendation in One Sentence

Keep the production and build stack unchanged, add no runtime package, isolate
`python-statemachine==2.5.0` and `python-statemachine==3.2.1` in two exact
dev-only benchmark locks, and extend the existing artifact-conformance and
installed-wheel evidence tools so the ordinary external singleton path retains
its direct lookup/execution shape and remains the only path governed by the
durable 200,000 operations/second floor.

## Required Stack Delta

| Area | Change | Why |
|------|--------|-----|
| Runtime dependencies | **None** | Final-state flags, transition mode metadata, a narrow rejection type, and termination queries need only existing core types and the standard library. The one-runtime-dependency contract stays intact. |
| Build backend/compiler | **None** | The reviewed `setuptools`/mypyc single-module build already produces pure and compiled wheels and must not be upgraded while changing lifecycle semantics. |
| Shared benchmark dependency group | Remove the floating `python-statemachine>=2.5.0` entry after version-specific runners exist | One installed distribution cannot represent both the historical and contemporary competitor. The current `uv.lock` still prefers its previously resolved 2.5.0, so a lower-bound declaration silently looks current while remaining historical. |
| Competitor fixtures | Add two exact, separately locked, dev-only runners: 2.5.0 and 3.2.1 | Exact isolation makes every comparison version-labelled and prevents a lock refresh from changing the competitor behind an old result. |
| Benchmark harness | Refactor the shared scenario/timing/report contract out of the legacy monolithic comparison script; keep version adapters thin | The same work shape, sample protocol, and JSON schema must be used across Fast FSM and both competitor versions, while allowing their public APIs to differ. |
| Artifact proof | Extend `tools/artifact_conformance.py` and the existing installed-wheel probe in `tools/release_evidence.py` | The repository already proves source/pure-wheel/compiled-wheel identity, origin, and semantic parity. New semantics should join that oracle instead of creating another packaging framework. |
| CI | Keep competitor comparison out of required CI; keep the installed compiled singleton gate | Competitor resolution and cross-library scenarios are slower and version-sensitive. The product gate is Fast FSM's own installed artifact, not another project's current performance. |

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| CPython | Project floor `>=3.10`; comparison interpreter CPython 3.12 | Runtime and common competitor execution environment | Keep the product floor. Use 3.12 for the manual comparison fixture because the historical 2.5.0 and current 3.2.1 competitor lines both declare support for it, and it matches the existing compiled benchmark CI interpreter. |
| `mypy-extensions` | Runtime requirement `>=1.0`; lock resolves 1.1.0 | Existing `@mypyc_attr` boundary | Keep as the sole runtime dependency. The new expected-rejection class can follow the existing compiled exception boundary; no exception/result library is warranted. |
| mypy + mypyc | Build/release pin 1.17.1 | Compile only `src/fast_fsm/core.py` and enforce compatible types | Keep the reviewed pin. New state/transition fields should be fixed, explicitly typed attributes; do not combine lifecycle work with a compiler upgrade. |
| setuptools | Build pin 80.9.0 | Existing selective-mypyc PEP 517 build | Keep. `setup.py` already compiles only `core.py` with `separate=False` and `multi_file=False`. |
| wheel | Build pin 0.45.1 | Pure and native artifact creation | Keep. Both artifact modes already flow through hash-, origin-, and mode-checked evidence. |
| uv | CI/evidence pin 0.12.6 | Project lock, builds, isolated benchmark execution | Keep 0.12.6 for official evidence during this milestone. A maintainer's local uv patch may be newer, but the executing version must be recorded rather than made part of the product API. |

**Confidence: HIGH.** These versions and boundaries are direct repository facts
from `pyproject.toml`, `uv.lock`, `setup.py`, CI, `Taskfile.yml`, and the release
evidence implementation.

### Runtime Representation and Fast-Path Placement

Use existing native/slotted core objects; add semantics where their cost is local:

| Feature | Representation/integration | Fast-path protection |
|---------|----------------------------|----------------------|
| Final state | Exact boolean state metadata normalized at construction; `is_terminated` reads the already-current state's flag | Reject outgoing edges from a final state during topology mutation. Do not scan outgoing topology or add a completion engine during `trigger()`. |
| Internal transition | Exact boolean or small closed transition-mode field on `TransitionEntry`, defaulting to current external behavior | Branch once after singleton/group selection. Keep the current external lifecycle method intact and route only marked transitions to a small internal lifecycle method that skips exit/entry hooks. |
| External self-transition | Existing lifecycle execution with source and target equal | Do not make self-transition behavior a machine-wide switch. Per-transition metadata must decide semantics. |
| Expected domain rejection | Existing `TransitionResult` plus one narrow built-in exception-derived signal with stable code/reason fields | Classify only when user code raises on a failure path. A successful unguarded transition must not allocate a rejection/context object or perform reflection. |

The direct path should remain:

```text
current-state dict lookup
  -> trigger dict lookup
  -> direct TransitionEntry
  -> ordinary external lifecycle
```

It must not become:

```text
lookup -> tuple/list wrapper -> topology scan -> mode strategy object
       -> unconditional context/rejection allocation -> lifecycle
```

Keep final-state validation at registration, keep termination as a current-state
property read, and keep rejection conversion inside existing exception handling.
The only new work an ordinary successful external transition should need is the
small mode discrimination needed to select the existing external executor.

**Confidence: HIGH** for architectural fit; the exact cost remains a measured
artifact observation rather than an assertion.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-statemachine` | Exactly 2.5.0 in its own script lock | Frozen historical comparison lane matching the existing Fast FSM benchmark history | Run only the legacy/common flat scenarios that the historical fixture actually models. Never call it “current.” |
| `python-statemachine` | Exactly 3.2.1 in a separate script lock | Contemporary 3.2.x comparison and semantic reference | Run the common flat baseline plus explicit final/internal/external-self scenarios that can be normalized to equivalent semantics. PyPI lists 3.2.1, released 2026-08-01, as current. |
| `transitions` | Existing benchmark constraint `>=0.9.3`; lock 0.9.3 | Optional continuity with legacy multi-library charts | Keep only for the existing broad manual comparison. It is not required to accept v0.5.0 semantics. |
| `matplotlib` | Existing `>=3.10.3`; lock 3.10.6 | Optional human-readable benchmark charts | Use only as a rendering adapter over saved JSON. Collection and pass/fail logic must not depend on it. |
| `networkx` | Existing `>=3.2`; lock is marker-resolved (3.4.2 on Python <3.11, 3.5 on >=3.11) | Existing benchmark/visual analysis support | Retain if still used by legacy comparison reports; it is not part of the hot path or the new proof contract. |

All five are **dev-only**. None belongs in `[project].dependencies`, an
installed Fast FSM wheel, or the stdlib-only installed benchmark child.

### Development Tools

| Tool | Resolved / pinned version | v0.5.0 use | Notes |
|------|---------------------------|------------|-------|
| pytest | 8.4.1 | Final-state invariants, transition-mode lifecycle ordering, rejection classification, and parity tests | Reuse current tests and markers; do not add a benchmark plugin. |
| pytest-asyncio | 1.3.0 | Sync/async semantic parity, cancellation, and rejection behavior | Internal transitions must skip async exit/entry callbacks exactly as sync ones do. |
| Hypothesis | 6.138.8 resolved | Generate finite flat graphs and operation sequences | Assert final states never publish outgoing edges, internal self-transitions preserve state and callback counts, and unrelated topology cannot affect singleton lookup. |
| Ruff | 0.12.11 resolved | Existing formatting/lint gate | No configuration change needed. |
| mypy/mypyc | 1.17.1 build pin | Blocking compilation/type gate | Run the existing `core.py` authority after every representation change. |
| ty | 0.0.1a19 resolved | Existing advisory type feedback | Keep advisory; do not make this milestone a type-tool migration. |
| Sphinx + doctest | Existing docs group | Progressive drone guide and exact API examples | Reuse `{testcode}`/`{testoutput}` and literal includes. No tutorial framework is needed. |
| `time.perf_counter` + `statistics` + `gc` | Python standard library | Existing warmup/sample/median collection | Keep the installed probe stdlib-only and checkout-independent. |

## Competitor Version and Fixture Strategy

### Exact lanes, not one floating dependency

The current declaration `python-statemachine>=2.5.0` is unsuitable for the new
evidence contract. uv's official resolution documentation says an existing lock
is retained as a preference until an upgrade is requested; that explains why
the repository still resolves 2.5.0 even though 3.2.1 exists. A floating lower
bound therefore provides neither a stable historical lane nor a guaranteed
current lane.

Recommended layout:

```text
benchmarks/
  contract.py                         # scenarios, timer, result schema
  adapters/
    fast_fsm_installed.py             # imports installed wheel only
    python_statemachine_2_5.py         # legacy API adapter
    python_statemachine_3_2.py         # current API adapter
  run_python_statemachine_2_5.py      # PEP 723: ==2.5.0
  run_python_statemachine_2_5.py.lock
  run_python_statemachine_3_2.py      # PEP 723: ==3.2.1
  run_python_statemachine_3_2.py.lock
```

Use `uv lock --script` to create each adjacent lock and `uv run --locked
--script ...` to execute it. Layer the exact freshly built Fast FSM wheel with
uv's `--with` mechanism so the Fast FSM side is an installed artifact rather
than an editable checkout. The Taskfile should own the exact command and verify
the wheel SHA/origin before any sample is accepted.

Version policy:

- `2.5.0` is immutable historical evidence. Refreshing packages must never
  change this lane.
- “Current” means an exact reviewed version at collection time: `3.2.1` as of
  2026-09-15. A future refresh changes the pin, adjacent lock, adapter tests,
  and result label together.
- Never use `>=`, `@latest`, or an unlocked ephemeral resolution in saved
  comparison evidence.
- Do not average or merge the two competitor lines. Report each distribution
  version independently.
- The historical lane establishes continuity with prior claims. It does not
  need feature-equivalent benchmarks for APIs/behaviors it cannot represent.

### Normalize semantics before timing

`python-statemachine` 3.x preserves a legacy `StateMachine` class but also adds
`StateChart` with different defaults. Its official upgrade guide says 3.x
`StateMachine` retains 2.x-style self-transition behavior while `StateChart`
uses exit/re-enter semantics. Therefore the current adapter must explicitly
choose/configure the behavior matching each Fast FSM scenario; class name alone
is not a fair semantic fixture.

For each scenario, run untimed assertions first:

1. initial/current state matches;
2. event count and final state match;
3. callback order and counts match;
4. accepted/rejected outcome category matches;
5. the measured callable performs no setup, printing, serialization, or state
   inspection not shared by the other implementation.

If equivalent semantics cannot be expressed, mark the competitor cell
`not_comparable` with a reason. Do not substitute a nearby feature and compute a
speed ratio anyway.

## Benchmark Acceptance Contract

### 1. Durable product gate — unchanged direct singleton

Keep the existing installed compiled two-state alternating trigger probe as the
only timeless absolute throughput policy:

- freshly build a wheel with `FAST_FSM_BUILD_MODE=compiled`;
- independently accept its archive, native `fast_fsm.core` origin,
  `ExtensionFileLoader`, architecture, build intent, and SHA256;
- run from a neutral temporary directory with only installed runtime
  dependencies;
- warm up 1,000 activate/deactivate pairs (2,000 operations);
- collect three samples of 20,000 pairs (40,000 operations per sample);
- validate the median from all raw samples;
- require median throughput `>=200,000 ops/sec`.

These operation/sample counts describe the current probe implementation. They
may be recalibrated deliberately if the evidence harness changes. The durable
policy is the installed compiled direct-singleton floor, not any exact observed
rate above it.

Add a structural regression test alongside the rate gate: the measured
singleton slot remains a direct `TransitionEntry`, executes without candidate
tuple iteration or graph snapshots, and its cost does not scale with unrelated
states/transitions.

### 2. Feature-local measurements — labelled, not universal floors

| Shape | Fixture | Acceptance form |
|-------|---------|-----------------|
| Final-state entry | Preconstruct a pool of identical one-shot `active -> final` machines; time only one transition per machine | Record raw samples and same-run ratio to an equivalent non-final one-shot pool. Do not mix construction into transition timing. |
| Termination query | Repeated `is_terminated` reads on non-final and final current states | Assert constant work/current-state lookup; report ns/op or ops/sec descriptively. |
| External self-transition | One-state machine whose exit and entry callbacks increment preallocated counters | Assert exit then entry on every event; record callback-inclusive samples. |
| Internal self-transition | Same state and payload/action shape, but mode suppresses exit and entry | Assert neither lifecycle callback runs and state identity is unchanged; record feature-local samples. |
| Expected rejection | A selected transition intentionally raises the narrow domain-rejection signal | Assert expected category/code, no commit, correct history/observer behavior, and no lower-priority fallthrough; report failure-path latency/allocation separately. |
| Guard false | Existing ineligible guard fixture | Keep distinct from expected rejection so priority fallthrough remains measurable and correct. |
| Unexpected callback failure | Existing stage-aware lifecycle fixture | Confirm it remains distinct from domain rejection and retains cause/stage behavior. |

For every row, record pure source/pure installed/compiled installed semantic
parity. Performance acceptance for v0.5.0 should be:

- hard fail if the installed compiled singleton floor or direct representation
  is lost;
- hard fail on semantic/callback/result mismatch in any artifact mode;
- hard fail if unrelated topology changes a singleton's work shape;
- require feature-local raw samples and same-run ratios to be captured and
  environment-labelled;
- do not invent permanent absolute floors for final, internal, or rejection
  paths before stable cross-run evidence exists.

### 3. Competitor comparison — manual descriptive evidence

Run the historical and contemporary competitor lanes through `task
benchmark-compare`; do not place either in required CI. At minimum compare the
common unguarded flat transition. Compare final/internal/external-self behavior
only against the contemporary lane after semantic normalization.

Every saved result must include:

| Field group | Required fields |
|-------------|-----------------|
| Fast FSM artifact | wheel filename, SHA256, distribution/package version, commit, asserted/classified mode, core origin, core loader |
| Competitor | distribution name, exact version, runner lock digest, adapter identifier |
| Runtime | Python implementation and full version, OS/platform, machine architecture, uv version |
| Measurement | scenario ID/version, operations per sample, warmup operations, raw samples, median, best sample, unit, GC policy |
| Semantics | initial/final state facts, callback counts/order, expected outcome category, comparability status/reason |
| Provenance | exact command, UTC timestamp, dirty/clean checkout state or commit identity |

Use `time.perf_counter` for short wall-clock durations. Python's official docs
recommend repetitions because system activity affects results and note that
baseline overhead exists. Preserve all raw samples; median remains the project
gate statistic, while best sample may be displayed as an additional descriptive
value. Never publish a ratio without both underlying observations and their
environment/version labels.

## Integration Points

| Existing seam | Required v0.5.0 work | Why reuse it |
|---------------|----------------------|--------------|
| `src/fast_fsm/core.py` | Add fixed state/transition metadata, internal lifecycle branch, termination query, and narrow rejection mapping | It is already the single mypyc unit and owns registration, selection, lifecycle, result, history, and sync/async execution. |
| `tools/artifact_conformance.py` | Add explicit scenario families/records for final state, internal/external self-transition, and expected rejection | It imports only installed Fast FSM plus stdlib and already prevents pure/compiled shared-wrong parity through required values. |
| `tools/release_evidence.py` | Preserve the current singleton sampler; optionally generalize the installed child to emit additional descriptive feature rows after identity acceptance | It already binds measurements to an accepted artifact SHA, loader, mode, commit, time, and environment. |
| `tests/test_performance_benchmarks.py` | Lock the unchanged singleton fixture and add topology-independence/feature-row schema tests | Existing slow CI gate and instrumentation checks live here. |
| `tests/test_installed_artifacts.py` | Validate new conformance records and reject detached/malformed feature evidence | Existing tests already validate sample count, finiteness, median, native loader, and artifact binding. |
| `benchmarks/benchmark.py` | Replace ad hoc single timing and mutable JSON output with orchestration over the shared contract/version adapters | Current script times broad application setup and scenarios with one aggregate duration; that is useful as a demo but insufficient as release-quality semantic evidence. |
| `benchmarks/benchmark_py_fsm.py` | Split/version the adapter rather than importing whichever `statemachine` happens to be installed | The existing module does not prove which competitor release supplied the API. |
| `Taskfile.yml` | Keep `benchmark-compare` manual; make it build/verify a compiled wheel and invoke both exact locked lanes | Gives maintainers one reproducible entry point without slowing or destabilizing CI. |
| `.github/workflows/ci.yml` | Keep the current compiled singleton job and locked setup | No competitor job is needed. Only Fast FSM's own floor is a release gate. |
| Sphinx/doctest + example smoke tests | Extend the existing controller-owned drone progression | Documentation parity belongs to existing tested docs, not a new example runner or simulator dependency. |

## Installation and Execution Shape

No production installation change:

```bash
uv sync --locked
```

Existing development and artifact gates remain:

```bash
uv sync --locked --all-groups
uv run mypy src/fast_fsm/core.py
uv run pytest tests/ -x -q
task release-installed-artifacts-check
task release-installed-performance-check
```

The future `task benchmark-compare` should encapsulate the exact commands for
building/verifying the compiled wheel and invoking both locked PEP 723 runners.
Do not require maintainers to mutate the shared `.venv` between competitor
versions.

## Alternatives Considered

| Recommended | Alternative | Why Not / When Alternative Fits |
|-------------|-------------|---------------------------------|
| Existing stdlib sampler + evidence validator | Add `pyperf` | `pyperf` is useful for a standalone benchmarking laboratory, but it would add a tool and result format without replacing artifact-origin, semantic, and release-identity checks. Reconsider only if CPU affinity/calibration becomes a demonstrated source of unusable evidence. |
| Existing pytest tests with explicit sampler helpers | Add `pytest-benchmark` | Plugin thresholds would couple correctness runs to noisy timing and would not solve competitor isolation or installed-wheel proof. |
| Two exact PEP 723 script locks | One shared `python-statemachine>=2.5.0` dependency | A lower bound plus existing lock preference can remain on 2.5.0 indefinitely and cannot install two versions simultaneously. |
| Exact contemporary pin refreshed deliberately | `python-statemachine@latest` on every run | Floating “latest” destroys result reproducibility and can change behavior between collection and review. |
| Installed compiled Fast FSM wheel | Editable checkout or in-place extension | An in-tree extension can shadow source and does not prove what users install. |
| Shared semantic contract with version adapters | Reuse the legacy aircraft wrapper unchanged for both versions | 3.x introduced statechart behavior/default distinctions; identical source text does not guarantee identical measured semantics. |
| Preserve external lifecycle method and branch to internal | Strategy objects/callback pipelines for every transition | Adds indirection/allocation to the common path and complicates mypyc. |
| Current `TransitionResult` plus narrow rejection signal | New result/validation framework dependency | Duplicates the established stage-aware contract and taxes a small semantic addition with a new runtime surface. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Any new runtime dependency | Violates the minimal-runtime identity for functionality expressible in existing core types | Standard library plus `mypy-extensions` only |
| A mypy/mypyc, setuptools, wheel, or backend upgrade in this milestone | Compiler/build changes would confound semantic and performance regressions | Keep reviewed pins; schedule upgrades independently |
| `pytest-benchmark`, `pyperf`, ASV, or BenchmarkDotNet-style infrastructure now | Adds collection/config/result machinery without covering artifact identity or semantic equivalence | Extend current stdlib sampler and evidence schema |
| A global self-transition mode | Intent belongs to each transition and a global flag makes mixed machines impossible | Immutable per-transition mode metadata |
| A completion queue, eventless loop, scheduler, or async task supervisor | Changes the engine category and imposes work unrelated to explicit flat semantics | Current explicit caller/controller event ownership |
| Runtime graph snapshots, validators, serialization, or visualization calls in dispatch | Would make ordinary transition cost depend on topology/tooling | Registration-time validation and opt-in diagnostics |
| Dispatch-time signature inspection or context allocation | Conflicts with predictable mypyc hot-path cost | Existing explicit callbacks and failure-only rejection mapping |
| Competitor benchmarks in required CI | Network/package drift and cross-project performance are not Fast FSM release invariants | Manual exact locked comparison task |
| Exact observed Fast FSM or competitor rates in long-lived policy/docs | Hardware, Python, OS, and load change them | Keep only the compiled singleton floor; label all observations |

## Stack Patterns by Variant

**Ordinary external singleton transition:**

- Direct nested dictionary lookup and direct `TransitionEntry` dispatch.
- Existing external lifecycle executor.
- No final/rejection/context object allocation and no topology scan.

**Internal self-transition:**

- Same direct lookup/selection representation.
- One immutable mode check routes to a small executor that omits exit/enter.
- Feature-local cost is paid only by the selected transition.

**Final-state query:**

- Read current state's immutable final flag.
- Validate outgoing-edge prohibition during construction, not query/dispatch.

**Expected domain rejection:**

- Raise the narrow intentional signal from the approved validation/action seam.
- Convert it into the existing structured result only on the exception path.
- Guard `False` still means candidate ineligibility/fallthrough; unexpected
  exceptions still mean stage-aware execution failure.

**Release performance proof:**

- Fresh compiled wheel, neutral install, verified loader/origin/hash.
- Existing fixed warmup, raw samples, and median floor.

**Competitor comparison:**

- Exact version-specific isolated lock.
- Untimed semantic oracle before timing.
- Manual JSON evidence with adapter and environment labels.

## Version Compatibility

| Package / tool | Compatible with | Notes |
|----------------|-----------------|-------|
| Fast FSM v0.5.0 target | CPython `>=3.10` | Do not raise the project floor. CI already covers 3.10–3.14 for Fast FSM itself. |
| `python-statemachine==2.5.0` | Python 3.7–3.13 per its official release notes | Use CPython 3.12 in comparisons; do not attempt the historical lane on the project's 3.14 CI cell. |
| `python-statemachine==3.2.1` | Python `>=3.10` per PyPI | Current 3.2.x lane as of research date. 3.2.1 supersedes 3.2.0 and is a security fix for its optional document IO layer; the benchmark should still install only the base package. |
| mypy/mypyc 1.17.1 | Current `setup.py` single-module configuration | Keep `core.py` as one compilation unit; interpreted extension surfaces remain outside it. |
| `mypy-extensions>=1.0` / 1.1.0 resolved | Pure and compiled Fast FSM wheels | Sole runtime dependency. |
| uv 0.12.6 evidence pin | Project `uv.lock` and PEP 723 script locks | Record the executing uv version. Do not hand-edit any uv lockfile. |
| setuptools 80.9.0 + wheel 0.45.1 | mypyc 1.17.1 build | Existing exact build/release trio; no milestone-local upgrade. |

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Runtime/build stack unchanged | HIGH | Direct repository metadata, build code, CI, and validated artifact tests |
| Fast-path integration points | HIGH | Direct inspection of `TransitionEntry`, selection, lifecycle, release sampler, and artifact oracle |
| Benchmark fixture/version strategy | MEDIUM | Repository gap is direct; uv behavior and current competitor facts are primary-source but classified MEDIUM by the research seam |
| `python-statemachine` current version/API | MEDIUM | Cross-checked official PyPI, release notes, upgrade guide, and API/transition docs |
| Exact feature-local performance | LOW until implemented | No rates were invented; must be measured on source/pure/compiled artifacts |

## Sources

### Repository sources (HIGH confidence)

- `pyproject.toml` and `uv.lock` — runtime/build/dev boundaries and resolved versions
- `setup.py` — selective `core.py` mypyc compilation
- `src/fast_fsm/core.py` — direct singleton representation, candidate groups, lifecycle seam
- `tools/release_evidence.py` — installed compiled artifact identity, sampler, raw samples, median, and 200,000 ops/sec floor
- `tools/artifact_conformance.py` — checkout-independent semantic oracle
- `Taskfile.yml` and `.github/workflows/ci.yml` — manual comparison task and required compiled benchmark gate
- `benchmarks/benchmark.py` and `benchmarks/benchmark_py_fsm.py` — current comparison limitations

### Primary external sources (MEDIUM confidence after cross-check)

- [python-statemachine on PyPI](https://pypi.org/project/python-statemachine/) — current 3.2.1 release, upload date, Python `>=3.10`, base/extras metadata
- [python-statemachine 2.5.0 release notes](https://python-statemachine.readthedocs.io/en/v2.5.0/releases/2.5.0.html) — historical date and Python support
- [python-statemachine 3.2.1 GitHub release](https://github.com/fgmacedo/python-statemachine/releases/tag/v3.2.1) — current patch/security release provenance
- [Upgrading python-statemachine 2.x to 3.0](https://python-statemachine.readthedocs.io/en/v3.2.1/releases/upgrade_2x_to_3.html) — `StateMachine` compatibility defaults, `StateChart` behavior, termination API, and migration differences
- [python-statemachine 3.2.1 transitions](https://python-statemachine.readthedocs.io/en/v3.2.1/transitions.html) — final/internal/external-self semantics in the exact contemporary fixture
- [uv running commands](https://docs.astral.sh/uv/concepts/projects/run/) — exact `--with` versions and isolated script behavior
- [uv running scripts](https://docs.astral.sh/uv/guides/scripts/) — PEP 723 adjacent lockfiles and locked script execution
- [uv resolution](https://docs.astral.sh/uv/concepts/resolution/) — existing lock entries as version preferences
- [Python `timeit`](https://docs.python.org/3/library/timeit.html) — repetitions, system noise, best observation, and baseline overhead
- [Python `time.perf_counter`](https://docs.python.org/3/library/time.html#time.perf_counter) — high-resolution monotonic short-duration clock
- [mypyc native classes](https://mypyc.readthedocs.io/en/stable/native_classes.html) — fixed attributes, non-native boundary, and interpreted subclass cost
- [mypyc compilation units](https://mypyc.readthedocs.io/en/stable/compilation_units.html) — early binding within one unit and slower late binding across units

## Open Questions for Phase Planning

- Which exact callback/action seam is permitted to raise expected domain
  rejection? This changes conformance cases but does not justify a new package.
- Should feature-local installed measurements live in the release manifest or a
  separate non-authorizing benchmark JSON? Keep the singleton gate authoritative
  either way.
- Does the historical 2.5.0 adapter expose a truly equivalent internal
  transition? If not, mark that cell `not_comparable`; do not emulate it with
  controller code.
- After initial v0.5.0 measurements, are any feature-local ratios stable enough
  to warrant a future regression budget? Do not set one before evidence.

---
*Stack research for: Fast FSM v0.5.0 Explicit Flat-FSM Semantics*
*Researched: 2026-09-15*
