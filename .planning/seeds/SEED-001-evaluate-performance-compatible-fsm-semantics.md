---
id: SEED-001
status: dormant
planted: 2026-09-11
planted_during: awaiting next milestone after v0.4.0
trigger_when: when relevant
scope: unknown
---

# SEED-001: Evaluate performance-compatible FSM semantics from `python-statemachine`

## Why This Matters

_To be filled in. Run `$gsd-capture --seed --enrich SEED-001` to add context._

## When to Surface

**Trigger:** when relevant

This seed will surface during `$gsd-new-milestone` when the milestone scope
matches.

## Scope Estimate

**Unknown** — run `$gsd-capture --seed --enrich SEED-001` to estimate effort.

## Breadcrumbs

- `.planning/research/python-statemachine-gap-assessment.md` — complete gap,
  architecture, usability, performance, and roadmap assessment.
- `.planning/quick/260911-ra8-implement-the-complete-condition-interfa/260911-ra8-SUMMARY.md`
  — condition-interface and transition-timing work already completed.
- `.planning/PROJECT.md` — core performance value, mypyc boundary, and existing
  out-of-scope decisions.
- `src/fast_fsm/core.py` — current flat-machine registration, resolution,
  lifecycle, and ownership implementation.
- `benchmarks/benchmark_py_fsm.py` and `uv.lock` — current competitor fixture and
  locked `python-statemachine` 2.5.0 baseline.

## Notes

The assessment recommends a possible next milestone around explicit final
states, internal-transition semantics, expected domain rejection, construction
and tooling parity, current competitor benchmarking, installed-artifact proof,
and a progressive drone tutorial. Bounded deferred events should remain a
separate later milestone candidate. Full hierarchical/parallel statecharts,
eventless stabilization, automatic sync/async dispatch, scheduler ownership,
and reflection-heavy callback injection are not recommended for the Fast FSM
core because they compromise its flat deterministic performance identity.

