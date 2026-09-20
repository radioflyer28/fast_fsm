---
phase: 31-semantic-diagnostics-visualization
audited_at: 2026-09-19
status: SECURED
threats_open: 0
controls_closed: 9
asvs_level: 1
register_authored_at_plan_time: true
---

# Phase 31: Security Review

**Verdict:** SECURED. The nine planned threat controls have implementation and automated evidence; three low-severity risks remain explicitly accepted within the documented caller-owned diagnostic boundary.

## Trust Boundaries

| Boundary | Data crossing | Control |
|----------|---------------|---------|
| Mutable FSM → cold diagnostic capture | State names, final flags, ordered transition facts | One owned scalar snapshot before validation, JSON, or diagram traversal |
| Caller text → JSON, Mermaid, PlantUML, Markdown | Names, trigger labels, guard descriptions | JSON encoding or sink-specific escaping with opaque diagram IDs and shared output limits |
| Runtime attempt → TRACE | Priority, mode, rejection code, current finality | Fixed metadata-only fields, bounded code validation, safe redaction and nullable failure fallback |
| Generated native artifacts → source checkout | Import origin and conformance evidence | Exact origin assertions and path-constrained, recoverable shadow relocation |

## Threat Register

| ID | Severity | Disposition | Control and evidence | Status |
|----|----------|-------------|----------------------|--------|
| T-31-01 | Medium | Mitigate | `_GraphSnapshot` captures final flags and edge mode once; JSON, validator, and both renderers project from that graph. Late mutation and cross-surface tests in `test_diagnostic_contracts.py`, `test_validation.py`, and `test_mypyc_guard.py` pass in pure and native modes. | Closed |
| T-31-02 | Medium | Mitigate | Diagram renderers use opaque IDs and language-specific escaping; hostile-name and hostile-label assertions in `test_visualization.py` and `test_output_safety.py` pass in both origins. | Closed |
| T-31-03 | Medium | Mitigate | One diagnostic ledger reserves graph work and output before emission; exact and one-less budget tests for JSON, validation, Mermaid, PlantUML, and composed output pass in both origins. | Closed |
| T-31-04 | High | Mitigate | TRACE emits fixed scalar metadata only, validates rejection codes, and preserves the result if finality getter inspection fails. Hostile payload, sync/async, redactor-failure, disabled-path, and subclass-getter tests in `test_logging_config.py` pass in both origins. | Closed |
| T-31-05 | Low | Accept | JSON is an explicit serialization of the caller's own named machine; the new fields add only finite final/mode facts, not attempt payload or exception text. | Closed — accepted |
| T-31-06 | Low | Accept | Legacy `dead_states` and `terminal` remain topology terms. New explicit-final and non-final-sink fields avoid silently changing their meaning; validation and JSON compatibility tests cover the distinction. | Closed — accepted |
| T-31-07 | Medium | Mitigate | TRACE redactor output is validated; failure uses fixed null-semantic fallback or suppression, with no raw exception/payload fallback. Exact-key and hostile-text tests pass. | Closed |
| T-31-08 | Low | Accept | Disabled TRACE checks enablement before projecting semantic fields at the caller, and the helper returns before reading result/state. Structural and behavioral tests protect this path; the full suite retains the installed compiled throughput floor. | Closed — accepted |
| T-31-09 | Medium | Mitigate | Pure and fresh native exact module origins were asserted for the same focused matrix. Only validated `core`/`core__mypyc` extension shadows were recoverably relocated, and pure source origin was reasserted before the passing full suite. | Closed |

## Accepted Risks Log

| ID | Rationale | Accepted basis | Date |
|----|-----------|----------------|------|
| T-31-05 | Caller-requested JSON contains caller-owned machine labels; no new secret attempt fields are serialized. | Phase 31 plan disposition | 2026-09-19 |
| T-31-06 | Old topology keys stay stable for compatibility; explicit new fields prevent ambiguity. | Phase 31 plan disposition | 2026-09-19 |
| T-31-08 | Disabled TRACE retains a logger-level check but no semantic projection; throughput floor passes. | Phase 31 plan disposition | 2026-09-19 |

## Security Audit Trail

| Audit date | Threats total | Closed | Open | Method |
|------------|---------------|--------|------|--------|
| 2026-09-19 | 9 | 9 | 0 | ASVS L1 planned-register inspection with pure/native test and review evidence |

## Sign-Off

- [x] All planned threats have a disposition.
- [x] Accepted risks are documented.
- [x] `threats_open: 0` is confirmed.
- [x] Status is `SECURED`.

**Approval:** verified 2026-09-19.
