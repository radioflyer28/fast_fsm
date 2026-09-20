# Phase 29: Expected Domain Rejection - Pattern Map

**Mapped:** 2026-09-17  
**Files analyzed:** 17 anticipated implementation, test, policy, and API-documentation files  
**Analogs found:** 17 / 17

Phase 29 should extend the existing terminal TransitionResult protocol. Copy the current result construction, local priority selection, query, lifecycle, observer, and native-layout seams. Do not add a second dispatch path, listener family, status enum, or condition-composition runtime.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| src/fast_fsm/core.py | public API, selector, result, exception | request-response / event-driven | TransitionError, TransitionResult, selector helpers | exact |
| src/fast_fsm/core.pyi | typed public stub | request-response API | TransitionError/TransitionResult declarations | exact |
| src/fast_fsm/__init__.py | package export facade | request-response API | existing core/condition exports and __all__ | exact |
| tests/test_expected_rejection.py | central integration/unit test | request-response / event-driven | priority and lifecycle matrices | role/data-flow exact |
| tests/test_priority_selection.py | selection regression | event-driven candidate selection | false fallthrough and terminal-exception tests | exact |
| tests/test_condition_interface.py | composition unit/async test | transform / async streaming | operator and deferred-await tests | exact |
| tests/test_transition_lifecycle.py | lifecycle/observer integration | event-driven | precommit/postcommit/cancellation matrices | exact |
| tests/test_async.py | async regression | async request-response | async trigger/query/ownership tests | role-match |
| tests/test_logging_config.py | logging confidentiality | event-driven / log output | metadata-only trace and hostile-repr tests | exact |
| tests/test_mypyc_guard.py | structural/native parity | build/evidence | result layout and pure/native oracles | exact |
| tests/test_release_evidence.py | policy/release test | batch/evidence | registered-exception authority tests | exact |
| tools/release_evidence.py | build policy utility | batch/file-I/O | REGISTERED_SLOTS_EXCEPTIONS and slots audit | exact |
| setup.py | compiler configuration (verify unless required) | build artifact | selective core.py mypyc compilation | role-match |
| .github/copilot-instructions.md | project policy | documentation/config | measured exception and quality-gate policy | exact |
| .specify/memory/spr-core-api.md | architecture contract | documentation | result/selector/native-layout rules | exact |
| docs/api/core.md | public API documentation | request-response docs | result/exception and priority sections | exact |
| docs/api/conditions.md | condition semantics documentation | composition docs | composition and short-circuit guidance | role-match |

src/fast_fsm/conditions.py is a verify-only source analog. Its combinators already propagate child exceptions, so add proof tests rather than special catches.

## Pattern Assignments

### src/fast_fsm/core.py — public API and selectors

Analogs: TransitionError and TransitionResult at core.py:536-603; sync selection at core.py:2771-3051; async selection at core.py:4991-5209; failure construction/finalization at core.py:3631-3709; trigger ownership at core.py:4179-4236 and 5298-5348.

Public exception boundary:

~~~python
@mypyc_attr(native_class=False)
class TransitionError(RuntimeError):
    def __init__(self, result: "TransitionResult") -> None:
        self.result = result
        ...
~~~

TransitionRejected is a control signal, not the result-consumption error. Keep only the validated code as public payload. Do not retain caller objects or format arbitrary exception messages. Its code validation belongs in the cold construction/conversion path.

Result carrier:

~~~python
@dataclass(slots=True)
class TransitionResult:
    success: bool
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    trigger: Optional[str] = None
    error: str = ""
    committed: bool = field(default=False, compare=False)
    stage: Optional[str] = field(default=None, compare=False)
    cause: Optional[BaseException] = field(default=None, repr=False, compare=False)
    priority: Optional[int] = field(default=None, compare=False)
    internal: bool = field(default=False, compare=False)
~~~

Append rejection_code as comparison-neutral and repr-visible; derive rejected from that field. Do not add a second boolean or status enum. Expected rejection uses cause=None, committed=False, to_state=None, and fixed bounded error text. Preserve raise_if_failed and TransitionError cause chaining.

Sync candidate scan:

~~~python
if isinstance(slot, _TransitionGroup):
    for entry in slot.entries:
        selected = self._select_sync_candidate(..., scan_group=True, ...)
        if selected is not None:
            return selected
    return self._build_failure_result(..., stage=_LIFECYCLE_STAGE_SELECTION)
~~~

None is the only group-fallthrough value. A caught rejection must return a terminal TransitionResult carrying candidate priority and internal metadata. Catch it only around:

1. transition condition evaluation at core.py:2915-2928;
2. declarative guard evaluation at core.py:2965-2994;
3. state permission at core.py:3016-3037.

Do not catch around timing, prepared dispatch construction, handlers, callbacks, observers, tracing, or the outer trigger. Unexpected exceptions retain their existing redacted message and hidden cause.

Async selection at core.py:5066-5209 mirrors the same three catch sites around awaited operations. Preserve task-local selection stage/priority/internal values used by cancellation. Catch Exception, not BaseException; CancelledError must reach core.py:5298-5344, be finalized once, and be re-raised unchanged.

Failure construction/finalization:

~~~python
return TransitionResult(
    False,
    from_state=from_state,
    to_state=to_state,
    trigger=trigger,
    error=error,
    committed=committed,
    stage=stage,
    cause=cause,
    priority=priority,
    internal=internal,
)
~~~

Extend _build_failure_result with a rejection-code argument or a narrow construction helper, but keep it observer-free. _trigger_owned and _trigger_async_owned remain the only trigger finalization owners. _finalize_failure snapshots tuple(self._on_failed_callbacks), keeps the unchanged callback signature, isolates observer failures, and returns the original result. Reuse it for rejection. Queries use their existing not isinstance(selected, TransitionResult) projection and must not finalize, mutate history, or trace.

Only selectors convert TransitionRejected. A signal raised by source-exit, destination-enter, handlers, trigger callbacks, observers, or after-transition remains an ordinary staged lifecycle failure with hidden cause and accurate commit/history truth.

Hot-path pitfalls: preserve direct singleton dispatch and local immutable group scans. Do not add sorting, reflection, copies, rejection ContextVars, success-path formatting, or speculative async work. Reject oversized codes before pattern scanning.

### src/fast_fsm/core.pyi — typed public stub

Analog: core.pyi:86-122.

Add TransitionRejected and trailing rejection_code: str | None plus a read-only rejected property with the same defaults and field order as runtime. Keep cause non-repr in the stub and preserve constructor compatibility. Do not widen the code type beyond exact str semantics.

### src/fast_fsm/__init__.py — export facade

Analog: __init__.py:7-42 imports and __all__ at :45-94.

Re-export TransitionRejected beside TransitionError in both import and __all__. Keep the package facade as the user-facing import path; do not create an alternate exception module.

### src/fast_fsm/conditions.py — verify-only composition component

Analog: _check_compound_conditions and _continue_compound_check at conditions.py:91-203, and NotCondition.check at :249-256.

~~~python
for condition in remaining:
    next_result = condition.check(*args, **kwargs)
    if _is_awaitable_guard_result(next_result):
        current = bool(await next_result)
    else:
        current = bool(next_result)
~~~

These helpers do not catch child exceptions. That is the desired pattern: rejection propagates immediately, later children are not evaluated, and NotCondition negates only boolean returns. Preserve direct evaluation outside an FSM boundary. Test recursive, nested, deferred, sync, and async cases; do not add conversion in conditions.py.

### tests/test_expected_rejection.py — new central semantic oracle

Analogs: tests/test_priority_selection.py:670-834 and :920-1133; tests/test_transition_lifecycle.py:506-576; existing async cancellation matrices.

Use requirement-labelled tests for REJECT-01 through REJECT-09. Parameterize transition guard, declarative guard, permission, sync/async, query/trigger, priority/internal metadata, and lifecycle location. Use event sentinels to prove no lower candidate or later child ran. Use asyncio.Event handshakes, not sleeps.

~~~python
machine.add_transition("go", source, failed, raising_condition, priority=-1)
machine.add_transition("go", source, later, later_condition, priority=1)
result = machine.trigger("go")
assert result.success is False
assert events == ["raising-condition"]
assert machine.current_state is source
~~~

### tests/test_priority_selection.py — selection regression

Analogs:
- test_sync_group_rejections_fall_through_each_eligibility_stage at :670-738;
- test_sync_group_guard_exception_is_terminal_and_finalized_once at :797-834;
- declarative/permission exceptions at :920-991;
- query tests at :1018-1133;
- async terminal/cancellation tests at :287-553.

Copy the existing distinction: False returns None and allows group fallthrough; exceptions are terminal; exhaustion creates one selection failure and observer pass; queries share ordering but do not finalize or mutate. Add rejection cases asserting cause is None, code, selected priority/internal, fixed error, no history, no lower candidate, and exactly one observer. Keep ordinary RuntimeError tests as the defect/cancellation regression guard.

### tests/test_condition_interface.py — composition unit/async

Analog: :55-98.

~~~python
combined_and = false & true
combined_or = false | true
negated = ~false
assert not combined_and.check()
assert combined_or.check()
assert await deferred
with pytest.raises(RuntimeError, match="cannot reuse"):
    await deferred
~~~

Add a raising leaf and later-child sentinel for And, Or, Not, and NegatedCondition. Assert signal identity and no later child. Extend deferred async coverage for one await ownership and unchanged cancellation.

### tests/test_transition_lifecycle.py — lifecycle and observers

Analogs: :422-504 committed destination-enter failure; :526-576 precommit truth; :578-666 observer isolation/reentry; :1018-1053 postcommit declarative failure.

~~~python
assert result.committed is True
assert result.stage == "destination-enter"
assert result.cause is failure
assert machine.history == [...]
~~~

Raise TransitionRejected from each post-selection surface. Assert ordinary stage-aware failure, hidden cause, commit/history truth, and no relabeling as expected rejection. Reuse ordered, failing, and reentrant observers to prove one unchanged finalization pass.

### tests/test_async.py — async ownership/regression

Use pytest.mark.asyncio, asyncio.Event, and existing task cleanup helpers. Assert sync/async parity, can_trigger_async false with zero observers/history, exact CancelledError identity/re-raise, and ownership release. Do not add sleeps, fan-out, shielding, rollback, or another selector.

### tests/test_logging_config.py — logging confidentiality

Analogs: metadata-only trace at :359-480; async failure trace at :805-873; redactor failures at :880-940.

~~~python
_assert_no_raw_payload(application_handler, hostile_payload, ...)
assert hostile_payload.repr_calls == 0
~~~

Add debug-level rejection checks allowing only validated scalar code metadata. Assert no exception repr, traceback, warning, raw trigger payload, or cause. Use hostile repr objects, caplog, capture handlers, and stderr.

### tests/test_mypyc_guard.py — structural/native oracle

Analogs: carrier tests at :2102-2268 and :2324-2395; hot-path AST checks at :1943-2012.

Extend the existing pure/native matrix for public exception/result property, field order/defaults, comparison/repr behavior, exactly three selector conversion sites, no sort/copy/reflection/task fan-out, direct singleton O(1) structure, and identical pure/native rejection oracle. Use existing origin/build helpers; do not relax structural checks for an alternate path.

### tests/test_release_evidence.py and tools/release_evidence.py — slots/build policy

Analogs: REGISTERED_SLOTS_EXCEPTIONS at tools/release_evidence.py:128-140 and tests/test_release_evidence.py:794-844.

Add fast_fsm.core.TransitionRejected as the fourth explicit instance-dictionary exception with a documented reason. Update registry, release assertions, project instructions, and SPR atomically. Keep only core.py compiled; conditions.py remains interpreted for user subclasses.

### .github/copilot-instructions.md and .specify/memory/spr-core-api.md — policy/architecture docs

Copy the current measured-exception, selector return-union, observer, performance, and pure/native parity wording. Update three exceptions to four and state the three-way outcome: false fallthrough, expected-rejection terminal result, unexpected exception/cancellation terminal failure. Preserve flat-FSM, no-reflection, no-hot-path-allocation, and unchanged observer contract.

### docs/api/core.md and docs/api/conditions.md — public docs

Copy the priority/result/exception sections in core.md and composition guidance in conditions.md. If the public symbol is documented in this phase, add TransitionRejected beside TransitionError, its exact bounded code grammar, selector-only conversion, and direct-condition propagation. Leave richer diagnostics and broad examples to later phases.

## Shared Patterns

### Terminal selection protocol

Sources: core.py:2771-3051 and :4991-5209; spr-core-api.md:28.

| Value | Meaning | Group behavior |
|---|---|---|
| None | ordinary false/timing ineligibility | continue local priority scan |
| _PreparedDispatch | selected candidate | begin lifecycle |
| TransitionResult | terminal failure/rejection | stop scan; finalize only at trigger |

Expected rejection belongs in the third row. Never encode it as False or None.

### Observer ownership and redaction

Source: core.py:3687-3709 and lifecycle tests :526-666.

Build results in selectors and finalize once at the public trigger. Keep callback signature, observer snapshot, and isolation. Public text is fixed/bounded; ordinary causes stay hidden in cause. Expected rejection specifically uses cause=None.

### Sync/async parity and cancellation

Sources: core.py:4974-5348 and priority/lifecycle async tests.

Keep the same eligibility order and three catch sites. Use task-local metadata only for existing cancellation. Never catch BaseException, swallow CancelledError, shield callbacks, or change finally-based ownership release.

### Mypy/mypyc and slots policy

Sources: setup.py:16-39, tools/release_evidence.py:128-140, tests/test_release_evidence.py:794-844, copilot-instructions.md:40-50.

core.py is the only compiled unit. conditions.py remains interpreted for Condition subclasses. Public exceptions must be explicitly listed in the measured slots registry; TransitionRejected becomes the fourth registered exception. Runtime, stub, evidence, and policy text must agree.

### Logging safety

Sources: tests/test_logging_config.py:359-480 and :805-940.

Use metadata-only categories. Never interpolate caller values, exception messages, exception reprs, tracebacks, or arbitrary rejection objects. Prove this with hostile repr and captured records.

## No Analog Found

None. The new public signal has no exact existing class, but TransitionError is a direct exception-boundary analog and all runtime semantics have close priority/lifecycle counterparts. No new framework, dependency, fixture module, or architecture seam is needed.

## Planner Pitfalls and Prohibitions

- Do not catch TransitionRejected in lifecycle, handler, observer, or tracing code.
- Do not convert rejection to ordinary false or permit priority fallthrough.
- Do not expose str(exc), repr(exc), arbitrary payloads, or rich rejection objects.
- Do not add rejection listeners, a second result status field, rollback, queues, schedulers, or statecharts.
- Do not alter legacy TransitionResult equality; use compare=False for the appended code.
- Do not add success-path regex/formatting/allocation or speculative async work.
- Do not weaken slots policy or move conditions.py into mypyc compilation.

## Metadata

**Analog search scope:** src/fast_fsm, tests, tools, docs/api, .github, .specify/memory, setup.py.  
**Files scanned:** 20+ targeted source, tests, policy, and documentation files.  
**Pattern extraction date:** 2026-09-17

