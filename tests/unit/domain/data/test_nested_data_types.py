from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import (
    DurationType,
    IntegerType,
    ListType,
    MapType,
    StringType,
    StructField,
    StructType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.errors.schema import FieldNotFoundError


def test_nested_and_duration_data_types_are_structural() -> None:
    profile = StructType(
        fields=(
            StructField("city", StringType(), nullable=False),
            StructField("score", IntegerType(), nullable=True),
        )
    )

    assert profile == StructType(
        fields=(
            StructField("city", StringType(), nullable=False),
            StructField("score", IntegerType(), nullable=True),
        )
    )
    assert ListType(StringType()) == ListType(StringType())
    assert MapType(StringType(), IntegerType()) == MapType(
        StringType(),
        IntegerType(),
    )
    assert DurationType(unit="ms") == DurationType(unit="ms")


def test_data_type_factories_cover_nested_and_duration_types() -> None:
    assert DurationType("us") == DurationType(unit="us")
    assert ListType(StringType()) == ListType(
        element_type=StringType(),
        element_nullable=True,
    )


@pytest.mark.parametrize("unit", ["minute", "", "MS"])
def test_duration_rejects_unknown_units(unit: str) -> None:
    with pytest.raises(ValueError, match="Time unit"):
        DurationType(unit=unit)


def test_schema_resolves_nested_struct_path_and_propagates_nullability() -> None:
    schema = Schema(
        fields=(
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField(
                            "address",
                            StructType(
                                fields=(
                                    StructField(
                                        "city",
                                        StringType(),
                                        nullable=False,
                                    ),
                                )
                            ),
                            nullable=False,
                        ),
                    )
                ),
                nullable=True,
            ),
        )
    )

    resolved = schema.resolve_path("profile.address.city")

    assert resolved.name == "city"
    assert resolved.data_type == StringType()
    assert resolved.nullable is True


def test_schema_rejects_nested_access_through_map_type() -> None:
    schema = Schema(
        fields=(
            Field(
                "attributes",
                MapType(StringType(), StringType()),
            ),
        )
    )

    with pytest.raises(FieldNotFoundError):
        schema.resolve_path("attributes.country")
