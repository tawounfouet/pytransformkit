from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.aggregate import (
    AggregateExpression,
    AggregateFunction,
)
from pytransformkit.domain.expressions.dependencies import (
    ExpressionDependencyExtractor,
)
from pytransformkit.domain.expressions.fingerprint import canonical_expression
from pytransformkit.domain.expressions.typing import (
    AggregateExpressionTypeResolver,
    ExpressionTypeResolver,
)
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.functions import (
    col,
    count,
    count_distinct,
    max,
    mean,
    min,
    sum,
)


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def test_aggregate_dsl_builds_portable_expression_nodes() -> None:
    expression = count_distinct(col("customer_id"))

    assert isinstance(expression, AggregateExpression)
    assert expression.function is AggregateFunction.COUNT_DISTINCT
    assert expression.argument is not None


def test_count_without_argument_represents_row_count() -> None:
    expression = count()

    assert expression.function is AggregateFunction.COUNT
    assert expression.argument is None


@pytest.mark.parametrize(
    ("expression", "expected_type", "nullable"),
    [
        (count(), IntegerType(bits=64), False),
        (count(col("amount")), IntegerType(bits=64), False),
        (count_distinct(col("status")), IntegerType(bits=64), False),
        (sum(col("customer_id")), IntegerType(bits=64), True),
        (sum(col("amount")), FloatType(bits=64), True),
        (min(col("status")), StringType(), True),
        (max(col("status")), StringType(), True),
        (mean(col("customer_id")), FloatType(bits=64), True),
    ],
)
def test_aggregate_type_inference(
    schema: Schema,
    expression: AggregateExpression,
    expected_type: object,
    nullable: bool,
) -> None:
    resolved = AggregateExpressionTypeResolver().resolve(
        expression,
        schema,
    )

    assert resolved.data_type == expected_type
    assert resolved.nullable is nullable


def test_sum_rejects_non_numeric_argument(schema: Schema) -> None:
    with pytest.raises(ExpressionTypeError, match="numeric"):
        AggregateExpressionTypeResolver().resolve(
            sum(col("status")),
            schema,
        )


def test_mean_rejects_non_numeric_argument(schema: Schema) -> None:
    with pytest.raises(ExpressionTypeError, match="numeric"):
        AggregateExpressionTypeResolver().resolve(
            mean(col("status")),
            schema,
        )


def test_row_expression_context_rejects_aggregate_expression(
    schema: Schema,
) -> None:
    with pytest.raises(ExpressionTypeError, match="only valid"):
        ExpressionTypeResolver().resolve(
            sum(col("amount")),
            schema,
        )


def test_nested_aggregate_is_rejected(schema: Schema) -> None:
    with pytest.raises(ExpressionTypeError, match="only valid"):
        AggregateExpressionTypeResolver().resolve(
            sum(count(col("amount"))),
            schema,
        )


def test_aggregate_dependencies_are_row_dependencies() -> None:
    dependencies = ExpressionDependencyExtractor().extract(
        sum(col("amount") + col("customer_id"))
    )

    assert {str(path) for path in dependencies} == {
        "amount",
        "customer_id",
    }


def test_aggregate_fingerprint_is_canonical() -> None:
    assert canonical_expression(count()) == "aggregate:count:(*)"
    assert canonical_expression(sum(col("amount"))).startswith("aggregate:sum:(column:")
