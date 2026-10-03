from __future__ import annotations

import json
import os
import socket
import subprocess
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")
pytest.importorskip("yaml")

from typer.testing import CliRunner

from pytransformkit.application.extensions import registry as plugin_registry_module
from pytransformkit.cli.app import app
from pytransformkit.cli.commands import contract as contract_command
from pytransformkit.cli.security import REDACTED
from pytransformkit.cli.services import schema as schema_service
from pytransformkit.cli.services import schema_convert as convert_service

runner = CliRunner()

SOURCE = """version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
"""


def _write(path: Path, text: str = SOURCE) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _temporary_siblings(path: Path) -> list[Path]:
    return list(path.parent.glob(f".{path.name}.*.tmp"))


@pytest.mark.parametrize(
    "args",
    [
        ["schema", "validate", "https://example.invalid/schema.yml"],
        ["schema", "inspect", "https://example.invalid/schema.yml"],
        ["schema", "format", "https://example.invalid/schema.yml"],
        [
            "schema",
            "convert",
            "https://example.invalid/schema.yml",
            "--to",
            "json",
        ],
    ],
)
def test_remote_schema_inputs_fail_before_any_network_access(
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
) -> None:
    def forbidden_network(*args: object, **kwargs: object) -> object:
        raise AssertionError("CLI security boundary attempted network access")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden_network)
    monkeypatch.setattr(socket, "create_connection", forbidden_network)

    result = runner.invoke(app, args)

    assert result.exit_code == 13
    assert "Remote schema" in result.stderr


def test_cli_path_does_not_expand_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expanded = _write(tmp_path / "expanded.yml")
    monkeypatch.setenv("PTK_CLI_SCHEMA", str(expanded))
    literal = tmp_path / "${PTK_CLI_SCHEMA}"

    result = runner.invoke(app, ["schema", "validate", str(literal)])

    assert result.exit_code == 12
    assert str(literal) in result.stderr
    assert expanded.exists()


def test_yaml_environment_reference_remains_literal_through_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PTK_CLI_SECRET", "must-not-expand")
    source = _write(
        tmp_path / "literal.yml",
        """version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      description: "${PTK_CLI_SECRET}"
""",
    )

    result = runner.invoke(app, ["schema", "inspect", str(source), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["schema"]["fields"][0]["description"] == "${PTK_CLI_SECRET}"
    assert "must-not-expand" not in result.stdout


def test_unsafe_yaml_constructor_never_executes_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    executed: list[tuple[object, ...]] = []

    def forbidden_system(*args: object, **kwargs: object) -> int:
        executed.append(args)
        raise AssertionError("unsafe YAML constructor executed a shell command")

    monkeypatch.setattr(os, "system", forbidden_system)
    source = _write(
        tmp_path / "unsafe.yml",
        """version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      description: !!python/object/apply:os.system ["echo compromised"]
""",
    )

    result = runner.invoke(app, ["schema", "validate", str(source)])

    assert result.exit_code == 10
    assert executed == []


def test_cli_commands_do_not_discover_or_activate_plugins(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("CLI attempted implicit plugin discovery or activation")

    monkeypatch.setattr(
        plugin_registry_module.PluginRegistry,
        "discover",
        classmethod(forbidden),
    )
    monkeypatch.setattr(plugin_registry_module.PluginRegistry, "activate", forbidden)

    commands = [
        ["--help"],
        ["doctor", "--json"],
        ["engines", "list", "--json"],
        ["schema", "validate", str(source), "--json"],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.output


def test_cli_schema_operations_do_not_execute_shell_commands(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("CLI attempted shell or subprocess execution")

    monkeypatch.setattr(os, "system", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)

    formatted = runner.invoke(app, ["schema", "format", str(source)])
    converted = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json"],
    )

    assert formatted.exit_code == 0
    assert converted.exit_code == 0


def test_schema_format_replace_failure_preserves_original_and_cleans_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")
    original = source.read_bytes()

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic atomic replace failure")

    monkeypatch.setattr(schema_service.os, "replace", fail_replace)

    result = runner.invoke(app, ["schema", "format", str(source), "--write"])

    assert result.exit_code == 12
    assert source.read_bytes() == original
    assert _temporary_siblings(source) == []


def test_schema_format_interrupt_before_commit_preserves_original_and_cleans_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")
    original = source.read_bytes()

    def interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(schema_service.os, "replace", interrupt)

    result = runner.invoke(app, ["schema", "format", str(source), "--write"])

    assert result.exit_code == 130
    assert source.read_bytes() == original
    assert _temporary_siblings(source) == []


def test_schema_convert_new_output_interrupt_leaves_no_output_or_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")
    output = tmp_path / "schema.json"

    def interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(convert_service.os, "link", interrupt)

    result = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 130
    assert not output.exists()
    assert _temporary_siblings(output) == []


def test_schema_convert_replace_failure_preserves_destination_and_cleans_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")
    output = _write(tmp_path / "schema.json", "ORIGINAL")

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic atomic replace failure")

    monkeypatch.setattr(convert_service.os, "replace", fail_replace)

    result = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(output),
            "--force",
        ],
    )

    assert result.exit_code == 12
    assert output.read_text(encoding="utf-8") == "ORIGINAL"
    assert _temporary_siblings(output) == []


def test_debug_traceback_is_redacted_without_changing_machine_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(self: object, contract_id: str) -> None:
        raise RuntimeError(
            "token=trace-secret "
            "authorization: Bearer bearer-secret "
            "https://user:pass@example.invalid/"
        )

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
    assert payload["error"]["category"] == "internal_error"
    assert "Traceback" in result.stderr
    for secret in ("trace-secret", "bearer-secret", "user:pass"):
        assert secret not in result.stdout
        assert secret not in result.stderr
    assert REDACTED in result.stderr


def test_remote_uri_credentials_are_redacted_from_json_error_path() -> None:
    result = runner.invoke(
        app,
        [
            "schema",
            "validate",
            "https://user:pass@example.invalid/schema.yml",
            "--json",
        ],
    )

    assert result.exit_code == 13
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    error = payload["error"]
    assert error["category"] == "unsupported_operation"
    assert "user:pass" not in error["path"]
    assert REDACTED in error["path"]



def test_schema_directory_is_rejected_without_recursive_discovery(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "nested.yml")

    result = runner.invoke(app, ["schema", "validate", str(tmp_path)])

    assert result.exit_code == 12
    assert "nested.yml" not in result.stdout
    assert (tmp_path / "nested.yml").exists()


def test_permission_denied_maps_to_filesystem_error_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "schema.yml")

    def denied(*args: object, **kwargs: object) -> object:
        raise PermissionError("permission denied by LOT-56 test")

    monkeypatch.setattr(schema_service, "load_schema", denied)

    result = runner.invoke(
        app,
        ["schema", "validate", str(source), "--no-color"],
    )

    assert result.exit_code == 12
    assert result.stdout == ""
    assert "permission denied" in result.stderr
    assert "Traceback" not in result.stderr
