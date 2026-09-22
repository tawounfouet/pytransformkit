"""Binary logical Expressions."""

from dataclasses import dataclass

from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.operators import BinaryOperator


@dataclass(frozen=True, slots=True, eq=False)
class BinaryExpression(Expression):
    left: Expression
    operator: BinaryOperator
    right: Expression

    def __post_init__(self) -> None:
        if not isinstance(self.left, Expression):
            raise TypeError("BinaryExpression left operand must be an Expression.")
        if not isinstance(self.operator, BinaryOperator):
            raise TypeError("BinaryExpression operator must be a BinaryOperator.")
        if not isinstance(self.right, Expression):
            raise TypeError("BinaryExpression right operand must be an Expression.")
