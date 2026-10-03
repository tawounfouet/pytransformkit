from __future__ import annotations

import json
import platform

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

import pytransformkit
from pytransformkit.cli.app import app

runner = CliRunner()


def test_version_human_report_contains_package_and_python_versions() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert f"PyTransformKit {pytransformkit.__version__}" in result.stdout
    assert f"Python {platform.python_version()}" in result.stdout
    assert result.stderr == ""


def test_root_version_alias_matches_human_version_semantics() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert f"PyTransformKit {pytransformkit.__version__}" in result.stdout
    assert f"Python {platform.python_version()}" in result.stdout
    assert result.stderr == ""


def test_version_json_uses_cli_v1_report_envelope() -> None:
    result = runner.invoke(app, ["version", "--json"])

    assert result.exit_code == 0
    assert result.stderr == ""
    assert "\x1b[" not in result.stdout

    payload = json.loads(result.stdout)
    assert payload == {
        "contract_version": 1,
        "ok": True,
        "command": "version",
        "data": {
            "pytransformkit": pytransformkit.__version__,
            "python": platform.python_version(),
        },
    }


def test_version_no_color_has_no_ansi_sequences() -> None:
    result = runner.invoke(app, ["version", "--no-color"])

    assert result.exit_code == 0
    assert "\x1b[" not in result.stdout
