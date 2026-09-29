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
            return _column_reference(expression)

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

        if operator in {
            BinaryOperator.EQ,
            BinaryOperator.NE,
            BinaryOperator.LT,
            BinaryOperator.LE,
            BinaryOperator.GT,
            BinaryOperator.GE,
        } and (_is_null_literal(expression.left) or _is_null_literal(expression.right)):
            anchor_expression = (
                expression.right
                if _is_null_literal(expression.left)
                else expression.left
            )
            anchor = self.compile(anchor_expression)
            row_anchor = anchor.is_null() | anchor.is_not_null()
            return row_anchor & pl.lit(None, dtype=pl.Boolean)

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

        raise AdapterError(f"Unsupported binary operator {operator.value!r}.")

    def _compile_function(self, expression: FunctionCall) -> Any:
        name = expression.function.value
        arguments = tuple(self.compile(argument) for argument in expression.arguments)

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
        if name == "core.temporal.year":
            return arguments[0].dt.year().cast(pl.Int32)
        if name == "core.temporal.month":
            return arguments[0].dt.month().cast(pl.Int32)
        if name == "core.temporal.day":
            return arguments[0].dt.day().cast(pl.Int32)
        if name == "core.temporal.hour":
            return arguments[0].dt.hour().cast(pl.Int32)
        if name == "core.temporal.minute":
            return arguments[0].dt.minute().cast(pl.Int32)
        if name == "core.temporal.second":
            return arguments[0].dt.second().cast(pl.Int32)
        if name == "core.temporal.to_date":
            return arguments[0].dt.date()
        if name == "core.temporal.normalize_timestamp":
            timezone = _literal_string(
                expression.arguments[1],
                "normalize_timestamp timezone",
            )
            unit = _literal_string(
                expression.arguments[2],
                "normalize_timestamp unit",
            )
            return (
                arguments[0]
                .dt.replace_time_zone(timezone)
                .cast(pl.Datetime(time_unit=unit, time_zone=timezone))
            )
        if name == "core.temporal.convert_timezone":
            timezone = _literal_string(
                expression.arguments[1],
                "convert_timezone timezone",
            )
            return arguments[0].dt.convert_time_zone(timezone)
        if name == "core.temporal.duration_between":
            unit = _literal_string(
                expression.arguments[2],
                "duration_between unit",
            )
            physical_unit = "us" if unit == "s" else unit
            return (arguments[1] - arguments[0]).cast(
                pl.Duration(time_unit=physical_unit)
            )

        raise AdapterError(f"Polars does not compile logical function {name!r}.")


def _column_reference(expression: ColumnReference) -> Any:
    parts = expression.path.parts
    value = pl.col(parts[0])
    for part in parts[1:]:
        value = value.struct.field(part)
    return value


def _literal_string(expression: Expression, label: str) -> str:
    if not isinstance(expression, Literal) or not isinstance(expression.value, str):
        raise AdapterError(f"{label} must be a string literal.")
    return expression.value


def _is_null_literal(expression: Expression) -> bool:
    return isinstance(expression, Literal) and expression.value is None
