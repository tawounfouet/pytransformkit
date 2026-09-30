"""Polars EngineAdapter with eager, lazy and relational execution."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import polars as pl

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
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.expressions.aggregate import (
    AggregateExpression,
    AggregateFunction,
)
from pytransformkit.domain.expressions.window import WindowExpression
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.quality.results import ValidationResult
from pytransformkit.domain.transformations.aggregation import (
    AggregateTransformation,
    group_output_name,
)
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.casting import (
    CastPolicy,
    CastTransformation,
)
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
)
from pytransformkit.domain.transformations.derivation import DeriveTransformation
from pytransformkit.domain.transformations.filtering import (
    DistinctTransformation,
    FilterTransformation,
    LimitTransformation,
)
from pytransformkit.domain.transformations.projection import (
    DropTransformation,
    RenameTransformation,
    SelectTransformation,
)
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
    NullJoinPolicy,
    UnionTransformation,
)
from pytransformkit.domain.transformations.reshaping import (
    ExplodeTransformation,
    FlattenTransformation,
    PivotAggregation,
    PivotTransformation,
    UnpivotTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.polars.expressions import (
    PolarsExpressionCompiler,
)
from pytransformkit.infrastructure.engines.polars.handle import (
    PolarsDatasetHandle,
)
from pytransformkit.infrastructure.engines.polars.quality import PolarsQualityEvaluator
from pytransformkit.infrastructure.engines.polars.types import PolarsTypeMapper
from pytransformkit.infrastructure.engines.polars.windows import PolarsWindowCompiler

_POLARS_CAPABILITIES = frozenset(
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
        EngineCapability.DEDUPLICATE,
        EngineCapability.AGGREGATE,
        EngineCapability.WINDOW,
        EngineCapability.WINDOW_ROWS_CUMULATIVE,
        EngineCapability.WINDOW_ROWS_MOVING,
        EngineCapability.PIVOT,
        EngineCapability.UNPIVOT,
        EngineCapability.EXPLODE,
        EngineCapability.FLATTEN,
        EngineCapability.NESTED,
        EngineCapability.TEMPORAL,
        EngineCapability.DURATION,
        EngineCapability.QUALITY,
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
        EngineCapability.LAZY,
    }
)


class PolarsAdapter:
    """Polars adapter implementing portable Transformation semantics."""

    def __init__(
        self,
        expression_compiler: PolarsExpressionCompiler | None = None,
        type_mapper: PolarsTypeMapper | None = None,
    ) -> None:
        self._expression_compiler = expression_compiler or PolarsExpressionCompiler()
        self._window_compiler = PolarsWindowCompiler(self._expression_compiler)
        self._quality_evaluator = PolarsQualityEvaluator(self._expression_compiler)
        self._type_mapper = type_mapper or PolarsTypeMapper()
        self._compatibility = EngineCompatibilityService()

    @property
    def descriptor(self) -> EngineDescriptor:
        return EngineDescriptor(
            id="polars",
            name="Polars",
            adapter_version=_package_version(),
            capabilities=_POLARS_CAPABILITIES,
        )

    def bind_native(self, value: object) -> PhysicalHandle:
        """Wrap a native Polars DataFrame/LazyFrame in a physical handle."""
        return PolarsDatasetHandle(value)

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Compatibility single-input execution path."""
        if len(plan.input_names) != 1:
            raise AdapterError(
                "PolarsAdapter.execute requires a single-input LogicalPlan; "
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
        """Execute a named-input LogicalPlan using Polars."""
        self._compatibility.validate(plan, self.descriptor)
        values: dict[object, Any] = {}
        validations: list[ValidationResult] = []

        for node in plan.nodes:
            if node.kind is PipelineNodeKind.INPUT:
                if node.name is None or node.name not in input_handles:
                    raise AdapterError(
                        f"Missing Polars input handle for {node.name!r}."
                    )
                handle = input_handles[node.name]
                if not isinstance(handle, PolarsDatasetHandle):
                    raise AdapterError(
                        "PolarsAdapter requires PolarsDatasetHandle inputs."
                    )
                values[node.node_id] = self._prepare_frame(
                    handle.frame,
                    context.mode,
                )
                continue

            if node.kind is PipelineNodeKind.TRANSFORMATION:
                inputs = tuple(values[item] for item in node.input_node_ids)
                if node.transformation is None:
                    raise AdapterError(
                        "Transformation LogicalPlan node is missing its specification."
                    )
                if isinstance(node.transformation, QualityGate):
                    if len(inputs) != 1 or node.input_schema is None:
                        raise AdapterError(
                            "QualityGate requires one resolved input Schema."
                        )
                    validation = self._quality_evaluator.evaluate(
                        node.transformation.spec,
                        inputs[0],
                        node.input_schema,
                    )
                    validations.append(validation)
                    values[node.node_id] = inputs[0]
                elif len(inputs) == 1:
                    values[node.node_id] = self._execute_transformation(
                        inputs[0],
                        node.transformation,
                        node.output_schema,
                    )
                else:
                    values[node.node_id] = self._execute_relational(
                        inputs,
                        node.transformation,
                        node.output_schema,
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
            frame = values[node.node_id]
            if context.mode is ExecutionMode.EAGER and isinstance(
                frame,
                pl.LazyFrame,
            ):
                frame = frame.collect()
            named_outputs.append(
                NamedEngineOutput(
                    name=node.name,
                    output_handle=PolarsDatasetHandle(frame),
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
            validations=tuple(validations),
        )

    @staticmethod
    def _prepare_frame(frame: Any, mode: ExecutionMode) -> Any:
        if mode is ExecutionMode.LAZY:
            if isinstance(frame, pl.DataFrame):
                return frame.lazy()
            return frame

        if mode is ExecutionMode.EAGER:
            if isinstance(frame, pl.LazyFrame):
                return frame.collect()
            return frame

        return frame

    def _execute_transformation(
        self,
        frame: Any,
        transformation: TransformationSpec,
        output_schema: Schema,
    ) -> Any:
        if isinstance(transformation, SelectTransformation):
            return frame.select([str(field) for field in transformation.fields])

        if isinstance(transformation, DropTransformation):
            return frame.drop([str(field) for field in transformation.fields])

        if isinstance(transformation, RenameTransformation):
            return frame.rename(
                {str(item.source): item.target for item in transformation.renames}
            )

        if isinstance(transformation, FilterTransformation):
            condition = self._expression_compiler.compile(
                transformation.condition,
                frame,
            )
            return frame.filter(condition)

        if isinstance(transformation, LimitTransformation):
            return frame.limit(transformation.count)

        if isinstance(transformation, DistinctTransformation):
            return frame.unique(maintain_order=True)

        if isinstance(transformation, CastTransformation):
            field_name = str(transformation.field)
            expression = pl.col(field_name).cast(
                self._type_mapper.to_native(transformation.target_type),
                strict=transformation.policy is not CastPolicy.NULL,
            )
            return frame.with_columns(expression.alias(field_name))

        if isinstance(transformation, DeriveTransformation):
            if isinstance(transformation.expression, WindowExpression):
                return self._window_compiler.derive(
                    frame,
                    transformation.expression,
                    field_name=transformation.field_name,
                )
            expression = self._expression_compiler.compile(
                transformation.expression,
                frame,
            )
            return frame.with_columns(expression.alias(transformation.field_name))

        if isinstance(transformation, AggregateTransformation):
            return self._execute_aggregate(
                frame,
                transformation,
                output_schema,
            )

        if isinstance(transformation, PivotTransformation):
            return self._execute_pivot(
                frame,
                transformation,
                output_schema,
            )

        if isinstance(transformation, UnpivotTransformation):
            return self._execute_unpivot(
                frame,
                transformation,
                output_schema,
            )

        if isinstance(transformation, ExplodeTransformation):
            return self._execute_explode(
                frame,
                transformation,
                output_schema,
            )

        if isinstance(transformation, FlattenTransformation):
            return self._execute_flatten(
                frame,
                transformation,
                output_schema,
            )

        if isinstance(transformation, SortTransformation):
            return frame.sort(
                by=[str(key.field) for key in transformation.keys],
                descending=[
                    key.direction.value == "desc" for key in transformation.keys
                ],
                nulls_last=[key.nulls.value == "last" for key in transformation.keys],
                maintain_order=True,
            )

        if isinstance(transformation, DeduplicateTransformation):
            return frame.unique(
                subset=[str(key) for key in transformation.keys],
                keep=transformation.keep.value,
                maintain_order=True,
            )

        raise AdapterError(
            "Polars execution is not implemented for "
            f"{type(transformation).__name__!r}."
        )

    def _execute_aggregate(
        self,
        frame: Any,
        transformation: AggregateTransformation,
        output_schema: Schema,
    ) -> Any:
        existing = _polars_columns(frame)
        group_columns: list[str] = []
        prepared: list[Any] = []
        metric_columns: dict[str, str | None] = {}

        for index, expression in enumerate(transformation.group_by):
            internal_name = _polars_internal_name(
                existing,
                "group",
                index,
            )
            existing.add(internal_name)
            prepared.append(
                self._expression_compiler.compile(
                    expression,
                    frame,
                ).alias(internal_name)
            )
            group_columns.append(internal_name)

        for index, metric in enumerate(transformation.metrics):
            argument = metric.expression.argument
            if argument is None:
                metric_columns[metric.name] = None
                continue
            internal_name = _polars_internal_name(
                existing,
                "metric",
                index,
            )
            existing.add(internal_name)
            prepared.append(
                self._expression_compiler.compile(
                    argument,
                    frame,
                ).alias(internal_name)
            )
            metric_columns[metric.name] = internal_name

        work = frame.with_columns(prepared) if prepared else frame
        aggregate_expressions = [
            _polars_aggregate_expression(
                metric.expression,
                metric_columns[metric.name],
            ).alias(metric.name)
            for metric in transformation.metrics
        ]

        if group_columns:
            result = work.group_by(
                group_columns,
                maintain_order=True,
            ).agg(aggregate_expressions)
            result = result.rename(
                {
                    internal_name: group_output_name(expression, index)
                    for index, (internal_name, expression) in enumerate(
                        zip(
                            group_columns,
                            transformation.group_by,
                            strict=True,
                        )
                    )
                }
            )
        else:
            result = work.select(aggregate_expressions)

        casts = [
            pl.col(field.name)
            .cast(
                self._type_mapper.to_native(field.data_type),
                strict=True,
            )
            .alias(field.name)
            for field in output_schema.fields
        ]
        return result.with_columns(casts).select(list(output_schema.names()))

    def _execute_pivot(
        self,
        frame: Any,
        transformation: PivotTransformation,
        output_schema: Schema,
    ) -> Any:
        index = [str(field) for field in transformation.index]
        category_field = str(transformation.columns)
        value_field = str(transformation.values)

        aggregates = [
            _polars_pivot_aggregate(
                transformation.aggregation,
                category_field=category_field,
                value_field=value_field,
                category=category,
            ).alias(category)
            for category in transformation.categories
        ]

        if index:
            result = frame.group_by(
                index,
                maintain_order=True,
            ).agg(aggregates)
        else:
            result = frame.select(aggregates)

        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_unpivot(
        self,
        frame: Any,
        transformation: UnpivotTransformation,
        output_schema: Schema,
    ) -> Any:
        kwargs = {
            "index": [str(field) for field in transformation.id_vars],
            "on": [str(field) for field in transformation.value_vars],
            "variable_name": transformation.variable_name,
            "value_name": transformation.value_name,
        }
        unpivot = getattr(frame, "unpivot", None)
        if unpivot is not None:
            result = unpivot(**kwargs)
        else:
            result = frame.melt(
                id_vars=kwargs["index"],
                value_vars=kwargs["on"],
                variable_name=transformation.variable_name,
                value_name=transformation.value_name,
            )
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_explode(
        self,
        frame: Any,
        transformation: ExplodeTransformation,
        output_schema: Schema,
    ) -> Any:
        result = frame.explode(str(transformation.field))
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_flatten(
        self,
        frame: Any,
        transformation: FlattenTransformation,
        output_schema: Schema,
    ) -> Any:
        field_name = str(transformation.field)
        existing = set(_polars_columns(frame))
        expressions: list[Any] = []

        for output_field in output_schema.fields:
            if output_field.name in existing:
                continue
            nested_name = _flatten_nested_name(
                transformation,
                output_field.name,
            )
            expressions.append(
                pl.col(field_name).struct.field(nested_name).alias(output_field.name)
            )

        result = frame.with_columns(expressions).drop(field_name)
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _coerce_output_schema(
        self,
        frame: Any,
        output_schema: Schema,
    ) -> Any:
        casts = [
            pl.col(field.name)
            .cast(
                self._type_mapper.to_native(field.data_type),
                strict=True,
            )
            .alias(field.name)
            for field in output_schema.fields
        ]
        return frame.with_columns(casts).select(list(output_schema.names()))

    def _execute_relational(
        self,
        inputs: tuple[Any, ...],
        transformation: TransformationSpec,
        output_schema: Schema,
    ) -> Any:
        if len(inputs) != 2:
            raise AdapterError("Relational transformations require two inputs.")
        left, right = inputs

        if isinstance(transformation, JoinTransformation):
            result = _join(left, right, transformation)
        elif isinstance(transformation, UnionTransformation):
            result = pl.concat(
                [left, right],
                how="vertical",
            )
            if not transformation.all:
                result = result.unique(maintain_order=True)
        elif isinstance(transformation, IntersectTransformation):
            columns = list(output_schema.names())
            result = left.join(
                right.unique(maintain_order=True),
                on=columns,
                how="semi",
                nulls_equal=True,
            ).unique(maintain_order=True)
        elif isinstance(transformation, ExceptTransformation):
            columns = list(output_schema.names())
            result = left.join(
                right.unique(maintain_order=True),
                on=columns,
                how="anti",
                nulls_equal=True,
            ).unique(maintain_order=True)
        else:
            raise AdapterError(
                "Polars relational execution is not implemented for "
                f"{type(transformation).__name__!r}."
            )

        expected = list(output_schema.names())
        return result.select(expected)


def _polars_pivot_aggregate(
    aggregation: PivotAggregation,
    *,
    category_field: str,
    value_field: str,
    category: str,
) -> Any:
    value = (
        pl.when(pl.col(category_field) == category)
        .then(pl.col(value_field))
        .otherwise(None)
    )

    if aggregation is PivotAggregation.COUNT:
        return value.count().cast(pl.Int64)
    if aggregation is PivotAggregation.SUM:
        count = value.count()
        return pl.when(count == 0).then(pl.lit(None)).otherwise(value.sum())
    if aggregation is PivotAggregation.MIN:
        return value.min()
    if aggregation is PivotAggregation.MAX:
        return value.max()
    if aggregation is PivotAggregation.MEAN:
        return value.mean().cast(pl.Float64)

    raise AdapterError(f"Unsupported Polars pivot aggregation {aggregation.value!r}.")


def _flatten_nested_name(
    transformation: FlattenTransformation,
    output_name: str,
) -> str:
    prefix = (
        transformation.prefix
        if transformation.prefix is not None
        else f"{transformation.field.name}_"
    )
    if not output_name.startswith(prefix):
        raise AdapterError(
            f"Flatten output {output_name!r} does not match prefix {prefix!r}."
        )
    return output_name[len(prefix) :]


def _polars_columns(frame: Any) -> set[str]:
    if isinstance(frame, pl.LazyFrame):
        return set(frame.collect_schema().names())
    return set(frame.columns)


def _polars_internal_name(
    existing: set[str],
    kind: str,
    index: int,
) -> str:
    candidate = f"__pytransformkit_{kind}_{index}__"
    while candidate in existing:
        candidate = f"_{candidate}"
    return candidate


def _polars_aggregate_expression(
    expression: AggregateExpression,
    column: str | None,
) -> Any:
    if expression.function is AggregateFunction.COUNT:
        if column is None:
            return pl.len().cast(pl.Int64)
        return pl.col(column).count().cast(pl.Int64)

    if column is None:
        raise AdapterError(
            f"{expression.function.value} requires an aggregate argument."
        )

    value = pl.col(column)

    if expression.function is AggregateFunction.COUNT_DISTINCT:
        return value.drop_nulls().n_unique().cast(pl.Int64)
    if expression.function is AggregateFunction.SUM:
        return pl.when(value.count() == 0).then(pl.lit(None)).otherwise(value.sum())
    if expression.function is AggregateFunction.MIN:
        return value.min()
    if expression.function is AggregateFunction.MAX:
        return value.max()
    if expression.function is AggregateFunction.MEAN:
        return value.mean().cast(pl.Float64)

    raise AdapterError(f"Unsupported aggregate function {expression.function.value!r}.")


def _join(
    left: Any,
    right: Any,
    transformation: JoinTransformation,
) -> Any:
    if transformation.how is JoinType.CROSS:
        return left.join(
            right,
            how="cross",
            suffix=transformation.right_suffix,
        )

    left_keys = [str(key.left) for key in transformation.keys]
    right_keys = [str(key.right) for key in transformation.keys]
    how = {
        JoinType.INNER: "inner",
        JoinType.LEFT: "left",
        JoinType.RIGHT: "right",
        JoinType.FULL: "full",
        JoinType.SEMI: "semi",
        JoinType.ANTI: "anti",
    }[transformation.how]

    kwargs = {
        "left_on": left_keys,
        "right_on": right_keys,
        "how": how,
        "suffix": transformation.right_suffix,
    }
    nulls_equal = transformation.nulls is NullJoinPolicy.MATCH

    try:
        return left.join(
            right,
            nulls_equal=nulls_equal,
            coalesce=True,
            **kwargs,
        )
    except TypeError:
        # Compatibility with early Polars 1.x releases.
        return left.join(
            right,
            join_nulls=nulls_equal,
            **kwargs,
        )


def _package_version() -> str:
    try:
        return version("pytransformkit")
    except PackageNotFoundError:
        return "0.3.0"
