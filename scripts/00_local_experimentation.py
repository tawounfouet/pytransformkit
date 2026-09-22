"""Local end-to-end experimentation with PyTransformKit.

Run from the repository root after installing the development and engine extras:

    pip install -e ".[dev,pandas,polars]"
    python "scripts/00_local_experimentation.py"
"""

from __future__ import annotations

import pandas as pd
import polars as pl

from pytransformkit import (
    EngineRegistry,
    ExecutionContext,
    ExecutionMode,
    RunPipelineService,
)
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines import Pipeline, PipelinePlanner
from pytransformkit.functions import col, lower, trim
from pytransformkit.infrastructure.engines.pandas import (
    PandasAdapter,
    PandasDatasetHandle,
)
from pytransformkit.infrastructure.engines.polars import (
    PolarsAdapter,
    PolarsDatasetHandle,
)

RECORDS = [
    {
        "customer_id": 1,
        "email": " JOHN@EXAMPLE.COM ",
        "status": "ACTIVE",
    },
    {
        "customer_id": 2,
        "email": " ALICE@EXAMPLE.COM ",
        "status": "ACTIVE",
    },
    {
        "customer_id": 3,
        "email": None,
        "status": "INACTIVE",
    },
    {
        "customer_id": 4,
        "email": " BOB@EXAMPLE.COM ",
        "status": "ACTIVE",
    },
]


def build_schema() -> Schema:
    """Create the logical, engine-independent input Schema."""
    return Schema(
        fields=(
            Field(
                "customer_id",
                IntegerType(),
                nullable=False,
            ),
            Field(
                "email",
                StringType(),
                nullable=True,
            ),
            Field(
                "status",
                StringType(),
                nullable=False,
            ),
        )
    )


def build_pipeline(schema: Schema) -> Pipeline:
    """Build one Pipeline that can execute on multiple engines."""
    return (
        Pipeline.create(
            "customers",
            schema,
        )
        .filter(col("status") == "ACTIVE")
        .derive(
            "normalized_email",
            lower(trim(col("email"))),
        )
        .select(
            "customer_id",
            "normalized_email",
        )
    )


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    schema = build_schema()
    pipeline = build_pipeline(schema)

    pandas_df = pd.DataFrame(RECORDS)
    polars_df = pl.DataFrame(RECORDS)

    print_section("1. Logical Schema")
    print(schema)

    print_section("2. Pipeline")
    print(pipeline)

    print_section("3. LogicalPlan — no physical data execution")
    plan = PipelinePlanner().plan(pipeline)
    print("Pipeline:", plan.pipeline_name)
    print("Output Schema:", plan.output_schema.names())
    print("Node kinds:", [node.kind.value for node in plan.nodes])

    registry = EngineRegistry()
    registry.register(PandasAdapter())
    registry.register(PolarsAdapter())
    service = RunPipelineService(registry)

    print_section("4. Pandas execution")
    pandas_result = service.run(
        pipeline,
        PandasDatasetHandle(pandas_df),
        engine_id="pandas",
    )
    pandas_output = pandas_result.output_handle.dataframe
    print(pandas_output)
    print("Execution id:", pandas_result.execution_id)
    print("Engine:", pandas_result.engine.id)
    print("Output Schema:", pandas_result.output_schema.names())

    print_section("5. Polars eager execution")
    polars_result = service.run(
        pipeline,
        PolarsDatasetHandle(polars_df),
        engine_id="polars",
    )
    polars_output = polars_result.output_handle.frame
    print(polars_output)
    print("Execution id:", polars_result.execution_id)
    print("Engine:", polars_result.engine.id)
    print("Output Schema:", polars_result.output_schema.names())

    print_section("6. Pandas / Polars semantic comparison")
    pandas_records = pandas_output.to_dict(orient="records")
    polars_records = polars_output.to_dicts()

    print("Pandas records:", pandas_records)
    print("Polars records:", polars_records)
    print("Equivalent:", pandas_records == polars_records)

    if pandas_records != polars_records:
        raise AssertionError(
            "Pandas and Polars produced different logical results."
        )

    print_section("7. Polars lazy execution")
    lazy_result = service.run(
        pipeline,
        PolarsDatasetHandle(polars_df.lazy()),
        engine_id="polars",
        context=ExecutionContext(
            mode=ExecutionMode.LAZY,
        ),
    )
    lazy_frame = lazy_result.output_handle.frame

    print("Physical result type:", type(lazy_frame))
    print("Lazy plan:")
    print(lazy_frame)

    print("Collected result:")
    print(lazy_frame.collect())

    print_section("Experiment completed successfully")


if __name__ == "__main__":
    main()
