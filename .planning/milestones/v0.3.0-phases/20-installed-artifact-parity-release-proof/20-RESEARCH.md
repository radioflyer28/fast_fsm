# Phase 20: Installed Artifact Parity & Release Proof - Research

**Researched:** 2026-09-04
**Domain:** Python wheel/sdist verification, native CI, deterministic release evidence
**Confidence:** HIGH for repository architecture and locked behavior; MEDIUM for hosted-runner availability and the recommended cibuildwheel upgrade

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- PyPI publishing and trusted-publisher configuration remain operational follow-up; this phase makes artifacts publishable but does not authorize external publication.
- New platforms, musllinux support, PyPy support, runtime build-info APIs, and public topology snapshot v2 remain outside v0.3.0.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REL-01 | A maintainer can verify that package metadata, `fast_fsm.__version__`, changelog, documentation, and the release tag all identify v0.3.0 before publishing. | Two-stage identity gate: static release identity before build, then tag-to-verified-commit equality before release. |
| REL-03 | A requested compiled release fails when mypyc compilation fails or the produced wheel does not contain the expected native extension. | Explicit `compiled` intent re-raises build failure; archive and installed-origin checks independently reject a missing native module. |
| REL-07 | CI verifies installed pure and compiled artifacts rather than relying only on imports from the source checkout. | Exact-path fresh-environment installer, neutral working directory, containment checks, and native verification matrix. |
| TEST-01 | One parameterized conformance suite exercises equivalent sync, async, builder, declarative, pure-source, and compiled behavior for the hardened contracts. | A data-driven scenario oracle emits normalized records shared by all modes. |
| TEST-03 | Compiled-wheel verification runs substantive behavior tests on supported native targets rather than a smoke import alone. | Every native compiled record must run the full hardened conformance inventory and upload its record. |
| TEST-04 | Release verification asserts installed module origin, metadata version, architecture, semantic parity, and intended artifact type. | Installed probe plus strict evidence aggregation binds runtime identity to artifact SHA-256 and expected matrix cell. |
| TEST-05 | Every performance-sensitive `core.py` phase measures compiled and pure-Python overhead before its design is frozen. | Consolidate Phase 16–19 command/environment evidence into the manifest, and label it historical rather than installed proof. |
| TEST-06 | Compiled `trigger()` throughput remains at least 200,000 operations/sec after lifecycle and ownership hardening. | Run a stable multi-sample benchmark inside the installed compiled environment after native-origin assertion. |
| TEST-07 | Core runtime operations remain O(1), while diagnostic APIs document and enforce their separate complexity and budget contracts. | Add invariant/size-scaling tests for the four named runtime operations and retain exact boundary tests for deterministic diagnostic limits. |
</phase_requirements>

## Summary

Phase 20 should be planned as an evidence-system integration phase, not as another source-test phase. The repository already has build intent resolution, archive inspection, deterministic JSON, a pure-source preflight, native source probes, hardened Phase 16–19 tests, and a release workflow. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:86-105] The missing seam is an exact-artifact verifier that creates a fresh environment, installs the named artifact, runs the same deterministic semantic oracle outside the checkout, and emits evidence that a strict release-wide aggregator can reconcile. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-42]

The most important fail-closed change is in packaging: the exact build modes are `"auto"`, `"pure"`, and `"compiled"`, selected by `"FAST_FSM_BUILD_MODE"`, while current `setup.py` catches every compilation exception and leaves `ext_modules` empty even for compiled intent. [VERIFIED: tools/build_modes.py:9-18] [VERIFIED: setup.py:23-49] Preserve optional fallback only for `auto`; explicit `compiled` must propagate the failure, and a second post-build/post-install check must reject an artifact without native `fast_fsm.core`. The current release job publishes after build completion and archive collection, while cross-built Linux aarch64 and macOS x86_64 tests are explicitly skipped. [VERIFIED: .github/workflows/release.yml:45-81] [VERIFIED: .github/workflows/release.yml:114-145] Therefore, release creation must depend on verified evidence aggregation rather than directly on builders.

The conformance oracle should contain stable scenario inputs and normalized outputs for graph/guard, lifecycle/history, ownership/cancellation, diagnostics, output grammar, and logging. It should not import test helpers from the checkout when run against an installed artifact. Each record should bind a suite-content digest and semantic result digest to artifact bytes, runtime identity, build intent, commit, and tag. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-42] Pure observations and historical phase measurements remain evidence, but only a native installed compiled measurement can satisfy the fixed floor. [VERIFIED: .planning/REQUIREMENTS.md:70-78]

**Primary recommendation:** Extend `tools/release_evidence.py` into one fail-closed artifact verification/aggregation entry point, backed by a checkout-independent conformance collector, and place its complete-matrix aggregate between artifact builds and `github_release`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Explicit pure/compiled build semantics | Build backend (`setup.py`) | Build-mode selector | `setup.py` is solely responsible for `ext_modules`, while the selector owns the exact intent vocabulary. [VERIFIED: setup.py:14-49] [VERIFIED: tools/build_modes.py:9-18] |
| Artifact archive identity | Verification CLI | Wheel/sdist formats | Existing `inspect_wheel()` parses filename, metadata, tags, and native members and rejects contradictions. [VERIFIED: tools/release_evidence.py:257-431] |
| Installed identity and semantic proof | Fresh artifact environment | Verification CLI | The installed interpreter must be the source of metadata, module origins, conformance, and measurements; the parent CLI binds those facts to artifact bytes. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-35] |
| Native execution coverage | CI runner matrix | Evidence aggregator | Cross-build output is not proof until executed on a matching native architecture. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:23-26] |
| Completeness and parity | Evidence aggregator | CI workflow | The aggregator compares actual records against a canonical expected matrix and semantic oracle digest. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-36] |
| Publish authorization | GitHub release job | Aggregated evidence | The write-capable job must have only the verified aggregate as its release prerequisite. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:38-42] |

## Project Constraints (from AGENTS.md)

- Use `bd` for all task tracking and use `--json` for programmatic operations; do not introduce Markdown TODO tracking or an external tracker. [VERIFIED: AGENTS.md:19-21] [VERIFIED: AGENTS.md:74-99]
- Use `uv` for Python/package/test commands; do not invoke `python`, `pip`, or `python -m pytest` directly in project workflows. [VERIFIED: .github/copilot-instructions.md:32-39]
- Keep compiled `trigger()` at or above `200,000` operations/second and keep `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()` O(1). The exact values are: `"≥ 200,000 ops/sec"` and `"trigger(), can_trigger(), add_state(), add_transition()"`. [VERIFIED: .github/copilot-instructions.md:40-48]
- Run tests sequentially; targeted tests are the development loop, and the full suite command is `"uv run pytest tests/ -x -q"` once before push. [VERIFIED: .github/copilot-instructions.md:55-61]
- Keep mypy blocking and ty independently visible/advisory. [VERIFIED: .github/copilot-instructions.md:206-221]
- Preserve condition/callback `*args, **kwargs`, existing constructor behavior, and the public-symbol deprecation policy. [VERIFIED: .github/copilot-instructions.md:50-53]
- Compile only `"src/fast_fsm/core.py"`; keep `conditions.py` and `condition_templates.py` interpreted and support both compiled and uncompiled operation. [VERIFIED: setup.py:16-39] [VERIFIED: .github/copilot-instructions.md:328-330]
- Keep the single runtime dependency `"mypy-extensions"`; verification tooling belongs in development/release groups or the standard library. [VERIFIED: pyproject.toml:1-9] [VERIFIED: .github/copilot-instructions.md:328-330]
- Sphinx documentation builds and doctests are required when documentation changes. [VERIFIED: .github/copilot-instructions.md:254-281]
- Stage only explicit task paths in a dirty worktree, and do not use `git add .` or `git add -A`. [VERIFIED: .github/copilot-instructions.md:104-113]
- Repository sessions normally require committing and pushing, but this delegated research task is explicitly scoped to writing the research artifact only. [VERIFIED: AGENTS.md:103-127]

**Constraint conflict to resolve before release:** the instructions name exactly `"CompiledFuncCondition"` and `"TransitionError"` as the two measured slots exceptions, while the current evidence registry contains the verbatim keys `"fast_fsm.conditions.CompiledFuncCondition"`, `"fast_fsm.core.TransitionError"`, and `"fast_fsm._diagnostics.DiagnosticBudgetExceeded"`. [VERIFIED: .github/copilot-instructions.md:40-45] [VERIFIED: tools/release_evidence.py:49-60] Phase 20 should not silently choose one authority: add a small prerequisite that reconciles the instructions/ADR/evidence registry, then use the reconciled registry in final release proof.

## Standard Stack

### Core

| Component | Version / contract | Purpose | Why Standard |
|-----------|--------------------|---------|--------------|
| Python `venv` orchestration through uv | uv `"0.12.6"`; Python `">=3.10"` | Create a fresh interpreter environment and install one exact local artifact | These values are already pinned/declared by the project, and uv supports selecting the target interpreter for package installation. [VERIFIED: tools/release_evidence.py:35-39] [VERIFIED: pyproject.toml:1-9] [CITED: https://docs.astral.sh/uv/pip/environments/] |
| `setuptools.build_meta` | setuptools `"80.9.0"`, wheel `"0.45.1"`, mypy/mypyc `"1.17.1"` | Reproducible wheel/sdist and selective mypyc builds | These are the exact existing build-system and release-group pins. [VERIFIED: pyproject.toml:22-26] [VERIFIED: pyproject.toml:43-45] |
| `tools/release_evidence.py` | current schema `1`, evolve for Phase 20 | Archive inspection, installed probe orchestration, deterministic records, aggregation | It already owns `"PACKAGE_NAME = \"fast_fsm\""`, `"CORE_MODULE_NAME = f\"{PACKAGE_NAME}.core\""`, strict JSON parsing, deterministic writes, and wheel identity checks. [VERIFIED: tools/release_evidence.py:35-41] [VERIFIED: tools/release_evidence.py:2731-2773] |
| pytest | `"pytest>=8.4.1"`, pytest-asyncio `">=1.3.0"`, Hypothesis `">=6.136.6"` | Shared conformance and boundary tests | The test framework and plugins already exist in the development group; the phase should add no test framework. [VERIFIED: pyproject.toml:11-21] |
| cibuildwheel GitHub Action | recommend `v4.2.0` at `1828c10ab37f080699c7b81cea34097c684a7074` | Produce supported native wheels | The official action is already used, but the repository pin is `v2.22.0`; the recommended tag/SHA was verified against the official repository and should be covered by the existing immutable-action-pin test. [VERIFIED: .github/workflows/release.yml:52-76] [CITED: https://github.com/pypa/cibuildwheel/releases/tag/v4.2.0] |
| GitHub Actions artifacts and `needs` graph | pinned action SHAs already present | Move artifacts/evidence between native jobs and block release on the aggregate | Workflow artifacts are the official mechanism for sharing files between jobs; dependent jobs are skipped when a prerequisite fails unless conditional behavior overrides that default. [CITED: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts] [CITED: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs] |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| `packaging` | existing development lock | Parse wheel filenames, normalized names, versions, and tags | Retain the current archive-inspection implementation instead of parsing filenames by hand. [VERIFIED: tools/release_evidence.py:257-265] |
| Python stdlib `hashlib`, `importlib.metadata`, `importlib.machinery`, `json`, `tarfile`, `zipfile`, `tempfile`, `subprocess` | interpreter-provided | SHA-256 binding, runtime identity, native loader detection, strict evidence, safe isolation | Avoid a new runtime or release dependency; use argument-array subprocess calls and bounded archive validation. [VERIFIED: pyproject.toml:1-9] |
| Existing Phase 16 isolated verifier | repository tool | Model controlled environment cleanup, source/native origin checks, and suite inventories | Reuse its process-isolation ideas, but install exact artifacts instead of exporting source. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:89-99] |
| Taskfile | project task runner | Stable maintainer entry points for local subset and final gates | The repository declares Taskfile commands as workflow wrappers and release-evidence commands as authoritative. [VERIFIED: .github/copilot-instructions.md:21-29] [VERIFIED: .github/copilot-instructions.md:63-71] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extending `release_evidence.py` | A separate unrelated verifier | Rejected: it would split archive identity, manifest normalization, and regression rules across competing authorities. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:89-105] |
| Exact-path install into a uv environment | `uv sync` from the checkout | Rejected: a project sync can install the repository rather than the artifact under test, invalidating REL-07. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-25] |
| Native runner execution | QEMU/cross-build smoke result | Cross-build remains useful for production, but cannot satisfy D-03 until a matching native runner executes the artifact. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:23-26] |
| Structured scenario records | Whole-object `repr` or raw exception snapshots | Rejected because paths, addresses, timings, payloads, and representation differences are volatile or sensitive. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-31] |

**Installation:** No new Python package is required. Preserve the locked environment with `uv sync --locked --all-groups`; artifact environments should install only the exact artifact path plus locked test-only inputs required by the standalone verifier. [VERIFIED: .github/copilot-instructions.md:328-330]

**Version verification:** Existing build pins are exactly `"setuptools==80.9.0"`, `"wheel==0.45.1"`, and `"mypy[mypyc]==1.17.1"`. [VERIFIED: pyproject.toml:22-26] The proposed action ref was verified from the official cibuildwheel repository; if the upgrade is accepted during implementation, update the repository's immutable-action regression expectation in the same task. [CITED: https://github.com/pypa/cibuildwheel/releases/tag/v4.2.0]

## Package Legitimacy Audit

The phase is dependency-neutral: it should not add an external PyPI/npm/crates package. The existing project and release pins remain the stack, so the package-legitimacy installation gate is not triggered. [VERIFIED: pyproject.toml:1-45]

| Package/action | Registry/source | Verdict | Disposition |
|----------------|-----------------|---------|-------------|
| Existing Python dependencies | Existing `pyproject.toml` and lock | Existing project dependency set | Retain; do not add packages. [VERIFIED: pyproject.toml:7-45] |
| `pypa/cibuildwheel` action | Official GitHub repository | Official, immutable tag SHA verified | Upgrade action pin only; validate changed defaults in CI. [CITED: https://github.com/pypa/cibuildwheel/releases/tag/v4.2.0] |

**Packages removed due to SLOP verdict:** none.

**Packages flagged as suspicious:** none.

## Architecture Patterns

### System Architecture Diagram

```text
tag/commit + locked source
          |
          v
 quality and static v0.3.0 identity gate
          |
          +-----------------------+-------------------------+
          |                       |                         |
          v                       v                         v
 universal pure wheel      compiled wheel matrix          sdist
          |                (explicit compiled)              |
          |                       |                  archive validation
          |                       |                         |
          |                       |                 explicit downstream
          |                       |                 pure + compiled wheels
          +-----------------------+-------------------------+
                                  |
                         exact artifact pathname
                                  v
                   fresh uv environment, neutral cwd
                                  |
                   identity/origin/type containment gate
                                  |
                    shared deterministic conformance oracle
                                  |
                 native compiled performance + complexity gates
                                  |
                     one JSON evidence record per run
                                  |
                 strict expected-matrix/parity aggregator
                                  |
                deterministic manifest + human summary
                                  |
                   tag == verified commit final gate
                                  |
                         GitHub release creation
```

### Recommended Project Structure

```text
tools/
├── release_evidence.py              # extend: artifact verify + aggregate authority
└── artifact_conformance.py          # recommended standalone collector [ASSUMED]
tests/
├── test_artifact_conformance.py     # source-mode oracle and record determinism [ASSUMED]
├── test_installed_artifacts.py      # isolation, identity, negative cases [ASSUMED]
├── test_release_evidence.py         # schema/matrix/release workflow regression
└── test_performance_benchmarks.py   # installed floor + O(1) invariant/scaling proof
.github/workflows/
└── release.yml                      # build -> native verify -> aggregate -> release
evidence/
└── release-baseline.json            # evolved deterministic release manifest
```

The two proposed test/module filenames are recommendations under D-05/D-09 discretion, not existing source-of-truth paths. [ASSUMED]

### Pattern 1: Parent Verifier + Checkout-Independent Child Probe

**What:** The parent process resolves and hashes one concrete archive, creates a temporary uv environment, installs by absolute path with project/config discovery disabled, copies or embeds the conformance collector into a neutral temporary directory, then invokes the installed interpreter. The child returns strict JSON only. The parent independently validates archive identity, expected intent, containment, and child schema before accepting the record. [CITED: https://docs.astral.sh/uv/reference/cli/] [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-35]

**When to use:** Every installed pure wheel, compiled wheel, and wheel derived from the sdist. The source-pure run calls the same collector through a source adapter, not a separate semantic test inventory. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-31]

**Required order:** hash/archive inspection → create fresh environment → exact-path install → assert distribution/package/core origins are inside the environment → assert pure/native type → run semantic scenarios → run performance only after native assertion → emit record. A failed earlier stage must prevent later claims. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-42]

### Pattern 2: Explicit Sdist Derivation Graph

An sdist is source that an installer/build frontend turns into a wheel before installation; it is not itself installed payload equivalent to a wheel. [CITED: https://packaging.python.org/en/latest/discussions/package-formats/] Plan three linked proofs: validate the sdist archive identity and required build inputs, derive a pure wheel under explicit `FAST_FSM_BUILD_MODE=pure`, derive a compiled wheel under explicit `FAST_FSM_BUILD_MODE=compiled`, then feed both children through the ordinary wheel verifier. Each derived record must carry the parent sdist filename/SHA-256 so the aggregator proves lineage. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-26]

### Pattern 3: One Canonical Expected Matrix

The current workflow declares CPython build selectors `"cp310-* cp311-* cp312-* cp313-* cp314-*"`, Linux architectures `"x86_64 aarch64"`, Windows `"AMD64"`, and macOS `"x86_64 arm64 universal2"`, with `"*musllinux*"` skipped. [VERIFIED: .github/workflows/release.yml:23-76] Encode the expected release matrix once in Python data, render/validate workflow configuration against it using the repository's existing CI-contract-test pattern, and make aggregation compare exact matrix keys rather than accepting all downloaded files. The aggregation key should distinguish artifact SHA/filename, CPython version, OS, machine architecture, asserted mode, and derivation parent where applicable. [ASSUMED]

Recommended native placement is Linux x86-64 on a standard Ubuntu runner, Linux arm64 on GitHub's public `ubuntu-24.04-arm` label, Windows AMD64 on a Windows x64 runner, macOS arm64 on an arm runner, and macOS x86-64 on `macos-15-intel`; hosted availability and repository entitlement must be exercised before locking the YAML. [CITED: https://docs.github.com/en/actions/reference/runners/github-hosted-runners]

A universal2 wheel must be executed once on each native macOS architecture, with two runtime evidence records bound to the same artifact SHA. [ASSUMED] A pure `py3-none-any` wheel should be installed under each supported CPython minor on one canonical OS because its compatibility claim spans Python 3, while compiled wheels require every produced native matrix cell. [CITED: https://packaging.python.org/en/latest/specifications/binary-distribution-format/]

### Pattern 4: Deterministic Semantic Oracle

Use stable scenario IDs, fixed inputs, explicit synchronization events for concurrency/cancellation, and allowlisted output fields. Normalize enums/exceptions/results to named scalar fields; sort unordered collections; record digests for large grammar output; and omit timestamps, elapsed time, absolute paths, object representations, exception addresses, raw args/kwargs, and user payloads from parity records. Performance observations live beside, not inside, the parity digest. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-42]

The scenario inventory must cover the exact hardened families: graph/guard invariants, lifecycle/result/history, sync/async equivalence, builder/declarative execution, ownership/reentry/cancellation, bounded diagnostics, grammar-safe Mermaid/PlantUML/JSON output, and redacted non-invasive logging. [VERIFIED: .planning/REQUIREMENTS.md:20-78] Record a digest of the conformance collector bytes or scenario-definition canonical JSON so every artifact proves that it ran the same oracle. [ASSUMED]

### Pattern 5: Two-Stage Release Identity

Before artifact build, assert the source-visible identity and claims are v0.3.0. At tag-triggered release time, additionally resolve the annotated/lightweight tag to a commit and compare it with the checked-out verified commit. Do not require the v0.3.0 tag to exist in ordinary pull-request CI; make tag equality a separate tag-time gate. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-42]

Current identity is not ready: project metadata says `version = "0.2.2"`, Sphinx says `release = "0.1.0"`, `fast_fsm.__version__` is read from installed metadata with fallback `"unknown"`, and the tracked manifest says `"distribution_version": "0.2.2"` with `"schema_version": 1`. [VERIFIED: pyproject.toml:1-9] [VERIFIED: docs/conf.py:10-15] [VERIFIED: src/fast_fsm/__init__.py:61-66] [VERIFIED: evidence/release-baseline.json:75-79] Plan one coordinated identity task that updates package metadata, changelog release section, both Sphinx `version`/`release` values or a single authoritative derivation, documentation claims, schema, and regression fixtures.

### Pattern 6: Native Performance and Complexity Evidence

Run warmup followed by at least three measured samples inside the installed compiled environment and gate on a predefined robust statistic (recommended median) against exactly `200000` operations/second. [ASSUMED] Record all samples, statistic, iterations, implementation, Python, OS, machine, and asserted native origin; pure measurements are observations only. The current collector has only one source-pure timing measurement with exact fields `"mode": "pure"`, `"operations"`, `"warmup_operations"`, `"elapsed_seconds"`, and `"ops_per_second"`, so it cannot satisfy TEST-06. [VERIFIED: tools/release_evidence.py:2554-2604]

For TEST-07, prefer deterministic structure/invariant assertions for `trigger()`, `can_trigger()`, `add_state()`, and `add_transition()` plus a coarse multi-size scaling backstop; a single wall-clock timing at one graph size is not O(1) proof. [VERIFIED: .github/copilot-instructions.md:40-48] Diagnostic work belongs in its current separate deterministic budget tests, not in the hot-path benchmark. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:38-42]

### Anti-Patterns to Avoid

- **Silent compiled fallback:** Catching mypyc failure and emitting a pure artifact under compiled intent defeats REL-03; only `auto` may warn/fallback. Current code does catch all compilation exceptions. [VERIFIED: setup.py:23-49]
- **Archive-only certification:** Wheel tags and native members prove packaging shape, not the behavior or actual imported module. Existing inspection stops at archive contents. [VERIFIED: tools/release_evidence.py:321-431]
- **Checkout contamination:** Running pytest from the repository or leaving `PYTHONPATH`/editable metadata active can certify source rather than the installed archive. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-25]
- **Treating a cross-build skip as proof:** Current release CI skips `"cp*-*linux_aarch64 cp*-macosx_x86_64"`; those artifacts need matching native verification jobs. [VERIFIED: .github/workflows/release.yml:66-73]
- **Completeness by glob:** Downloading `wheels-*` does not prove the expected matrix; require an explicit one-record-per-cell contract. Current release collection uses `pattern: wheels-*`. [VERIFIED: .github/workflows/release.yml:127-138]
- **One-architecture universal2 proof:** One successful import does not prove both slices of a multi-architecture wheel. [ASSUMED]
- **Volatile parity fields:** Paths, timings, reprs, addresses, and raw payloads make comparisons flaky or disclose data. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-31]
- **Performance before origin assertion:** A fast source/native shadow can produce a false passing floor. Origin/type validation must precede measurement. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-42]
- **Digest as authenticity:** SHA-256 binds evidence to bytes but does not prove publisher identity; do not describe it as a signature. [ASSUMED]
- **`always()` on release:** It could allow a write-capable release job after failed prerequisites; use an ordinary successful `needs` path. [CITED: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs]
- **Unreviewed cibuildwheel major upgrade:** v4 changed platform repair/audit behavior; if upgrading, inspect the wheel tags/native contents and update workflow regression tests. [CITED: https://github.com/pypa/cibuildwheel/releases/tag/v4.0.0]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Wheel name/tag parsing | String splitting and platform guesses | Existing `packaging.utils.parse_wheel_filename` seam | Wheel filenames contain normalized distribution/version/build and compatibility tags; the current tool already validates these consistently. [VERIFIED: tools/release_evidence.py:257-265] [CITED: https://packaging.python.org/en/latest/specifications/binary-distribution-format/] |
| Installation environment | Manipulating `sys.path` in the checkout | Fresh uv environment plus exact local artifact path | Isolation must prove the installed artifact, not simulate it. [CITED: https://docs.astral.sh/uv/pip/environments/] |
| Native-module detection | Only suffix text checks for `.so`/`.pyd` | `importlib` loader/spec plus `EXTENSION_SUFFIXES`, confirmed by resolved origin | Loader/type and containment are stronger than a filename substring alone. [ASSUMED] |
| Semantic parity | Duplicated pure/compiled smoke scripts | Shared data-driven conformance collector | A single oracle prevents mode drift and provides field-level diffs. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-31] |
| Matrix completeness | Count files or trust artifact globs | Canonical expected matrix + exact-key set reconciliation | Counts cannot detect a duplicate replacing a missing target. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-35] |
| Release evidence serialization | Ad hoc `repr`/YAML output | Existing strict, sorted JSON serializer/check path | The current reader rejects non-standard numbers and the writer has deterministic bytes. [VERIFIED: tools/release_evidence.py:2731-2773] |
| Cryptographic digest | Custom checksum | stdlib SHA-256 | The decision explicitly requires SHA-256 and the standard implementation avoids custom cryptography. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-35] |

**Key insight:** This phase is trustworthy only if one chain binds source identity → exact archive bytes → installed runtime origin → semantic record → native measurement → complete matrix → release authorization. Any independent smoke test or narrative claim outside that chain is supporting evidence, not publish proof.

## Common Pitfalls

### Pitfall 1: Explicit Compiled Mode Still Succeeds Pure

**What goes wrong:** mypyc raises, `setup.py` warns, the build succeeds with no extension, and later jobs treat the wheel as compiled.

**Why it happens:** Current code applies the same catch-and-fallback behavior to both `auto` and `compiled`. [VERIFIED: setup.py:23-49]

**How to avoid:** Re-raise for exact enum value `BuildMode.COMPILED`; retain warning/fallback only for `BuildMode.AUTO`; add negative tests that force import/mypycify failure; keep independent archive and installed-origin assertions.

**Warning signs:** A compiled job produces `py3-none-any`, `native_members` is empty, or installed `fast_fsm.core` resolves to `.py`.

### Pitfall 2: Fresh Environment, Dirty Import Resolution

**What goes wrong:** A new venv still imports from the checkout because cwd, `PYTHONPATH`, editable metadata, or a copied test helper points back to it.

**Why it happens:** Environment creation alone does not control working directory and module search inputs.

**How to avoid:** Resolve artifact before leaving the checkout, use a neutral temporary cwd, clear project/source path variables, invoke the environment's absolute interpreter, assert package/core origins are descendants of that environment, and fail if editable/direct-url metadata identifies the checkout. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-25]

**Warning signs:** `fast_fsm.__file__` contains the repository path, `core.__file__` is outside site-packages, or results change when cwd changes.

### Pitfall 3: Builder Output Is Mistaken for Runtime Proof

**What goes wrong:** QEMU/cross-compiled wheels are uploaded and counted despite skipped tests.

**Why it happens:** Build and verify are conflated in one matrix job.

**How to avoid:** Emit build artifacts separately, route every artifact to a matching native execution cell, and let aggregation accept only runtime evidence. Current skips are exact values `"cp*-*linux_aarch64 cp*-macosx_x86_64"`. [VERIFIED: .github/workflows/release.yml:66-73]

**Warning signs:** An expected release wheel has no evidence JSON, or an evidence record's runtime `machine` contradicts its wheel platform tag.

### Pitfall 4: Sdist Is Verified Only as a Tarball

**What goes wrong:** The archive looks correct, but explicit compiled downstream build silently falls back or omits setup tooling.

**Why it happens:** Archive inspection is cheaper than executing both requested derivations.

**How to avoid:** Treat archive inspection, explicit pure derivation, and explicit compiled derivation as three required linked results. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-26]

**Warning signs:** Sdist evidence has no child wheel SHA/origin/conformance record, or a child build used `auto`.

### Pitfall 5: Evidence Is Deterministic but Incomplete

**What goes wrong:** JSON sorting succeeds while one target is absent or duplicated.

**Why it happens:** Determinism and completeness are separate properties.

**How to avoid:** Compare expected and actual key sets, reject normalized filename/SHA duplicates, reject unexpected records, enforce one consistent version/commit/tag/suite digest, then render the human summary from the accepted structure. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-36]

**Warning signs:** Aggregation discovers its matrix from downloaded files, or merely checks a record count.

### Pitfall 6: Timing Is Used as Complexity Proof

**What goes wrong:** A fast constant-sized benchmark is reported as proof that operations are O(1).

**Why it happens:** Performance and asymptotic complexity are collapsed into one metric.

**How to avoid:** Use data-structure/instrumentation invariants and multiple graph sizes for the four exact core operations; keep diagnostic budget boundaries and throughput as separate gates. [VERIFIED: .github/copilot-instructions.md:40-48]

**Warning signs:** Only one topology size is measured, or diagnostics run inside the transition benchmark.

### Pitfall 7: Version Gate Cannot Run in Both PR and Tag CI

**What goes wrong:** PRs fail because the future tag does not exist, or the tag workflow fails to compare the tag with the verified commit.

**Why it happens:** Static source identity and tag provenance are implemented as one unconditional check.

**How to avoid:** Separate pre-tag v0.3.0 alignment from tag-time ref resolution equality. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-42]

**Warning signs:** A check accepts any `v*` tag, or only compares tag text with package version.

## Code Examples

Verified/recommended patterns for planning; exact new command/field names remain implementation discretion.

### Fail Closed Only for Explicit Compiled Intent

```python
# Source contract: tools/build_modes.py:9-18 and setup.py:27-49
try:
    ext_modules = mypycify(["src/fast_fsm/core.py"], ...)
except Exception:
    if build_mode is BuildMode.COMPILED:
        raise
    # BuildMode.AUTO alone may retain the documented warning/fallback.
```

The discrete source values used above are quoted verbatim as `COMPILED = "compiled"`, `AUTO = "auto"`, and `["src/fast_fsm/core.py"]`. [VERIFIED: tools/build_modes.py:9-14] [VERIFIED: setup.py:27-39]

### Exact-Artifact Installation Skeleton

```python
# Official uv patterns: https://docs.astral.sh/uv/pip/environments/
# and https://docs.astral.sh/uv/reference/cli/
artifact = supplied_artifact.resolve(strict=True)
subprocess.run(["uv", "venv", str(env_dir), "--python", python_spec], check=True)
subprocess.run(
    ["uv", "pip", "install", "--python", str(env_python),
     "--no-project", "--no-config", str(artifact)],
    cwd=neutral_dir,
    env=sanitized_environment,
    check=True,
)
subprocess.run(
    [str(env_python), str(copied_probe), "--expected-mode", expected_mode],
    cwd=neutral_dir,
    env=sanitized_environment,
    check=True,
)
```

`"FAST_FSM_BUILD_MODE"` with exact requested values `"pure"` or `"compiled"` must be present for downstream builds, never `"auto"` when collecting compiled proof. [VERIFIED: tools/build_modes.py:9-18] [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-26]

### Strict Matrix Reconciliation Skeleton

```python
# Recommended shape [ASSUMED]; behavior is locked by D-09.
expected_keys = set(expected_matrix)
actual_by_key = index_unique(records)
missing = expected_keys - actual_by_key.keys()
unexpected = actual_by_key.keys() - expected_keys
if missing or unexpected:
    raise EvidenceError(render_matrix_difference(missing, unexpected))
assert_one_value(records, "release.version", "0.3.0")
assert_one_value(records, "provenance.commit")
assert_one_value(records, "conformance.suite_sha256")
compare_scenario_records(records)
```

The exact required release value is `"v0.3.0"` at the tag surface and `"0.3.0"` in package metadata. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-36]

## State of the Art

| Old/current approach | Recommended current approach | Change driver | Impact |
|----------------------|------------------------------|---------------|--------|
| Inspect wheel archive metadata/native members | Inspect, install exact bytes, assert runtime containment/type, then run full conformance | REL-07/TEST-04 | Archive identity becomes one stage of end-to-end installed proof. [VERIFIED: tools/release_evidence.py:321-431] |
| cibuildwheel smoke runs basic/async tests and skips cross-built targets | Shared conformance on matching native runners for every published compiled artifact | D-03/TEST-03 | No artifact is behavior-proven merely because it built. [VERIFIED: .github/workflows/release.yml:66-73] |
| Release depends directly on quality/build jobs | Release depends on strict aggregate after native verification, identity, parity, and performance | D-14 | Partial or advisory evidence cannot publish. [VERIFIED: .github/workflows/release.yml:114-145] |
| Source-pure one-sample benchmark stored under compiled floor | Installed compiled multi-sample gate; pure measurement labeled observation | D-11/TEST-06 | The numeric floor is enforced on the artifact users receive. [VERIFIED: tools/release_evidence.py:2554-2663] |
| Repository action pin `v2.22.0` | Recommended official cibuildwheel `v4.2.0` immutable SHA after regression review | Supported CPython/native build maintenance | Brings the wheel builder current, but requires explicit validation of v4 repair/audit behavior. [VERIFIED: .github/workflows/release.yml:52-76] [CITED: https://github.com/pypa/cibuildwheel/releases/tag/v4.2.0] |

**Deprecated/outdated:**

- Treating source in-place compilation as installed compiled proof is explicitly insufficient for Phase 20. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:95-99]
- The current `github_release.needs` value `[quality_gate, build_wheels, build_sdist]` is incomplete for D-14. [VERIFIED: .github/workflows/release.yml:114-120]
- The comment that both auto and compiled retain optional fallback must be revised when REL-03 is implemented. [VERIFIED: setup.py:23-26]

## Historical Evidence Consolidation

TEST-05 should be satisfied by inventorying the existing Phase 16–19 performance artifacts in the final manifest with file SHA-256 and categorical provenance for each field: preserve an exact command, build mode, threshold/pass outcome, measurement/counter, environment fact, or commit only when the record captured it, and represent absent original detail explicitly as unavailable. Do not infer historical precision or use a later rerun to overwrite the original record. D-13's exact command/environment requirement is enforced for the new final installed Phase 20 rerun, which remains distinct from historical source evidence. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:38-42]

Plan the consolidation as a deterministic input allowlist, not a recursive glob. The existing tracked baseline currently records exact test values `"collected": 1503`, `"passed": 1503`, `"failed": 0`, `"errors": 0`, `"skipped": 0`, coverage values `"core_percent": 97.52` and `"total_percent": 98.11`, and only a pure observation; those are historical observations, not durable future minimums or compiled installed proof. [VERIFIED: evidence/release-baseline.json:39-73]

The initial allowlist should name the exact existing evidence paths `".planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md"`, `".planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md"`, `".planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md"`, and `".planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md"`. Across the set, the files record some pure/compiled origin, environment, command, threshold/pass, measurement, or deterministic-counter facts; they do not establish every exact field uniformly, so the schema must accept explicit unavailability. [VERIFIED: .planning/phases/16-canonical-graph-dispatch-invariants/16-PERFORMANCE-EVIDENCE.md:7-28] [VERIFIED: .planning/phases/17-atomic-transition-lifecycle/17-PERFORMANCE-EVIDENCE.md:1-24] [VERIFIED: .planning/phases/18-safe-ownership-concurrency/18-PERFORMANCE-EVIDENCE.md:1-26] [VERIFIED: .planning/phases/19-bounded-diagnostics-safe-output/19-PERFORMANCE-EVIDENCE.md:1-30]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Proposed standalone filenames `tools/artifact_conformance.py`, `tests/test_artifact_conformance.py`, and `tests/test_installed_artifacts.py`. | Project Structure | Low; names are explicitly agent discretion and can be changed without altering behavior. |
| A2 | Matrix key field names and nested evidence names shown in the aggregation skeleton. | Canonical Matrix / Code Examples | Low; exact schema ordering/types are agent discretion, while required content is locked. |
| A3 | Universal2 should produce one evidence run on each native macOS architecture. | Canonical Matrix | Medium; omitting one slice weakens execution proof, but CI/artifact routing may choose a different equivalent proof. |
| A4 | Use median of at least three samples for the compiled performance gate. | Native Performance | Low; the exact stable statistic is agent discretion. |
| A5 | SHA-256 provides byte identity/integrity binding, not publisher authenticity. | Anti-Patterns / Security | Low; wording matters for release claims, but no signing system is in scope. |
| A6 | Use `importlib` loader/spec plus `EXTENSION_SUFFIXES` for native detection. | Don't Hand-Roll | Low; an equivalent platform-correct origin/type assertion is acceptable. |
| A7 | Bind every artifact record to a digest of the exact conformance oracle definition. | Deterministic Semantic Oracle | Low; another deterministic suite-identity mechanism could provide equivalent proof. |
| A8 | Authentication/session ASVS categories do not apply, while stdlib hashing and bounded safe archive extraction are the appropriate controls. | Security Domain | Low; a project-specific security review may classify workflow identity under a different category without changing the required controls. |

## Open Questions

1. **Are all recommended native hosted runner labels enabled for this repository?**
   - **Status: RESOLVED AS AN EVIDENCE-ONLY RUN PLUS FAIL-CLOSED EXTERNAL PRE-RELEASE CHECKPOINT.** Availability is intentionally not assumed or claimed by planning. Plan 20-06 adds a manual/reusable workflow that resolves an input ref to one exact SHA, executes the full native `release` matrix, exposes terminal evidence, and contains no release-capable job or write permission. After a maintainer separately authorizes that run, `task release-hosted-prerelease-check FAST_FSM_HOSTED_RUN_ID=<authorized-run-id> FAST_FSM_EXPECTED_SHA=<40-char-sha>` reads its terminal metadata and downloaded evidence before any `v0.3.0` tag is created. An unavailable/queued-without-capacity runner or missing evidence cell blocks tagging; cross-build output is never substituted. Planning does not dispatch CI.
   - What we know: GitHub documents public Linux arm64 and separate macOS Intel/arm labels. [CITED: https://docs.github.com/en/actions/reference/runners/github-hosted-runners]
   - What's unclear: Repository plan, quota, and label entitlement are external account state.
   - Resolution: The maintainer must authorize the hosted run as a separate pre-release operation, then pass the exact-SHA read-only checkpoint. No runner success is recorded in this research or claimed by local workflow tests.

2. **Should cibuildwheel be upgraded in this phase?**
   - **Status: RESOLVED — YES.** Upgrade in Plan 20-06 Task 1 to official cibuildwheel v4.2.0 at immutable SHA `1828c10ab37f080699c7b81cea34097c684a7074`, with isolated workflow/tag/native-member regression coverage.
   - What we know: Release CI pins `v2.22.0`; official `v4.2.0` exists at the verified immutable tag SHA. [VERIFIED: .github/workflows/release.yml:52-76] [CITED: https://github.com/pypa/cibuildwheel/releases/tag/v4.2.0]
   - Resolution: The phase owns the artifact matrix, so the upgrade is included and isolated inside the workflow-contract task; immutable pin tests and wheel tag/content checks must pass before the change is accepted.

3. **What calendar date belongs in the v0.3.0 changelog section?**
   - **Status: RESOLVED — KEEP `UNRELEASED` DURING IMPLEMENTATION.** A concrete UTC release date is supplied only in the separately authorized tag-time operation after the hosted-native checkpoint passes; static identity accepts the explicit unreleased marker and tag-time identity rejects it.
   - What we know: Every identity surface must say v0.3.0 before release. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-36]
   - Resolution: Planning does not invent a future calendar date. The changelog remains explicitly unreleased until the authorized release operator supplies the actual date immediately before the non-mutating tag identity check and later tag creation.

4. **Which slots-exception registry is authoritative at release?**
   - **Status: RESOLVED — THE EXECUTABLE THREE-ENTRY REGISTRY IS AUTHORITATIVE.** Plan 20-04 Task 3 reconciles contributor instructions and SPR text to `CompiledFuncCondition`, `TransitionError`, and the ADR-006-accepted `DiagnosticBudgetExceeded`, without changing runtime layout or the `core.py`-only compilation boundary.
   - What we know: repository instructions name two exceptions, but executable evidence names three exact qualified values: `"fast_fsm.conditions.CompiledFuncCondition"`, `"fast_fsm.core.TransitionError"`, and `"fast_fsm._diagnostics.DiagnosticBudgetExceeded"`. [VERIFIED: .github/copilot-instructions.md:40-45] [VERIFIED: tools/release_evidence.py:49-60]
   - Resolution: ADR-006 and the shipped slotted RuntimeError establish the third measured exception as an accepted runtime fact. Documentation is the stale side and is updated in the same task as the executable evidence check.

## Environment Availability

The local research host is macOS arm64 and can exercise the canonical pure path plus one native compiled slice; it cannot locally prove Windows, Linux, or all Python minor/architecture cells. [VERIFIED: local command audit 2026-09-04]

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| uv | all Python orchestration | ✓ | `0.12.6` | none; required project tool [VERIFIED: local command audit 2026-09-04] |
| Python | source/local artifact checks | ✓ | project venv `3.12.10` | Hosted matrix for 3.10, 3.11, 3.13, 3.14 [VERIFIED: local command audit 2026-09-04] |
| pytest | conformance/tests | ✓ | `8.4.1` | none [VERIFIED: local command audit 2026-09-04] |
| Task | documented task entry points | ✓ | `3.53.1` | direct uv tool commands for diagnosis only [VERIFIED: local command audit 2026-09-04] |
| C compiler | local mypyc build | ✓ | Apple clang `21.0.0` | hosted native compiler [VERIFIED: local command audit 2026-09-04] |
| Docker | cibuildwheel/Linux investigation | ✓ | `29.7.2` | hosted GitHub Actions [VERIFIED: local command audit 2026-09-04] |
| Git/GitHub CLI | tag/commit and workflow diagnostics | ✓ | git `2.55.0`, gh `2.98.0` | GitHub web/API [VERIFIED: local command audit 2026-09-04] |
| Native Linux x64/arm64, Windows AMD64, macOS Intel | full release proof | ✗ locally | — | Hosted native runner matrix [CITED: https://docs.github.com/en/actions/reference/runners/github-hosted-runners] |

**Missing dependencies with no fallback:** none in the repository tooling; complete matrix execution requires hosted/native CI access.

**Missing dependencies with fallback:** non-local Python minors and non-arm-mac platforms use the hosted CI matrix.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=8.4.1`, pytest-asyncio `>=1.3.0`, Hypothesis `>=6.136.6` [VERIFIED: pyproject.toml:11-21] |
| Config file | `pyproject.toml`; exact addopts are `"-x"`, `"-q"`, `"--tb=short"`, `"--strict-markers"`, and asyncio mode is `"auto"`. [VERIFIED: pyproject.toml:56-73] |
| Quick run command | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py -x -q` [ASSUMED] |
| Conformance quick command | `uv run pytest tests/test_artifact_conformance.py -x -q` [ASSUMED: Wave 0 filename] |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: .github/copilot-instructions.md:55-61] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REL-01 | All static identity surfaces are 0.3.0; tag resolves to verified commit | unit + workflow integration | `uv run pytest tests/test_release_evidence.py -x -q` | ✅ extend existing |
| REL-03 | Explicit compiled build errors propagate; pure/auto remain intentional; missing native wheel rejected | unit + build integration | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py -x -q` | ✅ extend existing |
| REL-07 | Exact pure/compiled artifacts install in isolated envs with checkout excluded | integration | `uv run pytest tests/test_installed_artifacts.py -x -q` | ❌ Wave 0 [ASSUMED filename] |
| TEST-01 | Same scenario set produces equal normalized records for source-pure and installed modes | unit + integration | `uv run pytest tests/test_artifact_conformance.py -x -q` | ❌ Wave 0 [ASSUMED filename] |
| TEST-03 | Every native compiled target runs substantive conformance | workflow contract + native CI | `uv run pytest tests/test_release_evidence.py -x -q` plus release workflow | ✅ extend existing / CI execution |
| TEST-04 | Origin, metadata, architecture, type, intent, version, and parity are fail-closed | unit + integration | `uv run pytest tests/test_installed_artifacts.py tests/test_release_evidence.py -x -q` | ❌/✅ |
| TEST-05 | Phase 16–19 performance evidence inventory is complete and hashed | unit | `uv run pytest tests/test_release_evidence.py -x -q` | ✅ extend existing |
| TEST-06 | Installed native compiled median remains ≥200,000 trigger ops/sec | slow native benchmark | `uv run pytest tests/test_performance_benchmarks.py -m slow -x -q` | ✅ extend existing |
| TEST-07 | Four core operations remain O(1); diagnostic limit boundaries fail explicitly | invariant/scaling + unit | `uv run pytest tests/test_performance_benchmarks.py tests/test_diagnostic_contracts.py -x -q` | ✅ extend existing |

### Sampling Rate

- **Per task commit:** targeted existing/new test file through `uv run pytest ... -x -q`; tests remain sequential. [VERIFIED: .github/copilot-instructions.md:55-61]
- **Per wave merge:** `uv run pytest tests/ -x -q` plus the non-destructive pure-source check when packaging/import logic changes. [VERIFIED: .github/copilot-instructions.md:55-71]
- **Phase gate:** Full quality suite, source conformance, artifact builds, native artifact verification, aggregate parity/identity/performance, and tag equality all green before release creation. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:38-42]

### Wave 0 Gaps

- Create a checkout-independent conformance collector and its deterministic-record tests. [ASSUMED filenames]
- Create installed-artifact isolation tests covering source-path leakage, editable/direct-url provenance, stale native shadow, wrong mode, wrong architecture/version, and exact artifact SHA. [ASSUMED filename]
- Add sdist archive/derivation fixtures and forced compiled-failure fixtures to existing packaging tests.
- Add aggregate-matrix fixtures for duplicate, missing, unexpected, mixed version/commit/tag/suite digest, malformed JSON, and SHA mismatch.
- Add workflow contract tests proving every builder produces evidence, skipped cross-builds have native consumers, and `github_release` depends on the aggregate.
- Add deterministic O(1) invariant/multi-size tests for all four named core operations, preserving diagnostic budget boundary tests separately.

## Security Domain

Security enforcement is enabled because `.planning/config.json` contains no `"security_enforcement"` key; Nyquist validation is explicitly `"nyquist_validation": true`. [VERIFIED: .planning/config.json:15-30]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No application authentication surface is introduced; GitHub identity is platform-managed. [ASSUMED] |
| V3 Session Management | no | No user session is introduced. [ASSUMED] |
| V4 Access Control | yes | Keep workflow top-level `contents: read`; grant `contents: write` only to the final release job after all gates. Current permissions already follow that split. [VERIFIED: .github/workflows/release.yml:8-10] [VERIFIED: .github/workflows/release.yml:114-121] |
| V5 Input Validation | yes | Treat artifact paths, archive members, wheel metadata/tags, subprocess JSON, and downloaded evidence as untrusted; use strict schemas, containment checks, exact expected sets, and bounded reads. [CITED: https://github.com/OWASP/ASVS] |
| V6 Cryptography | yes | Use stdlib SHA-256 for content identity; do not hand-roll crypto and do not call a digest a publisher signature. [ASSUMED] |

### Known Threat Patterns for Artifact Verification

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Swapped artifact or detached evidence | Tampering | Parent computes SHA-256 from the exact input path; record and aggregator recompute/compare it. |
| Checkout/editable import presented as installed artifact | Spoofing | Neutral cwd, sanitized environment, installed-path containment, metadata/direct-url checks, native loader/type assertion. |
| Duplicate record replacing a missing target | Tampering | Exact expected-key set, uniqueness constraint, and mixed identity rejection. |
| Archive path traversal or symlink escape during sdist extraction | Elevation of privilege / Tampering | Validate normalized member destinations and member types before bounded extraction; prefer metadata inspection without extraction where possible. [ASSUMED] |
| Scenario records leak args, kwargs, paths, or exception payloads | Information disclosure | Allowlists, redaction, stable scalar normalization, no raw repr/payload fields. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-31] |
| Oversized archive/evidence causes resource exhaustion | Denial of service | Bound file count/size, reject malformed/non-standard JSON, and retain deterministic diagnostic budgets. Existing manifest parsing already rejects non-standard JSON numbers. [VERIFIED: tools/release_evidence.py:2731-2746] |
| Mutable third-party workflow action | Supply chain / Tampering | Continue full-length SHA pins and regression-test exact refs; update any version comment and expected SHA together. [VERIFIED: .github/workflows/release.yml:41-53] |
| Release runs after failed evidence | Elevation of privilege | Ordinary successful `needs` dependency on aggregate; no `always()` escape; write permission only in final job. [CITED: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs] |

## Planner-Ready Work Decomposition

1. **Wave 0 — oracle/schema tests:** Specify normalized scenario records, evidence schema, expected matrix, and negative fixtures before orchestration. This gives all later tasks one acceptance contract. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-36]
2. **Build fail-close:** Change `setup.py` and build-mode tests so explicit compiled failure propagates while pure/auto retain their intended contracts; add missing-native post-build rejection. [VERIFIED: setup.py:23-49]
3. **Shared conformance extraction:** Refactor selected Phase 16–19 scenarios into a standalone collector and prove source-pure determinism without weakening the existing detailed tests. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:28-31]
4. **Installed wheel verifier:** Extend `release_evidence.py` for exact artifact install, origin/type/version/architecture/provenance assertion, semantic collection, and native benchmark. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-42]
5. **Sdist verification:** Inspect archive and derive explicit pure/compiled children, reusing the wheel verifier and binding lineage to the sdist SHA. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:22-26]
6. **Aggregate and identity:** Implement exact-matrix reconciliation, semantic parity, history consolidation, v0.3.0 surface checks, deterministic manifest, and human summary. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-42]
7. **Complexity/performance:** Add four-operation invariant/scaling proof, preserve diagnostic limits, and gate installed native compiled samples at 200,000 ops/sec. [VERIFIED: .planning/REQUIREMENTS.md:70-78]
8. **CI/release graph:** Separate build/native verification/aggregation, route cross-built outputs to native jobs, upload per-run evidence, and make release depend only on successful aggregate; optionally upgrade cibuildwheel in an isolated subtask. [VERIFIED: .github/workflows/release.yml:16-145]
9. **Release alignment/runbook:** Set all v0.3.0 identity surfaces, update durable docs/task entry points, run quality and workflow regression gates, then exercise hosted native proof before tagging. [VERIFIED: .planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md:33-42]

## Sources

### Primary (HIGH confidence)

- `.planning/phases/20-installed-artifact-parity-release-proof/20-CONTEXT.md` — locked matrix, isolation, conformance, evidence, performance, and publish decisions.
- `.planning/REQUIREMENTS.md` — exact Phase 20 requirements and prior hardened behavior.
- `setup.py`, `tools/build_modes.py`, `tools/release_evidence.py` — build intent, current fallback, archive identity, manifest, and performance implementation.
- `.github/workflows/ci.yml`, `.github/workflows/release.yml` — current source/native jobs, matrix, skips, action pins, and release dependency graph.
- `pyproject.toml`, `src/fast_fsm/__init__.py`, `docs/conf.py`, `evidence/release-baseline.json` — exact dependency/version/evidence state.

### Secondary (MEDIUM confidence)

- [Python Packaging User Guide: Package Formats](https://packaging.python.org/en/latest/discussions/package-formats/) — sdist-to-wheel and installed-wheel model.
- [PyPA Binary Distribution Format](https://packaging.python.org/en/latest/specifications/binary-distribution-format/) — wheel filename/tag semantics.
- [uv: Using environments](https://docs.astral.sh/uv/pip/environments/) and [uv CLI reference](https://docs.astral.sh/uv/reference/cli/) — explicit environment/interpreter and local artifact installation.
- [cibuildwheel options](https://cibuildwheel.pypa.io/en/latest/options/) and [v4.2.0 release](https://github.com/pypa/cibuildwheel/releases/tag/v4.2.0) — installed test behavior and proposed current action version.
- [GitHub workflow jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs), [workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts), and [hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) — dependency semantics, evidence transfer, and native labels.
- [OWASP ASVS](https://github.com/OWASP/ASVS) — security verification category reference.

### Tertiary (LOW confidence)

- None; all discretionary/unverified recommendations are explicitly `[ASSUMED]` and listed in the Assumptions Log.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — repository pins and existing seams were read; the optional cibuildwheel upgrade is MEDIUM pending project CI exercise.
- Architecture: HIGH — it follows locked D-01 through D-14 and extends existing evidence/build boundaries.
- Pitfalls: HIGH — most are observable current gaps or direct consequences of locked isolation/completeness requirements; universal2 and digest-authenticity nuances are marked assumed.
- Native hosted availability: MEDIUM — official labels are documented, but repository entitlement/quota is external state.

**Research date:** 2026-09-04

**Valid until:** 2026-10-04 for repository architecture; re-check runner labels and cibuildwheel releases immediately before implementation.
