# Phase 20: Installed Artifact Parity & Release Proof - Pattern Map

**Mapped:** 2026-09-04  
**Files analyzed:** 18 planned/new or modified files  
**Analogs found:** 18 / 18 (8 exact or near-exact; 10 role/config/document analogs)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| setup.py | config/build backend | transform (source -> wheel extension) | setup.py:27-49 | exact |
| tools/build_modes.py | utility/config | request-response (env -> BuildMode) | tools/build_modes.py:25-73 | exact (preserve; change only if needed) |
| tools/artifact_conformance.py | utility/collector | transform (runtime scenarios -> normalized JSON) | tests/test_graph_invariants.py:18-39; tests/test_transition_lifecycle.py:52-80 | role-match; new seam |
| tools/release_evidence.py | service/utility | file-I/O + request-response | tools/release_evidence.py:318-455,2492-2913 | exact |
| tests/test_build_modes.py | test | batch/build verification | tests/test_build_modes.py:72-198 | exact |
| tests/test_artifact_conformance.py | test | transform/parity comparison | tests/test_graph_invariants.py:50-182; tests/test_transition_lifecycle.py:188-260 | role-match |
| tests/test_installed_artifacts.py | test | file-I/O/request-response | tests/test_release_evidence.py:98-155,1842-1929 | role-match |
| tests/test_release_evidence.py | test | file-I/O/request-response | same file:1474-1810,2320-2455 | exact |
| tests/test_performance_benchmarks.py | test | benchmark/size-scaling | tests/test_performance_benchmarks.py:379-435 | exact |
| .github/workflows/release.yml | config/orchestration | event-driven fan-out/fan-in | .github/workflows/release.yml:17-145 | exact |
| Taskfile.yml | config/orchestration | batch/request-response | Taskfile.yml:119-158 | exact |
| pyproject.toml | config/metadata | static identity/dependency declaration | pyproject.toml:1-51 | exact |
| evidence/release-baseline.json | data/manifest | file-I/O/aggregation input | evidence/release-baseline.json:1-79 | exact |
| docs/conf.py | config/metadata | static identity | docs/conf.py:6-27 | exact |
| CHANGELOG.md | documentation/release metadata | static identity | CHANGELOG.md:1-26 | exact |
| README.md | documentation/claims | static claims -> user docs | README.md:10-23,584-626 | role-match |
| docs/dev/releasing.md | documentation/runbook | request-response procedure | docs/dev/releasing.md:16-70,72-90 | exact |
| docs/dev/testing.md | documentation/runbook | request-response procedure | docs/dev/testing.md:130-170,214-220 | exact |

tools/build_modes.py and src/fast_fsm/__init__.py are existing identity seams to preserve. __version__ is metadata-derived (src/fast_fsm/__init__.py:61-66) and must be verified from the installed environment, not duplicated.

## Pattern Assignments

### setup.py (build backend, transform)

**Analog:** setup.py:7-49; selector analog tools/build_modes.py:25-73.

**Imports and path setup** (setup.py:7-14):

    _SETUP_ROOT = Path(__file__).resolve().parent
    if str(_SETUP_ROOT) not in sys.path:
        sys.path.insert(0, str(_SETUP_ROOT))
    from tools.build_modes import BuildMode, resolve_build_mode  # noqa: E402

Keep this sdist-safe import arrangement. The sdist must carry tools/__init__.py and tools/build_modes.py, as already asserted by tests/test_build_modes.py:146-176.

**Selective compilation seam** (setup.py:16-39):

    build_mode = resolve_build_mode(os.environ)
    ext_modules = []
    if build_mode is not BuildMode.PURE:
        ext_modules = mypycify(
            ["src/fast_fsm/core.py"],
            opt_level="3",
            debug_level="1",
            separate=False,
            multi_file=False,
        )

Copy the one-file boundary exactly. conditions.py and condition_templates.py remain interpreted so user subclasses continue to work.

**Fail-closed error pattern:** current setup.py:40-47 catches every exception and warns/falls back. Change the exception branch so BuildMode.COMPILED re-raises (or raises a build-specific error) and only AUTO retains warning/fallback. Preserve PURE as no mypycify call. Add a negative fake-mypyc test beside _setup_extensions() (tests/test_build_modes.py:72-102) that proves compiled failure exits nonzero and does not emit a pure artifact.

### tools/build_modes.py (utility/config, request-response)

**Analog:** tools/build_modes.py:9-18,25-73.

    class BuildMode(str, Enum):
        AUTO = "auto"
        PURE = "pure"
        COMPILED = "compiled"

    def resolve_build_mode(environ: Mapping[str, str]) -> BuildMode:
        explicit_value = environ.get(_BUILD_MODE_ENV)
        legacy_value = environ.get(_LEGACY_PURE_ENV)
        ...
        if explicit_mode is None:
            return legacy_mode or BuildMode.AUTO
        ...
        return explicit_mode

Use the existing exact vocabulary and conflict rejection. Do not introduce native, fallback, or implicit auto behavior into artifact proof. If adding a helper, keep it pure over an injected Mapping[str, str] so tests remain Python 3.10-compatible and deterministic.

### tools/artifact_conformance.py (collector, transform)

**Closest analogs:** tests/test_graph_invariants.py:18-39 (stable graph fingerprint), tests/test_transition_lifecycle.py:52-80 (observable recorder and typed helper), tests/test_visualization.py:47-79 (small deterministic fixtures), and tests/test_logging_config.py:50-60 (real infrastructure, no mocks).

**Stable-record pattern from graph tests** (tests/test_graph_invariants.py:18-39):

    def graph_fingerprint(machine: StateMachine) -> tuple[Any, ...]:
        transitions = tuple(sorted(
            (source_name, trigger, id(entry.to_state),
             id(entry.condition) if entry.condition is not None else None)
            for source_name, entries in machine._transitions.items()
            for trigger, entry in entries.items()
        ))
        snapshot = machine._graph_snapshot()
        return (..., machine._graph_version, id(machine.current_state), snapshot)

The collector must turn observations into allowlisted scalar records, not expose id(), repr(), absolute paths, exception addresses, timings, or caller payloads. Use stable scenario IDs, sorted collections, named outcome/stage fields, and a canonical JSON/digest for the scenario definition. Run the same collector for source-pure, installed-pure, installed-compiled, sync, async, builder, and declarative adapters.

**Lifecycle and redaction pattern** (tests/test_transition_lifecycle.py:188-260):

    failure = _DestinationEnterFailure("destination-secret")
    ...
    result = machine.trigger("advance", payload="caller-secret")
    assert result.success is False
    assert result.committed is True
    assert result.stage == "destination-enter"
    assert result.cause is failure
    assert "destination-secret" not in repr(result)
    assert "destination-secret" not in caplog.text

Normalize lifecycle success, committed, stage, history tuples, and redaction verdicts into explicit record fields. Keep secret strings inside the fixture only, never in emitted records.

**Scenario families:** copy real-object construction from tests/test_builder.py:40-119 for builder/declarative paths, tests/test_async.py:36-71,87-128 for sync/async conditions, tests/test_ownership_concurrency.py:254-300 for ownership/reentry, tests/test_visualization.py:87-180 for grammar-safe output, and tests/test_logging_config.py:50-114 for logging. The collector must be checkout-independent when run in an installed artifact environment; never import test modules or helpers.

### tools/release_evidence.py (artifact verifier/aggregator, file-I/O + request-response)

**Analog:** existing archive identity and deterministic CLI authority in tools/release_evidence.py:254-455,2492-2770,2792-2913.

**Imports/constants and error type** (tools/release_evidence.py:1-60):

    from importlib import machinery, metadata
    from packaging.utils import InvalidWheelFilename, canonicalize_name, parse_wheel_filename
    ...
    REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
    PACKAGE_NAME = "fast_fsm"
    CORE_MODULE_NAME = f"{PACKAGE_NAME}.core"
    REQUIRED_UV_VERSION = "0.12.6"
    MANIFEST_SCHEMA_VERSION = 1

    class EvidenceError(RuntimeError):
        """Raised when local release evidence is incomplete or contradictory."""

Extend this authority rather than creating a second manifest serializer or wheel parser. Retain EvidenceError for all fail-closed domain errors and keep schema versioning explicit.

**Archive inspection** (tools/release_evidence.py:318-428):

    filename_name, filename_version, filename_tags = _wheel_filename_identity(resolved_wheel)
    with ZipFile(resolved_wheel) as archive:
        dist_info_directory = _archive_dist_info_directory(archive)
        wheel_headers = Parser().parsestr(
            _archive_metadata(archive, dist_info_directory, "WHEEL")
        )
        package_headers = Parser().parsestr(
            _archive_metadata(archive, dist_info_directory, "METADATA")
        )
        native_members = tuple(
            sorted(name for name in archive.namelist() if _is_native_member(name))
        )

Continue using packaging.utils.parse_wheel_filename; cross-check filename/dist-info/METADATA versions and tags, and classify py3-none-any as pure only when it has no native members. For platform wheels, require native members before installation; after installation independently assert the loader/origin is an extension inside the fresh environment.

Source preflight ordering (tools/release_evidence.py:2492-2516) and manifest collection (tools/release_evidence.py:2598-2662) are the sequencing model: validate origin first, then collect facts, artifact identity, slots, benchmark, and toolchain. Phase 20 adds a parent verifier that hashes the exact artifact, creates a fresh uv environment, installs the absolute path from a neutral cwd, invokes a checkout-independent child collector, and validates child JSON before performance claims.

**Deterministic write/check and CLI** (tools/release_evidence.py:2722-2764,2767-2781,2792-2913):

    def _read_manifest(path: Path) -> dict[str, Any]:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_non_standard_number,
        )
        if not isinstance(payload, dict):
            raise EvidenceError(f"Manifest {path} must contain a JSON object.")
        return payload

    def write_or_check_manifest(..., write: bool) -> dict[str, Any]:
        validate_performance_observation(manifest)
        if write:
            _write_manifest(manifest_path, manifest)
            return dict(manifest)
        baseline = _read_manifest(manifest_path)
        ...

Preserve sorted, strict JSON and read-only check mode. Add explicit subcommands/entry points for installed artifact verification, sdist derivation, matrix aggregation, and identity/tag checks; emit a human summary only from validated machine-readable records.

Bind each record to artifact filename and SHA-256, wheel/sdist tags, interpreter/platform/machine, installed distribution metadata version, fast_fsm.__version__, package and fast_fsm.core origins, asserted pure/compiled type, build intent, conformance digest/result, and derivation parent for sdist children. Reject missing, contradictory, duplicate, unexpected, or mixed-version records.

### tests/test_build_modes.py (build test, batch/file-I/O)

**Analog:** existing subprocess and archive fixtures (tests/test_build_modes.py:72-198).

    completed = subprocess.run(
        [sys.executable, "setup.py", "--name"],
        cwd=ROOT,
        env={**os.environ, "FAST_FSM_BUILD_MODE": "invalid"},
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0

Use argument arrays, cwd=ROOT, copied environment with only selector changed, and assert stderr/exit status. Extend _setup_extensions() with fake mypycify that raises: pure skips compilation, auto warns/falls back, and compiled fails. Keep the existing sdist extraction/build test (tests/test_build_modes.py:146-198) and add explicit compiled derivation assertions where needed.

### tests/test_artifact_conformance.py (test, transform/parity)

**Closest analogs:** graph rejection/fingerprint tests (tests/test_graph_invariants.py:50-182), lifecycle record assertions (tests/test_transition_lifecycle.py:188-260), and parametrized async helpers (tests/test_async.py:87-180).

    first = machine._graph_snapshot()
    second = machine._graph_snapshot()
    assert first is not second
    ...
    assert machine.current_state is destination
    assert [
        (record.from_state, record.trigger, record.to_state)
        for record in machine.history
    ] == [...]

Test scenario IDs, canonical output, schema, suite digest, redaction, and equality of source-pure versus installed records. Use deterministic fixtures and pytest.mark.parametrize; do not compare paths, reprs, object identity, or elapsed time. Include negative cases for a missing/extra field, leaked payload, unsorted collection, and changed oracle digest.

### tests/test_installed_artifacts.py (integration test, file-I/O/request-response)

**Analog:** tests/test_release_evidence.py:98-155 subprocess/wheel fixture helpers and :1842-1929 call-order/temporary-wheel tests; isolation analog tools/phase16_isolated_verify.py:137-218,236-265.

    def _run_evidence(*arguments: str, environ: dict[str, str] | None = None):
        return subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            cwd=ROOT,
            env={**os.environ, **(environ or {})},
            text=True,
            capture_output=True,
            check=False,
        )

Use TemporaryDirectory/tmp_path, absolute artifact paths, array-form subprocesses, neutral cwd, and sanitized PYTHONPATH/VIRTUAL_ENV. Assert package and core origins are descendants of the new environment, direct-url/editable metadata does not point at checkout, pure mode has .py origin/no native shadow, compiled mode has extension loader/origin, and metadata/version/architecture/type/build-intent all agree. Test missing native extension, checkout leakage, stale native shadow, wrong version/tag, wrong architecture, duplicate evidence, and sdist parent/child lineage fail closed.

### tests/test_release_evidence.py (release evidence regression, file-I/O/request-response)

**Analog:** same file, with deterministic serialization (tests/test_release_evidence.py:1474-1484), mutation/freshness checks (:1651-1810), preflight ordering (:1842-1869), wheel selection (:1872-1929), and workflow/action contracts (:2320-2455).

    first = serialize_manifest(fixture)
    second = serialize_manifest(dict(reversed(list(fixture.items()))))
    assert first == second
    assert first.endswith("\n")
    assert list(json.loads(first)) == sorted(fixture)

Extend _manifest_fixture() with the Phase 20 schema. Add field-level negative fixtures for matrix missing/duplicate/unexpected records, SHA mismatch, mixed version/commit/tag/oracle digest, invalid origin/type, and incomplete identity. Keep tests proving failed checks never rewrite the tracked baseline. Update the immutable action pin fixture whenever cibuildwheel changes. Add release workflow assertions that native evidence and aggregation precede github_release, and no always() path can publish partial evidence.

### tests/test_performance_benchmarks.py (benchmark/invariant test, benchmark + size-scaling)

**Analog:** existing blocking floor (tests/test_performance_benchmarks.py:379-435) and simple construction/lookup loops (:731-799).

    for _ in range(1000):
        fsm.trigger("toggle")
    gc.collect()
    iterations = 200_000
    start = time.perf_counter()
    for _ in range(iterations):
        fsm.trigger("toggle")
    elapsed = time.perf_counter() - start
    ops_per_sec = iterations / elapsed

Retain real FSM fixtures, warmup, gc.collect(), perf_counter(), and environment labeling. Move the blocking >= 200,000 assertion to the installed compiled verifier after native-origin assertion; pure rates remain observations. Add deterministic invariant/size-scaling checks for trigger(), can_trigger(), add_state(), and add_transition() and keep diagnostic-budget boundary tests separate from hot-path timing.

### .github/workflows/release.yml (workflow config, event-driven fan-out/fan-in)

**Analog:** current matrix/artifact flow (.github/workflows/release.yml:17-81), sdist setup (:83-112), and release job (:114-145).

    build_wheels:
      needs: quality_gate
      strategy:
        fail-fast: false
        matrix:
          include:
            - os: ubuntu-latest
              cibw_archs: "x86_64 aarch64"
            - os: windows-latest
              cibw_archs: "AMD64"
            - os: macos-14
              cibw_archs: "x86_64 arm64 universal2"

Keep full-length action SHA pins and the declared CPython/platform matrix as the single expected matrix. Split build from native execution: every produced artifact must run the shared verifier on a matching native runner; cross-build/QEMU skips cannot count as behavior proof. Upload one evidence JSON per artifact, download/aggregate exact expected keys, and make github_release.needs depend on quality, all builds, native verification, identity, conformance, performance, and aggregate success. Preserve top-level contents: read and write permission only in final release job (release.yml:8-10,114-121).

### Taskfile.yml (workflow config, batch)

**Analog:** explicit uv task wrappers and preflight ordering (Taskfile.yml:119-158).

    release-baseline-check:
      env:
        FAST_FSM_BUILD_MODE: pure
      cmds:
        - uv sync --locked --all-groups
        - uv run python {{.EVIDENCE_TOOL}} verify-source --json
        - uv run python {{.EVIDENCE_TOOL}} evidence --check --manifest {{.EVIDENCE_MANIFEST}} --build-wheel

Add stable local entry points for artifact verification/aggregation using uv and exact paths. Keep pure-mode source preflight immediately after sync, no broad cleanup, and no direct python/pip invocation. Keep tests sequential and preserve release-baseline write/check semantics.

### pyproject.toml, docs/conf.py, CHANGELOG.md (metadata/config, static identity)

**Analogs:** current metadata (pyproject.toml:1-9,22-45), Sphinx identity (docs/conf.py:10-15), and Keep-a-Changelog sections (CHANGELOG.md:6-26).

    [project]
    name = "fast_fsm"
    version = "0.2.2"
    requires-python = ">=3.10"

    project = "Fast FSM"
    release = "0.1.0"

Coordinate the v0.3.0 update across package metadata, Sphinx version/release, changelog release section, manifest identity/schema, and any public release claim. Preserve locked build pins (setuptools==80.9.0, wheel==0.45.1, mypy[mypyc]==1.17.1) and the single runtime dependency. If deriving Sphinx version from package metadata, test the derivation; otherwise assert both fields directly. Tag-time checks additionally bind tag object to verified commit.

### evidence/release-baseline.json (manifest data, file-I/O)

**Analog:** current deterministic manifest (evidence/release-baseline.json:1-79).

    "artifact_evidence": {"source": {"core_origin": "src/fast_fsm/core.py"}, "wheels": [...]},
    "performance_contract": {"compiled_trigger_ops_per_sec_min": 200000, "observation": {...}},
    "release_identity": {"distribution_version": "0.2.2", "package": "fast_fsm"},
    "schema_version": 1

Evolve the schema deterministically to hold per-artifact SHA/tag/runtime identity, conformance/oracle digests, native performance records, complete expected matrix, historical Phase 16-19 evidence, and tag/commit identity. Do not hand-edit volatile timings into narrative docs; generate human summary from validated records. Keep strict JSON, sorted serialization, and immutable source bytes for read-only freshness checks.

### README.md, docs/dev/releasing.md, docs/dev/testing.md (documentation, request-response)

**Analogs:** README durable-vs-volatile claim split (README.md:10-23,584-626), release procedure (docs/dev/releasing.md:16-70), and phase-boundary wording (docs/dev/testing.md:139-170,214-220).

    Exact test, coverage, toolchain, source-origin, artifact-mode, and collected
    environment-labeled benchmark observations are recorded in the tracked
    evidence/release-baseline.json manifest.

    export FAST_FSM_BUILD_MODE=pure
    uv sync --locked --all-groups
    uv run python tools/release_evidence.py verify-source --json

Preserve the rule that durable docs state contracts while exact counts/timings live in JSON. Extend the runbook with absolute-artifact fresh-environment installation, neutral cwd/source-path exclusion, sdist pure/compiled derivation, native runner proof, strict matrix aggregation, and tag-to-verified-commit identity. Update testing guide to state source-tree conformance is prerequisite evidence, not installed-artifact proof. Keep documented build-mode vocabulary, uv-only commands, and no destructive cleanup.

## Shared Patterns

### Fail-closed domain errors

**Sources:** tools/release_evidence.py:60-62, tools/phase16_isolated_verify.py:123-125.

    class EvidenceError(RuntimeError):
        """Raised when local release evidence is incomplete or contradictory."""

    class VerificationError(RuntimeError):
        """Raised when an isolation precondition cannot be established."""

Use typed errors with actionable field/path/scenario context. Convert them to exit 1 only at CLI boundary (tools/release_evidence.py:2881-2913); never catch a compiled build failure and continue under a compiled claim.

### Isolated subprocesses and origin containment

**Sources:** tools/phase16_isolated_verify.py:137-145,209-218,236-265; tools/release_evidence.py:2492-2516.

    return subprocess.run(command, cwd=cwd, env=env, text=True, check=check)

Build/resolve artifacts before leaving checkout, invoke fresh environment absolute interpreter from neutral temporary cwd, remove PYTHONPATH and VIRTUAL_ENV, and assert package/core origins are descendants of that environment. Check distribution metadata/direct-url provenance as well as __file__; a fresh venv alone is insufficient.

### Deterministic evidence serialization

**Sources:** tools/release_evidence.py:2722-2770; tests/test_release_evidence.py:1474-1484,1651-1667.

Use strict JSON parsing (parse_constant rejects nonstandard values), sorted keys/collections, one trailing newline, field-level difference reporting, and write/check separation. SHA-256 binds evidence to exact artifact bytes but is not a publisher signature; do not overclaim its meaning.

### Shared conformance and redaction

**Sources:** tests/test_graph_invariants.py:18-39, tests/test_transition_lifecycle.py:217-260, tests/test_visualization.py:170-180, tests/test_logging_config.py:102-114.

Scenario records include only stable IDs, allowlisted named outcomes, sorted topology/history, grammar validity/digests, and logging redaction verdicts. Exclude payloads, reprs, paths, exception addresses, timestamps, and performance measurements from semantic parity. Record performance beside the parity digest and compare only declared mode/origin/artifact differences.

### Native performance gate

**Sources:** tests/test_performance_benchmarks.py:379-435; tools/release_evidence.py:2545-2595.

Warm up, collect, run fixed or multi-sample batch, and label implementation/Python/platform/machine. Assert native origin before timing. Only an installed compiled wheel on a matching native runner can satisfy >= 200,000 operations/sec; pure/source-tree observations remain historical/environment-labelled evidence.

### Workflow permissions and dependency gates

**Sources:** .github/workflows/release.yml:8-10,114-145; tests/test_release_evidence.py:2320-2455.

Keep action refs pinned to reviewed 40-character SHAs with version comments. Use ordinary successful needs dependencies (no always() release escape), artifact upload/download for evidence transfer, top-level read permissions, and write permission only at final release creation.

## No Exact Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| tools/artifact_conformance.py | utility/collector | transform | No existing checkout-independent installed-artifact semantic collector; compose stable-record patterns from graph/lifecycle/visualization/logging tests above. |
| tests/test_installed_artifacts.py | integration test | file-I/O/request-response | Existing tests exercise archive inspection and isolated source trees, but no exact-path fresh installation/origin containment test exists. |

These are role-match assignments, not invitations to duplicate test inventories: they must call one collector and reuse release_evidence.py identity/serialization helpers.

## Metadata

**Analog search scope:** setup.py, pyproject.toml, tools/, tests/, .github/workflows/, Taskfile.yml, evidence/, README.md, CHANGELOG.md, docs/conf.py, docs/dev/.  
**Files scanned:** 18 planned files plus supporting Phase 16-19 test/proof files.  
**Pattern extraction date:** 2026-09-04

