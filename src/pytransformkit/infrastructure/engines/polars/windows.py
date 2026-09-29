"""Polars execution of portable analytical WindowExpressions."""

from __future__ import annotations

from typing import Any

import polars as pl

from pytransformkit.domain.expressions.window import (
    WindowExpression,
    WindowFrameKind,
    WindowFunction,
)
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.polars.expressions import (
    PolarsExpressionCompiler,
)


class PolarsWindowCompiler:
    """Lower one WindowExpression to native Polars operations."""

    def __init__(
        self,
        expression_compiler: PolarsExpressionCompiler | None = None,
    ) -> None:
        self._expression_compiler = expression_compiler or PolarsExpressionCompiler()

    def derive(
        self,
        frame: Any,
        expression: WindowExpression,
        *,
        field_name: str,
    ) -> Any:
        existing = _column_names(frame)
        position = _internal_name(existing, "position")
        existing.add(position)

        work = _with_row_index(frame, position)

        partition_columns = [str(field) for field in expression.spec.partition_keys]
        order_columns = [str(key.field) for key in expression.spec.order_keys]

        sort_columns = partition_columns + order_columns
        if sort_columns:
            work = work.sort(
                by=sort_columns,
                descending=(
                    [False] * len(partition_columns)
                    + [
                        key.direction.value == "desc"
                        for key in expression.spec.order_keys
                    ]
                ),
                nulls_last=(
                    [False] * len(partition_columns)
                    + [key.nulls.value == "last" for key in expression.spec.order_keys]
                ),
                maintain_order=True,
            )

        argument_column: str | None = None
        if expression.argument is not None:
            argument_column = _internal_name(existing, "argument")
            existing.add(argument_column)
            work = work.with_columns(
                self._expression_compiler.compile(
                    expression.argument,
                    work,
                ).alias(argument_column)
            )

        default_column: str | None = None
        if expression.default is not None:
            default_column = _internal_name(existing, "default")
            existing.add(default_column)
            work = work.with_columns(
                self._expression_compiler.compile(
                    expression.default,
                    work,
                ).alias(default_column)
            )

        if expression.function is WindowFunction.ROW_NUMBER:
            derived = _row_number(position, partition_columns)
            work = work.with_columns(derived.alias(field_name))

        elif expression.function in {
            WindowFunction.RANK,
            WindowFunction.DENSE_RANK,
        }:
            work = _derive_rank(
                work,
                expression,
                field_name=field_name,
                position_column=position,
                partition_columns=partition_columns,
                order_columns=order_columns,
                existing=existing,
            )

        elif expression.function in {
            WindowFunction.LAG,
            WindowFunction.LEAD,
        }:
            if argument_column is None:
                raise AdapterError(f"{expression.function.value} requires an argument.")
            work = work.with_columns(
                _offset_expression(
                    expression,
                    position_column=position,
                    argument_column=argument_column,
                    default_column=default_column,
                    partition_columns=partition_columns,
                ).alias(field_name)
            )

        elif expression.function in {
            WindowFunction.COUNT,
            WindowFunction.SUM,
            WindowFunction.MIN,
            WindowFunction.MAX,
            WindowFunction.MEAN,
        }:
            work = _derive_aggregate(
                work,
                expression,
                field_name=field_name,
                position_column=position,
                argument_column=argument_column,
                partition_columns=partition_columns,
                existing=existing,
            )

        else:
            raise AdapterError(
                f"Unsupported Polars window function {expression.function.value!r}."
            )

        temporary = [
            name
            for name in _column_names(work)
            if name.startswith("__pytransformkit_window_")
        ]
        return work.sort(
            position,
            maintain_order=True,
        ).drop(temporary)


def _with_row_index(frame: Any, name: str) -> Any:
    method = getattr(frame, "with_row_index", None)
    if method is not None:
        return method(name)
    return frame.with_row_count(name)


def _row_number(
    position_column: str,
    partition_columns: list[str],
) -> Any:
    expression = pl.col(position_column).cum_count().cast(pl.Int64)
    return _over(expression, partition_columns)


def _derive_rank(
    frame: Any,
    expression: WindowExpression,
    *,
    field_name: str,
    position_column: str,
    partition_columns: list[str],
    order_columns: list[str],
    existing: set[str],
) -> Any:
    row_number_column = _internal_name(existing, "row_number")
    existing.add(row_number_column)
    frame = frame.with_columns(
        _row_number(
            position_column,
            partition_columns,
        ).alias(row_number_column)
    )

    previous_columns: list[str] = []
    for index, column in enumerate(order_columns):
        previous = _internal_name(existing, f"previous_{index}")
        existing.add(previous)
        previous_columns.append(previous)
        frame = frame.with_columns(
            _over(
                pl.col(column).shift(1),
                partition_columns,
            ).alias(previous)
        )

    same_order = pl.lit(True)
    for column, previous in zip(
        order_columns,
        previous_columns,
        strict=True,
    ):
        current_value = pl.col(column)
        previous_value = pl.col(previous)
        same = (
            (current_value == previous_value)
            .fill_null(
                current_value.is_null()
                & previous_value.is_null()
            )
        )
        same_order = same_order & same

    new_peer_group = (
        (pl.col(row_number_column) == 1)
        | ~same_order
    )

    flag_column = _internal_name(existing, "peer_group_start")
    existing.add(flag_column)
    frame = frame.with_columns(
        new_peer_group.cast(pl.Int64).alias(flag_column)
    )

    if expression.function is WindowFunction.DENSE_RANK:
        rank_expression = _over(
            pl.col(flag_column).cum_sum(),
            partition_columns,
        )
        return frame.with_columns(
            rank_expression.cast(pl.Int64).alias(field_name)
        )

    candidate_column = _internal_name(existing, "rank_candidate")
    existing.add(candidate_column)
    frame = frame.with_columns(
        pl.when(pl.col(flag_column) == 1)
        .then(pl.col(row_number_column))
        .otherwise(None)
        .alias(candidate_column)
    )
    rank_expression = _over(
        pl.col(candidate_column).forward_fill(),
        partition_columns,
    )
    return frame.with_columns(
        rank_expression.cast(pl.Int64).alias(field_name)
    )


def _offset_expression(
    expression: WindowExpression,
    *,
    position_column: str,
    argument_column: str,
    default_column: str | None,
    partition_columns: list[str],
) -> Any:
    periods = (
        expression.offset
        if expression.function is WindowFunction.LAG
        else -expression.offset
    )
    shifted_value = _over(
        pl.col(argument_column).shift(periods),
        partition_columns,
    )
    shifted_position = _over(
        pl.col(position_column).shift(periods),
        partition_columns,
    )

    default_value = (
        pl.lit(None)
        if default_column is None
        else pl.col(default_column)
    )

    return (
        pl.when(shifted_position.is_not_null())
        .then(shifted_value)
        .otherwise(default_value)
    )


def _derive_aggregate(
    frame: Any,
    expression: WindowExpression,
    *,
    field_name: str,
    position_column: str,
    argument_column: str | None,
    partition_columns: list[str],
    existing: set[str],
) -> Any:
    frame_kind = expression.frame_kind

    if frame_kind is WindowFrameKind.FULL_PARTITION:
        aggregate = _full_partition_aggregate(
            expression.function,
            position_column,
            argument_column,
            partition_columns,
        )
        return frame.with_columns(aggregate.alias(field_name))

    if frame_kind is WindowFrameKind.ROWS_CUMULATIVE:
        return _derive_cumulative(
            frame,
            expression.function,
            field_name=field_name,
            position_column=position_column,
            argument_column=argument_column,
            partition_columns=partition_columns,
            existing=existing,
        )

    if frame_kind is WindowFrameKind.ROWS_MOVING:
        window_frame = expression.spec.frame
        if window_frame is None or window_frame.start.offset is None:
            raise AdapterError("Moving ROWS frame is missing its PRECEDING offset.")
        aggregate = _moving_aggregate(
            expression.function,
            position_column,
            argument_column,
            partition_columns,
            window_size=window_frame.start.offset + 1,
        )
        return frame.with_columns(aggregate.alias(field_name))

    raise AdapterError(
        f"Polars does not support window frame kind {frame_kind.value!r}."
    )


def _full_partition_aggregate(
    function: WindowFunction,
    position_column: str,
    argument_column: str | None,
    partition_columns: list[str],
) -> Any:
    if function is WindowFunction.COUNT and argument_column is None:
        return _over(
            pl.col(position_column).count().cast(pl.Int64),
            partition_columns,
        )

    if argument_column is None:
        raise AdapterError(f"{function.value} requires an argument.")

    value = pl.col(argument_column)

    if function is WindowFunction.COUNT:
        return _over(value.count().cast(pl.Int64), partition_columns)
    if function is WindowFunction.SUM:
        count = _over(value.count(), partition_columns)
        total = _over(value.sum(), partition_columns)
        return pl.when(count == 0).then(pl.lit(None)).otherwise(total)
    if function is WindowFunction.MIN:
        return _over(value.min(), partition_columns)
    if function is WindowFunction.MAX:
        return _over(value.max(), partition_columns)
    if function is WindowFunction.MEAN:
        return _over(value.mean().cast(pl.Float64), partition_columns)

    raise AdapterError(
        f"Unsupported full-partition function {function.value!r}."
    )


def _derive_cumulative(
    frame: Any,
    function: WindowFunction,
    *,
    field_name: str,
    position_column: str,
    argument_column: str | None,
    partition_columns: list[str],
    existing: set[str],
) -> Any:
    if function is WindowFunction.COUNT and argument_column is None:
        return frame.with_columns(
            _row_number(
                position_column,
                partition_columns,
            ).alias(field_name)
        )

    if argument_column is None:
        raise AdapterError(f"{function.value} requires an argument.")

    value = pl.col(argument_column)
    non_null = value.is_not_null().cast(pl.Int64)
    count_expression = _over(
        non_null.cum_sum(),
        partition_columns,
    )

    if function is WindowFunction.COUNT:
        return frame.with_columns(
            count_expression.cast(pl.Int64).alias(field_name)
        )

    if function is WindowFunction.SUM:
        total = _over(
            value.fill_null(0).cum_sum(),
            partition_columns,
        )
        result = (
            pl.when(count_expression == 0)
            .then(pl.lit(None))
            .otherwise(total)
        )
        return frame.with_columns(result.alias(field_name))

    if function in {
        WindowFunction.MIN,
        WindowFunction.MAX,
    }:
        raw_column = _internal_name(existing, "cumulative")
        existing.add(raw_column)
        raw = (
            value.cum_min()
            if function is WindowFunction.MIN
            else value.cum_max()
        )
        frame = frame.with_columns(
            _over(raw, partition_columns).alias(raw_column)
        )
        filled = _over(
            pl.col(raw_column).forward_fill(),
            partition_columns,
        )
        return frame.with_columns(filled.alias(field_name))

    if function is WindowFunction.MEAN:
        total = _over(
            value.fill_null(0).cum_sum(),
            partition_columns,
        )
        result = (
            pl.when(count_expression == 0)
            .then(pl.lit(None))
            .otherwise(total / count_expression)
            .cast(pl.Float64)
        )
        return frame.with_columns(result.alias(field_name))

    raise AdapterError(
        f"Unsupported cumulative function {function.value!r}."
    )


def _moving_aggregate(
    function: WindowFunction,
    position_column: str,
    argument_column: str | None,
    partition_columns: list[str],
    *,
    window_size: int,
) -> Any:
    if function is WindowFunction.COUNT and argument_column is None:
        value = pl.col(position_column).is_not_null().cast(pl.Int64)
    elif argument_column is not None:
        value = pl.col(argument_column)
    else:
        raise AdapterError(f"{function.value} requires an argument.")

    if function is WindowFunction.COUNT:
        present = value.is_not_null().cast(pl.Int64)
        rolling = present.rolling_sum(
            window_size=window_size,
            min_samples=1,
        )
        return _over(rolling, partition_columns).cast(pl.Int64)

    if argument_column is None:
        raise AdapterError(f"{function.value} requires an argument.")

    if function is WindowFunction.SUM:
        rolling = value.rolling_sum(
            window_size=window_size,
            min_samples=1,
        )
    elif function is WindowFunction.MIN:
        rolling = value.rolling_min(
            window_size=window_size,
            min_samples=1,
        )
    elif function is WindowFunction.MAX:
        rolling = value.rolling_max(
            window_size=window_size,
            min_samples=1,
        )
    elif function is WindowFunction.MEAN:
        rolling = value.rolling_mean(
            window_size=window_size,
            min_samples=1,
        ).cast(pl.Float64)
    else:
        raise AdapterError(
            f"Unsupported moving function {function.value!r}."
        )

    return _over(rolling, partition_columns)


def _over(expression: Any, partition_columns: list[str]) -> Any:
    if not partition_columns:
        return expression
    return expression.over(partition_columns)


def _column_names(frame: Any) -> set[str]:
    if isinstance(frame, pl.LazyFrame):
        return set(frame.collect_schema().names())
    return set(frame.columns)


def _internal_name(existing: set[str], suffix: str) -> str:
    candidate = f"__pytransformkit_window_{suffix}__"
    while candidate in existing:
        candidate = f"_{candidate}"
    return candidate
