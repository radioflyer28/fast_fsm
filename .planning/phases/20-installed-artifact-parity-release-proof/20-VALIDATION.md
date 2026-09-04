---
phase: 20
slug: installed-artifact-parity-release-proof
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-04
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4.1, pytest-asyncio >=1.3.0, Hypothesis >=6.136.6 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py tests/test_artifact_conformance.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~30–60 seconds for quick source checks; installed/native matrices run as explicit slower gates |

---

## Sampling Rate

- **After every task commit:** Run the targeted test files named by that task's `<verify>` block.
- **After every plan wave:** Run `uv run pytest tests/ -x -q` plus the wave's artifact verifier command when packaging or CI changed.
- **Before `$gsd-verify-work`:** Full suite, quality gates, local pure/compiled installed artifact proof, and all locally executable workflow contract tests must be green.
- **Max feedback latency:** 60 seconds for the source quick loop; slow native builds/benchmarks are isolated named gates.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-W0-01 | TBD | 0 | TEST-01 | T-20-oracle-redaction | Scenario records exclude raw payloads and unstable repr data | unit | `uv run pytest tests/test_artifact_conformance.py -x -q` | ❌ W0 | ⬜ pending |
| 20-W0-02 | TBD | 0 | REL-07, TEST-04 | T-20-origin-spoof | Checkout/editable imports and wrong artifact identities fail closed | integration | `uv run pytest tests/test_installed_artifacts.py -x -q` | ❌ W0 | ⬜ pending |
| 20-BC-01 | TBD | 1 | REL-03 | T-20-fallback | Explicit compiled intent cannot silently produce pure output | unit + build | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py -x -q` | ✅ extend | ⬜ pending |
| 20-CF-01 | TBD | 1 | TEST-01, TEST-03 | T-20-oracle-drift | Every artifact mode executes the same digest-bound scenario inventory | unit + integration | `uv run pytest tests/test_artifact_conformance.py tests/test_installed_artifacts.py -x -q` | ❌ W0 | ⬜ pending |
| 20-EV-01 | TBD | 2 | REL-07, TEST-04 | T-20-record-tamper | SHA, origin, metadata, architecture, intent, and version contradictions are rejected | unit + integration | `uv run pytest tests/test_release_evidence.py tests/test_installed_artifacts.py -x -q` | ✅/❌ W0 | ⬜ pending |
| 20-AG-01 | TBD | 2 | REL-01, TEST-04, TEST-05 | T-20-matrix-substitution | Duplicate, missing, unexpected, or mixed-identity matrix records fail aggregation | unit | `uv run pytest tests/test_release_evidence.py -x -q` | ✅ extend | ⬜ pending |
| 20-PF-01 | TBD | 2 | TEST-06, TEST-07 | T-20-false-performance | Native origin is asserted before the 200k floor; runtime scaling and diagnostic budgets remain separate | invariant + slow benchmark | `uv run pytest tests/test_performance_benchmarks.py tests/test_diagnostic_contracts.py -x -q` | ✅ extend | ⬜ pending |
| 20-CI-01 | TBD | 3 | REL-01, REL-07, TEST-03 | T-20-release-bypass | Release creation has no path around native verification and strict aggregation | workflow contract | `uv run pytest tests/test_release_evidence.py -x -q` | ✅ extend | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_artifact_conformance.py` — deterministic checkout-independent scenario oracle and record normalization.
- [ ] `tests/test_installed_artifacts.py` — isolated exact-path install, origin/provenance, wrong-mode, architecture, version, SHA, and sdist-lineage fixtures.
- [ ] Aggregate-matrix fixtures for duplicate, missing, unexpected, mixed identity, malformed JSON, and digest mismatch cases in `tests/test_release_evidence.py`.
- [ ] Workflow contract fixtures proving each built artifact yields native evidence and `github_release` depends on the strict aggregate.
- [ ] Deterministic size-scaling/invariant cases for `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hosted runner availability for every promised native architecture | REL-07, TEST-03 | Runner entitlement and current GitHub-hosted capacity are external account state | Run the workflow-dispatch matrix before tagging and require every expected native evidence cell to upload successfully. |
| Final public tag target and attached release artifacts | REL-01 | No tag or release should be created during implementation | At release time, verify `v0.3.0` resolves to the aggregated commit and release assets exactly match the accepted SHA-256 set. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s for source quick loops
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
