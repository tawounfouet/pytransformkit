"""Static logical Expression type resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from pytransformkit.domain.data.data_types import (
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
    UnknownType,
)
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.functions import FunctionCall
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import BinaryOperator, UnaryOperator
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.errors.expression import (
    ExpressionTypeError,
    FunctionNotFoundError,
)


@dataclass(frozen=True, slots=True)
class ExpressionType:
    """Resolved logical type and nullability of an Expression."""

    data_type: DataType
    nullable: bool


class ExpressionTypeResolver:
    """Resolve Expression types from an input logical Schema."""

    _COMPARISON_OPERATORS = frozenset(
        {
            BinaryOperator.EQ,
            BinaryOperator.NE,
            BinaryOperator.LT,
            BinaryOperator.LE,
            BinaryOperator.GT,
            BinaryOperator.GE,
        }
    )
    _BOOLEAN_OPERATORS = frozenset(
        {
            BinaryOperator.AND,
            BinaryOperator.OR,
        }
    )
    _ARITHMETIC_OPERATORS = frozenset(
        {
            BinaryOperator.ADD,
            BinaryOperator.SUB,
            BinaryOperator.MUL,
            BinaryOperator.DIV,
        }
    )

    def resolve(
        self,
        expression: Expression,
        schema: Schema,
    ) -> ExpressionType:
        if isinstance(expression, ColumnReference):
            field = schema.field(str(expression.path))
            return ExpressionType(
                data_type=field.data_type,
                nullable=field.nullable,
            )

        if isinstance(expression, Literal):
            return self._resolve_literal(expression)

        if isinstance(expression, BinaryExpression):
            return self._resolve_binary(expression, schema)

        if isinstance(expression, UnaryExpression):
            return self._resolve_unary(expression, schema)

        if isinstance(expression, (IsNullExpression, IsNotNullExpression)):
            self.resolve(expression.operand, schema)
            return ExpressionType(BooleanType(), False)

        if isinstance(expression, FunctionCall):
            return self._resolve_function(expression, schema)

        raise ExpressionTypeError(
            f"Unsupported Expression node {type(expression).__name__!r}."
        )

    def _resolve_literal(self, literal: Literal) -> ExpressionType:
        if literal.data_type is not None:
            return ExpressionType(
                data_type=literal.data_type,
                nullable=literal.value is None,
            )

        value = literal.value
        if value is None:
            return ExpressionType(UnknownType(), True)
        if isinstance(value, bool):
            return ExpressionType(BooleanType(), False)
        if isinstance(value, int):
            return ExpressionType(IntegerType(), False)
        if isinstance(value, float):
            return ExpressionType(FloatType(), False)
        if isinstance(value, str):
            return ExpressionType(StringType(), False)
        if isinstance(value, Decimal):
            return ExpressionType(_decimal_type(value), False)
        if isinstance(value, datetime):
            timezone = str(value.tzinfo) if value.tzinfo is not None else None
            return ExpressionType(
                TimestampType(timezone=timezone),
                False,
            )
        if isinstance(value, date):
            return ExpressionType(DateType(), False)

        raise ExpressionTypeError(
            "Cannot infer a logical DataType for literal "
            f"{type(value).__name__!r}."
        )

    def _resolve_binary(
        self,
        expression: BinaryExpression,
        schema: Schema,
    ) -> ExpressionType:
        left = self.resolve(expression.left, schema)
        right = self.resolve(expression.right, schema)
        nullable = left.nullable or right.nullable

        if expression.operator in self._COMPARISON_OPERATORS:
            return ExpressionType(BooleanType(), nullable)

        if expression.operator in self._BOOLEAN_OPERATORS:
            _require_boolean(left, "left")
            _require_boolean(right, "right")
            return ExpressionType(BooleanType(), nullable)

        if expression.operator in self._ARITHMETIC_OPERATORS:
            return ExpressionType(
                _resolve_numeric_result(
                    left.data_type,
                    right.data_type,
                    expression.operator,
                ),
                nullable,
            )

        raise ExpressionTypeError(
            f"Unsupported binary operator {expression.operator.value!r}."
        )

    def _resolve_unary(
        self,
        expression: UnaryExpression,
        schema: Schema,
    ) -> ExpressionType:
        operand = self.resolve(expression.operand, schema)

        if expression.operator is UnaryOperator.NOT:
            _require_boolean(operand, "operand")
            return ExpressionType(BooleanType(), operand.nullable)

        if expression.operator is UnaryOperator.NEGATE:
            if not isinstance(
                operand.data_type,
                (IntegerType, FloatType, DecimalType),
            ):
                raise ExpressionTypeError(
                    "Unary negation requires a numeric Expression."
                )
            return operand

        raise ExpressionTypeError(
            f"Unsupported unary operator {expression.operator.value!r}."
        )

    def _resolve_function(
        self,
        expression: FunctionCall,
        schema: Schema,
    ) -> ExpressionType:
        name = expression.function.value
        arguments = tuple(
            self.resolve(argument, schema)
            for argument in expression.arguments
        )

        if name in {"core.lower", "core.upper", "core.trim"}:
            if len(arguments) != 1:
                raise ExpressionTypeError(
                    f"{name} requires exactly one argument."
                )
            argument = arguments[0]
            if not isinstance(argument.data_type, StringType):
                raise ExpressionTypeError(
                    f"{name} requires a String Expression."
                )
            return ExpressionType(StringType(), argument.nullable)

        if name == "core.concat":
            if not arguments:
                raise ExpressionTypeError(
                    "core.concat requires at least one argument."
                )
            if any(
                not isinstance(argument.data_type, StringType)
                for argument in arguments
            ):
                raise ExpressionTypeError(
                    "core.concat requires only String Expressions."
                )
            return ExpressionType(
                StringType(),
                any(argument.nullable for argument in arguments),
            )

        raise FunctionNotFoundError(name)


def _require_boolean(
    expression_type: ExpressionType,
    side: str,
) -> None:
    if not isinstance(expression_type.data_type, BooleanType):
        raise ExpressionTypeError(
            f"Boolean operation requires a Boolean {side} Expression."
        )


def _resolve_numeric_result(
    left: DataType,
    right: DataType,
    operator: BinaryOperator,
) -> DataType:
    numeric_types = (IntegerType, FloatType, DecimalType)
    if not isinstance(left, numeric_types) or not isinstance(right, numeric_types):
        raise ExpressionTypeError(
            "Arithmetic operations require numeric Expressions."
        )

    if isinstance(left, DecimalType) or isinstance(right, DecimalType):
        raise ExpressionTypeError(
            "Decimal arithmetic promotion is not defined in the initial MVP."
        )

    if operator is BinaryOperator.DIV:
        return FloatType(bits=64)

    if isinstance(left, FloatType) or isinstance(right, FloatType):
        left_bits = left.bits if isinstance(left, FloatType) else 64
        right_bits = right.bits if isinstance(right, FloatType) else 64
        return FloatType(bits=max(left_bits, right_bits))

    if isinstance(left, IntegerType) and isinstance(right, IntegerType):
        return IntegerType(
            bits=max(left.bits, right.bits),
            signed=left.signed or right.signed,
        )

    raise ExpressionTypeError("Unable to resolve numeric result type.")


def _decimal_type(value: Decimal) -> DecimalType:
    _, digits, exponent = value.as_tuple()
    digits_count = max(len(digits), 1)

    if exponent >= 0:
        return DecimalType(
            precision=digits_count + exponent,
            scale=0,
        )

    scale = -exponent
    return DecimalType(
        precision=max(digits_count, scale),
        scale=scale,
    )
