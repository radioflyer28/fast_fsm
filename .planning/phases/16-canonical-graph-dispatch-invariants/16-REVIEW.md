---
phase: 16-canonical-graph-dispatch-invariants
reviewed: 2026-08-30T17:03:33Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - .specify/memory/spr-core-api.md
  - docs/dev/architecture.md
  - docs/dev/testing.md
  - evidence/release-baseline.json
  - src/fast_fsm/condition_templates.py
  - src/fast_fsm/conditions.py
  - src/fast_fsm/core.py
  - tests/test_advanced_functionality.py
  - tests/test_async.py
  - tests/test_boundary_negative.py
  - tests/test_builder.py
  - tests/test_condition_templates.py
  - tests/test_graph_invariants.py
  - tests/test_mypyc_guard.py
  - tests/test_performance_benchmarks.py
  - tests/test_safety_kwargs.py
  - tools/phase16_isolated_verify.py
findings:
  critical: 5
  warning: 1
  info: 0
  total: 6
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-08-30T17:03:33Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

The three preceding cycle-two findings are fixed on their covered paths. The
24 focused subclass, temporary-file, malformed-percentage, and migration cases
passed in both asserted-pure and freshly compiled exports. An independent
asserted-pure baseline check also reproduced the committed 1,129/1,129 tests
and 96.21% / 94.57% total / `core.py` coverage.

The final adversarial pass nevertheless found five blocker-tier gaps. Builder
classification still bypasses an async `FuncCondition.check()` override even
though runtime evaluation now honors it; first-time manifest publication skips
generated-value validation; the 1,129-test floor can be silently rewritten;
the destination leaf is resolved through an in-repository symlink; and
`quick_build()` still uses value equality and discards supplied state objects.
The new temporary-file path also changes a normal repository manifest from
mode `0644` to `0600`.

The intentional dynamic `Any` casts at the mypyc awaitability boundary remain
runtime-required and are not findings.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Builder async classification still bypasses a `FuncCondition` subclass override

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:1680-1684`

**Issue:** Runtime async evaluation now correctly distinguishes the exact
built-in `FuncCondition` from public subclasses, but
`_contains_async_requirement()` still applies `isinstance(current,
FuncCondition)` and inspects only `current.func`. A subclass whose stored
function is synchronous but whose effective `check()` override is declared
with `async def` is therefore classified as synchronous. In fresh asserted-pure
and compiled reproductions, an auto-mode `FSMBuilder` returned
`StateMachine`, not `AsyncStateMachine`; explicit-sync preflight likewise does
not reject the async requirement. This leaves the repaired awaitable runtime
path unreachable through the builder's promised auto-detection contract.

**Fix:** Mirror the exact-type split used by the evaluator. Inspect `.func`
only when `type(current) is FuncCondition`; for a subclass, inspect its
effective bound/type-level `check` method with `asyncio.iscoroutinefunction`.
Retain explicit `force_async()` for dynamically returned awaitables that cannot
be detected without executing user code. Add pure and compiled regressions for
auto and explicit-sync builders using an `async def check()` override, plus the
existing reject/raise/awaitable runtime cases.

### CR-02: First-time publication skips validation of the generated manifest

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/tools/phase16_isolated_verify.py:286-293`

**Issue:** `_validate_coverage_floor()` returns immediately when the output
does not already exist, before `_coverage_values(generated)` runs. A direct
reproduction published a first-time manifest containing `NaN` coverage even
though the new parser correctly rejects the same generated value when an old
manifest exists. A new or custom `--manifest-output` can therefore bypass all
strict number, finite/range, and required-field validation and establish an
invalid baseline.

**Fix:** Parse and validate the generated manifest unconditionally before the
missing-existing-file branch. Use strict JSON loading that rejects non-standard
constants, catch `OverflowError` from oversized JSON integers, and add
first-write tests for `NaN`, infinities, booleans, strings, missing fields, and
out-of-range values. Each failure must leave the destination absent.

### CR-03: Baseline publication does not protect the 1,129-test floor

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/tools/phase16_isolated_verify.py:228-307`

**Issue:** The publication preflight extracts and compares only coverage. The
tracked manifest records 1,129 collected and 1,129 passed tests at
`evidence/release-baseline.json:67-72`, but a reproduction replaced that
baseline with a generated 1/1-test manifest when its coverage values remained
96.21% / 94.57%. A subsequent read-only check then compares against the newly
lowered file, so the lost test inventory is normalized rather than blocked.

**Fix:** Parse the complete durable quality floor before replacement. Require
strict non-boolean integer counts, zero failures/errors, and generated
`collected`/`passed` values no lower than the existing manifest. Extend the
separately reviewed migration schema if intentional test-floor reductions are
allowed. Add destination-byte-preservation tests for lower, malformed,
negative, boolean, and inconsistent test counts.

### CR-04: Resolving the destination leaf follows an in-repository symlink

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/tools/phase16_isolated_verify.py:212-225`

**Issue:** `_manifest_output()` calls `.resolve()` on the complete output path.
Although an external symlink target is rejected by the root check, a symlink to
another file inside the repository is accepted and converted to that target
path. `_export_manifest_atomically()` then replaces the unrelated target while
leaving the requested manifest path as a symlink. A temporary-root
reproduction overwrote `victim.json` through
`evidence/release-baseline.json -> ../victim.json`. The unpredictable temporary
name fixes the old temporary-symlink attack but does not provide no-follow
semantics for the destination itself.

**Fix:** Resolve and validate the parent directory, not the destination leaf.
Use `lstat()` to reject an existing symlink (or atomically replace the lexical
symlink itself without reading through it), and keep validation and replacement
anchored to the same checked directory. Add in-root and out-of-root destination
symlink tests proving the victim bytes never change.

### CR-05: `quick_build()` still violates canonical state identity

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:643-667`

**Issue:** `quick_build()` converts every `State` supplied through `states=` to
only its name and then creates a new base `State`, discarding the caller's
identity and any subclass behavior. It also excludes the initial object with
`state_obj != initial_obj` instead of identity. With a supported initial
`State` subclass whose distinct instances compare equal, an asserted-pure
reproduction skipped the generated target state and failed construction with
`ValueError: target state 'b' is not registered`. This is the same identity
class of defect fixed in `FSMBuilder.build()`, and it contradicts the Phase 16
canonical-convenience-constructor contract.

**Fix:** Build the convenience registry from exact supplied objects. Preserve
each `State` in `states=`, create base states only for string endpoints that do
not yet have an object, reject different objects with the same name, and skip
only `state_obj is initial_obj`. Add pure and compiled tests for a callback or
custom state supplied via `states=`, an equal-comparing initial subclass, and
same-name identity conflicts.

## Warnings

### WR-01: Atomic replacement silently narrows repository file permissions

**Classification:** WARNING

**File:** `/Users/akriz/code/fast_fsm/tools/phase16_isolated_verify.py:332-345`

**Issue:** `NamedTemporaryFile` creates the temporary with mode `0600`, and
`os.replace()` transfers that mode to the destination. A reproduction starting
with a normal `0644` manifest ended with `0600`. The content is correct, but
other users and automation sharing the checkout can unexpectedly lose read
access after a successful baseline refresh.

**Fix:** Determine the intended final mode before publication and apply it to
the open temporary descriptor with `os.fchmod()` before the file `fsync` and
replace. Preserve an existing regular destination's mode; use an explicit
repository-file default that respects the process umask for a first write. Add
tests for existing and first-write permissions alongside cleanup assertions.

---

_Reviewed: 2026-08-30T17:03:33Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
