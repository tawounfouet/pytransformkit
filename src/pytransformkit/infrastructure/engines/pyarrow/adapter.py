"""PyArrow EngineAdapter with explicit eager columnar execution."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from typing import Any

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
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.derivation import DeriveTransformation
from pytransformkit.domain.transformations.filtering import (
    FilterTransformation,
    LimitTransformation,
)
from pytransformkit.domain.transformations.projection import (
    DropTransformation,
    RenameTransformation,
    SelectTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.pyarrow.expressions import (
    PyArrowExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pyarrow.handle import (
    PyArrowDatasetHandle,
)

_PYARROW_CAPABILITIES = frozenset(
    {
        EngineCapability.SELECT,
        EngineCapability.DROP,
        EngineCapability.RENAME,
        EngineCapability.FILTER,
        EngineCapability.LIMIT,
        EngineCapability.DERIVE,
        EngineCapability.SORT,
    }
)


class PyArrowAdapter:
    """Arrow adapter for the explicitly qualified LOT-18 capability subset."""

    def __init__(
        self,
        expression_compiler: PyArrowExpressionCompiler | None = None,
    ) -> None:
        self._expression_compiler = expression_compiler or PyArrowExpressionCompiler()
        self._compatibility = EngineCompatibilityService()

    @property
    def descriptor(self) -> EngineDescriptor:
        return EngineDescriptor(
            id="pyarrow",
            name="PyArrow",
            adapter_version=_package_version(),
            capabilities=_PYARROW_CAPABILITIES,
        )

    def bind_native(self, value: object) -> PhysicalHandle:
        """Wrap an Arrow Table or RecordBatch without copying buffers."""
        return PyArrowDatasetHandle(value)

    def bind_arrow(self, value: object) -> PhysicalHandle:
        """Bind an Arrow interchange value without copying buffers."""
        return self.bind_native(value)

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Compatibility single-input execution path."""
        if len(plan.input_names) != 1:
            raise AdapterError(
                "PyArrowAdapter.execute requires a single-input LogicalPlan; "
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
        """Execute the supported LogicalPlan subset eagerly with Arrow."""
        if context.mode is ExecutionMode.LAZY:
            raise AdapterError("PyArrow LOT-18 adapter supports EAGER execution only.")

        self._compatibility.validate(plan, self.descriptor)
        values: dict[object, pa.Table] = {}

        for node in plan.nodes:
            if node.kind is PipelineNodeKind.INPUT:
                if node.name is None or node.name not in input_handles:
                    raise AdapterError(
                        f"Missing PyArrow input handle for {node.name!r}."
                    )
                handle = input_handles[node.name]
                if not isinstance(handle, PyArrowDatasetHandle):
                    raise AdapterError(
                        "PyArrowAdapter requires PyArrowDatasetHandle inputs."
                    )
                values[node.node_id] = handle.table
                continue

            if node.kind is PipelineNodeKind.TRANSFORMATION:
                inputs = tuple(values[item] for item in node.input_node_ids)
                if len(inputs) != 1:
                    raise AdapterError(
                        "LOT-18 PyArrow adapter currently supports unary plans only."
                    )
                if node.transformation is None:
                    raise AdapterError(
                        "Transformation LogicalPlan node is missing its specification."
                    )
                values[node.node_id] = self._execute_transformation(
                    inputs[0],
                    node.transformation,
                )
                continue

            if node.kind is PipelineNodeKind.OUTPUT:
                if len(node.input_node_ids) != 1:
                    raise AdapterError(
                        "Output LogicalPlan node requires one predecessor."
                    )
                values[node.node_id] = values[node.input_node_ids[0]]
                continue

            raise AdapterError(f"Unsupported LogicalPlan node kind {node.kind!r}.")

        named_outputs: list[NamedEngineOutput] = []
        for node in plan.nodes:
            if node.kind is not PipelineNodeKind.OUTPUT:
                continue
            if node.name is None:
                raise AdapterError("Output LogicalPlan node is missing its name.")
            table = values[node.node_id]
            named_outputs.append(
                NamedEngineOutput(
                    name=node.name,
                    output_handle=PyArrowDatasetHandle(table),
                    output_schema=node.output_schema,
                )
            )

        if not named_outputs:
            raise AdapterError("LogicalPlan did not produce any outputs.")

        first = named_outputs[0]
        return EngineExecutionResult(
            output_handle=first.output_handle,
            output_schema=first.output_schema,
            named_outputs=tuple(named_outputs),
        )

    def _execute_transformation(
        self,
        table: pa.Table,
        transformation: TransformationSpec,
    ) -> pa.Table:
        if isinstance(transformation, SelectTransformation):
            return table.select([str(field) for field in transformation.fields])

        if isinstance(transformation, DropTransformation):
            return table.drop_columns([str(field) for field in transformation.fields])

        if isinstance(transformation, RenameTransformation):
            mapping = {str(item.source): item.target for item in transformation.renames}
            return table.rename_columns(
                [mapping.get(name, name) for name in table.column_names]
            )

        if isinstance(transformation, FilterTransformation):
            mask = self._expression_compiler.compile(
                transformation.condition,
                table,
            )
            return table.filter(mask, null_selection_behavior="drop")

        if isinstance(transformation, LimitTransformation):
            return table.slice(0, transformation.count)

        if isinstance(transformation, DeriveTransformation):
            value = self._expression_compiler.compile(
                transformation.expression,
                table,
            )
            column = _as_column(value, table.num_rows)
            if transformation.field_name in table.column_names:
                if not transformation.replace_existing:
                    raise AdapterError(
                        f"Derived field {transformation.field_name!r} already exists."
                    )
                index = table.column_names.index(transformation.field_name)
                return table.set_column(
                    index,
                    transformation.field_name,
                    column,
                )
            return table.append_column(transformation.field_name, column)

        if isinstance(transformation, SortTransformation):
            null_orders = {key.nulls.value for key in transformation.keys}
            if len(null_orders) != 1:
                raise AdapterError(
                    "PyArrow adapter does not support mixed per-key NULL ordering."
                )
            sorting = [
                (
                    str(key.field),
                    "ascending" if key.direction.value == "asc" else "descending",
                )
                for key in transformation.keys
            ]
            null_placement = (
                "at_start" if next(iter(null_orders)) == "first" else "at_end"
            )
            return table.sort_by(sorting, null_placement=null_placement)

        raise AdapterError(
            "PyArrow execution is not implemented for "
            f"{type(transformation).__name__!r}."
        )


def _as_column(value: Any, row_count: int) -> Any:
    if isinstance(value, pa.Scalar):
        return pa.array([value.as_py()] * row_count, type=value.type)
    if isinstance(value, (pa.Array, pa.ChunkedArray)):
        if len(value) != row_count:
            raise AdapterError(
                "Arrow derived expression produced a column with invalid length."
            )
        return value
    if isinstance(value, list):
        if len(value) != row_count:
            raise AdapterError(
                "Arrow derived expression produced a list with invalid length."
            )
        return pa.array(value)
    scalar = pa.scalar(value)
    return pa.array([scalar.as_py()] * row_count, type=scalar.type)


def _package_version() -> str:
    try:
        return version("pytransformkit")
    except PackageNotFoundError:
        return "0.4.0a1"
