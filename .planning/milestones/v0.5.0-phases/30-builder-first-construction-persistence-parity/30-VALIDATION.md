---
phase: 30
slug: builder-first-construction-persistence-parity
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| 30-01-01 | 01 | 1 | BUILD-02, BUILD-06 | T-30-01, T-30-02, T-30-07 | Tracer oracle proves canonical declarative import, exactly-once execution, and atomic failure | unit + integration | `uv run pytest tests/test_construction_parity.py tests/test_builder.py -x -q -k "declarative and (builder or internal or exactly_once or immutable or direct_handle)"` | ✅ present | ✅ green |
| 30-01-02 | 01 | 1 | BUILD-02, BUILD-06 | T-30-01, T-30-07, T-30-08 | Runtime, stub, carrier fields, canonical publication, and hot-path structure agree without a registrar bypass | structural | `uv run pytest tests/test_construction_parity.py tests/test_graph_invariants.py tests/test_mypyc_guard.py -x -q -k "declarative or construction or adapter or hot_path"` | ✅ present | ✅ green |
| 30-02-01 | 02 | 2 | BUILD-02, BUILD-06 | T-30-01, T-30-02, T-30-07 | Declarative applicability, async detection, collisions, cache, and repaired retry preserve state-owned exactly-once semantics | unit + integration | `uv run pytest tests/test_builder.py tests/test_transition_modes.py -x -q -k "declarative and (builder or source or target or conflict or repair or cache or async or internal or exactly_once)"` | ✅ present | ✅ green |
| 30-02-02 | 02 | 2 | BUILD-06 | T-30-07, T-30-08 | Direct, batch, builder, declarative, and callback construction produce the same observable final/internal truth and atomic failure | integration + structural | `uv run pytest tests/test_construction_parity.py tests/test_final_states.py tests/test_transition_modes.py tests/test_graph_invariants.py -x -q -k "construction_parity or adapter or declarative or callback or final_source or internal"` | ✅ present | ✅ green |
| 30-03-01 | 03 | 3 | BUILD-03 | T-30-03, T-30-04 | Each deprecated public surface emits one fixed caller-attributed warning and preserves behavior | unit | `uv run pytest tests/test_builder.py -x -q -k "deprecat or warning or quick_build or from_states or simple_fsm or quick_fsm"` | ✅ present | ✅ green |
| 30-03-02 | 03 | 3 | BUILD-03, BUILD-06 | T-30-03, T-30-07 | Deprecated helpers remain exported, typed, subclass-safe, atomic, and semantically equivalent throughout v0.5.x | integration + static | `uv run pytest tests/test_builder.py tests/test_final_states.py tests/test_construction_parity.py -x -q -k "deprecat or quick or from_states or simple_fsm or construction_parity"` | ✅ present | ✅ green |
| 30-04-01 | 04 | 4 | BUILD-06, BUILD-07 | T-30-04, T-30-05, T-30-07 | Exact dictionary types, true-only output, legacy defaults, semantic round trips, and atomic malformed-input failure are locked | integration | `uv run pytest tests/test_advanced_functionality.py tests/test_final_states.py tests/test_transition_modes.py -x -q -k "from_dict or to_dict or roundtrip or serialization or legacy or internal or final"` | ✅ present | ✅ green |
| 30-04-02 | 04 | 4 | BUILD-06, BUILD-07, BUILD-08 | T-30-06, T-30-07, T-30-08 | Clone isolation, exact snapshot-v1 ownership, and complete retained-adapter parity are locked | integration + structural | `uv run pytest tests/test_advanced_functionality.py tests/test_final_states.py tests/test_graph_invariants.py tests/test_construction_parity.py -x -q -k "clone or snapshot or restore or construction_parity or adapter or internal or final"` | ✅ present | ✅ green |
| 30-05-01 | 05 | 5 | BUILD-01, BUILD-03 | T-30-04 | README, Quick Start, Tutorial, and cross-FSM teaching paths lead with builder and move warned helpers into bounded compatibility guidance | docs + executable examples | `uv run pytest tests/test_readme_examples.py -x -q -k "active_construction_guidance_uses_builder and (readme or quick_start or tutorial or cross_fsm_demo)" && uv run pytest tests/test_examples_smoke.py -x -q -k "cross_fsm_demo" && task docs-check && task docs-test` | ✅ present | ✅ green |
| 30-05-02 | 05 | 5 | BUILD-01, BUILD-02, BUILD-03, BUILD-07, BUILD-08 | T-30-04, T-30-07, T-30-08 | Core/validation/visualization API examples and contributor architecture agree on builder-first hierarchy, canonical ownership, directional persistence, clone, and snapshot contracts | docs + doctest | `uv run pytest tests/test_readme_examples.py -x -q -k "active_construction_guidance_uses_builder and (api_visualization or api_validation)" && task docs-check && task docs-test` | ✅ present | ✅ green |
| 30-06-01 | 06 | 6 | BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, BUILD-08 | T-30-03, T-30-04, T-30-05, T-30-06, T-30-07, T-30-08 | Normative SPR matches the focused public hierarchy, compatibility window, canonical transaction, directional persistence, clone, snapshot, and dispatch-exclusion contracts before structural closure | docs + doctest | `task docs-check && task docs-test` | ✅ present | ✅ green |
| 30-06-02 | 06 | 6 | BUILD-02, BUILD-06, BUILD-07, BUILD-08 | T-30-01, T-30-02, T-30-07, T-30-08 | Final parity-oracle and mypyc structural edits receive immediate focused feedback before heavyweight closure | unit + structural | `uv run pytest tests/test_construction_parity.py tests/test_mypyc_guard.py -x -q -k "construction_parity or declarative or adapter or hot_path"` | ✅ present | ✅ green |
| 30-06-03 | 06 | 6 | BUILD-01, BUILD-02, BUILD-03, BUILD-06, BUILD-07, BUILD-08 | T-30-01, T-30-02, T-30-03, T-30-04, T-30-05, T-30-06, T-30-07, T-30-08 | Pure/native semantics, static authority, performance floor, source restoration, documentation, and full regressions all agree | release closure | Plan closure sequence after SPR sync and the focused check: Ruff; mypy/visible ty/slots/docs; asserted pure oracle; trapped fresh native build/oracle/benchmark; exact shadow restoration; final pure-origin assertion; full suite | ✅ harness | ✅ green |

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

- [x] Add or isolate a central Phase 30 construction/persistence parity oracle that runs unchanged in pure and native modes.
- [x] Extend `tests/test_mypyc_guard.py` exact field sets for declarative metadata/handlers, including `internal`.
- [x] Add exact warning category, count, fixed text, and call-site attribution tests for all four deprecated surfaces.
- [x] Add exact dictionary type, legacy-default, and true-only transition-mode tests while preserving existing external-row output.

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

## Validation Audit 2026-09-17

| Metric | Count |
|--------|-------|
| Task rows executed | 13 |
| Requirements covered | 6/6 |
| Decisions covered | 20/20 |
| Threat controls covered | 8/8 |
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

The adversarial full-suite run exposed a stale synthetic source-archive fixture:
`tests/test_installed_artifacts.py` omitted the new interpreted
`src/fast_fsm/_construction_compat.py` module even though the release-evidence
inspector correctly requires it. The fixture was updated, its focused test
passed on the first repair iteration, and the complete pure-source suite then
passed. The same Phase 30 semantic oracle passed from a freshly compiled mypyc
origin, the compiled singleton throughput gate passed, and both verified core
extension shadows were moved to a recoverable temporary backup before exact
pure-source origin was reasserted.

The visible `task typecheck-ty` advisory remains the documented unresolved
relative-import limitation for `.conditions` and `._construction_compat`;
blocking mypy, Ruff, slots, strict Sphinx, doctests, focused tests, native
tests, throughput, source restoration, and the full sequential suite are green.

### Debug Log

| Gap | Iteration | Error Type | Action | Result |
|-----|-----------|------------|--------|--------|
| Sdist fixture omitted `_construction_compat.py` | 1/3 | Fixture/expectation drift | Added the required module to `_SDIST_PACKAGE_SOURCES` | green |

---

## Validation Sign-Off

- [x] Every final plan task has an automated verify route or an explicit Wave 0 dependency.
- [x] Sampling continuity has no three consecutive implementation tasks without automated verification.
- [x] Wave 0 covers every missing test reference.
- [x] Commands use no watch-mode flags.
- [x] Ordinary-task feedback latency remains below 60 seconds.
- [x] Pure/native closure restores and reasserts the pure source origin on every exit.
- [x] `nyquist_compliant: true` is set after the post-execution gap audit succeeds.

**Approval:** validated; all Phase 30 requirements have automated green evidence.

## Post-Review Revalidation (2026-09-19)

CR-01 and WR-01 fixes passed the same focused oracle in pure and freshly
compiled modes, the compiled singleton throughput test, Ruff, mypy,
runtime auditability/slots policy, strict Sphinx, and doctests. Generated native
shadows were recoverably relocated and exact pure-source origin was reasserted.
The broad sequential suite excluding `test_build_modes.py` and
`test_installed_artifacts.py` passed. The exact full suite initially stopped
because isolated `uv build --offline` checks could not resolve pinned build
tools absent from this host's uv cache. On 2026-09-19, a retry fetched those
exact packages into the normal cache, the previously failing isolated test
passed, and `FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q` passed in
full. The Phase 30 completion blocker is closed.

## Retroactive Nyquist Audit (2026-09-19)

| Metric | Count |
|--------|-------|
| Plan task rows audited | 13/13 |
| Assigned requirements with automated coverage | 6/6 |
| Threat controls represented in the validation map | 8/8 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated/manual-only | 0 |

All six Phase 30 PLAN/SUMMARY pairs were cross-checked against the existing
per-task map. The mapped test files and post-review CR-01/WR-01 regressions
exist. The quick construction/persistence selection, structural selection,
builder-first documentation/example selection, and three post-review
regression tests were rerun and passed. The exact full sequential suite and
the identical fresh-native Phase 30 oracle passed during Phase 30 closure;
`30-VERIFICATION.md` records those heavier gates and source restoration.
No validation gap requires a new test, manual-only entry, or implementation
change. `status: validated` and `nyquist_compliant: true` remain justified.
