<!-- refreshed: 2026-08-29 -->
# Codebase Concerns

**Analysis Date:** 2026-08-29

**Assessment Basis:** Independent source review and executable reproduction of
the highest-risk edge cases. Items labeled as bugs below were reproduced on
CPython 3.12.10 against the local compiled-core checkout unless explicitly
described as static/configuration findings.

**Priority Summary:** Fix release-version drift and graph/dispatch correctness
before expanding the API. The 722 passing tests are substantial, but they do not
cover several malformed-topology, async-parity, and release-integrity cases.

## Tech Debt

**Core runtime concentration:**
- Issue: The public state machine, async variant, declarative states, builder, logging helpers, serialization, and lifecycle behavior are all implemented in one 2,864-line module.
- Files: `src/fast_fsm/core.py`
- Impact: Changes to one execution path are easy to make without preserving the parallel sync/async or builder path; the duplicated trigger logic already has observable behavior differences.
- Fix approach: Keep the public API stable, but extract shared transition resolution, failure notification, and callback dispatch into small internal units and add parity tests for each sync/async operation.

**Builder mutability after build:**
- Issue: `FSMBuilder.build()` caches a machine and returns it on subsequent calls, while `add_state()`, `add_transition()`, and callback-registration methods continue changing only the builder staging lists afterward.
- Files: `src/fast_fsm/core.py:2382-2461`, `src/fast_fsm/core.py:2587-2658`
- Impact: A caller can append a state or transition after `build()` and receive a stale machine without an error; the API gives no indication that the new configuration was ignored.
- Fix approach: Reject all mutating builder calls after `build()` or invalidate/rebuild the cache consistently; test every mutator after a first build.

**Graph registration invariants are implicit:**
- Issue: `add_transition()` creates a `_transitions[from_state_name]` bucket for an unknown source but does not add that source to `_states`; a `State` object passed as `to_state` is also not registered automatically. Adding another `State` with an existing name silently replaces `_states[name]` while existing `TransitionEntry` objects retain the old object.
- Files: `src/fast_fsm/core.py:625-638`, `src/fast_fsm/core.py:640-742`
- Impact: `states`, `force_state()`, visualization, validation, and object-identity checks can disagree with the transition graph. Duplicate names can leave the active/target object different from `fsm._states[name]`.
- Fix approach: Validate or register both endpoints atomically, reject duplicate state names unless the same object is supplied, and add invariant checks covering `_states`, `_transitions`, and every `TransitionEntry`.

**Optional compilation hides build failures:**
- Issue: The packaging hook catches every `Exception` raised while importing or running mypyc and silently emits a pure-Python package with a warning.
- Files: `setup.py:16-42`
- Impact: A broken compiler configuration, source incompatibility, or packaging defect can ship as a slower artifact instead of failing CI/release; the performance contract is then silently lost.
- Fix approach: Catch only expected tool-availability failures, expose a strict build flag for releases, and verify the selected artifact type and benchmark threshold in wheel CI.

**Slots policy has an undocumented exception:**
- Issue: `CompiledFuncCondition` lives in compiled `core.py` but deliberately
  uses `@mypyc_attr(native_class=False)` without `__slots__`, so instances have a
  `__dict__`. This conflicts with the unqualified “all core classes” slots rule
  in `.github/copilot-instructions.md` and the zero-overhead messaging in
  `README.md`.
- Files: `src/fast_fsm/core.py:106-166`, `.github/copilot-instructions.md`
- Impact: Future contributors cannot tell whether the implementation or the
  written invariant is authoritative; memory claims can be overstated.
- Fix approach: Document a narrow measured exception or redesign the compiled
  wrapper so its storage and subclassing requirements satisfy the declared rule.

## Known Bugs

**Release/version records disagree:**
- Symptoms: `pyproject.toml` and `fast_fsm.__version__` report `0.2.2`, while
  `.planning/PROJECT.md` and `.planning/STATE.md` say v0.2.3 shipped. The
  v0.2.2/v0.2.3 feature set is still under `Unreleased` in `CHANGELOG.md`, and
  the `v0.2.3` Git tag points to source whose package metadata still says
  `0.2.2`. README/project guidance also advertises stale 290- and 653-test
  baselines instead of 722.
- Files: `pyproject.toml`, `src/fast_fsm/__init__.py`, `CHANGELOG.md`,
  `README.md`, `.planning/PROJECT.md`, `.planning/STATE.md`,
  `.github/copilot-instructions.md`
- Impact: The v0.2.3 release workflow builds artifacts whose package metadata
  says 0.2.2; release notes and support claims are not auditable from one source
  of truth.
- Fix approach: Choose the intended released version, update package metadata
  before tagging, move release notes into versioned changelog sections, and add
  a CI test comparing tag/package/changelog versions.

**Condition guards reject positional trigger arguments:**
- Symptoms: A transition with a condition returns a failed result when `trigger()` or `can_trigger()` receives positional arguments, even when the guard would accept them. The failure is `FuncCondition.check() takes 1 positional argument but 2 were given`.
- Files: `src/fast_fsm/core.py:1115-1124`, `src/fast_fsm/core.py:1520-1563`, `src/fast_fsm/conditions.py:36-92`
- Trigger: `fsm.add_transition("go", "a", "b", condition=lambda **kw: True); fsm.trigger("go", 1)`.
- Workaround: Pass all guard context as keyword arguments; this contradicts the `*args` forwarding advertised by `trigger()` and state callbacks.

**Zero-capacity history crashes successful transitions:**
- Symptoms: `enable_history(0)` followed by a successful trigger raises `IndexError` instead of recording nothing or rejecting the configuration.
- Files: `src/fast_fsm/core.py:594-609`, `src/fast_fsm/core.py:1478-1486`
- Trigger: Any successful transition after setting `max_entries <= 0`; trimming deletes index zero before the empty buffer can be appended to.
- Workaround: Use a positive `max_entries`; validate the argument and define behavior for zero explicitly.

**Declarative handlers are disconnected from FSM execution:**
- Symptoms: A `DeclarativeState` or `AsyncDeclarativeState` method marked with `@transition` is discovered and can be called directly through `handle_event()`/`handle_event_async()`, but `StateMachine.trigger()` and `AsyncStateMachine.trigger_async()` never invoke it. The transition can move state while the decorated method's side effects never happen.
- Files: `src/fast_fsm/core.py:2006-2149`, `src/fast_fsm/core.py:2209-2265`, `src/fast_fsm/core.py:1492-1585`, `src/fast_fsm/core.py:1812-1944`, `examples/declarative_state_example.py:70-99`, `examples/declarative_state_example.py:163-186`
- Trigger: Use a decorated state in a normal FSM and call the corresponding trigger; current example flows demonstrate this usage but no execution path calls `handle_event()`.
- Workaround: Invoke the handler manually or use `on_enter`/`on_exit` callbacks; either document this split explicitly or wire handlers into the transition path.

**Validator uses current state as initial state:**
- Symptoms: Validation performed after the machine advances starts reachability analysis from the current state, not the constructor's initial state, producing false unreachable/dead-state findings and misleading scores.
- Files: `src/fast_fsm/validation.py:36-56`, `src/fast_fsm/core.py:331-336`, `src/fast_fsm/core.py:861-869`
- Trigger: Advance an FSM, then construct `FSMValidator(fsm)`; `validator.initial_state` equals the advanced state while `fsm.initial_state_name` remains unchanged.
- Workaround: Validate before advancing or manually account for the initial state; use `fsm.initial_state_name` in the validator and add post-transition tests.

**Duplicate FSM names overwrite comparison results:**
- Symptoms: `compare_fsms()` and `batch_validate()` use `fsm.name` as a dictionary key, so two machines with the same name overwrite one another and rankings/counts no longer represent the input collection.
- Files: `src/fast_fsm/validation.py:1112-1154`, `src/fast_fsm/validation.py:1187-1203`
- Trigger: Pass two distinct machines with the same `name`.
- Workaround: Assign unique names before comparison; preserve positional results or reject duplicate names.

**Empty comparison crashes:**
- Symptoms: `compare_fsms()` with no arguments raises `ZeroDivisionError` while
  computing `avg_score`, despite already handling an empty ranking for
  `best_fsm`.
- Files: `src/fast_fsm/validation.py:1112-1157`
- Trigger: `compare_fsms()`.
- Workaround: Validate that at least one FSM is supplied or return a documented
  empty-result structure.

**Async `unless=` is not auto-detected by the builder:**
- Symptoms: `FSMBuilder` wraps an `AsyncCondition` used through `unless=` in `NegatedCondition`, then checks only the outer type. It builds a synchronous `StateMachine`, which has no `trigger_async()` and may call `asyncio.run()` from a running event loop.
- Files: `src/fast_fsm/core.py:2352-2380`, `src/fast_fsm/core.py:2407-2459`, `src/fast_fsm/conditions.py:95-121`
- Trigger: Build with `.add_transition(..., unless=AsyncCondition())` in auto-detect mode.
- Workaround: Call `force_async()` before adding/building or pass a pre-wrapped condition only after selecting `AsyncStateMachine` explicitly; recursively inspect compound/negated conditions.

**Cycle membership output is incomplete:**
- Symptoms: `to_json()` correctly reports `has_cycles=True` but records only the
  endpoints of each DFS back edge. For `a -> b -> c -> a`,
  `states_in_cycles` is `['a', 'c']` and omits `b`.
- Files: `src/fast_fsm/visualization.py:254-278`
- Impact: Agent/tool consumers receive a false list despite the public field
  claiming to identify states participating in cycles.
- Fix approach: Track the active DFS stack or compute strongly connected
  components, then test complete membership for cycles longer than two nodes.

## Security Considerations

**Trace logging exposes trigger payloads:**
- Risk: At the custom trace level, `_resolve_trigger()` formats and logs raw positional and keyword arguments. Applications may pass tokens, credentials, personal data, or other secrets as trigger context.
- Files: `src/fast_fsm/core.py:1307-1333`
- Current mitigation: Condition evaluation filters private keys and caps keyword count in the synchronous path, but the trace log occurs before that sanitization and logs the original payload.
- Recommendations: Never log values by default; log key names or an explicit redacted representation, document the data exposure of trace mode, and allow an application-supplied redactor.

**Async guards bypass condition sanitization:**
- Risk: `trigger_async()` and `can_trigger_async()` pass raw `*args`/`**kwargs` to async and sync conditions, unlike synchronous methods that call `_sanitize_condition_kwargs()`.
- Files: `src/fast_fsm/core.py:1100-1124`, `src/fast_fsm/core.py:1782-1810`, `src/fast_fsm/core.py:1837-1852`
- Current mitigation: The sync sanitizer removes `_`-prefixed keys and limits key count; there is no equivalent on the async execution path.
- Recommendations: Centralize sanitization and use the same policy for every condition type/path, with explicit opt-in for sensitive context rather than relying on callers to choose sync execution.

**Global logger configuration has application-wide side effects:**
- Risk: `configure_fsm_logging()` clears all handlers from the named logger and adds its own handler, potentially removing host-application handlers or changing output/duplication through propagation.
- Files: `src/fast_fsm/core.py:2679-2725`, `tests/test_logging_config.py:20-60`
- Current mitigation: Tests verify handler counts for isolated logger names; there is no ownership marker or restoration of handlers.
- Recommendations: Use a library-owned handler marker, avoid clearing application handlers, set propagation deliberately, and provide a reversible configuration API.

## Performance Bottlenecks

**History trimming is linear per recorded transition:**
- Problem: Once the history buffer reaches capacity, every transition executes `del self._history[0]` on a Python list.
- Files: `src/fast_fsm/core.py:1478-1486`
- Cause: Removing the first list element shifts all remaining entries.
- Improvement path: Use `collections.deque(maxlen=max_entries)` or a ring buffer; retain copy-on-read semantics for `history`.

**Validation longest-path analysis can be exponential:**
- Problem: Enhanced validation explores every acyclic branch and copies the visited set for each edge.
- Files: `src/fast_fsm/validation.py:654-706`
- Cause: `_find_longest_path()` has no memoization and can enumerate exponentially many paths in a branching DAG.
- Improvement path: Condense strongly connected components and memoize longest-path results on the DAG, or impose an explicit analysis budget for large FSMs.

**Matrix and path utilities scale quadratically or worse:**
- Problem: Adjacency generation allocates an N×N matrix; missing-transition scans inspect every state/event pair, and test-path generation branches across all outgoing transitions.
- Files: `src/fast_fsm/validation.py:118-196`, `src/fast_fsm/validation.py:198-262`
- Cause: These diagnostic APIs materialize dense structures regardless of sparse topology and have no size guard.
- Improvement path: Offer sparse adjacency output, stream/report aggregates, cap path expansion, and document complexity before using validators on generated or untrusted graphs.

**Synchronous callbacks block async callers:**
- Problem: `AsyncStateMachine.trigger_async()` invokes `_execute_transition()`, including synchronous state callbacks and listeners, directly on the event loop before awaiting async callbacks.
- Files: `src/fast_fsm/core.py:1812-1944`, `src/fast_fsm/core.py:1350-1466`
- Cause: The async path shares a synchronous callback executor; blocking user code cannot be detected or moved off-loop.
- Improvement path: Define callback execution contracts, provide an async-native dispatch path, and test event-loop responsiveness with blocking callbacks.

## Fragile Areas

**Callback failures are swallowed after state mutation:**
- Files: `src/fast_fsm/core.py:1350-1489`, `src/fast_fsm/core.py:1913-1944`
- Why fragile: Exceptions from `on_exit`, `on_enter`, listeners, and async callbacks are logged and ignored; `_current_state` is changed and a successful `TransitionResult` is returned even when required side effects fail.
- Safe modification: Preserve the current isolation contract only with an explicit failure policy (fail-fast, rollback, or best-effort), and include failure status in results/metrics. Test partial callback failure and history behavior.
- Test coverage: `tests/test_advanced_functionality.py` checks that callbacks run, but does not establish transactional semantics for partially failed callback chains.

**Reentrant and concurrent mutation is unsynchronized:**
- Files: `src/fast_fsm/core.py:1350-1585`, `src/fast_fsm/core.py:1691-1944`
- Why fragile: A callback can call `trigger()` while the outer transition still references the old current state, causing nested state changes to be overwritten by the outer assignment. Concurrent sync/async tasks can likewise interleave callbacks and state updates; no lock or reentrancy policy exists.
- Safe modification: Add a documented single-owner/thread-safety contract, reject or queue reentrant transitions, and use a lock/async lock only if it does not violate throughput requirements. Add deterministic interleaving tests.
- Test coverage: The suite has no concurrent or reentrant transition tests.

**Visualization assumes safe identifiers:**
- Files: `src/fast_fsm/visualization.py:28-104`, `src/fast_fsm/visualization.py:139-170`
- Why fragile: Mermaid IDs are generated by replacing invalid characters, so distinct names such as `a-b` and `a b` collide; PlantUML emits raw state, trigger, and title text without equivalent escaping.
- Safe modification: Generate collision-free aliases and quote/escape labels for each target syntax; test punctuation, Unicode, duplicate sanitized IDs, and user-controlled labels.
- Test coverage: `tests/test_visualization.py:89-216` exercises basic names and a few punctuation cases but not collision or injection-like strings.

**Validator and visualization couple to private runtime layout:**
- Files: `src/fast_fsm/validation.py:58-70`, `src/fast_fsm/visualization.py:79-102`, `src/fast_fsm/core.py:265-333`
- Why fragile: Diagnostics read `_states`, `_transitions`, and insertion order directly. Internal representation changes, duplicate state registration, or compiled-vs-interpreted differences can silently produce incorrect reports.
- Safe modification: Add a stable internal graph snapshot protocol and make all diagnostics consume it; keep invariant tests around endpoint registration and initial-state identity.
- Test coverage: Existing tests cover the current dictionaries, not representation-independent behavior.

## Scaling Limits

**Large or adversarial diagnostic graphs:**
- Current capacity: No state/event/path-size limit is enforced by `FSMValidator`, `EnhancedFSMValidator`, `to_json()`, or adjacency export.
- Limit: Dense diagnostics allocate O(states²) matrix storage; completeness is O(states×events); longest-path and path generation can grow exponentially with branching.
- Scaling path: Add configurable budgets, sparse representations, memoized graph algorithms, and reject or stream oversized exports. Treat config-driven `from_dict()` machines as untrusted input when diagnostics are exposed to external users.

**History buffers with large limits:**
- Current capacity: The default is 1,000 records, but callers may choose arbitrary positive values.
- Limit: List-front deletion is O(max_entries) per transition and each record retains three state/trigger references plus a timestamp.
- Scaling path: Use a bounded deque/ring buffer and validate an operational maximum or expose a memory estimate.

## Dependencies at Risk

**`ty` pre-release type checker:**
- Risk: Development and CI type validation depends on `ty>=0.0.1a19`, an alpha release explicitly described as pre-release by the tool itself.
- Impact: Type-check results and CI behavior can change unexpectedly across lockfile updates; type validation is not a stable release-quality gate.
- Migration plan: Pin a known-good version in `uv.lock`, monitor upgrades deliberately, and keep a stable checker such as mypy as the required compatibility gate until `ty` reaches a stable release.

**mypy/mypyc build toolchain:**
- Risk: `setup.py` compiles `core.py` with mypyc while the supported runtime path also needs interpreted subclass compatibility.
- Impact: Platform/compiler/Python-version differences can produce wheels with different behavior or fall back silently to pure Python.
- Migration plan: Build and run meaningful compiled-wheel tests on every supported platform/Python version, assert artifact selection, and retain an intentional pure-Python release path.

## Missing Critical Features

**Explicit transition transaction/failure policy:**
- Problem: There is no public way to choose whether callback failure should abort, roll back, or mark a transition unsuccessful after state mutation.
- Blocks: Reliable integration with side-effecting persistence, messaging, resource acquisition, or security callbacks that must not be reported as successful when a lifecycle hook fails.

**Thread/async ownership contract:**
- Problem: The public API provides mutable state and transition tables but no documented synchronization, single-owner restriction, or queueing model.
- Blocks: Safe use of one FSM from multiple worker threads or concurrent asyncio tasks without application-specific wrappers.

## Test Coverage Gaps

**Compiled extension versus source coverage:**
- What's not tested: The CI test matrix runs pure-Python tests, while the compiled job runs only a smoke test; current local compiled artifacts can cause coverage to report 0% for `src/fast_fsm/core.py` even when all tests pass.
- Files: `setup.py`, `.github/workflows/ci.yml`, `tests/test_mypyc_guard.py`, `src/fast_fsm/core.py`
- Risk: mypyc-only dispatch, extension import precedence, and platform-specific packaging regressions can ship unnoticed.
- Priority: High

**Local “pure Python” tasks can load stale compiled code:**
- What's not tested: `FAST_FSM_PURE_PYTHON=1` prevents `setup.py` from building
  an extension but does not stop an existing ignored `.so`/`.pyd` from shadowing
  `core.py`. The assessment's coverage run loaded
  `src/fast_fsm/core.cpython-312-darwin.so` and consequently measured `core.py`
  as 0%.
- Files: `Taskfile.yml`, `setup.py`, `.gitignore`, `src/fast_fsm/core.py`
- Risk: Developers can believe they tested the pure-Python path when they tested
  a stale compiled artifact; line coverage becomes misleading.
- Priority: High

**Guard argument and async sanitization parity:**
- What's not tested: Positional arguments to guarded sync/async transitions, private/unbounded kwargs on async conditions, and parity between `can_trigger*()` and `trigger*()`.
- Files: `src/fast_fsm/core.py`, `src/fast_fsm/conditions.py`, `tests/test_safety_kwargs.py`, `tests/test_async.py`
- Risk: Valid calls fail unexpectedly, or sensitive context bypasses the stated filtering policy.
- Priority: High

**Runtime graph invariants and builder lifecycle:**
- What's not tested: Unknown source endpoints, unregistered object targets, duplicate state names, post-build builder mutation, and `unless=AsyncCondition` auto-detection.
- Files: `src/fast_fsm/core.py`, `tests/test_builder.py`, `tests/test_basic_functionality.py`, `tests/test_advanced_functionality.py`
- Risk: Stale or internally inconsistent machines pass construction and fail later in state changes, diagnostics, or async execution.
- Priority: High

**Validation after state advancement and duplicate names:**
- What's not tested: Validator initial-state identity after transitions, comparison/batch behavior with duplicate machine names, and large branching graph analysis budgets.
- Files: `src/fast_fsm/validation.py`, `tests/test_validation.py`
- Risk: Health reports and rankings can be wrong or become impractically slow on real machines.
- Priority: Medium

**Quality gate drift:**
- Current status: The repository's quality gate is not green end-to-end. The
  full 722-test suite, `ty`, Sphinx HTML, and doctest checks pass, but
  `ruff check src/ tests/` reports an unused assignment at
  `tests/test_advanced_functionality.py:1488`, and `ruff format --check` reports
  `src/fast_fsm/visualization.py` would be reformatted.
- Files: `Taskfile.yml:60-89`, `.github/workflows/ci.yml:24-44`, `tests/test_advanced_functionality.py:1488`, `src/fast_fsm/visualization.py`
- Risk: A release or pull request can fail CI despite passing tests, obscuring actual regressions and weakening confidence in the documented baseline.
- Priority: Medium

---

*Concerns audit: 2026-08-29*
