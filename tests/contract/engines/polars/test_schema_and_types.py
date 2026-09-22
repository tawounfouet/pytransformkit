# ruff: noqa: E402

from __future__ import annotations

import pytest

pl = pytest.importorskip("polars")

from pytransformkit.domain.data.data_types import (
    BooleanType,
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
)
from pytransformkit.infrastructure.engines.polars import (
    PolarsSchemaInspector,
    PolarsTypeMapper,
)


def test_type_mapper_maps_logical_types_to_polars_dtypes() -> None:
    mapper = PolarsTypeMapper()

    assert mapper.to_native(StringType()) == pl.String
    assert mapper.to_native(BooleanType()) == pl.Boolean
    assert mapper.to_native(IntegerType(bits=32)) == pl.Int32
    assert mapper.to_native(IntegerType(bits=16, signed=False)) == pl.UInt16
    assert mapper.to_native(FloatType(bits=64)) == pl.Float64
    assert mapper.to_native(DecimalType(18, 2)) == pl.Decimal(18, 2)
    assert mapper.to_native(TimestampType()) == pl.Datetime("us")


def test_type_mapper_round_trips_native_primitives() -> None:
    mapper = PolarsTypeMapper()

    assert mapper.from_native(pl.String) == StringType()
    assert mapper.from_native(pl.Int64) == IntegerType()
    assert mapper.from_native(pl.UInt32) == IntegerType(
        bits=32,
        signed=False,
    )
    assert mapper.from_native(pl.Float32) == FloatType(bits=32)


def test_schema_inspector_handles_eager_dataframe() -> None:
    frame = pl.DataFrame(
        {
            "customer_id": [1, 2],
            "email": ["a@example.com", "b@example.com"],
        },
        schema={
            "customer_id": pl.Int64,
            "email": pl.String,
        },
    )

    schema = PolarsSchemaInspector().inspect(frame)

    assert schema.names() == ("customer_id", "email")
    assert schema.field("customer_id").data_type == IntegerType()
    assert schema.field("email").data_type == StringType()
    assert schema.field("email").nullable is True


def test_schema_inspector_reads_lazy_schema_without_collecting() -> None:
    lazy = pl.DataFrame(
        {
            "customer_id": [1, 2],
            "email": ["a", "b"],
        }
    ).lazy()

    schema = PolarsSchemaInspector().inspect(lazy)

    assert schema.names() == ("customer_id", "email")
    assert schema.field("customer_id").data_type == IntegerType()
