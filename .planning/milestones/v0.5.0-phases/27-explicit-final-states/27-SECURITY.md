---
phase: 27
slug: explicit-final-states
status: verified
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-16
---

# Phase 27 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Public State construction → compiled slotted State | Caller-controlled completion intent becomes immutable identity metadata. | Exact built-in `bool` |
| Canonical current State → termination query | Authoritative runtime identity becomes externally visible completion truth. | Derived boolean state |
| Public adapters → canonical registered States | Caller strings and State objects resolve to authoritative identities. | Transition endpoints and guards |
| Prepared request collection → live topology | Fully normalized requests become observable immutable slots and graph version. | Canonical transition entries |
| Caller dictionary → private machine candidate | Untrusted JSON-native topology becomes immutable State and transition metadata. | State names, final names, rows |
| Commit boundary → user callbacks and observers | Authoritative current State is visible to potentially failing or cancelling code. | Committed lifecycle state |
| Native build output → import resolution | Generated extensions may shadow pure source and alter validation mode. | Python/native module origin |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation and Evidence | Status |
|-----------|----------|-----------|----------|-------------|-------------------------|--------|
| T-27-01 | Tampering | `State.__init__` / `State.final` | high | mitigate | Exact built-in-bool validation, private immutable slot, pure/native tests, and PEP 561 bool surface in `core.pyi`. | closed |
| T-27-04 | Denial of Service | `StateMachine.is_terminated` | medium | mitigate | One direct `_current_state.final` read, guarded structurally in `tests/test_mypyc_guard.py`; no scan, cache, or allocation. | closed |
| T-27-07 | Spoofing | canonical State identity | low | accept | Current State is already canonical; registration/control rules own identity substitution and no authentication boundary exists. | closed |
| T-27-09 | Tampering | Phase Beads identity | medium | mitigate | Phase work uses the real claimed JSON identifier `fast_fsm-7xh`, retained through summaries and pending verification closure. | closed |
| T-27-02 | Tampering | canonical transition transaction | high | mitigate | Canonical sources resolve before the one final-source rejection; complete tuples prepare before publication, with rollback/retry tests. | closed |
| T-27-05 | Denial of Service | multi-source/emergency adapters | medium | mitigate | Finite supplied/registered source tuples are normalized once; dispatch performs no unrelated graph scan. | closed |
| T-27-06 | Information Disclosure | final-source errors | medium | mitigate | Fixed bounded error text omits caller-controlled State names; adapters add only established row context. | closed |
| T-27-08 | Tampering | builder and clone candidates | medium | mitigate | Private candidate construction publishes/caches only after the canonical transaction; repair/retry and topology isolation are tested. | closed |
| T-27-03 | Tampering | `from_dict` final-state metadata | high | mitigate | Exact list/item checks, count bound, set-backed duplicate/unknown rejection, private canonical construction, and atomic topology publication. | closed |
| T-27-10 | Denial of Service | `final_states` parsing | medium | mitigate | Count is rejected before item traversal and one set-backed linear pass validates names without graph scans. | closed |
| T-27-11 | Information Disclosure | dictionary validation errors | medium | mitigate | Fixed bounded field messages and established row indices avoid echoing arbitrary names or exception payloads. | closed |
| T-27-12 | Tampering | post-commit failure/cancellation | medium | mitigate | Current-State assignment remains authoritative; sync/async callback, observer, exception, and cancellation matrices prove no rollback. | closed |
| T-27-13 | Tampering | native source shadow | medium | mitigate | Native-origin assertion, exact-path recoverable relocation, pure-source verification, and final source-suite execution are enforced and evidenced. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-27-01 | T-27-07 | Canonical State identity is an internal integrity boundary governed by existing registration/control semantics, not an authentication boundary. | Phase 27 plan approval | 2026-09-15 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-16 | 13 | 13 | 0 | Codex orchestration audit (ASVS L1) |

The plan-time STRIDE register was complete, every mitigation or explicit accepted
risk had direct implementation/test evidence, and ASVS level 1 permits the
clean-register short circuit without a deeper specialist scan.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer).
- [x] Accepted risks are documented in the Accepted Risks Log.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-09-16
