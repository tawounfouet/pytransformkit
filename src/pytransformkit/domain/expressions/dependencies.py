"""Logical field dependency extraction from Expressions."""

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.aggregate import AggregateExpression
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
from pytransformkit.domain.expressions.window import WindowExpression
from pytransformkit.errors.expression import ExpressionError


class ExpressionDependencyExtractor:
    """Extract logical input FieldPaths referenced by an Expression."""

    def extract(
        self,
        expression: Expression,
    ) -> frozenset[FieldPath]:
        if isinstance(expression, AggregateExpression):
            if expression.argument is None:
                return frozenset()
            return self.extract(expression.argument)

        if isinstance(expression, WindowExpression):
            dependencies = frozenset(expression.spec.partition_keys)
            dependencies = dependencies | frozenset(
                key.field for key in expression.spec.order_keys
            )
            if expression.argument is not None:
                dependencies = dependencies | self.extract(expression.argument)
            if expression.default is not None:
                dependencies = dependencies | self.extract(expression.default)
            return dependencies

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
            function_dependencies: frozenset[FieldPath] = frozenset()
            for argument in expression.arguments:
                function_dependencies = function_dependencies | self.extract(argument)
            return function_dependencies

        raise ExpressionError(
            f"Unsupported Expression node {type(expression).__name__!r}."
        )
