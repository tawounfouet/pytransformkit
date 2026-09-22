"""Logical field dependency extraction from Expressions."""

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.functions import FunctionCall
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.errors.expression import ExpressionError


class ExpressionDependencyExtractor:
    """Extract logical input FieldPaths referenced by an Expression."""

    def extract(
        self,
        expression: Expression,
    ) -> frozenset[FieldPath]:
        if isinstance(expression, ColumnReference):
            return frozenset({expression.path})

        if isinstance(expression, Literal):
            return frozenset()

        if isinstance(expression, BinaryExpression):
            return self.extract(expression.left) | self.extract(expression.right)

        if isinstance(expression, UnaryExpression):
            return self.extract(expression.operand)

        if isinstance(expression, (IsNullExpression, IsNotNullExpression)):
            return self.extract(expression.operand)

        if isinstance(expression, FunctionCall):
            dependencies: frozenset[FieldPath] = frozenset()
            for argument in expression.arguments:
                dependencies = dependencies | self.extract(argument)
            return dependencies

        raise ExpressionError(
            f"Unsupported Expression node {type(expression).__name__!r}."
        )
