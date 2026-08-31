---
phase: 16
fixed_at: 2026-08-31T12:16:26Z
review_path: .planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md
cycle: 4
iteration: 2
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-08-31T12:16:26Z
**Source review:** `.planning/phases/16-canonical-graph-dispatch-invariants/16-REVIEW.md`
**Cycle / iteration:** 4 / 2

**Summary:**

- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: Public type signatures reject the supported async callable-wrapper API

**Status:** Fixed: requires human verification
**Files modified:** `src/fast_fsm/__init__.py`, `src/fast_fsm/conditions.py`, `src/fast_fsm/core.py`, `tests/test_builder.py`, `tests/test_mypyc_guard.py`, `evidence/release-baseline.json`
**Commit:** `472833c`
**Applied fix:** Published `GuardResult = bool | Awaitable[bool]` and
`GuardCallable`, updated public wrappers and transition APIs to use the truthful
contract, and re-exported both aliases from `fast_fsm` and `fast_fsm.core`.
The downstream strict-mypy regression covers exact and inherited package/core
wrappers with an async callable object. Focused regressions also cover the
pre-core binding fallback and synchronous declarative rejection/closure of an
awaitable `Condition` result; the refreshed evidence records the resulting
coverage and inventory changes.

### WR-01: Architecture guide falsely claims every production instance is dictionary-free

**Files modified:** `docs/dev/architecture.md`
**Commit:** `f822dcf`
**Applied fix:** Replaced the absolute `__slots__` claim with the measured
slots-policy rule, named the two registered instance-dictionary exceptions,
and documented the audit command that is authoritative for maintainers.

### WR-02: ADR-003 describes the compiled condition seam as both absent and present

**Files modified:** `.specify/decisions/ADR-003-mypyc-compilation-boundary.md`, `.specify/memory/spr-core-api.md`
**Commit:** `2708964`
**Applied fix:** Distinguished the interpreted wrapper/predicate from its
compiled invocation bridge, removed unmeasured acceleration claims, and
recorded the remaining profiling-and-API decision accurately.

## Verification

Source, test, evidence, and documentation edits were made in the isolated
review-fix worktree. Origin-sensitive gates ran in fresh temporary exports:
pure mode asserted `src/fast_fsm/core.py`, while compiled mode rebuilt and
asserted a fresh native extension. Developer-checkout native shadows were not
imported or removed. The final suite completed before the fast-forward; no
source, test, evidence, or documentation file changed between that exit and
integration.

- Focused direct fallback, downstream strict-mypy, and synchronous
  awaitable-condition regressions: 3 passed (exit 0).
- Final `uv run python tools/phase16_isolated_verify.py --suite phase16`:
  exit 0. Fresh pure and compiled semantic matrices, the compiled
  trigger/history performance selection, source-origin checks, Ruff
  format/lint, mypy, the pure release gate, Sphinx HTML, three doctests, and
  read-only release evidence all passed.
- `task release-baseline-write`: exit 0 with 1,191/1,191 pure tests, 96.53%
  total source coverage, and 95.06% `core.py` coverage.
- `task release-baseline-check`: exit 0 with the same values.
- `task typecheck-mypy`: exit 0 with no issues. Advisory `task typecheck-ty`:
  exit 0 with no diagnostics.

This report is intentionally uncommitted; the review workflow owns its
documentation commit.

---

_Fixed: 2026-08-31T12:16:26Z_
_Fixer: gsd-code-fixer_
_Cycle / iteration: 4 / 2_
