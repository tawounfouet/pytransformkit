from __future__ import annotations

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

import pytransformkit
from pytransformkit.cli.app import app

runner = CliRunner()


def test_root_without_arguments_shows_help_and_succeeds() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "PyTransformKit developer CLI." in result.stdout
    assert "version" in result.stdout
    assert "doctor" in result.stdout
    assert "schema" in result.stdout


def test_root_help_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "PyTransformKit developer CLI." in result.stdout
    assert "version" in result.stdout


def test_version_command_remains_available_from_root_app() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert f"PyTransformKit {pytransformkit.__version__}" in result.stdout
