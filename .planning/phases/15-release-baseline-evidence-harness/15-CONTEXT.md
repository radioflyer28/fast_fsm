# Phase 15: Release Baseline & Evidence Harness - Context

**Gathered:** 2026-08-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish trustworthy release history, quality gates, reproducible tooling,
pure-source verification, and an auditable evidence baseline before runtime
semantics change. This phase may define the common build-mode and evidence
interfaces needed by later work, but strict compiled-wheel enforcement and
publication proof remain Phase 20 responsibilities.

</domain>

<decisions>
## Implementation Decisions

### v0.2.3 Correction Record
- **D-01:** Classify v0.2.3 as a shipped release with defective package metadata; do not describe it as withdrawn or silently replace it.
- **D-02:** Preserve the existing v0.2.3 tag and any published artifacts. If artifacts exist on a package index, keep them available and direct users to the correction notice and v0.3.0.
- **D-03:** Create dated v0.2.2 and v0.2.3 changelog sections, move the currently misplaced `Unreleased` entries into their actual release sections, and annotate the v0.2.3 metadata defect.
- **D-04:** Publish the same concise correction in the GitHub v0.2.3 release notice; do not add a persistent historical warning to the README.

### Quality-Gate Authority
- **D-05:** Mypy is the blocking, stable type-compatibility authority. Keep `ty` as advisory feedback while it remains pre-release.
- **D-06:** Establish a trustworthy pure-Python coverage baseline and block regressions from that measured baseline rather than imposing an arbitrary fixed percentage immediately.
- **D-07:** Run the complete quality gate on every pull request and release: formatting, lint, mypy, tests, documentation, doctests, and coverage freshness/regression checks.
- **D-08:** Run blocking checks independently so one CI run reports all failures rather than stopping at the first failed category.

### Published Evidence Claims
- **D-09:** Narrative documentation uses durable rounded claims such as “700+ tests”; exact test counts live in generated evidence.
- **D-10:** Store the authoritative baseline in a tracked machine-readable manifest and render a readable CI summary from it. The manifest includes exact test count, clean-source coverage baseline, relevant tool versions, artifact mode, and environment-specific measurements.
- **D-11:** Provide an explicit generator command for the manifest. Contributors review the generated diff, and CI fails when the committed manifest is stale; CI must not commit updates automatically.
- **D-12:** Documentation states stable performance contracts such as the ≥200,000 compiled `trigger()` operations/sec floor. Exact benchmark results and their environment belong in the evidence manifest, not as volatile README headlines.

### Pure-Build Identity
- **D-13:** Use one explicit build-mode selector with `auto`, `pure`, and `compiled` values. Preserve `FAST_FSM_PURE_PYTHON=1` as a compatibility alias.
- **D-14:** Provide a canonical verification command that records wheel tags, installed metadata, and the loaded `fast_fsm.core` module origin. Do not add a public runtime `build_info()` API in this phase.
- **D-15:** A pure-source verification run that detects a stale `.so` or `.pyd` shadowing `core.py` fails immediately and reports the exact path. It never deletes developer files automatically; cleanup is explicit.
- **D-16:** The evidence model must support the v0.3.0 artifact set selected for Phase 20: compiled platform wheels plus one universal pure-Python wheel, with the pure wheel serving as an intentional fallback.

### Agent's Discretion
- Exact build-mode environment variable name and compatibility-parsing structure.
- Evidence-manifest filename, schema details, deterministic serialization format, and generator module location.
- Exact tool versions to pin, provided they are verified compatible with Python 3.10–3.14 and the mypyc boundary.
- Exact coverage-baseline comparison mechanics and CI job decomposition, provided every required check remains independently visible and blocking.
- Wording of the changelog and GitHub release correction, provided both records state the same facts without moving the historical tag.
- Measurement method for the `CompiledFuncCondition` slots-policy exception and how the result is summarized in project documentation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Phase Scope
- `.planning/PROJECT.md` — v0.3.0 goal, constraints, safe-default posture, and performance contract.
- `.planning/REQUIREMENTS.md` — Phase 15 requirements REL-02, REL-04, REL-05, REL-06, REL-08, and TEST-02.
- `.planning/ROADMAP.md` — Phase 15 boundary, dependencies, and observable success criteria.
- `.planning/research/SUMMARY.md` — research-backed evidence-first ordering, stack guidance, and Phase 15 risks.

### Verified Baseline and Risks
- `.planning/codebase/CONCERNS.md` — reproduced version drift, optional compilation risk, slots-policy exception, stale-extension shadowing, and quality-gate failures.
- `.planning/codebase/TESTING.md` — verified 722-test snapshot, Ruff failures, coverage artifact, test conventions, and canonical commands.
- `.planning/codebase/STACK.md` — current Python/tool matrix, build backend, environment flags, and conflicting version sources.

### Release and Quality Contracts
- `CHANGELOG.md` — release history that must be reorganized into dated v0.2.2 and v0.2.3 sections.
- `pyproject.toml` — package version, dependency groups, build requirements, pytest configuration, and package metadata.
- `setup.py` — current optional mypyc build and pure-Python selector behavior.
- `Taskfile.yml` — existing local quality, test, coverage, build, benchmark, and documentation commands.
- `.github/workflows/ci.yml` — pull-request quality matrix and current compiled smoke coverage.
- `.github/workflows/release.yml` — current artifact build and publication flow; strict release proof is completed in Phase 20.
- `.github/workflows/docs.yml` — documentation build/deployment checks.
- `.github/copilot-instructions.md` — mandatory uv workflow, quality gates, supported matrix, and currently stale test baseline.
- `.specify/memory/constitution.md` — project-level performance, testing, documentation, and compatibility principles.
- `.specify/decisions/ADR-003-mypyc-compilation-boundary.md` — authoritative boundary requiring only `core.py` to compile while condition classes remain interpreted.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/fast_fsm/__init__.py`: already derives `__version__` through `importlib.metadata`; version verification should test installed metadata rather than introduce another version constant.
- `setup.py`: existing mypyc selection and `FAST_FSM_PURE_PYTHON` handling are the integration point for the unified build-mode selector.
- `Taskfile.yml`: existing `test`, `test-coverage`, quality, build, benchmark, and docs tasks can be composed behind canonical generator/verification commands.
- `tests/test_mypyc_guard.py`: existing static compilation-boundary checks can anchor build-mode and installed-origin assertions.
- `tests/test_performance_benchmarks.py`: established warm-up and `time.perf_counter()` conventions can produce environment-specific evidence without changing narrative claims.
- Pytest, pytest-cov, Ruff, mypy, ty, Sphinx, and doctest are already development dependencies; no new runtime dependency is needed.

### Established Patterns
- Use `uv` for every Python dependency, execution, test, build, and documentation command.
- Tests exercise real FSM objects and run sequentially; the full suite is the merge gate.
- `core.py` remains the only mypyc compilation unit, while `conditions.py` and `condition_templates.py` stay interpreted for subclassing.
- The package has one runtime dependency (`mypy-extensions`); evidence tooling belongs in development/build groups or the standard library.
- Documentation uses Sphinx/MyST and Google-style docstrings; generated evidence should not become a second narrative documentation system.

### Integration Points
- Version and changelog reconciliation: `pyproject.toml`, `CHANGELOG.md`, `README.md`, and `.github/copilot-instructions.md`.
- Local evidence generation and pure-source checks: `Taskfile.yml`, `setup.py`, and a tracked manifest generated from clean commands.
- Pull-request enforcement: `.github/workflows/ci.yml` with independently visible blocking jobs/checks.
- Release reuse: `.github/workflows/release.yml` consumes the same canonical checks and manifest freshness contract; Phase 20 adds installed compiled/pure artifact proof.
- Historical public correction: `CHANGELOG.md` plus the existing GitHub v0.2.3 release notice.

</code_context>

<specifics>
## Specific Ideas

- Prefer durable prose (“700+ tests”, “≥200,000 compiled trigger operations/sec”) and keep exact, environment-sensitive numbers in generated evidence.
- Pure-mode verification must be fail-closed but non-destructive: identify the shadowing native file and tell the developer to run an explicit clean action.
- The build selector should make intent machine-readable while retaining the current pure-Python environment variable for compatibility.

</specifics>

<deferred>
## Deferred Ideas

- Strict failure when a requested compiled artifact cannot be produced or does not contain the native extension — Phase 20 (REL-03).
- Installed compiled/pure conformance and native-platform release proof — Phase 20 (REL-01, REL-07, TEST-01, TEST-03 through TEST-07).
- Publishing the selected compiled-wheel plus universal-pure-wheel artifact set — Phase 20; Phase 15 only defines the mode and evidence contracts it will consume.

</deferred>

---

*Phase: 15-release-baseline-evidence-harness*
*Context gathered: 2026-08-29*
