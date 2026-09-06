---
phase: 18-safe-ownership-concurrency
plan: 03
subsystem: async-ownership
tags: [asyncio, contextvars, concurrency, cancellation, mypyc]
requires:
  - phase: 18-02
    provides: per-machine synchronous ownership and direct-control admission
provides:
  - Permanent event-loop binding for each AsyncStateMachine
  - Non-blocking same-loop task serialization with cancellation-safe release
  - Causal child-task reentry rejection and bound-loop sync-writer policy
affects: [18-04, 18-05, async-writers, ownership-evidence]
tech-stack:
  added: []
  patterns: [per-machine-asyncio-lock, contextvar-causal-root, short-admission-gate]
key-files:
  created: []
  modified:
    - src/fast_fsm/core.py
    - tests/test_ownership_concurrency.py
    - tests/test_async.py
    - tests/test_transition_lifecycle.py
    - .specify/memory/spr-core-api.md
decisions:
  - "Bind AsyncStateMachine permanently to the exact first async event loop and thread."
  - "Reject inherited causal roots before an async child can await its parent-owned lock."
  - "Keep synchronous callbacks inline and use no worker-thread offload."
actuals:
  tokens: 6527
  tasks: 2
  commits: 2
status: complete
---

# Phase 18 Plan 03: Async Ownership and Causal Reentry Summary

**Async machines now bind once to an event loop, serialize independent tasks without blocking it, and reject callback-created child reentry before it can deadlock.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-01T17:19:35-04:00
- **Completed:** 2026-09-01T17:22:38-04:00
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added slotted per-machine async locks, permanent loop/thread identity, and a short sync/async admission gate.
- Wrapped async lifecycle execution with cancellation-safe owner installation and `finally` release, preserving Phase 17 commit/history boundaries.
- Added a causal `ContextVar` root so same-machine child tasks fail before waiting, while nested work on another machine remains valid.
- Enforced bound-loop synchronous writer admission and proved synchronous callbacks stay on the loop thread.

## Task Commits

1. **Task 1: Bind one loop and serialize independent tasks without blocking it** — `af13c61` (`feat`)
2. **Task 2: Reject causal child reentry and enforce bound async-machine sync writes** — `bedcb31` (`feat`)

## Files Created/Modified

- `src/fast_fsm/core.py` — supplies loop binding, async ownership metadata, causal-root checks, and mixed writer admission.
- `tests/test_ownership_concurrency.py` — covers permanent loop binding, heartbeat progress, both cancellation windows, causal children, and mixed writers.
- `tests/test_async.py` — asserts synchronous callback thread identity remains inline.
- `tests/test_transition_lifecycle.py` — asserts async ownership metadata and lock state clear after cancellation.
- `.specify/memory/spr-core-api.md` — records the permanent-loop, causal-root, mixed-mode, and no-offload contracts.

## Decisions Made

- Loop identity is object-identity based and never silently rebinds after the original loop closes.
- Async task ownership is installed only after `asyncio.Lock` acquisition; a waiting cancellation cannot leave an owner marker.
- A causal root is distinct from task identity, so a callback-created child cannot wait behind the task it needs to resume.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Compatibility] Kept `ContextVar` module-qualified for the slots audit**

- **Found during:** Task 1 verification
- **Issue:** A direct `ContextVar` import appeared as a runtime export to the slots-policy audit.
- **Fix:** Referenced it through the `contextvars` module without changing the private ownership-root contract.
- **Files modified:** `src/fast_fsm/core.py`
- **Verification:** `slots-policy --json` passes.

## Verification

- `uv run ruff format` and `uv run ruff check` passed for all changed Python files.
- Asserted-pure focused ownership and lifecycle suites passed: 38 selected tests, including same-loop contention, cancellation, callback, causal-root, and mixed-writer cases.
- `task typecheck-mypy` passed with no issues.
- `uv run python tools/release_evidence.py slots-policy --json` passed.
- The structural no-offload check confirmed `ContextVar` is present and neither `to_thread()` nor `run_in_executor()` appears in `core.py`.

## Known Stubs

None.

## Self-Check: PASSED

- Required source, test, SPR, and summary files exist.
- Task commits `af13c61` and `bedcb31` exist in git history.

## Next Phase Readiness

Plan 18-04 can extend the established admission policy from transition and direct-control paths to every remaining public writer.
