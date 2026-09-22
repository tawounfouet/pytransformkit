# ruff: noqa: E402

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

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
from pytransformkit.domain.transformations.sorting import (
    NullOrder,
    SortDirection,
)
from pytransformkit.errors import AdapterError
from pytransformkit.functions import col, lower, trim
from pytransformkit.infrastructure.engines.pandas import (
    PandasAdapter,
    PandasDatasetHandle,
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


def _execute(pipeline: Pipeline, dataframe):
    adapter = PandasAdapter()
    plan = PipelinePlanner().plan(pipeline)
    return adapter.execute(
        plan,
        PandasDatasetHandle(dataframe),
        ExecutionContext(mode=ExecutionMode.EAGER),
    )


def test_descriptor_advertises_initial_mvp_capabilities() -> None:
    descriptor = PandasAdapter().descriptor

    assert descriptor.id == "pandas"
    assert descriptor.supports(EngineCapability.SELECT)
    assert descriptor.supports(EngineCapability.DEDUPLICATE)
    assert descriptor.supports(EngineCapability.LAZY) is False


def test_reference_adapter_executes_logical_pipeline_end_to_end() -> None:
    dataframe = pd.DataFrame(
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
    pipeline = (
        Pipeline.create("customers", _schema())
        .select("customer_id", "email", "status", "amount")
        .rename({"status": "state"})
        .filter(col("customer_id") > 0)
        .cast("amount", FloatType(), policy=CastPolicy.NULL)
        .derive(
            "normalized_email",
            lower(trim(col("email"))),
        )
        .sort("customer_id", direction=SortDirection.ASC)
        .deduplicate(keys=("customer_id",))
        .drop("email")
        .limit(10)
    )

    result = _execute(pipeline, dataframe)
    output = result.output_handle.dataframe.reset_index(drop=True)

    assert output.columns.tolist() == [
        "customer_id",
        "state",
        "amount",
        "normalized_email",
    ]
    assert output["customer_id"].tolist() == [1, 2, 3]
    assert output["normalized_email"].iloc[0] == "a@example.com"
    assert output["normalized_email"].iloc[1] == "b@example.com"
    assert pd.isna(output["normalized_email"].iloc[2])
    assert result.output_schema.names() == tuple(output.columns)


def test_filter_drops_unknown_null_predicate_results() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "email": ["a", None],
            "status": ["ACTIVE", "ACTIVE"],
            "amount": ["1", "2"],
        }
    )
    pipeline = Pipeline.create("customers", _schema()).filter(
        col("email") == None  # noqa: E711
    )

    result = _execute(pipeline, dataframe)

    assert result.output_handle.dataframe.empty


def test_adapter_does_not_mutate_input_dataframe() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1],
            "email": [" A@EXAMPLE.COM "],
            "status": ["ACTIVE"],
            "amount": ["10"],
        }
    )
    original = dataframe.copy(deep=True)
    pipeline = (
        Pipeline.create("customers", _schema())
        .derive("normalized_email", lower(trim(col("email"))))
        .drop("email")
    )

    _execute(pipeline, dataframe)

    pd.testing.assert_frame_equal(dataframe, original)


def test_adapter_rejects_lazy_execution() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": [1],
            "email": ["a"],
            "status": ["ACTIVE"],
            "amount": ["1"],
        }
    )
    plan = PipelinePlanner().plan(
        Pipeline.create("customers", _schema())
    )

    with pytest.raises(AdapterError, match="LAZY"):
        PandasAdapter().execute(
            plan,
            PandasDatasetHandle(dataframe),
            ExecutionContext(mode=ExecutionMode.LAZY),
        )


def test_adapter_rejects_mixed_per_key_null_ordering() -> None:
    from pytransformkit.domain.data.field_path import FieldPath
    from pytransformkit.domain.transformations.sorting import (
        SortKey,
        SortTransformation,
    )

    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "email": ["a", None],
            "status": ["ACTIVE", "ACTIVE"],
            "amount": ["1", "2"],
        }
    )
    pipeline = Pipeline.create("customers", _schema()).then(
        SortTransformation(
            keys=(
                SortKey(
                    FieldPath.of("customer_id"),
                    nulls=NullOrder.FIRST,
                ),
                SortKey(
                    FieldPath.of("email"),
                    nulls=NullOrder.LAST,
                ),
            )
        )
    )

    with pytest.raises(AdapterError, match="mixed"):
        _execute(pipeline, dataframe)
