# ruff: noqa: E402

from __future__ import annotations

import pytest

pa = pytest.importorskip("pyarrow")

from pytransformkit.application.execution import ExecutionContext, ExecutionMode
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability
from pytransformkit.domain.pipelines import Pipeline, PipelinePlanner
from pytransformkit.domain.transformations.filtering import DistinctTransformation
from pytransformkit.errors import AdapterError, UnsupportedEngineCapabilityError
from pytransformkit.functions import col, lower, trim
from pytransformkit.infrastructure.engines.pyarrow import (
    PyArrowAdapter,
    PyArrowDatasetHandle,
)


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def _execute(pipeline: Pipeline, value):
    adapter = PyArrowAdapter()
    plan = PipelinePlanner().plan(pipeline)
    return adapter.execute(
        plan,
        PyArrowDatasetHandle(value),
        ExecutionContext(mode=ExecutionMode.EAGER),
    )


def test_descriptor_advertises_only_qualified_lot18_capabilities() -> None:
    descriptor = PyArrowAdapter().descriptor

    assert descriptor.id == "pyarrow"
    assert descriptor.supports(EngineCapability.SELECT)
    assert descriptor.supports(EngineCapability.FILTER)
    assert descriptor.supports(EngineCapability.DERIVE)
    assert descriptor.supports(EngineCapability.LAZY) is False
    assert descriptor.supports(EngineCapability.DISTINCT) is False
    assert descriptor.supports(EngineCapability.AGGREGATE) is False


def test_arrow_table_executes_supported_pipeline_end_to_end() -> None:
    table = pa.table(
        {
            "customer_id": [2, 1, 3],
            "email": [" B@EXAMPLE.COM ", " A@EXAMPLE.COM ", None],
            "status": ["ACTIVE", "ACTIVE", "INACTIVE"],
        }
    )
    pipeline = (
        Pipeline.create("customers", _schema())
        .select("customer_id", "email", "status")
        .rename({"status": "state"})
        .filter(col("customer_id") > 0)
        .derive("normalized_email", lower(trim(col("email"))))
        .sort("customer_id")
        .drop("email")
        .limit(10)
    )

    result = _execute(pipeline, table)
    output = result.output_handle.table

    assert output.column_names == [
        "customer_id",
        "state",
        "normalized_email",
    ]
    assert output.to_pydict() == {
        "customer_id": [1, 2, 3],
        "state": ["ACTIVE", "ACTIVE", "INACTIVE"],
        "normalized_email": ["a@example.com", "b@example.com", None],
    }
    assert result.output_schema.names() == tuple(output.column_names)


def test_record_batch_is_a_supported_input_handle() -> None:
    batch = pa.record_batch(
        [
            pa.array([1, 2], type=pa.int64()),
            pa.array(["A", "B"], type=pa.string()),
            pa.array(["ACTIVE", "ACTIVE"], type=pa.string()),
        ],
        names=["customer_id", "email", "status"],
    )

    result = _execute(Pipeline.create("customers", _schema()).limit(1), batch)

    assert result.output_handle.table.to_pydict()["customer_id"] == [1]


def test_unsupported_capability_fails_before_arrow_execution() -> None:
    table = pa.table(
        {
            "customer_id": [1, 1],
            "email": ["a", "a"],
            "status": ["ACTIVE", "ACTIVE"],
        }
    )
    pipeline = Pipeline.create("customers", _schema()).then(
        DistinctTransformation()
    )

    with pytest.raises(UnsupportedEngineCapabilityError):
        _execute(pipeline, table)


def test_arrow_adapter_rejects_lazy_mode_explicitly() -> None:
    plan = PipelinePlanner().plan(Pipeline.create("customers", _schema()))
    table = pa.table(
        {
            "customer_id": [1],
            "email": ["a"],
            "status": ["ACTIVE"],
        }
    )

    with pytest.raises(AdapterError, match="EAGER"):
        PyArrowAdapter().execute(
            plan,
            PyArrowDatasetHandle(table),
            ExecutionContext(mode=ExecutionMode.LAZY),
        )
