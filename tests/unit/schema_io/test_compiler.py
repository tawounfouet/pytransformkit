from __future__ import annotations

import pytest

from pytransformkit.domain.data import (
    DataType,
    DecimalType,
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
from pytransformkit.errors import (
    DeclarativeSchemaCardinalityError,
    DeclarativeSchemaDuplicateFieldError,
    DeclarativeSchemaTypeError,
    DuplicateFieldError,
)
from pytransformkit.schema_io._compiler import (
    SchemaDefinitionCompiler,
    SchemaDocumentCompiler,
)
from pytransformkit.schema_io._model import (
    DecimalTypeDefinition,
    FieldDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    SchemaDefinition,
    SchemaDocument,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimestampTypeDefinition,
)
from pytransformkit.schema_io._type_resolution import DeclarativeTypeResolver


def test_schema_definition_compiler_preserves_field_semantics_and_order() -> None:
    definition = SchemaDefinition(
        name="customers",
        fields=(
            FieldDefinition(
                name="customer_id",
                data_type=IntegerTypeDefinition(),
                nullable=False,
                description="Stable identifier",
            ),
            FieldDefinition(
                name="email",
                data_type=StringTypeDefinition(),
                nullable=True,
            ),
        ),
    )

    compiled = SchemaDefinitionCompiler().compile(definition)

    assert compiled == Schema(
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
    assert compiled.names() == ("customer_id", "email")


def test_schema_definition_compiler_resolves_nested_types_recursively() -> None:
    definition = SchemaDefinition(
        name="events",
        fields=(
            FieldDefinition(
                name="payload",
                data_type=MapTypeDefinition(
                    key_type=StringTypeDefinition(),
                    value_type=ListTypeDefinition(
                        element_type=StructTypeDefinition(
                            fields=(
                                StructFieldDefinition(
                                    name="amount",
                                    data_type=DecimalTypeDefinition(18, 2),
                                    nullable=False,
                                ),
                                StructFieldDefinition(
                                    name="created_at",
                                    data_type=TimestampTypeDefinition(
                                        unit="ns",
                                        timezone="UTC",
                                    ),
                                    nullable=True,
                                ),
                            )
                        ),
                        element_nullable=False,
                    ),
                    value_nullable=False,
                ),
                nullable=False,
            ),
        ),
    )

    compiled = SchemaDefinitionCompiler().compile(definition)

    assert compiled == Schema(
        fields=(
            Field(
                name="payload",
                data_type=MapType(
                    key_type=StringType(),
                    value_type=ListType(
                        element_type=StructType(
                            fields=(
                                StructField(
                                    name="amount",
                                    data_type=DecimalType(18, 2),
                                    nullable=False,
                                ),
                                StructField(
                                    name="created_at",
                                    data_type=TimestampType(
                                        unit="ns",
                                        timezone="UTC",
                                    ),
                                    nullable=True,
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


def test_document_compiler_preserves_schema_declaration_order() -> None:
    document = SchemaDocument(
        version=1,
        schemas=(
            SchemaDefinition(
                name="customers",
                fields=(
                    FieldDefinition(
                        name="id",
                        data_type=IntegerTypeDefinition(),
                    ),
                ),
            ),
            SchemaDefinition(
                name="orders",
                fields=(
                    FieldDefinition(
                        name="id",
                        data_type=IntegerTypeDefinition(),
                    ),
                ),
            ),
        ),
    )

    compiled = SchemaDocumentCompiler().compile(document)

    assert tuple(compiled) == ("customers", "orders")
    assert compiled["customers"].names() == ("id",)
    assert compiled["orders"].names() == ("id",)


@pytest.mark.parametrize("count", [0, 2])
def test_single_document_compilation_enforces_exact_cardinality(count: int) -> None:
    schemas = tuple(
        SchemaDefinition(name=f"schema_{index}", fields=()) for index in range(count)
    )
    document = SchemaDocument(version=1, schemas=schemas)

    with pytest.raises(DeclarativeSchemaCardinalityError) as error:
        SchemaDocumentCompiler().compile_single(
            document,
            source="schemas.yml",
        )

    assert str(error.value.code) == "PTK-DECL-009"
    assert error.value.required_count == 1
    assert error.value.actual_count == count
    assert error.value.source == "schemas.yml"
    assert error.value.object_path == "schemas"


def test_single_document_compilation_returns_only_schema_value() -> None:
    document = SchemaDocument(
        version=1,
        schemas=(
            SchemaDefinition(
                name="customers",
                fields=(
                    FieldDefinition(
                        name="id",
                        data_type=IntegerTypeDefinition(),
                    ),
                ),
            ),
        ),
    )

    compiled = SchemaDocumentCompiler().compile_single(document)

    assert isinstance(compiled, Schema)
    assert compiled.names() == ("id",)


def test_unvalidated_duplicate_fields_translate_domain_error_with_cause() -> None:
    definition = SchemaDefinition(
        name="customers",
        fields=(
            FieldDefinition(
                name="id",
                data_type=IntegerTypeDefinition(),
            ),
            FieldDefinition(
                name="id",
                data_type=StringTypeDefinition(),
            ),
        ),
    )

    with pytest.raises(DeclarativeSchemaDuplicateFieldError) as error:
        SchemaDefinitionCompiler().compile(
            definition,
            source="programmatic",
            object_path="schemas[0]",
        )

    assert str(error.value.code) == "PTK-DECL-007"
    assert error.value.field_name == "id"
    assert error.value.object_path == "schemas[0].fields[1].name"
    assert error.value.first_context is not None
    assert error.value.first_context.object_path == "schemas[0].fields[0].name"
    assert isinstance(error.value.__cause__, DuplicateFieldError)


class _RejectingResolver(DeclarativeTypeResolver):
    def resolve(self, definition: object) -> DataType:  # type: ignore[override]
        raise ValueError("simulated canonical constructor rejection")


def test_known_domain_type_construction_failure_is_translated_and_chained() -> None:
    definition = SchemaDefinition(
        name="customers",
        fields=(
            FieldDefinition(
                name="id",
                data_type=IntegerTypeDefinition(),
            ),
        ),
    )

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        SchemaDefinitionCompiler(
            type_resolver=_RejectingResolver(),
        ).compile(
            definition,
            source="programmatic",
            object_path="schemas[0]",
        )

    assert str(error.value.code) == "PTK-DECL-005"
    assert error.value.source == "programmatic"
    assert error.value.object_path == "schemas[0].fields[0].type"
    assert isinstance(error.value.__cause__, ValueError)
