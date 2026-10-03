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


def test_root_help_succeeds() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "PyTransformKit developer CLI." in result.stdout
    assert "version" in result.stdout


def test_version_command_reports_installed_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"PyTransformKit {pytransformkit.__version__}"
