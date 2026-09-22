from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from pytransformkit.domain.data.data_types import (
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
    UnknownType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.typing import ExpressionTypeResolver
from pytransformkit.errors.expression import (
    ExpressionTypeError,
    FunctionNotFoundError,
)
from pytransformkit.errors.schema import FieldNotFoundError
from pytransformkit.functions import col, concat, lit, lower


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
            Field("email", StringType(), nullable=True),
            Field("active", BooleanType(), nullable=False),
        )
    )


def test_column_reference_resolves_schema_type(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(col("customer_id"), schema)

    assert resolved.data_type == IntegerType()
    assert resolved.nullable is False


def test_missing_column_raises_schema_error(schema: Schema) -> None:
    with pytest.raises(FieldNotFoundError):
        ExpressionTypeResolver().resolve(col("missing"), schema)


@pytest.mark.parametrize(
    ("value", "expected_type", "nullable"),
    [
        (None, UnknownType(), True),
        (True, BooleanType(), False),
        (1, IntegerType(), False),
        (1.5, FloatType(), False),
        ("x", StringType(), False),
        (Decimal("12.30"), DecimalType(4, 2), False),
        (date(2026, 9, 22), DateType(), False),
        (
            datetime(2026, 9, 22, 12, tzinfo=UTC),
            TimestampType(timezone="UTC"),
            False,
        ),
    ],
)
def test_literal_type_inference(
    schema: Schema,
    value: object,
    expected_type: DataType,
    nullable: bool,
) -> None:
    resolved = ExpressionTypeResolver().resolve(lit(value), schema)

    assert resolved.data_type == expected_type
    assert resolved.nullable is nullable


def test_comparison_resolves_boolean_and_nullability(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        col("amount") > 0,
        schema,
    )

    assert resolved.data_type == BooleanType()
    assert resolved.nullable is True


def test_boolean_logic_requires_boolean_inputs(schema: Schema) -> None:
    with pytest.raises(ExpressionTypeError, match="Boolean"):
        ExpressionTypeResolver().resolve(
            (col("amount") > 0) & col("email"),
            schema,
        )


def test_integer_arithmetic_preserves_integer_family(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        col("customer_id") + 1,
        schema,
    )

    assert resolved.data_type == IntegerType()
    assert resolved.nullable is False


def test_mixed_numeric_arithmetic_promotes_to_float(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        col("customer_id") + col("amount"),
        schema,
    )

    assert resolved.data_type == FloatType()
    assert resolved.nullable is True


def test_integer_division_resolves_float(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        col("customer_id") / 2,
        schema,
    )

    assert resolved.data_type == FloatType()
    assert resolved.nullable is False


def test_string_function_preserves_nullable_semantics(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        lower(col("email")),
        schema,
    )

    assert resolved.data_type == StringType()
    assert resolved.nullable is True


def test_string_function_rejects_non_string(schema: Schema) -> None:
    with pytest.raises(ExpressionTypeError, match="String"):
        ExpressionTypeResolver().resolve(
            lower(col("customer_id")),
            schema,
        )


def test_concat_combines_string_nullability(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        concat("ID:", col("email")),
        schema,
    )

    assert resolved.data_type == StringType()
    assert resolved.nullable is True


def test_null_predicate_is_non_nullable_boolean(schema: Schema) -> None:
    resolved = ExpressionTypeResolver().resolve(
        col("email").is_null(),
        schema,
    )

    assert resolved.data_type == BooleanType()
    assert resolved.nullable is False


def test_unknown_function_raises_typed_error(schema: Schema) -> None:
    from pytransformkit.domain.expressions.functions import (
        FunctionCall,
        FunctionIdentifier,
    )

    expression = FunctionCall(
        function=FunctionIdentifier("plugin.missing"),
        arguments=(col("email"),),
    )

    with pytest.raises(FunctionNotFoundError) as error:
        ExpressionTypeResolver().resolve(expression, schema)

    assert error.value.function_name == "plugin.missing"
    assert str(error.value.code) == "PTK-EXPR-003"
