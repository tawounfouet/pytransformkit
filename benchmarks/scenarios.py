"""Deterministic benchmark scenarios for LOT-25 performance qualification."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from benchmarks.harness import ScenarioOutcome, metric_pairs
from pytransformkit import (
    EngineRegistry,
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit import functions as fn
from pytransformkit.adapters.duckdb import DuckDBEngineAdapter
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.adapters.pyarrow import PyArrowInterchange
from pytransformkit.application.execution import ExecutionContext, ExecutionMode
from pytransformkit.application.io import ReadRequest
from pytransformkit.domain.data.data_types import FloatType, IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.lineage import LineageAnalyzer
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.runtime import RuntimeEvent, RuntimeMetric, RuntimeTraceSpan
from pytransformkit.functions import col, lower, trim
from pytransformkit.infrastructure.engines.duckdb.expressions import (
    DuckDBExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pandas.expressions import (
    PandasExpressionCompiler,
)
from pytransformkit.infrastructure.engines.polars.expressions import (
    PolarsExpressionCompiler,
)
from pytransformkit.planning import LogicalOptimizer, TransformationCompiler
from pytransformkit.readers import LocalFileReader


class RecordingTelemetrySink:
    """Minimal in-memory sink used to quantify observability overhead."""

    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []
        self.metrics: list[RuntimeMetric] = []
        self.spans: list[RuntimeTraceSpan] = []

    def emit_event(self, event: RuntimeEvent) -> None:
        self.events.append(event)

    def record_metric(self, metric: RuntimeMetric) -> None:
        self.metrics.append(metric)

    def record_span(self, span: RuntimeTraceSpan) -> None:
        self.spans.append(span)


class PerformanceScenarios:
    """Own deterministic fixtures and benchmark callables for one run."""

    def __init__(self, *, row_count: int, root: Path) -> None:
        if row_count < 1_000:
            raise ValueError("row_count must be at least 1000.")
        self.row_count = row_count
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

        payload = _payload(row_count)
        self.pandas_frame = pd.DataFrame(payload).astype(
            {
                "segment": "string",
                "status": "string",
                "email": "string",
            }
        )
        self.polars_frame = pl.DataFrame(payload)
        self.arrow_table = pa.table(payload)

        self.schema = _schema()
        self.plan = _reference_plan(self.schema)
        self.row_plan = _row_preserving_plan(self.schema)
        self.logical_plan = TransformationCompiler().compile(self.plan)
        self.row_logical_plan = TransformationCompiler().compile(self.row_plan)
        self.expression = lower(trim(col("email")))

        self.pandas_adapter = PandasEngineAdapter()
        self.polars_adapter = PolarsEngineAdapter()
        self.pandas_runtime = _runtime(self.pandas_adapter)
        self.polars_runtime = _runtime(self.polars_adapter)

        self.pandas_handle = self.pandas_adapter.bind_native(self.pandas_frame)
        self.polars_handle = self.polars_adapter.bind_native(self.polars_frame)

        self.parquet_path = self.root / "performance.parquet"
        pq.write_table(self.arrow_table, self.parquet_path)
        self.reader = LocalFileReader(self.root)
        self.parquet_resource = ResourceReference(
            scheme="file",
            locator=self.parquet_path.name,
            media_type="application/vnd.apache.parquet",
        )

    def scenarios(self) -> tuple[tuple[str, Callable[[], object]], ...]:
        """Return the complete deterministic LOT-25 benchmark suite."""
        return (
            ("planning_compile", self.planning_compile),
            ("planning_optimize", self.planning_optimize),
            ("expression_duckdb_compile", self.expression_duckdb_compile),
            ("expression_polars_compile", self.expression_polars_compile),
            ("expression_pandas_compile_eval", self.expression_pandas_compile_eval),
            ("pandas_adapter_execution", self.pandas_adapter_execution),
            ("pandas_runtime_execution", self.pandas_runtime_execution),
            ("pandas_memory_amplification", self.pandas_memory_amplification),
            ("polars_eager_execution", self.polars_eager_execution),
            ("polars_lazy_execution", self.polars_lazy_execution),
            ("polars_memory_amplification", self.polars_memory_amplification),
            ("pandas_to_arrow", self.pandas_to_arrow),
            ("arrow_to_pandas", self.arrow_to_pandas),
            ("polars_to_arrow", self.polars_to_arrow),
            ("arrow_to_polars", self.arrow_to_polars),
            ("duckdb_eager_execution", self.duckdb_eager_execution),
            ("duckdb_lazy_dispatch", self.duckdb_lazy_dispatch),
            ("duckdb_lazy_materialized", self.duckdb_lazy_materialized),
            ("parquet_full_scan", self.parquet_full_scan),
            ("parquet_pushdown", self.parquet_pushdown),
            ("lineage_analysis", self.lineage_analysis),
            ("runtime_null_telemetry", self.runtime_null_telemetry),
            ("runtime_recording_telemetry", self.runtime_recording_telemetry),
        )

    def planning_compile(self) -> ScenarioOutcome:
        logical = TransformationCompiler().compile(self.plan)
        return ScenarioOutcome(
            value=logical,
            metrics=metric_pairs({"logical_nodes": len(logical.nodes)}),
        )

    def planning_optimize(self) -> ScenarioOutcome:
        optimized = LogicalOptimizer().optimize(self.logical_plan)
        return ScenarioOutcome(
            value=optimized,
            metrics=metric_pairs(
                {
                    "optimizer_passes": optimized.report.passes,
                    "optimizer_applications": len(optimized.report.applications),
                }
            ),
        )

    def expression_duckdb_compile(self) -> object:
        return DuckDBExpressionCompiler().compile(self.expression)

    def expression_polars_compile(self) -> object:
        return PolarsExpressionCompiler().compile(self.expression)

    def expression_pandas_compile_eval(self) -> ScenarioOutcome:
        values = PandasExpressionCompiler().compile(
            self.expression,
            self.pandas_frame,
        )
        return ScenarioOutcome(
            value=values,
            metrics=metric_pairs({"rows": len(values)}),
        )

    def pandas_adapter_execution(self) -> ScenarioOutcome:
        result = self.pandas_adapter.execute_many(
            self.logical_plan,
            {"source": self.pandas_handle},
            ExecutionContext(mode=ExecutionMode.EAGER),
        )
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs(
                {"rows": len(result.output_handle.dataframe)}
            ),
        )

    def pandas_runtime_execution(self) -> ScenarioOutcome:
        result = self.pandas_runtime.execute(
            self.plan,
            engine="pandas",
            inputs=_pandas_inputs(self.pandas_frame),
            mode=ExecutionMode.EAGER,
        )
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs(
                {"rows": len(result.output_handle.dataframe)}
            ),
        )

    def pandas_memory_amplification(self) -> ScenarioOutcome:
        result = self.pandas_runtime.execute(
            self.row_plan,
            engine="pandas",
            inputs=_pandas_inputs(self.pandas_frame),
            mode=ExecutionMode.EAGER,
        )
        output = result.output_handle.dataframe
        input_bytes = _pandas_bytes(self.pandas_frame)
        output_bytes = _pandas_bytes(output)
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs(
                {
                    "native_input_bytes": input_bytes,
                    "native_output_bytes": output_bytes,
                    "native_amplification_ratio": output_bytes / max(input_bytes, 1),
                }
            ),
        )

    def polars_eager_execution(self) -> ScenarioOutcome:
        result = self.polars_runtime.execute(
            self.plan,
            engine="polars",
            inputs=_polars_inputs(self.polars_frame, lazy=False),
            mode=ExecutionMode.EAGER,
        )
        output = result.output_handle.frame
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs({"rows": output.height}),
        )

    def polars_lazy_execution(self) -> ScenarioOutcome:
        result = self.polars_runtime.execute(
            self.plan,
            engine="polars",
            inputs=_polars_inputs(self.polars_frame, lazy=True),
            mode=ExecutionMode.LAZY,
        )
        output = result.output_handle.frame
        materialized = output.collect() if isinstance(output, pl.LazyFrame) else output
        return ScenarioOutcome(
            value=materialized,
            metrics=metric_pairs({"rows": materialized.height}),
        )

    def polars_memory_amplification(self) -> ScenarioOutcome:
        result = self.polars_runtime.execute(
            self.row_plan,
            engine="polars",
            inputs=_polars_inputs(self.polars_frame, lazy=False),
            mode=ExecutionMode.EAGER,
        )
        output = result.output_handle.frame
        input_bytes = self.polars_frame.estimated_size()
        output_bytes = output.estimated_size()
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs(
                {
                    "native_input_bytes": input_bytes,
                    "native_output_bytes": output_bytes,
                    "native_amplification_ratio": output_bytes / max(input_bytes, 1),
                }
            ),
        )

    def pandas_to_arrow(self) -> ScenarioOutcome:
        converted = PyArrowInterchange.from_pandas(self.pandas_frame)
        return ScenarioOutcome(
            value=converted,
            metrics=metric_pairs({"arrow_bytes": converted.value.table.nbytes}),
        )

    def arrow_to_pandas(self) -> ScenarioOutcome:
        converted = PyArrowInterchange.to_pandas(self.arrow_table)
        return ScenarioOutcome(
            value=converted,
            metrics=metric_pairs({"native_bytes": _pandas_bytes(converted.value)}),
        )

    def polars_to_arrow(self) -> ScenarioOutcome:
        converted = PyArrowInterchange.from_polars(self.polars_frame)
        return ScenarioOutcome(
            value=converted,
            metrics=metric_pairs({"arrow_bytes": converted.value.table.nbytes}),
        )

    def arrow_to_polars(self) -> ScenarioOutcome:
        converted = PyArrowInterchange.to_polars(self.arrow_table)
        return ScenarioOutcome(
            value=converted,
            metrics=metric_pairs({"native_bytes": converted.value.estimated_size()}),
        )

    def duckdb_eager_execution(self) -> ScenarioOutcome:
        adapter = DuckDBEngineAdapter()
        try:
            runtime = _runtime(adapter)
            result = runtime.execute(
                self.plan,
                engine="duckdb",
                inputs=_duckdb_inputs(self.arrow_table),
                mode=ExecutionMode.EAGER,
            )
            table = result.output_handle.to_arrow_table()
            return ScenarioOutcome(
                value=table,
                metrics=metric_pairs(
                    {"rows": table.num_rows, "arrow_bytes": table.nbytes}
                ),
            )
        finally:
            adapter.close()

    def duckdb_lazy_dispatch(self) -> ScenarioOutcome:
        adapter = DuckDBEngineAdapter()
        try:
            runtime = _runtime(adapter)
            result = runtime.execute(
                self.plan,
                engine="duckdb",
                inputs=_duckdb_inputs(self.arrow_table),
                mode=ExecutionMode.LAZY,
            )
            return ScenarioOutcome(
                value=None,
                metrics=metric_pairs(
                    {"diagnostics": len(result.diagnostics)}
                ),
            )
        finally:
            adapter.close()

    def duckdb_lazy_materialized(self) -> ScenarioOutcome:
        adapter = DuckDBEngineAdapter()
        try:
            runtime = _runtime(adapter)
            result = runtime.execute(
                self.plan,
                engine="duckdb",
                inputs=_duckdb_inputs(self.arrow_table),
                mode=ExecutionMode.LAZY,
            )
            table = result.output_handle.to_arrow_table()
            return ScenarioOutcome(
                value=table,
                metrics=metric_pairs(
                    {"rows": table.num_rows, "arrow_bytes": table.nbytes}
                ),
            )
        finally:
            adapter.close()

    def parquet_full_scan(self) -> ScenarioOutcome:
        result = self.reader.read(ReadRequest(resource=self.parquet_resource))
        table = result.value
        filtered = table.filter(pc.greater(table["amount"], 50.0)).select(
            ["id", "amount"]
        )
        return ScenarioOutcome(
            value=filtered,
            metrics=metric_pairs(
                {"rows": filtered.num_rows, "arrow_bytes": filtered.nbytes}
            ),
        )

    def parquet_pushdown(self) -> ScenarioOutcome:
        result = self.reader.read(
            ReadRequest(
                resource=self.parquet_resource,
                projection=("id", "amount"),
                predicate=col("amount") > 50.0,
            )
        )
        table = result.value
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs(
                {"rows": table.num_rows, "arrow_bytes": table.nbytes}
            ),
        )

    def lineage_analysis(self) -> ScenarioOutcome:
        lineage = LineageAnalyzer().analyze(self.logical_plan)
        return ScenarioOutcome(
            value=lineage,
            metrics=metric_pairs(
                {
                    "dataset_edges": len(lineage.dataset_edges),
                    "field_edges": len(lineage.field_edges),
                    "dependencies": len(lineage.dependencies),
                }
            ),
        )

    def runtime_null_telemetry(self) -> ScenarioOutcome:
        result = self.pandas_runtime.execute(
            self.row_plan,
            engine="pandas",
            inputs=_pandas_inputs(self.pandas_frame),
            mode=ExecutionMode.EAGER,
        )
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs({"diagnostics": len(result.diagnostics)}),
        )

    def runtime_recording_telemetry(self) -> ScenarioOutcome:
        sink = RecordingTelemetrySink()
        runtime = _runtime(self.pandas_adapter, telemetry=sink)
        result = runtime.execute(
            self.row_plan,
            engine="pandas",
            inputs=_pandas_inputs(self.pandas_frame),
            mode=ExecutionMode.EAGER,
        )
        return ScenarioOutcome(
            value=result,
            metrics=metric_pairs(
                {
                    "events": len(sink.events),
                    "metrics": len(sink.metrics),
                    "spans": len(sink.spans),
                }
            ),
        )


def _runtime(
    adapter: object,
    *,
    telemetry: object | None = None,
) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(
        engines=registry,
        telemetry=telemetry,  # type: ignore[arg-type]
    )


def _schema() -> Schema:
    return Schema(
        (
            Field("id", IntegerType(), nullable=False),
            Field("segment", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("email", StringType(), nullable=False),
        )
    )


def _reference_plan(schema: Schema) -> TransformationPlan:
    builder = TransformationPlan.builder("performance_reference")
    source = builder.input("source", schema=schema)
    active = builder.filter(
        "active",
        source=source,
        where=col("status") == "ACTIVE",
    )
    normalized = builder.derive(
        "normalized",
        source=active,
        field_name="normalized_email",
        expression=lower(trim(col("email"))),
    )
    enriched = builder.derive(
        "gross_amount",
        source=normalized,
        field_name="gross_amount",
        expression=col("amount") * 1.2,
    )
    aggregated = builder.aggregate(
        "aggregated",
        source=enriched,
        group_by=(col("segment"),),
        metrics={
            "row_count": fn.count(col("id")),
            "revenue": fn.sum(col("gross_amount")),
        },
    )
    ordered = builder.sort(
        "ordered",
        source=aggregated,
        by=("segment",),
    )
    return builder.output("result", ordered).build()


def _row_preserving_plan(schema: Schema) -> TransformationPlan:
    builder = TransformationPlan.builder("performance_rows")
    source = builder.input("source", schema=schema)
    active = builder.filter(
        "active",
        source=source,
        where=col("status") == "ACTIVE",
    )
    normalized = builder.derive(
        "normalized",
        source=active,
        field_name="normalized_email",
        expression=lower(trim(col("email"))),
    )
    selected = builder.select(
        "selected",
        source=normalized,
        columns=("id", "segment", "amount", "normalized_email"),
    )
    return builder.output("result", selected).build()


def _payload(row_count: int) -> dict[str, list[object]]:
    return {
        "id": list(range(row_count)),
        "segment": [f"S{index % 20:02d}" for index in range(row_count)],
        "amount": [float((index % 100) * 1.25) for index in range(row_count)],
        "status": [
            "ACTIVE" if index % 3 != 0 else "INACTIVE"
            for index in range(row_count)
        ],
        "email": [
            f" USER{index}@EXAMPLE.COM "
            for index in range(row_count)
        ],
    }


def _pandas_inputs(frame: pd.DataFrame) -> dict[str, InputBinding]:
    return {
        "source": InputBinding.from_native(
            "source",
            frame,
            engine="pandas",
        )
    }


def _polars_inputs(
    frame: pl.DataFrame,
    *,
    lazy: bool,
) -> dict[str, InputBinding]:
    native = frame.lazy() if lazy else frame
    return {
        "source": InputBinding.from_native(
            "source",
            native,
            engine="polars",
        )
    }


def _duckdb_inputs(table: pa.Table) -> dict[str, InputBinding]:
    return {
        "source": InputBinding.from_native(
            "source",
            table,
            engine="duckdb",
        )
    }


def _pandas_bytes(frame: pd.DataFrame) -> int:
    return int(frame.memory_usage(index=True, deep=True).sum())
