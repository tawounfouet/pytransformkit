"""Compilation of logical Expressions to Polars expressions."""

from typing import Any

import polars as pl

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
from pytransformkit.errors.engine import AdapterError


class PolarsExpressionCompiler:
    """Compile portable Expression trees to native Polars Expr objects."""

    def compile(
        self,
        expression: Expression,
        frame: Any | None = None,
    ) -> Any:
        del frame

        if isinstance(expression, ColumnReference):
            return pl.col(str(expression.path))

        if isinstance(expression, Literal):
            return pl.lit(expression.value)

        if isinstance(expression, BinaryExpression):
            return self._compile_binary(expression)

        if isinstance(expression, UnaryExpression):
            operand = self.compile(expression.operand)
            if expression.operator is UnaryOperator.NOT:
                return ~operand
            if expression.operator is UnaryOperator.NEGATE:
                return -operand
            raise AdapterError(
                f"Unsupported unary operator {expression.operator.value!r}."
            )

        if isinstance(expression, IsNullExpression):
            return self.compile(expression.operand).is_null()

        if isinstance(expression, IsNotNullExpression):
            return self.compile(expression.operand).is_not_null()

        if isinstance(expression, FunctionCall):
            return self._compile_function(expression)

        raise AdapterError(
            f"Unsupported Expression node {type(expression).__name__!r}."
        )

    def _compile_binary(self, expression: BinaryExpression) -> Any:
        operator = expression.operator

        if (
            operator
            in {
                BinaryOperator.EQ,
                BinaryOperator.NE,
                BinaryOperator.LT,
                BinaryOperator.LE,
                BinaryOperator.GT,
                BinaryOperator.GE,
            }
            and (
                _is_null_literal(expression.left)
                or _is_null_literal(expression.right)
            )
        ):
            return pl.lit(None, dtype=pl.Boolean)

        left = self.compile(expression.left)
        right = self.compile(expression.right)

        if operator is BinaryOperator.EQ:
            return left == right
        if operator is BinaryOperator.NE:
            return left != right
        if operator is BinaryOperator.LT:
            return left < right
        if operator is BinaryOperator.LE:
            return left <= right
        if operator is BinaryOperator.GT:
            return left > right
        if operator is BinaryOperator.GE:
            return left >= right
        if operator is BinaryOperator.ADD:
            return left + right
        if operator is BinaryOperator.SUB:
            return left - right
        if operator is BinaryOperator.MUL:
            return left * right
        if operator is BinaryOperator.DIV:
            return left / right
        if operator is BinaryOperator.AND:
            return left & right
        if operator is BinaryOperator.OR:
            return left | right

        raise AdapterError(
            f"Unsupported binary operator {operator.value!r}."
        )

    def _compile_function(self, expression: FunctionCall) -> Any:
        name = expression.function.value
        arguments = tuple(
            self.compile(argument)
            for argument in expression.arguments
        )

        if name == "core.lower":
            return arguments[0].str.to_lowercase()
        if name == "core.upper":
            return arguments[0].str.to_uppercase()
        if name == "core.trim":
            return arguments[0].str.strip_chars()
        if name == "core.concat":
            return pl.concat_str(
                arguments,
                separator="",
                ignore_nulls=False,
            )

        raise AdapterError(
            f"Polars does not compile logical function {name!r}."
        )


def _is_null_literal(expression: Expression) -> bool:
    return isinstance(expression, Literal) and expression.value is None
