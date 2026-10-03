from __future__ import annotations

import json

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

from pytransformkit.cli.app import app

runner = CliRunner()

CHECK_NAMES = [
    "pytransformkit",
    "python",
    "cli",
    "pyyaml",
    "pandas",
    "polars",
    "pyarrow",
    "duckdb",
]
CHECK_STATUSES = {
    "available",
    "missing",
    "incompatible",
    "error",
    "not_applicable",
}


def test_doctor_human_report_is_local_and_nonfatal_for_missing_optionals() -> None:
    result = runner.invoke(app, ["doctor", "--no-color"])

    assert result.exit_code == 0
    assert "Doctor:" in result.stdout
    for name in CHECK_NAMES:
        assert name in result.stdout
    assert result.stderr == ""
    assert "\x1b[" not in result.stdout


def test_doctor_json_uses_v1_report_contract_and_deterministic_order() -> None:
    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    assert result.stderr == ""
    assert "\x1b[" not in result.stdout

    payload = json.loads(result.stdout)
    assert payload["contract_version"] == 1
    assert payload["ok"] is True
    assert payload["command"] == "doctor"
    assert payload["data"]["status"] in {"healthy", "degraded", "error"}

    checks = payload["data"]["checks"]
    assert [check["name"] for check in checks] == CHECK_NAMES
    assert all(check["status"] in CHECK_STATUSES for check in checks)


def test_doctor_quiet_only_emits_summary() -> None:
    result = runner.invoke(app, ["doctor", "--quiet", "--no-color"])

    assert result.exit_code == 0
    assert result.stdout.strip() in {
        "Doctor: healthy",
        "Doctor: degraded",
    }
    assert "pytransformkit" not in result.stdout.lower()


def test_doctor_verbose_exposes_controlled_details_without_environment_dump() -> None:
    result = runner.invoke(app, ["doctor", "--verbose", "--no-color"])

    assert result.exit_code == 0
    assert "Detail" in result.stdout
    assert "PATH=" not in result.stdout
    assert "HOME=" not in result.stdout
    assert "SECRET" not in result.stdout


def test_doctor_debug_keeps_normal_report_semantics() -> None:
    result = runner.invoke(app, ["doctor", "--debug", "--no-color"])

    assert result.exit_code == 0
    assert "Doctor:" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize(
    "args",
    [
        ["doctor", "--quiet", "--verbose"],
        ["doctor", "--quiet", "--debug"],
        ["doctor", "--json", "--verbose"],
    ],
)
def test_doctor_rejects_contradictory_output_options(args: list[str]) -> None:
    result = runner.invoke(app, args)

    assert result.exit_code == 2


def test_doctor_help_is_available_without_schema_or_engine_activation() -> None:
    result = runner.invoke(app, ["doctor", "--help"])

    assert result.exit_code == 0
    assert "local PyTransformKit environment" in result.stdout
