"""Compilation of logical Expressions to PyArrow compute expressions."""

from __future__ import annotations

from typing import Any

import pyarrow as pa
import pyarrow.compute as pc

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


class PyArrowExpressionCompiler:
    """Compile portable Expressions to Arrow arrays/scalars."""

    def compile(self, expression: Expression, table: pa.Table) -> Any:
        if isinstance(expression, ColumnReference):
            return _column_reference(table, expression)

        if isinstance(expression, Literal):
            return pa.scalar(expression.value)

        if isinstance(expression, BinaryExpression):
            left = self.compile(expression.left, table)
            right = self.compile(expression.right, table)
            return _binary(expression.operator, left, right)

        if isinstance(expression, UnaryExpression):
            operand = self.compile(expression.operand, table)
            if expression.operator is UnaryOperator.NOT:
                return pc.invert(operand)
            if expression.operator is UnaryOperator.NEGATE:
                return pc.negate(operand)
            raise AdapterError(
                f"Unsupported unary operator {expression.operator.value!r}."
            )

        if isinstance(expression, IsNullExpression):
            return pc.is_null(self.compile(expression.operand, table))

        if isinstance(expression, IsNotNullExpression):
            return pc.invert(pc.is_null(self.compile(expression.operand, table)))

        if isinstance(expression, FunctionCall):
            return self._compile_function(expression, table)

        raise AdapterError(
            f"Unsupported Arrow Expression node {type(expression).__name__!r}."
        )

    def _compile_function(
        self,
        expression: FunctionCall,
        table: pa.Table,
    ) -> Any:
        name = expression.function.value
        arguments = tuple(
            self.compile(argument, table) for argument in expression.arguments
        )

        if name == "core.lower":
            return pc.utf8_lower(arguments[0])
        if name == "core.upper":
            return pc.utf8_upper(arguments[0])
        if name == "core.trim":
            return pc.utf8_trim_whitespace(arguments[0])
        if name == "core.concat":
            return pc.binary_join_element_wise(*arguments, pa.scalar(""))

        raise AdapterError(f"PyArrow does not compile logical function {name!r}.")


def _column_reference(
    table: pa.Table,
    expression: ColumnReference,
) -> Any:
    parts = expression.path.parts
    value: Any = table.column(parts[0])
    for part in parts[1:]:
        value = pc.struct_field(value, part)
    return value


def _binary(operator: BinaryOperator, left: Any, right: Any) -> Any:
    functions = {
        BinaryOperator.EQ: pc.equal,
        BinaryOperator.NE: pc.not_equal,
        BinaryOperator.LT: pc.less,
        BinaryOperator.LE: pc.less_equal,
        BinaryOperator.GT: pc.greater,
        BinaryOperator.GE: pc.greater_equal,
        BinaryOperator.ADD: pc.add,
        BinaryOperator.SUB: pc.subtract,
        BinaryOperator.MUL: pc.multiply,
        BinaryOperator.DIV: pc.divide,
        BinaryOperator.AND: pc.and_kleene,
        BinaryOperator.OR: pc.or_kleene,
    }
    try:
        function = functions[operator]
    except KeyError as error:
        raise AdapterError(
            f"Unsupported binary operator {operator.value!r}."
        ) from error
    return function(left, right)
