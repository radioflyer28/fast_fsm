---
phase: 26
slug: canonical-construction-evidence-contract
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-15
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4.1 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_competitor_benchmark_contract.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run the narrow test command named by that task.
- **After every plan wave:** Run `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_competitor_benchmark_contract.py -x -q`.
- **Before `$gsd-verify-work`:** Full sequential suite, type checks, Ruff, slots policy, semantic preflights, and the manual observation command must be green.
- **Max feedback latency:** 120 seconds for automated task-level checks.

## Phase Tracking Prerequisite and Closure

- Before Wave 1 implementation, run `bd ready --json`. If the repository's Dolt service cannot return valid JSON, stop at a blocking-human prerequisite; never invent an issue identifier or begin code changes.
- Discover an existing open/in-progress item titled `Phase 26: Canonical Construction & Evidence Contract`; reuse it if already claimed, claim it with `bd update <id> --claim --json` when open, or create exactly one with `bd create "Phase 26: Canonical Construction & Evidence Contract" --description="Implement and verify Phase 26 canonical construction and comparison evidence contracts." -t task -p 2 --json` and claim that returned ID when absent. Record the exact ID as `phase_bead_id` in `26-01-SUMMARY.md`.
- Do not create per-plan Beads items. Carry the same ID through `26-05-SUMMARY.md` and keep it claimed across execution, verification, and any gap-closure cycle.
- Only after every phase verification gate passes, run `bd close <phase_bead_id> --reason "Phase 26 verified" --json` and record the successful closure in the phase verification artifact. If verification finds gaps, leave the item claimed until those gaps are fixed and verification passes.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | BUILD-04 | T-26-01, T-26-09 | One real phase issue is available before direct/batch requests reach the immutable normalize/merge/publish transaction | prerequisite/unit/structural | `bd ready --json`; `uv run pytest tests/test_graph_invariants.py -x -q -k "construction_request or adapter_transaction or batch_atomic or priority"` | ✅ partial | ⬜ pending |
| 26-01-02 | 01 | 1 | BUILD-04, BUILD-05 | T-26-01, T-26-02 | Repeated/interrupted/concurrent machine use is atomic and runtime selectors remain isolated | unit/structural | `uv run pytest tests/test_graph_invariants.py -x -q -k "idempotent or interrupt or concurrent or construction_hot_path"` | ✅ partial | ⬜ pending |
| 26-02-01 | 02 | 2 | PERF-05, PERF-06 | T-26-03, T-26-04, T-26-06 | Strict allowlisted Fast FSM identity and both required semantic records precede timing | unit/static | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "schema or fast_fsm or preflight or false_guard or unsupported or bounded"` | ❌ W0 | ⬜ pending |
| 26-02-02 | 02 | 2 | PERF-05, PERF-06 | T-26-03, T-26-04, T-26-06 | Absolute repo-aware child commands, neutral-cwd Fast resolution, and parent contradictions are offline-testable | unit/static/integration | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "command or exact_version or origin or contradiction or subprocess or unsupported or neutral_cwd or false_guard"` | ❌ W0 | ⬜ pending |
| 26-03-01 | 03 | 2 | BUILD-04, BUILD-05 | T-26-01, T-26-08, T-26-10 | Helpers/factories/dictionaries/declarative endpoints and clone reconstruction share the transaction and fail outwardly atomically | unit/matrix | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py -x -q -k "adapter_matrix or bidirectional or emergency or quick_build or quick_fsm or from_dict or declarative or clone"` | ✅ partial | ⬜ pending |
| 26-03-02 | 03 | 2 | BUILD-04, BUILD-05 | T-26-02 | Builder request staging/cache/type remain unchanged and repairable after late failure | unit/matrix | `uv run pytest tests/test_builder.py tests/test_graph_invariants.py -x -q -k "builder and (request or atomic or failure or repair or cache or async)"` | ✅ partial | ⬜ pending |
| 26-04-01 | 04 | 3 | PERF-05 | T-26-SC | Human verifies exact official distribution releases/upstream before lock generation | blocking-human | Human verification of both official PyPI pages and upstream provenance | n/a | ⬜ pending |
| 26-05-01 | 05 | 4 | PERF-05, PERF-06 | T-26-05 | Adjacent locks match exact scripts and project dependency roots exclude competitors | unit/static | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q -k "project_groups or lock or dependency"` | ❌ W0 | ⬜ pending |
| 26-05-02 | 05 | 4 | PERF-05, PERF-06 | T-26-03, T-26-04, T-26-06 | Manual exact run passes both required semantics and ordinary CI/release paths remain isolated | contract/integration | `uv run pytest tests/test_competitor_benchmark_contract.py -x -q`; `task benchmark-compare -- --warmup 10 --operations 100 --samples 1` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Plan 26-01 adds direct/batch request, adjacency, idempotence, interruption, ownership, and hot-path structural cases to `tests/test_graph_invariants.py` before core changes.
- [ ] Plan 26-02 creates `tests/test_competitor_benchmark_contract.py` with strict records, both required cells, contradiction rejection, optional unsupported cells, absolute repo-aware command construction, neutral-cwd Fast-only resolution, bounded-output cases, and otherwise fixture-only execution.
- [ ] Plan 26-03 expands the adapter transaction matrix in `tests/test_graph_invariants.py` and `tests/test_builder.py` with clone success/failure/parity before routing remaining adapters and clone reconstruction.
- [ ] Plan 26-05 adds lock/project dependency, CI/release isolation, stdout-only, and live low-count observation coverage after package approval.
- [ ] Fixture records cover Fast FSM, 2.5.0, 3.2.1, malformed identity, failed `flat-alternating-cycle` and `false-guard-no-transition` required preflights, and unsupported optional scenarios without timing thresholds.
- Existing pytest infrastructure covers the phase; no framework installation is required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Official distribution legitimacy and adjacent lock review | PERF-05 | Package telemetry was unavailable to the automated research seam | Confirm both exact distributions and source provenance on official PyPI/upstream pages before committing generated locks. |
| Exact isolated comparison observation | PERF-05, PERF-06 | Deliberately excluded from ordinary CI because it downloads competitors and produces environment-sensitive timings | Run `task benchmark-compare`; verify both child versions/origins, all required semantic preflights, explicit unsupported cells, and no ratio for unsupported scenarios. |
| Close the single Phase 26 Beads item | BUILD-04, BUILD-05, PERF-05, PERF-06 | Closure is a post-verification project-governance action, not an implementation-plan success claim | After every phase gate passes, read `phase_bead_id` from `26-05-SUMMARY.md`, run `bd close <phase_bead_id> --reason "Phase 26 verified" --json`, and record the successful result; leave it claimed if any gap remains. |

---

## Validation Sign-Off

- [x] All implementation tasks have automated verification; the package-legitimacy task is an explicit blocking-human trust checkpoint.
- [x] Sampling continuity: no three consecutive implementation tasks lack automated verification.
- [x] Wave 0 work is assigned test-first inside Plans 26-01, 26-02, 26-03, and 26-05.
- [x] No watch-mode flags.
- [x] Focused automated feedback targets stay below 120 seconds; the deliberate external smoke run is a Phase 26 integration gate.
- [x] `nyquist_compliant: true` is set.
- [x] Beads preflight, single-ID propagation, and post-verification-only closure are explicit; no identifier is fabricated while Dolt is unavailable.

**Approval:** plan/task IDs reconciled 2026-09-15
