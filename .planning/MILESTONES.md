# Milestones

## v0.3.0 Reliability & Runtime Hardening (Completed: 2026-09-06; untagged and unreleased)

**Phases completed:** 6 phases, 41 plans, 81 tasks

**Verification:** 50/50 requirements and 6/6 phase reports passed. The final hosted evidence run ([34010662876](https://github.com/radioflyer28/fast_fsm/actions/runs/34010662876)) passed all 101 jobs at exact SHA `84d86cd2b91f8042f0a6a15945f4be10035e1329`; downloaded records were independently recomputed locally. Known verification overrides: 1 newly acknowledged non-blocking quick task, 0 carried forward. No v0.3.0 Git tag, GitHub Release, or package publication was created.

**Key accomplishments:**

- Explicit build modes, non-destructive pure-source/wheel evidence, and a recursive measured slots-policy audit for the Phase 15 release baseline.
- Deterministic pure-source release evidence with exact uv/build provenance, independent CI categories, and a hermetic five-version sdist-to-wheel proof.
- Auditable v0.2.3 history correction, clean pure-source release evidence, and an operator runbook that preserves immutable published release identity.
- Durable release-evidence, type-check, and measured slots-policy guidance across user docs, contributor docs, agent instructions, and sparse API memory.
- The exact Phase 15 corrective SHA passed all hosted CI gates, and the existing v0.2.3 GitHub release now carries the canonical additive metadata correction without changing its tag or 25 published assets.
- Ruff-clean visualization formatting and a behavior-preserving advanced-test cleanup unblock authoritative release-baseline evidence.
- Sphinx-9.1-compatible reStructuredText and Google-style markup in five public `core.py` docstrings, backed by runtime-AST and physical-diff containment evidence.
- A structural CI contract and exact action pin make all nine independent Taskfile-based GitHub Actions gates executable on their existing operating-system and Python matrices.
- Python patch-version portability now compares only the copied major.minor identity while exact audit patches, 794-test inventory, coverage, pins, source, artifact, and slots evidence remain strict.
- Canonical identity-safe topology mutation with immutable versioned graph snapshots, plus clean pure/compiled verification that never relies on local native shadows.
- Canonical, filter-first guard context now behaves equivalently across sync and async dispatch, while built-in wrapper graphs await nested async leaves and reject cycles safely.
- FSMBuilder now freezes only after a fully wired local machine is published, and preflights nested asynchronous requirements before choosing or allocating that machine.
- Ordinary declarative sync/async dispatch now resolves one canonical handler and invokes it exactly once, while bounded deque history validates capacity atomically and retains the disabled fast path.
- Phase 16 is frozen with accurate maintainers' contracts, a reviewed clean pure baseline, and asserted pure/native semantic and performance proof.
- A committed destination-enter failure now returns truthful lifecycle state, preserves its hidden cause, notifies observers once, and is proven in fresh pure and compiled exports.
- Resolution, guard, and state-permission failures now return one redacted, stage-aware pre-commit result and notify failure observers once in both sync and async triggers.
- Published the atomic lifecycle contract, recorded ADR-004, and proved it through fresh pure/native source-tree gates with a current 1,267-test baseline.
- A per-machine synchronous trigger ownership tracer with native representation proof, deterministic future-contract inventory, and origin-labelled performance evidence.
- Synchronous transitions and direct control now serialize per machine, reject callback reentry before nested work, and release cleanly after every tested exit.
- Async machines now bind once to an event loop, serialize independent tasks without blocking it, and reject callback-created child reentry before it can deadlock.
- Every remaining topology, history, listener, callback, and failure-observer write now uses a single per-machine ownership envelope without weakening construction or snapshot contracts.
- safe_trigger now exposes ownership misuse instead of downgrading it, and declarative guard preparation is context-local across machines, threads, tasks, and native builds.
- Published the full per-machine ownership contract and accepted ADR-005, making safe-trigger admission, loop binding, causal reentry, cleanup, and explicit non-promises auditable.
- Closed the ownership phase with asserted fresh source evidence, reviewed release baseline and performance observations, and a successful exact-SHA Python 3.10-3.14 native ownership matrix.
- Declarative prepared-guard consumption now compares independently sourced producer and consumer machine identities, with fresh-origin, exact-SHA hosted-native, and independent-audit proof.
- A one-capture declared-initial reachability tracer with finite deterministic budgets, scalar snapshot labels, and strict future diagnostic contracts.
- Strict-RED hostile output/logging contracts and a fail-closed Phase 19 pure/fresh-compiled suite definition are ready for the production-owner plans.
- Iterative SCC and condensation-depth analysis with sparse-first validation, dense allocation preflight, and deterministic bounded path enumeration.
- Duplicate-safe comparison and batch schemas now preserve input position, while snapshot-backed validation reports publish bounded SCC, depth, sparse, and completion status.
- Metadata-only sync/async tracing with explicit bounded redaction and a generation-safe logging handle that preserves application-owned handlers.
- Opaque snapshot-order diagrams plus one-capture sparse JSON and Markdown output with deterministic grammar-safe text and explicit dense compatibility.
- Complete user and maintainer documentation for bounded snapshot diagnostics, grammar-safe rendering, fail-closed trace redaction, and reversible logging ownership.
- A deterministic hardened-behavior oracle now proves source, exact pure-wheel, and exact compiled-wheel lifecycle parity from isolated installed environments.
- Explicit compiled builds now fail closed, and bounded source archives prove installed pure and compiled child wheels with SHA-256 parent lineage.
- Canonical release evidence now enforces an exact artifact matrix, while v0.3.0 identity is verified statically and at tag time without creating a tag.
- Truthful categorical Phase 16-19 provenance with non-gating retrospective observations and one ADR-backed three-exception slots policy.
- Four-operation O(1) evidence and a native-origin-first installed-wheel benchmark now gate a three-sample 200,000 ops/sec median without allowing historical or pure observations to substitute.
- Exact-SHA native release evidence, a v0.3.0 tag-only aggregate-and-identity release gate, and a non-authorizing local readiness projection.

---

## v0.2.3 Timing Condition Helpers (Shipped: 2026-04-05)

**Phases completed:** 3 phases (12–14), 15/15 requirements satisfied, 722 tests passing

**Key accomplishments:**

- `TimeoutCondition(seconds)` — allows transitions within a time window, blocks after timeout (Phase 12)
- `CooldownCondition(seconds)` — enforces minimum interval between successful triggers (Phase 12)
- `ElapsedCondition(seconds)` — gates transitions until elapsed time threshold is met (Phase 12)
- All timing conditions use `time.monotonic()`, `__slots__`, `reset()`, and `**kwargs` in `check()` (Phase 12)
- 27 new tests: unit tests (18), FSM integration tests (8), throughput benchmark (1) (Phase 13)
- Timing condition throughput verified ≥ 200k ops/sec compiled, ≥ 30k pure Python (Phase 13)
- README updated with timing condition examples; Sphinx autodoc covers all three (Phase 14)

---

## v0.2.2 Introspection & Agent Tooling (Shipped: 2026-04-05)

**Phases completed:** 6 phases (7–11.1), 21/21 requirements satisfied, 695 tests passing, 1.2M ops/sec

**Key accomplishments:**

- `StateMachine.to_dict()` / `from_dict()` topology serialization roundtrip (Phase 7)
- Opt-in transition history with `TransitionRecord`, bounded buffer, zero-cost when disabled (Phase 8)
- `to_plantuml()` state diagram visualization in `visualization.py` (Phase 9)
- `to_json()` machine-readable FSM export with topology + reachability + cycle + quality analysis (Phase 10)
- Performance verification & README documentation updates (Phase 11)
- History-enabled throughput benchmark — gap closure for PERF-02, ≤ 2× degradation verified (Phase 11.1)

---

## v0.2.1 Code Health & Quality (Shipped: 2026-04-04)

**Phases completed:** 6 phases, 1 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---
