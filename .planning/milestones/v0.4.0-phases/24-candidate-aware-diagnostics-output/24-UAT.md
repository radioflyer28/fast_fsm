---
status: complete
phase: 24-candidate-aware-diagnostics-output
source: 24-01-SUMMARY.md, 24-02-SUMMARY.md, 24-03-SUMMARY.md
started: 2026-09-07T00:00:00Z
updated: 2026-09-07T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Immutable priority-aware diagnostic projection
expected: A single immutable snapshot preserves each candidate's priority, guard presence, and narrow static-unconditional evidence without evaluating user policy.
result: pass
source: automated
coverage_id: 24-01/D1

### 2. Strict priority and conservative shadow validation
expected: Strict candidate priority groups are deterministic while malformed groups and proved versus possible shadows remain distinct, ordered, and side-effect free.
result: pass
source: automated
coverage_id: 24-01/D2

### 3. Candidate-complete graph analysis
expected: Sparse/dense adjacency, matrices, counts, and generated paths retain every candidate, including same-target candidates, in priority order.
result: pass
source: automated
coverage_id: 24-02/D1

### 4. Candidate-complete rendered output
expected: JSON, Mermaid, PlantUML, and Markdown preserve numeric priority and multiplicity under existing escaping rules.
result: pass
source: automated
coverage_id: 24-02/D2

### 5. Candidate-sized output budgets
expected: Each JSON candidate record charges the existing result budget and exhaustion remains explicit.
result: pass
source: automated
coverage_id: 24-02/D3

### 6. Pure/native diagnostic parity
expected: Candidate-aware diagnostic projection and output behavior agree in clean pure and freshly compiled core modes.
result: pass
source: automated
coverage_id: 24-03/D1, 24-03/D2

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]

## Automated Verification Note

All acceptance entries were automated and passing. Independent Phase 24 verification confirms all eight goal truths, satisfies DIAG-01 and DIAG-02, and requires no human verification.
