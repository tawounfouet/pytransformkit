from __future__ import annotations

from pathlib import Path

from pytransformkit import ResourceReference
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.functions import col
from pytransformkit.serialization import (
    ExpressionCodec,
    ResourceReferenceCodec,
    SchemaCodec,
)

_FIXTURES = Path(__file__).parents[2] / "fixtures" / "wire"


def _schema() -> Schema:
    return Schema(
        fields=(
            Field(
                "customer_id",
                IntegerType(),
                nullable=False,
            ),
            Field(
                "status",
                StringType(),
                description="Customer status",
            ),
        )
    )


def test_resource_reference_v1_matches_exact_golden_bytes() -> None:
    value = ResourceReference(
        scheme="file",
        locator="data/orders.parquet",
        media_type="application/vnd.apache.parquet",
    )
    expected = (_FIXTURES / "resource_reference_v1.json").read_bytes()

    assert ResourceReferenceCodec().to_bytes(value) + b"\n" == expected
    assert ResourceReferenceCodec().from_json(expected) == value


def test_schema_v1_matches_exact_golden_bytes() -> None:
    expected = (_FIXTURES / "schema_v1.json").read_bytes()

    assert SchemaCodec().to_bytes(_schema()) + b"\n" == expected
    assert SchemaCodec().from_json(expected) == _schema()


def test_expression_v1_matches_exact_golden_bytes() -> None:
    expression = col("amount") > 100
    expected = (_FIXTURES / "expression_v1.json").read_bytes()

    assert ExpressionCodec().to_bytes(expression) + b"\n" == expected

    decoded = ExpressionCodec().from_json(expected)
    assert decoded.structurally_equals(expression)
    assert ExpressionCodec().fingerprint(decoded) == expression.fingerprint()
