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
)
from pytransformkit import functions as fn
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
from pytransformkit.functions import col, lower


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("country", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def _records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 1,
            "country": "FR",
            "status": "PAID",
            "amount": 10.0,
        },
        {
            "customer_id": 1,
            "country": "FR",
            "status": "PAID",
            "amount": 20.0,
        },
        {
            "customer_id": 1,
            "country": "FR",
            "status": "OPEN",
            "amount": None,
        },
        {
            "customer_id": 2,
            "country": "DE",
            "status": "PAID",
            "amount": 5.0,
        },
        {
            "customer_id": 2,
            "country": "DE",
            "status": "PAID",
            "amount": None,
        },
        {
            "customer_id": 3,
            "country": None,
            "status": "OPEN",
            "amount": None,
        },
    ]


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("aggregate_orders")
    orders = builder.input("orders", schema=_schema())
    stats = builder.aggregate(
        "country_stats",
        source=orders,
        group_by=(col("country"),),
        metrics={
            "row_count": fn.count(),
            "amount_count": fn.count(col("amount")),
            "status_count": fn.count_distinct(col("status")),
            "total_amount": fn.sum(col("amount")),
            "min_amount": fn.min(col("amount")),
            "max_amount": fn.max(col("amount")),
            "mean_amount": fn.mean(col("amount")),
        },
    )
    return builder.output("stats", stats).build()


def _expression_group_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("aggregate_expression_group")
    orders = builder.input("orders", schema=_schema())
    stats = builder.aggregate(
        "status_stats",
        source=orders,
        group_by=(lower(col("status")),),
        metrics={
            "row_count": fn.count(),
        },
    )
    return builder.output("stats", stats).build()


def _global_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("aggregate_global")
    orders = builder.input("orders", schema=_schema())
    stats = builder.aggregate(
        "global_stats",
        source=orders,
        metrics={
            "row_count": fn.count(),
            "amount_count": fn.count(col("amount")),
            "total_amount": fn.sum(col("amount")),
            "min_amount": fn.min(col("amount")),
            "max_amount": fn.max(col("amount")),
            "mean_amount": fn.mean(col("amount")),
        },
    )
    return builder.output("stats", stats).build()


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
    normalized = [
        {key: _normalize_value(value) for key, value in record.items()}
        for record in records
    ]
    return sorted(normalized, key=repr)


def _pandas_execute(
    plan: TransformationPlan,
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            "orders": InputBinding.from_native(
                "orders",
                pd.DataFrame(records),
                engine="pandas",
            )
        },
    )
    return _normalize(result.output_handle.dataframe.to_dict(orient="records"))


def _polars_execute(
    plan: TransformationPlan,
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            "orders": InputBinding.from_native(
                "orders",
                pl.DataFrame(records),
                engine="polars",
            )
        },
    )
    return _normalize(result.output_handle.frame.to_dicts())


def test_grouped_aggregate_semantics_match_pandas_and_polars() -> None:
    plan = _plan()

    pandas_records = _pandas_execute(plan, _records())
    polars_records = _polars_execute(plan, _records())

    assert pandas_records == polars_records
    assert pandas_records == _normalize(
        [
            {
                "country": "FR",
                "row_count": 3,
                "amount_count": 2,
                "status_count": 2,
                "total_amount": 30.0,
                "min_amount": 10.0,
                "max_amount": 20.0,
                "mean_amount": 15.0,
            },
            {
                "country": "DE",
                "row_count": 2,
                "amount_count": 1,
                "status_count": 1,
                "total_amount": 5.0,
                "min_amount": 5.0,
                "max_amount": 5.0,
                "mean_amount": 5.0,
            },
            {
                "country": None,
                "row_count": 1,
                "amount_count": 0,
                "status_count": 1,
                "total_amount": None,
                "min_amount": None,
                "max_amount": None,
                "mean_amount": None,
            },
        ]
    )


def test_grouping_expression_semantics_match_engines() -> None:
    plan = _expression_group_plan()

    pandas_records = _pandas_execute(plan, _records())
    polars_records = _polars_execute(plan, _records())

    assert pandas_records == polars_records
    assert {record["group_0"] for record in pandas_records} == {
        "paid",
        "open",
    }


def test_global_aggregate_semantics_match_engines() -> None:
    plan = _global_plan()

    pandas_records = _pandas_execute(plan, _records())
    polars_records = _polars_execute(plan, _records())

    assert pandas_records == polars_records
    assert pandas_records == [
        {
            "row_count": 6,
            "amount_count": 3,
            "total_amount": 35.0,
            "min_amount": 5.0,
            "max_amount": 20.0,
            "mean_amount": pytest.approx(35.0 / 3.0),
        }
    ]


def test_global_empty_aggregate_preserves_null_semantics() -> None:
    plan = _global_plan()
    pandas_empty = pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="Int64"),
            "country": pd.Series(dtype="string"),
            "status": pd.Series(dtype="string"),
            "amount": pd.Series(dtype="Float64"),
        }
    )
    polars_empty = pl.DataFrame(
        schema={
            "customer_id": pl.Int64,
            "country": pl.String,
            "status": pl.String,
            "amount": pl.Float64,
        }
    )

    pandas_result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            "orders": InputBinding.from_native(
                "orders",
                pandas_empty,
                engine="pandas",
            )
        },
    )
    polars_result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            "orders": InputBinding.from_native(
                "orders",
                polars_empty,
                engine="polars",
            )
        },
    )

    pandas_records = _normalize(
        pandas_result.output_handle.dataframe.to_dict(orient="records")
    )
    polars_records = _normalize(polars_result.output_handle.frame.to_dicts())

    assert pandas_records == polars_records
    assert pandas_records == [
        {
            "row_count": 0,
            "amount_count": 0,
            "total_amount": None,
            "min_amount": None,
            "max_amount": None,
            "mean_amount": None,
        }
    ]
