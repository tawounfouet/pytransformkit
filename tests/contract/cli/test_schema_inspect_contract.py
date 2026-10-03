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

INSPECTABLE_SCHEMA = """version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
      description: Stable identifier
    - name: amount
      type:
        decimal:
          precision: 18
          scale: 2
    - name: occurred_at
      type:
        timestamp:
          unit: ms
          timezone: UTC
    - name: tags
      type:
        list:
          element:
            type: string
          element_nullable: false
"""

MULTI_SCHEMA = """version: 1
schemas:
  customers:
    fields: []
  orders:
    fields: []
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_schema_inspect_help_is_available() -> None:
    result = runner.invoke(app, ["schema", "inspect", "--help"])

    assert result.exit_code == 0
    assert "Inspect one local declarative schema file" in result.stdout


def test_schema_inspect_human_output_contains_schema_and_fields(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "customers.yml", INSPECTABLE_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), "--no-color"],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert "Schema: customers" in result.stdout
    assert str(path) in result.stdout.replace("\n", "")
    assert "customer_id" in result.stdout
    assert "int64" in result.stdout
    assert "Stable identifier" in result.stdout
    assert "amount" in result.stdout
    assert "decimal" in result.stdout
    assert "\x1b[" not in result.stdout


def test_schema_inspect_verbose_human_output_includes_type_details(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "customers.yml", INSPECTABLE_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), "--verbose", "--no-color"],
    )

    assert result.exit_code == 0
    assert "Type details" in result.stdout
    assert "precision" in result.stdout
    assert "timezone" in result.stdout
    assert "element" in result.stdout


def test_schema_inspect_json_uses_cli_report_not_schema_codec(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "customers.yml", INSPECTABLE_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), "--json"],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert "\x1b[" not in result.stdout

    payload = json.loads(result.stdout)
    assert payload["contract_version"] == 1
    assert payload["ok"] is True
    assert payload["command"] == "schema.inspect"
    assert set(payload) == {"contract_version", "ok", "command", "data"}
    assert payload["data"]["path"] == str(path)
    assert payload["data"]["schema"]["name"] == "customers"

    fields = payload["data"]["schema"]["fields"]
    assert [field["name"] for field in fields] == [
        "customer_id",
        "amount",
        "occurred_at",
        "tags",
    ]
    assert fields[0] == {
        "name": "customer_id",
        "type": "int64",
        "nullable": False,
        "description": "Stable identifier",
    }
    assert fields[1]["type"] == "decimal"
    assert fields[1]["description"] is None
    assert fields[1]["type_details"] == {
        "precision": 18,
        "scale": 2,
    }
    assert fields[2]["type_details"] == {
        "unit": "ms",
        "timezone": "UTC",
    }
    assert fields[3]["type_details"] == {
        "element": {
            "type": "string",
            "nullable": False,
        }
    }

    assert "contract" not in payload["data"]["schema"]
    assert "payload" not in payload["data"]["schema"]
    assert "pytransformkit.schema" not in result.stdout


def test_schema_inspect_quiet_success_has_no_output(tmp_path: Path) -> None:
    path = _write(tmp_path / "customers.yml", INSPECTABLE_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), "--quiet"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_schema_inspect_multi_schema_document_is_invalid_schema(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "schemas.yml", MULTI_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), "--json"],
    )

    assert result.exit_code == 10
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "schema.inspect"
    assert payload["error"]["category"] == "invalid_schema"
    assert payload["error"]["code"] == "PTK-DECL-009"
    assert payload["error"]["path"] == str(path)


def test_schema_inspect_missing_file_is_filesystem_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.yml"

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), "--json"],
    )

    assert result.exit_code == 12
    payload = json.loads(result.stdout)
    assert payload["error"]["category"] == "filesystem_error"
    assert payload["error"]["code"] == "PTK-DECL-011"
    assert payload["error"]["path"] == str(path)


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/schema.yml",
        "s3://bucket/schema.yml",
    ],
)
def test_schema_inspect_remote_uri_is_rejected_without_network(uri: str) -> None:
    result = runner.invoke(
        app,
        ["schema", "inspect", uri, "--json"],
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
def test_schema_inspect_rejects_contradictory_output_options(
    tmp_path: Path,
    args: list[str],
) -> None:
    path = _write(tmp_path / "customers.yml", INSPECTABLE_SCHEMA)

    result = runner.invoke(
        app,
        ["schema", "inspect", str(path), *args],
    )

    assert result.exit_code == 2
