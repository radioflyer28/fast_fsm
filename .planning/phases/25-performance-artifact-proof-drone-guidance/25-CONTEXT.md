# Phase 25: Performance, Artifact Proof & Drone Guidance - Context

**Gathered:** 2026-09-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove and document the completed priority-aware FSM as users consume it: truthful
complexity/benchmark guidance, equivalent clean source and installed pure/native
artifacts, and a runnable drone-controller example. Do not change priority
registration, selection, construction, or diagnostic semantics.
</domain>

<decisions>
## Implementation Decisions

### Truthful complexity and artifacts
- **D-01:** Documentation and benchmarks state O(1) source/trigger lookup and
  direct singleton dispatch; finite candidate-group mutation and ordered
  selection are local O(k), with no dispatch-time sort or unrelated graph scan.
- **D-02:** Conformance uses clean source, pure-wheel, and compiled-wheel
  origins to prove the same priority winner, guard evaluation order,
  result/history metadata, exhaustion, exceptions, and cancellation; compiled
  singleton dispatch retains the existing 200,000 ops/sec gate.

### Drone controller composition
- **D-03:** The example owns `TelemetryPolicy`, the FSM, and an `AircraftCommands`
  adapter in a `DroneController`; bound FSM callbacks command the aircraft.
  `SimulatedAircraft` remains replaceable hardware, not an FSM subclass.
- **D-04:** One `telemetry_tick` enters the controller-owned FSM. Guards encode
  fail-safe precedence; telemetry exposes facts such as heartbeat age and does
  not choose events, transitions, states, or commands. — **Reversibility: costly**
  — external dispatch would duplicate and undermine the finite transition model.

### the agent's Discretion
- Select benchmark group depths/winner positions and exact example module/doc
  organization consistent with existing test, artifact, and documentation tools.
</decisions>

<canonical_refs>
## Canonical References
- `.planning/ROADMAP.md` §Phase 25 — goal and five success criteria.
- `.planning/REQUIREMENTS.md` §Performance and Documentation — PERF-01,
  PERF-02, DOC-01.
- `.planning/PROJECT.md` §Constraints — core performance and mypyc boundary.
- `.specify/decisions/ADR-007-priority-topology.md` — O(1) singleton/local O(k)
  candidate contract.
- `.planning/phases/22-ordered-runtime-selection-lifecycle-integration/22-VERIFICATION.md`
  — order, result/history, exhaustion, exception, and cancellation semantics.
- `.planning/phases/23-construction-declarative-serialization-parity/23-VERIFICATION.md`
  — construction and callback boundaries.
- `.planning/phases/24-candidate-aware-diagnostics-output/24-VERIFICATION.md`
  — completed priority topology projection.
</canonical_refs>

<code_context>
## Existing Code Insights
- `tests/test_performance_benchmarks.py`, `tools/release_evidence.py`, and
  installed-artifact conformance are the existing evidence seams.
- `examples/` and documentation are the user-facing guidance seams.
- `StateMachine`/`AsyncStateMachine` already own ordered candidate selection;
  the example must call one FSM event rather than reproduce priority branching.
</code_context>

<specifics>
## Specific Ideas

The drone’s critical fault, link loss, and low battery are competing guarded
`telemetry_tick` candidates; the selected transition invokes a simulated
aircraft command such as return-to-home through a bound callback.
</specifics>

<deferred>
## Deferred Ideas

Dynamic priorities, automatic telemetry classifiers, schedulers, parallel
guards, and runtime candidate mutation remain out of scope.
</deferred>
