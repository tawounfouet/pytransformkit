from __future__ import annotations

import importlib

import pytest

from pytransformkit.domain.data import (
    BinaryType,
    BooleanType,
    DateType,
    DecimalType,
    DurationType,
    Field,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    Schema,
    StringType,
    StructField,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.errors import (
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaDuplicateFieldError,
)
from pytransformkit.schema_io._api import (
    _DeclarativeSchemaExporter,
    _dumps_schema,
    _dumps_schemas,
    _loads_schema,
    _loads_schemas,
)
from pytransformkit.schema_io._exporter import SchemaDocumentExporter
from pytransformkit.schema_io._model import (
    FieldDefinition,
    SchemaDefinition,
    SchemaDocument,
    StringTypeDefinition,
)
from pytransformkit.schema_io._yaml import YamlSchemaEmitter

pytest.importorskip("yaml")


def test_basic_single_schema_emission_is_canonical_and_deterministic() -> None:
    schema = Schema(
        fields=(
            Field(
                name="customer_id",
                data_type=IntegerType(),
                nullable=False,
                description="Stable identifier",
            ),
            Field(
                name="email",
                data_type=StringType(),
                nullable=True,
            ),
        )
    )

    first = _dumps_schema(schema, name="customers")
    second = _dumps_schema(schema, name="customers")

    assert first == second
    assert first == (
        "version: 1\n"
        "schema:\n"
        "  name: customers\n"
        "  fields:\n"
        "    - name: customer_id\n"
        "      type: int64\n"
        "      nullable: false\n"
        "      description: Stable identifier\n"
        "    - name: email\n"
        "      type: string\n"
        "      nullable: true\n"
    )
    assert first.endswith("\n")
    assert not first.endswith("\n\n")


def test_all_canonical_datatypes_round_trip_through_emitted_yaml() -> None:
    schema = Schema(
        fields=(
            Field("text", StringType()),
            Field("flag", BooleanType()),
            Field("i8", IntegerType(bits=8, signed=True)),
            Field("i16", IntegerType(bits=16, signed=True)),
            Field("i32", IntegerType(bits=32, signed=True)),
            Field("i64", IntegerType(bits=64, signed=True)),
            Field("u8", IntegerType(bits=8, signed=False)),
            Field("u16", IntegerType(bits=16, signed=False)),
            Field("u32", IntegerType(bits=32, signed=False)),
            Field("u64", IntegerType(bits=64, signed=False)),
            Field("f32", FloatType(bits=32)),
            Field("f64", FloatType(bits=64)),
            Field("amount", DecimalType(precision=18, scale=2)),
            Field("payload", BinaryType()),
            Field("business_date", DateType()),
            Field("default_time", TimeType()),
            Field("ns_time", TimeType(unit="ns")),
            Field("default_ts", TimestampType()),
            Field(
                "zoned_ts",
                TimestampType(unit="us", timezone="Europe/Paris"),
            ),
            Field("ns_ts", TimestampType(unit="ns")),
            Field("default_duration", DurationType()),
            Field("seconds", DurationType(unit="s")),
            Field("uncertain", UnknownType()),
            Field(
                "tags",
                ListType(
                    element_type=StringType(),
                    element_nullable=False,
                ),
            ),
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField(
                            name="city",
                            data_type=StringType(),
                            nullable=False,
                        ),
                    )
                ),
            ),
            Field(
                "attributes",
                MapType(
                    key_type=StringType(),
                    value_type=IntegerType(),
                    value_nullable=False,
                ),
            ),
        )
    )

    emitted = _dumps_schema(schema, name="all_types")
    reloaded = _loads_schema(emitted)

    assert reloaded == schema
    assert "type: int64" in emitted
    assert "type: uint64" in emitted
    assert "type: float64" in emitted
    assert "type: integer" not in emitted
    assert "type: float\n" not in emitted
    assert "type: time\n" in emitted
    assert "time:" in emitted
    assert "unit: ns" in emitted
    assert "type: timestamp\n" in emitted
    assert "timezone: Europe/Paris" in emitted
    assert "type: duration\n" in emitted
    assert "duration:" in emitted
    assert "unit: s" in emitted
    assert "element_nullable: false" in emitted
    assert "value_nullable: false" in emitted


def test_single_schema_emitter_preserves_unicode() -> None:
    schema = Schema(
        fields=(
            Field(
                name="libellé",
                data_type=StringType(),
                description="Client déjà actif — Paris",
            ),
        )
    )

    emitted = _dumps_schema(schema, name="données_clients")
    reloaded = _loads_schema(emitted)

    assert "données_clients" in emitted
    assert "libellé" in emitted
    assert "Client déjà actif — Paris" in emitted
    assert "\\u" not in emitted
    assert reloaded == schema


@pytest.mark.parametrize(
    "name",
    [
        "2026-10-01",
        "yes",
        "null",
        "00123",
        "true",
    ],
)
def test_ambiguous_schema_names_are_safely_quoted_and_round_trip(name: str) -> None:
    schema = Schema(fields=())

    emitted = _dumps_schema(schema, name=name)
    parsed = _loads_schemas(emitted)

    assert tuple(parsed) == (name,)
    assert parsed[name] == schema


@pytest.mark.parametrize(
    "description",
    [
        "yes",
        "no",
        "2026-10-01",
        "00123",
        "null",
        "false",
        "1.5",
    ],
)
def test_ambiguous_descriptions_remain_exact_strings(description: str) -> None:
    schema = Schema(
        fields=(
            Field(
                "value",
                StringType(),
                description=description,
            ),
        )
    )

    emitted = _dumps_schema(schema, name="sample")
    reloaded = _loads_schema(emitted)

    assert reloaded.fields[0].description == description


def test_multi_schema_emission_uses_schemas_form_and_preserves_order() -> None:
    schemas = {
        "customers": Schema(fields=(Field("id", IntegerType()),)),
        "orders": Schema(fields=(Field("id", IntegerType()),)),
    }

    emitted = _dumps_schemas(schemas)
    reloaded = _loads_schemas(emitted)

    assert emitted.startswith("version: 1\nschemas:\n")
    assert emitted.index("  customers:") < emitted.index("  orders:")
    assert tuple(reloaded) == ("customers", "orders")
    assert reloaded == schemas


def test_one_entry_multi_schema_export_keeps_multi_schema_form() -> None:
    emitted = _dumps_schemas(
        {
            "customers": Schema(fields=()),
        }
    )

    assert emitted.startswith("version: 1\nschemas:\n")
    assert "schema:\n" not in emitted
    assert tuple(_loads_schemas(emitted)) == ("customers",)


def test_empty_schema_and_empty_struct_round_trip() -> None:
    schema = Schema(
        fields=(
            Field(
                "empty_struct",
                StructType(fields=()),
            ),
        )
    )

    emitted = _dumps_schema(schema, name="empty")
    reloaded = _loads_schema(emitted)

    assert "fields: []" in emitted
    assert reloaded == schema


def test_emitter_never_generates_forbidden_yaml_mechanisms() -> None:
    schema = Schema(
        fields=(
            Field("first", StringType(), description="same"),
            Field("second", StringType(), description="same"),
        )
    )

    emitted = _dumps_schema(schema, name="sample")

    assert "&id" not in emitted
    assert "*id" not in emitted
    assert "!!" not in emitted
    assert "<<:" not in emitted
    assert "---" not in emitted
    assert "...\n" not in emitted
    assert _loads_schema(emitted) == schema


def test_direct_emitter_auto_selects_single_form_for_one_definition() -> None:
    document = SchemaDocument(
        version=1,
        schemas=(
            SchemaDefinition(
                name="sample",
                fields=(
                    FieldDefinition(
                        name="value",
                        data_type=StringTypeDefinition(),
                    ),
                ),
            ),
        ),
    )

    emitted = YamlSchemaEmitter().emit(document)

    assert emitted.startswith("version: 1\nschema:\n")


def test_direct_emitter_auto_selects_multi_form_for_many_definitions() -> None:
    document = SchemaDocument(
        version=1,
        schemas=(
            SchemaDefinition(name="first", fields=()),
            SchemaDefinition(name="second", fields=()),
        ),
    )

    emitted = YamlSchemaEmitter().emit(document)

    assert emitted.startswith("version: 1\nschemas:\n")


class _InvalidDocumentExporter(SchemaDocumentExporter):
    def export_single(
        self,
        schema: Schema,
        *,
        name: str,
        source: str | None = None,
    ) -> SchemaDocument:
        del schema, name, source
        duplicate = FieldDefinition(
            name="id",
            data_type=StringTypeDefinition(),
        )
        return SchemaDocument(
            version=1,
            schemas=(
                SchemaDefinition(
                    name="invalid",
                    fields=(duplicate, duplicate),
                ),
            ),
        )


class _SpyEmitter(YamlSchemaEmitter):
    def __init__(self) -> None:
        self.called = False

    def emit(
        self,
        document: SchemaDocument,
        *,
        multi_schema: bool | None = None,
    ) -> str:
        del document, multi_schema
        self.called = True
        return "should-not-emit\n"


def test_generated_document_is_validated_before_yaml_emission() -> None:
    emitter = _SpyEmitter()
    service = _DeclarativeSchemaExporter(
        exporter=_InvalidDocumentExporter(),
        emitter=emitter,
    )

    with pytest.raises(DeclarativeSchemaDuplicateFieldError):
        service.dumps_schema(
            Schema(fields=()),
            name="ignored",
        )

    assert emitter.called is False


def test_emitter_missing_yaml_dependency_is_controlled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yaml_module = importlib.import_module("pytransformkit.schema_io._yaml")
    real_import_module = yaml_module.importlib.import_module

    def controlled_import(name: str, package: str | None = None) -> object:
        if name == "yaml":
            raise ModuleNotFoundError("No module named 'yaml'")
        return real_import_module(name, package)

    monkeypatch.setattr(yaml_module.importlib, "import_module", controlled_import)

    document = SchemaDocument(
        version=1,
        schemas=(SchemaDefinition(name="sample", fields=()),),
    )
    with pytest.raises(DeclarativeSchemaDependencyError) as error:
        yaml_module.YamlSchemaEmitter().emit(document)

    assert str(error.value.code) == "PTK-DECL-010"
    assert error.value.dependency_name == "PyYAML"
