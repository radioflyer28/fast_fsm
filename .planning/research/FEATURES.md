# Feature Research: v0.3.0 Reliability & Runtime Hardening

**Domain:** High-performance in-process Python finite state machine library
**Researched:** 2026-08-29
**Confidence:** MEDIUM overall; HIGH for codebase-derived scope, MEDIUM for ecosystem-derived semantics

## Research Conclusion

v0.3.0 should harden the behavior users already invoke, not expand the library into
a workflow engine. The central user-facing contract should be: a trigger either
does not commit a state change, or commits exactly one coherent state change whose
callback outcome is reported truthfully. Arbitrary callback side effects cannot be
made transactional by an in-memory FSM, so automatic rollback would promise more
than the library can deliver.

The selected safe-default posture means reentrant firing must fail immediately
instead of deadlocking, queueing implicitly, or overwriting an outer transition.
Independent concurrent callers should be serialized. Synchronous machines need
thread serialization; asynchronous machines need task serialization on one event
loop and must reject unsupported cross-loop use. These safety mechanisms must retain
the existing 200,000 `trigger()` operations/second floor.

The other concerns resolve into three contracts: construction must produce one
canonical graph, sync and async entry points must apply the same rules, and
design-time tooling must be correct and bounded. Release integrity is part of the
feature, because users cannot rely on runtime guarantees that were tested against a
different version or execution path than the artifact they installed.

## Feature Landscape

### Table Stakes (Users Expect These)

| Capability | Expected user-visible behavior | Complexity | Acceptance boundary |
|------------|--------------------------------|------------|---------------------|
| Canonical graph construction | Every source and destination resolves to exactly one registered `State`; unknown endpoints and a different object with a duplicate name fail during construction | HIGH | Multi-source additions are all-or-nothing; runtime, `states`, reset, validation, and rendering observe the same objects |
| Sealed builder lifecycle | `build()` is idempotent, and every builder mutator after the first successful build raises immediately instead of being silently ignored | MEDIUM | State, transition, condition, sync callback, async callback, and mode mutators all follow the same rule |
| Guard argument contract | Guards receive supported positional context and the same sanitized keyword context from `can_trigger*()` and `trigger*()` | HIGH | Sync/async, callable/object, `condition=`, and `unless=` paths have parity; private or excessive keyword context cannot bypass one path |
| Correct async builder detection | A nested async component, including `unless=AsyncCondition(...)`, selects `AsyncStateMachine` in auto mode | MEDIUM | Detection recursively inspects wrappers/composites and never calls `asyncio.run()` from an already-running loop |
| Integrated declarative dispatch | Calling normal `trigger()`/`trigger_async()` invokes the matching decorated handler exactly once, not just its metadata guard | HIGH | Handler errors are handled at a documented pre-commit stage; direct event handling and machine dispatch cannot double-invoke it |
| Valid bounded history | `max_entries` must be a positive integer; invalid capacity fails when history is enabled, and a bounded buffer evicts oldest records in O(1) | LOW | History remains zero-cost when disabled, copy-on-read, and records every committed state change even when a later callback reports failure |
| Stage-aware callback failure | Callback processing stops at the first exception; pre-commit failure leaves the source active, while post-commit failure leaves the destination active and is returned/re-raised as failure | HIGH | No successful result is returned when a required callback failed; failure stage and underlying exception remain inspectable; notification occurs once |
| Explicit commit boundary | Guards, state permission, declarative action, before-transition callbacks, and exit callbacks complete before the one state assignment; entry/after callbacks run after it | HIGH | Tests assert state, result, failure notification, and history at every failure point in sync and async paths |
| Reentrancy rejection by default | A callback invoking any state/topology mutator on the same machine fails immediately with a clear error; it cannot deadlock, queue silently, or overwrite the outer transition | HIGH | Sync and async tests cover nested trigger, `force_state`, reset/restore, and graph mutation plus state, result, callbacks, and lock release after failure |
| Serialized concurrent access | Independent sync callers and same-loop async tasks serialize trigger, state-control, and topology-mutation entry points and evaluate against state/topology current when each acquires ownership | HIGH | Thread and task interleaving tests are deterministic; checks observe a coherent snapshot; an async machine is bound to one event loop and rejects cross-loop access |
| Sync/async semantic parity | Equivalent machine definitions produce equivalent transition selection, sanitization, callback order, results, history, and failure semantics | HIGH | The same parameterized contract suite runs against sync and async implementations |
| Non-blocking async contract | Async callbacks are awaited; synchronous callbacks run inline and are explicitly required to be short/non-blocking rather than being silently moved to worker threads | MEDIUM | Documentation explains event-loop blocking and directs I/O work to async callbacks; automatic thread offload is not introduced |
| Stable graph snapshot for tools | Validation, comparison, JSON, and renderers consume one immutable internal topology snapshot including the declared initial state | HIGH | Diagnostics no longer infer the initial state from current state or dictionary insertion order and do not couple independently to private tables |
| Correct comparison and cycle results | Empty comparisons return a documented empty aggregate; duplicate FSM names raise `ValueError` before analysis instead of overwriting results; cycle membership includes every member of each directed cycle | MEDIUM | Empty aggregate has count/average zero and no best machine; SCC-based tests cover self-loops and cycles longer than two states |
| Bounded deterministic diagnostics | Potentially quadratic/output-exponential operations accept or apply explicit work/result budgets and report truncation rather than hanging or silently returning a partial full result | HIGH | Limits are deterministic; dense adjacency and path generation fail or truncate explicitly; ordinary sparse graphs retain complete output |
| Safe visualization output | Mermaid and PlantUML use stable opaque aliases plus separately escaped labels and trigger text | MEDIUM | Punctuation, Unicode, quotes, line breaks, directive-like text, and colliding sanitized names render as distinct inert labels |
| Application-owned logging | Importing the library installs at most `NullHandler`; configuration never clears unrelated handlers and any helper-owned handler is idempotent and reversible | MEDIUM | Logger name/propagation are documented; application handlers survive configure/unconfigure cycles |
| Payload-redacted trace output | Default trace records structural facts such as trigger name and context key names, never raw positional or keyword values | MEDIUM | Tests use tokens, passwords, PII-like values, and newline/control text and assert they do not appear in logs |
| Auditable release identity | Git tag, `pyproject.toml`, built core metadata, installed `fast_fsm.__version__`, changelog section, docs, and advertised test count agree | MEDIUM | CI fails before publish on any mismatch; v0.3.0 notes are moved out of `Unreleased` only for the matching release |
| Strict compiled artifact release | Release builds fail if a compiled wheel was requested but mypyc compilation or extension inclusion fails | HIGH | Each supported platform/Python wheel is installed in isolation, module origin is asserted as compiled, and the semantic suite runs against it |
| Real pure-Python verification | Source-only tests run in an environment where no stale `.so`/`.pyd` can shadow `core.py` | MEDIUM | CI asserts `core.__file__` for both modes and applies equivalent tests; source coverage measures `core.py` rather than an ignored local extension |
| Green, stable quality baseline | Tests, formatting, lint, mypy/mypyc compatibility, docs, doctests, artifact checks, and throughput gates all pass from a clean checkout | MEDIUM | Pin the alpha `ty` tool if retained; stable mypy remains release-required; optional tools cannot redefine a green release gate unexpectedly |
| Honest performance/memory claims | Documentation states measured scope and the deliberate `CompiledFuncCondition` storage exception instead of claiming universal slots behavior | LOW | Test counts and benchmark context are generated or release-checked; no unqualified “all core classes” claim conflicts with reality |

### Recommended Transition Failure Semantics

| Failure point | Current state after failure | Result | Remaining callbacks | History |
|---------------|-----------------------------|--------|---------------------|---------|
| Guard or state permission | Source | Failed, no commit | None | No record |
| Declarative action / before / exit callback | Source | Failed, no commit | Stop immediately | No record |
| State assignment | Source if assignment cannot complete | Failed, no commit | None | No record |
| Enter / after / trigger-specific callback | Destination | Failed, committed | Stop immediately, then one failure notification | Record committed transition |
| Reentrant call from any callback | Outer transition follows its own callback-failure rule; nested call does not commit | Nested call fails immediately | No nested callbacks | No nested record |
| Concurrent independent call | Evaluated after prior owner releases machine | Normal success/failure | Normal order | Normal committed record |

This is state-atomic, not side-effect-atomic. A callback that has already written to
a database, sent a message, or mutated external state cannot be safely undone by the
FSM. The mature `transitions` library similarly documents that pre-state-change
callback failures leave the source active, post-state-change failures preserve the
destination, and no automatic rollback occurs. The v0.3.0 improvement is that Fast
FSM must never swallow such a failure and report success.

### Differentiators (Competitive Advantage)

| Capability | Value proposition | Complexity | Notes |
|------------|-------------------|------------|-------|
| Safe defaults above 200k ops/sec | Users do not have to trade basic correctness for Fast FSM's core performance claim | HIGH | Benchmark uncontended lock/owner checks, guards, failure paths, and history separately |
| One executable parity contract | Sync, async, builder, declarative, compiled, and source modes are validated as one product rather than parallel implementations | HIGH | Parameterized conformance tests become the strongest regression defense |
| Bounded agent-grade introspection | `to_json()` and validators remain safe and deterministic on generated or adversarial graphs | HIGH | Include limit/truncation metadata so tools can distinguish “complete” from “budget exhausted” |
| Installed-artifact proof | CI demonstrates what users install, not merely what passes from the checkout | HIGH | Assert distribution metadata, extension origin, public imports, semantics, and throughput after wheel installation |
| Secure diagrams and trace logs by default | User-controlled names and event context can flow through tooling without becoming executable diagram syntax or secret-bearing logs | MEDIUM | Opaque IDs plus escaped labels are simpler and safer than increasingly complex sanitizers |
| Truthful failure observability | Integrations can distinguish not-committed failures from committed transitions with failed lifecycle work | MEDIUM | Preserve existing result/exception style while making stage and commit status inspectable |

### Anti-Features (Commonly Requested, Often Problematic)

| Anti-feature | Why it sounds useful | Why it is problematic here | Recommended alternative |
|--------------|----------------------|----------------------------|-------------------------|
| Automatic rollback of arbitrary callbacks | Appears to make transitions transactional | External side effects are neither knowable nor reversible; rollback callbacks can fail or create new side effects | Define one state commit point, fail truthfully, and let applications implement compensation |
| Implicitly queue reentrant triggers | Avoids rejecting work fired from callbacks | Changes return timing and state assumptions, can create unbounded queues, and hides accidental recursion | Reject reentry by default; consider an explicit queue feature only in a later API milestone |
| Reentrant lock as the only safety mechanism | Allows same-thread nested acquisition | It permits exactly the nested mutation that currently corrupts outer transitions | Track transition ownership and reject the owner before lock acquisition |
| Automatic worker-thread execution for sync callbacks | Could keep an event loop responsive | Changes thread affinity, context, ordering, exception timing, and safety of user code | Require non-blocking sync callbacks in async machines and provide async callbacks for I/O |
| Silent endpoint auto-registration or duplicate replacement | Makes graph construction look convenient | Hides typos and leaves diagnostics/object identity ambiguous | Require explicit canonical registration and reject inconsistent topology atomically |
| Unbounded exhaustive diagnostics | Produces every path/cycle in one call | Output itself can be exponential even with an optimal algorithm | Provide budgets, deterministic truncation, sparse/internal algorithms, and explicit completeness metadata |
| Raw payload trace mode | Seems helpful for debugging | Trigger context commonly carries tokens, PII, keys, and attacker-controlled control text | Log names, counts, and key sets; require application logging for values |
| Library takeover of logging handlers | One helper makes logs appear immediately | Breaks host configuration and tests and can duplicate output | Use `NullHandler`; make explicit helper changes additive, marked, idempotent, and reversible |
| Runtime NetworkX dependency | Offers mature graph algorithms quickly | Violates the single-runtime-dependency constraint and adds weight to optional design tooling | Implement the small SCC/budget algorithms internally and use NetworkX docs as algorithmic evidence |
| Silent pure-Python fallback in release wheels | Lets builds finish on machines without a compiler | Publishes an artifact that violates the performance promise under the expected platform tag | Allow intentional source-only builds, but make compiled release mode strict |
| Split `core.py` into multiple compiled modules | Reduces source-file concentration | Conflicts with the established single mypyc compilation-unit constraint and may slow cross-unit calls | Share internal helpers inside `core.py`; enforce parity through tests |
| Broad API expansion during hardening | Could address every future policy at once | Increases review surface before core behavior is trustworthy | Keep existing public symbols; add only observability/configuration required by hardening |

## Feature Dependencies

```text
[Release identity + green baseline]
    └──requires before──> [Runtime behavior changes]
                            └──validated by──> [Installed source/compiled parity]
                                                    └──gates──> [Release publish]

[Canonical graph invariants]
    └──enables──> [Stable graph snapshot]
                     ├──enables──> [Correct validator/comparison/cycle analysis]
                     └──enables──> [Collision-free visualization]

[Explicit transition commit boundary]
    ├──requires──> [Stage-aware callback failures]
    ├──requires──> [Integrated declarative dispatch]
    ├──enables──> [Reentrancy rejection]
    └──enables──> [Serialized concurrent access]

[Unified guard context]
    └──enables──> [Sync/async parity]
                     ├──enables──> [Async builder correctness]
                     └──enables──> [Shared conformance suite]

[Bounded graph snapshot algorithms]
    └──enables──> [Deterministic diagnostic budgets]
                     └──enables──> [Safe agent-grade JSON]
```

### Dependency Notes

- **Establish the release baseline first:** Correct version/changelog/test-count
  drift and make current gates green before behavioral work, so subsequent
  failures can be attributed to v0.3.0 changes.
- **Canonical topology precedes diagnostics:** Validator and renderer fixes will
  remain fragile until both consume one invariant-preserving snapshot.
- **Commit semantics precede locking:** A lock only prevents interleaving; it does
  not define whether state changed after a callback exception. Define and test the
  lifecycle first, then serialize it.
- **Reentry detection precedes lock acquisition:** Otherwise a primitive lock
  converts a clear programming error into a deadlock.
- **Sync/async parity precedes builder repair:** Recursive async detection is only
  useful if the selected async machine applies the same context and failure rules.
- **Artifact parity follows semantic tests:** One contract suite should be reused
  for interpreted modules and installed compiled wheels rather than creating a
  weaker compilation smoke suite.
- **Performance gating follows correctness:** Benchmark the final owner/lock path
  and fail the milestone if normal `trigger()` falls below 200,000 operations/sec.

## v0.3.0 Milestone Definition

### Launch With

- Canonical graph and sealed builder invariants.
- Unified guard context, declarative dispatch, history validation, and recursive
  async detection.
- Explicit state commit boundary with fail-fast, truthful callback outcomes.
- Default reentrancy rejection and serialized thread/task access.
- Sync/async/source/compiled conformance coverage.
- Correct initial-state, empty/duplicate comparison, SCC cycle membership, and
  deterministic diagnostic budgets.
- Collision-free, escaped Mermaid and PlantUML output.
- Application-owned logging and payload-redacted trace output.
- One auditable version/changelog/docs/test baseline and strict installed-wheel
  verification on supported platforms.
- Green formatting, lint, stable type checking, docs, doctests, tests, and
  throughput gates.
- Documentation of the `CompiledFuncCondition` storage exception and of sync
  callback blocking in async machines.

### Include If It Does Not Expand the Public Surface Materially

- An application-supplied trace redactor, provided raw values remain unavailable
  to default formatters.
- A sparse adjacency export if it can be additive; otherwise enforce a dense
  matrix budget and defer the new representation.
- A history memory estimate; otherwise document O(`max_entries`) retention and
  validate positive capacity.

### Recommended Deferrals

- Opt-in queued reentrant firing and configurable queue overflow policies.
- Automatic rollback/compensation orchestration for application side effects.
- Cross-event-loop sharing of one `AsyncStateMachine`.
- Automatic thread offload or parallel execution of callbacks.
- A public generalized graph-snapshot protocol; keep the v0.3.0 snapshot internal.
- Replacing `ty` entirely; pin it and keep stable mypy as the required gate first.
- Redesigning `CompiledFuncCondition` solely to remove `__dict__` unless measurement
  shows material user impact.
- Splitting the mypyc compilation unit, scheduler/auto-fire timers, topology-rich
  snapshot v2, and unrelated API expansion.

## Feature Prioritization Matrix

| Capability group | User value | Implementation cost | Priority | Rationale |
|------------------|------------|---------------------|----------|-----------|
| Release identity and green baseline | HIGH | MEDIUM | P1 | All later evidence depends on knowing which version/artifact was tested |
| Graph and builder invariants | HIGH | HIGH | P1 | Prevents machines whose runtime and tools disagree |
| Transition commit and callback failure semantics | HIGH | HIGH | P1 | Safe-default decision and primary correctness boundary |
| Reentrancy and concurrency safety | HIGH | HIGH | P1 | Prevents silent state corruption and deadlock |
| Guard/declarative/sync-async parity | HIGH | HIGH | P1 | Repairs reproduced public-API failures across all dispatch modes |
| History correctness and O(1) eviction | HIGH | LOW | P1 | Small fix on an advertised capability and hot path |
| Diagnostic correctness and budgets | HIGH | HIGH | P1 | Fixes false results and unbounded behavior on configuration-driven graphs |
| Visualization escaping and aliasing | HIGH | MEDIUM | P1 | Prevents collisions and treats user labels as inert data |
| Logging ownership and payload redaction | HIGH | MEDIUM | P1 | Removes secret exposure and application-wide side effects |
| Installed source/compiled parity | HIGH | HIGH | P1 | Required for the performance and compatibility promise |
| Custom trace redactor | MEDIUM | MEDIUM | P2 | Useful flexibility after safe no-values default exists |
| Sparse public adjacency representation | MEDIUM | HIGH | P2 | Additive scalability improvement; budgets can provide v0.3.0 safety |
| History memory estimator | LOW | LOW | P3 | Documentation gives adequate control after O(1) storage is fixed |
| Queued reentrant firing mode | MEDIUM | HIGH | P3 | New semantics and API surface; reject safely in this milestone |
| Callback compensation framework | LOW | HIGH | P3 | Belongs in an integration/workflow layer, not the core FSM |

**Priority key:** P1 is required for v0.3.0; P2 is conditional on contained API
impact; P3 is deferred.

## Ecosystem Behavior Comparison

| Concern | Current Fast FSM | Relevant ecosystem behavior | Recommended v0.3.0 behavior |
|---------|------------------|-----------------------------|-----------------------------|
| Callback exception | Logged/swallowed; success may be returned | `transitions` stops the callback chain, propagates/handles the error, keeps source before commit and destination after commit | Stop, expose failure, preserve actual commit state, never pretend rollback |
| Reentrant firing | Unsynchronized nested mutation | `transitions` makes queueing explicit; Python primitive locks would otherwise deadlock on same-owner reentry | Reject owner reentry immediately; do not queue by default |
| Concurrent firing | Can interleave | Python provides separate thread and same-loop task mutexes; `asyncio.Lock` is not thread-safe | Serialize threads or same-loop tasks; reject unsupported cross-loop ownership |
| Async blocking | Sync callbacks run on event loop | Python documents `asyncio.to_thread()` for explicitly selected blocking I/O | Keep deterministic inline contract; require async callbacks for I/O rather than silently changing thread context |
| Library logging | Helper clears handlers and trace exposes values | Python recommends named loggers and only `NullHandler`; OWASP recommends removing/masking tokens, secrets, and PII | Preserve application handlers and omit raw values by default |
| Diagram names | Sanitized IDs can collide; PlantUML text is raw | Mermaid and PlantUML distinguish aliases/IDs from display labels | Opaque unique IDs plus target-specific escaped labels |
| Cycle diagnostics | DFS back-edge endpoints omit members | SCC decomposition identifies cyclic components without enumerating every cycle | SCC membership including self-loops; budget only output-expanding analyses |
| Compiled release | Compilation failure may silently fall back | PyPA expects platform wheels for extensions and installed-artifact validation; mypyc supports selected compiled modules | Strict compiled mode, isolated wheel tests, explicit origin assertion, intentional source fallback only |

## Concern Coverage Audit

| `CONCERNS.md` category | Covered by |
|------------------------|------------|
| Core concentration | Internal shared lifecycle/guard/snapshot helpers inside the single compilation unit; parity tests; module split remains deferred constraint |
| Builder mutability | Sealed builder lifecycle |
| Graph registration | Canonical graph construction and atomic multi-source validation |
| Optional compilation | Strict compiled release mode and installed-wheel proof |
| Slots exception | Honest measured documentation; redesign deferred unless impact is material |
| Known runtime bugs | Guard arguments, history capacity, declarative dispatch, validator initial state, duplicate/empty comparison, nested async `unless=`, SCC cycle membership |
| Security | Redacted trace context, sync/async sanitization parity, application-owned logging, escaped diagram labels |
| Performance | O(1) history, bounded graph diagnostics, explicit async callback contract, 200k hot-path gate |
| Fragile runtime areas | Stage-aware callback failure, reentry/concurrency safety, stable graph snapshot |
| Scaling limits | Positive bounded history, SCC algorithms, deterministic path/matrix budgets, optional sparse export |
| Dependency risks | Pin alpha `ty`, retain stable mypy gate, strict mypyc wheel matrix, intentional pure/source path |
| Missing critical contracts | Explicit state commit/failure semantics and thread/task/event-loop ownership |
| Test gaps | Shared sync/async contract suite, graph/builder edge cases, isolated source/compiled runs, release/quality gates |

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Existing defect scope | HIGH | Direct codebase audit includes executable reproductions and line-level evidence |
| Callback/commit recommendation | MEDIUM | Cross-checked against official `transitions` behavior; arbitrary side-effect rollback remains application-specific |
| Concurrency recommendation | MEDIUM | Based on official Python lock/task semantics; performance impact must be benchmarked in this codebase |
| Logging/security recommendation | MEDIUM | Official Python library guidance and OWASP agree; custom-redactor shape remains a design choice |
| Diagnostics recommendation | MEDIUM | Established SCC/output-sensitive algorithm behavior; exact default budgets require project benchmarks |
| Visualization recommendation | MEDIUM | Official grammars support alias/label separation; exact escaping functions require renderer tests |
| Release recommendation | MEDIUM | Current PyPA and mypyc guidance support the artifact workflow; platform matrix details remain repository-specific |

## Sources

Primary and project sources, with confidence tiers produced by the research seam:

- [Python 3.10 `threading` documentation](https://docs.python.org/3.10/library/threading.html) — thread locks and reentrant locks. **MEDIUM**
- [Python 3.10 asyncio synchronization primitives](https://docs.python.org/3.10/library/asyncio-sync.html) — task mutex fairness and non-thread-safety. **MEDIUM**
- [Python 3.10 coroutines and tasks](https://docs.python.org/3.10/library/asyncio-task.html) — explicit `to_thread()` behavior for blocking work. **MEDIUM**
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library) — library-owned logger and handler guidance. **MEDIUM**
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#data-to-exclude) — sensitive-data exclusion and masking. **MEDIUM**
- [`transitions` official project documentation](https://github.com/pytransitions/transitions#callback-execution-order) — callback order, exception behavior, and explicit queued transitions. **MEDIUM**
- [Mermaid state diagram syntax](https://mermaid.js.org/syntax/stateDiagram.html) — state IDs and descriptions. **MEDIUM**
- [PlantUML state diagram syntax](https://plantuml.com/en/state-diagram) — quoted names and aliases. **MEDIUM**
- [NetworkX strongly connected components](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.strongly_connected_components.html) — SCC membership algorithm. **MEDIUM**
- [NetworkX simple cycles](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cycles.simple_cycles.html) — output-sensitive cycle enumeration complexity. **MEDIUM**
- [PyPA core metadata specification](https://packaging.python.org/en/latest/specifications/core-metadata/) and [version specification](https://packaging.python.org/en/latest/specifications/version-specifiers/) — required and normalized version identity. **MEDIUM**
- [PyPA packaging flow](https://packaging.python.org/en/latest/flow/) and [tool recommendations](https://packaging.python.org/en/latest/guides/tool-recommendations/) — modern builds and platform-wheel CI. **MEDIUM**
- [mypyc getting started](https://mypyc.readthedocs.io/en/latest/getting_started.html) — selective compilation, wheel builds, and interpreted-mode workflow. **MEDIUM**
- [Project concerns](../codebase/CONCERNS.md), [architecture](../codebase/ARCHITECTURE.md), [project](../PROJECT.md), and repository tests/source — milestone scope and reproduced failures. **HIGH**

---
*Feature research for: Fast FSM v0.3.0 Reliability & Runtime Hardening*
*Researched: 2026-08-29*
