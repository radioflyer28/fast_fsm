# Stack Research

**Domain:** Hardening an existing high-performance Python FSM library
**Researched:** 2026-08-29
**Confidence:** MEDIUM — repository findings are direct; current-version and ecosystem claims were verified against primary sources but the research seam classifies web-sourced evidence as MEDIUM

## Recommendation in One Sentence

Keep the production stack exactly as small as it is—Python 3.10+ plus
`mypy-extensions`—and harden it with standard-library synchronization,
logging, metadata, and sparse-graph primitives; spend the milestone's tooling
budget on reproducible builds and testing the artifacts users actually install.

## Recommended Stack

### Core Technologies

| Technology | Version | Status | Purpose | Why Recommended |
|------------|---------|--------|---------|-----------------|
| CPython | 3.10–3.14 | Keep | Supported runtime matrix | This is the project's established compatibility contract. Do not add 3.15 during a hardening milestone; first make the existing five-version matrix release-auditable. |
| `mypy-extensions` | 1.1.0 resolved; public requirement `>=1.0` | Keep | Runtime `@mypyc_attr` support | Preserve the one-runtime-dependency constraint and current subclassing boundary. No hardening concern requires another runtime package. |
| mypy + mypyc | **2.3.1 exact for builds** | Upgrade and pin | Compile only `src/fast_fsm/core.py`; authoritative compatibility check for compiled code | Build isolation otherwise resolves an arbitrary future compiler. An exact pin makes wheel output reproducible and the same compiler is available to `uv run mypy src/fast_fsm/core.py`. |
| setuptools | **84.0.0 exact in `[build-system].requires`** | Upgrade and pin | Existing PEP 517 backend and selective `ext_modules` hook | Retain setuptools because the project already needs the small `setup.py` mypyc hook. Changing backends adds risk without solving a milestone concern. |
| wheel | **0.48.0 exact in `[build-system].requires`** | Upgrade and pin | Wheel construction | Exact build-isolation pins prevent artifact drift between local, CI, and tag builds. |
| uv | **0.12.7** | Upgrade and pin | Environment, lockfile, and local build orchestration | Continue the established tool. Add `tool.uv.required-version = "==0.12.7"`, install that version in CI, and use `uv sync --locked`; the current workflow silently accepts both a mutable uv version and an ignored lockfile. |
| cibuildwheel | **4.2.0** | Upgrade and pin | Compiled wheel matrix and installed-wheel tests | Current 4.2 supports the required CPython/platform matrix, native ARM runners, pinned dependency sets, wheel tests, and the `build` frontend. Move configuration into `pyproject.toml` so CI and release behavior cannot drift. |

**Version policy:** exact-pin build-producing tools and CI actions; let `uv.lock`
pin development tools. Keep compatible lower bounds in the `dev` group only
where they are useful to contributors. `ty` is the exception: pin it exactly
because its official version policy permits diagnostic changes in every 0.0.x
release.

### Standard-Library Building Blocks

| Library / Algorithm | Version | Status | Purpose | Integration Point |
|---------------------|---------|--------|---------|-------------------|
| `threading.Lock` | Python 3.10+ | Required | Reject overlapping or reentrant synchronous mutations without blocking | One non-reentrant lock per `StateMachine`; acquire with `blocking=False` at every state/topology mutation boundary. `RLock` is intentionally wrong because it permits the reentrancy the safe default must reject. |
| `asyncio.Lock` + `asyncio.current_task()` | Python 3.10+ | Required | Exclusive async mutation and owner identification | One task lock per `AsyncStateMachine`; record the owning task so recursive callbacks fail immediately instead of deadlocking. Do not use this lock for OS-thread safety—the official API explicitly is not thread-safe. |
| `collections.deque(maxlen=N)` | Python 3.10+ | Required | O(1) bounded history retention | Replace front-deletion from a list. Reject `max_entries <= 0` with `ValueError`; do not let a zero-length deque silently disguise invalid configuration. Return a list copy from the public `history` property. |
| `logging` + `NullHandler` | Python 3.10+ | Required | Application-owned logging with safe defaults | Attach only `NullHandler` at the package logger. `configure_fsm_logging()` may add/remove only a handler it created and marked; it must never clear host handlers. Log trigger key names/counts, never payload values, by default. |
| `importlib.metadata` + `importlib.machinery` | Python 3.10+ | Required | Installed version and loader verification | Compare `fast_fsm.__version__` with `importlib.metadata.version("fast_fsm")`; assert `ExtensionFileLoader` for compiled wheels and `SourceFileLoader` for the pure wheel. This is stronger than checking `.so`/`.pyd` suffix strings. |
| Iterative Tarjan SCC | O(V+E) | Required | Complete cycle membership and graph condensation | Implement internally over sparse adjacency. SCC size >1, or a singleton with a self-loop, identifies every state in a cycle. Iterative traversal avoids Python recursion-depth failures on large machines. |
| SCC condensation + topological DP | O(V+E) | Required | Bounded longest-path diagnostics | Condense SCCs to a DAG, then process it with `graphlib.TopologicalSorter` or an internal Kahn pass. Do not enumerate every acyclic path. |
| Deterministic work budgets | Node/edge/path expansion counters | Required | Bound expensive diagnostics | Limit graph work by counts, not wall-clock time. Return explicit `truncated`, `budget_used`, and reason metadata so results remain deterministic in tests and across machines. |

### Supporting Test Libraries

These are development-only and should remain outside the runtime dependency
set.

| Library | Verified Current Version | Status | Purpose | When to Use |
|---------|--------------------------|--------|---------|-------------|
| pytest | **9.1.1** | Upgrade in lock | Main correctness and artifact parity suite | Run the same hardening suite against pure source, the universal pure wheel, in-place compiled core, and every published compiled wheel. |
| pytest-asyncio | **1.4.0** | Upgrade in lock | Async ownership, reentrancy, callback, and guard parity | Keep `asyncio_mode = "auto"`; this project supports asyncio only, so strict multi-framework isolation adds ceremony without value. |
| Hypothesis | **6.165.10** | Upgrade in lock | Generated topology and transition-sequence invariants | Add `RuleBasedStateMachine`/generated graph tests for registration identity, duplicate names, builder freeze, serialization round trips, sync/async parity, and bounded diagnostics. |
| pytest-cov | **7.1.0** | Upgrade in lock | Source coverage | Measure `core.py` only in a proven pure-Python environment. Report compiled-wheel parity separately; compiled execution cannot honestly count as Python line coverage. |
| Ruff | **0.16.5** | Upgrade in lock | Formatting and lint gate | Set `target-version = "py310"` explicitly; require both `ruff format --check src tests` and `ruff check src tests` before tests and release. |
| ty | **0.0.75 exact** | Upgrade and exact-pin | Fast broad type diagnostics | Keep as the fast full-package gate, but not as the only type check: ty remains beta and documents unstable diagnostics. |
| mypy | **2.3.1 exact** | Upgrade and exact-pin | mypyc compatibility and static typing | Add a mandatory `uv run mypy src/fast_fsm/core.py` CI step. Successful C compilation is not a substitute for the intended source-level gate. |

No new test framework is required. Concurrency tests should use
`threading.Barrier`, `threading.Thread`/`ThreadPoolExecutor`, `asyncio.Event`,
and `asyncio.create_task()`/`gather()` so tests exercise the library's actual
ownership boundary in one process.

## Build-Mode Contract

The current broad `except Exception` in `setup.py` can turn a broken mypyc
configuration into a silently slow artifact. Preserve convenient local
fallback while making release intent explicit:

| Mode | Selector | Required Behavior |
|------|----------|-------------------|
| Pure Python | Existing `FAST_FSM_PURE_PYTHON=1` | Build a `py3-none-any` wheel and sdist without invoking mypyc; installed probe must load `core.py`. |
| Strict compiled | Add `FAST_FSM_REQUIRE_COMPILED=1` | Any import, mypycification, compiler, or extension-build failure aborts the build; installed probe must load an extension module. |
| Local automatic | Neither variable | May preserve the current convenience fallback, but it is forbidden in CI/release and must emit an actionable warning naming the failed stage. |

Build and publish a tested universal pure-Python wheel in addition to compiled
platform wheels and the sdist. It gives unsupported platforms a real fallback
instead of asking their installer to discover whether compilation happens to
work. Compatible platform wheels remain preferred by Python installers.

## Required CI and Release Gates

### 1. Reproducibility and Quality

Run on every pull request and every push; remove the broad `paths-ignore` rules
for `uv.lock`, Markdown, changelog, and release metadata.

```bash
uv sync --locked --group dev
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
uv run ty check src/fast_fsm/
uv run mypy src/fast_fsm/core.py
uv run pytest tests/ -x -q
```

Required configuration changes:

- Pin uv 0.12.7 through setup-uv and `[tool.uv].required-version`; never use an
  unqualified `latest` installer in a release-producing workflow.
- Treat `uv.lock` changes as CI-relevant and use `--locked` so stale lockfiles
  fail instead of being repaired during a job.
- Establish a green baseline first: fix the known Ruff F841 and formatting
  failures before using this gate to judge hardening changes.
- Keep the pure correctness matrix at Python 3.10–3.14 on Linux, macOS, and
  Windows; assert the loaded core is source code at test start.

### 2. Version and Metadata Integrity

Use `pyproject.toml` as the single writable version source. Keep
`fast_fsm.__version__` derived from `importlib.metadata`; do not add
`setuptools-scm` for one static pre-1.0 release number.

A standard-library verification script should fail unless:

1. installed `fast_fsm.__version__` equals
   `importlib.metadata.version("fast_fsm")`;
2. the sdist filename, its `PKG-INFO`, every wheel filename, and wheel
   `METADATA` all contain the same normalized version;
3. for tag builds, that version equals `GITHUB_REF_NAME` after stripping `v`;
4. `CHANGELOG.md` contains a released heading for that exact version and no
   v0.3.0 changes remain stranded under `Unreleased`;
5. documentation contains no authoritative hard-coded test count—CI should
   report the collected count rather than making it release metadata.

Run source-integrity checks before a tag can build artifacts, then rerun them
over the downloaded aggregate artifact set before creating the GitHub release.

### 3. Compiled/Pure Parity

The ordinary matrix currently tests pure Python while the compiled job performs
only one smoke transition. Replace that asymmetry with these gates:

| Gate | Frequency | Mode Assertion | Tests |
|------|-----------|----------------|-------|
| Pure source matrix | Every PR/push | `SourceFileLoader` | Full suite on 3.10–3.14 × Linux/macOS/Windows |
| Compiled core | Every PR/push | `ExtensionFileLoader` | Full suite plus mypyc guard on Linux CPython 3.12 |
| Performance | Push to main and release candidate | `ExtensionFileLoader` | Existing 200,000 ops/sec compiled floor, 30,000 pure floor, history ratio, and guarded-transition floor |
| Pure universal wheel | Release | `SourceFileLoader` from a clean temporary environment | Full suite and pure performance floor |
| Every compiled wheel | Release | `ExtensionFileLoader` from cibuildwheel test environment | Full hardening/parity suite; at minimum all core, async, safety, builder, validation, logging, serialization, and invariant tests |

Do not publish artifacts covered only by `CIBW_TEST_SKIP`. Use native runners
(`ubuntu-24.04-arm`, macOS Intel, and macOS Apple Silicon) for the architectures
currently built under QEMU or cross-compilation. If a universal2 wheel remains,
download and install the same wheel on both Intel and Apple Silicon runners so
both slices are exercised. Otherwise publish the two tested architecture wheels
and drop universal2.

Move cibuildwheel settings to `[tool.cibuildwheel]` and pin its test requirements
to the same versions used by `uv.lock`. Explicitly keep musllinux and
free-threaded CPython builds out of scope until they have native execution and
mypyc/locking verification.

### 4. Safe Runtime Semantics

Required deterministic verification:

- A callback that recursively calls `trigger()`/`trigger_async()` fails
  immediately with the documented reentrancy result; it never deadlocks.
- Two synchronized threads/tasks attempting a transition cannot both mutate
  from the same source state. Tests start contenders with barriers/events and
  assert one committed transition plus one explicit concurrency failure.
- Locks are released on guard, exit callback, state mutation, enter callback,
  listener, and exception paths.
- Callback failures are surfaced and transition outcome/state follow one
  documented transaction policy. Tests should not assume external callback side
  effects are rollbackable.
- Lock-free read methods are retained only when a coherent snapshot is possible;
  any read spanning multiple mutable structures uses the same ownership guard.
- Measure the lock/owner check in the compiled hot-path benchmark. Rejecting
  races is not permission to fall below 200,000 `trigger()` operations/sec.

### 5. Graph and Diagnostic Bounds

Use sparse `dict[node, iterable[node]]` structures internally. Compute SCCs once
per diagnostic run and reuse the condensation for cycle membership,
reachability summaries, and longest-path scoring. Add deterministic budgets for
node visits, edge visits, and generated test paths. Dense N×N adjacency may
remain as an explicitly requested compatibility view, but must reject or mark
truncation beyond a documented size rather than allocate without bound.

## GitHub Actions Hardening

As of the research date, the official repositories list these current releases:

| Action | Current Release | Recommendation |
|--------|-----------------|----------------|
| `actions/checkout` | 6.0.2 | Upgrade from v4, set `persist-credentials: false`, and pin the reviewed release to its full commit SHA. |
| `astral-sh/setup-uv` | 9.0.0 | Upgrade from v5, pin full SHA, and request uv 0.12.7 explicitly. |
| `actions/upload-artifact` | 7.0.1 | Upgrade from v4 and pin full SHA. |
| `actions/download-artifact` | 8.0.1 | Upgrade from v4 and pin full SHA; v8 fails artifact digest mismatches by default. |
| `pypa/cibuildwheel` | 4.2.0 | Upgrade from v2.22.0 and pin full SHA/version. |

Declare top-level `permissions: contents: read`; grant `contents: write` only to
the GitHub-release job and `id-token: write` only to a future PyPI trusted-publish
job. Make the release job depend on artifact verification, not merely artifact
build completion. Full-SHA action pins are required because GitHub's own
hardening guidance notes that tags can move.

## Installation and Pin Update

Target configuration (performed during the implementation phase, not by this
research task):

```toml
[build-system]
requires = [
  "setuptools==84.0.0",
  "wheel==0.48.0",
  "mypy[mypyc]==2.3.1",
]
build-backend = "setuptools.build_meta"

[tool.uv]
package = true
required-version = "==0.12.7"
```

Then upgrade deliberately and commit the resolved lock:

```bash
uv lock --upgrade
uv sync --locked --all-groups
```

Do not copy all current PyPI versions into unbounded `>=` constraints and call
that reproducibility. The committed lock controls developer/CI tools; exact
`[build-system]` pins control isolated wheel builds.

## Alternatives Considered

| Recommended | Alternative | When the Alternative Would Be Appropriate |
|-------------|-------------|-------------------------------------------|
| Per-instance `threading.Lock` / `asyncio.Lock` | Application-supplied external locks | Only if Fast FSM explicitly documented itself as single-owner and did not promise safe defaults. That is contrary to this milestone decision. |
| Fail-fast overlap semantics | Queue/serialize concurrent triggers | A later API could add an explicit queued dispatcher when ordering/backpressure semantics are designed. Silently waiting now can deadlock callbacks and hides misuse. |
| Internal iterative Tarjan + topological DP | NetworkX SCC/DAG algorithms | Use NetworkX in benchmark/research scripts or if diagnostic breadth becomes a separate product. It is not justified as a runtime dependency for two linear algorithms. |
| Static version in `pyproject.toml` + validation | `setuptools-scm` | Use SCM-derived versions in projects already designed around dynamic version metadata. Here it adds build-time behavior while the existing import path already derives from distribution metadata. |
| Existing pytest + explicit timing loops | `pytest-benchmark` or `pyperf` | Add a benchmark framework only if the project starts tracking statistically comparable historical runs. The milestone needs a stable floor and mode assertion, not a new benchmark product. |
| Native architecture runners | QEMU/cross-build with skipped tests | Emulation is acceptable for non-published experimental artifacts. Published wheels should execute on their target architecture. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| New runtime dependencies | They weaken the library's defining small-footprint contract and none are needed for the audited concerns. | Python standard library plus existing `mypy-extensions`. |
| `threading.RLock` for transition ownership | It explicitly permits same-thread recursion, preserving the unsafe behavior being removed. | Non-reentrant `threading.Lock` with nonblocking acquisition and owner diagnostics. |
| `pytest-xdist` for concurrency correctness | Multiple processes do not exercise shared in-process state and can make race tests less deterministic. | Barriers/events and multiple threads/tasks inside one pytest process. |
| Wall-clock diagnostic timeouts | Results vary with machine load and can leave partial work hard to reproduce. | Explicit node/edge/path expansion budgets and truncation metadata. |
| `networkx` in `project.dependencies` | Large dependency cost for SCC and DAG operations that are linear and narrow. | Internal sparse Tarjan + `graphlib`/Kahn processing. |
| `structlog` or a redaction package | Logging ownership and payload exposure are policy bugs, not missing logging infrastructure. | Standard `logging`, `NullHandler`, structural messages, and an optional caller redactor callback. |
| A compiler/toolchain rewrite (Cython, Rust, C extension by hand) | High risk to subclassing, public symbols, and the core-only mypyc boundary; unrelated to current correctness gaps. | Keep mypyc and make its artifacts observable and fail-closed. |
| Source-tree coverage while an ignored extension exists | It can report `core.py` at 0% while tests actually execute stale native code. | Clean isolated installs plus explicit loader assertions before coverage/test execution. |
| Automatically publishing untested cross-compiled wheels | A successful build is not evidence that imports, dispatch, or callbacks work on the target. | Native test runners or omit the artifact. |

## Version Compatibility

| Package / Tool | Compatible With | Notes |
|----------------|-----------------|-------|
| mypy/mypyc 2.3.1 | Python 3.10–3.14 project matrix | Official metadata requires Python 3.10+ and publishes the `mypyc` extra. Compile/test each targeted CPython because generated extensions remain interpreter/platform-specific. |
| pytest 9.1.1 | Python 3.10+ | Matches the project's floor. Upgrade together with pytest-asyncio and pytest-cov in one lock change. |
| pytest-asyncio 1.4.0 | Python 3.10–3.14 | Official metadata lists this exact supported range and matches the current `asyncio_mode = "auto"` design. |
| Hypothesis 6.165.10 | Python 3.10+ | Use for design-time/stateful tests only; never import from production modules. |
| Ruff 0.16.5 | Python 3.10 target | Set target explicitly even though Ruff's documented default is currently py310. |
| ty 0.0.75 | Targets Python 3.10+ | Beta and unstable across 0.0.x; exact pin is mandatory if diagnostics are a merge gate. |
| cibuildwheel 4.2.0 | Host Python 3.11+; builds CPython 3.10+ wheels | Its own host requirement does not change the package's Python 3.10 runtime floor. |
| setup-uv 9.0.0 / uv 0.12.7 | GitHub-hosted runners | Pin both action SHA and installed uv version; the action can read `required-version` from `pyproject.toml`. |

## Sources

### Primary / Official

- [Fast FSM project contract](../PROJECT.md) and
  [independent concerns audit](../codebase/CONCERNS.md) — current architecture,
  reproduced failures, and performance constraints (direct repository evidence,
  HIGH confidence).
- [Python Packaging User Guide: single-sourcing the version](https://packaging.python.org/en/latest/discussions/single-source-version/) — recommends testing import version against installed distribution metadata (MEDIUM via research seam).
- [PyPA source distribution specification](https://packaging.python.org/en/latest/specifications/source-distribution-format/) and
  [core metadata specification](https://packaging.python.org/en/latest/specifications/core-metadata/) — filename/metadata and sdist/wheel consistency rules (MEDIUM).
- [cibuildwheel 4.2 options](https://cibuildwheel.pypa.io/en/latest/options/) and
  [configuration](https://cibuildwheel.pypa.io/en/latest/configuration/) — build frontend, test command, pinned test requirements, native architectures, and test skips (MEDIUM).
- [Python 3.10 threading locks](https://docs.python.org/3.10/library/threading.html#lock-objects) and
  [asyncio synchronization](https://docs.python.org/3.10/library/asyncio-sync.html#lock) — nonblocking sync acquisition and task-only async mutual exclusion (MEDIUM).
- [Python bounded deque](https://docs.python.org/3.10/library/collections.html#collections.deque),
  [library logging guidance](https://docs.python.org/3.10/howto/logging.html#configuring-logging-for-a-library),
  [importlib metadata](https://docs.python.org/3.10/library/importlib.metadata.html), and
  [graphlib](https://docs.python.org/3.10/library/graphlib.html) — standard-library implementation primitives (MEDIUM).
- [Tarjan, “Depth-First Search and Linear Graph Algorithms,” SIAM Journal on Computing](https://epubs.siam.org/doi/abs/10.1137/0201010) — linear strongly connected components algorithm (MEDIUM).
- [GitHub workflow hardening guidance](https://docs.github.com/en/enterprise-cloud@latest/code-security/tutorials/secure-your-organization/protect-against-threats) — full-SHA action pins and least permissions (MEDIUM).
- Official release/metadata pages for
  [uv 0.12.7](https://pypi.org/project/uv/),
  [pytest 9.1.1](https://pypi.org/project/pytest/),
  [pytest-asyncio 1.4.0](https://pypi.org/project/pytest-asyncio/),
  [pytest-cov 7.1.0](https://pypi.org/project/pytest-cov/),
  [Hypothesis 6.165.10](https://pypi.org/project/hypothesis/),
  [Ruff 0.16.5](https://pypi.org/project/ruff/),
  [ty 0.0.75](https://pypi.org/project/ty/),
  [mypy/mypyc 2.3.1](https://pypi.org/project/mypy/),
  [setuptools 84.0.0](https://pypi.org/project/setuptools/),
  [wheel 0.48.0](https://pypi.org/project/wheel/), and
  [cibuildwheel 4.2.0](https://pypi.org/project/cibuildwheel/) — versions verified 2026-08-29 (MEDIUM).
- Official action releases for
  [checkout](https://github.com/actions/checkout/releases),
  [setup-uv](https://github.com/astral-sh/setup-uv),
  [upload-artifact](https://github.com/actions/upload-artifact/releases), and
  [download-artifact](https://github.com/actions/download-artifact/releases) — current action majors and security behavior (MEDIUM).

## Research Gaps to Resolve During Implementation

- Benchmark the exact per-instance lock/owner representation under mypyc 2.3.1
  before freezing slots; the behavior recommendation is firm, but field layout
  belongs to implementation measurement.
- Decide whether to retain universal2 after proving the same artifact on both
  macOS architectures; separate tested arm64/x86_64 wheels are preferable to an
  incompletely tested universal artifact.
- Verify the full 722+ test suite against pytest 9/mypy 2 before merging the
  lock upgrade. Current-version compatibility metadata is necessary but not a
  substitute for this repository's mypyc-specific tests.
- Define the exact callback transaction outcome before code changes. Locks can
  guarantee exclusivity, but no stack choice can roll back external side
  effects performed by user callbacks.

---
*Stack research for: Fast FSM v0.3.0 Reliability & Runtime Hardening*
*Researched: 2026-08-29*
