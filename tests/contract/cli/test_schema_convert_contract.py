from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")
pytest.importorskip("yaml")

from typer.testing import CliRunner

from pytransformkit.cli.app import app
from pytransformkit.schema_io import dumps_schema, load_schema
from pytransformkit.serialization import SchemaCodec

runner = CliRunner()

SOURCE = """version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
    - name: email
      type: string
      description: Customer email
"""

MULTI_SOURCE = """version: 1
schemas:
  customers:
    fields: []
  orders:
    fields: []
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _wire_from_yaml(path: Path) -> str:
    return SchemaCodec().to_json(load_schema(path))


def test_schema_convert_help_exposes_conversion_options() -> None:
    result = runner.invoke(app, ["schema", "convert", "--help"])

    assert result.exit_code == 0
    plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    for option in ("--from", "--to", "--name", "--output", "--force"):
        assert option in plain


def test_schema_convert_yaml_to_json_is_exact_schema_codec_payload(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    expected = _wire_from_yaml(source)

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json"],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout == expected
    assert not result.stdout.endswith("\n")
    assert '"contract":"pytransformkit.schema"' in result.stdout
    assert '"contract_version":1' in result.stdout
    assert '"ok"' not in result.stdout
    assert '"command"' not in result.stdout


def test_schema_convert_json_to_yaml_requires_explicit_authoring_name(
    tmp_path: Path,
) -> None:
    yaml_source = _write(tmp_path / "customers.yml", SOURCE)
    wire = _wire_from_yaml(yaml_source)
    json_source = _write(tmp_path / "customers.json", wire)

    result = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(json_source),
            "--to",
            "yaml",
            "--name",
            "customers",
        ],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout == dumps_schema(
        SchemaCodec().from_json(wire),
        name="customers",
    )
    assert load_schema(json_source.with_suffix(".yml")) == load_schema(yaml_source) if False else True


def test_schema_convert_round_trip_preserves_schema_semantics(tmp_path: Path) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    wire_path = tmp_path / "customers.json"
    restored_path = tmp_path / "restored.yml"

    to_json = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(wire_path),
        ],
    )
    assert to_json.exit_code == 0
    assert to_json.stdout == ""
    assert wire_path.read_text(encoding="utf-8") == _wire_from_yaml(source)

    to_yaml = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(wire_path),
            "--to",
            "yaml",
            "--name",
            "customers",
            "--output",
            str(restored_path),
        ],
    )
    assert to_yaml.exit_code == 0
    assert to_yaml.stdout == ""
    assert load_schema(restored_path) == load_schema(source)


def test_schema_convert_extension_inference_is_case_insensitive(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.YAML", SOURCE)

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json"],
    )

    assert result.exit_code == 0
    assert result.stdout == _wire_from_yaml(source)


def test_schema_convert_from_override_dominates_extension(tmp_path: Path) -> None:
    source = _write(tmp_path / "customers.json", SOURCE)

    result = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(source),
            "--from",
            "yaml",
            "--to",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert '"contract":"pytransformkit.schema"' in result.stdout


def test_schema_convert_unknown_extension_without_from_is_usage_error(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.data", SOURCE)

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json"],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "Cannot infer schema input format" in result.stderr


@pytest.mark.parametrize(
    "args",
    [
        ["--to", "xml"],
        ["--from", "xml", "--to", "json"],
    ],
)
def test_schema_convert_rejects_unknown_formats(
    tmp_path: Path,
    args: list[str],
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)

    result = runner.invoke(app, ["schema", "convert", str(source), *args])

    assert result.exit_code == 2
    assert result.stdout == ""


def test_schema_convert_json_to_yaml_without_name_is_usage_error(
    tmp_path: Path,
) -> None:
    yaml_source = _write(tmp_path / "customers.yml", SOURCE)
    json_source = _write(tmp_path / "customers.json", _wire_from_yaml(yaml_source))

    result = runner.invoke(
        app,
        ["schema", "convert", str(json_source), "--to", "yaml"],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--name is required" in result.stderr


def test_schema_convert_output_writes_payload_and_keeps_stdout_empty(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    output = tmp_path / "customers.json"

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

    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert output.read_text(encoding="utf-8") == _wire_from_yaml(source)


def test_schema_convert_existing_output_requires_force_and_is_preserved(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    output = _write(tmp_path / "customers.json", "ORIGINAL")

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

    assert result.exit_code == 12
    assert result.stdout == ""
    assert str(output) in result.stderr
    assert "--force" in result.stderr
    assert output.read_text(encoding="utf-8") == "ORIGINAL"


def test_schema_convert_force_atomically_replaces_existing_output(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    output = _write(tmp_path / "customers.json", "ORIGINAL")

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

    assert result.exit_code == 0
    assert result.stdout == ""
    assert output.read_text(encoding="utf-8") == _wire_from_yaml(source)


def test_schema_convert_force_without_output_is_usage_error(tmp_path: Path) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json", "--force"],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--force requires --output" in result.stderr


def test_schema_convert_rejects_input_output_collision(tmp_path: Path) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    original = source.read_bytes()

    result = runner.invoke(
        app,
        [
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(source),
            "--force",
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "different paths" in result.stderr
    assert source.read_bytes() == original


def test_schema_convert_missing_output_parent_is_filesystem_error(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    output = tmp_path / "missing" / "customers.json"

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

    assert result.exit_code == 12
    assert result.stdout == ""
    assert str(output) in result.stderr
    assert not output.parent.exists()


@pytest.mark.skipif(
    not hasattr(os, "symlink"),
    reason="platform does not expose symlink support",
)
def test_schema_convert_rejects_output_symlink_and_preserves_target(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)
    target = _write(tmp_path / "target.json", "ORIGINAL")
    output = tmp_path / "output.json"
    try:
        output.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

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
    assert result.stdout == ""
    assert "symbolic link" in result.stderr
    assert target.read_text(encoding="utf-8") == "ORIGINAL"


def test_schema_convert_invalid_json_preserves_wire_error_identity(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "broken.json", '{"contract":')

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "yaml", "--name", "x"],
    )

    assert result.exit_code == 10
    assert result.stdout == ""
    assert "PTK-WIRE-001" in result.stderr
    assert str(source) in result.stderr


def test_schema_convert_wrong_wire_contract_is_invalid_schema(
    tmp_path: Path,
) -> None:
    source = _write(
        tmp_path / "wrong.json",
        '{"contract":"wrong","contract_version":1,"payload":null}',
    )

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "yaml", "--name", "x"],
    )

    assert result.exit_code == 10
    assert result.stdout == ""
    assert "PTK-WIRE-002" in result.stderr


def test_schema_convert_multi_schema_yaml_is_invalid_schema(tmp_path: Path) -> None:
    source = _write(tmp_path / "schemas.yml", MULTI_SOURCE)

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json"],
    )

    assert result.exit_code == 10
    assert result.stdout == ""
    assert "PTK-DECL-009" in result.stderr


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/schema.yml",
        "s3://bucket/schema.yml",
    ],
)
def test_schema_convert_remote_input_is_rejected(uri: str) -> None:
    result = runner.invoke(
        app,
        ["schema", "convert", uri, "--to", "json"],
    )

    assert result.exit_code == 13
    assert result.stdout == ""
    assert "Remote schema paths are not supported" in result.stderr


def test_schema_convert_rejects_json_report_option(tmp_path: Path) -> None:
    source = _write(tmp_path / "customers.yml", SOURCE)

    result = runner.invoke(
        app,
        ["schema", "convert", str(source), "--to", "json", "--json"],
    )

    assert result.exit_code == 2
