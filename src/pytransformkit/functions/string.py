"""Portable string Expression functions."""

from pytransformkit.domain.expressions.base import Expression, ensure_expression
from pytransformkit.domain.expressions.functions import FunctionCall, FunctionIdentifier

LOWER = FunctionIdentifier("core.lower")
UPPER = FunctionIdentifier("core.upper")
TRIM = FunctionIdentifier("core.trim")
CONCAT = FunctionIdentifier("core.concat")


def lower(value: object) -> Expression:
    return FunctionCall(LOWER, (ensure_expression(value),))


def upper(value: object) -> Expression:
    return FunctionCall(UPPER, (ensure_expression(value),))


def trim(value: object) -> Expression:
    return FunctionCall(TRIM, (ensure_expression(value),))


def concat(*values: object) -> Expression:
    if not values:
        raise ValueError("concat requires at least one value.")
    return FunctionCall(
        CONCAT,
        tuple(ensure_expression(value) for value in values),
    )
