# ruff: noqa: E402

from __future__ import annotations

import math

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

from pytransformkit import EngineRegistry, RunPipelineService
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines import Pipeline
from pytransformkit.domain.transformations.casting import CastPolicy
from pytransformkit.domain.transformations.sorting import SortDirection
from pytransformkit.functions import col, lower, trim
from pytransformkit.infrastructure.engines.pandas import (
    PandasAdapter,
    PandasDatasetHandle,
)
from pytransformkit.infrastructure.engines.polars import (
    PolarsAdapter,
    PolarsDatasetHandle,
)


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", StringType(), nullable=True),
        )
    )


def _records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 2,
            "email": " B@EXAMPLE.COM ",
            "status": "ACTIVE",
            "amount": "20.5",
        },
        {
            "customer_id": 1,
            "email": " A@EXAMPLE.COM ",
            "status": "ACTIVE",
            "amount": "10.0",
        },
        {
            "customer_id": 2,
            "email": " B2@EXAMPLE.COM ",
            "status": "ACTIVE",
            "amount": "bad",
        },
        {
            "customer_id": 3,
            "email": None,
            "status": "INACTIVE",
            "amount": "30.0",
        },
    ]


def _pipeline() -> Pipeline:
    return (
        Pipeline.create("customers", _schema())
        .select("customer_id", "email", "status", "amount")
        .rename({"status": "state"})
        .filter(col("customer_id") > 0)
        .cast("amount", FloatType(), policy=CastPolicy.NULL)
        .derive("normalized_email", lower(trim(col("email"))))
        .sort("customer_id", direction=SortDirection.ASC)
        .deduplicate(keys=("customer_id",))
        .drop("email")
    )


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


def _normalize_records(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            key: _normalize_value(value)
            for key, value in record.items()
        }
        for record in records
    ]


def test_same_pipeline_produces_same_pandas_and_polars_result() -> None:
    pipeline = _pipeline()

    pandas_registry = EngineRegistry()
    pandas_registry.register(PandasAdapter())
    pandas_result = RunPipelineService(pandas_registry).run(
        pipeline,
        PandasDatasetHandle(pd.DataFrame(_records())),
        engine_id="pandas",
    )

    polars_registry = EngineRegistry()
    polars_registry.register(PolarsAdapter())
    polars_result = RunPipelineService(polars_registry).run(
        pipeline,
        PolarsDatasetHandle(pl.DataFrame(_records())),
        engine_id="polars",
    )

    pandas_records = _normalize_records(
        pandas_result.output_handle.dataframe.to_dict(
            orient="records"
        )
    )
    polars_records = _normalize_records(
        polars_result.output_handle.frame.to_dicts()
    )

    assert pandas_result.logical_plan.output_schema == (
        polars_result.logical_plan.output_schema
    )
    assert pandas_records == polars_records


def test_null_comparison_filter_semantics_match_across_engines() -> None:
    pipeline = Pipeline.create("customers", _schema()).filter(
        col("email") == None  # noqa: E711
    )

    pandas_registry = EngineRegistry()
    pandas_registry.register(PandasAdapter())
    pandas_result = RunPipelineService(pandas_registry).run(
        pipeline,
        PandasDatasetHandle(pd.DataFrame(_records())),
        engine_id="pandas",
    )

    polars_registry = EngineRegistry()
    polars_registry.register(PolarsAdapter())
    polars_result = RunPipelineService(polars_registry).run(
        pipeline,
        PolarsDatasetHandle(pl.DataFrame(_records())),
        engine_id="polars",
    )

    assert pandas_result.output_handle.dataframe.empty
    assert polars_result.output_handle.frame.height == 0
