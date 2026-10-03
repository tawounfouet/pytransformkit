from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")
pytest.importorskip("yaml")

from typer.testing import CliRunner

from pytransformkit.cli.app import app
from pytransformkit.cli.commands import contract as contract_command
from pytransformkit.schema_io import dumps_schema, load_schema
from pytransformkit.serialization import SchemaCodec

runner = CliRunner()

UNICODE_SCHEMA = """version: 1
schema:
  name: clients_été
  fields:
    - name: libellé
      type: string
      description: "[bold]Créé à Paris — 東京[/bold]"
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "args",
    [
        ["doctor", "--json", "--verbose"],
        ["engines", "list", "--json", "--verbose"],
        ["contract", "inspect", "--json", "--verbose"],
    ],
)
def test_json_semantic_option_errors_use_json_error_envelope(
    args: list[str],
) -> None:
    result = runner.invoke(app, args)

    assert result.exit_code == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["contract_version"] == 1
    assert payload["ok"] is False
    assert payload["error"]["category"] == "invalid_usage"


def test_schema_json_semantic_option_error_precedes_schema_loading(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.yml"

    result = runner.invoke(
        app,
        ["schema", "inspect", str(missing), "--json", "--verbose"],
    )

    assert result.exit_code == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["command"] == "schema.inspect"
    assert payload["error"]["category"] == "invalid_usage"


@pytest.mark.parametrize("option", ["--quiet", "--debug", "--no-color"])
def test_json_success_is_invariant_to_nonsemantic_output_options(
    option: str,
) -> None:
    baseline = runner.invoke(
        app,
        ["contract", "inspect", "schema-wire", "--json"],
        terminal_width=80,
    )
    variant = runner.invoke(
        app,
        ["contract", "inspect", "schema-wire", "--json", option],
        terminal_width=80,
    )

    assert baseline.exit_code == 0
    assert variant.exit_code == 0
    assert baseline.stderr == ""
    assert variant.stderr == ""
    assert variant.stdout == baseline.stdout


def test_json_output_is_independent_of_terminal_width() -> None:
    narrow = runner.invoke(
        app,
        ["contract", "inspect", "cli", "--json"],
        terminal_width=40,
    )
    wide = runner.invoke(
        app,
        ["contract", "inspect", "cli", "--json"],
        terminal_width=180,
    )

    assert narrow.exit_code == 0
    assert wide.exit_code == 0
    assert narrow.stderr == ""
    assert wide.stderr == ""
    assert narrow.stdout == wide.stdout


def test_debug_does_not_change_successful_human_stdout() -> None:
    normal = runner.invoke(
        app,
        ["contract", "inspect", "schema-wire", "--no-color"],
    )
    debug = runner.invoke(
        app,
        ["contract", "inspect", "schema-wire", "--debug", "--no-color"],
    )

    assert normal.exit_code == 0
    assert debug.exit_code == 0
    assert normal.stderr == ""
    assert debug.stderr == ""
    assert debug.stdout == normal.stdout


def test_human_semantic_option_error_uses_stderr_without_traceback() -> None:
    result = runner.invoke(
        app,
        ["doctor", "--quiet", "--verbose", "--no-color"],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--quiet and --verbose cannot be used together" in result.stderr
    assert "Traceback" not in result.stderr


def test_quiet_never_suppresses_fatal_error() -> None:
    result = runner.invoke(
        app,
        ["contract", "inspect", "runtime", "--quiet", "--no-color"],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "Unknown contract id" in result.stderr


def test_debug_internal_error_keeps_json_on_stdout_and_traceback_on_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(self: object, contract_id: str) -> None:
        raise RuntimeError("synthetic internal failure")

    monkeypatch.setattr(
        contract_command.ContractInspectionService,
        "inspect",
        fail,
    )

    result = runner.invoke(
        app,
        ["contract", "inspect", "cli", "--json", "--debug"],
    )

    assert result.exit_code == 70
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "contract.inspect"
    assert payload["error"]["category"] == "internal_error"
    assert "Traceback" in result.stderr
    assert "synthetic internal failure" in result.stderr
    assert "Traceback" not in result.stdout


def test_unicode_and_rich_markup_are_literal_in_human_and_json_outputs(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "clients.yml", UNICODE_SCHEMA)

    human = runner.invoke(
        app,
        ["schema", "inspect", str(source), "--no-color"],
        terminal_width=180,
    )
    machine = runner.invoke(
        app,
        ["schema", "inspect", str(source), "--json"],
    )

    assert human.exit_code == 0
    assert machine.exit_code == 0
    assert "[bold]Créé à Paris — 東京[/bold]" in human.stdout
    assert "\x1b[" not in human.stdout

    payload = json.loads(machine.stdout)
    assert payload["data"]["schema"]["name"] == "clients_été"
    assert (
        payload["data"]["schema"]["fields"][0]["description"]
        == "[bold]Créé à Paris — 東京[/bold]"
    )
    assert "clients_été" in machine.stdout
    assert "東京" in machine.stdout
    assert "\x1b[" not in machine.stdout


def test_schema_format_payload_is_width_and_debug_invariant(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "clients.yml", UNICODE_SCHEMA)
    expected = dumps_schema(load_schema(source), name="clients_été")

    narrow = runner.invoke(
        app,
        ["schema", "format", str(source)],
        terminal_width=40,
    )
    wide_debug = runner.invoke(
        app,
        ["schema", "format", str(source), "--debug"],
        terminal_width=180,
    )

    assert narrow.exit_code == 0
    assert wide_debug.exit_code == 0
    assert narrow.stderr == ""
    assert wide_debug.stderr == ""
    assert narrow.stdout == expected
    assert wide_debug.stdout == expected
    assert "Success!" not in narrow.stdout
    assert "Output:" not in narrow.stdout


def test_schema_convert_payload_is_width_and_debug_invariant(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "clients.yml", UNICODE_SCHEMA)
    expected = SchemaCodec().to_json(load_schema(source))

    narrow = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json"],
        terminal_width=40,
    )
    wide_debug = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--debug",
        ],
        terminal_width=180,
    )

    assert narrow.exit_code == 0
    assert wide_debug.exit_code == 0
    assert narrow.stderr == ""
    assert wide_debug.stderr == ""
    assert narrow.stdout == expected
    assert wide_debug.stdout == expected
    assert "Success!" not in narrow.stdout
    assert "Output:" not in narrow.stdout
