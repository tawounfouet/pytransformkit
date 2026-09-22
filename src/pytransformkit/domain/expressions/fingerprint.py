"""Canonical structural fingerprints for logical Expressions."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal

from pytransformkit.domain.data.data_types import DataType
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
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.errors.expression import ExpressionError


def expression_fingerprint(expression: Expression) -> Fingerprint:
    canonical = canonical_expression(expression)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Fingerprint("sha256", digest)


def canonical_expression(expression: Expression) -> str:
    if isinstance(expression, ColumnReference):
        return f"column:{_quoted(str(expression.path))}"

    if isinstance(expression, Literal):
        return (
            "literal:"
            f"{_data_type_token(expression.data_type)}:"
            f"{_literal_token(expression.value)}"
        )

    if isinstance(expression, BinaryExpression):
        return (
            f"binary:{expression.operator.value}:("
            f"{canonical_expression(expression.left)},"
            f"{canonical_expression(expression.right)})"
        )

    if isinstance(expression, UnaryExpression):
        return (
            f"unary:{expression.operator.value}:("
            f"{canonical_expression(expression.operand)})"
        )

    if isinstance(expression, IsNullExpression):
        return f"is_null:({canonical_expression(expression.operand)})"

    if isinstance(expression, IsNotNullExpression):
        return f"is_not_null:({canonical_expression(expression.operand)})"

    if isinstance(expression, FunctionCall):
        arguments = ",".join(
            canonical_expression(argument) for argument in expression.arguments
        )
        return f"function:{_quoted(expression.function.value)}:({arguments})"

    raise ExpressionError(f"Unsupported Expression node {type(expression).__name__!r}.")


def _quoted(value: str) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _data_type_token(data_type: DataType | None) -> str:
    if data_type is None:
        return "inferred"
    return _quoted(repr(data_type))


def _literal_token(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool:true" if value else "bool:false"
    if isinstance(value, int):
        return f"int:{value}"
    if isinstance(value, float):
        return f"float:{value.hex()}"
    if isinstance(value, str):
        return f"string:{_quoted(value)}"
    if isinstance(value, Decimal):
        return f"decimal:{_quoted(str(value))}"
    if isinstance(value, datetime):
        return f"datetime:{_quoted(value.isoformat())}"
    if isinstance(value, date):
        return f"date:{_quoted(value.isoformat())}"

    raise ExpressionError(
        f"Literal value {type(value).__name__!r} "
        "does not have a canonical representation."
    )
