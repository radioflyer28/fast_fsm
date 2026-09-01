# Phase 18: Safe Ownership & Concurrency - Research

**Researched:** 2026-09-01
**Domain:** CPython/mypyc per-instance thread ownership, asyncio loop/task ownership, causal reentry, and deterministic concurrency verification
**Confidence:** HIGH for repository architecture; MEDIUM for cross-version runtime behavior until the Python 3.10–3.14 native matrix runs

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Ownership Violation Contract
- **D-01:** Reentrant and cross-event-loop ownership violations raise `RuntimeError` immediately as operational precondition failures. They do not become a failed `TransitionResult`, add a lifecycle stage, or introduce a new public exception type. — **Reversibility:** costly — changing the exception surface after v0.3.0 would alter control flow for every guarded public write.
- **D-02:** Reentry by the current execution context is detected before lock acquisition and before transition preparation, guard evaluation, callbacks, or mutation. Reentry is rejected, never queued.
- **D-03:** When an uncaught reentrant call occurs inside a Phase 17 callback, the nested call raises and the existing outer lifecycle classifies that exception at the callback's normal stage. The nested operation never acquires ownership or mutates the machine; a callback may deliberately catch the `RuntimeError` and continue.
- **D-04:** Ownership error messages use stable operation/category metadata only. They must not include trigger positional arguments, keyword values, callback payloads, stored causes, or arbitrary exception text.

### Synchronous Serialization
- **D-05:** Every synchronous machine owns one private synchronization primitive and explicit owner marker stored on the instance; no module-global lock, caller-supplied lock, or shared lock registry is introduced. Ownership checks and uncontended acquisition remain O(1).
- **D-06:** Same-thread reentry fails before acquisition. Independent threads block and serialize one complete public write at a time. The public contract promises neither fairness, timeouts, nor queue ordering beyond mutual exclusion. — **Reversibility:** costly — switching later to fail-if-busy or a fair queue would change scheduling visible to callers.
- **D-07:** The ownership envelope covers the whole public operation: validation/preparation, guard evaluation, lifecycle callbacks, commit, declarative and trigger callbacks, failure observers, and final result construction. Callbacks therefore cannot open an unowned window into partially completed work.
- **D-08:** One `try/finally`-shaped release boundary clears the owner marker and releases the primitive after success, ordinary exceptions, every `BaseException`, and callback failure. The state and history left behind are exactly the coherent pre- or post-commit boundary already defined by Phase 17.

### Async Loop and Task Ownership
- **D-09:** An `AsyncStateMachine` binds permanently to the running event loop of its first async control operation. Later access from a different loop raises `RuntimeError` before lock acquisition; an idle or closed original loop does not authorize silent rebinding. — **Reversibility:** costly — cross-loop rebinding would require an ownership-transfer protocol and invalidate stored synchronization state.
- **D-10:** Independent tasks in the bound loop serialize through one asyncio-native per-machine lock. Waiting never blocks the event-loop thread. Cancellation while waiting propagates unchanged without installing ownership; cancellation while owning follows Phase 17 and releases ownership in `finally`.
- **D-11:** Ownership includes a causal context token in addition to the concrete current task. A child task created inside an owned callback inherits that context and is rejected as reentrant instead of waiting behind the parent and deadlocking it. Tasks created independently outside the owned context serialize normally.
- **D-12:** Synchronous machine mutators inherited by `AsyncStateMachine` may configure an unbound machine under synchronous per-instance protection. After loop binding, they are accepted only from the bound loop's thread while idle; during an async-owned operation they fail immediately, and calls from other threads/loops fail explicitly rather than blocking the event loop.
- **D-13:** Synchronous callbacks on `AsyncStateMachine` continue to run inline on the event-loop thread at their Phase 17 lifecycle slots. Async callbacks are awaited at their matching slots. The library does not infer blocking work or offload callbacks to worker threads. — **Reversibility:** costly — implicit offload would change ordering, context propagation, exception identity, and cancellation behavior.

### Coverage, Cleanup, and Performance
- **D-14:** The shared ownership policy applies to every public machine write: `trigger()`/`trigger_async()`, force/reset/restore, state and transition graph changes (including batch forms), history enable/disable, and callback/listener/failure-observer registration. A registration attempted from an owned callback is rejected; existing snapshot iteration still prevents current-pass observer duplication.
- **D-15:** Read-only properties and helpers do not gain a new cross-field snapshot guarantee in Phase 18. Simple current-state/history reads remain available; stable topology snapshots and diagnostic consistency remain Phase 19. Factories, builders before publication, and independent clones retain their existing Phase 16 semantics and do not share ownership primitives.
- **D-16:** Deterministic tests use barriers, events, and explicit task handshakes rather than sleeps. Evidence must cover sync threads, same-loop tasks, causal child-task reentry, cross-loop rejection, every write family, ordinary exceptions, `BaseException`, cancellation before/after commit, fresh pure/compiled origins, O(1) ownership operations, and the compiled `trigger()` floor of 200,000 operations/second.

### the agent's Discretion
- Private helper/type names, exact slot ordering, and whether owner metadata is represented as identifiers or private token objects, provided the observable rules above and mypyc constraints hold.
- Exact stable wording of redacted `RuntimeError` messages and the organization of table-driven ownership tests.
- Whether closely related public write methods share decorators, context managers, or explicit enter/exit helpers, provided acquisition order and release guarantees are mechanically auditable.

### Deferred Ideas (OUT OF SCOPE)
- Queued reentrant transitions with ordering and overflow policy — FUTR-01.
- Cross-event-loop ownership transfer or rebinding — FUTR-03.
- Automatic worker-thread execution for synchronous async-machine callbacks — FUTR-04.
- Stable multi-consumer diagnostic graph snapshots and read consistency — Phase 19.
- Installed wheel/sdist parity and final release proof — Phase 20.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OWN-01 | A transition or mutator invoked reentrantly by its current owner fails immediately before lock acquisition and cannot overwrite the outer operation. | Pre-acquisition thread/root-token checks, private owned bodies, and callback-stage matrices. |
| OWN-02 | Independent threads operating on one synchronous machine are serialized without a global lock. | One per-instance primitive, explicit owner marker, full-operation envelope, and Event/Barrier tests. |
| OWN-03 | Independent tasks operating on one asynchronous machine in the same event loop are serialized without blocking the loop. | One per-instance `asyncio.Lock`, awaited acquisition, heartbeat/handshake tests, and no thread lock held across awaits. |
| OWN-04 | Unsupported cross-event-loop use fails explicitly instead of binding or corrupting ownership silently. | Explicit first-operation loop binding and identity check before async lock acquisition. |
| OWN-05 | State and topology mutators, including trigger, force/reset/restore, and graph changes, participate in the same per-machine ownership policy. | Complete public write-family inventory and one-entry/private-body architecture. |
| OWN-06 | Ownership is released after exceptions, `BaseException`, or cancellation, leaving state and history at a documented coherent boundary. | `with`/`async with` plus `finally`, Phase 17 seam preservation, cancellation-at-wait/owner matrices. |
| OWN-07 | The async callback contract explicitly states that synchronous callbacks run inline, while async callbacks and machine control remain event-loop safe; automatic thread offload is not implied. | Loop-thread identity tests and documentation contract; no executor/to-thread use. |
</phase_requirements>

## Summary

Phase 18 should add an ownership shell around the Phase 17 transition/control bodies, not alter the lifecycle itself. A synchronous `StateMachine` needs a normal per-instance `threading.Lock` plus a same-thread owner marker. An `AsyncStateMachine` additionally needs a permanent bound-loop identity, a per-instance `asyncio.Lock`, an active task marker, and an active causal-root marker. The sync shell must use a lock context plus inner `finally`; the async shell must use `async with` so cancellation while awaiting acquisition never installs ownership and cancellation after acquisition always releases it. These are direct applications of the standard-library synchronization contracts. [CITED: https://docs.python.org/3.14/library/threading.html] [CITED: https://docs.python.org/3.14/library/asyncio-sync.html] [CITED: https://docs.python.org/3.14/library/asyncio-task.html]

The causal marker should be one module-level `ContextVar` containing an execution-root token. A top-level acquisition creates the root; nested operations on another machine reuse it; each actively owned machine stores the root it admitted. That yields O(1) identity checks, preserves cross-machine nesting, and causes a callback-created child task to inherit the root and fail immediately on the same machine. `ContextVar.set()`/`reset(token)` must be explicit because token context-manager syntax exists only in Python 3.14 while the package supports Python 3.10+. [CITED: https://docs.python.org/3.14/library/contextvars.html] [CITED: https://docs.python.org/3.10/library/contextvars.html] [CITED: https://docs.python.org/3.14/library/asyncio-task.html]

Two existing seams require deliberate plan tasks. First, the module-global `_prepared_declarative_guards` dictionary is not execution-context-local: synchronous callers all use the key `None`, so independent machines/threads can overwrite the marker. Quote: `_prepared_declarative_guards: Dict[Optional[int], Tuple[int, str, int]] = {}` and `return None` outside a task. [VERIFIED: src/fast_fsm/core.py:46-125] Replace this with a context-local marker that includes machine identity. Second, `safe_trigger()` currently says it “wraps the entire call in a broad `except Exception` barrier” and calls `self.trigger(...)`; this conflicts with D-01/D-14 because it would convert an ownership `RuntimeError` into a result. [VERIFIED: src/fast_fsm/core.py:2617-2659] The ownership precondition must remain outside that catch barrier, and the compatibility documentation/tests must be updated explicitly.

**Primary recommendation:** Build one auditable per-machine ownership layer with private non-owning operation bodies, explicit async loop admission, and a module-level causal-root `ContextVar`; then prove every write family and cleanup boundary in fresh pure and compiled origins before accepting the throughput evidence.

## Severe Interface Conflict

**SEVERE — public behavior conflict, not a dependency blocker:** `safe_trigger()` currently catches every escaping `Exception`, while D-01 and D-14 require an ownership `RuntimeError` from every public write to escape before transition handling. The exact current implementation is `try: return self.trigger(trigger, *args, **kwargs)` followed by `except Exception as e`; therefore simply wrapping `trigger()` would violate the locked contract. [VERIFIED: src/fast_fsm/core.py:2649-2659]

The planner must allocate an explicit compatibility task: ownership admission occurs outside the `safe_trigger()` catch, a private already-owned trigger body remains inside it, the docstring/README/SPR are revised, and regression tests prove ordinary safe-trigger exceptions still become results while ownership preconditions raise. This is an intentional pre-production behavior correction authorized by the locked Phase 18 context; it must not be hidden as an implementation detail.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Synchronous serialization and reentry rejection | Runtime library (`core.py`) | CPython threading primitive | The machine owns the mutable state and must protect its entire public write envelope. |
| Async loop/task ownership | Runtime library (`core.py`) | Event loop | The machine enforces permanent loop identity; `asyncio.Lock` only provides same-loop task exclusion. |
| Causal child-task reentry | Runtime execution context | `contextvars`/Task context | Task identity alone cannot detect a child task that inherited the parent's causal call chain. |
| State/history/topology atomicity | Runtime library (`core.py`) | Existing Phase 16/17 seams | Ownership must surround, not replace, canonical plan commit and lifecycle commit. |
| Pure/compiled semantic parity | Verification harness | mypyc build | `core.py` is the single native compilation unit and must be tested from asserted origins. |
| Public ownership contract | README/Sphinx/SPR/ADR | Tests/doctests | Users need stable exception, callback-thread, and unsupported-use semantics. |

## Project Constraints (from AGENTS.md)

- Use `uv` for every Python/package/test command. Exact directive: “**ALWAYS use `uv`** — never `python`, `pip`, or `python -m pytest` directly.” [VERIFIED: .github/copilot-instructions.md:36-38]
- Preserve slots on hot-path production classes. Exact exceptions: “`CompiledFuncCondition` and `TransitionError` are the only measured registered exceptions.” [VERIFIED: .github/copilot-instructions.md:40-47]
- Preserve the exact performance contracts: “Compiled `trigger()` throughput MUST stay ≥ 200,000 ops/sec” and “Core operations (`trigger()`, `can_trigger()`, `add_state()`, `add_transition()`) MUST be O(1).” [VERIFIED: .github/copilot-instructions.md:40-48]
- Preserve `*args, **kwargs`, existing constructors, and every public symbol; removals require deprecation. [VERIFIED: .github/copilot-instructions.md:50-53]
- Run targeted tests during development and the sequential full suite once before push. Exact full command: `uv run pytest tests/ -x -q`. [VERIFIED: .github/copilot-instructions.md:55-61]
- Keep `core.py` as the only mypyc compilation unit; `conditions.py` and `condition_templates.py` remain interpreted. [VERIFIED: .github/copilot-instructions.md:305-330]
- Keep the one runtime dependency. Exact project dependency list: `dependencies = ["mypy-extensions>=1.0"]`. [VERIFIED: pyproject.toml:1-9]
- Rebuild Sphinx with warnings as errors and doctests after public-doc changes. Exact commands: `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` and `uv run sphinx-build -b doctest docs docs/_build/doctest`. [VERIFIED: .github/copilot-instructions.md:254-302]
- Use beads for issue tracking, preserve unrelated dirty work, and stage only explicit paths; never use `git add .` or `git add -A`. [VERIFIED: AGENTS.md:1-129] [VERIFIED: .github/copilot-instructions.md:80-119]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `threading.Lock` + `threading.get_ident` | stdlib, Python 3.10–3.14 | Per-instance sync exclusion and same-thread owner identity | Primitive lock acquisition/release is atomic; blocked waiter ordering is deliberately unspecified; `get_ident()` is a recyclable cookie, safe here because the marker is cleared before the live owner releases. [CITED: https://docs.python.org/3.14/library/threading.html] |
| Python `asyncio.Lock` + `get_running_loop()` + `current_task()` | stdlib, Python 3.10–3.14 | Same-loop task serialization, permanent loop identity, task metadata | The lock is awaitable and not thread-safe; `get_running_loop()` identifies the active loop in the current OS thread. [CITED: https://docs.python.org/3.14/library/asyncio-sync.html] [CITED: https://docs.python.org/3.14/library/asyncio-eventloop.html] |
| Python `contextvars.ContextVar` | stdlib, Python 3.10–3.14 | O(1) causal-root identity inherited by child tasks | Tasks copy the current context; explicit token reset works across all supported versions. [CITED: https://docs.python.org/3.14/library/contextvars.html] [CITED: https://docs.python.org/3.14/library/asyncio-task.html] |
| mypy/mypyc | `1.17.1` | Compile and validate the single `core.py` unit | Exact release pin is `"mypy[mypyc]==1.17.1"`. [VERIFIED: pyproject.toml:21-24,42-44] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | `8.4.1` installed | Deterministic behavior matrices | All ownership families, failures, redaction, and performance selections. [VERIFIED: local `uv run` environment; pyproject.toml:11-20] |
| pytest-asyncio | `1.3.0` installed | Same-loop coroutine tests | Async lock, loop binding, cancellation, and task-context tests; project mode is exactly `asyncio_mode = "auto"`. [VERIFIED: local `uv run` environment; pyproject.toml:55-74] |
| `threading.Event` / `threading.Barrier` | stdlib | Deterministic thread handshakes | Coordinate entry, owner hold, contender arrival, release, and completion without sleeps. [CITED: https://docs.python.org/3.14/library/threading.html] |
| `asyncio.Event` | stdlib | Deterministic task/cancellation handshakes | Prove waiter cancellation and owner cancellation at exact Phase 17 boundaries. [CITED: https://docs.python.org/3.14/library/asyncio-sync.html] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `threading.Lock` + explicit owner | `threading.RLock` | Rejected: recursive acquisition would permit the overwrite/deadlock class D-01 explicitly rejects. |
| Per-instance locks | Global/shared registry lock | Rejected by D-05 and would couple independent machines. |
| Awaited `asyncio.Lock` | Blocking thread lock across async lifecycle | Rejected: it can block the event-loop thread while callbacks/guards await. |
| Causal-root `ContextVar` | Task identity only | Rejected: callback-created child tasks have different task identities and can deadlock waiting behind their parent. |
| Inline sync callbacks | `asyncio.to_thread()`/executor offload | Deferred by D-13/FUTR-04; offload changes ordering, context, exception, and cancellation semantics. |

**Installation:** No package installation. This phase uses the standard library and already-pinned dev/build dependencies.

## Package Legitimacy Audit

No external package is added. The package-legitimacy gate is not applicable.

## Architecture Patterns

### System Architecture Diagram

```text
Sync public write
  -> same-thread owner check
       -> match: redacted RuntimeError (before preparation/mutation)
       -> no match: per-machine threading.Lock acquisition
            -> install thread owner
            -> private operation body
            -> Phase 16 prepare/graph plan OR Phase 17 lifecycle/control body
            -> result / exception
            -> finally clear owner
            -> release lock

Async public control
  -> get running loop
  -> permanent bind/check
       -> different loop: redacted RuntimeError (before asyncio lock)
  -> compare current causal root with active machine root
       -> match: redacted RuntimeError (before asyncio lock)
       -> no match: await per-machine asyncio.Lock
            -> create/reuse causal root; install task/root owner
            -> private async operation body
            -> Phase 17 lifecycle + awaits at existing slots
            -> result / CancelledError / BaseException
            -> finally clear task/root and reset ContextVar
            -> release asyncio lock

Inherited sync write on AsyncStateMachine
  -> sync per-instance admission
  -> if unbound: permit under sync ownership
  -> if bound: require bound thread + no different running loop + async idle
  -> otherwise: redacted RuntimeError; never block the event loop
```

### Recommended Project Structure

```text
src/fast_fsm/core.py                 # ownership slots/helpers + existing lifecycle bodies
tests/test_ownership_concurrency.py  # authoritative OWN-01..OWN-07 matrix
tests/test_transition_lifecycle.py   # Phase 17 preservation and observer-registration update
tests/test_async.py                  # async API compatibility and inline callback contract
tests/test_mypyc_guard.py            # slot/layout/single-unit structural guards
tests/test_performance_benchmarks.py # pure/compiled ownership overhead and fixed floor
tools/phase16_isolated_verify.py     # new phase18 inventory/suite
README.md
docs/QUICK_START.md
docs/dev/architecture.md
docs/dev/testing.md
.specify/memory/spr-core-api.md
.specify/decisions/ADR-005-safe-ownership-concurrency.md
```

### Pattern 1: One Ownership Entry, Private Operation Body

**What:** Every public write performs exactly one ownership admission. Public methods that currently delegate to other public writes must delegate to private bodies after admission.

**When to use:** `safe_trigger()`/`trigger()`, `reset()`/`force_state()`, and `restore()`/`force_state()` are the mandatory cases. Current exact delegations are `return self.trigger(trigger, *args, **kwargs)`, `self.force_state(self._initial_state.name)`, and `self.force_state(state_name)`. [VERIFIED: src/fast_fsm/core.py:1925-1935,1954-1980,2617-2659]

**Why:** Wrapping both public caller and public callee would look like forbidden same-owner reentry. It also makes operation labels ambiguous and can accidentally move validation outside the ownership envelope.

### Pattern 2: Lock Context Outside, Owner Cleanup Inside

**What:** For sync writes, pre-check the explicit owner, enter the primitive lock context, install the owner, then clear the marker in an inner `finally`. For async writes, pre-check loop/root, use `async with` for acquisition, then install and clear task/root under `finally`.

**When to use:** Every operation that can mutate machine state, history, topology, or callback registries.

**Official equivalence:** Python documents lock context management as acquisition followed by a `try/finally` release. [CITED: https://docs.python.org/3.14/library/threading.html] [CITED: https://docs.python.org/3.14/library/asyncio-sync.html]

### Pattern 3: Module-Level Causal Root, Per-Machine Active Root

**What:** Keep one module-level `ContextVar` with default `None`. The outermost ownership admission sets a fresh private object and resets the returned token in `finally`; nested different-machine calls reuse the root. Each active machine stores the admitted root and compares by identity before lock acquisition.

**When to use:** Async operations and any async-machine sync admission that needs causal rejection. This catches direct reentry, awaited nested calls, and callback-created child tasks without scanning a stack.

**Why:** Python says `ContextVar`s should be created at module level, and Tasks copy the current context when created. [CITED: https://docs.python.org/3.14/library/contextvars.html] [CITED: https://docs.python.org/3.14/library/asyncio-task.html]

### Pattern 4: Explicit Loop Admission Independent of `asyncio.Lock` Internals

**What:** Store the exact loop object and loop-thread identity on first async control call; compare with `is` before touching the async lock on later calls. Do not rely on lazy internal binding of `asyncio.Lock`.

**When to use:** Both `can_trigger_async()` and `trigger_async()` because D-09 says “first async control operation.” `can_trigger_async()` binds/checks but, under D-15, does not acquire write ownership or promise a stable cross-field snapshot.

**Why:** `get_running_loop()` returns the running loop in the current OS thread and raises when none exists. CPython's internal loop-bound mixin binds lazily, so the machine needs its own eager, permanent contract. [CITED: https://docs.python.org/3.14/library/asyncio-eventloop.html] [CITED: https://github.com/python/cpython/blob/3.14/Lib/asyncio/mixins.py]

### Pattern 5: Replace the Shared Declarative Guard Dictionary

**What:** Replace `_prepared_declarative_guards` with a context-local marker and include machine identity in the marker value. Preserve set/restore nesting semantics.

**When to use:** The declarative condition suppression seam used by sync and async policy evaluation.

**Why:** The current quote `_prepared_declarative_guards: Dict[Optional[int], Tuple[int, str, int]] = {}` uses the shared key `None` for all non-task execution. [VERIFIED: src/fast_fsm/core.py:46-125] A per-machine transition lock cannot protect that dictionary from other machines.

### Complete Public Write-Family Inventory

The planner should make one table-driven coverage row for each exact family below:

| Family | Exact public methods | Integration rule |
|--------|----------------------|------------------|
| Ordinary transition | `trigger`, `safe_trigger`, `trigger_async` | One owner entry; Phase 17 result/finalizer remains inside; ownership errors escape. |
| Direct control | `force_state`, `reset`, `restore` | One owner entry; private force body retains best-effort callback contract. |
| State graph | `add_state` | Validation and graph-version mutation inside the envelope. |
| Transition graph | `add_transition`, `add_transitions`, `add_bidirectional_transition`, `add_emergency_transition` | Entire preflight and all-or-nothing plan commit inside one envelope. |
| History | `enable_history`, `disable_history` | Validation and buffer replacement/discard inside one envelope. |
| Listener/callback registration | `add_listener`, `on_enter`, `on_exit`, `after_transition`, `on_failed`, `on_trigger` | Reentrant callback registration raises; snapshot iteration remains defensive. |
| Async callback registration | `on_enter_async`, `on_exit_async` | Same inherited sync-admission rules as all other sync methods on async machines. |

The method names above are quoted from their definitions in `core.py`. [VERIFIED: src/fast_fsm/core.py:896-965,1115-1260,1307-1430,1901-1980,2458-2659,2746-2800,3083-3238]

### Anti-Patterns to Avoid

- **RLock as the only policy:** It silently permits same-owner reentry and preserves the corruption class.
- **Acquire before reentry check:** A same-thread `Lock` call deadlocks instead of raising D-01's precondition error.
- **Thread lock held across `await`:** An unrelated OS thread can block the event loop indefinitely.
- **Owner installed before awaited acquisition:** Cancellation while waiting can leave a phantom owner.
- **Relying on task identity only:** A child task has a new task object but inherits its parent's causal context.
- **Double-wrapping public delegations:** `reset -> force_state`, `restore -> force_state`, and `safe_trigger -> trigger` self-reenter.
- **Catching ownership errors in lifecycle/safe wrappers:** Ownership is not a lifecycle failure stage or `TransitionResult`.
- **Reading arbitrary values into error strings:** D-04 excludes machine payloads, trigger arguments, callbacks, causes, and exception text.
- **Assuming the GIL is the lock:** Python 3.13 supports optional free-threaded builds, and mypyc requires explicit synchronization where races are possible. [CITED: https://docs.python.org/3.14/library/threading.html] [CITED: https://mypyc.readthedocs.io/en/stable/differences_from_python.html]
- **Changing observer-snapshot tests without replacing their proof:** Existing tests deliberately register an observer inside a failure callback; Phase 18 must change the expected behavior to ownership rejection while retaining a separate external-between-failures snapshot test. [VERIFIED: tests/test_transition_lifecycle.py:356-376,980-1019]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread mutual exclusion | Spin flag, busy wait, global registry | Per-instance `threading.Lock` | Atomic, portable across supported CPython versions, correct under free-threaded execution. |
| Async task serialization | Poll loop, thread lock, custom waiter queue | Per-instance `asyncio.Lock` | Awaited acquisition does not block the loop and cancellation integrates with Tasks. |
| Causal task propagation | Parent-task registry or task-name convention | `ContextVar` root token | Task creation copies context by contract. |
| Cleanup | Ad-hoc releases on return branches | `with`/`async with` and one `finally` | Covers success, ordinary exception, `BaseException`, and cancellation. |
| Cross-loop transfer | Rebinding or lock recreation | Permanent loop identity + rejection | Transfer is FUTR-03 and requires a separate protocol. |
| Callback offload | Automatic executor/to-thread dispatch | Keep inline/awaited Phase 17 slots | Offload is FUTR-04 and changes observable semantics. |
| Fairness/timeouts | Ticket locks, timeout queues | No promise beyond D-06/D-10 | Not required; adds hot-path state and API commitments. |

**Key insight:** The standard primitives solve exclusion and context propagation. Fast FSM's work is the admission policy, full-operation boundary, and preservation of the existing lifecycle—not a new scheduler.

## Common Pitfalls

### Pitfall 1: `safe_trigger()` Swallows the Ownership Contract

**What goes wrong:** A reentrant `safe_trigger()` returns a failed result instead of raising `RuntimeError`.

**Why it happens:** Its current broad `except Exception` surrounds `self.trigger(...)`. Exact quote: `return self.trigger(trigger, *args, **kwargs)` followed by `except Exception as e`. [VERIFIED: src/fast_fsm/core.py:2649-2659]

**How to avoid:** Perform ownership admission before the safety catch, then invoke a private trigger body inside the catch. Document that ownership preconditions are outside the “safe” transition-failure barrier.

**Warning signs:** Ownership tests observe `TransitionResult(success=False)` or payload-bearing error text instead of a redacted `RuntimeError`.

### Pitfall 2: Public-to-Public Delegation Becomes False Reentry

**What goes wrong:** `reset()` and `restore()` acquire ownership and then call an acquiring `force_state()`.

**Why it happens:** Both methods currently delegate publicly. [VERIFIED: src/fast_fsm/core.py:1925-1935,1954-1980]

**How to avoid:** Validate each public call under its own label and route all three to one private, already-owned control body.

**Warning signs:** Ordinary `reset()` raises an ownership error with no callback activity.

### Pitfall 3: Binding an Async Lock Is Not the Machine Contract

**What goes wrong:** An uncontended first operation can leave `asyncio.Lock` internally unbound, permitting later use from another loop before contention reveals it.

**Why it happens:** CPython's lock binding is lazy and implementation-specific. [CITED: https://github.com/python/cpython/blob/3.14/Lib/asyncio/mixins.py]

**How to avoid:** Persist the loop object explicitly on the machine at the first async control boundary.

**Warning signs:** Cross-loop tests pass while uncontended but fail or corrupt only when two tasks contend.

### Pitfall 4: Causal Child Task Waits Forever

**What goes wrong:** An owned callback creates and awaits a child task that calls the same machine; task identity differs, so the child waits on the parent's lock while the parent waits on the child.

**Why it happens:** Tasks copy context but not identity. [CITED: https://docs.python.org/3.14/library/asyncio-task.html]

**How to avoid:** Compare an inherited causal root to the machine's active root before lock acquisition.

**Warning signs:** A deterministic test needs a timeout to terminate rather than receiving immediate `RuntimeError`.

### Pitfall 5: Cancellation Window Leaks the Lock

**What goes wrong:** Cancellation lands after `await lock.acquire()` but before the caller establishes its release `finally`.

**Why it happens:** Manual acquire/release splits the protected setup sequence.

**How to avoid:** Use `async with lock` as the outer acquisition boundary, install owner metadata inside it, clear/reset metadata in an inner `finally`, and bare re-raise Phase 17 cancellation. Python recommends `try/finally` cleanup and propagation. [CITED: https://docs.python.org/3.14/library/asyncio-task.html]

**Warning signs:** A second independent task hangs after cancelling the first.

### Pitfall 6: Async Sync-Mutator Admission Races Initial Binding

**What goes wrong:** A foreign thread begins configuration while the first async operation binds, or the loop thread blocks on a long sync-owner lock.

**Why it happens:** Base-class sync writes and subclass async writes use different primitives without a short admission handshake.

**How to avoid:** Reuse the base per-instance sync primitive as the atomic admission gate only when binding/checking async metadata; never hold it across an await. If a sync write is active during first async admission, fail that async admission explicitly rather than blocking the loop. After binding, pre-reject foreign threads and any sync write while async ownership is active.

**Warning signs:** Event-loop heartbeat stops while another thread is in a callback, or the bound loop changes after a race.

### Pitfall 7: Observer Snapshot Regression Is Misread as a Failure

**What goes wrong:** Phase 17 tests expecting callback-time registration to affect the next failure now conflict with D-14.

**Why it happens:** The old test proves snapshot iteration by mutating the registry inside ownership. [VERIFIED: tests/test_transition_lifecycle.py:356-376,980-1019]

**How to avoid:** Assert the nested registration raises/gets isolated at the callback's current stage, then separately register between completed operations and prove the next snapshot sees it.

**Warning signs:** Implementers loosen registration ownership solely to keep the old expected event list.

### Pitfall 8: Cross-Version Runtime-Type Assumptions

**What goes wrong:** Code treats `threading.Lock` as a class on Python 3.10–3.12.

**Why it happens:** `Lock` changed from a factory function to a class in Python 3.13. [CITED: https://docs.python.org/3.14/library/threading.html]

**How to avoid:** Construct it normally but avoid runtime `isinstance(x, threading.Lock)` assumptions; let mypy infer or use a compilation-safe private annotation validated in the matrix.

**Warning signs:** Python 3.10 import/type-check failures despite 3.12/3.14 passing.

## Code Examples

Verified patterns from official sources; these are structural patterns, not final private names.

### Exception-Safe Synchronous Lock Scope

```python
# Source: https://docs.python.org/3.14/library/threading.html
with some_lock:
    # access shared state
    ...
```

The documentation defines this as acquire followed by `try/finally` release. Put the machine's explicit owner installation and cleanup inside this scope.

### Cancellation-Safe Async Lock Scope

```python
# Source: https://docs.python.org/3.14/library/asyncio-sync.html
async with lock:
    # access shared state
    ...
```

This is documented as awaited acquisition with `finally: lock.release()`. Install active task/root only after entering the scope.

### Cross-Version ContextVar Reset

```python
# Source: https://docs.python.org/3.10/library/contextvars.html
token = var.set("new value")
try:
    use_current_context()
finally:
    var.reset(token)
```

Use explicit reset rather than Python 3.14's token context-manager shorthand so Python 3.10–3.13 remain supported.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pass `loop=` into asyncio synchronization primitives | Create primitives without a loop parameter and bind/check explicitly at library boundary | Python 3.10 removed `loop=` | Fast FSM must persist its own permanent loop identity. [CITED: https://docs.python.org/3.14/library/asyncio-sync.html] |
| Treat `threading.Lock` as a factory-only API | `Lock` is a class on newer CPython | Python 3.13 | Avoid runtime class assumptions if supporting 3.10–3.12. [CITED: https://docs.python.org/3.14/library/threading.html] |
| Always call `ContextVar.reset(token)` | Token can also be a context manager | Python 3.14 | Do not adopt shorthand while minimum Python is 3.10. [CITED: https://docs.python.org/3.14/library/contextvars.html] |
| Assume the GIL protects compound runtime mutations | Free-threaded CPython exists and mypyc documents explicit synchronization | Python 3.13+ / current mypyc | Ownership must be real synchronization, not atomicity folklore. [CITED: https://docs.python.org/3.14/library/threading.html] [CITED: https://mypyc.readthedocs.io/en/stable/differences_from_python.html] |

**Deprecated/outdated:**

- Explicit asyncio `loop=` constructor arguments are unavailable on the supported range. [CITED: https://docs.python.org/3.14/library/asyncio-sync.html]
- Relying on the GIL as a mutual-exclusion contract is invalid for optional free-threaded builds and not portable to compiled atomicity. [CITED: https://docs.python.org/3.14/library/threading.html] [CITED: https://mypyc.readthedocs.io/en/stable/differences_from_python.html]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | [ASSUMED] The lock/ContextVar slot pattern that compiled and executed locally with mypyc 1.17.1 on CPython 3.12/macOS will compile identically on Python 3.10, 3.11, 3.13, and 3.14 and other supported native targets. | Standard Stack / Environment | Native CI could fail or expose version-specific typing/runtime behavior; Wave 0 must compile and run the full version matrix before design freeze. |

## Resolved Questions

1. **How should `safe_trigger()` describe ownership preconditions?**
   - What we know: D-01/D-14 require ownership `RuntimeError` to escape, but current docs say the whole `trigger()` call is inside `except Exception`. [VERIFIED: src/fast_fsm/core.py:2617-2659]
   - **RESOLVED:** State that `safe_trigger()` converts transition/internal `Exception`s only after successful ownership admission. Ownership, loop, causal-root, foreign-thread, and busy preconditions are outside its catch and raise `RuntimeError` before the safety barrier. This is the exact public wording and implementation boundary used by Plan 18-05.

2. **What happens if the first async operation races an unbound sync write?**
   - What we know: The event loop must never block, and unbound sync configuration is permitted.
   - **RESOLVED:** Use one short, non-awaiting per-instance admission gate to arbitrate initial loop binding and synchronous configuration per D-12. A sync writer installs its active-owner reservation under the gate, releases the gate, and then runs its lifecycle; a first async control operation acquires the gate only non-blockingly, rejects with a stable busy-category `RuntimeError` if sync ownership is active, otherwise records the permanent loop binding and async reservation before releasing the gate. The gate is never held across an await, callback, lifecycle, or mutation body. Once bound, foreign threads/loops reject before acquisition, while a synchronous write from the bound loop thread is admitted only when async ownership is idle. This defines exclusion without adding waiting, fairness, or offload semantics.

3. **How is supported-version native representation compatibility gated?**
   - What we know: A temporary probe using `threading.Lock`, `asyncio.Lock`, `ContextVar`, task/loop slots, `with`, `async with`, and `finally` compiled and ran with repository-pinned mypyc 1.17.1 on local CPython 3.12/macOS. [VERIFIED: local mypyc compile/import probe]
   - **RESOLVED:** Wave 0 adds a repository-native representation probe and requires its strict local/current-runtime compiled import to pass before production representation expansion. The same Wave defines the Python 3.10–3.14 native matrix contract. Phase closure then requires that matrix to compile actual `core.py`, assert native origin, execute ownership semantics, and succeed for the exact implementation SHA. This separates the local design gate from hosted coverage without treating an unavailable or unfinished run as success.

**Resolution status:** Questions 1 and 2 are fully resolved by the locked Phase 18 plan contract. Question 3 is an evidence gate rather than an interface ambiguity: Wave 0 must pass a local/current-runtime native representation probe and define the Python 3.10–3.14 hosted matrix before later plans depend on the representation; Phase 18 closure requires an exact-SHA hosted matrix success.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | All project commands | ✓ | `0.12.6` | None; required by project rules. |
| CPython | Local semantic tests | ✓ | `3.12.10` | CI matrix for other supported versions. |
| mypy/mypyc | Native compile proof | ✓ | `1.17.1` | None for compiled evidence. |
| pytest | Unit/integration evidence | ✓ | `8.4.1` | None. |
| pytest-asyncio | Async ownership tests | ✓ | `1.3.0` | None. |
| C compiler | Local mypyc build | ✓ | Apple clang `21.0.0` | CI native toolchains on Linux/Windows. |
| Task | Repository quality gates | ✓ | `3.53.1` | Invoke underlying documented `uv` commands if needed. |

**Missing dependencies with no fallback:** None in the local Phase 18 path.

**Missing dependencies with fallback:** Local Python 3.10, 3.11, 3.13, 3.14 and non-macOS native environments were not probed; use the existing CI/native matrix rather than weakening the supported range.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1` + pytest-asyncio `1.3.0` |
| Config file | `pyproject.toml` with exact `asyncio_mode = "auto"` [VERIFIED: pyproject.toml:55-74] |
| Quick run command | `uv run pytest tests/test_ownership_concurrency.py -x -q` |
| Lifecycle regression | `uv run pytest tests/test_ownership_concurrency.py tests/test_transition_lifecycle.py tests/test_async.py tests/test_graph_invariants.py tests/test_listeners.py tests/test_builder.py tests/test_boundary_negative.py tests/test_mypyc_guard.py -x -q` |
| Full suite command | `uv run python tools/phase16_isolated_verify.py --suite phase18` after adding the suite |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OWN-01 | Direct/callback reentry rejects before preparation for every write family; caught nested error lets outer callback continue | Unit matrix, sync + async | `uv run pytest tests/test_ownership_concurrency.py -x -q -k reentrant` | No — Wave 0 |
| OWN-02 | Two independent threads serialize one full sync operation; independent machines do not share a lock | Deterministic integration | `uv run pytest tests/test_ownership_concurrency.py -x -q -k thread` | No — Wave 0 |
| OWN-03 | Same-loop independent tasks wait without blocking the loop; max active owners is one | Async integration | `uv run pytest tests/test_ownership_concurrency.py -x -q -k same_loop` | No — Wave 0 |
| OWN-04 | First async operation binds; second loop rejects before lock/preparation; closed loop never rebinds | Cross-thread/loop integration | `uv run pytest tests/test_ownership_concurrency.py -x -q -k cross_loop` | No — Wave 0 |
| OWN-05 | Every exact write family uses the same admission policy, including batch graph and all registrars | Parameterized unit/structural | `uv run pytest tests/test_ownership_concurrency.py tests/test_mypyc_guard.py -x -q -k write_family` | No — Wave 0 |
| OWN-06 | Ordinary exception, `KeyboardInterrupt`/`SystemExit`, waiter cancellation, and owner cancellation release ownership at pre/post-commit boundaries | Failure/cancellation integration | `uv run pytest tests/test_ownership_concurrency.py tests/test_transition_lifecycle.py -x -q -k 'release or cancellation or base_exception'` | Partial lifecycle fixtures exist; ownership cases Wave 0 |
| OWN-07 | Sync callbacks run on loop thread inline; async callbacks are awaited in Phase 17 slots; no implicit offload | Async behavior + docs | `uv run pytest tests/test_ownership_concurrency.py tests/test_async.py tests/test_readme_examples.py -x -q -k callback` | Partial callback tests exist; thread identity/docs Wave 0 |

### Deterministic Test Design

- Thread tests use `Barrier` to start contenders and `Event` objects for “owner entered,” “contender attempted,” and “owner may exit.” The test asserts an event/order/counter, never elapsed time.
- Async tests use `asyncio.Event` handshakes and explicit created tasks. A separate heartbeat task/event proves the loop keeps advancing while a contender awaits the machine lock.
- Watchdog timeouts may fail a hung test, but they are not evidence of ordering or correctness.
- Causal reentry creates a child task inside an owned async callback and awaits it; the child must immediately raise, allowing the parent callback to observe it and finish without timeout.
- Cross-loop tests run two explicit loops in coordinated threads, bind in loop A, then attempt in loop B; assert no preparation callback ran and the loop reference stayed identical.
- Release tests reuse the same machine immediately after every injected exit path; successful reuse is the primary no-leak assertion.
- Redaction tests pass unique secret sentinels in args, kwargs, callback exceptions, machine names, and causes, then assert absence from exception text, repr, and logs.

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_ownership_concurrency.py -x -q` plus directly affected Phase 16/17 file.
- **Per wave merge:** lifecycle regression command above, mypy, and slots audit.
- **Phase gate:** Fresh pure and freshly compiled Phase 18 suite, compiled ownership/trigger benchmarks, full sequential release gate, Sphinx `-W`, and doctests.

### Wave 0 Gaps

| Gap | Required proof |
|-----|----------------|
| `tests/test_ownership_concurrency.py` | OWN-01 through OWN-07 deterministic behavioral matrix. |
| `tools/phase16_isolated_verify.py --suite phase18` | Explicit Phase 18 overlay/inventory; asserted `.py` and freshly built native origin. |
| `tests/test_mypyc_guard.py` ownership inventory guard | Every public write is wrapped once; required slots exist; no new runtime dependency/global lock. |
| `tests/test_performance_benchmarks.py` ownership cases | Pure/compiled uncontended ownership overhead plus fixed compiled `trigger()` floor. |
| Phase 18 performance evidence file | Before/after environment-labelled results; no unstated exact-rate promise. |
| Python 3.10–3.14 compile/semantic matrix | Confirm mypyc slot/type behavior across supported interpreters before freezing private representation. |

The existing Phase 17 harness quote `PHASE17_INVENTORY = (` includes runtime, lifecycle, async, builder, docs, SPR/ADR, and evidence, and its suite runs semantic tests in both `("pure", "compiled")` modes before the compiled performance selection and pure release gate. [VERIFIED: tools/phase16_isolated_verify.py:55-81,885-943] Phase 18 should extend this pattern rather than create a second artifact harness.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Library has no identity/authentication boundary. |
| V3 Session Management | no | Library owns in-process machine state, not user sessions. |
| V4 Access Control | no | Ownership is concurrency admission, not authorization; do not describe it as an access-control boundary. |
| V5 Input Validation | yes | Stable operation/category whitelist in ownership errors; reject unsupported loop/thread/task context before mutation. |
| V6 Cryptography | no | No cryptographic operation or secret storage is introduced. |
| V7 Error Handling and Logging | yes | D-04 redaction, no payload/cause formatting, and unchanged Phase 17 observer isolation. |

### Known Threat Patterns for Python/mypyc Ownership

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Reentrant overwrite of outer commit | Tampering | Same thread/causal root check before acquisition and preparation. |
| Child-task self-deadlock | Denial of Service | Inherited causal root rejected before `asyncio.Lock`. |
| Lock leak after `BaseException`/cancellation | Denial of Service | `with`/`async with`, inner metadata `finally`, and immediate reuse tests. |
| Cross-loop lock corruption or silent rebinding | Tampering / Denial of Service | Permanent loop object identity checked before acquisition. |
| Shared declarative marker collision | Tampering | Replace global dict with context-local, machine-qualified marker. |
| Ownership error leaks caller payload/cause | Information Disclosure | Constant operation/category messages; sentinel tests across repr/logs. |
| `safe_trigger` downgrades precondition failure | Repudiation / Tampering | Admit ownership outside its catch barrier; ownership errors never become results. |
| Callback monopolizes ownership indefinitely | Denial of Service | Document full-operation ownership and inline sync callback contract; do not promise timeout/fairness/offload. |
| Free-threaded/native data race | Tampering | Explicit primitives around all writes; do not depend on GIL or incidental atomicity. |

Security enforcement is enabled (the config does not set `security_enforcement: false`), so Phase 18's plan should include a threat model and a post-execution security audit.

## Sources

### Primary (HIGH confidence)

- `src/fast_fsm/core.py` — current slots, lifecycle, write families, public delegations, async boundaries, and shared declarative marker; opened directly this session.
- `tests/test_transition_lifecycle.py` — Phase 17 callback/observer snapshot and cancellation fixtures; opened directly this session.
- `tools/phase16_isolated_verify.py` — fresh pure/compiled inventory and suite contract; opened directly this session.
- `pyproject.toml` — Python floor, dependency set, pinned release mypyc, pytest settings; opened directly this session.
- `.planning/phases/17-atomic-transition-lifecycle/17-VERIFICATION.md` — independently passed predecessor seams and 12/12 evidence.
- Local mypyc 1.17.1 CPython 3.12/macOS compile/import probe — `threading.Lock`, `asyncio.Lock`, `ContextVar`, slots, `with`, `async with`, and `finally` compiled and executed.

### Secondary (MEDIUM confidence)

- https://docs.python.org/3.14/library/threading.html — primitive lock, context management, owner/fairness semantics, `get_ident`, free-threaded note.
- https://docs.python.org/3.14/library/asyncio-sync.html — async lock/event semantics and non-thread-safe boundary.
- https://docs.python.org/3.14/library/asyncio-eventloop.html — running-loop/thread identity and thread-safe scheduling boundary.
- https://docs.python.org/3.14/library/asyncio-task.html — current task, context copying, cancellation cleanup/propagation, inline/offload distinction.
- https://docs.python.org/3.14/library/contextvars.html and https://docs.python.org/3.10/library/contextvars.html — module-level creation, token reset, asyncio support, 3.14-only token context manager.
- https://github.com/python/cpython/blob/3.14/Lib/asyncio/mixins.py — current CPython lazy loop-binding implementation.
- https://mypyc.readthedocs.io/en/stable/native_classes.html — declared native attributes and compilation behavior.
- https://mypyc.readthedocs.io/en/stable/differences_from_python.html — type-error gate and explicit synchronization/free-threading guidance. Current docs are newer than the repository's 1.17.1 pin, so local compile and CI matrix remain authoritative for exact compatibility.

### Tertiary (LOW confidence)

- None used as an implementation authority.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — standard library only, exact project pins read, local pinned-mypyc probe passed.
- Architecture: HIGH — derived from locked decisions and opened predecessor/current code seams.
- Cross-version native compatibility: MEDIUM — official API availability checked; only CPython 3.12/macOS compiled locally.
- Pitfalls: HIGH — `safe_trigger`, nested public delegation, shared marker, and observer-test conflicts are directly visible in source/tests.
- Validation architecture: HIGH — extends the already verified Phase 17 fresh-origin harness and existing deterministic event pattern.

**What might have been missed:** platform-specific free-threaded/native behavior outside the local macOS CPython 3.12 environment; alternative event-loop implementations that obey public asyncio APIs but differ in private lock binding; and a hidden public mutator outside `core.py`. The plan should answer the last point with an AST/structural inventory test and the first two with the supported CI matrix.

**Research date:** 2026-09-01
**Valid until:** 2026-10-01
