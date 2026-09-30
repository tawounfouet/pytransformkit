# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pd = pytest.importorskip("pandas")

from pytransformkit import (
    InputBinding,
    OutputBinding,
    ResourceReference,
    RetrySafety,
    TransformationPlan,
    TransformationRuntime,
    WriteMode,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.application.io import ResourceIORegistry, WriteResult
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.resources import ResourceFormat, WriteStatus
from pytransformkit.engines import EngineRegistry
from pytransformkit.errors import UnknownOutcomeExecutionError
from pytransformkit.functions import col
from pytransformkit.readers import LocalFileReader
from pytransformkit.writers import LocalFileWriter


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=True),
            Field("status", StringType(), nullable=True),
        )
    )


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("resource_runtime")
    source = builder.input("customers", schema=_schema())
    active = builder.filter(
        "active",
        source=source,
        where=col("status") == "ACTIVE",
    )
    return builder.output("result", active).build()


def _engine_registry() -> EngineRegistry:
    engines = EngineRegistry()
    engines.register(PandasEngineAdapter())
    return engines


def test_runtime_reads_resource_and_materializes_output_with_resource_lineage(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customers.csv"
    input_path.write_text(
        "customer_id,status\n1,ACTIVE\n2,INACTIVE\n",
        encoding="utf-8",
    )

    io = ResourceIORegistry()
    io.register_reader(LocalFileReader(tmp_path))
    io.register_writer(LocalFileWriter(tmp_path))

    input_resource = ResourceReference(
        scheme="file",
        locator="customers.csv",
        media_type="text/csv",
    )
    output_resource = ResourceReference(
        scheme="file",
        locator="active.parquet",
        media_type="application/vnd.apache.parquet",
    )

    result = TransformationRuntime(
        engines=_engine_registry(),
        resources=io,
    ).execute(
        _plan(),
        engine="pandas",
        inputs={
            "customers": InputBinding.from_resource(
                "customers",
                input_resource,
            )
        },
        outputs={
            "result": OutputBinding.to_resource(
                "result",
                output_resource,
                mode=WriteMode.CREATE_NEW,
                retry_safety=RetrySafety.SAFE,
            )
        },
    )

    assert result.output_handle.dataframe.to_dict(orient="records") == [
        {"customer_id": 1, "status": "ACTIVE"}
    ]
    assert len(result.writes) == 1
    assert result.writes[0].status is WriteStatus.SUCCEEDED
    assert (tmp_path / "active.parquet").exists()

    resource_links = {(link.name, link.resource) for link in result.lineage.resources}
    assert ("customers", input_resource) in resource_links
    assert ("result", output_resource) in resource_links


class _UnknownOutcomeWriter:
    @property
    def schemes(self) -> frozenset[str]:
        return frozenset({"file"})

    def write(self, request):  # type: ignore[no-untyped-def]
        return WriteResult(
            resource=request.resource,
            resource_format=ResourceFormat.PARQUET,
            status=WriteStatus.UNKNOWN_OUTCOME,
            retry_safety=RetrySafety.REQUIRES_RECONCILIATION,
        )


def test_runtime_preserves_unknown_write_outcome_as_reconciliation_required(
    tmp_path: Path,
) -> None:
    io = ResourceIORegistry()
    io.register_writer(_UnknownOutcomeWriter())

    runtime = TransformationRuntime(
        engines=_engine_registry(),
        resources=io,
    )

    with pytest.raises(UnknownOutcomeExecutionError) as captured:
        runtime.execute(
            _plan(),
            engine="pandas",
            inputs={
                "customers": InputBinding.from_native(
                    "customers",
                    pd.DataFrame(
                        {
                            "customer_id": [1],
                            "status": ["ACTIVE"],
                        }
                    ),
                    engine="pandas",
                )
            },
            outputs={
                "result": OutputBinding.to_resource(
                    "result",
                    ResourceReference(
                        scheme="file",
                        locator="uncertain.parquet",
                    ),
                    mode=WriteMode.REPLACE,
                    retry_safety=RetrySafety.UNKNOWN,
                )
            },
        )

    error = captured.value
    assert error.execution is not None
    assert error.execution.status.value == "unknown_outcome"
    assert error.failure_evidence is not None
    assert error.failure_evidence.uncertainty.value == "requires_reconciliation"
