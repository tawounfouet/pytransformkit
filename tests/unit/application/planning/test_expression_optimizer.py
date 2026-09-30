from __future__ import annotations

from hypothesis import given, strategies as st

from pytransformkit.application.planning.expression_optimizer import (
    BOOLEAN_SIMPLIFICATION_RULE,
    CONSTANT_FOLDING_RULE,
    ExpressionOptimizer,
)
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import BinaryOperator
from pytransformkit.functions import col, lit


def test_constant_folding_reduces_literal_arithmetic() -> None:
    expression = (col("amount") > (lit(1) + lit(2))) & lit(True)

    optimized = ExpressionOptimizer().optimize(expression)

    expected = col("amount") > 3
    assert optimized.expression.structurally_equals(expected)
    assert CONSTANT_FOLDING_RULE in optimized.applied_rules
    assert BOOLEAN_SIMPLIFICATION_RULE in optimized.applied_rules


def test_boolean_simplification_preserves_unknown_capable_operand() -> None:
    expression = lit(True) & col("is_active")

    optimized = ExpressionOptimizer().optimize(expression)

    assert optimized.expression.structurally_equals(col("is_active"))
    assert optimized.applied_rules == (BOOLEAN_SIMPLIFICATION_RULE,)


@given(st.integers(min_value=-10_000, max_value=10_000), st.integers(-10_000, 10_000))
def test_integer_addition_constant_folding_is_semantically_equivalent(
    left: int,
    right: int,
) -> None:
    expression = BinaryExpression(
        Literal(left),
        BinaryOperator.ADD,
        Literal(right),
    )

    optimized = ExpressionOptimizer().optimize(expression)

    assert isinstance(optimized.expression, Literal)
    assert optimized.expression.value == left + right


@given(st.booleans(), st.booleans())
def test_boolean_and_constant_folding_matches_python_truth_table(
    left: bool,
    right: bool,
) -> None:
    expression = BinaryExpression(
        Literal(left),
        BinaryOperator.AND,
        Literal(right),
    )

    optimized = ExpressionOptimizer().optimize(expression)

    assert isinstance(optimized.expression, Literal)
    assert optimized.expression.value is (left and right)
