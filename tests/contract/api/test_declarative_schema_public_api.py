from __future__ import annotations

import importlib
import inspect
import os
from collections import OrderedDict
from pathlib import Path
from typing import get_type_hints

import pytest

import pytransformkit
import pytransformkit.schema_io as schema_io
from pytransformkit.domain.data import Field, IntegerType, Schema, StringType
from pytransformkit.errors import (
    DeclarativeSchemaCardinalityError,
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaExportError,
    DeclarativeSchemaIOError,
    DeclarativeSchemaValidationError,
)

pytest.importorskip("yaml")

_EXPECTED_EXPORTS = [
    "dump_schema",
    "dump_schemas",
    "dumps_schema",
    "dumps_schemas",
    "load_schema",
    "load_schemas",
    "loads_schema",
    "loads_schemas",
]


def _customer_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field(
                "email",
                StringType(),
                nullable=True,
                description="Customer email",
            ),
        )
    )


def test_schema_io_all_is_exact_and_internal_services_remain_hidden() -> None:
    assert schema_io.__all__ == _EXPECTED_EXPORTS
    assert set(schema_io.__dict__).issuperset(_EXPECTED_EXPORTS)

    forbidden = {
        "DeclarativeSafeLoader",
        "DeclarativeTypeExporter",
        "DeclarativeTypeResolver",
        "SchemaDefinition",
        "SchemaDefinitionCompiler",
        "SchemaDefinitionExporter",
        "SchemaDocument",
        "SchemaDocumentCompiler",
        "SchemaDefinitionValidator",
        "YamlSchemaEmitter",
        "YamlSchemaParser",
    }
    assert forbidden.isdisjoint(schema_io.__all__)


def test_schema_io_functions_are_not_promoted_to_root() -> None:
    assert set(_EXPECTED_EXPORTS).isdisjoint(pytransformkit.__all__)
    for name in _EXPECTED_EXPORTS:
        assert name not in pytransformkit.__dict__


def test_stable_public_signatures_are_frozen() -> None:
    assert str(inspect.signature(schema_io.load_schema)) == (
        "(path: 'str | os.PathLike[str]') -> 'Schema'"
    )
    assert str(inspect.signature(schema_io.loads_schema)) == (
        "(text: 'str', *, source: 'str | None' = None) -> 'Schema'"
    )
    assert str(inspect.signature(schema_io.load_schemas)) == (
        "(path: 'str | os.PathLike[str]') -> 'dict[str, Schema]'"
    )
    assert str(inspect.signature(schema_io.loads_schemas)) == (
        "(text: 'str', *, source: 'str | None' = None) -> 'dict[str, Schema]'"
    )
    assert str(inspect.signature(schema_io.dump_schema)) == (
        "(schema: 'Schema', path: 'str | os.PathLike[str]', *, name: 'str') -> 'None'"
    )
    assert str(inspect.signature(schema_io.dumps_schema)) == (
        "(schema: 'Schema', *, name: 'str') -> 'str'"
    )
    assert str(inspect.signature(schema_io.dump_schemas)) == (
        "(schemas: 'Mapping[str, Schema]', path: 'str | os.PathLike[str]') -> 'None'"
    )
    assert str(inspect.signature(schema_io.dumps_schemas)) == (
        "(schemas: 'Mapping[str, Schema]') -> 'str'"
    )


def test_type_hints_resolve_public_contract_types() -> None:
    load_hints = get_type_hints(schema_io.load_schema)
    loads_hints = get_type_hints(schema_io.loads_schemas)
    dump_hints = get_type_hints(schema_io.dump_schema)

    assert load_hints["path"] == str | os.PathLike[str]
    assert load_hints["return"] is Schema
    assert loads_hints["return"] == dict[str, Schema]
    assert dump_hints["return"] is type(None)


def test_single_schema_in_memory_round_trip() -> None:
    schema = _customer_schema()

    text = schema_io.dumps_schema(schema, name="customers")
    reloaded = schema_io.loads_schema(text, source="<contract>")

    assert isinstance(text, str)
    assert text.startswith("version: 1\nschema:\n")
    assert text.endswith("\n")
    assert reloaded == schema


def test_multi_schema_round_trip_preserves_mapping_iteration_order() -> None:
    schemas = OrderedDict(
        (
            ("customers", _customer_schema()),
            ("orders", Schema(fields=(Field("order_id", IntegerType()),))),
        )
    )

    text = schema_io.dumps_schemas(schemas)
    reloaded = schema_io.loads_schemas(text)

    assert text.startswith("version: 1\nschemas:\n")
    assert tuple(reloaded) == ("customers", "orders")
    assert reloaded == dict(schemas)


def test_multi_loader_accepts_single_schema_document() -> None:
    schema = _customer_schema()
    text = schema_io.dumps_schema(schema, name="customers")

    loaded = schema_io.loads_schemas(text)

    assert loaded == {"customers": schema}


def test_single_loader_rejects_multi_schema_document() -> None:
    text = schema_io.dumps_schemas(
        {
            "customers": _customer_schema(),
            "orders": Schema(fields=()),
        }
    )

    with pytest.raises(DeclarativeSchemaCardinalityError) as error:
        schema_io.loads_schema(text)

    assert str(error.value.error_code) == "PTK-DECL-009"
    assert error.value.required_count == 1
    assert error.value.actual_count == 2


def test_public_in_memory_loaders_do_not_accept_bytes() -> None:
    with pytest.raises(TypeError, match="text must be str"):
        schema_io.loads_schema(b"version: 1")

    with pytest.raises(TypeError, match="text must be str"):
        schema_io.loads_schemas(b"version: 1")


def test_file_round_trip_uses_exact_utf8_path(tmp_path: Path) -> None:
    path = tmp_path / "contrat-client.data"
    schema = Schema(
        fields=(
            Field(
                "libellé",
                StringType(),
                description="Déjà actif — Île-de-France",
            ),
        )
    )

    schema_io.dump_schema(schema, path, name="données_clients")

    raw = path.read_bytes()
    assert "données_clients".encode() in raw
    assert "Déjà actif — Île-de-France".encode() in raw
    assert schema_io.load_schema(path) == schema


def test_dump_schema_overwrites_exact_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "schema.yml"
    path.write_text("stale", encoding="utf-8")

    schema_io.dump_schema(
        Schema(fields=(Field("id", IntegerType(), nullable=False),)),
        path,
        name="customers",
    )

    text = path.read_text(encoding="utf-8")
    assert "stale" not in text
    assert "name: customers" in text


def test_dump_schema_does_not_create_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "schema.yml"

    with pytest.raises(DeclarativeSchemaIOError) as error:
        schema_io.dump_schema(
            Schema(fields=()),
            path,
            name="empty",
        )

    assert str(error.value.error_code) == "PTK-DECL-011"
    assert error.value.path == str(path)
    assert error.value.operation == "write"
    assert error.value.source == str(path)
    assert isinstance(error.value.__cause__, OSError)
    assert not path.parent.exists()


def test_missing_file_is_wrapped_as_public_io_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.yml"

    with pytest.raises(DeclarativeSchemaIOError) as error:
        schema_io.load_schema(path)

    assert str(error.value.error_code) == "PTK-DECL-011"
    assert error.value.path == str(path)
    assert error.value.operation == "read"
    assert error.value.source == str(path)
    assert isinstance(error.value.__cause__, OSError)


def test_invalid_utf8_file_is_wrapped_as_public_io_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(DeclarativeSchemaIOError) as error:
        schema_io.load_schema(path)

    assert error.value.operation == "read"
    assert isinstance(error.value.__cause__, UnicodeError)


def test_write_to_directory_is_wrapped_as_public_io_error(tmp_path: Path) -> None:
    with pytest.raises(DeclarativeSchemaIOError) as error:
        schema_io.dump_schema(
            Schema(fields=()),
            tmp_path,
            name="empty",
        )

    assert error.value.path == str(tmp_path)
    assert error.value.operation == "write"
    assert isinstance(error.value.__cause__, OSError)


def test_file_path_becomes_declarative_diagnostic_source(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text(
        "version: 1\n"
        "schema:\n"
        "  name: sample\n"
        "  fields:\n"
        "    - name: id\n"
        "      type: string\n"
        "      nullable: nope\n",
        encoding="utf-8",
    )

    with pytest.raises(DeclarativeSchemaValidationError) as error:
        schema_io.load_schema(path)

    assert error.value.source == str(path)


def test_str_path_and_pathlike_are_both_supported(tmp_path: Path) -> None:
    schema = _customer_schema()
    path = tmp_path / "schema.yml"

    schema_io.dump_schema(schema, str(path), name="customers")
    assert schema_io.load_schema(path) == schema


def test_bytes_path_is_not_part_of_stable_path_contract(tmp_path: Path) -> None:
    path = os.fsencode(tmp_path / "schema.yml")

    with pytest.raises(TypeError, match="path must resolve to str"):
        schema_io.load_schema(path)  # type: ignore[arg-type]


def test_yaml_dependency_failure_occurs_on_operation_not_namespace_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yaml_adapter = importlib.import_module("pytransformkit.schema_io._yaml")
    real_import_module = yaml_adapter.importlib.import_module

    def controlled_import(name: str, package: str | None = None) -> object:
        if name == "yaml":
            raise ModuleNotFoundError("No module named 'yaml'")
        return real_import_module(name, package)

    monkeypatch.setattr(
        yaml_adapter.importlib,
        "import_module",
        controlled_import,
    )

    assert schema_io.__all__ == _EXPECTED_EXPORTS
    with pytest.raises(DeclarativeSchemaDependencyError) as error:
        schema_io.loads_schema("version: 1\nschema:\n  name: empty\n  fields: []\n")

    assert str(error.value.error_code) == "PTK-DECL-010"
    assert error.value.dependency_name == "PyYAML"


def test_generated_validation_failures_do_not_leak_as_load_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_module = importlib.import_module("pytransformkit.schema_io._api")

    def invalid_dump(schema: Schema, *, name: str) -> str:
        del schema, name
        raise DeclarativeSchemaValidationError("internal generated document invalid")

    monkeypatch.setattr(api_module, "_dumps_schema", invalid_dump)

    with pytest.raises(DeclarativeSchemaExportError) as error:
        schema_io.dumps_schema(Schema(fields=()), name="sample")

    assert str(error.value.error_code) == "PTK-DECL-012"
    assert isinstance(error.value.__cause__, DeclarativeSchemaValidationError)
