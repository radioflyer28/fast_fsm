"""Offline contract tests for isolated competitor comparison evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 only
    import tomli as tomllib

import pytest
import yaml

BENCHMARK_ROOT = Path(__file__).parents[1] / "benchmarks"
REPOSITORY_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(BENCHMARK_ROOT))

from comparison import common  # noqa: E402
from comparison import fast_fsm_runner  # noqa: E402
from comparison import run_comparison  # noqa: E402


def supported_scenario(
    scenario_id: str,
    preflight: dict[str, object],
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "status": "supported",
        "preflight": preflight,
        "unsupported_reason": None,
        "warmup_operations": 1,
        "operations": 2,
        "samples_ns": [100.0, 120.0, 110.0],
        "median_ns": 110.0,
        "operations_per_second": 2_000_000_000 / 110.0,
    }


def unsupported_scenario(scenario_id: str) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "status": "unsupported",
        "preflight": {},
        "unsupported_reason": "api-unavailable",
        "warmup_operations": None,
        "operations": None,
        "samples_ns": None,
        "median_ns": None,
        "operations_per_second": None,
    }


def fixture_record(
    implementation_id: str = "python-statemachine-2.5.0",
) -> dict[str, object]:
    if implementation_id == "fast-fsm":
        distribution = "fast-fsm"
        version = "0.5.0"
        origin = str(Path(tempfile.gettempdir()) / "fast_fsm" / "core.py")
    else:
        distribution = "python-statemachine"
        version = implementation_id.rsplit("-", 1)[1]
        origin = str(
            Path(tempfile.gettempdir())
            / implementation_id
            / "statemachine"
            / "__init__.py"
        )
    return {
        "schema_version": common.COMPARISON_SCHEMA_VERSION,
        "implementation_id": implementation_id,
        "requested_distribution": distribution,
        "requested_version": version,
        "resolved_version": version,
        "module_origin": origin,
        "module_loader": "SourceFileLoader",
        "python_implementation": "cpython",
        "python_version": "3.12.10",
        "platform": "Darwin",
        "machine": "arm64",
        "command": ["fixture-child"],
        "observation_only": True,
        "scenarios": [
            supported_scenario(
                "flat-alternating-cycle",
                {"initial": "idle", "after_first": "active", "after_second": "idle"},
            ),
            supported_scenario(
                "false-guard-no-transition",
                {"guard_calls": 1, "state": "idle", "transition_callbacks": 0},
            ),
            unsupported_scenario("final-state-rejection"),
        ],
    }


def test_schema_accepts_exact_supported_and_unsupported_cells() -> None:
    record = fixture_record()
    assert common.validate_child_record(record) == record


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda record: record.update(extra=True), "record fields"),
        (
            lambda record: record.update(resolved_version="3.2.1"),
            "resolved version",
        ),
        (
            lambda record: record.update(module_origin="relative.py"),
            "module origin",
        ),
        (
            lambda record: record["scenarios"][0].update(operations=True),
            "operation count",
        ),
        (
            lambda record: record["scenarios"][0].update(samples_ns=[math.nan]),
            "samples",
        ),
        (
            lambda record: record["scenarios"][0].update(status="unsupported"),
            "required scenario",
        ),
        (
            lambda record: record["scenarios"][2].update(
                samples_ns=[1.0], median_ns=1.0
            ),
            "unsupported scenario",
        ),
    ],
)
def test_schema_rejects_malformed_or_contradictory_records(
    mutate: Any,
    match: str,
) -> None:
    record = fixture_record()
    mutate(record)
    with pytest.raises(common.ComparisonContractError, match=match):
        common.validate_child_record(record)


def test_canonical_json_is_deterministic_and_finite() -> None:
    assert common.canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    with pytest.raises(ValueError):
        common.canonical_json({"sample": math.inf})


def test_measure_scenario_validates_counts_and_returns_finite_samples() -> None:
    calls = 0

    def operation() -> None:
        nonlocal calls
        calls += 1

    measured = common.measure_scenario(operation, warmup=1, operations=2, samples=3)
    assert calls == 7
    assert len(measured["samples_ns"]) == 3
    assert measured["median_ns"] > 0
    assert measured["operations_per_second"] > 0
    with pytest.raises(common.ComparisonContractError, match="operation count"):
        common.measure_scenario(operation, warmup=True, operations=2, samples=3)


def test_fast_fsm_preflight_contradiction_prevents_sampling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sampled: list[bool] = []
    monkeypatch.setattr(
        fast_fsm_runner,
        "_preflight_false_guard",
        lambda: (
            {"guard_calls": 2, "state": "idle", "transition_callbacks": 0},
            lambda: None,
        ),
    )
    monkeypatch.setattr(
        fast_fsm_runner,
        "measure_scenario",
        lambda *args, **kwargs: sampled.append(True),
    )

    with pytest.raises(common.ComparisonContractError, match="preflight"):
        fast_fsm_runner.build_record(
            argparse.Namespace(warmup=1, operations=2, samples=3)
        )
    assert sampled == []


def test_fast_fsm_record_proves_false_guard_before_measurement() -> None:
    record = fast_fsm_runner.build_record(
        argparse.Namespace(warmup=1, operations=2, samples=3)
    )
    checked = common.validate_child_record(record)
    false_guard = next(
        scenario
        for scenario in checked["scenarios"]
        if scenario["scenario_id"] == "false-guard-no-transition"
    )
    assert false_guard["preflight"] == {
        "guard_calls": 1,
        "state": "idle",
        "transition_callbacks": 0,
    }
    assert Path(str(checked["module_origin"])).is_absolute()


def comparison_args() -> argparse.Namespace:
    return argparse.Namespace(warmup=1, operations=2, samples=3)


def test_exact_version_children_have_distinct_locked_script_commands() -> None:
    commands = run_comparison.build_child_commands(comparison_args())

    assert set(commands) == {
        "fast-fsm",
        "python-statemachine-2.5.0",
        "python-statemachine-3.2.1",
    }
    fast = commands["fast-fsm"]
    assert fast[:5] == [
        "uv",
        "run",
        "--locked",
        "--project",
        str(Path(__file__).parents[1].resolve()),
    ]
    assert Path(fast[6]).name == "fast_fsm_runner.py"
    for version, implementation_id in (
        ("2_5", "python-statemachine-2.5.0"),
        ("3_2", "python-statemachine-3.2.1"),
    ):
        command = commands[implementation_id]
        assert command[:3] == ["uv", "run", "--locked"]
        assert command[3] == "--script"
        assert Path(command[4]).name == f"python_statemachine_{version}.py"


@pytest.mark.parametrize(
    ("filename", "version"),
    [
        ("python_statemachine_2_5.py", "2.5.0"),
        ("python_statemachine_3_2.py", "3.2.1"),
    ],
)
def test_exact_version_child_metadata_is_self_contained(
    filename: str, version: str
) -> None:
    source = (BENCHMARK_ROOT / "comparison" / filename).read_text()
    assert f'"python-statemachine=={version}"' in source
    assert "import fast_fsm" not in source
    assert "from fast_fsm" not in source
    other = "3.2.1" if version == "2.5.0" else "2.5.0"
    assert f'"python-statemachine=={other}"' not in source


def test_project_groups_exclude_competitors() -> None:
    """Ordinary dependency groups do not install isolated comparators."""
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    grouped_requirements = {
        requirement.split("[", 1)[0].split("=", 1)[0].split(">", 1)[0]
        for requirements in project["dependency-groups"].values()
        for requirement in requirements
    }

    assert "python-statemachine" not in grouped_requirements
    assert "transitions" not in grouped_requirements


def test_project_lock_excludes_comparator_packages() -> None:
    """The ordinary project resolution has no comparator transitive lane."""
    project_lock = tomllib.loads((REPOSITORY_ROOT / "uv.lock").read_text())
    package_names = {package["name"] for package in project_lock["package"]}

    assert "python-statemachine" not in package_names
    assert "transitions" not in package_names


@pytest.mark.parametrize(
    ("script_name", "version"),
    [
        ("python_statemachine_2_5.py", "2.5.0"),
        ("python_statemachine_3_2.py", "3.2.1"),
    ],
)
def test_adjacent_script_lock_resolves_exact_approved_version(
    script_name: str, version: str
) -> None:
    """Each generated adjacent lock belongs to one exact PEP 723 lane."""
    lock_path = BENCHMARK_ROOT / "comparison" / f"{script_name}.lock"
    locked = tomllib.loads(lock_path.read_text())
    packages = {package["name"]: package for package in locked["package"]}

    assert packages["python-statemachine"]["version"] == version
    assert set(packages) == {"python-statemachine"}


def test_parent_builds_ratios_only_after_identity_and_required_semantics() -> None:
    records = [
        fixture_record("fast-fsm"),
        fixture_record("python-statemachine-2.5.0"),
        fixture_record("python-statemachine-3.2.1"),
    ]

    report = run_comparison.build_comparison_report(records)

    assert report["observation_only"] is True
    comparisons = {
        comparison["scenario_id"]: comparison
        for comparison in report["scenario_comparisons"]
    }
    assert set(comparisons) == {
        "flat-alternating-cycle",
        "false-guard-no-transition",
        "final-state-rejection",
    }
    for scenario_id in common.REQUIRED_SCENARIO_IDS:
        comparison = comparisons[scenario_id]
        assert comparison["status"] == "supported"
        assert comparison["unsupported_reason"] is None
        assert comparison["required_values"] == common.EXPECTED_PREFLIGHTS[scenario_id]
        assert set(comparison["ratios"]) == {
            "python-statemachine-2.5.0",
            "python-statemachine-3.2.1",
        }
    optional = comparisons["final-state-rejection"]
    assert optional["status"] == "unsupported"
    assert optional["ratios"] == {}
    assert optional["medians_ns"] == {}
    assert optional["operations_per_second"] == {}
    assert optional["unsupported_reason"] == {
        implementation: "api-unavailable"
        for implementation in (
            "fast-fsm",
            "python-statemachine-2.5.0",
            "python-statemachine-3.2.1",
        )
    }


def test_parent_rejects_shared_origin_and_required_preflight_contradiction() -> None:
    fast = fixture_record("fast-fsm")
    old = fixture_record("python-statemachine-2.5.0")
    current = fixture_record("python-statemachine-3.2.1")
    current["module_origin"] = old["module_origin"]
    with pytest.raises(common.ComparisonContractError, match="distinct origin"):
        run_comparison.build_comparison_report([fast, old, current])

    current = fixture_record("python-statemachine-3.2.1")
    current["scenarios"][1]["preflight"]["guard_calls"] = 2
    with pytest.raises(common.ComparisonContractError, match="preflight"):
        run_comparison.build_comparison_report([fast, old, current])


def test_run_child_bounds_and_validates_subprocess_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = fixture_record()
    emit_argument = [sys.executable, "-c", "import sys; print(sys.argv[1])"]
    assert run_comparison.run_child([*emit_argument, json.dumps(valid)]) == valid

    with pytest.raises(common.ComparisonContractError, match="stdout"):
        run_comparison.run_child([*emit_argument, "{} trailing"])

    monkeypatch.setattr(run_comparison, "MAX_CHILD_OUTPUT_BYTES", 64)
    monkeypatch.setattr(run_comparison, "CHILD_TIMEOUT_SECONDS", 2)
    started = time.monotonic()
    with pytest.raises(common.ComparisonContractError, match="stdout"):
        run_comparison.run_child(
            [
                sys.executable,
                "-c",
                "import sys, time; "
                "sys.stdout.write('x' * 4096); sys.stdout.flush(); time.sleep(10)",
            ]
        )
    assert time.monotonic() - started < 1.5

    with pytest.raises(
        common.ComparisonContractError, match="child process failed"
    ) as error:
        run_comparison.run_child(
            [sys.executable, "-c", "import sys; print('caller secret'); sys.exit(2)"]
        )
    assert "caller secret" not in str(error.value)


def test_run_child_redacts_process_launch_failures() -> None:
    missing = "fast-fsm-deliberately-missing-child-executable"
    with pytest.raises(
        common.ComparisonContractError, match="child process could not start"
    ) as error:
        run_comparison.run_child([missing])
    assert missing not in str(error.value)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX session regression")
def test_run_child_timeout_survives_detached_pipe_holding_descendant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(run_comparison, "CHILD_TIMEOUT_SECONDS", 0.1)
    descendant = (
        "import subprocess, sys; "
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(2)'], "
        "start_new_session=True); print('parent-exits', flush=True)"
    )
    started = time.monotonic()
    with pytest.raises(common.ComparisonContractError, match="timed out"):
        run_comparison.run_child([sys.executable, "-c", descendant])
    assert time.monotonic() - started < 0.75


def test_neutral_cwd_fast_child_smoke_resolves_repository_origin(
    tmp_path: Path,
) -> None:
    command = run_comparison.build_child_commands(comparison_args())["fast-fsm"]
    completed = subprocess.run(
        command,
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    record = common.validate_child_record(json.loads(completed.stdout))

    assert record["implementation_id"] == "fast-fsm"
    assert record["requested_version"] == record["resolved_version"]
    assert Path(str(record["module_origin"])).is_relative_to(
        Path(__file__).parents[1].resolve()
    )


def test_stdout_default_and_explicit_output_use_the_same_canonical_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The parent persists nothing unless an output path is explicit."""

    def install_fixture_children() -> None:
        records = iter(
            [
                fixture_record("fast-fsm"),
                fixture_record("python-statemachine-2.5.0"),
                fixture_record("python-statemachine-3.2.1"),
            ]
        )
        monkeypatch.setattr(run_comparison, "run_child", lambda _command: next(records))

    monkeypatch.chdir(tmp_path)
    install_fixture_children()
    run_comparison.main(["--warmup", "1", "--operations", "2", "--samples", "1"])
    stdout_only = capsys.readouterr().out
    report = json.loads(stdout_only)
    assert set(report) == {
        "schema_version",
        "observation_only",
        "generated_at_utc",
        "command",
        "implementations",
        "scenario_comparisons",
    }
    assert list(tmp_path.iterdir()) == []

    output = tmp_path / "explicit-report.json"
    install_fixture_children()
    run_comparison.main(
        [
            "--warmup",
            "1",
            "--operations",
            "2",
            "--samples",
            "1",
            "--output",
            str(output),
        ]
    )
    explicit_stdout = capsys.readouterr().out
    assert output.read_text() == explicit_stdout
    assert json.loads(explicit_stdout)["observation_only"] is True


def test_manual_task_and_compatibility_runner_have_one_comparison_path() -> None:
    """Only the manual Task entry point reaches the isolated parent."""
    taskfile = yaml.safe_load((REPOSITORY_ROOT / "Taskfile.yml").read_text())
    tasks = taskfile["tasks"]
    comparison = json.dumps(tasks["benchmark-compare"], sort_keys=True)
    assert "run_comparison.py" in comparison
    assert "CLI_ARGS" in comparison
    assert "manual" in comparison.lower()
    assert "observ" in comparison.lower()

    forbidden = (
        "benchmark-compare",
        "run_comparison.py",
        "python_statemachine_2_5.py",
        "python_statemachine_3_2.py",
    )
    for task_name, definition in tasks.items():
        if task_name == "benchmark-compare":
            continue
        serialized = json.dumps(definition, sort_keys=True)
        assert all(token not in serialized for token in forbidden)

    wrapper = (BENCHMARK_ROOT / "benchmark.py").read_text()
    assert "comparison.run_comparison import main" in wrapper
    assert "benchmark_results.json" not in wrapper
    assert "benchmark_py_fsm" not in wrapper
    assert "benchmark_transitions_fsm" not in wrapper


def test_ordinary_ci_and_release_paths_exclude_comparison_execution() -> None:
    """Required CI/release graphs contain no comparator execution edge."""
    ordinary_sources = [
        (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(),
        (REPOSITORY_ROOT / "tools" / "release_evidence.py").read_text(),
    ]
    forbidden = (
        "benchmark-compare",
        "run_comparison.py",
        "python_statemachine_2_5.py",
        "python_statemachine_3_2.py",
        "fast_over_competitor",
    )
    for source in ordinary_sources:
        assert all(token not in source for token in forbidden)
