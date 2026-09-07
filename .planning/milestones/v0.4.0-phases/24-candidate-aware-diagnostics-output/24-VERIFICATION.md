---
phase: 24-candidate-aware-diagnostics-output
verified: 2026-09-07T04:44:38Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 8/8
  gaps_closed: []
  gaps_remaining: []
  regressions: []
decision_coverage:
  honored: 4
  total: 4
  not_honored: []
---

# Phase 24: Candidate-Aware Diagnostics & Output Verification Report

**Phase Goal:** Diagnostics and structured or human-readable outputs represent each transition candidate exactly once in deterministic priority order under existing safety budgets.

**Verified:** 2026-09-07T04:44:38Z  
**Status:** passed  
**Re-verification:** Yes — after summary-only UAT metadata correction (`5d766a6`)

## Re-verification Scope

`5d766a6` changes only `24-02-SUMMARY.md`, replacing the UAT coverage kind
`boundary` with `integration`. `git diff --name-only 28f45d1..5d766a6 -- src tests`
is empty. The correction has no implementation or test surface to re-execute.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Validation accepts strictly ordered candidate groups, rejects equal/descending/Boolean/non-integer priorities, and distinguishes proved from possible shadowing without executing policy. | ✓ VERIFIED | Core captures only `entry.condition is None and type(source_state) is State`; `validation.py` scans scalar edges with exact-int validation. Pure malformed/shadow tests and the pure/native semantic oracle pass. |
| 2 | JSON, Mermaid, PlantUML, both Markdown forms, sparse/dense adjacency, transition matrices, and paths preserve each candidate and numeric priority in canonical order, including repeated targets. | ✓ VERIFIED | `_diagnostics.py` projects one `_DiagnosticEdge` per snapshot row and carries priority through adjacency/path records; output tests exercise same-target candidates and hostile labels in every sink. |
| 3 | Traversal, candidate records, rendered edges, findings, and paths charge the existing budget per candidate; a one-less capacity fails explicitly instead of appearing complete. | ✓ VERIFIED | The shared ledger reserves before exposing work/results. Budget test and cross-mode oracle assert fixed `diagnostic budget exhausted` plus incomplete status. |
| 4 | Each diagnostic result derives from one immutable snapshot and no diagnostic consumer reads live singleton/group runtime storage. | ✓ VERIFIED | `_graph_from_snapshot()` copies only `snapshot.transitions` in order; diagnostic modules have no `_transitions` or `_states` access. One-capture and structural tests pass. |
| 5 | Candidate validation findings retain source, event, target, candidate priority, and shadowing priority in source/trigger/priority order. | ✓ VERIFIED | Ordered validation emits scalar candidate findings; malformed/shadow tests assert exact records and enhanced-validator severity. |
| 6 | Pure and native core produce equivalent snapshot facts, diagnostics, budget failure, callback payload, and history priority. | ✓ VERIFIED | The pure oracle and identical tests against a temporary package containing preserved Phase 24 `core*.so` pass; native `find_spec` origin ends in `.so`. |
| 7 | The sole compiled-core boundary, frozen/slotted records, escaping, selector/callback behavior, and package boundary remain intact. | ✓ VERIFIED | Structural guard verifies record layouts and cold boundary; the oracle proves caller-owned callback kwargs and selected/history priority. Ruff and slots policy pass. |
| 8 | The living SPR documents snapshot, strict/shadow, output, and budget rules without absorbing Phase 25 performance, artifact, public-documentation, or drone scope. | ✓ VERIFIED | `spr-core-api.md` records the private diagnostic contract; the re-verification revision is summary-only. |

**Score:** 8/8 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/fast_fsm/core.py` | Frozen candidate rows and static evidence | ✓ VERIFIED | Frozen/slotted `_GraphTransition` retains exact priority and `statically_unconditional`. |
| `src/fast_fsm/_diagnostics.py` | Scalar candidate graph and shared ledger | ✓ VERIFIED | Frozen/slotted `_DiagnosticEdge`, tuple graph, candidate-aware adapters, and reserve-before-work/results. |
| `src/fast_fsm/validation.py` | Strict priority and conservative shadow analysis | ✓ VERIFIED | Contiguous scalar-group scan emits malformed/proved/possible results without executing policy. |
| `src/fast_fsm/visualization.py` | Candidate-complete, escaped output sinks | ✓ VERIFIED | JSON, Mermaid, PlantUML, and Markdown consume captured scalar rows with numeric priority. |
| Phase 24 test files | Behavior and parity proof | ✓ VERIFIED | All named phase tests active and passed; Phase 24 oracle ran in both source and native-core modes. |
| `.specify/memory/spr-core-api.md` | Living maintainer contract | ✓ VERIFIED | Records private projection, strict shadowing, output shapes, and candidate-level budgets. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `_graph_snapshot_owned()` | `_graph_from_snapshot()` | one immutable row → one scalar edge | ✓ WIRED | Core emits priority/static evidence; scalar projection consumes every snapshot row in tuple order. |
| `_DiagnosticGraph.edges` | `FSMValidator.check_determinism()` | contiguous source/trigger scan | ✓ WIRED | Validator iterates scalar edges and retains priority/shadowing identity. |
| `check_determinism()` | `EnhancedFSMValidator._analyze_determinism()` | finding-to-severity mapping | ✓ WIRED | Error, warning, and info map priority errors, proved shadows, and possible shadows. |
| `_DiagnosticGraph.edges` | adjacency/path/rendering | candidate record/reservation | ✓ WIRED | All adapters and sinks iterate scalar edges and preserve numeric priority. |
| compiled `_GraphTransition` | interpreted `_DiagnosticEdge` | same snapshot projection | ✓ WIRED | Native semantic oracle passes through the real public diagnostic path. |
| SPR | implementation | maintainer contract | ✓ WIRED | Current SPR matches snapshot, validation, renderer, and ledger seams. |

### Data-Flow Trace

Not applicable to this in-process library. The relevant topology flow is
canonical runtime topology → immutable `_GraphSnapshot` → scalar
`_DiagnosticGraph` → validators/adapters/renderers.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Clean pure-source origin | `UV_CACHE_DIR=/private/tmp/fast-fsm-phase23-uv-cache task pure-source-check` | `core_origin: src/fast_fsm/core.py` | ✓ PASS |
| All Phase 24 behavior truths | Nine named tests from the Phase 24 test files | 13 passed (including parametrized malformed priorities) | ✓ PASS |
| Native diagnostic parity | Preserved `core*.so` in temporary package; two named Phase 24 structural/oracle tests | 2 passed; native origin printed | ✓ PASS |
| Static quality/layout | Ruff and `slots-policy --json` | Both passed; exactly three registered exceptions | ✓ PASS |

### Probe Execution

No Phase 24 probe scripts are declared or discovered.

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| DIAG-01 | 24-01, 24-03 | Strict determinism, malformed-priority rejection, and conservative shadowing. | ✓ SATISFIED | Scalar validation behavior, no-user-policy guard, and pure/native semantic oracle. |
| DIAG-02 | 24-02, 24-03 | Candidate-complete priority output, adjacency, paths, escaping, and budgets. | ✓ SATISFIED | Candidate adapters, all output sinks, one-less budget test, and pure/native oracle. |

Both Phase 24 requirements are claimed by plans; no orphaned Phase 24 requirement exists.

### Decision Coverage

`check.decision-coverage-verify` reports all 4/4 trackable CONTEXT decisions honored.

### Test Quality Audit

| Test File | Linked Requirement | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/test_validation.py`, `tests/test_graph_invariants.py` | DIAG-01 | Yes | No linked skips | No | Behavioral/value | PASS |
| `tests/test_diagnostic_contracts.py`, `tests/test_visualization.py` | DIAG-02 | Yes | No linked skips | No | Behavioral/value | PASS |
| `tests/test_mypyc_guard.py` | DIAG-01, DIAG-02 | Yes | No linked skips | No | Structural + real-machine parity | PASS |

The two skip calls in `test_mypyc_guard.py` are unrelated platform/compiled-only
guards; the Phase 24 oracle did run in both selected configurations. No circular
expected-output generator or weak assertion was found in Phase 24 evidence.

## Anti-Patterns Found

No Phase 24 debt markers, placeholders, implementation stubs, live diagnostic
storage reads, or Phase 25 scope changes were found. The generic key-link query
cannot resolve planned component names as file paths; manual source tracing above
is the authoritative wiring evidence.

## Human Verification Required

N/A — infrastructure/foundation phase with no user-facing elements. Every
ordering, budget, and native-boundary invariant has executable evidence.

## Gaps Summary

**No gaps found.** Phase 24 remains complete after the UAT metadata-only correction.

---

_Verified: 2026-09-07T04:44:38Z_  
_Verifier: the agent (gsd-verifier)_
