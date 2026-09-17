---
phase: 28-same-state-transition-modes
reviewed: 2026-09-17T01:17:04Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - .github/copilot-instructions.md
  - .gitignore
  - .specify/memory/spr-core-api.md
  - .vscode/mcp.json
  - AGENTS.md
  - src/fast_fsm/core.py
  - src/fast_fsm/core.pyi
  - tests/test_builder.py
  - tests/test_graph_invariants.py
  - tests/test_hypothesis.py
  - tests/test_mypyc_guard.py
  - tests/test_priority_selection.py
  - tests/test_transition_modes.py
  - tests/test_transition_timing.py
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 28: Code Review Report

**Reviewed:** 2026-09-17T01:17:04Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

The Phase 28 implementation has a blocker in its canonical topology carrier: the new `internal` mode is mutable after registration even though mode is validated only while the transition is registered. A caller can therefore bypass the self-transition invariant and produce a successful result whose destination disagrees with the machine's actual state. The builder atomicity helpers also omit the new identity-bearing field, leaving this mode vulnerable to undetected staging/topology regressions.

The scoped test suite completed successfully with 6 skipped tests, but neither issue is covered by those tests.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Mutable transition mode bypasses canonical self-transition validation

**Classification:** BLOCKER

**File:** `/Users/akriz/code/fast_fsm/src/fast_fsm/core.py:632-665`

**Issue:** `TransitionEntry` is publicly exported and stores `internal` in an ordinary writable slot. Registration validates `internal=True` only for canonical self-targets, but the published entry can be mutated afterward. For example, changing an already registered `s -> t` entry to `entry.internal = True` makes `trigger()` take the internal commit path: it returns `success=True`, `internal=True`, and `to_state="t"`, while `current_state` remains `s`. This violates the finite topology, result/state coherence, and the phase's explicit immutable-mode/tamper-resistance contract. Every other identity field on the same carrier is writable as well, so replacing `to_state` or `priority` can similarly invalidate the validated plan after publication.

**Fix:** Make the canonical entry actually immutable at runtime and expose it as read-only in the stub. Preserve the existing identity-based equality/repr behavior if converting it to a dataclass, then add a regression that assignment raises and that a registered non-self edge cannot be converted into an internal edge.

```python
@dataclass(frozen=True, slots=True, eq=False, repr=False)
class TransitionEntry:
    to_state: "State"
    condition: Optional[Condition] = None
    priority: int = 0
    condition_ref: Optional[str] = None
    after: Optional[float] = None
    within: Optional[float] = None
    internal: bool = False
```

The equivalent manual slotted implementation is acceptable if mypyc constraints require it, provided every published field becomes runtime read-only.

## Warnings

### WR-01: Builder atomicity fingerprints omit the new identity-bearing mode

**Classification:** WARNING

**File:** `/Users/akriz/code/fast_fsm/tests/test_builder.py:123-161`

**Issue:** `_machine_topology_fingerprint()` records target, condition, and priority but not `entry.internal`; `builder_staging_fingerprint()` records every prior request field but not `request.internal`. These helpers are used broadly to assert that failed or repeated builder operations leave staging and published topology unchanged. A regression that replaces a request/entry with one whose only difference is mode would therefore satisfy the atomicity assertions even though Phase 28 defines mode as candidate identity and the machine's lifecycle behavior has changed.

**Fix:** Include the mode in both fingerprints and retain the existing failure/retry tests against internal requests.

```python
# _machine_topology_fingerprint
(id(entry.to_state), id(entry.condition), entry.priority, entry.internal)

# builder_staging_fingerprint
(
    request.trigger,
    request.sources,
    request.to_state,
    id(request.condition),
    request.priority,
    id(request.unless) if request.unless is not None else None,
    request.condition_ref,
    request.after,
    request.within,
    request.internal,
)
```

---

_Reviewed: 2026-09-17T01:17:04Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
