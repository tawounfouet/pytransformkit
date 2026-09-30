from __future__ import annotations

from pytransformkit.domain.data.data_types import (
    DecimalType,
    ListType,
    MapType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.serialization import DataTypeCodec, FieldCodec, SchemaCodec


def test_nested_data_type_round_trip_is_exact() -> None:
    data_type = StructType(
        fields=(
            StructField(
                "amounts",
                ListType(DecimalType(precision=18, scale=2)),
                nullable=False,
            ),
            StructField(
                "labels",
                MapType(StringType(), StringType()),
            ),
            StructField(
                "event_at",
                TimestampType(unit="us", timezone="UTC"),
            ),
        )
    )

    codec = DataTypeCodec()
    encoded = codec.to_json(data_type)

    assert codec.from_json(encoded) == data_type
    assert codec.to_json(codec.from_json(encoded)) == encoded


def test_field_and_schema_codecs_preserve_order_and_nullability() -> None:
    field = Field(
        "customer_id",
        StringType(),
        nullable=False,
        description="Stable customer identity",
    )
    schema = Schema(
        fields=(
            field,
            Field("country", StringType()),
        )
    )

    assert FieldCodec().from_json(FieldCodec().to_json(field)) == field
    decoded = SchemaCodec().from_json(SchemaCodec().to_json(schema))

    assert decoded == schema
    assert decoded.names() == ("customer_id", "country")
    assert decoded.field("customer_id").nullable is False
