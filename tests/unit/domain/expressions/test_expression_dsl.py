from __future__ import annotations

from collections.abc import Callable

import pytest

from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.functions import FunctionCall
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import (
    BinaryOperator,
    UnaryOperator,
)
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.errors.expression import InvalidBooleanUsageError
from pytransformkit.functions import col, concat, lit, lower, trim, upper


def test_col_builds_column_reference() -> None:
    expression = col("customer.address.city")

    assert isinstance(expression, ColumnReference)
    assert str(expression.path) == "customer.address.city"


def test_lit_builds_literal_without_column_ambiguity() -> None:
    expression = lit("email")

    assert isinstance(expression, Literal)
    assert expression.value == "email"


def test_python_value_is_coerced_to_literal_in_comparison() -> None:
    expression = col("amount") > 0

    assert isinstance(expression, BinaryExpression)
    assert expression.operator is BinaryOperator.GT
    assert isinstance(expression.left, ColumnReference)
    assert isinstance(expression.right, Literal)
    assert expression.right.value == 0


def test_boolean_operators_build_expression_tree() -> None:
    expression = (col("amount") > 0) & (col("status") == "ACTIVE")

    assert isinstance(expression, BinaryExpression)
    assert expression.operator is BinaryOperator.AND
    assert isinstance(expression.left, BinaryExpression)
    assert isinstance(expression.right, BinaryExpression)


def test_not_builds_unary_expression() -> None:
    expression = ~col("active")

    assert isinstance(expression, UnaryExpression)
    assert expression.operator is UnaryOperator.NOT


def test_python_bool_coercion_is_rejected() -> None:
    expression = col("amount") > 0

    with pytest.raises(InvalidBooleanUsageError) as error:
        bool(expression)

    assert str(error.value.code) == "PTK-EXPR-002"


def test_null_predicates_are_explicit_nodes() -> None:
    is_null = col("email").is_null()
    is_not_null = col("email").is_not_null()

    assert isinstance(is_null, IsNullExpression)
    assert isinstance(is_not_null, IsNotNullExpression)


@pytest.mark.parametrize(
    ("builder", "function_name"),
    [
        (lower, "core.lower"),
        (upper, "core.upper"),
        (trim, "core.trim"),
    ],
)
def test_string_functions_build_portable_function_calls(
    builder: Callable[[object], Expression],
    function_name: str,
) -> None:
    expression = builder(col("email"))

    assert isinstance(expression, FunctionCall)
    assert expression.function.value == function_name
    assert len(expression.arguments) == 1


def test_concat_builds_variadic_function_call() -> None:
    expression = concat(
        col("first_name"),
        " ",
        col("last_name"),
    )

    assert isinstance(expression, FunctionCall)
    assert expression.function.value == "core.concat"
    assert len(expression.arguments) == 3
    assert isinstance(expression.arguments[1], Literal)
    assert expression.arguments[1].value == " "


def test_concat_requires_at_least_one_value() -> None:
    with pytest.raises(ValueError, match="at least one"):
        concat()
