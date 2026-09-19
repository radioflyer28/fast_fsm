# Phase 32: Performance, Artifact & Progressive Guidance Proof - Context

**Gathered:** 2026-09-19
**Status:** Ready for planning
**Mode:** Carry-forward of approved milestone scope and earlier user decisions under the active milestone-completion goal; no new product choice was required

<domain>
## Phase Boundary

Close v0.5.0's performance, installed-artifact, and user-guidance proof. Measure and preserve the direct compiled singleton fast path; publish environment-labelled, scenario-separated costs of the new flat-FSM semantics; run one fixed semantic oracle across source, native, installed-wheel, and release-artifact modes. Complete the progressive controller-owned drone tutorial and builder-first README/Sphinx migration guidance. This phase does not add a new runtime scheduler, statechart model, transition API, or publication/tagging operation by implication.

</domain>

<decisions>
## Implementation Decisions

### Performance and Evidence

- **D-01:** Keep the established fresh installed compiled singleton floor at **200,000 transitions/second**. Do not lower it or substitute source-tree throughput. The unfeatured singleton path remains O(1) and must avoid unrelated candidate scans, graph traversal, reflection, and per-dispatch diagnostic allocation. — **Reversibility:** costly — this is the library's core performance contract and a release gate.
- **D-02:** Measure final-state, internal self, external self, and expected-rejection costs as separately identified scenarios, with exact runtime/build origin, Python/tool versions, platform, sample method, and environment label. Report observations, not universal speedup claims; compare local candidate work against unrelated topology growth.
- **D-03:** Reuse the existing release/artifact evidence harness and `uv.lock`/`uv sync --locked` workflow. Do not add a required uv patch version, offline mode, custom cache, or an automatic baseline rewrite. A manifest write is an explicit reviewed evidence step; read-only checks remain the CI behavior. — **Reversibility:** costly — evidence reproducibility and contributor setup depend on this contract.
- **D-04:** Run the same fixed semantic oracle for pure source, freshly built native core, installed pure and compiled wheels, and release artifacts. Assert exact origin/build intent before accepting each result; generated core shadows are moved only through a path-constrained, recoverable protocol.
- **D-05:** Exact isolated `python-statemachine` 2.5.0 and 3.2.1 comparisons remain labelled manual or scheduled observations with semantic preflight and unsupported-cell disclosure, not ordinary CI pass/fail gates. The native Fast FSM floor is the durable release threshold.

### Progressive Drone Tutorial

- **D-06:** Keep `DroneController` as owner of the FSM and replaceable aircraft command adapter. `TelemetryPolicy` may expose measured facts such as heartbeat age, but all state-dependent transition eligibility and precedence belong in FSM guards on one `telemetry_tick`; the controller does not route failsafes through `if`/`dispatch` branches.
- **D-07:** Teach one concept at a time in the existing deterministic training simulation: prioritized telemetry guards, internal self-updates, external self-reentry, explicit landing finals, expected `TransitionRejected(code)`, and commands issued only by committed entry behavior. Simulated telemetry is deterministic, with no hidden scheduler, actual hardware integration, or real-time flight-safety claim.
- **D-08:** Keep the example builder-first and smoke-testable. Show a distinct false guard (ineligible candidate) versus expected rejection (terminal domain outcome); explain why final landing is not merely a dead-end node.

### README and Sphinx Learning Path

- **D-09:** Start with one small `FSMBuilder` recipe and only then layer guards, priority, mode, finality, rejection, diagnostics, async/direct advanced use, and artifact/performance details. Direct `StateMachine`/`AsyncStateMachine` construction remains supported advanced use; `from_dict()` stays the serialized-topology adapter, not a rival general-purpose builder. — **Reversibility:** costly — this hierarchy is the public onboarding contract from Phase 30.
- **D-10:** Give actionable migration examples for `simple_fsm`, `quick_fsm`, `quick_build`, and `from_states` to `FSMBuilder`, noting their one-warning-per-call compatibility period through v0.5.x and removal no earlier than v0.6.0. Do not suggest that direct constructors, `from_dict()`, or declarative states are deprecated.
- **D-11:** Explain the three important distinctions consistently in README and Sphinx: explicit finality versus no-outgoing topology, expected rejection versus ordinary false/ineligibility versus unexpected failure, and internal self-transition versus external self-transition. Prefer runnable examples and exact output fields over abstract prose alone.

### the agent's Discretion

- Exact benchmark script/module layout, labelled record schema additions, sample counts beyond the unchanged durable floor gate, and documentation page split may follow existing project patterns.
- The tutorial may reuse or simplify `examples/drone_failsafes.py` and its Sphinx literal inclusion, provided the one-example progressive story stays deterministic and all existing command effects remain post-commit.
- Release artifact proof does not itself create a Git tag, GitHub Release, or PyPI publication; milestone audit and the separately authorized release workflow govern external publication.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Scope

- `.planning/ROADMAP.md` §Phase 32 — phase goal, eight requirement IDs, and five success criteria.
- `.planning/REQUIREMENTS.md` §Performance and Release Evidence and §Documentation and Examples — PERF-01–PERF-04 and DOC-01–DOC-04.
- `.planning/PROJECT.md` — speed identity, flat-FSM boundary, benchmark policy, controller-owned drone, and locked-uv release decision.
- `.planning/research/FEATURES.md` — approved high/medium feature cut and user-facing distinctions.
- `.planning/research/ARCHITECTURE.md` — evidence and documentation integration recommendations.
- `.planning/research/PITFALLS.md` — artifact parity, benchmark, and documentation traps.

### Settled Phase Contracts

- `.planning/phases/26-canonical-construction-evidence-contract/26-CONTEXT.md` — isolated competitor lanes and existing evidence seam.
- `.planning/phases/27-explicit-final-states/27-CONTEXT.md` — finality and non-final sink meaning.
- `.planning/phases/28-same-state-transition-modes/28-CONTEXT.md` — internal/external self behavior and timing.
- `.planning/phases/29-expected-domain-rejection/29-CONTEXT.md` — exact rejection code and guard fallthrough distinction.
- `.planning/phases/30-builder-first-construction-persistence-parity/30-CONTEXT.md` — builder-first hierarchy and deprecation timing.
- `.planning/phases/31-semantic-diagnostics-visualization/31-CONTEXT.md` — final/mode/rejection diagnostic truth and safeguards.
- `.planning/phases/31-semantic-diagnostics-visualization/31-VERIFICATION.md` — passing pure/native cross-surface proof and remaining Phase 32 hand-off.

### Implementation and Release Contracts

- `.github/copilot-instructions.md` — authoritative quality, uv, source/native, and release-evidence workflow.
- `.specify/memory/constitution.md` — performance, safety, and documentation invariants.
- `tools/release_evidence.py` and `tools/artifact_conformance.py` — exact-origin artifact and installed-performance harness.
- `benchmarks/comparison/run_comparison.py` — isolated comparator scenario framework.
- `Taskfile.yml` and `uv.lock` — normal locked developer/release commands.
- `examples/drone_failsafes.py`, `tests/test_drone_failsafes_example.py`, and `docs/examples/index.md` — current controller-owned simulation and documentation entry point.
- `README.md`, `docs/QUICK_START.md`, and `docs/api/core.md` — current onboarding and API hierarchy to consolidate.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `tools/release_evidence.py` already builds/installs exact wheels, asserts module origins, runs a three-sample compiled trigger floor, and records labelled evidence. `tools/artifact_conformance.py` and `tests/test_installed_artifacts.py` cover semantic parity.
- `benchmarks/benchmark_fast_fsm.py` and `benchmarks/comparison/` provide existing scenario and isolated-comparator runners.
- `examples/drone_failsafes.py` already has `DroneController`, `TelemetryPolicy`, `AircraftCommands`, prioritized `telemetry_tick` candidates, and committed entry commands; it lacks the new Phase 27–29 teaching cases.
- `README.md`, `docs/QUICK_START.md`, API pages, and `docs/examples/index.md` already have builder examples and a tiered example index; Phase 32 can reorganize rather than create a second guide hierarchy.

### Established Patterns

- `core.py` is the only mypyc compilation unit. Installed compiled throughput is gated; exact scenario timings are labelled observations.
- Release baseline writes are deliberate; CI checks freshness without writing. `uv.lock` governs dependency resolution, without machine-specific cache/offline policy.
- Examples are deterministic, runnable, and hardware-free. Transitions own priority; application adapters perform effects on committed entry.
- Codebase maps under `.planning/codebase/` predate Phases 26–31 and are orientation only; live code and current phase artifacts outrank their old line numbers and feature inventories.

### Integration Points

- Add scenario probes to the existing benchmark/evidence families; do not splice them into the unfeatured trigger hot path.
- Extend one fixed artifact semantic oracle and exact-origin assertions across source/native/installed/release modes.
- Update the drone script, its smoke tests, README, Quick Start, Sphinx examples/API pages, and migration references as one progressive teaching path.

</code_context>

<specifics>
## Specific Ideas

The user wants the FSM itself to own priority and transition rules, with the controller merely feeding live telemetry and the simulated aircraft adapter receiving commands after the selected transition commits. The library's speed advantage over `python-statemachine` is the reason to avoid extra dispatch-time work. Examples should be themed and progressive rather than each trying to show every feature.

</specifics>

<deferred>
## Deferred Ideas

- Queued/reentrant processing, deferred event-context construction, pluggable state storage, and statechart/scheduler behavior remain future requirements, not Phase 32 work.
- External publication/tagging is handled after milestone proof and authorization, not inferred from an artifact conformance test.

</deferred>

---

*Phase: 32-performance-artifact-progressive-guidance-proof*
*Context gathered: 2026-09-19*
