"""Special logical predicate Expressions."""

from dataclasses import dataclass

from pytransformkit.domain.expressions.base import Expression


@dataclass(frozen=True, slots=True, eq=False)
class IsNullExpression(Expression):
    operand: Expression

    def __post_init__(self) -> None:
        if not isinstance(self.operand, Expression):
            raise TypeError("IS NULL operand must be an Expression.")


@dataclass(frozen=True, slots=True, eq=False)
class IsNotNullExpression(Expression):
    operand: Expression

    def __post_init__(self) -> None:
        if not isinstance(self.operand, Expression):
            raise TypeError("IS NOT NULL operand must be an Expression.")
