# ruff: noqa: E402

from __future__ import annotations

import math

import pytest

duckdb = pytest.importorskip("duckdb")
pa = pytest.importorskip("pyarrow")
pd = pytest.importorskip("pandas")

from pytransformkit import (
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
    window,
)
from pytransformkit import functions as fn
from pytransformkit.adapters.duckdb import DuckDBEngineAdapter
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.domain.data.data_types import FloatType, IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.transformations.relational import NullJoinPolicy
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


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
    return sorted(
        [
            {key: _normalize_value(value) for key, value in row.items()}
            for row in records
        ],
        key=repr,
    )


def _pandas_records(
    plan: TransformationPlan,
    inputs: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            name: InputBinding.from_native(
                name,
                pd.DataFrame(records),
                engine="pandas",
            )
            for name, records in inputs.items()
        },
    )
    return _normalize(result.output_handle.dataframe.to_dict(orient="records"))


def _duckdb_records(
    plan: TransformationPlan,
    inputs: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    adapter = DuckDBEngineAdapter()
    try:
        result = _runtime(adapter).execute(
            plan,
            engine="duckdb",
            inputs={
                name: InputBinding.from_native(
                    name,
                    pa.Table.from_pylist(records),
                    engine="duckdb",
                )
                for name, records in inputs.items()
            },
        )
        return _normalize(result.output_handle.to_arrow_table().to_pylist())
    finally:
        adapter.close()


def _join_schema() -> Schema:
    return Schema(
        (
            Field("customer_id", IntegerType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def _right_join_schema() -> Schema:
    return Schema(
        (
            Field("customer_id", IntegerType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", IntegerType(), nullable=False),
        )
    )


@pytest.mark.parametrize(
    ("how", "nulls"),
    [
        ("inner", NullJoinPolicy.MATCH),
        ("left", NullJoinPolicy.MATCH),
        ("right", NullJoinPolicy.MATCH),
        ("full", NullJoinPolicy.MATCH),
        ("semi", NullJoinPolicy.MATCH),
        ("anti", NullJoinPolicy.MATCH),
        ("inner", NullJoinPolicy.NEVER_MATCH),
    ],
)
def test_duckdb_join_semantics_match_pandas(
    how: str,
    nulls: NullJoinPolicy,
) -> None:
    builder = TransformationPlan.builder("duckdb_join")
    left = builder.input("left", schema=_join_schema())
    right = builder.input("right", schema=_right_join_schema())
    joined = builder.join(
        "joined",
        left=left,
        right=right,
        how=how,
        on=(("customer_id", "customer_id"),),
        nulls=nulls,
    )
    plan = builder.output("result", joined).build()

    inputs = {
        "left": [
            {"customer_id": None, "status": "LEFT_NULL"},
            {"customer_id": 1, "status": "ACTIVE"},
            {"customer_id": 2, "status": "INACTIVE"},
        ],
        "right": [
            {"customer_id": None, "status": "RIGHT_NULL", "amount": 99},
            {"customer_id": 1, "status": "PAID", "amount": 10},
            {"customer_id": 3, "status": "OPEN", "amount": 30},
        ],
    }

    assert _duckdb_records(plan, inputs) == _pandas_records(plan, inputs)


def _aggregate_schema() -> Schema:
    return Schema(
        (
            Field("country", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def test_duckdb_grouped_aggregates_match_pandas() -> None:
    builder = TransformationPlan.builder("duckdb_aggregate")
    source = builder.input("orders", schema=_aggregate_schema())
    result = builder.aggregate(
        "stats",
        source=source,
        group_by=(col("country"),),
        metrics={
            "row_count": fn.count(),
            "status_count": fn.count_distinct(col("status")),
            "total_amount": fn.sum(col("amount")),
            "mean_amount": fn.mean(col("amount")),
        },
    )
    plan = builder.output("result", result).build()

    inputs = {
        "orders": [
            {"country": "FR", "status": "PAID", "amount": 10.0},
            {"country": "FR", "status": "OPEN", "amount": None},
            {"country": "FR", "status": "PAID", "amount": 20.0},
            {"country": None, "status": "OPEN", "amount": None},
        ]
    }

    assert _duckdb_records(plan, inputs) == _pandas_records(plan, inputs)


def _window_schema() -> Schema:
    return Schema(
        (
            Field("customer_id", IntegerType(), nullable=False),
            Field("ordered_at", IntegerType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def test_duckdb_windows_match_pandas_for_qualified_frames() -> None:
    ordered = window.partition_by("customer_id").order_by("ordered_at")
    cumulative = ordered.rows_between(
        window.unbounded_preceding(),
        window.current_row(),
    )
    moving = ordered.rows_between(
        window.preceding(1),
        window.current_row(),
    )

    builder = TransformationPlan.builder("duckdb_windows")
    source = builder.input("orders", schema=_window_schema())
    result = builder.derive(
        "row_number",
        source=source,
        field_name="row_number",
        expression=window.row_number().over(ordered),
    )
    result = builder.derive(
        "lag_amount",
        source=result,
        field_name="lag_amount",
        expression=window.lag(col("amount"), default=-1.0).over(ordered),
    )
    result = builder.derive(
        "cumulative_sum",
        source=result,
        field_name="cumulative_sum",
        expression=window.sum(col("amount")).over(cumulative),
    )
    result = builder.derive(
        "moving_mean",
        source=result,
        field_name="moving_mean",
        expression=window.mean(col("amount")).over(moving),
    )
    plan = builder.output("result", result).build()

    inputs = {
        "orders": [
            {"customer_id": 1, "ordered_at": 10, "amount": 10.0},
            {"customer_id": 1, "ordered_at": 20, "amount": None},
            {"customer_id": 1, "ordered_at": 30, "amount": 30.0},
            {"customer_id": 2, "ordered_at": 5, "amount": 4.0},
            {"customer_id": 2, "ordered_at": 15, "amount": 6.0},
        ]
    }

    assert _duckdb_records(plan, inputs) == _pandas_records(plan, inputs)
