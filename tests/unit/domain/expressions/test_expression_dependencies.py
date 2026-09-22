from __future__ import annotations

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.dependencies import (
    ExpressionDependencyExtractor,
)
from pytransformkit.functions import col, concat, lower


def test_dependency_extractor_collects_nested_expression_columns() -> None:
    expression = (
        (col("amount") > 0)
        & col("customer_id").is_not_null()
        & (lower(col("status")) == "active")
    )

    dependencies = ExpressionDependencyExtractor().extract(expression)

    assert dependencies == frozenset(
        {
            FieldPath.of("amount"),
            FieldPath.of("customer_id"),
            FieldPath.of("status"),
        }
    )


def test_literal_only_expression_has_no_dependencies() -> None:
    expression = concat("A", "B")

    assert ExpressionDependencyExtractor().extract(expression) == frozenset()
