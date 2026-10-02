from __future__ import annotations

import pytest

from pytransformkit.domain.data import (
    DataType,
    Field,
    IntegerType,
    ListType,
    MapType,
    Schema,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pytransformkit.errors import DeclarativeSchemaExportError
from pytransformkit.schema_io._exporter import (
    SchemaDefinitionExporter,
    SchemaDocumentExporter,
)
from pytransformkit.schema_io._model import (
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimestampTypeDefinition,
)


def test_schema_exporter_preserves_order_nullability_and_description() -> None:
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

    definition = SchemaDefinitionExporter().export(
        schema,
        name="customers",
    )

    assert definition.name == "customers"
    assert tuple(field.name for field in definition.fields) == (
        "customer_id",
        "email",
    )
    assert definition.fields[0].data_type == IntegerTypeDefinition()
    assert definition.fields[0].nullable is False
    assert definition.fields[0].description == "Stable identifier"
    assert definition.fields[1].data_type == StringTypeDefinition()
    assert definition.fields[1].nullable is True
    assert definition.fields[1].description is None


def test_schema_exporter_preserves_nested_type_state() -> None:
    schema = Schema(
        fields=(
            Field(
                name="payload",
                data_type=MapType(
                    key_type=StringType(),
                    value_type=ListType(
                        element_type=StructType(
                            fields=(
                                StructField(
                                    name="created_at",
                                    data_type=TimestampType(
                                        unit="ns",
                                        timezone="UTC",
                                    ),
                                    nullable=False,
                                ),
                            )
                        ),
                        element_nullable=False,
                    ),
                    value_nullable=False,
                ),
                nullable=False,
            ),
        )
    )

    definition = SchemaDefinitionExporter().export(
        schema,
        name="events",
    )

    assert definition.fields[0].data_type == MapTypeDefinition(
        key_type=StringTypeDefinition(),
        value_type=ListTypeDefinition(
            element_type=StructTypeDefinition(
                fields=(
                    StructFieldDefinition(
                        name="created_at",
                        data_type=TimestampTypeDefinition(
                            unit="ns",
                            timezone="UTC",
                        ),
                        nullable=False,
                    ),
                )
            ),
            element_nullable=False,
        ),
        value_nullable=False,
    )


@pytest.mark.parametrize("name", ["", " ", "\t"])
def test_schema_export_requires_explicit_non_blank_name(name: str) -> None:
    with pytest.raises(DeclarativeSchemaExportError) as error:
        SchemaDefinitionExporter().export(
            Schema(fields=()),
            name=name,
        )

    assert str(error.value.code) == "PTK-DECL-012"
    assert error.value.object_path == "schema.name"


def test_schema_name_is_external_identity_not_injected_into_schema() -> None:
    schema = Schema(fields=(Field("id", IntegerType()),))
    exporter = SchemaDefinitionExporter()

    customers = exporter.export(schema, name="customers")
    clients = exporter.export(schema, name="clients")

    assert customers.name == "customers"
    assert clients.name == "clients"
    assert customers.fields == clients.fields
    assert not hasattr(schema, "name")


def test_multi_schema_document_export_preserves_mapping_order() -> None:
    exporter = SchemaDocumentExporter()
    document = exporter.export_many(
        {
            "customers": Schema(fields=(Field("id", IntegerType()),)),
            "orders": Schema(fields=(Field("id", IntegerType()),)),
        }
    )

    assert tuple(schema.name for schema in document.schemas) == (
        "customers",
        "orders",
    )


def test_single_document_export_uses_declarative_version_one() -> None:
    document = SchemaDocumentExporter().export_single(
        Schema(fields=()),
        name="empty",
    )

    assert document.version == 1
    assert tuple(schema.name for schema in document.schemas) == ("empty",)


class CustomDataType(DataType):
    pass


def test_unsupported_custom_datatype_fails_without_semantic_degradation() -> None:
    schema = Schema(
        fields=(
            Field(
                name="custom",
                data_type=CustomDataType(),
            ),
        )
    )

    with pytest.raises(DeclarativeSchemaExportError) as error:
        SchemaDefinitionExporter().export(
            schema,
            name="sample",
            source="generated",
        )

    assert str(error.value.code) == "PTK-DECL-012"
    assert error.value.source == "generated"
    assert error.value.object_path == "schema.fields[0].type"
    assert isinstance(error.value.__cause__, DeclarativeSchemaExportError)


def test_corrupted_nullable_state_fails_instead_of_bool_coercion() -> None:
    field = Field("id", IntegerType())
    object.__setattr__(field, "nullable", 1)
    schema = Schema(fields=(field,))

    with pytest.raises(DeclarativeSchemaExportError) as error:
        SchemaDefinitionExporter().export(
            schema,
            name="sample",
        )

    assert error.value.object_path == "schema.fields[0].nullable"


def test_corrupted_description_state_is_not_silently_dropped() -> None:
    field = Field("id", IntegerType(), description="valid")
    object.__setattr__(field, "description", " ")
    schema = Schema(fields=(field,))

    with pytest.raises(DeclarativeSchemaExportError) as error:
        SchemaDefinitionExporter().export(
            schema,
            name="sample",
        )

    assert error.value.object_path == "schema.fields[0].description"
