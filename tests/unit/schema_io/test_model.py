from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from pytransformkit.schema_io._model import (
    BinaryTypeDefinition,
    BooleanTypeDefinition,
    DateTypeDefinition,
    DecimalTypeDefinition,
    DurationTypeDefinition,
    FieldDefinition,
    FloatTypeDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    SchemaDefinition,
    SchemaDocument,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimeTypeDefinition,
    TimestampTypeDefinition,
    TypeDefinition,
    UnknownTypeDefinition,
)


def test_scalar_definition_defaults_are_semantic_values() -> None:
    assert IntegerTypeDefinition() == IntegerTypeDefinition(bits=64, signed=True)
    assert FloatTypeDefinition() == FloatTypeDefinition(bits=64)
    assert TimeTypeDefinition() == TimeTypeDefinition(unit="us")
    assert TimestampTypeDefinition() == TimestampTypeDefinition(
        unit="us",
        timezone=None,
    )
    assert DurationTypeDefinition() == DurationTypeDefinition(unit="us")


@pytest.mark.parametrize(
    "definition",
    [
        StringTypeDefinition(),
        BooleanTypeDefinition(),
        IntegerTypeDefinition(),
        FloatTypeDefinition(),
        DecimalTypeDefinition(precision=18, scale=2),
        BinaryTypeDefinition(),
        DateTypeDefinition(),
        TimeTypeDefinition(),
        TimestampTypeDefinition(),
        DurationTypeDefinition(),
        UnknownTypeDefinition(),
        ListTypeDefinition(StringTypeDefinition()),
        StructTypeDefinition(
            fields=(
                StructFieldDefinition(
                    name="city",
                    data_type=StringTypeDefinition(),
                ),
            )
        ),
        MapTypeDefinition(
            key_type=StringTypeDefinition(),
            value_type=IntegerTypeDefinition(),
        ),
    ],
)
def test_every_v1_type_variant_is_a_type_definition(
    definition: TypeDefinition,
) -> None:
    assert isinstance(definition, TypeDefinition)
    assert not hasattr(definition, "__dict__")


def test_definition_values_are_frozen_and_hashable() -> None:
    field = FieldDefinition(
        name="customer_id",
        data_type=IntegerTypeDefinition(),
        nullable=False,
    )
    schema = SchemaDefinition(name="customers", fields=(field,))
    document = SchemaDocument(version=1, schemas=(schema,))

    with pytest.raises(FrozenInstanceError):
        field.nullable = True

    assert hash(field) == hash(
        FieldDefinition(
            name="customer_id",
            data_type=IntegerTypeDefinition(),
            nullable=False,
        )
    )
    assert hash(schema)
    assert hash(document)


def test_nested_definition_construction_preserves_order_and_semantics() -> None:
    address = StructTypeDefinition(
        fields=(
            StructFieldDefinition(
                name="city",
                data_type=StringTypeDefinition(),
                nullable=False,
            ),
            StructFieldDefinition(
                name="postal_code",
                data_type=StringTypeDefinition(),
            ),
        )
    )
    tags = ListTypeDefinition(
        element_type=StringTypeDefinition(),
        element_nullable=False,
    )
    attributes = MapTypeDefinition(
        key_type=StringTypeDefinition(),
        value_type=TimestampTypeDefinition(unit="ns", timezone="UTC"),
        value_nullable=False,
    )
    schema = SchemaDefinition(
        name="customers",
        fields=(
            FieldDefinition("address", address, nullable=False),
            FieldDefinition("tags", tags),
            FieldDefinition("attributes", attributes),
        ),
    )
    document = SchemaDocument(version=1, schemas=(schema,))

    assert tuple(field.name for field in schema.fields) == (
        "address",
        "tags",
        "attributes",
    )
    assert tuple(field.name for field in address.fields) == (
        "city",
        "postal_code",
    )
    assert document.schemas[0] == schema


def test_field_definition_defaults_match_canonical_field_semantics() -> None:
    field = FieldDefinition(
        name="email",
        data_type=StringTypeDefinition(),
    )

    assert field.nullable is True
    assert field.description is None


def test_struct_field_definition_has_no_description_semantics() -> None:
    nested = StructFieldDefinition(
        name="city",
        data_type=StringTypeDefinition(),
    )

    assert not hasattr(nested, "description")


@pytest.mark.parametrize("bits", [8, 16, 32, 64])
@pytest.mark.parametrize("signed", [True, False])
def test_integer_definition_accepts_supported_widths(
    bits: int,
    signed: bool,
) -> None:
    assert IntegerTypeDefinition(bits=bits, signed=signed).bits == bits


@pytest.mark.parametrize("bits", [0, 7, 128])
def test_integer_definition_rejects_unsupported_widths(bits: int) -> None:
    with pytest.raises(ValueError, match="bits must be one of"):
        IntegerTypeDefinition(bits=bits)


@pytest.mark.parametrize("bits", [32, 64])
def test_float_definition_accepts_supported_widths(bits: int) -> None:
    assert FloatTypeDefinition(bits=bits).bits == bits


@pytest.mark.parametrize("bits", [16, 128])
def test_float_definition_rejects_unsupported_widths(bits: int) -> None:
    with pytest.raises(ValueError, match="bits must be one of"):
        FloatTypeDefinition(bits=bits)


@pytest.mark.parametrize("unit", ["s", "ms", "us", "ns"])
def test_temporal_definitions_accept_supported_units(unit: str) -> None:
    assert TimeTypeDefinition(unit=unit).unit == unit
    assert TimestampTypeDefinition(unit=unit).unit == unit
    assert DurationTypeDefinition(unit=unit).unit == unit


@pytest.mark.parametrize("unit", ["", "minute", "µs"])
def test_temporal_definitions_reject_invalid_units(unit: str) -> None:
    with pytest.raises(ValueError):
        TimeTypeDefinition(unit=unit)
    with pytest.raises(ValueError):
        TimestampTypeDefinition(unit=unit)
    with pytest.raises(ValueError):
        DurationTypeDefinition(unit=unit)


@pytest.mark.parametrize(
    ("precision", "scale"),
    [
        (0, 0),
        (-1, 0),
        (10, -1),
        (10, 11),
    ],
)
def test_decimal_definition_rejects_invalid_parameters(
    precision: int,
    scale: int,
) -> None:
    with pytest.raises(ValueError):
        DecimalTypeDefinition(precision=precision, scale=scale)


def test_timestamp_timezone_must_be_non_blank_when_present() -> None:
    with pytest.raises(ValueError, match="timezone"):
        TimestampTypeDefinition(timezone="   ")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: IntegerTypeDefinition(bits=True),
        lambda: IntegerTypeDefinition(signed=1),
        lambda: FloatTypeDefinition(bits=True),
        lambda: DecimalTypeDefinition(precision=True, scale=0),
        lambda: ListTypeDefinition(
            element_type=StringTypeDefinition(),
            element_nullable=1,
        ),
        lambda: FieldDefinition(
            name="id",
            data_type=StringTypeDefinition(),
            nullable=1,
        ),
        lambda: SchemaDocument(version=True, schemas=()),
    ],
)
def test_definition_model_does_not_coerce_scalar_types(factory: object) -> None:
    with pytest.raises(TypeError):
        factory()  # type: ignore[operator]


@pytest.mark.parametrize("name", ["", " ", "\t"])
def test_names_must_contain_non_whitespace_text(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        FieldDefinition(name=name, data_type=StringTypeDefinition())
    with pytest.raises(ValueError, match="name"):
        StructFieldDefinition(name=name, data_type=StringTypeDefinition())
    with pytest.raises(ValueError, match="name"):
        SchemaDefinition(name=name, fields=())


def test_field_description_must_be_non_blank_when_present() -> None:
    with pytest.raises(ValueError, match="description"):
        FieldDefinition(
            name="email",
            data_type=StringTypeDefinition(),
            description=" ",
        )


def test_definition_references_must_be_typed_values() -> None:
    with pytest.raises(TypeError, match="TypeDefinition"):
        FieldDefinition(name="email", data_type="string")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TypeDefinition"):
        ListTypeDefinition(element_type="string")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TypeDefinition"):
        MapTypeDefinition(  # type: ignore[arg-type]
            key_type="string",
            value_type=StringTypeDefinition(),
        )


def test_collections_require_tuples_and_typed_members() -> None:
    field = FieldDefinition(name="id", data_type=IntegerTypeDefinition())
    schema = SchemaDefinition(name="customers", fields=(field,))

    with pytest.raises(TypeError, match="tuple"):
        SchemaDefinition(name="customers", fields=[field])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="FieldDefinition"):
        SchemaDefinition(name="customers", fields=("id",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="tuple"):
        StructTypeDefinition(fields=[])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SchemaDefinition"):
        SchemaDocument(version=1, schemas=(field,))  # type: ignore[arg-type]

    assert SchemaDocument(version=1, schemas=(schema,)).schemas == (schema,)
