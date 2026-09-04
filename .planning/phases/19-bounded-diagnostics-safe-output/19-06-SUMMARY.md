---
phase: 19-bounded-diagnostics-safe-output
plan: "06"
subsystem: visualization
tags: [diagnostics, visualization, mermaid, plantuml, markdown, json, snapshot, budgets]
requires:
  - phase: 19-02
    provides: hostile output corpus and one-snapshot renderer contracts
  - phase: 19-04
    provides: structured snapshot-backed validation analysis and diagnostic status records
provides:
  - opaque snapshot-position IDs and grammar-specific diagram encoders
  - one-capture JSON, fenced, and Markdown rendering adapters with one shared budget
  - sparse-default structured JSON and preflighted dense adjacency compatibility
affects: [19-08, visualization, validation, release-verification]
actuals:
  tokens: 11839
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - private from-snapshot output composition with one shared diagnostic ledger
    - target-specific final-sink allowlist encoders for diagram and Markdown grammar
    - dense compatibility validation without implicit dense allocation
key-files:
  created: []
  modified:
    - src/fast_fsm/visualization.py
    - tests/test_output_safety.py
    - tests/test_visualization.py
    - tests/test_diagnostic_contracts.py
    - .specify/memory/spr-visualization.md
key-decisions:
  - "Diagram identity is always s{snapshot_position}; labels are escaped display data only."
  - "JSON, fenced, and document APIs capture once and compose from the same graph and budget rather than calling public helpers."
  - "Dense adjacency is opt-in or must fully equal the captured graph; mismatches use one fixed redacted error."
patterns-established:
  - "Public rendering controls remain additive keyword-only arguments, including limits and dense opt-in."
  - "Output ordering follows immutable snapshot state and edge order; no output helper rereads live topology."
requirements-completed: [DIAG-01, DIAG-04, DIAG-05, DIAG-06, DIAG-07, DIAG-08, OUT-01, OUT-02]
coverage:
  - id: D1
    description: Mermaid and PlantUML use deterministic opaque IDs with inert caller text and one snapshot per render.
    requirement: OUT-01
    verification:
      - kind: integration
        ref: uv run pytest tests/test_output_safety.py tests/test_visualization.py -x -q -k 'opaque or mermaid or plantuml or escape or hostile or stable or snapshot'
        status: pass
    human_judgment: false
  - id: D2
    description: JSON, fenced, and Markdown output share one bounded snapshot with sparse analysis and safe dense compatibility.
    requirement: DIAG-08
    verification:
      - kind: integration
        ref: uv run pytest tests/test_output_safety.py tests/test_visualization.py tests/test_diagnostic_contracts.py -x -q
        status: pass
    human_judgment: false
metrics:
  duration: 13min
  completed: 2026-09-03
  tasks: 2
  files: 5
status: complete
---

# Phase 19 Plan 06: Bounded Diagnostic Visualization Summary

**Opaque snapshot-order diagrams plus one-capture sparse JSON and Markdown output with deterministic grammar-safe text and explicit dense compatibility.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-03T20:28:35-04:00
- **Completed:** 2026-09-03T20:41:47-04:00
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Replaced label-derived Mermaid and PlantUML identity with deterministic `s0`, `s1`, … snapshot-position IDs, and encoded every caller-controlled sink with grammar-specific one-line encoders.
- Added private from-snapshot composition for Mermaid fences, Markdown documents, and JSON so each public output API captures exactly once and shares its graph and budget.
- Published snapshot-ordered sparse topology, declared initial/current separation, SCC/depth/status analysis, opt-in dense adjacency, and fixed stale-matrix rejection.

## Task Commits

1. **Task 1 RED: opaque diagram contracts** — `1af71a2` (test)
2. **Task 1: encode Mermaid and PlantUML with opaque snapshot-order IDs** — `5e0f37a` (feat)
3. **Task 2 RED: snapshot output contracts** — `1695a2f` (test)
4. **Task 2: share one bounded snapshot across JSON, fenced, and Markdown output** — `8705d7e` (feat)

## Files Created/Modified

- `src/fast_fsm/visualization.py` — opaque diagram renderers, target-specific encoders, structured JSON, private fenced/document composition, and dense matrix validation.
- `tests/test_output_safety.py` — hostile rendering, private-composition, sparse JSON, dense preflight, and stale-input coverage.
- `tests/test_visualization.py` — intentional opaque-ID output migration and fixed empty-matrix compatibility expectation.
- `tests/test_diagnostic_contracts.py` — activated the assigned one-snapshot JSON status contract.
- `.specify/memory/spr-visualization.md` — living output, encoding, status, and dense compatibility contract.

## Decisions Made

- Allocate renderer IDs only from immutable snapshot position; caller labels are never identities.
- Keep each output grammar at an independent final-sink encoding boundary instead of introducing a generic sanitizer.
- Preserve existing callable names while adding keyword-only `limits` and explicit `include_adjacency` controls.

## TDD Gate Compliance

- Task 1 recorded RED (`1af71a2`) before GREEN (`5e0f37a`).
- Task 2 recorded RED (`1695a2f`) before GREEN (`8705d7e`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test contract] Corrected hostile-output assertions that conflicted with fixed grammar syntax**
- **Found during:** Task 1
- **Issue:** The corpus treated PlantUML's required outer `@startuml`/`@enduml` delimiters as injected caller text, and its opaque-ID alias regex escaped its own word boundary.
- **Fix:** Asserted exactly one fixed delimiter and repaired the regex while retaining hostile-text containment coverage.
- **Files modified:** `tests/test_output_safety.py`
- **Verification:** Focused Mermaid/PlantUML hostile and collision tests passed.
- **Committed in:** `5e0f37a`

**2. [Rule 1 - Compatibility contract] Rejected empty supplied adjacency data instead of silently rendering it**
- **Found during:** Task 2
- **Issue:** The legacy empty-dict test contradicted the required full-equivalence stale-matrix rule.
- **Fix:** Migrated the test to assert the fixed `adjacency matrix does not match captured snapshot` error.
- **Files modified:** `tests/test_visualization.py`
- **Verification:** Output/visualization/diagnostic tests and the full suite passed.
- **Committed in:** `8705d7e`

### Authorized Scope Correction

**3. [Plan file omission] Activated the assigned JSON strict-RED contract outside `files_modified`**
- **Found during:** Task 2
- **Issue:** `tests/test_diagnostic_contracts.py` contained the sole remaining `RED until 19-06` JSON contract but was omitted from Plan 19-06's declared file list.
- **Resolution:** The executor received explicit narrow authorization to add this file solely to remove the marker and align it with the shipped `diagnostic_status` JSON schema.
- **Files modified:** `tests/test_diagnostic_contracts.py`
- **Verification:** Focused diagnostic/output tests and the full suite passed.
- **Committed in:** `8705d7e`

---

**Total deviations:** 2 Rule 1 test-contract fixes and 1 authorized plan-file omission correction.
**Impact on plan:** All changes enforce the planned safe-output contract; no runtime dependency, public renderer name, or unrelated project artifact changed.

## Verification

- `uv run pytest tests/test_output_safety.py tests/test_visualization.py tests/test_diagnostic_contracts.py -x -q` — passed.
- `uv run pytest tests/ -x -q` — passed.
- `uv run ruff format --check ...` and `uv run ruff check ...` — passed.
- `FAST_FSM_BUILD_MODE=pure uv run mypy src/fast_fsm/` and `task typecheck-ty` — passed.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 19-08 can consume the finalized renderer, JSON, and dense-output contracts in its isolated Phase 19 verification suite.

## Self-Check: PASSED

- All five modified implementation/test/memory files and this summary exist.
- TDD RED/GREEN commits `1af71a2`, `5e0f37a`, `1695a2f`, and `8705d7e` exist in history.

---
*Phase: 19-bounded-diagnostics-safe-output*
*Completed: 2026-09-03*
