from __future__ import annotations

import pytest

from pytransformkit.errors import (
    DeclarativeSchemaDuplicateFieldError,
    DeclarativeSchemaDuplicateSchemaError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaValidationError,
    DeclarativeSchemaVersionError,
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
    TypeDefinition,
)
from pytransformkit.schema_io._validation import SchemaDefinitionValidator

VALIDATOR = SchemaDefinitionValidator()


def _document(*schemas: SchemaDefinition, version: int = 1) -> SchemaDocument:
    return SchemaDocument(version=version, schemas=tuple(schemas))


def _schema(
    name: str = "customers",
    *fields: FieldDefinition,
) -> SchemaDefinition:
    return SchemaDefinition(name=name, fields=tuple(fields))


def _field(
    name: str,
    data_type: TypeDefinition | None = None,
    *,
    nullable: bool = True,
) -> FieldDefinition:
    return FieldDefinition(
        name=name,
        data_type=data_type or StringTypeDefinition(),
        nullable=nullable,
    )


def test_valid_document_passes_without_mutation() -> None:
    document = _document(
        _schema(
            "customers",
            _field("customer_id", IntegerTypeDefinition(), nullable=False),
            _field(
                "profile",
                StructTypeDefinition(
                    fields=(
                        StructFieldDefinition(
                            name="email",
                            data_type=StringTypeDefinition(),
                            nullable=True,
                        ),
                        StructFieldDefinition(
                            name="tags",
                            data_type=ListTypeDefinition(
                                element_type=StringTypeDefinition(),
                                element_nullable=False,
                            ),
                            nullable=False,
                        ),
                    )
                ),
            ),
            _field(
                "attributes",
                MapTypeDefinition(
                    key_type=StringTypeDefinition(),
                    value_type=TimestampTypeDefinition(
                        unit="ns",
                        timezone="UTC",
                    ),
                    value_nullable=False,
                ),
            ),
        ),
        _schema("orders", _field("order_id", IntegerTypeDefinition())),
    )
    before = hash(document)

    assert VALIDATOR.validate_document(document) is None
    assert hash(document) == before


@pytest.mark.parametrize("version", [2, 0, -1])
def test_unsupported_document_version_uses_version_error(version: int) -> None:
    with pytest.raises(DeclarativeSchemaVersionError) as error:
        VALIDATOR.validate_document(_document(version=version))

    assert str(error.value.code) == "PTK-DECL-002"
    assert error.value.actual_version == version
    assert error.value.supported_versions == (1,)
    assert error.value.object_path == "version"


def test_non_integer_document_version_uses_version_error() -> None:
    document = _document()
    object.__setattr__(document, "version", "1")

    with pytest.raises(DeclarativeSchemaVersionError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.actual_version == "1"
    assert error.value.object_path == "version"


def test_version_failure_precedes_schema_failures() -> None:
    document = _document(
        _schema("customers"),
        _schema("customers"),
    )
    object.__setattr__(document, "version", 2)

    with pytest.raises(DeclarativeSchemaVersionError):
        VALIDATOR.validate_document(document)


def test_duplicate_schema_names_fail_on_second_declaration() -> None:
    document = _document(
        _schema("customers"),
        _schema("orders"),
        _schema("customers"),
    )

    with pytest.raises(DeclarativeSchemaDuplicateSchemaError) as error:
        VALIDATOR.validate_document(document, source="schemas.yml")

    assert str(error.value.code) == "PTK-DECL-008"
    assert error.value.schema_name == "customers"
    assert error.value.source == "schemas.yml"
    assert error.value.object_path == "schemas[2].name"
    assert error.value.first_context is not None
    assert error.value.first_context.object_path == "schemas[0].name"


def test_duplicate_top_level_fields_fail_before_domain_construction() -> None:
    document = _document(
        _schema(
            "customers",
            _field("customer_id"),
            _field("email"),
            _field("customer_id", IntegerTypeDefinition()),
        )
    )

    with pytest.raises(DeclarativeSchemaDuplicateFieldError) as error:
        VALIDATOR.validate_document(document)

    assert str(error.value.code) == "PTK-DECL-007"
    assert error.value.field_name == "customer_id"
    assert error.value.object_path == "schemas[0].fields[2].name"
    assert error.value.first_context is not None
    assert error.value.first_context.object_path == "schemas[0].fields[0].name"


def test_duplicate_nested_struct_fields_fail_depth_first() -> None:
    nested = StructTypeDefinition(
        fields=(
            StructFieldDefinition("city", StringTypeDefinition()),
            StructFieldDefinition("city", IntegerTypeDefinition()),
        )
    )
    document = _document(_schema("customers", _field("address", nested)))

    with pytest.raises(DeclarativeSchemaDuplicateFieldError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.field_name == "city"
    assert error.value.object_path == "schemas[0].fields[0].type.struct.fields[1].name"
    assert error.value.first_context is not None
    assert (
        error.value.first_context.object_path
        == "schemas[0].fields[0].type.struct.fields[0].name"
    )


def test_custom_type_definition_fails_closed() -> None:
    class CustomTypeDefinition(TypeDefinition):
        pass

    document = _document(_schema("customers", _field("custom", CustomTypeDefinition())))

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document)

    assert str(error.value.code) == "PTK-DECL-005"
    assert error.value.object_path == "schemas[0].fields[0].type"
    assert "CustomTypeDefinition" in str(error.value)


def test_invalid_decimal_state_reports_precise_path() -> None:
    decimal = DecimalTypeDefinition(precision=18, scale=2)
    object.__setattr__(decimal, "scale", 19)
    document = _document(_schema("customers", _field("balance", decimal)))

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas[0].fields[0].type.decimal.scale"
    assert "must not exceed precision" in str(error.value)


@pytest.mark.parametrize("unit", ["seconds", "NS", ""])
def test_invalid_temporal_unit_reports_type_error(unit: str) -> None:
    timestamp = TimestampTypeDefinition()
    object.__setattr__(timestamp, "unit", unit)
    document = _document(_schema("events", _field("created_at", timestamp)))

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas[0].fields[0].type.timestamp.unit"


def test_blank_timestamp_timezone_reports_type_error() -> None:
    timestamp = TimestampTypeDefinition(timezone="UTC")
    object.__setattr__(timestamp, "timezone", " ")
    document = _document(_schema("events", _field("created_at", timestamp)))

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas[0].fields[0].type.timestamp.timezone"


def test_non_boolean_field_nullability_is_validation_error() -> None:
    field = _field("email")
    object.__setattr__(field, "nullable", 1)
    document = _document(_schema("customers", field))

    with pytest.raises(DeclarativeSchemaValidationError) as error:
        VALIDATOR.validate_document(document)

    assert str(error.value.code) == "PTK-DECL-003"
    assert error.value.object_path == "schemas[0].fields[0].nullable"


def test_non_boolean_nested_nullability_is_type_error() -> None:
    nested = ListTypeDefinition(element_type=StringTypeDefinition())
    object.__setattr__(nested, "element_nullable", 1)
    document = _document(_schema("customers", _field("tags", nested)))

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas[0].fields[0].type.list.element_nullable"


def test_blank_programmatic_schema_name_is_validation_error() -> None:
    schema = _schema("customers")
    object.__setattr__(schema, "name", " ")
    document = _document(schema)

    with pytest.raises(DeclarativeSchemaValidationError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas[0].name"


def test_invalid_first_nested_type_precedes_later_duplicate_field() -> None:
    decimal = DecimalTypeDefinition(precision=18, scale=2)
    object.__setattr__(decimal, "scale", 19)
    document = _document(
        _schema(
            "customers",
            _field("amount", decimal),
            _field("amount", StringTypeDefinition()),
        )
    )

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas[0].fields[0].type.decimal.scale"


def test_source_label_is_propagated_to_nested_diagnostics() -> None:
    nested = MapTypeDefinition(
        key_type=StringTypeDefinition(),
        value_type=TimestampTypeDefinition(),
    )
    object.__setattr__(nested.value_type, "unit", "minutes")
    document = _document(_schema("events", _field("payload", nested)))

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        VALIDATOR.validate_document(document, source="schemas/events.yml")

    assert error.value.source == "schemas/events.yml"
    assert (
        error.value.object_path
        == "schemas[0].fields[0].type.map.value.type.timestamp.unit"
    )


def test_document_collection_shape_is_revalidated() -> None:
    document = _document(_schema("customers"))
    object.__setattr__(document, "schemas", [_schema("customers")])

    with pytest.raises(DeclarativeSchemaValidationError) as error:
        VALIDATOR.validate_document(document)

    assert error.value.object_path == "schemas"
