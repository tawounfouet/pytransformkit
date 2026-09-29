# ruff: noqa: E402

from __future__ import annotations

import math

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

from pytransformkit import (
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
    window,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.engines import EngineRegistry
from pytransformkit.errors import UnsupportedEngineCapabilityError
from pytransformkit.functions import col
from pytransformkit.runtime import ExecutionMode


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("ordered_at", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def _records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 1,
            "ordered_at": 20,
            "status": "PAID",
            "amount": None,
        },
        {
            "customer_id": 1,
            "ordered_at": 10,
            "status": "OPEN",
            "amount": 10.0,
        },
        {
            "customer_id": 1,
            "ordered_at": 20,
            "status": "PAID",
            "amount": 20.0,
        },
        {
            "customer_id": 1,
            "ordered_at": 30,
            "status": "PAID",
            "amount": 30.0,
        },
        {
            "customer_id": 2,
            "ordered_at": 5,
            "status": "OPEN",
            "amount": 4.0,
        },
        {
            "customer_id": 2,
            "ordered_at": 15,
            "status": "PAID",
            "amount": 6.0,
        },
    ]


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def _window_plan() -> TransformationPlan:
    ordered = window.partition_by("customer_id").order_by("ordered_at")
    cumulative = ordered.rows_between(
        window.unbounded_preceding(),
        window.current_row(),
    )
    moving = ordered.rows_between(
        window.preceding(1),
        window.current_row(),
    )

    builder = TransformationPlan.builder("analytical_orders")
    orders = builder.input("orders", schema=_schema())

    result = builder.derive(
        "row_number",
        source=orders,
        field_name="row_number",
        expression=window.row_number().over(ordered),
    )
    result = builder.derive(
        "rank",
        source=result,
        field_name="rank",
        expression=window.rank().over(ordered),
    )
    result = builder.derive(
        "dense_rank",
        source=result,
        field_name="dense_rank",
        expression=window.dense_rank().over(ordered),
    )
    result = builder.derive(
        "lag_status",
        source=result,
        field_name="lag_status",
        expression=window.lag(
            col("status"),
            default="START",
        ).over(ordered),
    )
    result = builder.derive(
        "lead_status",
        source=result,
        field_name="lead_status",
        expression=window.lead(
            col("status"),
            default="END",
        ).over(ordered),
    )
    result = builder.derive(
        "partition_sum",
        source=result,
        field_name="partition_sum",
        expression=window.sum(col("amount")).over(
            window.partition_by("customer_id")
        ),
    )
    result = builder.derive(
        "cumulative_count",
        source=result,
        field_name="cumulative_count",
        expression=window.count(col("amount")).over(cumulative),
    )
    result = builder.derive(
        "cumulative_sum",
        source=result,
        field_name="cumulative_sum",
        expression=window.sum(col("amount")).over(cumulative),
    )
    result = builder.derive(
        "cumulative_mean",
        source=result,
        field_name="cumulative_mean",
        expression=window.mean(col("amount")).over(cumulative),
    )
    result = builder.derive(
        "moving_sum",
        source=result,
        field_name="moving_sum",
        expression=window.sum(col("amount")).over(moving),
    )
    result = builder.derive(
        "moving_mean",
        source=result,
        field_name="moving_mean",
        expression=window.mean(col("amount")).over(moving),
    )

    return builder.output("result", result).build()


def _descending_plan() -> TransformationPlan:
    spec = window.partition_by("customer_id").order_by(
        window.desc("ordered_at")
    )
    builder = TransformationPlan.builder("descending_rank")
    orders = builder.input("orders", schema=_schema())
    result = builder.derive(
        "row_number_desc",
        source=orders,
        field_name="row_number_desc",
        expression=window.row_number().over(spec),
    )
    return builder.output("result", result).build()


def _normalize_value(value: object) -> object:
    if value is None:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _normalize(records: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {key: _normalize_value(value) for key, value in record.items()}
        for record in records
    ]


def _pandas_execute(plan: TransformationPlan) -> list[dict[str, object]]:
    result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            "orders": InputBinding.from_native(
                "orders",
                pd.DataFrame(_records()),
                engine="pandas",
            )
        },
    )
    return _normalize(
        result.output_handle.dataframe.to_dict(orient="records")
    )


def _polars_execute(
    plan: TransformationPlan,
    *,
    mode: ExecutionMode = ExecutionMode.EAGER,
) -> list[dict[str, object]]:
    native = pl.DataFrame(_records())
    if mode is ExecutionMode.LAZY:
        native = native.lazy()

    result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            "orders": InputBinding.from_native(
                "orders",
                native,
                engine="polars",
            )
        },
        mode=mode,
    )

    frame = result.output_handle.frame
    if isinstance(frame, pl.LazyFrame):
        frame = frame.collect()
    return _normalize(frame.to_dicts())


def test_common_window_suite_matches_pandas_and_polars() -> None:
    plan = _window_plan()

    pandas_records = _pandas_execute(plan)
    polars_records = _polars_execute(plan)

    assert pandas_records == polars_records

    first_customer = [
        record
        for record in pandas_records
        if record["customer_id"] == 1
    ]

    assert [record["row_number"] for record in first_customer] == [2, 1, 3, 4]
    assert [record["rank"] for record in first_customer] == [2, 1, 2, 4]
    assert [record["dense_rank"] for record in first_customer] == [2, 1, 2, 3]

    assert [record["lag_status"] for record in first_customer] == [
        "OPEN",
        "START",
        "PAID",
        "PAID",
    ]
    assert [record["lead_status"] for record in first_customer] == [
        "PAID",
        "PAID",
        "PAID",
        "END",
    ]

    assert [record["partition_sum"] for record in first_customer] == [
        60.0,
        60.0,
        60.0,
        60.0,
    ]
    assert [record["cumulative_count"] for record in first_customer] == [
        1,
        1,
        2,
        3,
    ]
    assert [record["cumulative_sum"] for record in first_customer] == [
        10.0,
        10.0,
        30.0,
        60.0,
    ]
    assert [record["moving_sum"] for record in first_customer] == [
        10.0,
        10.0,
        20.0,
        50.0,
    ]


def test_descending_window_order_matches_engines() -> None:
    plan = _descending_plan()

    pandas_records = _pandas_execute(plan)
    polars_records = _polars_execute(plan)

    assert pandas_records == polars_records

    first_customer = [
        record
        for record in pandas_records
        if record["customer_id"] == 1
    ]
    assert [record["row_number_desc"] for record in first_customer] == [
        2,
        4,
        3,
        1,
    ]


def test_polars_lazy_window_execution_preserves_semantics() -> None:
    plan = _window_plan()

    eager = _polars_execute(plan)
    lazy = _polars_execute(
        plan,
        mode=ExecutionMode.LAZY,
    )

    assert lazy == eager


@pytest.mark.parametrize(
    "spec",
    [
        window.order_by("ordered_at").rows_between(
            window.current_row(),
            window.following(1),
        ),
        window.order_by("ordered_at").range_between(
            window.unbounded_preceding(),
            window.current_row(),
        ),
    ],
)
@pytest.mark.parametrize(
    ("engine", "adapter", "native"),
    [
        (
            "pandas",
            PandasEngineAdapter(),
            lambda: pd.DataFrame(_records()),
        ),
        (
            "polars",
            PolarsEngineAdapter(),
            lambda: pl.DataFrame(_records()),
        ),
    ],
)
def test_unsupported_frame_semantics_fail_during_capability_validation(
    spec: object,
    engine: str,
    adapter: object,
    native: object,
) -> None:
    builder = TransformationPlan.builder("unsupported_frame")
    orders = builder.input("orders", schema=_schema())
    result = builder.derive(
        "windowed",
        source=orders,
        field_name="metric",
        expression=window.sum(col("amount")).over(spec),  # type: ignore[arg-type]
    )
    plan = builder.output("result", result).build()

    with pytest.raises(UnsupportedEngineCapabilityError):
        _runtime(adapter).execute(
            plan,
            engine=engine,
            inputs={
                "orders": InputBinding.from_native(
                    "orders",
                    native(),  # type: ignore[operator]
                    engine=engine,
                )
            },
        )
