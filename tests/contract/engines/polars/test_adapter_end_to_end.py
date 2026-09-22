# ruff: noqa: E402

from __future__ import annotations

import pytest

pl = pytest.importorskip("polars")

from pytransformkit import EngineRegistry, RunPipelineService
from pytransformkit.application.execution import (
    ExecutionContext,
    ExecutionMode,
)
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability
from pytransformkit.domain.pipelines import Pipeline, PipelinePlanner
from pytransformkit.domain.transformations.casting import CastPolicy
from pytransformkit.domain.transformations.sorting import SortDirection
from pytransformkit.functions import col, lower, trim
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


def _frame():
    return pl.DataFrame(
        {
            "customer_id": [2, 1, 2, 3],
            "email": [
                " B@EXAMPLE.COM ",
                " A@EXAMPLE.COM ",
                " B2@EXAMPLE.COM ",
                None,
            ],
            "status": ["ACTIVE", "ACTIVE", "ACTIVE", "INACTIVE"],
            "amount": ["20.5", "10.0", "bad", "30.0"],
        }
    )


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
        .limit(10)
    )


def test_descriptor_advertises_eager_and_lazy_capabilities() -> None:
    descriptor = PolarsAdapter().descriptor

    assert descriptor.id == "polars"
    assert descriptor.supports(EngineCapability.SELECT)
    assert descriptor.supports(EngineCapability.DEDUPLICATE)
    assert descriptor.supports(EngineCapability.LAZY)


def test_polars_adapter_executes_eager_pipeline() -> None:
    plan = PipelinePlanner().plan(_pipeline())

    result = PolarsAdapter().execute(
        plan,
        PolarsDatasetHandle(_frame()),
        ExecutionContext(mode=ExecutionMode.EAGER),
    )
    output = result.output_handle.frame

    assert isinstance(output, pl.DataFrame)
    assert output.columns == [
        "customer_id",
        "state",
        "amount",
        "normalized_email",
    ]
    assert output["customer_id"].to_list() == [1, 2, 3]
    assert output["normalized_email"].to_list() == [
        "a@example.com",
        "b@example.com",
        None,
    ]
    assert output["amount"].to_list() == [10.0, 20.5, 30.0]
    assert result.output_schema.names() == tuple(output.columns)


def test_polars_adapter_keeps_lazy_execution_lazy() -> None:
    plan = PipelinePlanner().plan(_pipeline())

    result = PolarsAdapter().execute(
        plan,
        PolarsDatasetHandle(_frame().lazy()),
        ExecutionContext(mode=ExecutionMode.LAZY),
    )

    assert isinstance(result.output_handle.frame, pl.LazyFrame)
    output = result.output_handle.frame.collect()
    assert output["customer_id"].to_list() == [1, 2, 3]


def test_application_service_executes_polars_explicitly() -> None:
    registry = EngineRegistry()
    registry.register(PolarsAdapter())

    result = RunPipelineService(registry).run(
        _pipeline(),
        PolarsDatasetHandle(_frame()),
        engine_id="polars",
    )

    assert result.engine.id == "polars"
    assert isinstance(result.output_handle.frame, pl.DataFrame)
    assert result.output_schema.names() == (
        "customer_id",
        "state",
        "amount",
        "normalized_email",
    )


def test_application_service_executes_polars_lazy_explicitly() -> None:
    registry = EngineRegistry()
    registry.register(PolarsAdapter())

    result = RunPipelineService(registry).run(
        _pipeline(),
        PolarsDatasetHandle(_frame()),
        engine_id="polars",
        context=ExecutionContext(mode=ExecutionMode.LAZY),
    )

    assert isinstance(result.output_handle.frame, pl.LazyFrame)
