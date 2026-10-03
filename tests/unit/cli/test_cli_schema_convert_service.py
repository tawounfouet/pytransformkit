from __future__ import annotations

from pathlib import Path

import pytest

from pytransformkit.cli.exceptions import CLIFileSystemError, CLIUsageError
from pytransformkit.cli.services import schema_convert
from pytransformkit.domain.data import Field, IntegerType, Schema


def _schema() -> Schema:
    return Schema(fields=(Field("id", IntegerType(), nullable=False),))


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("schema.yml", "yaml"),
        ("schema.yaml", "yaml"),
        ("schema.YAML", "yaml"),
        ("schema.json", "json"),
        ("schema.JSON", "json"),
    ],
)
def test_source_format_inference_is_extension_bounded(
    filename: str,
    expected: str,
) -> None:
    assert schema_convert._infer_source_format(Path(filename)) == expected


def test_unknown_extension_requires_explicit_from() -> None:
    with pytest.raises(CLIUsageError, match="Cannot infer"):
        schema_convert._infer_source_format(Path("schema.data"))


@pytest.mark.parametrize("value", ["xml", "yml", "", "toml"])
def test_format_normalization_rejects_unknown_values(value: str) -> None:
    with pytest.raises(CLIUsageError):
        schema_convert._normalize_format(value, option="--to")


def test_yaml_to_json_delegates_to_public_schema_and_wire_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = _schema()
    seen: list[object] = []

    def fake_load(path: str) -> dict[str, Schema]:
        seen.append(("load", path))
        return {"customers": schema}

    class FakeCodec:
        def to_json(self, value: Schema) -> str:
            seen.append(("to_json", value))
            return '{"wire":true}'

    monkeypatch.setattr(schema_convert, "load_schemas", fake_load)
    monkeypatch.setattr(schema_convert, "SchemaCodec", FakeCodec)

    payload = schema_convert.SchemaConversionService().convert(
        "schema.yml",
        to_format="json",
    )

    assert payload == '{"wire":true}'
    assert seen == [
        ("load", "schema.yml"),
        ("to_json", schema),
    ]


def test_json_to_yaml_requires_name_and_uses_public_emitter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = _schema()
    source = tmp_path / "schema.json"
    source.write_text('{"wire":true}', encoding="utf-8")
    seen: list[object] = []

    class FakeCodec:
        def from_json(self, value: bytes) -> Schema:
            seen.append(("from_json", value))
            return schema

    def fake_dump(value: Schema, *, name: str) -> str:
        seen.append(("dump", value, name))
        return "canonical-yaml\n"

    monkeypatch.setattr(schema_convert, "SchemaCodec", FakeCodec)
    monkeypatch.setattr(schema_convert, "dumps_schema", fake_dump)

    payload = schema_convert.SchemaConversionService().convert(
        source,
        to_format="yaml",
        name="customers",
    )

    assert payload == "canonical-yaml\n"
    assert seen == [
        ("from_json", b'{"wire":true}'),
        ("dump", schema, "customers"),
    ]


def test_json_to_yaml_missing_name_is_usage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "schema.json"
    source.write_text("{}", encoding="utf-8")

    class FakeCodec:
        def from_json(self, value: bytes) -> Schema:
            return _schema()

    monkeypatch.setattr(schema_convert, "SchemaCodec", FakeCodec)

    with pytest.raises(CLIUsageError, match="--name is required"):
        schema_convert.SchemaConversionService().convert(
            source,
            to_format="yaml",
        )


def test_from_override_dominates_unknown_extension(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "schema.data"
    source.write_text("ignored", encoding="utf-8")
    schema = _schema()

    monkeypatch.setattr(
        schema_convert,
        "load_schemas",
        lambda path: {"customers": schema},
    )

    class FakeCodec:
        def to_json(self, value: Schema) -> str:
            assert value is schema
            return "{}"

    monkeypatch.setattr(schema_convert, "SchemaCodec", FakeCodec)

    assert (
        schema_convert.SchemaConversionService().convert(
            source,
            from_format="yaml",
            to_format="json",
        )
        == "{}"
    )


def test_force_without_output_is_usage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "schema.yml"
    monkeypatch.setattr(schema_convert, "load_schemas", lambda path: {"x": _schema()})

    with pytest.raises(CLIUsageError, match="--force requires --output"):
        schema_convert.SchemaConversionService().convert(
            source,
            to_format="json",
            force=True,
        )


def test_input_output_collision_is_rejected_before_loading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "schema.yml"
    called = False

    def forbidden_load(path: str) -> dict[str, Schema]:
        nonlocal called
        called = True
        return {"x": _schema()}

    monkeypatch.setattr(schema_convert, "load_schemas", forbidden_load)

    with pytest.raises(CLIUsageError, match="different paths"):
        schema_convert.SchemaConversionService().convert(
            source,
            to_format="json",
            output=source,
        )

    assert called is False


def test_existing_output_requires_force_and_is_preserved(tmp_path: Path) -> None:
    output = tmp_path / "schema.json"
    output.write_text("original", encoding="utf-8")

    with pytest.raises(CLIFileSystemError, match="--force"):
        schema_convert._write_output(output, "replacement", force=False)

    assert output.read_text(encoding="utf-8") == "original"


def test_atomic_new_output_failure_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "schema.json"

    def fail_link(src: object, dst: object) -> None:
        raise OSError("link failed")

    monkeypatch.setattr(schema_convert.os, "link", fail_link)

    with pytest.raises(CLIFileSystemError, match="link failed"):
        schema_convert._write_new_atomic(output, "payload")

    assert not output.exists()
    assert list(tmp_path.glob(".schema.json.*.tmp")) == []


def test_force_replace_failure_preserves_existing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "schema.json"
    output.write_text("original", encoding="utf-8")

    def fail_replace(src: object, dst: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(schema_convert.os, "replace", fail_replace)

    with pytest.raises(CLIFileSystemError, match="replace failed"):
        schema_convert._write_output(output, "replacement", force=True)

    assert output.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.glob(".schema.json.*.tmp")) == []
