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
from pytransformkit.schema_io import (
    dumps_schema,
    dumps_schemas,
    load_schema,
    load_schemas,
    loads_schemas,
)

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
    fields:
      - name: customer_id
        type: int64
        nullable: false
  orders:
    fields:
      - name: order_id
        type: int64
        nullable: false
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_schema_format_help_is_available() -> None:
    result = runner.invoke(app, ["schema", "format", "--help"])

    assert result.exit_code == 0
    plain = re.sub(r"\x1b\\[[0-9;]*m", "", result.stdout)
    assert "Format one local declarative schema file" in plain
    assert "--write" in plain


def test_schema_format_emits_canonical_yaml_without_modifying_source(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "customers.yml", SOURCE)
    original = path.read_bytes()

    expected = dumps_schema(load_schema(path), name="customers")
    result = runner.invoke(app, ["schema", "format", str(path)])

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout == expected
    assert path.read_bytes() == original
    assert "\x1b[" not in result.stdout


def test_schema_format_supports_multi_schema_documents(tmp_path: Path) -> None:
    path = _write(tmp_path / "schemas.yml", MULTI_SOURCE)

    expected = dumps_schemas(load_schemas(path))
    result = runner.invoke(app, ["schema", "format", str(path)])

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout == expected
    assert tuple(loads_schemas(result.stdout)) == ("customers", "orders")


def test_schema_format_is_idempotent_and_semantically_round_trippable(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "source.yml", SOURCE)

    first = runner.invoke(app, ["schema", "format", str(source)])
    assert first.exit_code == 0

    canonical = _write(tmp_path / "canonical.yml", first.stdout)
    second = runner.invoke(app, ["schema", "format", str(canonical)])

    assert second.exit_code == 0
    assert second.stdout == first.stdout
    assert load_schemas(source) == load_schemas(canonical)


def test_schema_format_write_replaces_source_and_keeps_stdout_clean(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "customers.yml", SOURCE)
    expected = dumps_schema(load_schema(path), name="customers")

    result = runner.invoke(app, ["schema", "format", str(path), "--write"])

    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert path.read_text(encoding="utf-8") == expected

    second = runner.invoke(app, ["schema", "format", str(path), "--write"])
    assert second.exit_code == 0
    assert second.stdout == ""
    assert path.read_text(encoding="utf-8") == expected


def test_schema_format_missing_file_is_filesystem_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.yml"

    result = runner.invoke(app, ["schema", "format", str(path)])

    assert result.exit_code == 12
    assert result.stdout == ""
    assert "PTK-DECL-011" in result.stderr
    assert str(path) in result.stderr


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/schema.yml",
        "s3://bucket/schema.yml",
    ],
)
def test_schema_format_remote_uri_is_rejected_without_network(uri: str) -> None:
    result = runner.invoke(app, ["schema", "format", uri])

    assert result.exit_code == 13
    assert result.stdout == ""
    assert "Remote schema sources are not supported" in result.stderr


def test_schema_format_rejects_json_report_mode(tmp_path: Path) -> None:
    path = _write(tmp_path / "customers.yml", SOURCE)

    result = runner.invoke(app, ["schema", "format", str(path), "--json"])

    assert result.exit_code == 2


@pytest.mark.skipif(
    not hasattr(os, "symlink"),
    reason="platform does not expose symlink support",
)
def test_schema_format_write_rejects_symlink_and_preserves_target(
    tmp_path: Path,
) -> None:
    target = _write(tmp_path / "target.yml", SOURCE)
    link = tmp_path / "link.yml"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    original = target.read_bytes()
    result = runner.invoke(app, ["schema", "format", str(link), "--write"])

    assert result.exit_code == 12
    assert result.stdout == ""
    assert "symbolic link" in result.stderr
    assert target.read_bytes() == original
    assert link.is_symlink()
