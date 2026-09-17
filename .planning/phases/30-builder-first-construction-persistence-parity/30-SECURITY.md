---
phase: 30-builder-first-construction-persistence-parity
audited_at: 2026-09-17
status: SECURED
threats_open: 0
controls_closed: 8
---

# Phase 30: Security Review

**Verdict:** SECURED

Phase 30's builder-first construction and persistence surfaces retain one
canonical validation/publication path, keep construction policy out of dispatch,
and bound the affected validation diagnostics without interpolating untrusted
trigger or source values.

## Threat Controls

| ID | Threat | Control and evidence | Status |
|----|--------|----------------------|--------|
| T-30-01 | Declarative metadata mutates after declaration | Frozen/slotted declaration records defensively copy plural sources; construction tests cover caller-list mutation. | Closed |
| T-30-02 | Declarative guard is evaluated twice or bypasses selection | Builder-derived rows carry topology only; state-owned handlers retain guard ownership and exactly-once counter coverage. | Closed |
| T-30-03 | Nested deprecated constructors multiply warnings | The four public compatibility boundaries warn once, then use private non-warning workers; warning attribution/count tests cover valid and invalid calls. | Closed |
| T-30-04 | Warning or validation diagnostics disclose caller payloads | Fixed warning text is payload-free. `from_dict()` legacy ambiguity now reports the transition row, and duplicate canonical sources report their source position. Hostile trigger/source tests assert that supplied secrets do not occur in either diagnostic. | Closed |
| T-30-05 | Malformed dictionary input partially publishes topology | Complete serialized rows are parsed into a request tuple and canonical publication happens once after validation; indexed malformed-input and atomicity tests cover the boundary. | Closed |
| T-30-06 | Clone aliases mutable topology or callback containers | Clone replays canonical requests while rebuilding mutable containers; identity/isolation tests cover sync and async machines. | Closed |
| T-30-07 | An adapter weakens final/internal validation | Direct, batch, builder, declarative, helper, clone, and dictionary paths are compared by the construction parity oracle and structural transaction checks. | Closed |
| T-30-08 | Construction policy enters the dispatch hot path | Structural source-region checks exclude construction/import/warning work from selector, lifecycle, and trigger regions; Phase 30 native closure retained the singleton throughput gate. | Closed |

## T-30-04 Remediation

The repair replaces the two caller-data interpolations identified in the audit:

- `from_dict()` reports `transition[index]` for an ambiguous legacy condition
  key, without emitting the trigger value.
- Canonical duplicate-source validation reports `source index` within the
  request, without emitting the source name or representation.

`tests/test_advanced_functionality.py` asserts the fixed bounded wording and
uses hostile trigger and source markers to prove neither appears in the raised
message. The existing transition row context, exception classes, full-document
validation, and canonical adapter transaction are unchanged.

## Verification

Executed after the remediation in the shared milestone checkout:

- `uv run pytest tests/test_advanced_functionality.py -x -q -k "from_dict or duplicate_source or legacy_trigger_guard"` — 16 passed.
- `uv run pytest tests/test_construction_parity.py -x -q` — 11 passed.
- `uv run pytest tests/test_graph_invariants.py tests/test_mypyc_guard.py -x -q -k "construction or persistence or adapter or canonical"` — 20 passed (one expected compatibility deprecation warning).
- `uv run ruff format --check src/fast_fsm/core.py tests/test_advanced_functionality.py` — passed.
- `uv run ruff check src/fast_fsm/core.py tests/test_advanced_functionality.py` — passed.
- `uv run mypy src/fast_fsm/` — passed with no issues.

The already-recorded Phase 30 validation closure supplies the broader pure/native,
documentation, slots, throughput, and full-suite evidence; this audit change is
limited to bounded validation diagnostics and their regression coverage.

## Accepted Risks Log

| ID | Severity | Accepted risk | Rationale and control |
|----|----------|---------------|-----------------------|
| T-30-SC | Low | Supply-chain inputs remain an environmental release risk. | No runtime dependency was added. `uv.lock` and normal build inputs remain authoritative; comparator dependencies stay isolated outside ordinary installation. Installed-artifact inventory requires `src/fast_fsm/_construction_compat.py`, preventing that compatibility boundary from being omitted from release artifacts. |

## Conclusion

All eight Phase 30 threat controls are closed. No open security threat remains
for the phase (`threats_open: 0`).
