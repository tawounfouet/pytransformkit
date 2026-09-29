"""Portable temporal Expression functions."""

from pytransformkit.domain.expressions.base import Expression, ensure_expression
from pytransformkit.domain.expressions.functions import FunctionCall, FunctionIdentifier

YEAR = FunctionIdentifier("core.temporal.year")
MONTH = FunctionIdentifier("core.temporal.month")
DAY = FunctionIdentifier("core.temporal.day")
HOUR = FunctionIdentifier("core.temporal.hour")
MINUTE = FunctionIdentifier("core.temporal.minute")
SECOND = FunctionIdentifier("core.temporal.second")
TO_DATE = FunctionIdentifier("core.temporal.to_date")
NORMALIZE_TIMESTAMP = FunctionIdentifier("core.temporal.normalize_timestamp")
CONVERT_TIMEZONE = FunctionIdentifier("core.temporal.convert_timezone")
DURATION_BETWEEN = FunctionIdentifier("core.temporal.duration_between")


def year(value: object) -> Expression:
    return FunctionCall(YEAR, (ensure_expression(value),))


def month(value: object) -> Expression:
    return FunctionCall(MONTH, (ensure_expression(value),))


def day(value: object) -> Expression:
    return FunctionCall(DAY, (ensure_expression(value),))


def hour(value: object) -> Expression:
    return FunctionCall(HOUR, (ensure_expression(value),))


def minute(value: object) -> Expression:
    return FunctionCall(MINUTE, (ensure_expression(value),))


def second(value: object) -> Expression:
    return FunctionCall(SECOND, (ensure_expression(value),))


def to_date(value: object) -> Expression:
    return FunctionCall(TO_DATE, (ensure_expression(value),))


def normalize_timestamp(
    value: object,
    *,
    timezone: str = "UTC",
    unit: str = "us",
) -> Expression:
    if not timezone or not timezone.strip():
        raise ValueError("normalize_timestamp timezone must not be blank.")
    return FunctionCall(
        NORMALIZE_TIMESTAMP,
        (
            ensure_expression(value),
            ensure_expression(timezone),
            ensure_expression(unit),
        ),
    )


def convert_timezone(value: object, timezone: str) -> Expression:
    if not timezone or not timezone.strip():
        raise ValueError("convert_timezone timezone must not be blank.")
    return FunctionCall(
        CONVERT_TIMEZONE,
        (
            ensure_expression(value),
            ensure_expression(timezone),
        ),
    )


def duration_between(
    start: object,
    end: object,
    *,
    unit: str = "us",
) -> Expression:
    return FunctionCall(
        DURATION_BETWEEN,
        (
            ensure_expression(start),
            ensure_expression(end),
            ensure_expression(unit),
        ),
    )
