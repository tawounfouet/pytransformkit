# ruff: noqa: E402

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
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
    ListType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.transformations.reshaping import PivotAggregation
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col
from pytransformkit.runtime import ExecutionMode


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def _normalize_value(value: object) -> object:
    if value is None:
        return None
    if value is pd.NA:
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return value.total_seconds()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _normalize(records: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized = [
        {key: _normalize_value(value) for key, value in record.items()}
        for record in records
    ]
    return sorted(normalized, key=repr)


def _execute_pandas(
    plan: TransformationPlan,
    records: list[dict[str, object]],
    input_name: str,
) -> list[dict[str, object]]:
    result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            input_name: InputBinding.from_native(
                input_name,
                pd.DataFrame(records),
                engine="pandas",
            )
        },
    )
    return _normalize(
        result.output_handle.dataframe.to_dict(orient="records")
    )


def _execute_polars(
    plan: TransformationPlan,
    records: list[dict[str, object]],
    input_name: str,
    *,
    mode: ExecutionMode = ExecutionMode.EAGER,
) -> list[dict[str, object]]:
    frame = pl.DataFrame(records)
    native = frame.lazy() if mode is ExecutionMode.LAZY else frame
    result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            input_name: InputBinding.from_native(
                input_name,
                native,
                engine="polars",
            )
        },
        mode=mode,
    )
    output = result.output_handle.frame
    if isinstance(output, pl.LazyFrame):
        output = output.collect()
    return _normalize(output.to_dicts())


def _nested_temporal_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField("city", StringType(), nullable=False),
                        StructField("score", IntegerType(), nullable=True),
                    )
                ),
                nullable=False,
            ),
            Field(
                "event_at",
                TimestampType(unit="us", timezone="UTC"),
                nullable=False,
            ),
            Field(
                "previous_at",
                TimestampType(unit="us", timezone="UTC"),
                nullable=False,
            ),
        )
    )


def _nested_temporal_records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 1,
            "profile": {"city": "Paris", "score": 10},
            "event_at": datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc),
            "previous_at": datetime(2026, 9, 29, 7, 0, tzinfo=timezone.utc),
        },
        {
            "customer_id": 2,
            "profile": {"city": "Lyon", "score": None},
            "event_at": datetime(2026, 10, 1, 18, 15, tzinfo=timezone.utc),
            "previous_at": datetime(2026, 10, 1, 18, 0, tzinfo=timezone.utc),
        },
    ]


def _nested_temporal_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("nested_temporal")
    source = builder.input("events", schema=_nested_temporal_schema())
    result = builder.derive(
        "city",
        source=source,
        field_name="city",
        expression=col("profile.city"),
    )
    result = builder.derive(
        "event_year",
        source=result,
        field_name="event_year",
        expression=fn.year(col("event_at")),
    )
    result = builder.derive(
        "event_date",
        source=result,
        field_name="event_date",
        expression=fn.to_date(col("event_at")),
    )
    result = builder.derive(
        "normalized_at",
        source=result,
        field_name="normalized_at",
        expression=fn.normalize_timestamp(
            col("event_at"),
            timezone="UTC",
            unit="us",
        ),
    )
    result = builder.derive(
        "paris_at",
        source=result,
        field_name="paris_at",
        expression=fn.convert_timezone(
            col("event_at"),
            "Europe/Paris",
        ),
    )
    result = builder.derive(
        "elapsed",
        source=result,
        field_name="elapsed",
        expression=fn.duration_between(
            col("previous_at"),
            col("event_at"),
            unit="s",
        ),
    )
    return builder.output("result", result).build()


def test_nested_and_temporal_semantics_match_pandas_and_polars() -> None:
    plan = _nested_temporal_plan()
    records = _nested_temporal_records()

    pandas_records = _execute_pandas(plan, records, "events")
    polars_records = _execute_polars(plan, records, "events")

    assert pandas_records == polars_records
    assert [record["city"] for record in pandas_records] == ["Paris", "Lyon"]
    assert [record["event_year"] for record in pandas_records] == [2026, 2026]
    assert [record["elapsed"] for record in pandas_records] == [5400.0, 900.0]


def _reshape_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("category", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
            Field("q1", FloatType(), nullable=True),
            Field("q2", FloatType(), nullable=True),
            Field(
                "tags",
                ListType(StringType(), element_nullable=False),
                nullable=False,
            ),
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField("city", StringType(), nullable=False),
                        StructField("score", IntegerType(), nullable=True),
                    )
                ),
                nullable=False,
            ),
        )
    )


def _reshape_records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 1,
            "category": "A",
            "amount": 10.0,
            "q1": 10.0,
            "q2": 15.0,
            "tags": ["gold", "active"],
            "profile": {"city": "Paris", "score": 10},
        },
        {
            "customer_id": 1,
            "category": "A",
            "amount": 5.0,
            "q1": 10.0,
            "q2": 15.0,
            "tags": ["gold"],
            "profile": {"city": "Paris", "score": 10},
        },
        {
            "customer_id": 1,
            "category": "B",
            "amount": 20.0,
            "q1": 10.0,
            "q2": 15.0,
            "tags": ["active"],
            "profile": {"city": "Paris", "score": 10},
        },
        {
            "customer_id": 2,
            "category": "B",
            "amount": 7.0,
            "q1": 7.0,
            "q2": 9.0,
            "tags": ["new", "active"],
            "profile": {"city": "Lyon", "score": None},
        },
    ]


def _pivot_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("pivot")
    source = builder.input("source", schema=_reshape_schema())
    result = builder.pivot(
        "pivoted",
        source=source,
        index=("customer_id",),
        columns="category",
        values="amount",
        categories=("A", "B", "C"),
        aggregation=PivotAggregation.SUM,
    )
    return builder.output("result", result).build()


def _unpivot_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("unpivot")
    source = builder.input("source", schema=_reshape_schema())
    result = builder.unpivot(
        "unpivoted",
        source=source,
        id_vars=("customer_id",),
        value_vars=("q1", "q2"),
        variable_name="quarter",
        value_name="revenue",
    )
    return builder.output("result", result).build()


def _explode_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("explode")
    source = builder.input("source", schema=_reshape_schema())
    result = builder.explode(
        "exploded",
        source=source,
        field="tags",
    )
    return builder.output("result", result).build()


def _flatten_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("flatten")
    source = builder.input("source", schema=_reshape_schema())
    result = builder.flatten(
        "flattened",
        source=source,
        field="profile",
    )
    return builder.output("result", result).build()


@pytest.mark.parametrize(
    "plan_factory",
    [
        _pivot_plan,
        _unpivot_plan,
        _explode_plan,
        _flatten_plan,
    ],
)
def test_reshaping_semantics_match_pandas_and_polars(
    plan_factory: object,
) -> None:
    plan = plan_factory()  # type: ignore[operator]
    records = _reshape_records()

    pandas_records = _execute_pandas(plan, records, "source")
    polars_records = _execute_polars(plan, records, "source")

    assert pandas_records == polars_records


@pytest.mark.parametrize(
    "plan_factory",
    [
        _pivot_plan,
        _unpivot_plan,
        _explode_plan,
        _flatten_plan,
    ],
)
def test_polars_lazy_reshaping_matches_eager(
    plan_factory: object,
) -> None:
    plan = plan_factory()  # type: ignore[operator]
    records = _reshape_records()

    eager = _execute_polars(plan, records, "source")
    lazy = _execute_polars(
        plan,
        records,
        "source",
        mode=ExecutionMode.LAZY,
    )

    assert lazy == eager


def test_pivot_uses_declared_categories_and_null_for_missing_sum() -> None:
    records = _execute_pandas(
        _pivot_plan(),
        _reshape_records(),
        "source",
    )

    assert records == [
        {"customer_id": 1, "A": 15.0, "B": 20.0, "C": None},
        {"customer_id": 2, "A": None, "B": 7.0, "C": None},
    ]
