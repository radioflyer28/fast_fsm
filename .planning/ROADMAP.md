# Roadmap: Fast FSM

## Milestones

- ✅ **v0.2.1 Code Health & Quality** — Phases 1–6 (shipped 2026-04-04)
- ✅ **v0.2.2 Introspection & Agent Tooling** — Phases 7–11.1 (shipped 2026-04-05)
- ✅ **v0.2.3 Timing Condition Helpers** — Phases 12–14 (shipped 2026-04-05)
- ✅ **v0.3.0 Reliability & Runtime Hardening** — Phases 15–20 (completed 2026-09-06; untagged and unreleased)

## Phases

<details>
<summary>✅ v0.2.1 Code Health & Quality (Phases 1–6) — SHIPPED 2026-04-04</summary>

Version metadata, exception handling, typing, state inheritance, test triage, and the compiled throughput CI gate. **14/14 requirements satisfied.** Full details: `.planning/milestones/v0.2.1-ROADMAP.md`.

</details>

<details>
<summary>✅ v0.2.2 Introspection & Agent Tooling (Phases 7–11.1) — SHIPPED 2026-04-05</summary>

Topology serialization, transition history, PlantUML and JSON output, plus performance verification. **21/21 requirements satisfied.** Full details: `.planning/milestones/v0.2.2-ROADMAP.md`.

</details>

<details>
<summary>✅ v0.2.3 Timing Condition Helpers (Phases 12–14) — SHIPPED 2026-04-05</summary>

Timeout, cooldown, and elapsed conditions with integration tests and documentation. **15/15 requirements satisfied.** Full details: `.planning/milestones/v0.2.3-ROADMAP.md`.

</details>

<details>
<summary>✅ v0.3.0 Reliability & Runtime Hardening (Phases 15–20) — COMPLETED 2026-09-06</summary>

**Milestone goal:** Make Fast FSM release-auditable, internally consistent, and safe by default while preserving public symbols, the single mypyc compilation unit, one runtime dependency, and the compiled throughput floor.

- [x] **Phase 15: Release Baseline & Evidence Harness** — auditable version, quality, pure-source, and toolchain evidence.
- [x] **Phase 16: Canonical Graph & Dispatch Invariants** — consistent construction, topology, guards, dispatch, and history.
- [x] **Phase 17: Atomic Transition Lifecycle** — truthful pre-commit, commit, and post-commit outcomes for sync and async machines.
- [x] **Phase 18: Safe Ownership & Concurrency** — per-machine ownership, reentry rejection, and safe concurrent access.
- [x] **Phase 19: Bounded Diagnostics & Safe Output** — bounded snapshot diagnostics, grammar-safe output, and non-invasive redacted logging.
- [x] **Phase 20: Installed Artifact Parity & Release Proof** — exact installed-artifact parity and hosted evidence proof.

**Result:** 50/50 requirements, 6/6 phases, and 41/41 plans verified. The final exact-SHA hosted run passed all 101 jobs, and downloaded evidence was independently recomputed. Planning records are archived under `.planning/milestones/v0.3.0-*`. No v0.3.0 Git tag, GitHub Release, or package publication was created.

</details>

## Current Status

No active milestone. Begin the next milestone with `/gsd-new-milestone` when ready.
