"""Pandas execution of portable analytical WindowExpressions."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from pytransformkit.domain.expressions.window import (
    WindowExpression,
    WindowFrameKind,
    WindowFunction,
)
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.pandas.expressions import (
    PandasExpressionCompiler,
)


class PandasWindowCompiler:
    """Evaluate one WindowExpression while preserving input row order."""

    def __init__(
        self,
        expression_compiler: PandasExpressionCompiler | None = None,
    ) -> None:
        self._expression_compiler = (
            expression_compiler or PandasExpressionCompiler()
        )

    def compile(
        self,
        expression: WindowExpression,
        dataframe: Any,
    ) -> Any:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Pandas windows require a pandas.DataFrame.")

        work = pd.DataFrame(
            {"__ptk_position__": range(len(dataframe))}
        )

        partition_columns: list[str] = []
        for index, field in enumerate(expression.spec.partition_keys):
            name = f"__ptk_partition_{index}__"
            work[name] = dataframe[str(field)].reset_index(drop=True)
            partition_columns.append(name)

        order_columns: list[str] = []
        for index, key in enumerate(expression.spec.order_keys):
            name = f"__ptk_order_{index}__"
            work[name] = dataframe[str(key.field)].reset_index(drop=True)
            order_columns.append(name)

        argument_column: str | None = None
        if expression.argument is not None:
            argument_column = "__ptk_argument__"
            work[argument_column] = _materialize(
                self._expression_compiler.compile(
                    expression.argument,
                    dataframe,
                ),
                len(dataframe),
            )

        default_column: str | None = None
        if expression.default is not None:
            default_column = "__ptk_default__"
            work[default_column] = _materialize(
                self._expression_compiler.compile(
                    expression.default,
                    dataframe,
                ),
                len(dataframe),
            )

        work = _stable_window_sort(
            work,
            order_columns,
            expression,
        )

        groups = _group_positions(
            work,
            partition_columns,
        )

        if expression.function is WindowFunction.ROW_NUMBER:
            values = _row_number(work, groups)
        elif expression.function in {
            WindowFunction.RANK,
            WindowFunction.DENSE_RANK,
        }:
            values = _rank(
                work,
                groups,
                order_columns,
                dense=expression.function is WindowFunction.DENSE_RANK,
            )
        elif expression.function in {
            WindowFunction.LAG,
            WindowFunction.LEAD,
        }:
            if argument_column is None:
                raise AdapterError(
                    f"{expression.function.value} requires an argument."
                )
            values = _offset(
                work,
                groups,
                argument_column,
                default_column,
                expression,
            )
        elif expression.function in {
            WindowFunction.COUNT,
            WindowFunction.SUM,
            WindowFunction.MIN,
            WindowFunction.MAX,
            WindowFunction.MEAN,
        }:
            values = _aggregate(
                work,
                groups,
                argument_column,
                expression,
            )
        else:
            raise AdapterError(
                f"Unsupported Pandas window function {expression.function.value!r}."
            )

        restored: list[object] = [pd.NA] * len(work)
        for sorted_position, original_position in enumerate(
            work["__ptk_position__"].tolist()
        ):
            restored[int(original_position)] = values[sorted_position]

        return pd.Series(
            restored,
            index=dataframe.index,
        )


def _materialize(value: Any, size: int) -> Any:
    if isinstance(value, pd.Series):
        return value.reset_index(drop=True)
    return pd.Series([value] * size)


def _stable_window_sort(
    dataframe: Any,
    order_columns: list[str],
    expression: WindowExpression,
) -> Any:
    result = dataframe
    for column, key in reversed(
        list(zip(order_columns, expression.spec.order_keys, strict=True))
    ):
        result = result.sort_values(
            by=column,
            ascending=key.direction.value == "asc",
            na_position=key.nulls.value,
            kind="mergesort",
        )
    return result.reset_index(drop=True)


def _group_positions(
    dataframe: Any,
    partition_columns: list[str],
) -> tuple[tuple[int, ...], ...]:
    if not partition_columns:
        return (tuple(range(len(dataframe))),)

    groups = dataframe.groupby(
        partition_columns,
        dropna=False,
        sort=False,
    ).indices
    return tuple(
        tuple(int(position) for position in positions)
        for positions in groups.values()
    )


def _row_number(
    dataframe: Any,
    groups: tuple[tuple[int, ...], ...],
) -> list[object]:
    values: list[object] = [0] * len(dataframe)
    for positions in groups:
        for number, position in enumerate(positions, start=1):
            values[position] = number
    return values


def _rank(
    dataframe: Any,
    groups: tuple[tuple[int, ...], ...],
    order_columns: list[str],
    *,
    dense: bool,
) -> list[object]:
    values: list[object] = [0] * len(dataframe)

    for positions in groups:
        previous: tuple[object, ...] | None = None
        current_rank = 0
        dense_rank = 0

        for ordinal, position in enumerate(positions, start=1):
            current = tuple(
                dataframe.iloc[position][column]
                for column in order_columns
            )
            if previous is None or not _tuple_equal(previous, current):
                current_rank = ordinal
                dense_rank += 1
            values[position] = dense_rank if dense else current_rank
            previous = current

    return values


def _offset(
    dataframe: Any,
    groups: tuple[tuple[int, ...], ...],
    argument_column: str,
    default_column: str | None,
    expression: WindowExpression,
) -> list[object]:
    values: list[object] = [pd.NA] * len(dataframe)
    direction = -1 if expression.function is WindowFunction.LAG else 1

    for positions in groups:
        for local_index, position in enumerate(positions):
            source_index = local_index + direction * expression.offset
            if 0 <= source_index < len(positions):
                source_position = positions[source_index]
                values[position] = dataframe.iloc[source_position][argument_column]
            elif default_column is not None:
                values[position] = dataframe.iloc[position][default_column]

    return values


def _aggregate(
    dataframe: Any,
    groups: tuple[tuple[int, ...], ...],
    argument_column: str | None,
    expression: WindowExpression,
) -> list[object]:
    frame_kind = expression.frame_kind
    if frame_kind not in {
        WindowFrameKind.FULL_PARTITION,
        WindowFrameKind.ROWS_CUMULATIVE,
        WindowFrameKind.ROWS_MOVING,
    }:
        raise AdapterError(
            f"Pandas does not support window frame kind {frame_kind.value!r}."
        )

    values: list[object] = [pd.NA] * len(dataframe)

    for positions in groups:
        for local_index, position in enumerate(positions):
            start, end = _frame_bounds(
                len(positions),
                local_index,
                expression,
            )
            frame_positions = positions[start:end]
            values[position] = _aggregate_frame(
                dataframe,
                frame_positions,
                argument_column,
                expression.function,
            )

    return values


def _frame_bounds(
    group_size: int,
    current_index: int,
    expression: WindowExpression,
) -> tuple[int, int]:
    frame_kind = expression.frame_kind

    if frame_kind is WindowFrameKind.FULL_PARTITION:
        return 0, group_size

    if frame_kind is WindowFrameKind.ROWS_CUMULATIVE:
        return 0, current_index + 1

    if frame_kind is WindowFrameKind.ROWS_MOVING:
        frame = expression.spec.frame
        if frame is None or frame.start.offset is None:
            raise AdapterError("Moving ROWS frame is missing its PRECEDING offset.")
        return max(0, current_index - frame.start.offset), current_index + 1

    raise AdapterError(
        f"Unsupported Pandas frame kind {frame_kind.value!r}."
    )


def _aggregate_frame(
    dataframe: Any,
    positions: Iterable[int],
    argument_column: str | None,
    function: WindowFunction,
) -> object:
    positions = tuple(positions)

    if function is WindowFunction.COUNT and argument_column is None:
        return len(positions)

    if argument_column is None:
        raise AdapterError(f"{function.value} requires an argument.")

    series = dataframe.iloc[list(positions)][argument_column]

    if function is WindowFunction.COUNT:
        return int(series.count())
    if function is WindowFunction.SUM:
        return series.sum(min_count=1)
    if function is WindowFunction.MIN:
        return series.min()
    if function is WindowFunction.MAX:
        return series.max()
    if function is WindowFunction.MEAN:
        return series.mean()

    raise AdapterError(
        f"Unsupported Pandas aggregate window function {function.value!r}."
    )


def _tuple_equal(
    left: tuple[object, ...],
    right: tuple[object, ...],
) -> bool:
    return all(_scalar_equal(a, b) for a, b in zip(left, right, strict=True))


def _scalar_equal(left: object, right: object) -> bool:
    if _is_null(left) and _is_null(right):
        return True
    try:
        return bool(left == right)
    except (TypeError, ValueError):
        return False


def _is_null(value: object) -> bool:
    try:
        result = pd.isna(value)
        return bool(result)
    except (TypeError, ValueError):
        return False
