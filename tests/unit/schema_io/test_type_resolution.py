from __future__ import annotations

import pytest

from pytransformkit.domain.data import (
    BinaryType,
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    DurationType,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    StringType,
    StructField,
    StructType,
    TimeType,
    TimestampType,
    UnknownType,
)
from pytransformkit.errors import (
    DeclarativeSchemaExportError,
    DeclarativeSchemaTypeError,
)
from pytransformkit.schema_io._model import (
    BinaryTypeDefinition,
    BooleanTypeDefinition,
    DateTypeDefinition,
    DecimalTypeDefinition,
    DurationTypeDefinition,
    FloatTypeDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimeTypeDefinition,
    TimestampTypeDefinition,
    TypeDefinition,
    UnknownTypeDefinition,
)
from pytransformkit.schema_io._type_resolution import (
    DeclarativeTypeExporter,
    DeclarativeTypeResolver,
)

RESOLVER = DeclarativeTypeResolver()
EXPORTER = DeclarativeTypeExporter()


@pytest.mark.parametrize(
    ("definition", "expected"),
    [
        (StringTypeDefinition(), StringType()),
        (BooleanTypeDefinition(), BooleanType()),
        (IntegerTypeDefinition(bits=8, signed=True), IntegerType(8, True)),
        (IntegerTypeDefinition(bits=16, signed=True), IntegerType(16, True)),
        (IntegerTypeDefinition(bits=32, signed=True), IntegerType(32, True)),
        (IntegerTypeDefinition(bits=64, signed=True), IntegerType(64, True)),
        (IntegerTypeDefinition(bits=8, signed=False), IntegerType(8, False)),
        (IntegerTypeDefinition(bits=16, signed=False), IntegerType(16, False)),
        (IntegerTypeDefinition(bits=32, signed=False), IntegerType(32, False)),
        (IntegerTypeDefinition(bits=64, signed=False), IntegerType(64, False)),
        (FloatTypeDefinition(bits=32), FloatType(32)),
        (FloatTypeDefinition(bits=64), FloatType(64)),
        (DecimalTypeDefinition(precision=18, scale=2), DecimalType(18, 2)),
        (BinaryTypeDefinition(), BinaryType()),
        (DateTypeDefinition(), DateType()),
        (TimeTypeDefinition(), TimeType()),
        (TimeTypeDefinition(unit="ns"), TimeType(unit="ns")),
        (TimestampTypeDefinition(), TimestampType()),
        (
            TimestampTypeDefinition(unit="us", timezone="UTC"),
            TimestampType(unit="us", timezone="UTC"),
        ),
        (DurationTypeDefinition(), DurationType()),
        (DurationTypeDefinition(unit="ms"), DurationType(unit="ms")),
        (UnknownTypeDefinition(), UnknownType()),
    ],
)
def test_resolver_maps_all_scalar_definition_states(
    definition: TypeDefinition,
    expected: DataType,
) -> None:
    assert RESOLVER.resolve(definition) == expected


@pytest.mark.parametrize(
    "data_type",
    [
        StringType(),
        BooleanType(),
        IntegerType(bits=8, signed=True),
        IntegerType(bits=16, signed=True),
        IntegerType(bits=32, signed=True),
        IntegerType(bits=64, signed=True),
        IntegerType(bits=8, signed=False),
        IntegerType(bits=16, signed=False),
        IntegerType(bits=32, signed=False),
        IntegerType(bits=64, signed=False),
        FloatType(bits=32),
        FloatType(bits=64),
        DecimalType(precision=1, scale=0),
        DecimalType(precision=18, scale=2),
        DecimalType(precision=18, scale=18),
        BinaryType(),
        DateType(),
        TimeType(unit="s"),
        TimeType(unit="ms"),
        TimeType(unit="us"),
        TimeType(unit="ns"),
        TimestampType(),
        TimestampType(unit="ns"),
        TimestampType(unit="us", timezone="UTC"),
        TimestampType(unit="ms", timezone="Europe/Paris"),
        DurationType(unit="s"),
        DurationType(unit="ms"),
        DurationType(unit="us"),
        DurationType(unit="ns"),
        UnknownType(),
    ],
)
def test_scalar_domain_types_round_trip_through_definitions(
    data_type: DataType,
) -> None:
    definition = EXPORTER.export(data_type)

    assert RESOLVER.resolve(definition) == data_type


def test_list_mapping_preserves_recursive_type_and_nullability() -> None:
    definition = ListTypeDefinition(
        element_type=DecimalTypeDefinition(precision=18, scale=2),
        element_nullable=False,
    )

    resolved = RESOLVER.resolve(definition)

    assert resolved == ListType(
        element_type=DecimalType(precision=18, scale=2),
        element_nullable=False,
    )
    assert EXPORTER.export(resolved) == definition


def test_struct_mapping_preserves_order_nested_types_and_nullability() -> None:
    definition = StructTypeDefinition(
        fields=(
            StructFieldDefinition(
                name="city",
                data_type=StringTypeDefinition(),
                nullable=False,
            ),
            StructFieldDefinition(
                name="coordinates",
                data_type=StructTypeDefinition(
                    fields=(
                        StructFieldDefinition(
                            name="latitude",
                            data_type=FloatTypeDefinition(bits=64),
                            nullable=False,
                        ),
                        StructFieldDefinition(
                            name="longitude",
                            data_type=FloatTypeDefinition(bits=64),
                            nullable=False,
                        ),
                    )
                ),
                nullable=True,
            ),
        )
    )

    resolved = RESOLVER.resolve(definition)

    assert resolved == StructType(
        fields=(
            StructField(
                name="city",
                data_type=StringType(),
                nullable=False,
            ),
            StructField(
                name="coordinates",
                data_type=StructType(
                    fields=(
                        StructField(
                            name="latitude",
                            data_type=FloatType(bits=64),
                            nullable=False,
                        ),
                        StructField(
                            name="longitude",
                            data_type=FloatType(bits=64),
                            nullable=False,
                        ),
                    )
                ),
                nullable=True,
            ),
        )
    )
    assert EXPORTER.export(resolved) == definition


def test_empty_struct_mapping_is_preserved() -> None:
    definition = StructTypeDefinition(fields=())

    assert RESOLVER.resolve(definition) == StructType(fields=())
    assert EXPORTER.export(StructType(fields=())) == definition


def test_map_mapping_preserves_recursive_key_value_and_nullability() -> None:
    definition = MapTypeDefinition(
        key_type=IntegerTypeDefinition(bits=64, signed=True),
        value_type=ListTypeDefinition(
            element_type=TimestampTypeDefinition(
                unit="ns",
                timezone="UTC",
            ),
            element_nullable=False,
        ),
        value_nullable=False,
    )

    resolved = RESOLVER.resolve(definition)

    assert resolved == MapType(
        key_type=IntegerType(bits=64, signed=True),
        value_type=ListType(
            element_type=TimestampType(unit="ns", timezone="UTC"),
            element_nullable=False,
        ),
        value_nullable=False,
    )
    assert EXPORTER.export(resolved) == definition


def test_deep_recursive_mapping_round_trip() -> None:
    data_type = ListType(
        element_type=StructType(
            fields=(
                StructField(
                    name="attributes",
                    data_type=MapType(
                        key_type=StringType(),
                        value_type=ListType(
                            element_type=DecimalType(precision=12, scale=4),
                            element_nullable=False,
                        ),
                        value_nullable=False,
                    ),
                    nullable=False,
                ),
            )
        ),
        element_nullable=True,
    )

    definition = EXPORTER.export(data_type)

    assert RESOLVER.resolve(definition) == data_type
    assert EXPORTER.export(RESOLVER.resolve(definition)) == definition


def test_resolver_rejects_custom_type_definition_subclass() -> None:
    class CustomTypeDefinition(TypeDefinition):
        pass

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        RESOLVER.resolve(CustomTypeDefinition())

    assert str(error.value.code) == "PTK-DECL-005"
    assert "CustomTypeDefinition" in str(error.value)


def test_exporter_rejects_custom_data_type_subclass() -> None:
    class CustomDataType(DataType):
        pass

    with pytest.raises(DeclarativeSchemaExportError) as error:
        EXPORTER.export(CustomDataType())

    assert str(error.value.code) == "PTK-DECL-012"
    assert "CustomDataType" in str(error.value)


@pytest.mark.parametrize(
    "data_type",
    [
        IntegerType(bits=64, signed=1),  # type: ignore[arg-type]
        ListType(
            element_type=StringType(),
            element_nullable=1,  # type: ignore[arg-type]
        ),
        StructType(
            fields=(
                StructField(
                    name="city",
                    data_type=StringType(),
                    nullable=1,  # type: ignore[arg-type]
                ),
            )
        ),
        MapType(
            key_type=StringType(),
            value_type=StringType(),
            value_nullable=1,  # type: ignore[arg-type]
        ),
    ],
)
def test_exporter_rejects_non_boolean_canonical_nullability_state(
    data_type: DataType,
) -> None:
    with pytest.raises(DeclarativeSchemaExportError) as error:
        EXPORTER.export(data_type)

    assert str(error.value.code) == "PTK-DECL-012"


def test_type_mapping_is_deterministic_and_stateless() -> None:
    definition = MapTypeDefinition(
        key_type=StringTypeDefinition(),
        value_type=IntegerTypeDefinition(bits=32, signed=False),
        value_nullable=True,
    )

    first = RESOLVER.resolve(definition)
    second = RESOLVER.resolve(definition)

    assert first == second
    assert first is not second
    assert EXPORTER.export(first) == EXPORTER.export(second)
