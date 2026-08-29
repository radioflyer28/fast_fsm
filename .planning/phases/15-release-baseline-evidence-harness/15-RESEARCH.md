# Phase 15: Release Baseline & Evidence Harness - Research

**Researched:** 2026-08-29
**Scope:** REL-02, REL-04, REL-05, REL-06, REL-08, TEST-02
**Confidence:** HIGH for repository findings; MEDIUM for the final pin set until the full Python matrix runs

## Research Summary

Phase 15 should ship one evidence system with four coordinated seams: release-history correction, explicit build-mode selection, pure-source verification, and deterministic baseline generation/freshness checking. The current repository has most individual commands already, but they are not authoritative as a group: `pyproject.toml` says 0.2.2 despite the v0.2.3 tag, `ty` is the only blocking CI checker, build requirements are ranges or unbounded names, a local native extension can shadow `core.py` during a purported pure run, and exact test/coverage evidence lives only in prose or transient output.

The safest decomposition is to build and test the reusable Python verification primitives first, then compose them into local tasks and independent CI jobs, and finally update historical/public documentation from generated evidence. Phase 15 must define interfaces that Phase 20 can reuse, but must not add strict compiled-publication enforcement or claim installed compiled-wheel parity.

## Current-State Findings

### Release identity

- `pyproject.toml` declares `version = "0.2.2"`; `src/fast_fsm/__init__.py` correctly derives `__version__` from installed metadata and should remain unchanged.
- `CHANGELOG.md` holds shipped v0.2.2/v0.2.3 work under `Unreleased`. The correction must create dated sections and explicitly state that the immutable v0.2.3 tag/artifacts contain 0.2.2 metadata.
- The GitHub v0.2.3 release notice is an external correction target. The repository should track the canonical correction wording and an operator command/checklist; publishing it is a deliberate release-maintainer action, not a source test.
- Phase 15 must not bump the package to v0.3.0; REL-01 and final release identity belong to Phase 20.

### Build selection

- `setup.py` currently means “compile unless `FAST_FSM_PURE_PYTHON=1`; otherwise warn and fall back.” This conflates auto fallback with explicit intent.
- Implement one parser for a new selector such as `FAST_FSM_BUILD_MODE=auto|pure|compiled`. The legacy `FAST_FSM_PURE_PYTHON=1` maps to `pure`; contradictory selectors must fail clearly. Invalid values must fail rather than silently select auto.
- In Phase 15, `compiled` should express intent and expose the seam Phase 20 will harden. Strict failure and native-wheel content enforcement remain deferred to Phase 20 per D-16/REL-03.
- A pure wheel must contain no extension and have a universal `py3-none-any` tag. Wheel-tag and installed-origin inspection should be implemented in one canonical verifier so Phase 20 can extend it.

### Pure-source identity and coverage

- Setting the pure build flag does not affect import precedence. A sibling `src/fast_fsm/core*.so` or `core*.pyd` still shadows `core.py`.
- Verification must scan for native shadows before importing, fail with each exact path, and never delete them. After import, it must assert that `fast_fsm.core.__file__` ends in `.py` and record the resolved origin.
- Run coverage against `src/fast_fsm` only after the shadow preflight. The prior 44% report is invalid as a pure-source baseline because compiled `core` produced zero Python-line coverage.
- Record total source coverage at a stable precision in the manifest and fail when measured coverage is below the committed baseline. A generator refreshes the baseline intentionally; a check mode compares without rewriting.

### Quality-gate authority

- `Taskfile.yml:check` and `.github/workflows/ci.yml:lint` use Ruff plus `ty`; `mypy` exists as a separate local task but is not blocking.
- Make mypy blocking and retain ty as an independent advisory job/step. A ty failure should remain visible without controlling the stable compatibility verdict.
- PR and release evidence must independently report formatting, lint, mypy, full tests, Sphinx HTML, doctest, and evidence freshness/coverage. Avoid a single fail-fast shell chain for these CI categories.
- Existing Ruff defects (`src/fast_fsm/visualization.py` formatting and the unused assignment in `tests/test_advanced_functionality.py`) must be fixed before recording the baseline.
- `uv sync --locked` is the clean-checkout entry condition. The lock already resolves mypy 1.17.1, Ruff 0.12.11, ty 0.0.1a19, pytest 8.4.1, pytest-cov 6.2.1, and setuptools 80.9.0; validate any changed pins across Python 3.10-3.14 before freezing them.

### Evidence manifest

- Use a tracked deterministic JSON manifest (recommended: `evidence/release-baseline.json`) with a schema version.
- Separate stable baseline fields from environment-specific observation fields. Minimum fields: package/release identity, exact pytest collection/pass count, pure-source line coverage, build mode, core module origin classification, wheel tag/metadata when an artifact is supplied, relevant tool versions, Python/platform measurement context, slots-policy measurements, and performance contract/result metadata.
- The generator must support `--write` and `--check` (or equivalent). `--check` generates in memory, normalizes volatile fields, compares the tracked representation, and exits nonzero with a useful diff/freshness reason.
- Exact timings and platform facts are evidence, not README contracts. Narrative docs should say “700+ tests” and retain the stable compiled throughput floor.

### Slots exception

- `CompiledFuncCondition` at `src/fast_fsm/core.py:106` intentionally uses `@mypyc_attr(native_class=False)` and lacks `__slots__`; its docstring already explains inheritance compatibility.
- Add a focused measurement that enumerates production classes subject to the slots policy, verifies the ordinary classes lack instance `__dict__`, and records the deliberate `CompiledFuncCondition` exception and measured instance size/`__dict__` behavior.
- Update `.github/copilot-instructions.md`, `README.md`, and `docs/dev/contributing.md` so the policy is qualified rather than falsely claiming no exceptions.
- Do not redesign `CompiledFuncCondition` in this phase; document and measure the intentional boundary.

## Recommended Implementation Shape

### Verification module/CLI

Create a small development CLI under a repository-owned package or `tools/` directory, invoked only through `uv run python`. Keep standard-library parsing/origin checks separate from subprocess orchestration so they are unit-testable. Suggested commands:

- `build-mode`: parse selector and legacy alias, returning `auto`, `pure`, or `compiled`.
- `verify-source`: preflight native shadows, import `fast_fsm.core`, assert `.py` origin, emit structured origin evidence.
- `verify-wheel <path>`: inspect filename tags and archive contents; optionally install into an isolated environment when metadata/origin evidence is requested.
- `evidence generate --write|--check`: collect deterministic gate results and compare/write the tracked manifest.
- `slots-policy`: enumerate/measure the declared exception set.

Do not expose these as a new public `fast_fsm.build_info()` API. They are maintainer/release tooling.

### Plan decomposition

1. **Build/evidence primitives:** add build-mode parsing, pure-shadow/origin checks, wheel identity checks, slots measurement, unit tests, and the manifest schema/generator.
2. **Gate integration:** repair Ruff baseline, make mypy blocking/ty advisory, add canonical Taskfile commands, independent CI jobs, locked installs, pure coverage regression and freshness enforcement, and release-workflow reuse.
3. **Release records and docs:** reorganize changelog, add the tracked correction wording/operator step, replace exact narrative counts with durable claims, document the slots exception/build modes/evidence workflow, generate the authoritative baseline, and run the full clean gate.

This order prevents documentation and committed evidence from being authored against an unstable implementation.

## Validation Architecture

### Test layers

| Layer | What it proves | Suggested location/command |
|---|---|---|
| Unit | Selector precedence, invalid/conflicting modes, native suffix detection, wheel tag/content classification, manifest normalization/comparison, slots inventory | focused new `tests/test_release_evidence.py` and/or `tests/test_build_modes.py` |
| Integration | A stale fake/native-suffix file is reported without deletion; pure verifier loads `core.py`; generator detects a deliberately stale manifest; pure wheel classifies universal | subprocess tests in temporary copied package/build trees |
| Repository gate | Ruff format/check, mypy, full pytest, Sphinx HTML, doctest, pure coverage non-regression, evidence freshness | independent Taskfile commands and independent CI jobs |
| Clean-checkout proof | `uv sync --locked` followed by the canonical evidence verification produces the committed exact test/coverage/tool observation | final Phase 15 verification on a clean worktree or equivalent isolated checkout |
| External audit | v0.2.3 GitHub release notice matches the tracked correction wording | maintainer checklist plus `gh release view v0.2.3`; source cannot prove publication offline |

### Nyquist mapping

- REL-02: changelog structure/source tests plus manual/external release-notice audit.
- REL-04: selector unit matrix and pure-wheel tag/content integration test.
- REL-05: independent CI jobs and one canonical clean evidence command; manifest records at least 722 passing tests.
- REL-06: locked/pinned build inputs plus a blocking mypy job and nonblocking/advisory ty job.
- REL-08: slots inventory test and generated measurement entry including `CompiledFuncCondition`.
- TEST-02: fail-first stale-shadow subprocess test, `.py` origin assertion, and coverage baseline comparison.

### Fail-first fixtures

- Invalid selector and conflicting legacy/new selector.
- A temporary `core.fake.so`/platform native suffix placed where the verifier scans; assert nonzero exit, exact path, and file still exists.
- A wheel renamed/tagged as pure while containing a native extension; assert classification failure.
- A manifest with a decremented/incremented count or changed schema/tool observation; assert freshness failure and actionable diff.
- A non-exempt slotted class with an injected/declared policy violation in a test fixture; assert inventory failure.

### Baseline acceptance

The phase is not complete until an isolated pure-source run proves `core.py` origin, records meaningful nonzero `core.py` coverage and total coverage, collects at least 722 passing tests, and passes every independent quality/documentation gate. The tracked manifest must be regenerated from that run and then pass check mode without mutation.

## Risks and Mitigations

- **Volatile manifest churn:** normalize ordering and exclude wall-clock durations from blocking equality; retain measurement timestamp/environment as reviewed metadata only when intentionally regenerated.
- **Compiled-mode scope leak:** define selector semantics now, but leave strict compiled build failure and published installed-wheel parity to Phase 20.
- **Coverage gaming:** compare the clean-source total and record per-file data or at least `core.py` coverage so a native-shadow regression cannot hide behind aggregate numbers.
- **CI duplication drift:** have Taskfile and workflows call the same Python verifier rather than reimplementing suffix/tag/manifest rules in YAML.
- **Historical rewrite:** never move the v0.2.3 tag or replace artifacts. The correction is additive in changelog and GitHub release notice.
- **External API assumptions:** GitHub release mutation requires authenticated maintainer authority; plan an explicit checkpoint or operator command rather than silently claiming it happened.
- **Security:** verifier paths are local/untrusted strings; do not shell-interpolate them. Use `pathlib`, `subprocess` argument arrays, isolated temporary directories, and archive traversal-safe inspection. Do not embed secrets or full environment variables in evidence.

## Specless Probe Results

The deterministic edge probe classified all six phase requirements as applicable but unclassified. Planning must therefore carry explicit assumptions for: historical external-state auditability, selector conflicts/invalid values, partial gate failure reporting, lock/tool differences across Python versions, slots inventory drift, and platform-native suffix shadowing. The prohibition probe found no bespoke values/safety/ethics prohibitions after routine engineering and canonical security concerns were filtered; normal archive/path/process safety remains covered by the threat model and security review.

## Sources

- `.planning/phases/15-release-baseline-evidence-harness/15-CONTEXT.md`
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
- `.planning/research/SUMMARY.md`
- `.planning/codebase/CONCERNS.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/STACK.md`
- `pyproject.toml`, `uv.lock`, `setup.py`, `Taskfile.yml`
- `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.github/workflows/release.yml`
- `src/fast_fsm/__init__.py`, `src/fast_fsm/core.py`, `tests/test_mypyc_guard.py`, `tests/test_performance_benchmarks.py`
- `CHANGELOG.md`, `README.md`, `docs/dev/contributing.md`, `.github/copilot-instructions.md`

