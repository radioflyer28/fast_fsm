# Phase 23: Construction, Declarative & Serialization Parity - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-07
**Phase:** 23-Construction, Declarative & Serialization Parity
**Areas discussed:** construction parity, declarative handler identity, serialized guard references, read/clone semantics

---

## Autonomous decision record

The previously authorized `--auto` workflow selected the conservative,
compatibility-preserving option for each area:

| Area | Options considered | Selected |
|---|---|---|
| Construction parity | Adapter-specific candidate storage; replay through canonical registrar | Replay through canonical registrar ✓ |
| Declarative identity | One trigger-wide handler; candidate-specific handler metadata | Candidate-specific metadata ✓ |
| Serialized guards | Serialize callables; opaque references with external bindings | Opaque references with external bindings ✓ |
| Legacy ambiguity | Reuse a trigger-wide guard; fail explicitly | Fail explicitly ✓ |
| Read/clone behavior | Collapse groups; preserve all candidate identity | Preserve all candidate identity ✓ |

**Notes:** These choices carry forward the user's settled design: priority is
an ordinary transition attribute, ordered selection belongs to the FSM, and
application callbacks/telemetry data must not become an external priority
dispatcher. No new capability was added beyond PAR-01 through PAR-03.

## the agent's Discretion

Private helper names, row typing, schema field spelling, and focused test
placement are left to research/planning, subject to the locked public behavior.

## Deferred Ideas

None.
