"""DuckDB EngineAdapter and SQL execution lifecycle."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from typing import Any
from uuid import uuid4

import duckdb
import pyarrow as pa

from pytransformkit.application.execution.compatibility import (
    EngineCompatibilityService,
)
from pytransformkit.application.execution.context import (
    ExecutionContext,
    ExecutionMode,
)
from pytransformkit.application.execution.results import (
    EngineExecutionResult,
    NamedEngineOutput,
)
from pytransformkit.application.ports.engines import PhysicalHandle
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.runtime import Diagnostic, DiagnosticSeverity
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.duckdb.handle import (
    DuckDBDatasetHandle,
)
from pytransformkit.infrastructure.engines.duckdb.planner import (
    DuckDBCompiledPlan,
    DuckDBPlanCompiler,
)

_DUCKDB_CAPABILITIES = frozenset(
    {
        EngineCapability.SELECT,
        EngineCapability.DROP,
        EngineCapability.RENAME,
        EngineCapability.FILTER,
        EngineCapability.LIMIT,
        EngineCapability.DISTINCT,
        EngineCapability.CAST,
        EngineCapability.DERIVE,
        EngineCapability.SORT,
        EngineCapability.JOIN_INNER,
        EngineCapability.JOIN_LEFT,
        EngineCapability.JOIN_RIGHT,
        EngineCapability.JOIN_FULL,
        EngineCapability.JOIN_SEMI,
        EngineCapability.JOIN_ANTI,
        EngineCapability.JOIN_CROSS,
        EngineCapability.UNION,
        EngineCapability.INTERSECT,
        EngineCapability.EXCEPT,
        EngineCapability.AGGREGATE,
        EngineCapability.WINDOW,
        EngineCapability.WINDOW_ROWS_CUMULATIVE,
        EngineCapability.WINDOW_ROWS_MOVING,
        EngineCapability.WINDOW_ROWS_ARBITRARY,
        EngineCapability.WINDOW_RANGE,
        EngineCapability.LAZY,
    }
)


class DuckDBAdapter:
    """Relational DuckDB backend using parameterized SQL lowering."""

    def __init__(
        self,
        connection: Any | None = None,
        *,
        plan_compiler: DuckDBPlanCompiler | None = None,
    ) -> None:
        if connection is None:
            self._connection = duckdb.connect(database=":memory:")
            self._owns_connection = True
        else:
            if not isinstance(connection, duckdb.DuckDBPyConnection):
                raise TypeError(
                    "DuckDBAdapter connection must be a DuckDBPyConnection."
                )
            self._connection = connection
            self._owns_connection = False

        self._compiler = plan_compiler or DuckDBPlanCompiler()
        self._compatibility = EngineCompatibilityService()
        self._leased_views: dict[str, Any] = {}
        self._closed = False

    @property
    def descriptor(self) -> EngineDescriptor:
        return EngineDescriptor(
            id="duckdb",
            name="DuckDB",
            adapter_version=_package_version(),
            capabilities=_DUCKDB_CAPABILITIES,
        )

    @property
    def connection(self) -> Any:
        """Expose the active connection for explicit advanced integrations."""
        self._ensure_open()
        return self._connection

    @property
    def owns_connection(self) -> bool:
        return self._owns_connection

    def bind_native(self, value: object) -> PhysicalHandle:
        """Bind DuckDB or Arrow data to this adapter connection."""
        self._ensure_open()

        if isinstance(value, duckdb.DuckDBPyRelation):
            table = value.to_arrow_table()
            relation = self._connection.from_arrow(table)
            return DuckDBDatasetHandle(
                relation=relation,
                connection=self._connection,
            )

        if isinstance(value, (pa.Table, pa.RecordBatch, pa.RecordBatchReader)):
            relation = self._connection.from_arrow(value)
            return DuckDBDatasetHandle(
                relation=relation,
                connection=self._connection,
            )

        raise TypeError(
            "DuckDBAdapter native values must be DuckDB relations or Arrow objects."
        )

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Compatibility single-input execution path."""
        if len(plan.input_names) != 1:
            raise AdapterError(
                "DuckDBAdapter.execute requires a single-input LogicalPlan; "
                "use execute_many for multi-input plans."
            )
        return self.execute_many(
            plan,
            {plan.input_names[0]: input_handle},
            context,
        )

    def execute_many(
        self,
        plan: LogicalPlan,
        input_handles: Mapping[str, PhysicalHandle],
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Compile and execute a LogicalPlan using DuckDB SQL."""
        self._ensure_open()
        self._compatibility.validate(plan, self.descriptor)

        views, relations = self._bind_execution_views(
            plan,
            input_handles,
        )
        compiled = self._compiler.compile(plan, views)

        try:
            result = self._execute_compiled(
                plan,
                compiled,
                context,
            )
        except Exception as error:
            self._drop_views(tuple(views.values()))
            if isinstance(error, AdapterError):
                raise
            raise AdapterError(f"DuckDB execution failed: {error}") from error

        if context.mode is ExecutionMode.EAGER:
            self._drop_views(tuple(views.values()))
        else:
            for view_name, relation in relations.items():
                self._leased_views[view_name] = relation

        return result

    def explain(
        self,
        plan: LogicalPlan,
        input_handles: Mapping[str, PhysicalHandle],
    ) -> dict[str, str]:
        """Return DuckDB's native physical-plan explanation per named output."""
        self._ensure_open()
        self._compatibility.validate(plan, self.descriptor)
        views, _ = self._bind_execution_views(plan, input_handles)
        compiled = self._compiler.compile(plan, views)

        try:
            explanations = {
                output.name: self._connection.sql(
                    output.sql,
                    params=list(output.params),
                ).explain()
                for output in compiled.outputs
            }
        finally:
            self._drop_views(tuple(views.values()))

        return explanations

    def close(self) -> None:
        """Release adapter-created views and only owned connections."""
        if self._closed:
            return

        self._drop_views(tuple(self._leased_views))
        self._leased_views.clear()

        if self._owns_connection:
            self._connection.close()
        self._closed = True

    def _execute_compiled(
        self,
        plan: LogicalPlan,
        compiled: DuckDBCompiledPlan,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        outputs: list[NamedEngineOutput] = []
        diagnostics: list[Diagnostic] = []

        for output in compiled.outputs:
            if context.mode is ExecutionMode.LAZY:
                relation = self._connection.sql(
                    output.sql,
                    params=list(output.params),
                )
                if output.params:
                    diagnostics.append(
                        Diagnostic(
                            code="PTK-DUCKDB-LAZY-001",
                            severity=DiagnosticSeverity.INFO,
                            summary=(
                                "DuckDB parameterized relational execution may "
                                "materialize intermediate state during binding."
                            ),
                            source_component="duckdb.adapter",
                        )
                    )
            else:
                cursor = self._connection.execute(
                    output.sql,
                    list(output.params),
                )
                table = cursor.to_arrow_table()
                relation = self._connection.from_arrow(table)

            outputs.append(
                NamedEngineOutput(
                    name=output.name,
                    output_handle=DuckDBDatasetHandle(
                        relation=relation,
                        connection=self._connection,
                    ),
                    output_schema=plan.schema_for_output(output.name),
                )
            )

        first = outputs[0]
        return EngineExecutionResult(
            output_handle=first.output_handle,
            output_schema=first.output_schema,
            named_outputs=tuple(outputs),
            diagnostics=tuple(diagnostics),
        )

    def _bind_execution_views(
        self,
        plan: LogicalPlan,
        input_handles: Mapping[str, PhysicalHandle],
    ) -> tuple[dict[str, str], dict[str, Any]]:
        prefix = f"__ptk_{uuid4().hex}"
        views: dict[str, str] = {}
        relations: dict[str, Any] = {}

        for index, name in enumerate(plan.input_names):
            if name not in input_handles:
                raise AdapterError(f"Missing DuckDB input handle for {name!r}.")
            handle = input_handles[name]
            if not isinstance(handle, DuckDBDatasetHandle):
                raise AdapterError(
                    "DuckDBAdapter requires DuckDBDatasetHandle inputs."
                )

            if handle.connection is self._connection:
                relation = handle.relation
            else:
                relation = self._connection.from_arrow(
                    handle.relation.to_arrow_table()
                )

            view_name = f"{prefix}_{index}"
            relation.create_view(view_name, replace=False)
            views[name] = view_name
            relations[view_name] = relation

        return views, relations

    def _drop_views(self, view_names: tuple[str, ...]) -> None:
        for view_name in view_names:
            try:
                escaped = view_name.replace('"', '""')
                self._connection.execute(
                    f'DROP VIEW IF EXISTS "{escaped}"'
                )
            except Exception:
                continue
            self._leased_views.pop(view_name, None)

    def _ensure_open(self) -> None:
        if self._closed:
            raise AdapterError("DuckDBAdapter is closed.")


def _package_version() -> str:
    try:
        return version("pytransformkit")
    except PackageNotFoundError:
        return "0.4.0a2"
