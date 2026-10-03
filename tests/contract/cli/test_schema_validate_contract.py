from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")
pytest.importorskip("yaml")

from typer.testing import CliRunner

from pytransformkit.cli.app import app

runner = CliRunner()

VALID_SCHEMA = """version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
"""

INVALID_SCHEMA = """version: 1
schema:
  name: customers
  fields:
    - name: amount
      type: money128
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_schema_group_and_validate_help_succeed() -> None:
    group = runner.invoke(app, ["schema", "--help"])
    command = runner.invoke(app, ["schema", "validate", "--help"])

    assert group.exit_code == 0
    assert "validate" in group.stdout
    assert command.exit_code == 0
    assert "local declarative schema file" in command.stdout


def test_schema_validate_valid_file_human_success(tmp_path: Path) -> None:
    path = _write(tmp_path / "customers.yml", VALID_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "validate", str(path), "--no-color"],
    )

    assert result.exit_code == 0
    assert "Valid schema:" in result.stdout
    assert str(path) in result.stdout.replace("\n", "")
    assert result.stderr == ""
    assert "\x1b[" not in result.stdout


def test_schema_validate_valid_file_json_success(tmp_path: Path) -> None:
    path = _write(tmp_path / "customers.yml", VALID_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "validate", str(path), "--json"],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "contract_version": 1,
        "ok": True,
        "command": "schema.validate",
        "data": {
            "path": str(path),
            "valid": True,
        },
    }


def test_schema_validate_quiet_success_has_no_output(tmp_path: Path) -> None:
    path = _write(tmp_path / "customers.yml", VALID_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "validate", str(path), "--quiet"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_schema_validate_invalid_schema_preserves_ptk_code(tmp_path: Path) -> None:
    path = _write(tmp_path / "invalid.yml", INVALID_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "validate", str(path), "--json"],
    )

    assert result.exit_code == 10
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "schema.validate"
    assert payload["error"]["category"] == "invalid_schema"
    assert payload["error"]["code"] == "PTK-DECL-005"
    assert payload["error"]["path"] == str(path)


def test_schema_validate_missing_file_is_filesystem_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.yml"

    result = runner.invoke(
        app,
        ["schema", "validate", str(path), "--json"],
    )

    assert result.exit_code == 12
    payload = json.loads(result.stdout)
    assert payload["error"]["category"] == "filesystem_error"
    assert payload["error"]["code"] == "PTK-DECL-011"
    assert payload["error"]["path"] == str(path)


def test_schema_validate_directory_is_filesystem_error(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["schema", "validate", str(tmp_path), "--json"],
    )

    assert result.exit_code == 12
    payload = json.loads(result.stdout)
    assert payload["error"]["category"] == "filesystem_error"
    assert payload["error"]["code"] == "PTK-DECL-011"


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/schema.yml",
        "s3://bucket/schema.yml",
    ],
)
def test_schema_validate_remote_uri_is_rejected_without_network(uri: str) -> None:
    result = runner.invoke(
        app,
        ["schema", "validate", uri, "--json"],
    )

    assert result.exit_code == 13
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["error"]["category"] == "unsupported_operation"
    assert payload["error"]["path"] == uri


@pytest.mark.parametrize(
    "args",
    [
        ["--quiet", "--verbose"],
        ["--quiet", "--debug"],
        ["--json", "--verbose"],
    ],
)
def test_schema_validate_rejects_contradictory_output_options(
    tmp_path: Path,
    args: list[str],
) -> None:
    path = _write(tmp_path / "customers.yml", VALID_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "validate", str(path), *args],
    )

    assert result.exit_code == 2
