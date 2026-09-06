# Phase 20: Installed Artifact Parity & Release Proof - Context

**Gathered:** 2026-09-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the v0.3.0 release contract by building, installing, and verifying the
actual pure wheel, compiled platform wheels, and source distribution in clean
environments. The phase unifies hardened behavioral conformance, artifact
identity and provenance, native performance, diagnostic-complexity proof, and
release metadata into one fail-closed publish gate. It does not publish to PyPI,
broaden the runtime API, add platforms outside the documented support matrix,
or redesign behavior already accepted in Phases 15–19.

</domain>

<decisions>
## Implementation Decisions

### Artifact Matrix and Isolation
- **D-01:** The release set contains one intentional universal pure-Python wheel, one source distribution capable of producing the requested pure or compiled installation, and compiled wheels for the supported CPython/platform matrix already declared by release CI. Compiled intent must fail if compilation fails or the installed wheel lacks the native `fast_fsm.core` extension. — **Reversibility:** costly — artifact types and tags are part of the published v0.3.0 distribution contract.
- **D-02:** Every artifact check installs into a fresh environment from a concrete wheel or sdist path with the repository and source tree excluded from import resolution. Verification fails on checkout imports, editable installs, stale native shadows, or an origin outside the installed environment.
- **D-03:** CI may split work across native runners, but every artifact-producing job runs the same verifier and uploads its machine-readable evidence. Cross-compiled artifacts that cannot execute on the builder are not accepted as behavior-proven until a matching native job verifies them.
- **D-04:** The sdist is verified both as an archive contract and as the input to isolated downstream wheel builds. Requested pure and compiled outcomes are explicit; `auto` fallback is never accepted as compiled release proof.

### Shared Hardened Conformance
- **D-05:** One parameterized conformance suite is the semantic oracle for source-pure, installed-pure, installed-compiled, synchronous, asynchronous, builder, and declarative paths. Mode-specific tests may supplement it, but they cannot replace parity scenarios with smoke imports.
- **D-06:** Conformance covers the contracts hardened in Phases 16–19: graph and guard invariants, lifecycle/result/history semantics, ownership and cancellation, bounded diagnostics, grammar-safe output, and redacted non-invasive logging. Expected mode differences are limited to declared origin, artifact type, and performance measurements.
- **D-07:** Parity comparison uses deterministic structured scenario records rather than comparing incidental reprs, timings, paths, or exception addresses. A mismatch identifies the scenario and fields that differ without exposing user payloads.

### Identity, Provenance, and Evidence
- **D-08:** Each installed-artifact evidence record includes artifact filename and SHA-256, wheel/sdist tags, interpreter and platform architecture, installed distribution metadata version, `fast_fsm.__version__`, package path, `fast_fsm.core` origin, asserted pure/compiled type, conformance result, and build intent. Missing or contradictory identity fields fail closed.
- **D-09:** Release-wide aggregation requires a complete expected matrix and rejects duplicate, missing, unexpected, or mixed-version records. Evidence is deterministic and machine-readable, with a concise human summary generated from the same records.
- **D-10:** The release tag, checked-out commit, package metadata, changelog, Sphinx version/release, documentation claims, evidence schema, and every artifact must identify v0.3.0 before release creation. The tag must resolve to the exact verified commit. — **Reversibility:** one-way — a public tag and attached artifacts are immutable release history and corrections must be additive.

### Performance and Publish Gate
- **D-11:** The ≥200,000 `trigger()` operations/second gate runs against an installed compiled wheel on a native runner with asserted native origin. Pure-Python rates and per-phase overhead are recorded as environment-labelled observations rather than substituted for the compiled floor.
- **D-12:** O(1) runtime claims are backed by invariant-focused or size-scaling checks for the core operations named by the milestone; diagnostic work remains outside the hot path and is proven separately by deterministic budget-boundary tests.
- **D-13:** Historical evidence for performance-sensitive Phases 16–19 is consolidated into the final manifest with exact commands and environments. Phase 20 reruns the final installed compiled floor and parity suite rather than treating source-tree phase evidence as installed-artifact proof.
- **D-14:** GitHub release creation depends on successful quality, build, native verification, aggregation, identity, conformance, and performance jobs. Artifact collection alone is insufficient, and no publish/release job may run on partial or advisory evidence.

### Agent's Discretion
- Exact verifier module names, evidence schema field ordering, scenario record types, and CI job decomposition.
- Exact native platform subsets used for local development versus hosted CI, provided the published matrix has native verification before release.
- Exact statistically stable benchmark warmup/sample mechanics, provided the existing fixed compiled floor remains blocking and measurements identify their environment.
- Whether the conformance suite is invoked directly by pytest or through an artifact-verifier wrapper, provided the same collected scenarios execute for every supported mode.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and Release Contract
- `.planning/ROADMAP.md` § Phase 20 — phase goal, dependency, requirements, and five success criteria.
- `.planning/REQUIREMENTS.md` — REL-01, REL-03, REL-07, and TEST-01 through TEST-07.
- `.planning/PROJECT.md` — v0.3.0 goal, compatibility posture, single-module compilation boundary, runtime dependency limit, and performance floor.
- `.github/copilot-instructions.md` — repository workflow, testing, documentation, mypyc, slots, and release quality gates.

### Upstream Decisions and Verified Contracts
- `.planning/phases/15-release-baseline-evidence-harness/15-CONTEXT.md` — build-mode selector, immutable v0.2.3 correction, evidence authority, artifact-set intent, and quality-gate policy.
- `.planning/phases/16-canonical-graph-dispatch-invariants/16-CONTEXT.md` — graph/dispatch contracts that installed artifacts must preserve.
- `.planning/phases/17-atomic-transition-lifecycle/17-CONTEXT.md` — lifecycle/result/history parity contract.
- `.planning/phases/18-safe-ownership-concurrency/18-CONTEXT.md` — thread/task ownership, cancellation, and native-matrix contract.
- `.planning/phases/19-bounded-diagnostics-safe-output/19-CONTEXT.md` — bounded analysis, output escaping, logging safety, and Phase 20 handoff.

### Packaging, CI, and Evidence Surfaces
- `pyproject.toml` — package version, supported Python lower bound, build backend, pinned release dependencies, and package metadata.
- `setup.py` — authoritative `core.py`-only mypyc build boundary and explicit build-mode behavior.
- `.github/workflows/ci.yml` — supported CPython matrix and current source/native quality jobs.
- `.github/workflows/release.yml` — current cibuildwheel matrix, sdist build, artifact collection, and release dependency graph.
- `tools/build_modes.py` — `auto`, `pure`, and `compiled` intent resolution.
- `tools/release_evidence.py` — existing source, wheel, version, coverage, benchmark, and manifest evidence seams.
- `tools/phase16_isolated_verify.py` — fresh-export pure/compiled verification pattern and explicit inventory model.
- `evidence/release-baseline.json` — current machine-readable baseline to evolve into installed-artifact proof.
- `docs/dev/releasing.md` — maintainer release runbook and fail-closed source checks.
- `docs/dev/testing.md` — source-phase evidence boundaries and explicit Phase 20 installed-artifact ownership.
- `CHANGELOG.md` — release history and v0.3.0 release notes source.
- `docs/conf.py` — Sphinx version/release identity that must agree with package metadata.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/release_evidence.py` already captures source origin, wheel tags, metadata, slots, coverage, and benchmark context; extend its structured evidence model instead of creating an unrelated verifier.
- `tools/phase16_isolated_verify.py` already creates explicit fresh pure/native exports, rejects native shadows in pure mode, and runs phase suites from controlled inventories.
- `tools/build_modes.py` and `setup.py` already centralize explicit pure/compiled intent; Phase 20 must make compiled intent truly fail closed.
- The Phase 16–19 tests and evidence suites provide hardened scenarios to extract into a shared conformance matrix.

### Established Patterns
- `uv` and exact locked build dependencies are the only supported local orchestration path.
- Mypy is blocking, ty is advisory, and all quality gates remain independently visible.
- Evidence is deterministic JSON checked read-only in CI; narrative docs use durable claims while exact counts and measurements live in manifests.
- Source-tree and freshly compiled-export proof are prerequisites, not substitutes for installed wheel/sdist proof.

### Integration Points
- Packaging behavior joins at `setup.py`, `pyproject.toml`, and `tools/build_modes.py`.
- Artifact verification joins the conformance suite, `tools/release_evidence.py`, Taskfile commands, and native CI jobs.
- Release aggregation must sit between artifact upload and `github_release` in `.github/workflows/release.yml`.
- Version synchronization touches `pyproject.toml`, `CHANGELOG.md`, `docs/conf.py`, public documentation, tag checks, and generated evidence.

</code_context>

<specifics>
## Specific Ideas

- Install by absolute artifact path into a fresh environment, change to a neutral working directory, clear source-path variables, and assert the loaded package and core origins before collecting any semantic evidence.
- Emit one signed-by-content evidence JSON per artifact, then make a separate aggregation command validate the expected release matrix and render the release summary.
- Keep the conformance scenarios data-driven so source-pure and installed artifacts produce comparable redacted records without importing test helpers from the checkout at runtime.

</specifics>

<deferred>
## Deferred Ideas

- PyPI publishing and trusted-publisher configuration remain operational follow-up; this phase makes artifacts publishable but does not authorize external publication.
- New platforms, musllinux support, PyPy support, runtime build-info APIs, and public topology snapshot v2 remain outside v0.3.0.

</deferred>

---

*Phase: 20-installed-artifact-parity-release-proof*
*Context gathered: 2026-09-04*
