"""Base logical Expression API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytransformkit.errors.expression import InvalidBooleanUsageError

if TYPE_CHECKING:
    from pytransformkit.domain.expressions.operators import BinaryOperator


class Expression:
    """Immutable logical expression node base."""

    __slots__ = ()

    def __bool__(self) -> bool:
        raise InvalidBooleanUsageError()

    def __eq__(self, other: object) -> Expression:  # type: ignore[override]
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.EQ, other)

    def __ne__(self, other: object) -> Expression:  # type: ignore[override]
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.NE, other)

    def __lt__(self, other: object) -> Expression:  # type: ignore[override]
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.LT, other)

    def __le__(self, other: object) -> Expression:  # type: ignore[override]
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.LE, other)

    def __gt__(self, other: object) -> Expression:  # type: ignore[override]
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.GT, other)

    def __ge__(self, other: object) -> Expression:  # type: ignore[override]
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.GE, other)

    def __add__(self, other: object) -> Expression:
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.ADD, other)

    def __sub__(self, other: object) -> Expression:
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.SUB, other)

    def __mul__(self, other: object) -> Expression:
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.MUL, other)

    def __truediv__(self, other: object) -> Expression:
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.DIV, other)

    def __and__(self, other: object) -> Expression:
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.AND, other)

    def __or__(self, other: object) -> Expression:
        from pytransformkit.domain.expressions.operators import BinaryOperator

        return self._binary(BinaryOperator.OR, other)

    def __invert__(self) -> Expression:
        from pytransformkit.domain.expressions.operators import UnaryOperator
        from pytransformkit.domain.expressions.unary import UnaryExpression

        return UnaryExpression(UnaryOperator.NOT, self)

    def __neg__(self) -> Expression:
        from pytransformkit.domain.expressions.operators import UnaryOperator
        from pytransformkit.domain.expressions.unary import UnaryExpression

        return UnaryExpression(UnaryOperator.NEGATE, self)

    def is_null(self) -> Expression:
        from pytransformkit.domain.expressions.predicates import IsNullExpression

        return IsNullExpression(self)

    def is_not_null(self) -> Expression:
        from pytransformkit.domain.expressions.predicates import IsNotNullExpression

        return IsNotNullExpression(self)

    def structurally_equals(self, other: Expression) -> bool:
        from pytransformkit.domain.expressions.fingerprint import expression_fingerprint

        return expression_fingerprint(self) == expression_fingerprint(other)

    def _binary(self, operator: BinaryOperator, other: object) -> Expression:
        from pytransformkit.domain.expressions.binary import BinaryExpression

        return BinaryExpression(self, operator, ensure_expression(other))


def ensure_expression(value: object) -> Expression:
    """Coerce a Python scalar to a logical Literal when needed."""
    if isinstance(value, Expression):
        return value

    from pytransformkit.domain.expressions.literals import Literal

    return Literal(value=value)
