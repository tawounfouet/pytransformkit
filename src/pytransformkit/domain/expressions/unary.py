"""Unary logical Expressions."""

from dataclasses import dataclass

from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.operators import UnaryOperator


@dataclass(frozen=True, slots=True, eq=False)
class UnaryExpression(Expression):
    operator: UnaryOperator
    operand: Expression

    def __post_init__(self) -> None:
        if not isinstance(self.operator, UnaryOperator):
            raise TypeError("UnaryExpression operator must be a UnaryOperator.")
        if not isinstance(self.operand, Expression):
            raise TypeError("UnaryExpression operand must be an Expression.")
