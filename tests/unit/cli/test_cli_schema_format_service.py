from __future__ import annotations

import os
from pathlib import Path

import pytest

from pytransformkit.cli.services import schema as schema_service
from pytransformkit.domain.data import Field, IntegerType, Schema


def test_schema_format_uses_public_schema_io_helpers_without_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = Schema(fields=(Field("id", IntegerType(), nullable=False),))
    seen: list[object] = []

    def fake_load_schemas(path: str) -> dict[str, Schema]:
        seen.append(("load", path))
        return {"customers": schema}

    def fake_dumps_schema(value: Schema, *, name: str) -> str:
        seen.append(("dump", value, name))
        return "canonical\n"

    def forbidden_write(path: Path, text: str) -> None:
        raise AssertionError("default format must not write")

    monkeypatch.setattr(schema_service, "load_schemas", fake_load_schemas)
    monkeypatch.setattr(schema_service, "dumps_schema", fake_dumps_schema)
    monkeypatch.setattr(schema_service, "_atomic_replace_text", forbidden_write)

    payload = schema_service.SchemaCLIService().format("schema.yml")

    assert payload == "canonical\n"
    assert seen == [
        ("load", "schema.yml"),
        ("dump", schema, "customers"),
    ]


def test_schema_format_uses_multi_schema_public_emitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schemas = {
        "customers": Schema(fields=()),
        "orders": Schema(fields=()),
    }

    monkeypatch.setattr(schema_service, "load_schemas", lambda path: schemas)
    monkeypatch.setattr(
        schema_service,
        "dumps_schemas",
        lambda values: "multi-canonical\n" if values is schemas else "wrong",
    )

    assert (
        schema_service.SchemaCLIService().format("schemas.yml") == "multi-canonical\n"
    )


def test_atomic_replace_failure_preserves_original_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "schema.yml"
    path.write_text("original\n", encoding="utf-8")

    def fail_replace(src: object, dst: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(schema_service.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        schema_service._atomic_replace_text(path, "replacement\n")

    assert path.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob(".schema.yml.*.tmp")) == []


def test_atomic_replace_interrupt_preserves_original_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "schema.yml"
    path.write_text("original\n", encoding="utf-8")

    def interrupt_replace(src: object, dst: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(schema_service.os, "replace", interrupt_replace)

    with pytest.raises(KeyboardInterrupt):
        schema_service._atomic_replace_text(path, "replacement\n")

    assert path.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob(".schema.yml.*.tmp")) == []


@pytest.mark.skipif(
    not hasattr(os, "symlink"),
    reason="platform does not expose symlink support",
)
def test_schema_format_write_rejects_symlink_before_loading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target.yml"
    target.write_text(
        "version: 1\nschema:\n  name: x\n  fields: []\n",
        encoding="utf-8",
    )
    link = tmp_path / "link.yml"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    called = False

    def forbidden_load(path: str) -> dict[str, Schema]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(schema_service, "load_schemas", forbidden_load)

    with pytest.raises(OSError, match="symbolic link"):
        schema_service.SchemaCLIService().format(link, write=True)

    assert called is False


def test_atomic_replace_preserves_existing_permission_bits(tmp_path: Path) -> None:
    path = tmp_path / "schema.yml"
    path.write_text("original\n", encoding="utf-8")
    path.chmod(0o640)

    schema_service._atomic_replace_text(path, "replacement\n")

    assert path.read_text(encoding="utf-8") == "replacement\n"
    assert path.stat().st_mode & 0o777 == 0o640
