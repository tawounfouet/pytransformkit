"""Public analytical window DSL."""

from __future__ import annotations

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.window import (
    WindowBoundary,
    WindowBoundaryKind,
    WindowFunction,
    WindowFunctionCall,
    WindowOrderKey,
    WindowSpec,
    as_window_argument,
)
from pytransformkit.domain.transformations.sorting import NullOrder, SortDirection


def partition_by(*fields: str) -> WindowSpec:
    """Create a WindowSpec with explicit partition fields."""
    return WindowSpec(
        partition_keys=tuple(FieldPath.of(field) for field in fields),
    )


def order_by(*fields: str | WindowOrderKey) -> WindowSpec:
    """Create a global WindowSpec with explicit ordering."""
    return WindowSpec().order_by(*fields)


def asc(
    field: str,
    *,
    nulls: NullOrder = NullOrder.LAST,
) -> WindowOrderKey:
    """Create an ascending window order key."""
    return WindowOrderKey(
        field=FieldPath.of(field),
        direction=SortDirection.ASC,
        nulls=nulls,
    )


def desc(
    field: str,
    *,
    nulls: NullOrder = NullOrder.LAST,
) -> WindowOrderKey:
    """Create a descending window order key."""
    return WindowOrderKey(
        field=FieldPath.of(field),
        direction=SortDirection.DESC,
        nulls=nulls,
    )


def unbounded_preceding() -> WindowBoundary:
    return WindowBoundary(WindowBoundaryKind.UNBOUNDED_PRECEDING)


def preceding(offset: int) -> WindowBoundary:
    return WindowBoundary(WindowBoundaryKind.PRECEDING, offset=offset)


def current_row() -> WindowBoundary:
    return WindowBoundary(WindowBoundaryKind.CURRENT_ROW)


def following(offset: int) -> WindowBoundary:
    return WindowBoundary(WindowBoundaryKind.FOLLOWING, offset=offset)


def unbounded_following() -> WindowBoundary:
    return WindowBoundary(WindowBoundaryKind.UNBOUNDED_FOLLOWING)


def row_number() -> WindowFunctionCall:
    return WindowFunctionCall(WindowFunction.ROW_NUMBER)


def rank() -> WindowFunctionCall:
    return WindowFunctionCall(WindowFunction.RANK)


def dense_rank() -> WindowFunctionCall:
    return WindowFunctionCall(WindowFunction.DENSE_RANK)


def lag(
    value: object,
    *,
    offset: int = 1,
    default: object | None = None,
) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.LAG,
        argument=as_window_argument(value),
        offset=offset,
        default=None if default is None else as_window_argument(default),
    )


def lead(
    value: object,
    *,
    offset: int = 1,
    default: object | None = None,
) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.LEAD,
        argument=as_window_argument(value),
        offset=offset,
        default=None if default is None else as_window_argument(default),
    )


def count(value: object | None = None) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.COUNT,
        argument=None if value is None else as_window_argument(value),
    )


def sum(value: object) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.SUM,
        argument=as_window_argument(value),
    )


def min(value: object) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.MIN,
        argument=as_window_argument(value),
    )


def max(value: object) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.MAX,
        argument=as_window_argument(value),
    )


def mean(value: object) -> WindowFunctionCall:
    return WindowFunctionCall(
        WindowFunction.MEAN,
        argument=as_window_argument(value),
    )


avg = mean


__all__ = [
    "WindowBoundary",
    "WindowOrderKey",
    "WindowSpec",
    "asc",
    "avg",
    "count",
    "current_row",
    "dense_rank",
    "desc",
    "following",
    "lag",
    "lead",
    "max",
    "mean",
    "min",
    "order_by",
    "partition_by",
    "preceding",
    "rank",
    "row_number",
    "sum",
    "unbounded_following",
    "unbounded_preceding",
]
