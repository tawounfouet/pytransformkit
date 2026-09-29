"""Portable aggregate Expression constructors."""

from __future__ import annotations

from pytransformkit.domain.expressions.aggregate import (
    AggregateExpression,
    AggregateFunction,
)
from pytransformkit.domain.expressions.base import ensure_expression


def count(value: object | None = None) -> AggregateExpression:
    """Count rows when value is omitted, otherwise count non-null values."""
    return AggregateExpression(
        AggregateFunction.COUNT,
        None if value is None else ensure_expression(value),
    )


def count_distinct(value: object) -> AggregateExpression:
    """Count distinct non-null values."""
    return AggregateExpression(
        AggregateFunction.COUNT_DISTINCT,
        ensure_expression(value),
    )


def sum(value: object) -> AggregateExpression:
    """Sum non-null numeric values."""
    return AggregateExpression(
        AggregateFunction.SUM,
        ensure_expression(value),
    )


def min(value: object) -> AggregateExpression:
    """Return the minimum non-null value."""
    return AggregateExpression(
        AggregateFunction.MIN,
        ensure_expression(value),
    )


def max(value: object) -> AggregateExpression:
    """Return the maximum non-null value."""
    return AggregateExpression(
        AggregateFunction.MAX,
        ensure_expression(value),
    )


def mean(value: object) -> AggregateExpression:
    """Return the arithmetic mean of non-null numeric values."""
    return AggregateExpression(
        AggregateFunction.MEAN,
        ensure_expression(value),
    )


avg = mean


__all__ = [
    "avg",
    "count",
    "count_distinct",
    "max",
    "mean",
    "min",
    "sum",
]
