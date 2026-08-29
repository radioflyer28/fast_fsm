# Project Research Summary

**Project:** Fast FSM
**Domain:** High-performance, in-process Python finite state machine library
**Milestone:** v0.3.0 Reliability & Runtime Hardening
**Researched:** 2026-08-29
**Confidence:** MEDIUM overall; HIGH for repository-derived findings

## Executive Summary

Fast FSM is a compact Python FSM whose value is O(1) dispatch, low memory use,
and a compiled `core.py` hot path. Experts would preserve that shape while
making the runtime state-atomic and observable: one canonical graph, one
transition lifecycle with an explicit commit point, immediate rejection of
reentrant work, serialized independent callers, and equivalent sync/async and
source/compiled behavior. The stack should remain Python 3.10–3.14 plus the
single runtime dependency `mypy-extensions`; synchronization, bounded history,
logging, SCC analysis, and artifact checks can all use the standard library.

The milestone should prioritize evidence before broad refactoring. First make
version metadata, changelog, test counts, formatting/lint, type checks, docs,
and build intent agree. Then stabilize graph construction and the shared
dispatch contract, define callback failure semantics, and add safe-default
ownership. Only after those boundaries are stable should validators,
visualizers, logging, and release artifacts be hardened. The largest risks are
false-success callback results, deadlock/state corruption from reentry and
concurrency, diagnostics that are false or unbounded, payload leakage, and a
compiled wheel that silently falls back to Python. Each must have deterministic
tests, explicit failure metadata, and a clean installed-artifact verification
path while preserving the >=200,000 compiled `trigger()` operations/sec floor.

## Key Findings

### Recommended Stack

Keep the production dependency surface unchanged and keep `core.py` as the
single mypyc compilation unit. Pin build-producing tools so release artifacts
are reproducible: mypy/mypyc 2.3.1, setuptools 84.0.0, wheel 0.48.0, uv 0.12.7,
and cibuildwheel 4.2.0; pin the development lock to pytest 9.1.1,
pytest-asyncio 1.4.0, Hypothesis 6.165.10, Ruff 0.16.5, ty 0.0.75, and mypy
2.3.1 where adopted. Keep Python 3.10–3.14 as the support matrix.

**Core technologies:**

- `threading.Lock` with owner detection — fail fast for sync reentry and
  serialize independent threads without the recursive behavior of `RLock`.
- `asyncio` task/loop ownership — serialize same-loop async callers and reject
  unsupported cross-loop use; do not use an async lock as thread protection.
- `collections.deque(maxlen=N)` — make bounded history eviction O(1) and reject
  non-positive capacities.
- Standard `logging`, `NullHandler`, and `importlib` — preserve application
  handlers, redact payloads, and verify installed version/module origin.
- Iterative Tarjan SCC plus sparse adjacency and deterministic budgets — provide
  complete cycle membership and bounded diagnostics without a runtime graph
  dependency.
- mypyc/setuptools/cibuildwheel — retain selective compilation while adding
  strict compiled and intentional pure-Python artifact modes.

The essential gates are `uv sync --locked`, Ruff format/check, ty plus stable
mypy for `core.py`, the full test suite, docs/doctests, a clean pure-source
matrix, installed compiled-wheel tests, and the existing compiled throughput
floor. A universal pure wheel is a deliberate fallback; a requested compiled
release must fail closed if compilation or extension inclusion fails.

### Expected Features

**Must have (table stakes):**

- Canonical graph registration: all endpoints resolve to registered objects,
  duplicate names are rejected, and fan-out mutations are atomic.
- A sealed, idempotent builder; every post-build mutator fails immediately.
- One guard context policy preserving positional arguments and sanitizing
  keyword arguments across sync/async, `can_trigger*()`, `trigger*()`, and
  `condition`/`unless` paths; recursive async detection.
- Declarative handlers integrated into normal trigger dispatch exactly once.
- Explicit state commit boundary and stage-aware callback failures: pre-commit
  failure keeps the source; post-commit failure keeps the destination, reports
  `committed=True`, and never claims success. No automatic rollback of external
  side effects.
- Safe defaults: same-owner reentry fails immediately; independent sync
  callers and same-loop async tasks are serialized; cancellation always cleans
  ownership and preserves state/history coherence.
- Sync/async semantic parity, including callback order, history, guard context,
  errors, and failure observers. Synchronous callbacks in async machines remain
  explicitly inline/non-blocking rather than silently moving to worker threads.
- Correct history capacity and O(1) eviction; correct initial-state validation,
  empty/duplicate comparisons, complete SCC cycle membership, and bounded
  deterministic diagnostics.
- Stable internal graph snapshots consumed by validation, comparison, JSON, and
  renderers; collision-free opaque diagram aliases and grammar-specific escaping.
- Application-owned logging with redacted trace output and reversible helper
  configuration.
- Auditable version/changelog/docs/test identity, clean source verification,
  strict compiled wheels, and parity/performance tests on installed artifacts.

**Should have (competitive):**

- One parameterized conformance suite spanning sync, async, builder,
  declarative, source, and compiled modes.
- Agent-grade JSON/validation that reports completeness, budget usage, and
  truncation/error metadata instead of silently degrading.
- Optional application-supplied trace redaction and additive sparse adjacency
  output if these do not materially expand the public API.
- Secure, trustworthy Mermaid/PlantUML output for Unicode, punctuation,
  control text, and names that collide under sanitization.

**Defer (v2+):**

- Implicit or opt-in queued reentrant transitions and queue overflow policy.
- Automatic callback rollback/compensation orchestration.
- Cross-event-loop sharing, automatic worker-thread callback offload, timers,
  scheduler behavior, and unrelated API expansion.
- Splitting `core.py`, adding NetworkX or other runtime dependencies, replacing
  ty wholesale, a public topology snapshot v2, and redesigning
  `CompiledFuncCondition` solely to remove its measured `__dict__` exception.

### Architecture Approach

Keep one compiled module but establish explicit internal seams: canonical graph
ownership, immutable topology snapshots, transition admission/resolution, and a
staged lifecycle executor. Runtime mutation methods share a per-machine control
gate and all diagnostics consume the same snapshot rather than private tables.
State assignment and history append occur in one non-awaiting commit section;
post-commit callbacks can fail without pretending rollback occurred.

**Major components:**

1. `_TransitionControl` — non-blocking admission, owner token, operation label,
   reentrancy/concurrency errors, and guaranteed cleanup for all mutators.
2. Canonical graph and `_GraphSnapshot` — identity-safe registration, graph
   versioning, declared initial state, deterministic topology, and an immutable
   observation boundary for tools.
3. Shared transition pipeline — resolve, authorize, pre-commit callbacks,
   commit/history, post-commit callbacks, and one truthful result/failure path;
   sync and async differ only in stage execution/awaiting.
4. Builder/condition/declarative binding — terminal builder state, recursive
   async capability detection, one sanitized guard context, and bound handlers.
5. Snapshot analyzer and renderers — sparse adjacency, SCC/condensation/DAG
   calculations, explicit budgets, stable comparison identity, JSON analysis,
   opaque aliases, and target-specific escaping.
6. Artifact parity harness — isolated pure and compiled wheel installs with
   module-origin, metadata, semantic, and throughput assertions.

### Critical Pitfalls

1. **Locking before semantics:** adding a mutex around the current body preserves
   false-success callback behavior or deadlocks. Define the state commit point,
   stage failures, history, and cancellation semantics first.
2. **Reentrant lock/no owner detection:** `RLock` permits corruption and a plain
   blocking lock deadlocks the owner. Detect same-owner reentry before acquire,
   use non-blocking admission, and clean up in `finally`.
3. **Rollback claims:** arbitrary callbacks may have external side effects.
   Preserve source on pre-commit failure and destination on post-commit failure,
   expose stage/commit status, and require application compensation.
4. **Partial graph or dispatch fixes:** endpoint identity, builder mutability,
   guard arguments, declarative execution, async `unless`, and sync/async paths
   must be covered by one parity and construction-invariant suite.
5. **Untrusted evidence:** silent mypyc fallback, stale extension shadowing,
   unbounded diagnostics, raw logs, and raw diagram labels can ship or expose
   materially different behavior. Assert artifact origins, use deterministic
   budgets, redact values, and escape labels with opaque IDs.

## Implications for Roadmap

Based on the combined research and the concerns audit, use six dependency-aware
implementation phases. The ordering is deliberately concrete; each phase has a
release-level verification boundary and must benchmark the compiled hot path
when it touches `core.py`.

### Phase 0: Release Baseline and Contract Harness

**Rationale:** Current package metadata/tag/changelog/test claims disagree and
the existing Ruff gate is not green. Later behavior results are not credible
until source-versus-artifact identity is explicit.

**Delivers:** One version source and v0.3.0 release section; corrected docs/test
baseline; green formatting, lint, docs/doctests, type, and test gates; pinned
tooling/lock behavior; strict compiled versus intentional pure build selectors;
loader-origin and metadata probes; reusable semantic and throughput harness.

**Addresses:** Release integrity, optional compilation, stale-extension coverage,
quality-gate drift, test baseline, and the compiled-function slots exception
documentation.

**Avoids:** Silent fallback, testing the checkout instead of an installed wheel,
and spending later phases diagnosing baseline drift. Do not change runtime
semantics here beyond harness hooks.

### Phase 1: Canonical Graph, Builder, and Dispatch Invariants

**Rationale:** Validators, renderers, and transition semantics cannot be trusted
while graph identity and sync/async dispatch disagree.

**Delivers:** Atomic endpoint validation and duplicate policy; graph version and
`_GraphSnapshot`; sealed builder; recursive async condition capability; unified
guard argument/sanitization policy; declarative handler binding; correct history
capacity validation; parameterized sync/async and `can_trigger`/`trigger`
conformance tests.

**Addresses:** Core concentration through internal seams, builder mutability,
unknown/unregistered/duplicate states, positional guards, async `unless`,
declarative dispatch, and zero-capacity history.

**Avoids:** Partial fan-out graph mutations, stale builder caches, path-specific
patches, wrapper-only async detection, and inconsistent object identity.

### Phase 2: Atomic Transition Lifecycle

**Rationale:** Synchronization is only safe after the commit semantics are
   defined; callbacks currently mutate/report ambiguously.

**Delivers:** Shared staged lifecycle with explicit pre/post commit boundary,
commit-aware `TransitionResult`/`TransitionRecord`, O(1) history storage,
fail-fast callback handling, one failure notification, and documented
state-atomic/no-rollback behavior for sync and async callbacks.

**Addresses:** Swallowed callback exceptions, truthful results/history, callback
ordering, cancellation boundaries, and performance impact of enabled history.

**Avoids:** Wrapping the old body in a lock, post-commit rollback lies, history
written after an await, and treating external side effects as ACID transactions.

### Phase 3: Ownership, Reentrancy, and Concurrency

**Rationale:** With a defined lifecycle, enforce the user-selected safe default
without hiding races or deadlocking callbacks.

**Delivers:** Per-instance non-reentrant sync control, async task/loop ownership,
immediate reentrant/concurrent failure, serialization of independent callers,
protected state/topology mutators, cancellation cleanup, cross-loop rejection,
and explicit async sync-callback policy/documentation.

**Addresses:** Reentrant overwrite, concurrent mutation, force/reset/restore
interleavings, async event-loop safety, and callback failure/recovery paths.

**Avoids:** `RLock`, blocking acquisition in async code, implicit queues,
automatic `to_thread()` semantics, global locks, and owner leaks after
`CancelledError` or `BaseException`.

### Phase 4: Bounded Diagnostics, Visualization, and Logging

**Rationale:** Once topology and lifecycle boundaries are stable, migrate all
   consumers away from mutable private layout and make output safe for generated
   or user-controlled graphs/data.

**Delivers:** Snapshot-based validator/comparison/JSON/rendering; declared
initial-state reachability; complete SCC cycle membership; memoized/bounded
longest-path analysis; sparse adjacency and deterministic work/result budgets;
empty/duplicate comparison behavior; collision-free Mermaid/PlantUML/Markdown
escaping; redacted trace logs; application-handler preservation and reversible
logging configuration.

**Addresses:** Validator drift, duplicate/empty comparisons, exponential or
quadratic diagnostics, visualization collisions/injection, raw payload logging,
logger takeover, and diagnostic broad-catch degradation.

**Avoids:** Dense unbounded matrices, exhaustive path enumeration, silent partial
results, generic sanitizers, raw labels, and `logger.handlers.clear()`.

### Phase 5: Compiled/Source Parity and Release Proof

**Rationale:** The shipped product—not only the source checkout—must prove the
same behavior and performance on supported targets.

**Delivers:** Clean source matrix and installed pure universal wheel tests;
strict compiled wheel builds/tests on supported platform/Python combinations;
semantic trace comparison; extension/source loader assertions; native architecture
coverage; full docs/type/test/quality gates; >=200,000 compiled trigger ops/sec
and documented pure-mode floor; final tag/package/changelog/artifact identity.

**Addresses:** Core-only mypyc boundary, silent compilation fallback, stale local
extensions, platform wheel confidence, compiled slots behavior, release drift,
and the performance contract.

**Avoids:** Smoke-only compiled CI, `CIBW_TEST_SKIP`-covered publications,
cross-compiled untested wheels, source-tree shadowing, and retagging a different
source tree.

### Phase Ordering Rationale

- Establish evidence first so every subsequent failure is attributable to the
  milestone, not stale metadata, tools, or import mode.
- Canonical graph identity and a shared guard/dispatch policy precede the
  lifecycle; otherwise callback and async behavior are being specified over
  contradictory machines.
- The commit boundary precedes locks: ownership protects defined semantics and
  can put history/assignment in one non-awaiting critical section.
- Reentry detection precedes acquisition; Phase 2's stage model supplies the
  cancellation and callback tests needed by concurrency work.
- Snapshot-based diagnostics follow graph invariants; logging and renderers then
  share the same safe data/analysis boundary.
- Artifact parity and performance are final release gates, but benchmark every
  `core.py` phase so the 200k requirement cannot regress invisibly.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 0:** Exact uv/build backend/action pins, version migration, and clean
  installed-artifact harness details should be validated against CI constraints.
- **Phase 2:** The exact public result/exception shape and callback transaction
  stages require a compatibility decision; rollback must remain out of scope.
- **Phase 3:** Measure lock/owner-token cost under mypyc and pure Python; settle
  async loop binding and the explicit synchronous-callback policy.
- **Phase 4:** Choose public versus internal budget APIs, defaults, truncation
  schema, and grammar-specific escaping behavior with renderer tests.
- **Phase 5:** Verify native architecture availability, universal2 versus split
  wheels, mypyc compatibility across Python 3.10–3.14, and release permissions.

Phases with standard patterns (skip `--research-phase` unless implementation
uncovers a gap):

- **Phase 1:** Atomic validation, immutable value snapshots, builder state
  machines, and parameterized conformance tests are local design work.
- **Phase 4 (algorithm core):** SCC, sparse adjacency, deque history, and
  topological DP are established algorithms; only project-specific limits need
  validation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Tool versions and ecosystem guidance were checked against primary sources, but exact CI/platform compatibility remains to be proven. |
| Features | MEDIUM/HIGH | Scope and defects come directly from the concerns audit and project decisions; external UX semantics are less certain. |
| Architecture | HIGH/MEDIUM | Boundaries fit the inspected code and single-module constraint; lock and snapshot cost still needs benchmarks/mypyc validation. |
| Pitfalls | MEDIUM/HIGH | Reproduced repository failure modes are high confidence; remedies involving platforms and callback policy need implementation tests. |

**Overall confidence:** MEDIUM, with high confidence in the priority ordering and
the required defect scope.

### Gaps to Address

- Decide exact exception/result fields while preserving all public symbols and
  existing callback signatures; test migration of callers against safe defaults.
- Benchmark non-blocking lock/owner checks, history, guards, callbacks, logging,
  and declarative dispatch in both modes before freezing implementation choices.
- Define default diagnostic budgets and whether budget exhaustion is an exception
  or explicit incomplete result for each existing API.
- Verify mypyc accepts new slot fields/value objects and that interpreted
  subclasses of `conditions.py` continue to work.
- Prove pure-source import isolation and every published compiled wheel on native
  targets; decide whether universal2 is retained only after both slices run.
- Reconcile current v0.2.3 tag/version/changelog drift without retagging a
  different source tree, then generate the v0.3.0 release identity from one
  source.

## Sources

### Primary (HIGH confidence)

- `.planning/codebase/CONCERNS.md` — independent executable assessment,
  reproduced bugs, security risks, scaling limits, and test gaps.
- `.planning/PROJECT.md` — v0.3.0 goal, constraints, safe-default decision,
  public compatibility, one runtime dependency, mypyc boundary, 722-test
  baseline, and >=200,000 throughput requirement.
- `src/fast_fsm/core.py`, `validation.py`, `visualization.py`, `setup.py`, and
  repository tests — direct implementation evidence cited by the research.

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md` — pinned stack, build modes, CI/release gates,
  and standard-library recommendations.
- `.planning/research/FEATURES.md` — table stakes, differentiators,
  anti-features, dependencies, and acceptance boundaries.
- `.planning/research/ARCHITECTURE.md` — internal seams, staged lifecycle,
  snapshots, analyzer design, and dependency-aware build order.
- `.planning/research/PITFALLS.md` — failure taxonomy, prevention/recovery,
  integration gotchas, and verification gates.
- Python, PyPA, mypyc, cibuildwheel, GitHub Actions, Mermaid, PlantUML, OWASP,
  `transitions`, and NetworkX documentation linked in the detailed research
  files.

---
*Research completed: 2026-08-29*
*Ready for roadmap: yes*
