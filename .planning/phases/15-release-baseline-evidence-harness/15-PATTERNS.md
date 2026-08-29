# Phase 15: Release Baseline & Evidence Harness - Pattern Map

**Mapped:** 2026-08-29
**Files analyzed:** 14 likely new/modified files
**Analogs found:** 12 / 14 (the evidence CLI and manifest have no direct analog)

This map covers the release-history, build-selection, clean-source verification,
evidence, quality-gate, and slots-policy work in REL-02, REL-04, REL-05,
REL-06, REL-08, and TEST-02. Phase 15 is repository tooling and maintainer
workflow; it should not add a public runtime `build_info()` API or implement the
strict compiled-release proof deferred to Phase 20.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `setup.py` | build/config adapter | transform (environment to build configuration) | existing `setup.py` | exact |
| `tools/release_evidence.py` (or equivalent repository-owned tooling module) | utility/CLI | batch + file-I/O + subprocess | `benchmarks/benchmark_fast_fsm.py` and `tests/test_mypyc_guard.py` | role-match |
| `evidence/release-baseline.json` (filename is discretionary) | generated evidence/config artifact | batch + file-I/O | no direct analog; `uv.lock` is the closest deterministic artifact | partial |
| `tests/test_release_evidence.py` (or split `test_build_modes.py`) | test | request-response + subprocess/file-I/O integration | `tests/test_mypyc_guard.py` | exact for static policy, role-match for subprocess |
| `pyproject.toml` | package/build config | declarative configuration | current `pyproject.toml` | exact |
| `Taskfile.yml` | task orchestration | request-response/batch command composition | current `Taskfile.yml` | exact |
| `.github/workflows/ci.yml` | CI config | event-driven matrix/batch gates | current `ci.yml` | exact |
| `.github/workflows/release.yml` | release orchestration | event-driven artifact build/publish | current `release.yml` | exact |
| `.github/workflows/docs.yml` | CI/docs config | event-driven build/deploy | current `docs.yml` | exact |
| `CHANGELOG.md` | historical release record | append/transform documentation | current `CHANGELOG.md` | exact |
| `README.md` | user-facing documentation | static documentation | current `README.md` | exact |
| `docs/dev/contributing.md` and `docs/dev/testing.md` | maintainer documentation | static documentation/procedure | current developer guides | exact |
| `.github/copilot-instructions.md` | project workflow contract | static procedure/configuration | current instructions | exact |
| `docs/dev/releasing.md` (if a dedicated operator checklist is added) | maintainer runbook | request-response + external release audit | `docs/dev/contributing.md` | role-match |

The exact evidence-tool filename and whether the release operator record is a
new page or a section in `docs/dev/contributing.md` are open decisions. Keep
the same boundaries either way: reusable pure functions in the tool, shell
orchestration in Taskfile/workflows, and historical wording in the changelog.

## Pattern Assignments

### `setup.py` (build/config adapter, transform)

**Analog:** `setup.py` itself (lines 1-36)

**Imports and configuration seam** (lines 1-3):

```python
import os

from setuptools import setup
```

**Current build selector** (lines 5-26):

```python
# mypyc selective compilation — only core.py is compiled.
ext_modules = []
if os.environ.get("FAST_FSM_PURE_PYTHON", "0") != "1":
    try:
        from mypyc.build import mypycify

        ext_modules = mypycify(
            ["src/fast_fsm/core.py"],
            opt_level="3",
            debug_level="1",
            separate=False,
            multi_file=False,
        )
    except Exception as exc:
        ...

setup(ext_modules=ext_modules)
```

Preserve the single `core.py` compilation boundary and `setup(ext_modules=...)`.
Add one clearly testable parser before this branch for `auto`, `pure`, and
`compiled`, with the legacy `FAST_FSM_PURE_PYTHON=1` mapping to `pure`. Invalid
values and contradictory selectors should fail explicitly. Do not silently
turn an explicitly requested `compiled` mode into `auto`; strict artifact
failure remains a Phase 20 policy, but mode intent must be observable now.

**Error-handling warning:** the broad `except Exception` at lines 27-34 is a
known risk (CONCERNS.md lines 35-39). A new implementation should isolate the
expected tool/compiler-unavailable fallback and preserve actionable errors for
invalid mode configuration. Keep parser logic independent from mypyc imports
so it can be unit-tested without compiling.

**Boundary to preserve:** ADR-003 says only `core.py` is compiled and
`conditions.py`/`condition_templates.py` remain interpreted. The compiled mode
selector must not alter this file list.

---

### `tools/release_evidence.py` (utility/CLI, batch + file-I/O)

**Analogs:** `tests/test_mypyc_guard.py` (AST/static inspection, lines 25-35 and
96-168) and `benchmarks/benchmark_fast_fsm.py`/`tests/test_performance_benchmarks.py`
(measured execution, lines 62-86 and 513-543 of the test file).

There is no existing repository CLI that emits a manifest, so this is a
no-analog area. Keep it a narrow maintainer tool, not a package runtime import.
Prefer standard-library modules (`argparse`, `ast`, `importlib`, `json`,
`pathlib`, `platform`, `subprocess`, `sys`, `zipfile`) because the package has a
single runtime dependency and tools already run through `uv`.

**Static-path pattern** (from `test_mypyc_guard.py` lines 104-118):

```python
source = CORE_PY.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(CORE_PY))
classes: dict[str, ast.ClassDef] = {
    node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
}
missing = [
    f"  {name} (line {classes[name].lineno})"
    for name in sorted(candidates)
    if not _has_allow_interpreted(classes[name])
]
assert not missing, "..." + "\n".join(missing)
```

Use this style for slots inventory: report exact class/path/line evidence and
fail with an actionable list. The new tool should enumerate the production
classes covered by the slots policy, explicitly identify
`CompiledFuncCondition`, and record the deliberate `__dict__` exception and
measurement rather than hiding it.

**Measurement pattern** (from `test_performance_benchmarks.py` lines 62-86 and
513-543):

```python
for _ in range(100):
    fsm.trigger("start")
    fsm.trigger("finish")
gc.collect()
start_time = time.perf_counter()
...
elapsed = time.perf_counter() - start_time
ops_per_sec = iterations / elapsed
```

Warm hot paths, use `time.perf_counter()`, identify compiled versus pure
origin, and store environment context with observations. Do not put volatile
timings into the blocking identity comparison unless intentionally normalized.

**Pure-source verification flow:**

1. Resolve the repository/package path with `pathlib`.
2. Before importing `fast_fsm.core`, scan the package directory for platform
   extension suffixes from `importlib.machinery.EXTENSION_SUFFIXES` (including
   `.so` and `.pyd` variants). Fail closed with every exact shadow path; never
   delete it.
3. Import only after the scan and assert the module origin ends in `.py`.
4. Run/collect pure tests and coverage through argument-array subprocess calls;
   do not interpolate paths into shell strings.
5. Normalize deterministic data, compare against the tracked JSON, and emit an
   actionable diff/reason for `--check` failures. `--write` is explicit and
   never performed by CI.

**Wheel inspection:** use `zipfile.ZipFile` to inspect archive names and
`importlib.metadata`/`packaging` only if already available in the dev graph.
At minimum classify filename tags, metadata version, and whether a native
extension is present. Reject a wheel claiming universal pure mode when it
contains a native extension. Installed compiled/pure parity and publication
proof remain Phase 20.

**Subprocess safety:** use `subprocess.run([...], check=False, text=True,
capture_output=True, cwd=...)`; pass each argument separately, use temporary
directories, and do not serialize secrets or the full environment into the
manifest. This follows the research threat model; no current source analog
handles untrusted paths, so the planner must make this an explicit invariant.

---

### `evidence/release-baseline.json` (generated evidence, batch + file-I/O)

**Analog:** `uv.lock` is the closest existing deterministic machine-readable
artifact; there is no project-generated JSON baseline to copy.

Keep the file tracked, schema-versioned, deterministic, and readable. Separate
stable baseline fields from environment-specific observations. The minimum
shape should cover:

- release/package identity and correction-record reference;
- exact pytest collected/passed count (currently 722 was measured; do not put
  that number in prose as an immutable promise);
- clean pure-source total and `core.py` coverage;
- build mode and module-origin classification;
- optional supplied wheel tags/metadata/content classification;
- Python/platform and tool versions (`uv.lock` is the resolution authority);
- slots-policy inventory including `CompiledFuncCondition` exception;
- performance contract/result metadata, with exact timings contextualized.

Use stable key ordering and a final newline. Exclude timestamps, durations,
absolute paths, and host-specific volatile fields from the equality portion or
normalize them before `--check`; retain context only in explicitly reviewed
observation fields. A fresh generator should produce byte-identical output
from equivalent measurements.

---

### `tests/test_release_evidence.py` / `tests/test_build_modes.py` (tests,
request-response + subprocess/file-I/O)

**Analog:** `tests/test_mypyc_guard.py` (lines 1-28, 38-88, 96-168)

The existing guard is a focused module-level test file, reads source with
`Path`, parses AST, and asserts detailed failure text. Follow its no-fixture,
direct-assert structure for selector parsing, slots inventory, and source
policy. Keep tests flat under `tests/`, named `test_<feature>.py`; pytest
discovery is configured in `pyproject.toml` lines 50-66.

**Static guard style:**

```python
def test_no_unexpected_classes_exempted() -> None:
    source = CORE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CORE_PY))
    ...
    assert not stale, (
        "INTERNAL_CLOSED ... contains names ...\n"
        + "\n".join(f"  {n}" for n in stale)
    )
```

Add fail-first tests for: valid auto/pure/compiled values; legacy alias;
invalid and conflicting values; native suffix fixture under `tmp_path` that is
reported and remains on disk; `.py` module origin; pure-wheel universal tag
and extension-content mismatch; stale manifest count/tool/schema differences;
and the slots exception measurement. Subprocess tests should invoke the tool
with `sys.executable`/`uv run`-compatible arguments and inspect return code,
stdout/stderr, and file existence. The research validation architecture calls
for temporary copied/build trees when import precedence matters.

Do not subclass FSM classes in new tests. Existing project testing guidance
requires composition because compiled classes cannot be subclassed from
interpreted Python (`docs/dev/testing.md` lines 60-72). Do not mock the
verification computation; mock only environment/time/I/O if unavoidable.

---

### `pyproject.toml` (package/build config, declarative)

**Analog:** current file (lines 1-69).

Preserve the PEP 621 `[project]` metadata and `src` package discovery. The
package version is currently `0.2.2` (lines 1-9), while
`src/fast_fsm/__init__.py` derives `__version__` from installed metadata (lines
53-58), so do not create a second runtime version constant. Phase 15 records the
v0.2.3 mismatch; it must not bump the package to v0.3.0.

Development dependencies are currently ranges (`mypy[mypyc]>=1.17`,
`pytest>=8.4.1`, `ruff>=0.12.11`, `ty>=0.0.1a19`, lines 11-32) and
`uv.lock` carries the concrete resolution. If changing lower bounds/build
requirements, verify all Python 3.10-3.14 markers and regenerate the lock with
`uv`, not pip. Keep `mypy[mypyc]` available for both `mypy` and compilation.

The pytest config (lines 50-69) is the source of truth for test discovery,
strict markers, sequential `-x -q`, and asyncio mode; new evidence tests should
fit it rather than adding an alternate runner configuration.

---

### `Taskfile.yml` (task orchestration, request-response/batch)

**Analog:** current tasks, especially lines 24-50, 57-88, 95-113, 140-153,
170-182.

**Task environment and commands:**

```yaml
test:
  desc: "Run full test suite — merge gate (pure Python, -x -q)"
  env:
    FAST_FSM_PURE_PYTHON: "1"
  cmds:
    - uv run pytest tests/ -x -q

check:
  desc: "Phase 2: Validate formatting, linting, and types (blocks merge)"
  cmds:
    - uv run ruff format --check src/ tests/
    - uv run ruff check src/ tests/
    - uv run ty check {{.SRC_DIR}}/

typecheck-mypy:
  desc: Type check with mypy (mypyc compatibility verification)
  cmds:
    - uv run mypy {{.SRC_DIR}}/
```

Add canonical evidence/build-mode/pure-source/coverage freshness tasks as
thin wrappers around the Python verifier. Retain direct `uv run` commands and
the explicit pure environment (or migrate all callers to the one new selector
while preserving the alias). Do not duplicate suffix, wheel, or JSON comparison
logic in YAML. Make `mypy` blocking and `ty` separately visible/advisory per
D-05; replace the current `check` flow only after ensuring independent CI
reporting. Existing `ci` composes `check`, `test`, and `build-check` (lines
177-182), so update its description and composition to include all required
gates without hiding failures behind one opaque shell chain.

The existing `build-check` heredoc smoke test (lines 100-113) is a useful
compiled smoke pattern but should not become the Phase 15 pure-evidence
implementation. Prefer a checked-in tool entry point and explicit artifact
cleanup/temporary locations.

---

### `.github/workflows/ci.yml` (CI config, event-driven matrix/batch)

**Analog:** current workflow (lines 1-116).

Preserve the Python 3.10-3.14 × Ubuntu/Windows/macOS matrix and
`fail-fast: false` (lines 41-49). Each check should be independently visible:
format, lint, blocking mypy, advisory ty, full pure tests, pure coverage and
manifest freshness, Sphinx HTML, doctest, and the existing compiled smoke/
performance check. Avoid one job step that runs `check && test && docs`; a
failure in that shell chain conceals later categories.

**Existing install/matrix pattern** (lines 23-39 and 54-66):

```yaml
- uses: astral-sh/setup-uv@v5
  with:
    python-version: "3.12"

- name: Install dev deps
  run: uv sync --group dev
  env:
    FAST_FSM_PURE_PYTHON: "1"

- name: Run test suite
  run: uv run pytest tests/ -x -q
  env:
    FAST_FSM_PURE_PYTHON: "1"
```

Use `uv sync --locked` for clean-checkout reproducibility, and keep pure-source
preflight before coverage. The current `lint` runs Ruff format/check and then
ty in one job (lines 32-39); split stable mypy authority from advisory ty while
keeping all outcomes visible. Release and pull-request workflows should call
the same Taskfile/tool commands rather than reimplementing checks.

---

### `.github/workflows/release.yml` (release orchestration, event-driven)

**Analog:** current artifact workflow (lines 1-147).

Preserve the matrix-oriented `build_wheels` job (`cibuildwheel` at lines 9-71),
the pure sdist job (lines 73-92), artifact upload/download, and GitHub release
job (lines 94-123). Phase 15 should add the canonical independent release gate
and evidence freshness/check invocation before publication, and ensure the
source/sdist path selects pure mode intentionally. Do not claim Phase 20’s
installed native-wheel parity or strict compiled-failure enforcement here.

Current sdist selection:

```yaml
- name: Build sdist
  run: uv build --sdist
  env:
    FAST_FSM_PURE_PYTHON: "1"
```

Keep the legacy variable working while workflows migrate to the unified mode
selector. The v0.2.3 correction is an external GitHub release-notice action;
the repository can carry canonical wording/operator instructions and verify
that the local text matches, but cannot assert publication without maintainer
credentials.

---

### `.github/workflows/docs.yml` (docs CI config, event-driven build/deploy)

**Analog:** current workflow (lines 29-75).

Keep separate HTML and doctest commands with warnings-as-errors for HTML:

```yaml
- name: Build HTML
  run: uv run sphinx-build -b html docs docs/_build/html -W --keep-going

- name: Verify doctest examples
  run: uv run sphinx-build -b doctest docs docs/_build/doctest
```

Use `uv sync --locked` and the pure-source selector/preflight where the docs
import package code. Do not put generated evidence into the Sphinx output as a
second narrative source; link or summarize the tracked manifest according to
the documentation decision.

---

### `CHANGELOG.md` (historical record, append/transform documentation)

**Analog:** current release sections (lines 1-99).

The current v0.2.2/v0.2.3-era entries are under `Unreleased` (lines 6-67),
followed by the dated `[0.2.1]` section (lines 69-98). Preserve Keep a
Changelog headings and additive history. Move shipped entries into dated
v0.2.2/v0.2.3 sections without moving the immutable v0.2.3 tag or replacing
artifacts. The v0.2.3 section must say that artifacts carry defective 0.2.2
metadata and point users to the correction/v0.3.0; avoid wording that implies
withdrawal.

Do not place exact test counts, host-specific coverage, or benchmark timings in
the historical narrative. Use the durable “700+ tests” style in user docs and
the generated manifest for exact evidence.

---

### `README.md` (user documentation, static)

**Analog:** current performance/release prose (lines 11-25) and compatibility
matrix (lines 27-53).

Replace mutable claims such as “Production ready — 290 tests” (line 16) and
volatile exact benchmark headlines with durable rounded claims and links to the
verification/evidence instructions. Preserve the simple installation and
`uv` commands (lines 55-63), supported Python range, and stable performance
contract (`trigger()` floor ≥200,000 compiled operations/sec) while moving exact
measurements to the manifest. Do not add a persistent historical v0.2.3 warning;
the correction belongs in dated changelog/GitHub release records.

---

### `docs/dev/contributing.md` and `docs/dev/testing.md` (developer docs,
static procedures)

**Analogs:** existing quality workflow (contributing lines 49-88), slots/build
policy (contributing lines 92-170), performance checklist (contributing lines
172-180), and testing commands/baseline (testing lines 3-18, 100-121).

Preserve the sequence of incremental targeted tests followed by the full suite,
Google-style documentation, and `uv`-only commands. Update the current
unqualified “all classes/no exceptions” slots statement (contributing lines
92-95) to name and measure `CompiledFuncCondition` as the deliberate exception.
Document the unified `auto|pure|compiled` selector plus legacy alias, the
non-destructive stale-extension cleanup instruction, and the canonical evidence
generator/check command. Change the stale 62-test baseline (testing lines
117-121) to durable “700+” prose with exact values delegated to the manifest.

Keep the existing prohibition against test inheritance and logic mocking
(testing lines 60-72). Evidence tests should use real filesystem/zip/module
fixtures and subprocesses, not mocks of the verifier itself.

---

### `.github/copilot-instructions.md` (workflow contract, static procedure)

**Analog:** current Golden Rules and workflow sections (lines 29-52, 61-106,
182-220).

Preserve the explicit `uv` command policy, sequential test execution, quality
gate commands, and source-to-test mapping. Replace the stale 290-test baseline
(lines 48-52) with the durable rounded claim and point exact counts to the
tracked evidence manifest. Qualify “all core classes MUST use `__slots__`” (line
38) with the measured `CompiledFuncCondition` exception and link ADR-003.
Document mypy as blocking and ty as advisory, plus the canonical clean/pure
verification command and manifest freshness procedure.

Do not add a public API requirement here. This document is operational guidance;
the package version remains derived from metadata by `__init__.py`.

---

### `docs/dev/releasing.md` (optional operator runbook, request-response)

**Analog:** `docs/dev/contributing.md` procedural sections (lines 49-88 and
154-180) and the release workflow’s artifact steps (`release.yml` lines 94-123).

If a dedicated page is added, use short copy/paste `uv` commands, explicit
preconditions, and a checkpoint for authenticated external actions. Include the
canonical v0.2.3 correction wording/operator command, but state clearly that
`gh release edit/view v0.2.3` requires maintainer authority. The runbook should
tell maintainers to preserve the tag/artifacts, review the generated manifest
diff, and run `--check` after regeneration; it must not claim that the external
release notice was published merely because local tests pass.

## Shared Patterns

### Package/version identity

**Sources:** `src/fast_fsm/__init__.py` lines 53-58; `pyproject.toml` lines 1-9;
`CHANGELOG.md` lines 69-98.

```python
from importlib.metadata import version as _get_version, PackageNotFoundError as _PNF

try:
    __version__ = _get_version("fast_fsm")
except _PNF:
    __version__ = "unknown"
```

Keep metadata as the runtime version source. Reconcile historical records
additively and test installed metadata rather than introducing a second
constant.

### `uv` and lockfile authority

**Sources:** `pyproject.toml` lines 11-39; `Taskfile.yml` lines 24-29, 63-88;
`ci.yml` lines 23-30, 54-66.

All Python execution, dependency installation, tests, builds, and docs use
`uv`. Use `uv sync --locked` in clean evidence/release jobs. Ranges in
`pyproject.toml` describe compatibility; exact reproducibility comes from the
tracked `uv.lock`. Record relevant resolved tool versions in evidence.

### Independent quality categories

**Sources:** `Taskfile.yml` lines 63-88 and `ci.yml` lines 15-40.

Ruff format, Ruff lint, mypy, ty, tests, coverage/freshness, Sphinx HTML, and
doctests must each have an independently visible result. Existing `fail-fast:
false` applies to the matrix (ci.yml lines 45-49), but separate jobs or steps
are still needed to avoid losing later categories after one command fails.

### Test discipline and evidence failures

**Sources:** `tests/test_mypyc_guard.py` lines 96-168;
`docs/dev/testing.md` lines 60-72; `tests/test_performance_benchmarks.py` lines
62-99 and 513-543.

Use focused regression tests, exact actionable assertions, real code paths,
composition over subclassing, warmups and `perf_counter()` for measurements,
and wide hardware-tolerant performance thresholds. A failing stale manifest or
native shadow test must preserve the fixture and explain the explicit cleanup
action.

### Selective compilation boundary

**Sources:** `setup.py` lines 5-26; ADR-003 lines 26-43, 148-177;
`src/fast_fsm/core.py` lines 105-162.

Only `core.py` is compiled. `conditions.py` and `condition_templates.py` stay
interpreted for user subclassing. `CompiledFuncCondition` is decorated
`native_class=False` and intentionally uses `__dict__`; measure/document that
exception rather than changing it in Phase 15.

## No Analog Found

| File/Concern | Why no direct analog | Planning consequence |
|---|---|---|
| Evidence generator CLI | No existing repository tool emits a deterministic machine-readable baseline or performs wheel/source-origin inspection | Use the research architecture; keep pure functions separate from subprocess orchestration and test both independently. |
| Evidence manifest schema | `uv.lock` is deterministic but does not model test/coverage/origin/slots observations | Define a schema version, stable ordering, normalized comparison, and explicit `--write`/`--check`; do not infer a schema from runtime modules. |
| GitHub v0.2.3 correction publication | External release state is not represented in source | Track canonical wording/operator command and require a maintainer audit; do not report publication as locally proven. |

## Anti-Patterns to Avoid

- Treating `FAST_FSM_PURE_PYTHON=1` as proof of pure import. Existing local
  `src/fast_fsm/core.cpython-312-darwin.so` shadows `core.py` even when no new
  extension is built (`.planning/codebase/TESTING.md` lines 31-36).
- Catching every build exception and silently producing a pure artifact when
  the user requested compiled mode; make fallback/intent explicit and defer
  strict release failure to Phase 20.
- Reimplementing suffix detection, wheel tags, or manifest comparison in YAML,
  shell snippets, Taskfile, and tests separately; centralize in the tool.
- Using a single `&&`/fail-fast gate for all categories, or letting advisory ty
  determine the stable type verdict.
- Committing exact volatile test/coverage/timing claims in README/changelog;
  keep rounded contracts in prose and contextual exact values in JSON.
- Deleting stale `.so`/`.pyd` files from the verifier. Report exact paths and
  require an explicit developer cleanup command.
- Adding a public runtime evidence/build-info API, changing the mypyc boundary,
  or claiming installed compiled-wheel publication parity in this phase.

## Metadata

**Analog search scope:** `src/fast_fsm/`, `tests/`, `benchmarks/`, `docs/`,
`Taskfile.yml`, `pyproject.toml`, `setup.py`, `uv.lock`, `.github/workflows/`,
`.planning/codebase/`, `.specify/`.
**Files scanned:** 12 direct source/test/config/doc analogs plus planning maps and
architecture records.
**Pattern extraction date:** 2026-08-29
