# ruff: noqa: E402

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

from pytransformkit import (
    EngineRegistry,
    ExecutionContext,
    ExecutionMode,
    RunPipelineService,
)
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines import Pipeline
from pytransformkit.errors import UnsupportedEngineCapabilityError
from pytransformkit.functions import col, lower
from pytransformkit.infrastructure.engines.pandas import (
    PandasAdapter,
    PandasDatasetHandle,
)


def test_application_service_executes_pandas_without_core_coupling() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [2, 1],
            "email": ["B@EXAMPLE.COM", "A@EXAMPLE.COM"],
        }
    )
    schema = Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=False),
        )
    )
    pipeline = (
        Pipeline.create("customers", schema)
        .filter(col("customer_id") > 0)
        .derive("normalized_email", lower(col("email")))
        .select("customer_id", "normalized_email")
    )

    registry = EngineRegistry()
    registry.register(PandasAdapter())

    result = RunPipelineService(registry).run(
        pipeline,
        PandasDatasetHandle(dataframe),
        engine_id="pandas",
    )

    assert result.engine.id == "pandas"
    assert result.output_schema.names() == (
        "customer_id",
        "normalized_email",
    )
    assert result.output_handle.dataframe.columns.tolist() == [
        "customer_id",
        "normalized_email",
    ]
    assert result.output_handle.dataframe["normalized_email"].tolist() == [
        "b@example.com",
        "a@example.com",
    ]
    assert result.logical_plan.pipeline_name == "customers"


def test_application_service_rejects_pandas_lazy_before_execution() -> None:
    dataframe = pd.DataFrame({"customer_id": [1]})
    schema = Schema(
        fields=(Field("customer_id", IntegerType(), nullable=False),)
    )
    pipeline = Pipeline.create("customers", schema)

    registry = EngineRegistry()
    registry.register(PandasAdapter())

    with pytest.raises(
        UnsupportedEngineCapabilityError,
        match="lazy",
    ):
        RunPipelineService(registry).run(
            pipeline,
            PandasDatasetHandle(dataframe),
            engine_id="pandas",
            context=ExecutionContext(mode=ExecutionMode.LAZY),
        )
