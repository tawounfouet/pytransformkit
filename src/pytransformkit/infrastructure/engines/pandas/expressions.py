"""Compilation of logical Expressions to Pandas values."""

from typing import Any

import pandas as pd

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


class PandasExpressionCompiler:
    """Compile portable Expression trees to Pandas Series/scalars."""

    def compile(
        self,
        expression: Expression,
        dataframe: Any,
    ) -> Any:
        if isinstance(expression, ColumnReference):
            return dataframe[str(expression.path)]

        if isinstance(expression, Literal):
            return expression.value

        if isinstance(expression, BinaryExpression):
            return self._compile_binary(expression, dataframe)

        if isinstance(expression, UnaryExpression):
            operand = self.compile(expression.operand, dataframe)
            if expression.operator is UnaryOperator.NOT:
                return ~operand
            if expression.operator is UnaryOperator.NEGATE:
                return -operand
            raise AdapterError(
                f"Unsupported unary operator {expression.operator.value!r}."
            )

        if isinstance(expression, IsNullExpression):
            return self._is_null(
                self.compile(expression.operand, dataframe)
            )

        if isinstance(expression, IsNotNullExpression):
            return ~self._is_null(
                self.compile(expression.operand, dataframe)
            )

        if isinstance(expression, FunctionCall):
            return self._compile_function(expression, dataframe)

        raise AdapterError(
            f"Unsupported Expression node {type(expression).__name__!r}."
        )

    def _compile_binary(
        self,
        expression: BinaryExpression,
        dataframe: Any,
    ) -> Any:
        left = self.compile(expression.left, dataframe)
        right = self.compile(expression.right, dataframe)
        operator = expression.operator

        if (
            (_is_null_scalar(left) or _is_null_scalar(right))
            and operator
            in {
                BinaryOperator.EQ,
                BinaryOperator.NE,
                BinaryOperator.LT,
                BinaryOperator.LE,
                BinaryOperator.GT,
                BinaryOperator.GE,
            }
        ):
            return pd.Series(
                pd.NA,
                index=dataframe.index,
                dtype="boolean",
            )

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

    def _compile_function(
        self,
        expression: FunctionCall,
        dataframe: Any,
    ) -> Any:
        name = expression.function.value
        arguments = tuple(
            self.compile(argument, dataframe)
            for argument in expression.arguments
        )

        if name == "core.lower":
            return _string_unary(arguments[0], "lower")
        if name == "core.upper":
            return _string_unary(arguments[0], "upper")
        if name == "core.trim":
            return _string_unary(arguments[0], "strip")
        if name == "core.concat":
            return _concat(arguments)

        raise AdapterError(
            f"Pandas does not compile logical function {name!r}."
        )

    @staticmethod
    def _is_null(value: Any) -> Any:
        if isinstance(value, pd.Series):
            return value.isna()
        return pd.isna(value)


def _is_null_scalar(value: Any) -> bool:
    if isinstance(value, pd.Series):
        return False
    return value is None or value is pd.NA


def _string_unary(value: Any, method: str) -> Any:
    if isinstance(value, pd.Series):
        accessor = value.astype("string").str
        return getattr(accessor, method)()

    if _is_null_scalar(value):
        return pd.NA

    return getattr(str(value), method)()


def _concat(values: tuple[Any, ...]) -> Any:
    if not values:
        raise AdapterError("Pandas concat requires at least one value.")

    normalized = tuple(_as_string(value) for value in values)
    result = normalized[0]

    for value in normalized[1:]:
        result = result + value

    return result


def _as_string(value: Any) -> Any:
    if isinstance(value, pd.Series):
        return value.astype("string")
    if _is_null_scalar(value):
        return pd.NA
    return str(value)
