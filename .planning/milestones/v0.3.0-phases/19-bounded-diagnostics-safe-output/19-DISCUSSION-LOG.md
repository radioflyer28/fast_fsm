# Phase 19: Bounded Diagnostics & Safe Output - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-09-02
**Phase:** 19-bounded-diagnostics-safe-output
**Mode:** `--auto` using the user's standing instruction to choose recommended answers
**Areas discussed:** Snapshot identity, deterministic budgets, graph semantics, grammar-safe output, logging ownership

---

## Snapshot Identity and Duplicate Names

| Option | Description | Selected |
|--------|-------------|----------|
| One snapshot + positional identity | Capture once per top-level call; preserve duplicate names using stable input positions | ✓ |
| Re-read live topology | Let each nested helper inspect the machine independently | |
| Reject duplicate names | Require unique machine display names in comparisons | |

**Choice:** One snapshot plus positional identity (recommended default).
**Notes:** Empty comparison returns a structured empty result with undefined numeric aggregates represented as `None`.

## Deterministic Budget Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Finite counted-work budget | Use deterministic operation/result limits with explicit incomplete metadata or a documented exception | ✓ |
| Wall-clock timeout | Stop analysis after elapsed time | |
| Caller-only limits | Remain unbounded unless every caller supplies a limit | |

**Choice:** Finite deterministic counted-work budgets (recommended default).
**Notes:** Existing return types may use a stable redacted budget exception where partial metadata cannot be added compatibly. Dense allocation is opt-in and preflight-budgeted.

## Cycle and Longest-Path Meaning

| Option | Description | Selected |
|--------|-------------|----------|
| SCC membership + condensation depth | Report every cyclic member and compute memoized structural depth on the condensed DAG | ✓ |
| Enumerate simple paths | Search every acyclic path through the original graph | |
| Back-edge endpoints only | Report only nodes directly touching a DFS back edge | |

**Choice:** SCC membership and condensation-DAG depth (recommended default).
**Notes:** This gives complete cycle membership and bounded deterministic complexity without promising the NP-hard exact longest simple path in cyclic graphs.

## Mermaid and PlantUML Encoding

| Option | Description | Selected |
|--------|-------------|----------|
| Opaque IDs + separate grammar escapers | Allocate collision-free IDs and encode labels independently for each grammar | ✓ |
| Sanitized names as IDs | Continue deriving identifiers by replacing punctuation | |
| One shared generic escape | Apply the same replacements to both output grammars | |

**Choice:** Opaque IDs with grammar-specific escaping (recommended default).
**Notes:** User text remains inert across names, triggers, conditions, titles, control characters, comments, directives, and fences.

## Trace Redaction and Handler Ownership

| Option | Description | Selected |
|--------|-------------|----------|
| Metadata-only + reversible owned handler | Redact values by default, fail closed on redactor errors, preserve app handlers, restore only library changes | ✓ |
| Clear and replace handlers | Keep the current global logger reset behavior | |
| Raw trace with opt-out | Emit payloads unless the caller installs a filter | |

**Choice:** Metadata-only trace plus reversible library-owned configuration (recommended default).
**Notes:** Repeated configuration replaces only the library-owned handler; propagation is explicit; `set_fsm_logging_level()` uses the same seam.

## the agent's Discretion

- Exact private/public helper names and slot-backed record shapes.
- Exact finite default budget values after deterministic adversarial calibration.
- Exact escaping tables and SCC implementation details.

## Deferred Ideas

- Public versioned topology snapshots, installed-artifact release proof, interactive diagram tooling, and external logging backends remain outside Phase 19.
