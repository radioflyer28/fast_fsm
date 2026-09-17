---
phase: 29-expected-domain-rejection
verified: 2026-09-17T17:44:59Z
status: passed
score: 10/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 15
  total: 15
  not_honored: []
human_verification: []
---

# Phase 29: Expected Domain Rejection Verification Report

**Phase Goal:** Applications can reject an otherwise considered transition as an expected domain outcome without hiding defects or selecting a lower-priority behavior.
**Verified:** 2026-09-17T17:44:59Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Public `TransitionRejected(code)` accepts only exact built-in strings matching `[a-z][a-z0-9_.-]*` at length 1..64, validates eagerly without normalization, and exposes a read-only code. | ✓ VERIFIED | `src/fast_fsm/core.py:558-599` implements exact-type, length-before-scan, ASCII validation and getter-only storage. Active boundary tests in `tests/test_expected_rejection.py:24-68` cover valid endpoints, `str` subclasses, empty/oversized, uppercase, whitespace, slash, and Unicode values. |
| 2 | Expected rejection produces an uncommitted, destination-free result with `cause=None`, bounded error text, comparison-neutral repr-visible `rejection_code`, derived `rejected`, and unchanged `TransitionError` escalation. | ✓ VERIFIED | `src/fast_fsm/core.py:608-645` and `:3834-3858`; `test_reject_05_result_tail_is_read_only_and_preserves_error_boundary` passed. Runtime/stub field layout and public export structural tests also passed. |
| 3 | Only transition guards, declarative guards, and state permission checks convert expected rejection, preserving source, trigger, stage, selected priority, and internal mode before lifecycle begins. | ✓ VERIFIED | Exactly three sync conversions at `core.py:2988`, `:3051`, `:3138` and three async conversions at `:5313`, `:5354`, `:5402`; no conversion exists in trigger, lifecycle, observer, tracing, or `conditions.py`. The parameterized approved-boundary and query matrices passed for singleton/grouped and internal/external cases. |
| 4 | Ordinary false eligibility may fall through in deterministic priority order, but expected rejection and unexpected exceptions stop the complete candidate group before any lower candidate or lifecycle work. | ✓ VERIFIED | `_select_transition_sync()` / `_select_transition_async()` advance only on `None`; every rejection catch returns a terminal `TransitionResult`. Sync and async false-before-rejection tests pass and assert the later candidate is untouched. |
| 5 | `can_trigger()` and `can_trigger_async()` project expected rejection to `False` without state/history mutation, lifecycle, observer notification, trace finalization, or lower-candidate evaluation. | ✓ VERIFIED | `core.py:2730-2752` and `:5147-5164` project terminal selector results directly. The full sync/async three-boundary query matrices passed and assert unchanged state/history and zero observers/lower candidates. |
| 6 | Real rejected triggers use the existing failure-observer family exactly once, with unchanged callback shape, while logging exposes only validated debug-level scalar metadata. | ✓ VERIFIED | `_trigger_owned()` and `_trigger_async_owned()` each call shared `_finalize_failure()` once; `core.py:3845-3849` logs only the validated code. Observer failure/reentry and hostile-repr logging tests passed. |
| 7 | Direct, AND, OR, NOT, legacy negation, nested, deferred, synchronous, and asynchronous condition evaluation propagates the same rejection signal and does not evaluate a later child. | ✓ VERIFIED | `src/fast_fsm/conditions.py` remains catch-free. All 20 active `test_condition_interface.py` cases passed, including the post-review cancellation later-child sentinel. |
| 8 | Async cancellation remains cancellation, retains staged priority/internal truth, prevents later candidate/child evaluation, finalizes through existing ownership, and releases ownership. | ✓ VERIFIED | Selector catches remain `Exception`-only and `_trigger_async_owned()` retains its dedicated `CancelledError` finalizer/re-raise at `core.py:5560-5588`. Focused composition cancellation and fresh compiled semantic-oracle tests passed. |
| 9 | The same signal outside approved eligibility seams retains ordinary staged execution-failure or process-control behavior with correct cause, commit, destination, history, priority, and internal truth. | ✓ VERIFIED | Timing, sync lifecycle, async lifecycle, declarative action, and observer tests passed; ordinary lifecycle results retain the original signal as hidden cause and have `rejected=False`. No outer conversion catch exists. |
| 10 | Runtime, stub, package export, slots policy, selective compilation, docs, and pure/native execution agree on one bounded contract without widening the direct singleton success path. | ✓ VERIFIED | Structural tests passed; slots audit reports exactly four registered exceptions; Sphinx `-W` passed; a fresh mypyc build loaded `core.cpython-312-darwin.so` and passed the focused semantic oracle; generated shadows were recoverably moved to `/private/tmp/fast-fsm-phase29-verifier-native.i5Jkzq`, after which exact pure origin was reconfirmed as `src/fast_fsm/core.py`. |

**Score:** 10/10 truths verified (0 present, behavior-unverified)

### Roadmap Success Criteria Coverage

| Roadmap criterion | Covered by truths | Status |
|-------------------|-------------------|--------|
| Bounded public signal, including composed conditions | 1, 7 | ✓ VERIFIED |
| False fallthrough versus terminal expected/unexpected outcomes | 3, 4 | ✓ VERIFIED |
| Structured result plus side-effect-free boolean queries | 2, 5 | ✓ VERIFIED |
| One existing failure-observer notification and bounded diagnostics | 6 | ✓ VERIFIED |
| Outside-seam failure and cancellation truth | 8, 9 | ✓ VERIFIED |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fast_fsm/core.py` | Signal, result carrier, six selector conversions, finalization | ✓ VERIFIED | Substantive implementation; exact six cold-path classifier calls and no broad conversion catch. |
| `src/fast_fsm/core.pyi` | Typed public exception/result contract | ✓ VERIFIED | Declares `TransitionRejected`, trailing `rejection_code`, and read-only `rejected`. |
| `src/fast_fsm/__init__.py` | Package-root export | ✓ VERIFIED | Imported and listed in `__all__`. |
| `src/fast_fsm/conditions.py` | Catch-free composition propagation | ✓ VERIFIED | Existing iterative/deferred/negation paths propagate exceptions naturally; active behavioral tests cover the path. |
| `tests/test_expected_rejection.py` | Central REJECT-01..09 oracle | ✓ VERIFIED | 769 lines, 57 active collected cases, no disabled tests; full file passed. |
| `tests/test_condition_interface.py` | Composition and cancellation oracle | ✓ VERIFIED | 20 active collected cases; full file passed. |
| `tests/test_transition_lifecycle.py` | Ordinary outside-boundary failure truth | ✓ VERIFIED | Parameterized lifecycle behavior test passed in the verifier spot-check. |
| `tests/test_logging_config.py` | Metadata confidentiality | ✓ VERIFIED | Hostile signal/payload repr test passed. |
| `tests/test_mypyc_guard.py` | Structural and pure/native contract | ✓ VERIFIED | Two expected-rejection structural/semantic tests passed in pure mode; semantic test also passed from a fresh compiled origin. |
| `tests/test_release_evidence.py` / `tools/release_evidence.py` | Exact slots-policy authority | ✓ VERIFIED | Exact four-exception authority test and live slots audit passed. |
| `docs/api/core.md` / `docs/api/conditions.md` | Focused public reference | ✓ VERIFIED | Exact signal/result/query/composition/boundary semantics documented; warnings-as-errors Sphinx build passed. |
| `.github/copilot-instructions.md` / `.specify/memory/spr-core-api.md` | Maintainer policy and living architecture contract | ✓ VERIFIED | Both name the four measured exceptions and selector-only rejection contract. |

**Artifacts:** 12/12 artifact groups verified at existence, substance, and wiring levels.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `TransitionRejected.__init__` | selector conversion | shared exact validator plus cold-path revalidation | ✓ WIRED | `_validate_transition_rejection_code()` is used at construction and by `_revalidate_transition_rejection_code()` at all conversion sites. |
| sync selector hooks | `TransitionResult` | `_build_rejection_result()` | ✓ WIRED | Transition guard, declarative guard, and permission catches all return the same terminal builder. |
| async selector hooks | `TransitionResult` | `_build_rejection_result()` | ✓ WIRED | Same three approved awaited seams; cancellation remains outside `Exception` handling. |
| trigger boundaries | failure observers | shared `_finalize_failure()` | ✓ WIRED | Sync and async trigger owners finalize a terminal result once; selectors never notify. |
| query boundaries | selectors | terminal-result-to-`False` projection | ✓ WIRED | No failure finalizer, lifecycle, or trace call occurs in query methods. |
| condition composition | selector boundary | unchanged exception propagation | ✓ WIRED | No catch in combinators; direct calls propagate and machines convert only at selector hooks. |
| lifecycle surfaces | ordinary failure results | existing lifecycle builders | ✓ WIRED | No rejection-specific catch; original signal remains `cause`. |
| runtime carrier | stub and package facade | matching symbol/field/property export | ✓ WIRED | Structural test passed. |
| slots registry | release tests and policy docs | exact four-name authority | ✓ WIRED | Release authority test and runtime inventory passed. |
| API implementation | Sphinx reference | documented exception/result/condition semantics | ✓ WIRED | Strict docs build passed. |

**Wiring:** 10/10 connections verified manually. The plan key-link query could not auto-resolve symbol names because the plans use conceptual `from`/`to` values rather than file paths; direct source tracing above resolves every link.

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|----------|---------------|--------|--------------------|--------|
| `TransitionRejected` | validated `code` | caller-provided exact built-in string | Yes — validated at construction and conversion | ✓ FLOWING |
| selector result | `rejection_code`, stage, priority, internal | caught eligibility signal plus selected entry | Yes — copied into a terminal uncommitted result | ✓ FLOWING |
| query result | boolean | terminal selector result | Yes — projects to `False` without finalization | ✓ FLOWING |
| trigger observation | bounded `error` | rejected result | Yes — existing observers receive one unchanged callback pass | ✓ FLOWING |
| docs | public contract | runtime/stub surface | Yes — autodoc/API reference builds with warnings as errors | ✓ FLOWING |

No rendered UI or database data flow exists in this headless library phase.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Validation, priority terminality, sync query side effects, observers, composition/cancellation, lifecycle classification | Six named pytest nodes from the central, condition, and lifecycle suites | 41 parameterized cases passed | ✓ PASS |
| Complete focused rejection/composition/logging oracle | `uv run pytest tests/test_expected_rejection.py tests/test_condition_interface.py tests/test_logging_config.py::test_expected_rejection_logs_only_validated_debug_metadata -q` | 78 active cases passed | ✓ PASS |
| Structural contract | `uv run pytest tests/test_mypyc_guard.py -q -k expected_rejection` | 2 passed | ✓ PASS |
| Slots authority | exact release-evidence test plus live `slots-policy --json` | 1 test passed; exactly four registered exceptions reported | ✓ PASS |
| Fresh compiled semantics | `task build-check` then compiled expected-rejection semantic test | Compiled smoke test and focused semantic oracle passed | ✓ PASS |
| Pure-source restoration | `task pure-source-check` plus exact module-origin assertion | `src/fast_fsm/core.py` confirmed | ✓ PASS |
| Public API docs | `uv run sphinx-build -b html docs docs/_build/html -W --keep-going` | Build succeeded with no warnings | ✓ PASS |
| Prior-phase regression gate | Orchestrator's just-completed 10-file prior-phase gate | No failures | ✓ PASS (corroborating) |

### Probe Execution

No Phase 29 `probe-*.sh` paths are declared by the plans or summaries, and this runtime-library phase does not imply a separate probe contract. **SKIPPED (no declared probes).**

### Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| REJECT-01: public pre-commit `TransitionRejected(code)` | 29-01, 29-04 | ✓ SATISFIED | Public runtime/stub/export and exact construction tests. |
| REJECT-02: stable bounded payload-safe identifiers | 29-01, 29-03, 29-04 | ✓ SATISFIED | Positive validation, conversion revalidation, fixed text, hostile-repr logging test. |
| REJECT-03: selector-only conversion seams | 29-01, 29-02, 29-03, 29-04 | ✓ SATISFIED | Exactly six conversion sites plus approved/outside-boundary behavioral matrices. |
| REJECT-04: rejection aborts group while false falls through | 29-01, 29-02, 29-04 | ✓ SATISFIED | Sync/async false-before-rejection tests and lower-candidate sentinels. |
| REJECT-05: explicit uncommitted rejected result distinct from cause | 29-01, 29-04 | ✓ SATISFIED | Result contract test and builder implementation. |
| REJECT-06: sync/async queries return false without side effects | 29-02, 29-04 | ✓ SATISFIED | Full three-boundary query matrices. |
| REJECT-07: existing observers exactly once | 29-01, 29-02, 29-03, 29-04 | ✓ SATISFIED | Shared finalizer wiring and failing/reentrant observer test. |
| REJECT-08: composed conditions preserve rejection | 29-02, 29-04 | ✓ SATISFIED | Direct/nested/deferred/negated sync/async tests. |
| REJECT-09: outside-seam ordinary failure truth | 29-02, 29-03, 29-04 | ✓ SATISFIED | Timing, lifecycle, observer, and cancellation tests. |

**Coverage:** 9/9 requirements satisfied. No Phase 29 requirement is orphaned from the plans.

### Decision Coverage

All **15/15** trackable decisions in `29-CONTEXT.md` are honored. The GSD decision-coverage query returned `not_honored: []`; direct source and test evidence confirms D-01 through D-15 rather than relying on the heuristic alone.

### Prohibition Checks

| Prohibition group | Status | Evidence |
|-------------------|--------|----------|
| No alternate rejection API, status enum, stored boolean, rich payload, validator, or listener family | ✓ RESOLVED | One public signal, one scalar result field, derived property, and existing observer registry only. |
| No expected-rejection-as-`False`/`None` in dispatch and no lower candidate after rejection | ✓ RESOLVED | Terminal result wiring and sync/async sentinel tests. |
| No broad lifecycle/trigger/composition conversion catch | ✓ RESOLVED | Exactly six selector classifier calls; none in `conditions.py`, trigger owners, lifecycle, observers, or tracing. |
| No speculative async fan-out, shielding, second selector, or rejection `ContextVar` | ✓ RESOLVED | Sequential existing selector retained; structural oracle passed. |
| No slots-policy weakening, extra dependency, compiled `conditions.py`, or fifth exception | ✓ RESOLVED | Live slots audit and compiler configuration remain exact. |
| No generated native shadow left in source | ✓ RESOLVED | Fresh verifier artifacts moved recoverably; final pure-source and exact-origin assertions passed. |
| No Phase 31/32 diagnostics/tutorial/installed-artifact claims pulled forward | ✓ RESOLVED | Docs remain API-reference focused; later roadmap scope remains intact. |

### Test Quality Audit

| Test file | Linked requirements | Active | Skipped relevant tests | Circular | Strongest assertion | Verdict |
|-----------|---------------------|--------|------------------------|----------|--------------------|---------|
| `tests/test_expected_rejection.py` | REJECT-01..09 | 57 collected | 0 | No | Behavioral state/result/order/observer assertions | ✓ STRONG |
| `tests/test_condition_interface.py` | REJECT-08, cancellation part of REJECT-09 | 20 collected | 0 | No | Signal identity, child ordering, cancellation | ✓ STRONG |
| `tests/test_transition_lifecycle.py` | REJECT-03, 07, 09 | Yes | 0 requirement-linked skips | No | Multi-stage commit/state/history/cause assertions | ✓ STRONG |
| `tests/test_logging_config.py` | REJECT-02, 07 | Yes | 0 requirement-linked skips | No | Exact records, levels, and hostile-repr non-use | ✓ STRONG |
| `tests/test_mypyc_guard.py` | REJECT-01..09 structural/native | 2 focused | Native/platform skips elsewhere have active pure and fresh-native routes | No | AST/layout plus full semantic workflow | ✓ STRONG |
| `tests/test_release_evidence.py` | slots/release closure | Yes | Platform skips unrelated to Phase 29 authority | No | Exact-set/runtime-layout value assertions | ✓ STRONG |

**Disabled tests on requirements:** 0.  
**Circular patterns detected:** 0.  
**Insufficient assertions:** 0.

Disconfirmation note: corrupt post-construction signal handling is directly behavior-tested at the synchronous transition-guard seam rather than separately parameterized at all six seams. This is not a coverage failure: all six sites call the same revalidation helper, structural tests assert the exact sites, and both pure and fresh-compiled semantic oracles passed. A broader corrupt-signal parameter matrix would be defense-in-depth only.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| Phase 29 changed files | — | No added `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, placeholder, empty implementation, or disabled requirement test | — | None |

The phrase “not available” in `_PRIORITY_GROUP_RUNTIME_ERROR` is an established runtime error constant, not a placeholder. Existing platform/native skip guards are backed by active pure tests and the verifier's fresh compiled run.

### Human Verification Required

N/A — infrastructure/foundation library phase with no user-facing UI or external service. All acceptance criteria, including state transitions, ordering, cancellation, observer behavior, native parity, and documentation, are verified programmatically.

### Gaps Summary

**No gaps found.** Phase 29's goal is achieved. Expected rejection is a bounded, machine-readable, selector-only terminal outcome; ordinary false eligibility still falls through, defects and cancellation retain distinct truth, and the result/observer/query/condition/native contracts are wired and exercised.

---

_Verified: 2026-09-17T17:44:59Z_  
_Verifier: the agent (gsd-verifier)_
