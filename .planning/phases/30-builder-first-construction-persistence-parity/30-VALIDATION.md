---
phase: 30
slug: builder-first-construction-persistence-parity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-17
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for builder-first construction and persistence parity.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 with pytest-asyncio and Hypothesis |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_builder.py tests/test_advanced_functionality.py tests/test_final_states.py tests/test_transition_modes.py tests/test_graph_invariants.py -x -q -k "declarative or deprecat or from_dict or clone or snapshot or internal or final or construction"` |
| **Structural command** | `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py -x -q -k "construction or declarative or persistence or adapter or hot_path"` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | Quick: <60 seconds; full/native closure: project-dependent |

---

## Sampling Rate

- **After every task commit:** Run the requirement-specific targeted command below; for `core.py` or stub changes also run `task typecheck-mypy`.
- **After every plan wave:** Run the quick construction/persistence suite, `task typecheck-mypy`, visible `task typecheck-ty`, and non-mutating Ruff checks.
- **Before `$gsd-verify-work`:** Run warning-as-error docs/doctests, slots policy, pure semantic oracle, fresh compiled semantic oracle, singleton performance gate, final pure-source assertion, and the full sequential suite.
- **Max feedback latency:** 60 seconds for ordinary tasks; the explicit native/full-suite closure task is the heavyweight exception.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 30-W0-01 | W0 | 0 | BUILD-02, BUILD-06 | T-30-01, T-30-02, T-30-07 | Central parity oracle proves canonical declarative import, exactly-once execution, and atomic failure across adapters | unit + integration | `uv run pytest tests/test_builder.py tests/test_graph_invariants.py -x -q -k "declarative or construction or parity"` | ✅ extend | ⬜ pending |
| 30-W0-02 | W0 | 0 | BUILD-02, BUILD-06 | T-30-01, T-30-07 | Runtime, stub, carrier fields, and hot-path structure agree without a registrar bypass | structural | `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py -x -q -k "declarative or adapter or hot_path"` | ✅ extend | ⬜ pending |
| 30-W0-03 | W0 | 0 | BUILD-03 | T-30-03, T-30-04 | Each deprecated public surface emits one fixed caller-attributed warning and preserves behavior | unit | `uv run pytest tests/test_builder.py tests/test_final_states.py -x -q -k "deprecat or quick or from_states or simple_fsm"` | ✅ extend | ⬜ pending |
| 30-W0-04 | W0 | 0 | BUILD-07, BUILD-08 | T-30-05, T-30-06 | Exact dictionary types, true-only internal emission, legacy defaults, clone isolation, and snapshot-v1 ownership are locked | integration | `uv run pytest tests/test_advanced_functionality.py tests/test_final_states.py tests/test_transition_modes.py tests/test_graph_invariants.py -x -q -k "from_dict or roundtrip or clone or snapshot or restore or internal or final"` | ✅ extend | ⬜ pending |
| 30-DOC-01 | TBD | TBD | BUILD-01, BUILD-03 | T-30-04 | Focused API guidance leads with builder, distinguishes advanced direct construction and serialized reconstruction, and gives bounded migration guidance | docs + executable examples | `uv run pytest tests/test_readme_examples.py -x -q && task docs-check && task docs-test` | ✅ extend | ⬜ pending |
| 30-GATE-01 | TBD | TBD | BUILD-01–BUILD-08 | T-30-01–T-30-08 | Pure/native semantics, static authority, performance floor, source restoration, and full regressions all agree | release closure | Plan closure sequence: Ruff; mypy/visible ty/slots/docs; asserted pure oracle; trapped fresh native build/oracle/benchmark; exact shadow restoration; final pure-origin assertion; full suite | ✅ harness | ⬜ pending |

*The planner replaces TBD plan/wave labels and may split rows while preserving every requirement and threat mapping.*

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Required Validation Matrices

1. **Decorator contract:** default/explicit mode, exact bool rejection, retained priority/timing, immutable plural sources, matching runtime/stub fields, and frozen metadata.
2. **Declarative builder:** initial/later import, omitted/single/plural source constraints, unknown/final/internal failures, explicit/declarative collisions, repair after failure, and cached success.
3. **Exactly once:** sync/async decorator guard, handler, entry guard, permission, and lifecycle counters; no copied guard may execute twice.
4. **Warning contract:** one exact `DeprecationWarning` per public invocation, user call-site attribution, fixed bounded message, unchanged returned behavior/type, and silence on nondeprecated surfaces.
5. **Dictionary contract:** external omission, explicit false input, true-only output, old-payload defaults, exact container/scalar negatives, indexed errors, JSON round-trip, and no partial publication.
6. **Clone/snapshot:** state subclass/final/internal preservation, independent topology and callback containers, concrete async type, reset-to-initial clone, exact two-key snapshot v1, and receiver-owned finality/mode after restore.
7. **Structural/native parity:** every retained adapter converges on canonical requests/publication; construction policy is absent from dispatch; the same semantic oracle passes asserted pure and fresh native origins.

---

## Wave 0 Requirements

- [ ] Add or isolate a central Phase 30 construction/persistence parity oracle that runs unchanged in pure and native modes.
- [ ] Extend `tests/test_mypyc_guard.py` exact field sets for declarative metadata/handlers, including `internal`.
- [ ] Add exact warning category, count, fixed text, and call-site attribution tests for all four deprecated surfaces.
- [ ] Add exact dictionary type, legacy-default, and true-only transition-mode tests while preserving existing external-row output.

No new framework, dependency, configuration, or shared fixture module is required.

---

## Threat Register

| ID | Threat | Required control |
|----|--------|------------------|
| T-30-01 | Declarative metadata mutates after declaration | Deep-freeze caller collections into immutable metadata before staging. |
| T-30-02 | Declarative guard executes twice or bypasses canonical selection | Keep guard ownership at the handler seam and import only topology scalars through `_TransitionRequest`. |
| T-30-03 | Nested deprecated helpers multiply warnings | Warn only at each public boundary and delegate to private non-warning workers. |
| T-30-04 | Warning or validation text leaks caller payloads | Use fixed bounded messages and indexed structural context without payload repr. |
| T-30-05 | Malformed dictionaries partially publish topology | Validate the complete document and publish once through the Phase 26 transaction. |
| T-30-06 | Clone aliases mutable topology/callback containers | Rebuild independent tables/entries/registries while retaining documented state/callable identities. |
| T-30-07 | Adapter-specific validation weakens final/internal rules | Normalize every path through the same canonical request and publication seam. |
| T-30-08 | Construction policy reaches the hot dispatch path | Enforce structural absence checks and the compiled singleton throughput floor. |

---

## Manual-Only Verifications

All Phase 30 behaviors have automated verification routes.

---

## Validation Sign-Off

- [ ] Every final plan task has an automated verify route or an explicit Wave 0 dependency.
- [ ] Sampling continuity has no three consecutive implementation tasks without automated verification.
- [ ] Wave 0 covers every missing test reference.
- [ ] Commands use no watch-mode flags.
- [ ] Ordinary-task feedback latency remains below 60 seconds.
- [ ] Pure/native closure restores and reasserts the pure source origin on every exit.
- [ ] `nyquist_compliant: true` is set after the post-execution gap audit succeeds.

**Approval:** pending execution and Nyquist audit.
