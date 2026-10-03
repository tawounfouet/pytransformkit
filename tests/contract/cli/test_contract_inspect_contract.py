from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

from pytransformkit.cli.app import app

runner = CliRunner()

CONTRACT_IDS = ["public-api", "errors", "schema-wire", "cli"]


def test_contract_help_exposes_inspect() -> None:
    result = runner.invoke(app, ["contract", "--help"])

    assert result.exit_code == 0
    plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "inspect" in plain


def test_contract_inspect_without_id_lists_contracts_deterministically() -> None:
    result = runner.invoke(app, ["contract", "inspect", "--no-color"])

    assert result.exit_code == 0
    assert result.stderr == ""
    positions = [result.stdout.index(contract_id) for contract_id in CONTRACT_IDS]
    assert positions == sorted(positions)
    assert "STABLE" in result.stdout
    assert "CANDIDATE" in result.stdout
    assert "\x1b[" not in result.stdout


def test_contract_inspect_list_json_uses_report_envelope() -> None:
    result = runner.invoke(app, ["contract", "inspect", "--json"])

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)

    assert payload["contract_version"] == 1
    assert payload["ok"] is True
    assert payload["command"] == "contract.inspect"
    assert [item["id"] for item in payload["data"]["contracts"]] == CONTRACT_IDS


@pytest.mark.parametrize("contract_id", CONTRACT_IDS)
def test_contract_inspect_known_contract_json(contract_id: str) -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", contract_id, "--json"],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["command"] == "contract.inspect"
    assert payload["data"]["id"] == contract_id
    assert isinstance(payload["data"]["document"], dict)


def test_contract_inspect_schema_wire_matches_stable_wire_identity() -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", "schema-wire", "--json"],
    )

    assert result.exit_code == 0
    document = json.loads(result.stdout)["data"]["document"]
    assert document == {
        "codec": "SchemaCodec",
        "contract": "pytransformkit.schema",
        "contract_version": 1,
    }


def test_contract_inspect_cli_is_candidate_not_frozen() -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", "cli", "--json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)["data"]
    assert data["status"] == "candidate"
    assert data["document"]["status"] == "candidate"
    assert data["document"]["commands"][-1] == "contract.inspect"


def test_contract_inspect_quiet_emits_normalized_id_only() -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", "  ERRORS  ", "--quiet"],
    )

    assert result.exit_code == 0
    assert result.stdout == "errors\n"
    assert result.stderr == ""


def test_contract_inspect_quiet_catalogue_emits_ids_only() -> None:
    result = runner.invoke(app, ["contract", "inspect", "--quiet"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == CONTRACT_IDS


def test_contract_inspect_verbose_includes_packaged_document() -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", "schema-wire", "--verbose", "--no-color"],
    )

    assert result.exit_code == 0
    assert "Document:" in result.stdout
    assert '"contract": "pytransformkit.schema"' in result.stdout
    assert "\x1b[" not in result.stdout


def test_contract_inspect_unknown_contract_is_usage_error() -> None:
    result = runner.invoke(app, ["contract", "inspect", "runtime"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "Unknown contract id" in result.stderr
    assert "public-api" in result.stderr


def test_contract_inspect_unknown_contract_json_is_error_report() -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", "runtime", "--json"],
    )

    assert result.exit_code == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "contract.inspect"
    assert payload["error"]["category"] == "invalid_usage"


def test_contract_inspect_works_outside_repository_checkout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["contract", "inspect", "errors", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["document"]["contract"] == "pytransformkit.errors.v1"


def test_contract_inspect_does_not_require_yaml_or_engine_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    for module_name in ("yaml", "pandas", "polars", "pyarrow", "duckdb"):
        monkeypatch.setitem(sys.modules, module_name, None)

    result = runner.invoke(
        app,
        ["contract", "inspect", "public-api", "--json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["id"] == "public-api"
