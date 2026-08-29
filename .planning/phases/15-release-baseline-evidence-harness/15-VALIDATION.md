---
phase: 15
slug: release-baseline-evidence-harness
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-08-29
---

# Phase 15 — Validation Strategy

> Draft task-by-task validation contract. `$gsd-validate-phase` owns final Nyquist sign-off and the `nyquist_compliant` transition.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1; subprocess/archive integration tests; Ruff; mypy; advisory ty; Sphinx; GitHub Actions/CLI external evidence |
| **Config files** | `pyproject.toml`, `Taskfile.yml`, `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.github/workflows/release.yml` |
| **Focused local command** | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py -x -q` after those files are created by their owning tasks |
| **Wave/final recollection** | `task release-baseline-check`, `uv run pytest tests/ -x -q`, independent Ruff/mypy/docs/doctest/build/performance gates |
| **Exact tool contract** | uv 0.12.6; locked Python dependencies from `uv.lock`; Python 3.10-3.14 remote build proof |

## Sampling Rate

- **After every code-producing task:** run only the task's focused command, targeting feedback under 30 seconds where the check is local.
- **After each wave:** run the full gates affected by that wave. Full evidence recollection (`task release-baseline-check`) is a wave/final gate, not routine per-task feedback.
- **After the final repository wave:** push the exact commit, wait for the complete GitHub Actions run, and record every job conclusion before REL-05/REL-06 can close.
- **External checkpoints:** Actions watch and release publication may exceed 30 seconds because their purpose is terminal remote proof; they block rather than silently time out or infer success.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirements | Threat Refs | Secure/Observable Behavior | Test Ownership | Focused Automated Command | Status |
|---------|------|------|--------------|-------------|----------------------------|----------------|---------------------------|--------|
| 15-01-01 | 01 | 1 | REL-04, REL-06 | T-15-01 | Python-3.10-compatible selector rejects invalid/conflicting intent; pure sdist includes selector and unpacked sdist builds a wheel | `tests/test_build_modes.py` created fail-first inside this tracer task; not Wave 0 | `uv run pytest tests/test_build_modes.py -x -q` plus `uv run --python 3.10 --no-project python -c "from tools.build_modes import BuildMode, resolve_build_mode; assert resolve_build_mode({'FAST_FSM_BUILD_MODE':'pure'}) is BuildMode.PURE"` | pending |
| 15-01-02 | 01 | 1 | REL-04, TEST-02 | T-15-02, T-15-03 | Native shadow fails before import without deletion; one universal pure plus multiple compiled platform-wheel inputs retain independent normalized filename/tag/metadata/native-member evidence | `tests/test_release_evidence.py` shadow/source/wheel cases created fail-first inside this task | `uv run pytest tests/test_release_evidence.py -x -q -k "shadow or source_origin or wheel"` | pending |
| 15-01-03 | 01 | 1 | REL-08 | T-15-04, T-15-28 | Recursive inventory accounts for every relevant `src/fast_fsm` class and independently measures registered `CompiledFuncCondition` and `TransitionError` exceptions without leaking absolute environment data | slots cases added fail-first to the task-owned test file | `uv run pytest tests/test_release_evidence.py -x -q -k slots` | pending |
| 15-02-01 | 02 | 2 | REL-04, REL-05, REL-06, REL-08, TEST-02 | T-15-06, T-15-07, T-15-08 | Deterministic manifest fails read-only check on stale/regressed evidence, preserves repeatable multi-wheel records, contains the complete two-exception recursive slots inventory, and records uv 0.12.6 | manifest normalization/comparison cases added fail-first inside this task | `uv run pytest tests/test_release_evidence.py -x -q -k evidence` | pending |
| 15-02-02 | 02 | 2 | REL-04, REL-05, REL-06 | T-15-06, T-15-08 | Tracked baseline and canonical task commands set pure mode before/during every clean install, preflight immediately after sync, use the exact lock, and keep separate mypy/ty authority | no missing test dependency; consumes Task 1 tests and generated temporary evidence | `FAST_FSM_BUILD_MODE=pure uv sync --locked`, then `FAST_FSM_BUILD_MODE=pure uv run python tools/release_evidence.py verify-source --json`, then `FAST_FSM_BUILD_MODE=pure task release-baseline-check`; also `uv lock --check` and `task --list` | pending |
| 15-02-03 | 02 | 2 | REL-05, REL-06 | T-15-08, T-15-09, T-15-10 | Independent workflow jobs pin uv 0.12.6; clean jobs establish pure mode before locked sync and immediately preflight; Python 3.10-3.14 locked sync/build exists; release changes only gate and existing pure sdist | workflow-contract cases added fail-first to `tests/test_release_evidence.py` inside this task | `uv run pytest tests/test_release_evidence.py -x -q -k "workflow_contract or setup_uv or supported_python"` | pending |
| 15-04-01 | 04 | 3 | REL-05, REL-08 | T-15-16 | Durable prose uses 700+ and stable performance contract while exact values stay in manifest | existing README example tests; documentation compilation is a wave gate | `uv run pytest tests/test_readme_examples.py -x -q` | pending |
| 15-04-02 | 04 | 3 | REL-05, REL-08 | T-15-17, T-15-18 | Agent/SPR policy agrees on mypy, advisory ty, pure evidence, both registered measured slots exceptions, and recursive inventory coverage | consumes slots/mypyc tests created earlier; no Wave 0 dependency | `uv run pytest tests/test_mypyc_guard.py tests/test_release_evidence.py -x -q -k "slots or mypyc"` | pending |
| 15-06-01 | 06 | 3 | REL-05 | T-15-24, T-15-25 | Two-file Ruff repair is scoped and behavior-preserving | existing visualization/advanced tests; no new test scaffold | `uv run ruff format --check src/fast_fsm/visualization.py tests/test_advanced_functionality.py`; `uv run ruff check src/fast_fsm/visualization.py tests/test_advanced_functionality.py`; `uv run pytest tests/test_visualization.py tests/test_advanced_functionality.py -x -q` | pending |
| 15-07-01 | 07 | 3 | REL-05 | T-15-29, T-15-30 | Exactly five malformed public docstrings render under Sphinx 9.1 warnings-as-errors and doctest while the normalized non-docstring AST, signatures, behavior, and compiled boundary remain unchanged | existing core/API tests and Sphinx builders; no new test scaffold or source helper | docstring-change-set AST guard plus `git diff --check -- src/fast_fsm/core.py`; `uv run sphinx-build -b html docs docs/_build/html -W --keep-going`; `for name in "State.create" "StateMachine.quick_build" "StateMachine.add_listener" "quick_fsm" "condition_builder"; do rg -Fq "$name" docs/_build/html/api/core.html || { printf 'missing rendered API name: %s\n' "$name"; exit 1; }; done`; `uv run sphinx-build -b doctest docs docs/_build/doctest`; `uv run pytest tests/test_state_machine_utils.py tests/test_basic_functionality.py tests/test_listeners.py tests/test_builder.py -x -q` | pending |
| 15-03-01 | 03 | 4 | REL-02 | T-15-11, T-15-14 | Immutable tag mismatch and canonical additive correction remain source-auditable | release-history cases added fail-first to `tests/test_release_evidence.py` inside this task | `uv run pytest tests/test_release_evidence.py -x -q -k release_history` | pending |
| 15-03-02 | 03 | 4 | REL-05, REL-08, TEST-02 | T-15-12, T-15-13, T-15-15 | Clean committed checkout establishes pure mode before every install, preflights immediately after sync, and produces exact uv/test/coverage/pure-origin/two-exception baseline without touching developer shadows | no missing test dependency; clean-worktree collection is performed in-task; full recollection reserved for wave gate | `FAST_FSM_BUILD_MODE=pure uv sync --locked`, then `FAST_FSM_BUILD_MODE=pure uv run python tools/release_evidence.py verify-source --json`, then `FAST_FSM_BUILD_MODE=pure task release-baseline-check`, then `FAST_FSM_BUILD_MODE=pure uv run python -c "import json; d=json.load(open('evidence/release-baseline.json')); names={x['qualified_name'] for x in d['slots_policy']['registered_exceptions']}; assert d['toolchain']['uv']=='0.12.6' and d['quality_baseline']['tests']['passed'] in range(722,1000000) and d['artifact_evidence']['source']['core_origin'].endswith('.py') and d['slots_policy']['inventory'] and names=={'fast_fsm.core.CompiledFuncCondition','fast_fsm.core.TransitionError'}"` | pending |
| 15-08-01 | 08 | 5 | REL-05, REL-06 | T-15-32, T-15-33, T-15-34, T-15-35 | YAML-structural traversal of every job/step/run scalar proves plain, block, multiline, and environment-prefixed Task consumers install exact Task 3.53.1 through full action SHA `c0bc642852239c2689f73f4ea6459c29405f3c52` (`v3.0.0`) before every invocation while existing gates remain unchanged | fail-first structural discovery, mutation, pin, and ordering contracts added to `tests/test_release_evidence.py` inside this task | `uv run pytest tests/test_release_evidence.py -x -q -k "task_runner or workflow_contract or setup_uv or supported_python"`; YAML parse; full `tests/test_release_evidence.py`; pure source verification; `FAST_FSM_BUILD_MODE=pure task release-gate` | pending |
| 15-05-01 | 05 | 6 | REL-05, REL-06 | T-15-26, T-15-27 | Corrective exact pushed SHA has terminal all-job proof including locked sync/build for Python 3.10-3.14, then closes fast_fsm-6yg | blocking external checkpoint; no local test scaffold can substitute for Actions | `gh run list --repo radioflyer28/fast_fsm --workflow ci.yml --commit "$(git rev-parse HEAD)" --status completed --json headSha,status,conclusion,url --limit 1`, followed by recorded `gh run view ... --json jobs` | pending |
| 15-05-02 | 05 | 6 | REL-02 | T-15-20, T-15-21, T-15-22, T-15-23 | Canonical correction is live while URL, tag name/target SHA, and assets compare unchanged before/after | blocking authenticated external checkpoint; local canonical/history tests already exist | `gh release view v0.2.3 --repo radioflyer28/fast_fsm --json url,body,tagName,assets` piped to the plan's canonical normalized-body assertion | pending |

## Wave Gates

| After Wave | Gate | Purpose |
|------------|------|---------|
| 1 | `uv run pytest tests/test_build_modes.py tests/test_release_evidence.py -x -q`; `uv run mypy tools/build_modes.py tools/release_evidence.py` | Selector/sdist, source/wheel, and slots primitives are sound. |
| 2 | `uv lock --check`; `FAST_FSM_BUILD_MODE=pure uv sync --locked`; immediately `FAST_FSM_BUILD_MODE=pure uv run python tools/release_evidence.py verify-source --json`; `FAST_FSM_BUILD_MODE=pure task supported-python-build-matrix-local`; `FAST_FSM_BUILD_MODE=pure task release-baseline-check`; `task typecheck-mypy` | Locally available supported versions are exercised and reported; every clean path preflights before collection; deterministic multi-artifact/two-exception evidence, exact pins, canonical tasks, and workflow contracts compose. |
| 3 | `uv run ruff format --check src/ tests/`; `uv run ruff check src/ tests/`; Sphinx HTML/doctest builds | Dedicated repair and durable docs are repository-clean. |
| 4 | `task release-history-check`; `FAST_FSM_BUILD_MODE=pure uv sync --locked`; immediately `FAST_FSM_BUILD_MODE=pure uv run python tools/release_evidence.py verify-source --json`; `FAST_FSM_BUILD_MODE=pure task release-baseline-check`; `FAST_FSM_BUILD_MODE=pure uv run pytest tests/ -x -q`; all independent local release gates | Clean authoritative evidence and additive history pass before push; no test, coverage, or artifact collection precedes the post-sync source-origin preflight. |
| 5 | Focused pinned-Task workflow contracts; YAML parse; full release-evidence tests; pure-source verification; `FAST_FSM_BUILD_MODE=pure task release-gate` | The corrective workflow is locally proven without substituting local checks for hosted execution. |
| 6 | Corrective exact-SHA `gh run watch --exit-status` plus complete `gh run view --json jobs`; fast_fsm-6yg closure on success; authenticated release pre/post comparison | Remote supported-version proof and public correction are complete. |

## Wave 0 Requirements

None. `wave_0_complete: true` means no test scaffold must pre-exist before execution. The two new test files are production outputs of Plan 01, and later fail-first cases are added inside their owning TDD/test-first tasks. Existing tests used by Plans 04 and 06 already exist. This does not imply Phase 15 is Nyquist-compliant; final validate-phase review remains pending.

## Manual/External Verifications

| Behavior | Requirements | Why External | Blocking Evidence |
|----------|--------------|--------------|-------------------|
| Exact pushed commit passes all independent jobs and Python 3.10-3.14 locked sync/build | REL-05, REL-06 | Hosted Actions execution cannot be proven by repository YAML | Run URL, exact head SHA, terminal conclusion, and complete job-name/conclusion table in `15-05-SUMMARY.md`. |
| GitHub v0.2.3 notice matches canonical correction while immutable identity is preserved | REL-02 | Authenticated public release mutation is outside source control | Pre/post URL/tag/assets/tag-target comparison plus canonical normalized-body assertion and redacted result. |

## Validation Sign-Off

- [ ] Every task's focused command passes.
- [ ] Full recollection is limited to wave/final gates.
- [ ] Every blocking threat mitigation has executable evidence.
- [ ] Exact uv 0.12.6 and Python 3.10-3.14 remote build proof are recorded.
- [ ] External GitHub comparisons are redacted and identity-preserving.
- [ ] Final `$gsd-validate-phase 15` sets `nyquist_compliant: true` only after implementation and remote evidence exist.

**Approval:** pending plan checker and post-execution validate-phase
