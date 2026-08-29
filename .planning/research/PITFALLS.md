# Pitfalls Research: v0.3.0 Reliability & Runtime Hardening

**Domain:** High-performance in-process Python finite state machine library
**Researched:** 2026-08-29
**Confidence:** MEDIUM overall; HIGH for codebase-specific failure modes, MEDIUM for externally validated remedies

## Risk Classification

| Class | Meaning in this milestone | Release posture |
|-------|---------------------------|-----------------|
| Safety-critical | Can commit the wrong state, report success after required work failed, deadlock, race, expose secrets, or ship a materially different artifact | Must be fixed before v0.3.0 release |
| Correctness-critical | Produces a contradictory graph, false diagnostic result, or sync/async behavioral mismatch | Must be fixed before v0.3.0 release |
| Performance debt | Preserves correctness but violates the 200,000 `trigger()` operations/second floor or becomes unbounded on realistic diagnostic graphs | Must be measured and bounded before release |
| Tooling/release debt | Lets source, metadata, tests, and installed wheels disagree | Must gate release, though it need not precede local runtime implementation |

The most important distinction is between **state atomicity** and **side-effect atomicity**. Fast FSM can guarantee one coherent state commit boundary. It cannot automatically undo a database write, message send, file operation, or other side effect performed by user callbacks. v0.3.0 should report failures truthfully and document compensation, not promise rollback it cannot provide.

## Critical Pitfalls

### Pitfall 1: Adding locks before defining the transition commit boundary

**Class:** Safety-critical

**What goes wrong:**
A mutex prevents two callers from interleaving, but the transition still has ambiguous semantics. A callback can fail after some lifecycle work ran, history can disagree with the active state, and the caller can receive either success or failure without knowing whether the destination was committed. Locking the current `_execute_transition()` would merely serialize the existing ambiguity.

**Why it happens:**
Concurrency feels like the obvious fix for races, so implementation starts with `Lock` or `asyncio.Lock`. The current code, however, catches every callback exception around a state assignment in the middle of the callback chain and always returns success. There is no stage or committed-state field in `TransitionResult`.

**How to avoid:**

- Define one explicit state assignment as the commit boundary before introducing synchronization.
- Treat guards, state permission, declarative action, before callbacks, and exit callbacks as pre-commit. Failure leaves the source active and stops the chain.
- Treat enter, after, and trigger-specific callbacks as post-commit. Failure leaves the destination active, stops the chain, and reports `committed=True` with the failing stage and original exception available.
- Record history immediately at commit, before any post-commit callback or `await`, so cancellation cannot produce an unrecorded committed state.
- Invoke failure observers once after primary failure capture. Observer failures must be secondary and must not replace the original failure.
- Never advertise automatic rollback of callback side effects. Document application-level compensation instead.

**Warning signs:**

- A callback exception is logged while `TransitionResult.success` remains true.
- Tests assert only the final state, not callback order, failure stage, commit status, history, and notification count.
- History is appended only after all callbacks complete.
- A proposed rollback sets `_current_state` back but cannot account for already completed external side effects.

**Recovery:**
Freeze callback-order changes, add a stage-by-stage contract matrix, and reproduce failures at every callback slot. If a released implementation already reported false success, add explicit result metadata and release notes rather than silently changing failure interpretation again.

**Phase to address:** Phase 2 — Atomic Transition Lifecycle, after canonical dispatch is established and before concurrency work.

---

### Pitfall 2: Using a reentrant lock, or a primitive lock without owner detection

**Class:** Safety-critical

**What goes wrong:**
An `RLock` allows the same callback to start a nested transition and recreate the current overwrite bug. A primitive `Lock` rejects nothing; the nested call blocks forever waiting for its own outer transition. The async equivalent can suspend forever on the same task. Neither outcome implements the selected safe default of immediate reentrancy rejection.

**Why it happens:**
Lock reentrancy is confused with FSM reentrancy. Python documents `RLock` specifically as allowing recursive acquisition, while primitive locks block subsequent acquisition. The FSM needs serialization between independent owners but rejection for the current owner.

**How to avoid:**

- Track the active owner separately from the serialization primitive: thread identity for sync execution and task identity plus event-loop identity for async execution.
- Check same-owner reentry before blocking and raise/return a dedicated, inspectable reentrancy failure immediately.
- Use a non-reentrant per-instance lock to serialize independent sync callers; use `asyncio.Lock` for same-loop async tasks.
- Bind an `AsyncStateMachine` to one running event loop on first mutating use and reject cross-loop or cross-thread use explicitly. `asyncio` locks are not thread-safe.
- Protect every state/topology mutator, not only `trigger*()`: `force_state`, `reset`, `restore`, state/transition registration, and callback registration must not mutate an in-flight machine.
- Release owner markers and locks in `finally`. Do not catch and suppress `CancelledError`; before commit it leaves the source active, after commit it leaves the destination active and propagates after invariant cleanup.

**Warning signs:**

- The design says “thread-safe” but specifies only one lock and no ownership state.
- Reentrant tests hang instead of completing with a deterministic failure.
- Async tests use only one task and never cancel at each `await` point.
- `trigger()` is locked but `force_state()` or `add_transition()` is not.
- Cross-loop access produces a low-level “bound to a different event loop” error instead of a Fast FSM contract error.

**Recovery:**
Add a watchdog-backed reentrancy test first, then introduce owner detection ahead of acquisition. For stuck async machines, guarantee cleanup with structured `try/finally` and test that a normal transition succeeds after every injected cancellation.

**Phase to address:** Phase 3 — Ownership, Reentrancy, and Concurrency.

---

### Pitfall 3: Treating callback failure as transactional rollback

**Class:** Safety-critical

**What goes wrong:**
The library resets `_current_state` after a callback fails and claims the transition was rolled back, while earlier callbacks may already have sent messages, acquired resources, or changed external storage. Retrying can duplicate those effects. Rollback callbacks can also fail, producing an even less knowable state.

**Why it happens:**
“Atomic transition” is interpreted as an ACID transaction rather than an in-memory state assignment. Mature FSM callback ordering demonstrates the realistic boundary: pre-change failures retain the source; post-change failures retain the destination; no automatic rollback occurs.

**How to avoid:**

- Use the term **state-atomic** in requirements and documentation.
- Stop the chain on first failure and expose whether the state committed.
- Recommend idempotent callbacks and application-owned compensation for external effects.
- Keep `safe_trigger()` as an exception-to-result barrier, not as a mechanism that converts a partially failed committed transition into success.

**Warning signs:**

- Requirements include “rollback callbacks” without defining external transaction participation.
- A post-enter failure causes history deletion or a second state assignment back to the source.
- Retry guidance does not discuss idempotency or duplicate side effects.

**Recovery:**
Remove the rollback promise, preserve the actual committed state, and expose the primary callback failure. Applications that consumed the ambiguous behavior need reconciliation using history and domain-specific compensation.

**Phase to address:** Phase 2 — Atomic Transition Lifecycle.

---

### Pitfall 4: Repairing graph validation without atomic construction

**Class:** Correctness-critical

**What goes wrong:**
`add_transition()` can mutate some source buckets before discovering an invalid endpoint, duplicate state names can replace canonical objects while entries retain old objects, and builder changes after `build()` disappear into staging lists. Runtime state, serialization, validation, and diagrams then describe different machines.

**Why it happens:**
Current construction accepts strings and objects through several convenience paths, normalizes and mutates incrementally, and lets diagnostics infer topology directly from private dictionaries. Fan-out additions make partial mutation especially easy.

**How to avoid:**

- Resolve and validate all source and destination endpoints before changing any table.
- Require every endpoint to resolve to exactly one registered `State` object. Reject an unknown state and reject a different object with an existing name; accepting the identical object idempotently is safe.
- Apply fan-out transition additions all-or-nothing.
- Reject every builder mutator after the first successful `build()`; keep repeated `build()` idempotent.
- Add one immutable internal graph snapshot containing the declared initial state, canonical states, and transitions. Validation and rendering consume only this snapshot.
- Run invariant checks under the same ownership boundary as topology mutation.

**Warning signs:**

- `_states[name] is not entry.to_state` for any registered endpoint.
- `_transitions` contains a source absent from `_states`.
- `next(iter(_states))` is used as the initial-state contract.
- A bulk addition raises after leaving earlier transitions installed.
- A builder mutator succeeds after `build()` but the returned machine does not change.

**Recovery:**
Fail validation on contradictory graphs instead of attempting silent repair. Reconstruct a canonical machine from an explicit topology snapshot; do not guess which duplicate object was intended.

**Phase to address:** Phase 1 — Canonical Graph and Dispatch Invariants.

---

### Pitfall 5: Fixing one dispatch path while its twins retain old semantics

**Class:** Safety- and correctness-critical

**What goes wrong:**
Sync and async machines disagree about condition sanitization, positional arguments, callback order, declarative handlers, history, or failures. `can_trigger*()` approves work that `trigger*()` rejects. `unless=AsyncCondition` remains hidden inside `NegatedCondition`, so the builder selects a sync machine. Inherited sync methods on an async machine may attempt to execute async conditions incorrectly.

**Why it happens:**
`core.py` contains duplicated sync/async dispatch and several construction adapters. Type checks inspect only outer wrappers. The existing test suite is feature-oriented rather than one executable parity contract.

**How to avoid:**

- Create one transition-context preparation policy for supported `*args`, sanitized `**kwargs`, and condition evaluation.
- Define a recursive condition-capability protocol so wrappers such as negation expose nested async requirements.
- Wire declarative handlers into normal dispatch exactly once and place their failure stage explicitly before commit.
- Parameterize one semantic contract over sync/async, `condition=`/`unless=`, callable/object conditions, `can_trigger*()`/`trigger*()`, direct/builder construction, and declarative/ordinary states.
- Enforce API mode: async-only components cannot run through inherited sync entry points.
- Do not automatically move sync callbacks to worker threads. That changes thread affinity, context variables, ordering, and exception timing; instead require short non-blocking sync callbacks in async machines and provide async callbacks for I/O.

**Warning signs:**

- A fix duplicates code into `trigger()` and `trigger_async()` instead of adding a shared policy and parity tests.
- Async tests omit private, excessive, positional, or wrapped guard context.
- The builder uses only `isinstance(condition, AsyncCondition)`.
- A decorated handler can be called directly but has no assertion proving normal trigger dispatch executes it once.

**Recovery:**
Stop adding path-specific patches and introduce a conformance matrix. Keep the single `core.py` compilation unit, but use small internal helpers and tables within it to make semantic drift visible.

**Phase to address:** Phase 1 — Canonical Graph and Dispatch Invariants, with failure ordering completed in Phase 2.

---

### Pitfall 6: Cancellation produces an impossible async state/history combination

**Class:** Safety-critical

**What goes wrong:**
An async task is cancelled after `_current_state` changes but before history is recorded, or while owner state remains set. The destination is active with no record, and all later callers are rejected or blocked. Catching broad exceptions can also convert cancellation into an ordinary failed result unexpectedly.

**Why it happens:**
Every `await` is an interruption point. The current async path runs the synchronous transition—including state mutation and history—then awaits extra callbacks, but the hardened lifecycle will likely add awaits earlier. Python cancellation requires `try/finally` cleanup and should generally propagate after cleanup.

**How to avoid:**

- Mark each await as pre-commit or post-commit in the lifecycle contract.
- Perform the state assignment and history append in one non-awaiting critical section.
- Use `async with` plus a `finally` that clears ownership even if cancellation is raised.
- Re-raise cancellation after invariant cleanup. Never let an `on_failed` observer suppress it.
- Inject cancellation before and after every awaited guard/callback in deterministic tests, then assert state, history, owner, lock usability, and remaining callback order.

**Warning signs:**

- Cancellation tests merely assert `CancelledError` without checking machine recovery.
- History recording occurs after an awaited enter or after callback.
- Owner cleanup exists only on `Exception`, not `BaseException`/`finally` paths.

**Recovery:**
Reconcile history from the active state only if application evidence exists; the library cannot infer the missing trigger safely. Fix the commit section first and add a “next transition succeeds” assertion to every cancellation test.

**Phase to address:** Phase 3 — Ownership, Reentrancy, and Concurrency.

---

### Pitfall 7: A passing source-tree suite is mistaken for compiled-wheel proof

**Class:** Tooling/release-critical with runtime impact

**What goes wrong:**
A release catches a mypyc or compiler failure and silently produces a pure-Python wheel, violating the performance promise. Conversely, a stale ignored `.so` shadows `core.py` while a task claims to test pure Python. Coverage reports `core.py` at 0%, and a smoke test misses compiled/interpreted differences.

**Why it happens:**
`setup.py` catches every `Exception` and intentionally falls back. Python import precedence is independent of `FAST_FSM_PURE_PYTHON`; the variable prevents a build but does not hide an existing extension. mypyc also documents behavioral differences involving type enforcement, native namespaces, monkey patching, introspection, tracing, and recursion.

**How to avoid:**

- Split build intent explicitly: strict compiled release mode fails closed; intentional source-only mode skips compilation.
- Build every supported platform/Python wheel, install it into a clean temporary environment outside the source tree, and run the semantic contract suite there.
- Assert wheel tags, distribution metadata version, `fast_fsm.__version__`, and `fast_fsm.core.__file__` suffix before tests.
- Run a separate clean source test where no `.so`/`.pyd` can exist on the import path; assert `.py` origin before collecting coverage.
- Run throughput against the installed compiled artifact and preserve the ≥200,000 operations/second release floor.
- Avoid conformance tests that require monkey-patching compiled native definitions; exercise public behavior with real objects.

**Warning signs:**

- A release job reports a compilation warning but exits successfully.
- A platform wheel is tagged `py3-none-any` or contains no extension.
- Tests run with the repository root or `src/` ahead of the installed wheel.
- “Pure Python” logs never print/assert the loaded module origin.
- Compiled CI runs only an import smoke test or benchmark subset.

**Recovery:**
Quarantine the artifact, rebuild from the tagged source in strict mode, inspect wheel contents/metadata, install into a fresh environment, and rerun the full contract and performance suites. Do not retag a different source tree under the same version.

**Phase to address:** Phase 0 — Release Baseline for current drift; full installed-artifact proof in Phase 5 — Compiled/Source Parity and Release Proof.

---

### Pitfall 8: Correct-looking diagnostics are incomplete or unbounded

**Class:** Correctness-critical and performance debt

**What goes wrong:**
Cycle output omits middle members, validation starts from the current rather than declared initial state, duplicate machine names overwrite comparison entries, empty comparisons divide by zero, and large graphs allocate dense matrices or enumerate exponentially many paths. A timeout or broad catch then returns a plausible partial result without identifying incompleteness.

**Why it happens:**
Diagnostics independently traverse mutable private tables with algorithms chosen for small examples. Back-edge endpoints do not equal full cycle membership. The number of simple paths can be factorial even when traversing one path is linear.

**How to avoid:**

- Analyze one immutable canonical graph snapshot with an explicit declared initial state.
- Compute complete cycle membership from strongly connected components; a component of size >1 is cyclic, and a singleton is cyclic only with a self-loop.
- Condense SCCs to a DAG and memoize longest-path analysis, or report that a requested metric is undefined/truncated under budget.
- Keep sparse adjacency internally. Refuse or explicitly truncate dense matrix/export requests above a documented node/cell budget.
- Apply deterministic budgets for nodes, edges, depth, expanded work, results, and output bytes. Return `complete: false` plus the exhausted limit; never label partial output as complete.
- Reject duplicate FSM names before analysis or preserve positional identity; define the empty aggregate with zero count/average and no best FSM.
- Prefer iterative traversal for adversarial graphs; mypyc documentation warns uncontrolled recursion can crash compiled code.

**Warning signs:**

- Cycle tests assert only `has_cycles`, not exact member sets for long cycles and self-loops.
- A diagnostic API accepts arbitrary config-derived graphs without any budget.
- `visited.copy()` appears inside every DFS branch.
- Output fields contain partial lists but no completeness/truncation metadata.
- A broad `except Exception` turns a validator error into `quality=None` silently.

**Recovery:**
Mark affected reports untrusted, rebuild from a canonical snapshot, and rerun with explicit budgets. If an API previously returned silent partial data, add completeness metadata before optimizing the algorithm.

**Phase to address:** Phase 4 — Bounded Diagnostics and Safe Output.

---

### Pitfall 9: Escaping labels without separating them from identifiers

**Class:** Security- and correctness-critical

**What goes wrong:**
Names such as `a-b` and `a b` collapse to the same Mermaid ID. Raw PlantUML or Mermaid title, state, trigger, and condition text can terminate a line, introduce a directive/comment, or corrupt the diagram. Markdown adjacency tables have separate pipe, backtick, and newline hazards.

**Why it happens:**
Sanitization is treated as character replacement. It is not injective and it mixes two concerns: graph identity and user-visible text. Each output grammar has different quoting rules.

**How to avoid:**

- Assign deterministic opaque aliases (`s0`, `s1`, … or stable hashes) from canonical state identity; never derive identity solely by replacing user characters.
- Emit user text only as separately escaped labels using each target format's documented alias syntax.
- Implement distinct Mermaid, PlantUML, and Markdown escaping functions. Escape or reject newlines and grammar terminators in titles, triggers, conditions, and labels.
- Test Unicode, quotes, backslashes, colons, brackets, pipes, backticks, comment/directive markers, embedded newlines, and pairs that collide under the old sanitizer.
- Parse/render generated diagrams in verification when practical; substring-only tests cannot prove grammar safety.

**Warning signs:**

- One generic `sanitize()` helper serves identifiers, labels, titles, and two diagram languages.
- State IDs are produced by a regex replacement without collision detection.
- Tests compare only friendly ASCII snapshots.

**Recovery:**
Regenerate diagrams with opaque aliases. Treat previously generated text from untrusted names as unsafe to render until it has passed the new grammar-specific exporter.

**Phase to address:** Phase 4 — Bounded Diagnostics and Safe Output.

---

### Pitfall 10: Redacted logging still leaks data or takes over the application logger

**Class:** Security-critical

**What goes wrong:**
Trace mode logs raw positional and keyword values, exposing tokens, PII, or attacker-controlled control characters. A helper clears handlers installed by the host application, changing audit routing and test behavior. Repeated helper calls can duplicate output or leave no path to restore prior configuration.

**Why it happens:**
Debug convenience is implemented inside the library rather than at the application boundary. Python's official logging guidance assigns handler configuration to the application and strongly advises library loggers to install no handler other than `NullHandler`.

**How to avoid:**

- Never log raw trigger argument values by default, even at trace. Prefer trigger/state names, argument counts, and a deliberately limited structural summary.
- If key names are emitted, sanitize control characters and document that names themselves can be sensitive. An application-supplied redactor must be explicit and must default to removing values.
- Add only `NullHandler` automatically at the top-level library logger.
- If the public configuration helper remains, mark and manage only its own handler; never clear unrelated handlers. Make configure/unconfigure idempotent and reversible, and define propagation deliberately.
- Test with sentinel secrets in strings, nested containers, object `repr`, keys, positional data, and exception messages. Test that application handlers survive configure/unconfigure cycles.

**Warning signs:**

- A log call formats `args`, `kwargs`, or `repr(value)` before the level check or redactor.
- `logger.handlers.clear()` appears in library code.
- Tests assert handler count rather than preservation of pre-existing handler identity and routing.

**Recovery:**
Disable trace logging, rotate exposed credentials if logs may have left the process, restore application handlers, and ship the redaction/configuration fix as a security-relevant change.

**Phase to address:** Phase 4 — Bounded Diagnostics and Safe Output.

## Technical Debt Patterns

| Shortcut | Immediate benefit | Long-term cost | When acceptable |
|----------|-------------------|----------------|-----------------|
| Wrap the existing trigger body in one lock | Small patch | Serializes false-success semantics and can deadlock on reentry | Never |
| Use `RLock` to avoid deadlock | Nested calls keep running | Recreates state overwrite and makes callback order recursive | Never under safe defaults |
| Roll `_current_state` back after post-commit failure | Looks transactional | Lies about external effects and can create duplicate retries | Never |
| Patch sync and async methods separately | Local progress | Parity drifts again at the next change | Only as a short-lived spike, never merged without shared contract tests |
| Inspect only outer condition type | Cheap async detection | Wrapped `AsyncCondition` selects the wrong runtime | Never |
| Keep diagnostics coupled to `_states`/`_transitions` | No snapshot abstraction | Tools disagree and race with mutations | Only until Phase 1 snapshot exists |
| Catch all build exceptions and fall back | Installation succeeds broadly | Release silently violates compiled performance contract | Acceptable only in explicit source-only build mode |
| Run tests from checkout after wheel build | Reuses current harness | Source can shadow installed artifact | Never for release proof |
| Materialize dense matrices unconditionally | Simple API | O(states²) memory even for sparse graphs | Only below an enforced cell budget |
| Enumerate all simple paths | Complete small examples | Factorial output on dense graphs | Only with explicit depth/result/work budgets |
| Regex-replace diagram identifiers | Short implementation | Alias collisions and grammar injection | Never for user-controlled names |
| Log raw payloads at trace | Rich debugging | Secret/PII leakage and log forging | Never as library default |

## Sync/Async and Compiled/Interpreted Integration Gotchas

| Boundary | Common mistake | Correct approach |
|----------|----------------|------------------|
| Sync vs async guards | Sanitize only sync kwargs or forward different positional data | Prepare one transition context and apply the same policy in `can_trigger*()` and `trigger*()` |
| Wrapped async conditions | Test only the outer `NegatedCondition` | Expose recursive async capability through condition wrappers |
| Async cancellation | Catch as ordinary callback failure or leave ownership set | Stage cancellation relative to commit, clean up in `finally`, then propagate |
| Sync callbacks in async machines | Automatically offload with `to_thread()` | Keep ordering/thread affinity explicit; require short sync callbacks and async callbacks for I/O |
| Async locking | Share `asyncio.Lock` across threads/loops | Bind one machine to one loop and reject unsupported access |
| Compiled native classes | Test through monkey-patching/introspection | Use real public behavior; mypyc native namespaces and tracing differ |
| Pure-Python verification | Set an environment variable while stale extension remains | Test in a clean path and assert `core.__file__` is Python source |
| Wheel verification | Import with repository `src/` on `sys.path` | Install and test from a temporary directory outside the checkout |
| Release fallback | Treat mypyc absence and compilation defects identically | Separate intentional source build from strict compiled release mode |

## Performance Traps

| Trap | Symptoms | Prevention | When it breaks |
|------|----------|------------|----------------|
| Lock/owner checks added repeatedly through helpers | Unguarded trigger benchmark drops below contract | One per-instance ownership boundary; benchmark uncontended sync and async hot paths after every lifecycle change | Release-breaking below 200,000 `trigger()` ops/sec |
| Global lock shared across machines | Independent FSMs block each other | Per-instance lock/owner state in `__slots__` | Immediately under multi-machine concurrency |
| Front-deleting history list | Throughput degrades with capacity | `deque(maxlen=...)` or ring buffer; validate positive capacity | Every full-buffer transition; cost grows with `max_entries` |
| Callback/log formatting on disabled paths | No-callback/no-log path slows unexpectedly | Guard before constructing messages/context; preserve zero/constant-cost disabled paths | Hot path even with no observers |
| Dense adjacency export | Memory spikes | Sparse internal representation plus explicit dense cell budget | O(states²); 10,000 states implies 100M cells |
| Branch-copy longest path | CPU grows explosively | SCC condensation plus DAG dynamic programming and work budget | Branching DAGs with many alternate paths |
| Unbounded path generation | Huge output or hang | Depth, result, work, and byte limits with truncation metadata | Can reach O(n!) paths in complete graphs |
| Recursive adversarial traversal | Recursion error or compiled crash | Iterative traversal or validated depth limit | Deep generated/config-driven graphs |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Raw `args`/`kwargs` trace logging | Credentials, PII, and object representations leave process boundaries | Structural metadata only; explicit redactor; secret sentinel tests |
| Logging unsanitized exception text | Callback payload can reappear through exception messages | Document exception-text risk, sanitize control characters, and avoid echoing context |
| Clearing application handlers | Audit logs disappear or reroute | `NullHandler` only by default; helper owns only marked handlers |
| Diagram alias collisions | Distinct states render as one node | Opaque collision-free aliases |
| Raw diagram titles/labels | Directive/comment injection or malformed output | Grammar-specific label escaping and newline handling |
| Raw Markdown diagnostics | Table/fence injection | Separate Markdown escaping and output-size limits |
| Unbounded diagnostics on config-derived graph | CPU/memory denial of service | Deterministic resource budgets and explicit incomplete results |

## User-Experience Pitfalls

| Pitfall | User impact | Better approach |
|---------|-------------|-----------------|
| Failure result does not say whether state changed | Caller cannot safely retry or compensate | Expose failure stage and commit status while preserving existing symbols |
| Reentry hangs | Application appears frozen | Immediate dedicated reentrancy error/failure |
| Concurrent calls race nondeterministically | Same input yields different state/callback order | Serialize independent callers and document ownership contract |
| Builder accepts ignored edits | Configuration looks valid but is stale | Raise on every post-build mutator |
| Diagnostic truncation is silent | Agents act on incomplete topology | Include `complete`, limits, counts, and truncation reason |
| Compiled fallback is silent | Installed performance differs from advertised | Explicit artifact mode and module-origin evidence |
| Diagram exporter corrupts names | Users cannot trust generated docs | Preserve labels exactly after safe escaping via opaque aliases |

## “Looks Done But Is Not” Verification Gates

| Area | Superficial completion | Required proof |
|------|------------------------|----------------|
| Callback failures | One callback exception test passes | Inject every pre/post callback stage; assert state, result, cause, callback stop, history, and one failure notification in sync and async modes |
| Reentrancy | A lock exists | Nested trigger/state/topology calls fail promptly without deadlock; outer transition outcome follows stage policy; next transition succeeds |
| Concurrency | One two-thread test passes | Deterministic barriers cover competing success/failure, topology mutation, force/reset, and same-loop tasks |
| Cancellation | `CancelledError` propagates | Inject at each await; assert commit/history coherence, owner cleanup, lock release, and subsequent success |
| Graph invariants | Unknown target is rejected | Unknown sources, object targets, duplicate names, fan-out atomicity, and all builder mutators are covered |
| Async parity | One async condition works | Shared contract covers positional/sanitized context, `unless=`, declarative dispatch, callbacks, results, and history |
| Diagnostics | Example graph looks right | Exact SCC membership, declared initial state, duplicate/empty comparisons, deterministic budgets, and truncation metadata pass |
| Visualization | Friendly names render | Collision pairs, Unicode, grammar metacharacters, newlines, directives, conditions, titles, and Markdown tables are escaped and parsed/rendered |
| Redaction | A password keyword is hidden | Secrets in positional values, nested objects, keys, exception messages, and control text never appear by default |
| Pure Python | Environment flag is set | Module origin is asserted as `.py` in an extension-free environment and source coverage measures `core.py` |
| Compiled wheel | Build and import succeed | Installed wheel outside checkout has platform tag/extension origin, passes full semantic suite, and meets throughput floor |
| Release identity | Source says v0.3.0 | Tag, `pyproject.toml`, wheel metadata, installed `__version__`, changelog, docs, and test baseline agree |

## Recovery Strategies

| Pitfall | Recovery cost | Recovery steps |
|---------|---------------|----------------|
| Ambiguous callback commit | HIGH | Freeze behavior, add stage metadata/tests, reconcile application state from domain evidence, then document compensation |
| Reentrancy deadlock | MEDIUM | Reproduce with watchdog, add pre-acquisition owner detection, guarantee cleanup, verify next-call recovery |
| Concurrent state corruption | HIGH | Stop sharing affected instance, reconstruct from trusted snapshot/history, serialize access, add deterministic interleaving tests |
| Partial graph mutation | MEDIUM | Reject contradictory topology, rebuild canonical graph from explicit config, make future bulk changes atomic |
| Async cancellation leak | HIGH | Clear owner only through invariant-safe cleanup, reconcile committed state/history, inject cancellation across all awaits |
| Silent pure-Python release | HIGH | Quarantine artifact, rebuild strict platform wheel from tag, inspect/install/test/benchmark, publish corrected version |
| False diagnostic report | MEDIUM | Mark report incomplete/untrusted, rerun canonical snapshot algorithms under explicit budgets |
| Secret-bearing logs | HIGH | Disable trace, restrict/rotate logs and credentials, ship redaction fix, verify application handler routing |
| Malformed/injectable diagram | LOW to MEDIUM | Stop rendering old output, regenerate with opaque aliases and target-specific escaping |
| Performance regression | MEDIUM | Benchmark by feature path, profile owner/lock/history/log overhead, optimize without weakening correctness |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention phase | Verification |
|---------|------------------|--------------|
| Release/version/gate drift | Phase 0 — Release Baseline and Contract Harness | Clean checkout gates pass; one version/test baseline assertion covers metadata, changelog, docs, and tag context |
| Partial graph and stale builder | Phase 1 — Canonical Graph and Dispatch Invariants | Property tests prove endpoint identity, fan-out atomicity, duplicate rejection, and sealed builder behavior |
| Sync/async/guard/declarative drift | Phase 1 — Canonical Graph and Dispatch Invariants | One parameterized parity suite runs across all dispatch/construction variants |
| Ambiguous callback commit and rollback lie | Phase 2 — Atomic Transition Lifecycle | Stage-failure matrix proves state, commit flag, cause, history, ordering, and notification behavior |
| Reentrancy deadlock/corruption | Phase 3 — Ownership, Reentrancy, and Concurrency | Watchdog tests fail promptly on nested mutation and leave the machine reusable |
| Concurrent/cross-loop/cancellation corruption | Phase 3 — Ownership, Reentrancy, and Concurrency | Barrier/cancellation tests prove serialization, loop ownership, commit/history coherence, and cleanup |
| False or unbounded diagnostics | Phase 4 — Bounded Diagnostics and Safe Output | SCC, empty/duplicate, large sparse/dense, budget, and explicit truncation tests pass |
| Diagram/Markdown injection and alias collision | Phase 4 — Bounded Diagnostics and Safe Output | Hostile labels remain distinct and inert in parser/render verification |
| Payload leakage and logger takeover | Phase 4 — Bounded Diagnostics and Safe Output | Secret sentinels absent; application handler identities/routing survive reversible helper calls |
| Source/compiled semantic mismatch | Phase 5 — Compiled/Source Parity and Release Proof | Same conformance suite passes with asserted `.py` and extension origins |
| Silent compilation fallback | Phase 5 — Compiled/Source Parity and Release Proof | Strict builds fail on injected compiler errors; platform wheels install and test outside checkout |
| Hot-path performance loss | Phases 1–5 continuously; final gate in Phase 5 | Benchmark after every `core.py` phase; installed compiled `trigger()` remains ≥200,000 ops/sec |

## Phase Ordering Rationale

1. **Phase 0 establishes trustworthy evidence.** Fix current format/lint/version drift and create the reusable semantic/performance harness before behavior changes.
2. **Phase 1 establishes one canonical machine and dispatch meaning.** Callback atomicity cannot be specified reliably while endpoints and sync/async dispatch disagree.
3. **Phase 2 establishes the commit boundary.** Synchronization must protect defined semantics, not preserve ambiguous ones.
4. **Phase 3 adds ownership and serialization.** Reentry detection must precede blocking acquisition; cancellation tests depend on the Phase 2 stage model.
5. **Phase 4 hardens consumers of topology.** Diagnostics, logging, and renderers can then consume the canonical snapshot and lifecycle metadata.
6. **Phase 5 proves the shipped product.** Run the completed contract against clean source and installed compiled artifacts, then enforce the final throughput and release-identity gates.

## Sources

### Primary external sources

- [Python 3.10 `threading` synchronization documentation](https://docs.python.org/3.10/library/threading.html) — primitive lock, reentrant lock, ownership, context-manager, and fairness caveats. **Confidence: MEDIUM** (verified websearch tier).
- [Python 3.10 `asyncio` synchronization primitives](https://docs.python.org/3.10/library/asyncio-sync.html) — task serialization, fairness, and non-thread-safe scope. **Confidence: MEDIUM**.
- [Python 3.10 task cancellation documentation](https://docs.python.org/3.10/library/asyncio-task.html) — cancellation propagation and `finally` cleanup. **Confidence: MEDIUM**.
- [`transitions` callback execution order](https://github.com/pytransitions/transitions#callback-execution-order) — explicit state-change boundary, stop-on-failure behavior, post-change persistence, and no rollback. **Confidence: MEDIUM**.
- [Python 3.10 Logging HOWTO: configuring logging for a library](https://docs.python.org/3.10/howto/logging.html#configuring-logging-for-a-library) — `NullHandler` and application ownership of handlers. **Confidence: MEDIUM**.
- [mypyc: Differences from Python](https://mypyc.readthedocs.io/en/stable/differences_from_python.html) — compiled/interpreted semantic, introspection, monkey-patching, tracing, recursion, and concurrency caveats. **Confidence: MEDIUM**.
- [Python Packaging User Guide: packaging flow](https://packaging.python.org/en/latest/flow/) and [package formats](https://packaging.python.org/en/latest/discussions/package-formats/) — platform wheels and extension artifact expectations. **Confidence: MEDIUM**.
- [cibuildwheel testing options](https://cibuildwheel.pypa.io/en/stable/options/#test-command) — installed-wheel tests outside the source tree. **Confidence: MEDIUM**.
- [Mermaid state diagram syntax](https://mermaid.js.org/syntax/stateDiagram.html) and [PlantUML state diagrams](https://plantuml.com/en/state-diagram) — state aliases separating descriptions from identifiers. **Confidence: MEDIUM**.
- [NetworkX `all_simple_paths`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.all_simple_paths.html) — factorial path counts and cutoff control. **Confidence: MEDIUM**.
- [NetworkX strongly connected components reference](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.strongly_connected_components.html) — complete SCC membership for directed graphs. **Confidence: MEDIUM**.

### Project evidence

- `.planning/codebase/CONCERNS.md`, `src/fast_fsm/core.py`, `src/fast_fsm/validation.py`, `src/fast_fsm/visualization.py`, and `setup.py` — reproduced and directly inspected project-specific failures. **Confidence: HIGH**.
- `.planning/research/FEATURES.md` — selected safe-default contract and milestone acceptance boundaries. **Confidence: HIGH** for project decisions.
- `.planning/codebase/TESTING.md` — 722-test baseline, current quality failures, compiled-origin coverage artifact, and missing parity cases. The requested `QUALITY.md` does not exist; `TESTING.md` is the current codebase quality/testing map. **Confidence: HIGH**.

---
*Pitfalls research for: Fast FSM v0.3.0 Reliability & Runtime Hardening*
*Researched: 2026-08-29*
