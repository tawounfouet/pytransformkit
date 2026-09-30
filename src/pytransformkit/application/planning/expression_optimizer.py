"""Engine-neutral expression simplification used by the logical optimizer."""

from __future__ import annotations

import operator
from dataclasses import dataclass, replace
from decimal import Decimal

from pytransformkit.domain.expressions.aggregate import AggregateExpression
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.functions import FunctionCall
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import BinaryOperator, UnaryOperator
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.domain.expressions.window import WindowExpression

CONSTANT_FOLDING_RULE = "constant-folding"
BOOLEAN_SIMPLIFICATION_RULE = "boolean-simplification"


@dataclass(frozen=True, slots=True)
class ExpressionOptimization:
    """One optimized expression and the rules that changed it."""

    expression: Expression
    applied_rules: tuple[str, ...] = ()


class ExpressionOptimizer:
    """Perform conservative semantics-preserving expression rewrites."""

    def optimize(self, expression: Expression) -> ExpressionOptimization:
        if not isinstance(expression, Expression):
            raise TypeError("ExpressionOptimizer requires an Expression.")
        optimized, rules = self._visit(expression)
        return ExpressionOptimization(
            expression=optimized,
            applied_rules=_dedupe(rules),
        )

    def _visit(self, expression: Expression) -> tuple[Expression, tuple[str, ...]]:
        if isinstance(expression, BinaryExpression):
            left, left_rules = self._visit(expression.left)
            right, right_rules = self._visit(expression.right)
            binary_current = BinaryExpression(left, expression.operator, right)
            simplified, binary_rule = _simplify_binary(binary_current)
            binary_rules = left_rules + right_rules
            if binary_rule is not None:
                binary_rules += (binary_rule,)
            return simplified, binary_rules

        if isinstance(expression, UnaryExpression):
            operand, unary_rules = self._visit(expression.operand)
            unary_current = UnaryExpression(expression.operator, operand)
            simplified, unary_rule = _simplify_unary(unary_current)
            if unary_rule is not None:
                unary_rules += (unary_rule,)
            return simplified, unary_rules

        if isinstance(expression, IsNullExpression):
            operand, null_rules = self._visit(expression.operand)
            null_current = IsNullExpression(operand)
            if isinstance(operand, Literal):
                return Literal(operand.value is None), null_rules + (
                    CONSTANT_FOLDING_RULE,
                )
            return null_current, null_rules

        if isinstance(expression, IsNotNullExpression):
            operand, not_null_rules = self._visit(expression.operand)
            not_null_current = IsNotNullExpression(operand)
            if isinstance(operand, Literal):
                return Literal(operand.value is not None), not_null_rules + (
                    CONSTANT_FOLDING_RULE,
                )
            return not_null_current, not_null_rules

        if isinstance(expression, FunctionCall):
            arguments: list[Expression] = []
            function_rules: tuple[str, ...] = ()
            for argument in expression.arguments:
                optimized, argument_rules = self._visit(argument)
                arguments.append(optimized)
                function_rules += argument_rules
            return replace(expression, arguments=tuple(arguments)), function_rules

        if isinstance(expression, AggregateExpression):
            if expression.argument is None:
                return expression, ()
            aggregate_argument, aggregate_rules = self._visit(expression.argument)
            return replace(expression, argument=aggregate_argument), aggregate_rules

        if isinstance(expression, WindowExpression):
            window_rules: tuple[str, ...] = ()
            window_argument: Expression | None = expression.argument
            window_default: Expression | None = expression.default
            if window_argument is not None:
                optimized_argument, argument_rules = self._visit(window_argument)
                window_argument = optimized_argument
                window_rules += argument_rules
            if window_default is not None:
                optimized_default, default_rules = self._visit(window_default)
                window_default = optimized_default
                window_rules += default_rules
            return (
                replace(
                    expression,
                    argument=window_argument,
                    default=window_default,
                ),
                window_rules,
            )

        return expression, ()


def _simplify_binary(
    expression: BinaryExpression,
) -> tuple[Expression, str | None]:
    operator_id = expression.operator
    left = expression.left
    right = expression.right

    if operator_id is BinaryOperator.AND:
        if _literal_bool(left, True):
            return right, BOOLEAN_SIMPLIFICATION_RULE
        if _literal_bool(right, True):
            return left, BOOLEAN_SIMPLIFICATION_RULE
        if _literal_bool(left, False) or _literal_bool(right, False):
            return Literal(False), BOOLEAN_SIMPLIFICATION_RULE

    if operator_id is BinaryOperator.OR:
        if _literal_bool(left, False):
            return right, BOOLEAN_SIMPLIFICATION_RULE
        if _literal_bool(right, False):
            return left, BOOLEAN_SIMPLIFICATION_RULE
        if _literal_bool(left, True) or _literal_bool(right, True):
            return Literal(True), BOOLEAN_SIMPLIFICATION_RULE

    if not isinstance(left, Literal) or not isinstance(right, Literal):
        return expression, None
    if left.data_type is not None or right.data_type is not None:
        return expression, None
    if left.value is None or right.value is None:
        return expression, None
    if not _foldable_scalar(left.value) or not _foldable_scalar(right.value):
        return expression, None

    operation = _BINARY_OPERATIONS.get(operator_id)
    if operation is None:
        return expression, None

    try:
        result = operation(left.value, right.value)
    except (ArithmeticError, TypeError, ValueError):
        return expression, None

    if not _foldable_scalar(result):
        return expression, None
    return Literal(result), CONSTANT_FOLDING_RULE


def _simplify_unary(
    expression: UnaryExpression,
) -> tuple[Expression, str | None]:
    operand = expression.operand

    if (
        expression.operator is UnaryOperator.NOT
        and isinstance(operand, UnaryExpression)
        and operand.operator is UnaryOperator.NOT
    ):
        return operand.operand, BOOLEAN_SIMPLIFICATION_RULE

    if not isinstance(operand, Literal) or operand.data_type is not None:
        return expression, None

    if expression.operator is UnaryOperator.NOT and isinstance(operand.value, bool):
        return Literal(not operand.value), CONSTANT_FOLDING_RULE

    if (
        expression.operator is UnaryOperator.NEGATE
        and isinstance(operand.value, (int, float, Decimal))
        and not isinstance(operand.value, bool)
    ):
        return Literal(-operand.value), CONSTANT_FOLDING_RULE

    return expression, None


def _literal_bool(expression: Expression, expected: bool) -> bool:
    return (
        isinstance(expression, Literal)
        and isinstance(expression.value, bool)
        and expression.value is expected
    )


def _foldable_scalar(value: object) -> bool:
    return value is None or isinstance(value, (bool, int, float, str, Decimal))


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


_BINARY_OPERATIONS = {
    BinaryOperator.EQ: operator.eq,
    BinaryOperator.NE: operator.ne,
    BinaryOperator.LT: operator.lt,
    BinaryOperator.LE: operator.le,
    BinaryOperator.GT: operator.gt,
    BinaryOperator.GE: operator.ge,
    BinaryOperator.ADD: operator.add,
    BinaryOperator.SUB: operator.sub,
    BinaryOperator.MUL: operator.mul,
    BinaryOperator.DIV: operator.truediv,
}
