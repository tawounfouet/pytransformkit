# ruff: noqa: E402

from __future__ import annotations

import pytest

pa = pytest.importorskip("pyarrow")

from pytransformkit.domain.data.data_types import (
    DecimalType,
    DurationType,
    IntegerType,
    ListType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pytransformkit.infrastructure.engines.pyarrow import (
    PyArrowDatasetHandle,
    PyArrowSchemaInspector,
    PyArrowTypeMapper,
)


def test_type_mapper_qualifies_nested_decimal_and_temporal_types() -> None:
    mapper = PyArrowTypeMapper()
    nested = StructType(
        (
            StructField("name", StringType(), nullable=False),
            StructField(
                "scores",
                ListType(IntegerType(bits=32)),
                nullable=True,
            ),
        )
    )

    assert mapper.to_native(DecimalType(precision=18, scale=4)) == pa.decimal128(18, 4)
    assert mapper.to_native(TimestampType(unit="ms", timezone="UTC")) == pa.timestamp(
        "ms", tz="UTC"
    )
    assert mapper.to_native(DurationType(unit="us")) == pa.duration("us")
    assert mapper.from_native(mapper.to_native(nested)) == nested


def test_schema_inspector_preserves_arrow_nullability() -> None:
    table = pa.table(
        {
            "customer_id": pa.array([1, 2], type=pa.int64()),
            "email": pa.array(["a", "b"], type=pa.string()),
        },
        schema=pa.schema(
            [
                pa.field("customer_id", pa.int64(), nullable=False),
                pa.field("email", pa.string(), nullable=True),
            ]
        ),
    )

    schema = PyArrowSchemaInspector().inspect(table)

    assert schema.names() == ("customer_id", "email")
    assert schema.field("customer_id").data_type == IntegerType()
    assert schema.field("customer_id").nullable is False
    assert schema.field("email").data_type == StringType()
    assert schema.field("email").nullable is True


def test_handle_accepts_table_and_record_batch_without_combining_chunks() -> None:
    chunked = pa.chunked_array([[1, 2], [3, 4]], type=pa.int64())
    table = pa.table({"value": chunked})
    handle = PyArrowDatasetHandle(table)

    assert handle.table.column("value").num_chunks == 2

    batch = pa.record_batch([pa.array([1, 2])], names=["value"])
    batch_handle = PyArrowDatasetHandle(batch)

    assert batch_handle.table.to_pydict() == {"value": [1, 2]}
