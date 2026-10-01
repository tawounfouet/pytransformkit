# ruff: noqa: E402

from __future__ import annotations

from decimal import Decimal

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

from pytransformkit import (
    EngineRegistry,
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit import functions as fn
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.domain.data.data_types import (
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.transformations.casting import CastPolicy
from pytransformkit.functions import col, lower
from pytransformkit.planning import TransformationCompiler


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def _pandas_records(
    plan: TransformationPlan,
    frame: object,
) -> list[dict[str, object]]:
    result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            "source": InputBinding.from_native(
                "source",
                frame,
                engine="pandas",
            )
        },
    )
    return result.output_handle.dataframe.to_dict(orient="records")


def _polars_records(
    plan: TransformationPlan,
    frame: object,
) -> list[dict[str, object]]:
    result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            "source": InputBinding.from_native(
                "source",
                frame,
                engine="polars",
            )
        },
    )
    return result.output_handle.frame.to_dicts()


def test_null_and_nan_are_distinct_logical_states_across_stable_engines() -> None:
    schema = Schema((Field("value", FloatType(), nullable=True),))
    builder = TransformationPlan.builder("null_nan")
    source = builder.input("source", schema=schema)
    with_null_flags = builder.derive(
        "is_null",
        source=source,
        field_name="is_null",
        expression=col("value").is_null(),
    )
    with_both_flags = builder.derive(
        "is_not_null",
        source=with_null_flags,
        field_name="is_not_null",
        expression=col("value").is_not_null(),
    )
    selected = builder.select(
        "flags",
        source=with_both_flags,
        columns=("is_null", "is_not_null"),
    )
    plan = builder.output("result", selected).build()

    pandas_frame = pd.DataFrame(
        {
            "value": pd.Series(
                [1.0, float("nan"), None],
                dtype="object",
            )
        }
    )
    polars_frame = pl.DataFrame({"value": [1.0, float("nan"), None]})

    expected = [
        {"is_null": False, "is_not_null": True},
        {"is_null": False, "is_not_null": True},
        {"is_null": True, "is_not_null": False},
    ]

    assert _pandas_records(plan, pandas_frame) == expected
    assert _polars_records(plan, polars_frame) == expected


def test_numeric_promotion_matches_between_pandas_and_polars() -> None:
    schema = Schema(
        (
            Field("whole", IntegerType(bits=64), nullable=False),
            Field("fraction", FloatType(bits=64), nullable=False),
        )
    )
    builder = TransformationPlan.builder("numeric_promotion")
    source = builder.input("source", schema=schema)
    derived = builder.derive(
        "total",
        source=source,
        field_name="total",
        expression=col("whole") + col("fraction"),
    )
    selected = builder.select("selected", source=derived, columns=("total",))
    plan = builder.output("result", selected).build()

    pandas = _pandas_records(
        plan,
        pd.DataFrame({"whole": [2, 3], "fraction": [0.5, 1.25]}),
    )
    polars = _polars_records(
        plan,
        pl.DataFrame({"whole": [2, 3], "fraction": [0.5, 1.25]}),
    )

    assert pandas == [{"total": 2.5}, {"total": 4.25}]
    assert polars == pandas
    logical = TransformationCompiler().compile(plan)
    assert isinstance(logical.output_schema.field("total").data_type, FloatType)


def test_decimal_cast_and_sum_match_between_pandas_and_polars() -> None:
    schema = Schema((Field("amount", StringType(), nullable=True),))
    builder = TransformationPlan.builder("decimal_conformance")
    source = builder.input("source", schema=schema)
    decimal_amounts = builder.cast(
        "decimal_amounts",
        source=source,
        field="amount",
        target_type=DecimalType(precision=10, scale=2),
        policy=CastPolicy.NULL,
    )
    totals = builder.aggregate(
        "totals",
        source=decimal_amounts,
        metrics={"total_amount": fn.sum(col("amount"))},
    )
    plan = builder.output("result", totals).build()

    pandas = _pandas_records(
        plan,
        pd.DataFrame({"amount": ["10.10", "2.35", "bad", None]}),
    )
    polars = _polars_records(
        plan,
        pl.DataFrame({"amount": ["10.10", "2.35", "bad", None]}),
    )

    assert pandas == [{"total_amount": Decimal("12.45")}]
    assert polars == pandas
    logical = TransformationCompiler().compile(plan)
    assert logical.output_schema.field("total_amount").data_type == DecimalType(10, 2)


def test_unicode_distinct_ordering_and_empty_data_match() -> None:
    schema = Schema(
        (
            Field("customer_id", IntegerType(), nullable=False),
            Field("name", StringType(), nullable=False),
        )
    )
    builder = TransformationPlan.builder("unicode_ordering")
    source = builder.input("source", schema=schema)
    normalized = builder.derive(
        "normalized",
        source=source,
        field_name="normalized_name",
        expression=lower(col("name")),
    )
    selected = builder.select(
        "selected",
        source=normalized,
        columns=("customer_id", "normalized_name"),
    )
    distinct = builder.distinct("distinct", source=selected)
    ordered = builder.sort(
        "ordered",
        source=distinct,
        by=("customer_id",),
    )
    plan = builder.output("result", ordered).build()

    records = [
        {"customer_id": 2, "name": "ÉLODIE"},
        {"customer_id": 1, "name": "BJÖRK"},
        {"customer_id": 2, "name": "ÉLODIE"},
        {"customer_id": 3, "name": "Zoë"},
    ]

    pandas = _pandas_records(plan, pd.DataFrame(records))
    polars = _polars_records(plan, pl.DataFrame(records))

    expected = [
        {"customer_id": 1, "normalized_name": "björk"},
        {"customer_id": 2, "normalized_name": "élodie"},
        {"customer_id": 3, "normalized_name": "zoë"},
    ]
    assert pandas == expected
    assert polars == expected

    empty_pandas = pd.DataFrame(
        {
            "customer_id": pd.Series([], dtype="int64"),
            "name": pd.Series([], dtype="string"),
        }
    )
    empty_polars = pl.DataFrame(
        schema={
            "customer_id": pl.Int64,
            "name": pl.String,
        }
    )

    assert _pandas_records(plan, empty_pandas) == []
    assert _polars_records(plan, empty_polars) == []
