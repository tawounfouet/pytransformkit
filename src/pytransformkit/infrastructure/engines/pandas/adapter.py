"""Pandas reference EngineAdapter."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import pandas as pd

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
from pytransformkit.domain.data.data_types import (
    BooleanType,
    DateType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
)
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
from pytransformkit.infrastructure.engines.pandas.expressions import (
    PandasExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pandas.handle import (
    PandasDatasetHandle,
)
from pytransformkit.infrastructure.engines.pandas.quality import PandasQualityEvaluator
from pytransformkit.infrastructure.engines.pandas.types import PandasTypeMapper
from pytransformkit.infrastructure.engines.pandas.windows import PandasWindowCompiler

_PANDAS_CAPABILITIES = frozenset(
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
    }
)


class PandasAdapter:
    """Reference eager adapter implementing PyTransformKit semantics."""

    def __init__(
        self,
        expression_compiler: PandasExpressionCompiler | None = None,
        type_mapper: PandasTypeMapper | None = None,
    ) -> None:
        self._expression_compiler = expression_compiler or PandasExpressionCompiler()
        self._window_compiler = PandasWindowCompiler(self._expression_compiler)
        self._quality_evaluator = PandasQualityEvaluator(self._expression_compiler)
        self._type_mapper = type_mapper or PandasTypeMapper()
        self._compatibility = EngineCompatibilityService()

    @property
    def descriptor(self) -> EngineDescriptor:
        return EngineDescriptor(
            id="pandas",
            name="Pandas",
            adapter_version=_package_version(),
            capabilities=_PANDAS_CAPABILITIES,
        )

    def bind_native(self, value: object) -> PhysicalHandle:
        """Wrap a native pandas DataFrame in a physical handle."""
        return PandasDatasetHandle(value)

    def bind_arrow(self, value: object) -> PhysicalHandle:
        """Bind an Arrow Table/RecordBatch into a Pandas handle."""
        import pyarrow as pa

        if not isinstance(value, (pa.Table, pa.RecordBatch)):
            raise TypeError("PandasAdapter.bind_arrow requires Arrow tabular data.")
        table = value if isinstance(value, pa.Table) else pa.Table.from_batches([value])
        return PandasDatasetHandle(table.to_pandas())

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Compatibility single-input execution path."""
        if len(plan.input_names) != 1:
            raise AdapterError(
                "PandasAdapter.execute requires a single-input LogicalPlan; "
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
        """Execute a named-input LogicalPlan eagerly with Pandas."""
        if context.mode is ExecutionMode.LAZY:
            raise AdapterError("Pandas does not support LAZY execution mode.")

        self._compatibility.validate(plan, self.descriptor)
        values: dict[object, Any] = {}
        validations: list[ValidationResult] = []

        for node in plan.nodes:
            if node.kind is PipelineNodeKind.INPUT:
                if node.name is None or node.name not in input_handles:
                    raise AdapterError(
                        f"Missing Pandas input handle for {node.name!r}."
                    )
                handle = input_handles[node.name]
                if not isinstance(handle, PandasDatasetHandle):
                    raise AdapterError(
                        "PandasAdapter requires PandasDatasetHandle inputs."
                    )
                if handle.engine_id != self.descriptor.id:
                    raise AdapterError(
                        "Input PhysicalHandle engine does not match Pandas."
                    )
                values[node.node_id] = handle.dataframe.copy(deep=False)
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
                    values[node.node_id] = inputs[0].copy(deep=False)
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
            named_outputs.append(
                NamedEngineOutput(
                    name=node.name,
                    output_handle=PandasDatasetHandle(
                        values[node.node_id].copy(deep=False)
                    ),
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

    def _execute_transformation(
        self,
        dataframe: Any,
        transformation: TransformationSpec,
        output_schema: Schema,
    ) -> Any:
        if isinstance(transformation, SelectTransformation):
            names = [str(field) for field in transformation.fields]
            return dataframe.loc[:, names].copy()

        if isinstance(transformation, DropTransformation):
            names = [str(field) for field in transformation.fields]
            return dataframe.drop(columns=names).copy()

        if isinstance(transformation, RenameTransformation):
            mapping = {str(item.source): item.target for item in transformation.renames}
            return dataframe.rename(columns=mapping).copy()

        if isinstance(transformation, FilterTransformation):
            condition = self._expression_compiler.compile(
                transformation.condition,
                dataframe,
            )
            return _filter(dataframe, condition)

        if isinstance(transformation, LimitTransformation):
            return dataframe.head(transformation.count).copy()

        if isinstance(transformation, DistinctTransformation):
            return dataframe.drop_duplicates(keep="first").copy()

        if isinstance(transformation, CastTransformation):
            field_name = str(transformation.field)
            casted = self._cast_series(
                dataframe[field_name],
                transformation,
            )
            return dataframe.assign(**{field_name: casted})

        if isinstance(transformation, DeriveTransformation):
            if isinstance(transformation.expression, WindowExpression):
                value = self._window_compiler.compile(
                    transformation.expression,
                    dataframe,
                )
            else:
                value = self._expression_compiler.compile(
                    transformation.expression,
                    dataframe,
                )
            return dataframe.assign(**{transformation.field_name: value})

        if isinstance(transformation, AggregateTransformation):
            return self._execute_aggregate(
                dataframe,
                transformation,
                output_schema,
            )

        if isinstance(transformation, PivotTransformation):
            return self._execute_pivot(
                dataframe,
                transformation,
                output_schema,
            )

        if isinstance(transformation, UnpivotTransformation):
            return self._execute_unpivot(
                dataframe,
                transformation,
                output_schema,
            )

        if isinstance(transformation, ExplodeTransformation):
            return self._execute_explode(
                dataframe,
                transformation,
                output_schema,
            )

        if isinstance(transformation, FlattenTransformation):
            return self._execute_flatten(
                dataframe,
                transformation,
                output_schema,
            )

        if isinstance(transformation, SortTransformation):
            return _sort(dataframe, transformation)

        if isinstance(transformation, DeduplicateTransformation):
            subset = [str(key) for key in transformation.keys]
            return dataframe.drop_duplicates(
                subset=subset,
                keep=transformation.keep.value,
            ).copy()

        raise AdapterError(
            "Pandas execution is not implemented for "
            f"{type(transformation).__name__!r}."
        )

    def _execute_aggregate(
        self,
        dataframe: Any,
        transformation: AggregateTransformation,
        output_schema: Schema,
    ) -> Any:
        work = dataframe.copy()
        group_columns: list[str] = []
        existing = {str(column) for column in work.columns}

        for index, expression in enumerate(transformation.group_by):
            internal_name = _pandas_internal_name(
                existing,
                "group",
                index,
            )
            existing.add(internal_name)
            work[internal_name] = self._expression_compiler.compile(
                expression,
                dataframe,
            )
            group_columns.append(internal_name)

        metric_columns: dict[str, str | None] = {}
        for index, metric in enumerate(transformation.metrics):
            argument = metric.expression.argument
            if argument is None:
                metric_columns[metric.name] = None
                continue
            internal_name = _pandas_internal_name(
                existing,
                "metric",
                index,
            )
            existing.add(internal_name)
            work[internal_name] = self._expression_compiler.compile(
                argument,
                dataframe,
            )
            metric_columns[metric.name] = internal_name

        if group_columns:
            named_aggregations: dict[str, Any] = {}
            for metric in transformation.metrics:
                column = metric_columns[metric.name]
                if column is None:
                    internal_name = _pandas_internal_name(
                        existing,
                        "row_count",
                        len(existing),
                    )
                    existing.add(internal_name)
                    work[internal_name] = 1
                    column = internal_name
                named_aggregations[metric.name] = pd.NamedAgg(
                    column=column,
                    aggfunc=_pandas_group_aggfunc(metric.expression),
                )

            result = work.groupby(
                group_columns,
                dropna=False,
                sort=False,
                as_index=False,
            ).agg(**named_aggregations)
            result = result.rename(
                columns={
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
            row: dict[str, object] = {}
            for metric in transformation.metrics:
                column = metric_columns[metric.name]
                series = None if column is None else work[column]
                row[metric.name] = _pandas_scalar_aggregate(
                    dataframe,
                    series,
                    metric.expression,
                )
            result = pd.DataFrame([row])

        result = result.loc[:, list(output_schema.names())]
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_pivot(
        self,
        dataframe: Any,
        transformation: PivotTransformation,
        output_schema: Schema,
    ) -> Any:
        index = [str(field) for field in transformation.index]
        column = str(transformation.columns)
        value = str(transformation.values)
        categories = list(transformation.categories)

        work = dataframe.loc[
            dataframe[column].isin(categories),
            index + [column, value],
        ]

        if index:
            grouped = work.groupby(
                index + [column],
                dropna=False,
                sort=False,
            )[value]
            aggregated = _pandas_pivot_aggregate(
                grouped,
                transformation.aggregation,
            )
            result = aggregated.unstack(column)
            result = result.reindex(columns=categories).reset_index()
        else:
            grouped = work.groupby(
                column,
                dropna=False,
                sort=False,
            )[value]
            aggregated = _pandas_pivot_aggregate(
                grouped,
                transformation.aggregation,
            )
            row = {
                category: (
                    aggregated.get(category, 0)
                    if transformation.aggregation is PivotAggregation.COUNT
                    else aggregated.get(category, pd.NA)
                )
                for category in categories
            }
            result = pd.DataFrame([row])

        if transformation.aggregation is PivotAggregation.COUNT:
            for category in categories:
                result[category] = result[category].fillna(0)

        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_unpivot(
        self,
        dataframe: Any,
        transformation: UnpivotTransformation,
        output_schema: Schema,
    ) -> Any:
        result = dataframe.melt(
            id_vars=[str(field) for field in transformation.id_vars],
            value_vars=[str(field) for field in transformation.value_vars],
            var_name=transformation.variable_name,
            value_name=transformation.value_name,
            ignore_index=True,
        )
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_explode(
        self,
        dataframe: Any,
        transformation: ExplodeTransformation,
        output_schema: Schema,
    ) -> Any:
        result = dataframe.explode(
            str(transformation.field),
            ignore_index=True,
        )
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _execute_flatten(
        self,
        dataframe: Any,
        transformation: FlattenTransformation,
        output_schema: Schema,
    ) -> Any:
        field_name = str(transformation.field)
        result = dataframe.copy()

        for output_field in output_schema.fields:
            if output_field.name in dataframe.columns:
                continue
            nested_name = _flatten_nested_name(
                transformation,
                output_field.name,
            )
            result[output_field.name] = result[field_name].map(
                lambda value, key=nested_name: _pandas_nested_value(value, key)
            )

        result = result.drop(columns=[field_name])
        result = result.loc[:, list(output_schema.names())]
        return self._coerce_output_schema(
            result,
            output_schema,
        )

    def _coerce_output_schema(
        self,
        dataframe: Any,
        output_schema: Schema,
    ) -> Any:
        result = dataframe.copy()
        for field in output_schema.fields:
            try:
                native_type = self._type_mapper.to_native(
                    field.data_type,
                    nullable=field.nullable,
                )
            except AdapterError:
                continue
            result[field.name] = result[field.name].astype(native_type)
        return result

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
            result = pd.concat(
                [left, right],
                ignore_index=True,
                copy=False,
            )
            if not transformation.all:
                result = result.drop_duplicates(keep="first")
        elif isinstance(transformation, IntersectTransformation):
            columns = list(output_schema.names())
            result = left.merge(
                right.drop_duplicates(),
                on=columns,
                how="inner",
                sort=False,
            ).drop_duplicates(keep="first")
        elif isinstance(transformation, ExceptTransformation):
            columns = list(output_schema.names())
            marker = "__ptk_set_membership__"
            merged = left.merge(
                right.drop_duplicates(),
                on=columns,
                how="left",
                indicator=marker,
                sort=False,
            )
            result = merged.loc[merged[marker] == "left_only", columns].drop_duplicates(
                keep="first"
            )
        else:
            raise AdapterError(
                "Pandas relational execution is not implemented for "
                f"{type(transformation).__name__!r}."
            )

        expected = list(output_schema.names())
        missing = [name for name in expected if name not in result.columns]
        if missing:
            raise AdapterError(
                f"Pandas relational result is missing expected columns: {missing!r}."
            )
        return result.loc[:, expected].reset_index(drop=True)

    def _cast_series(
        self,
        series: Any,
        transformation: CastTransformation,
    ) -> Any:
        data_type = transformation.target_type
        errors = "coerce" if transformation.policy is CastPolicy.NULL else "raise"

        if isinstance(data_type, IntegerType):
            converted = pd.to_numeric(series, errors=errors)
            return converted.astype(self._type_mapper.to_native(data_type))

        if isinstance(data_type, FloatType):
            converted = pd.to_numeric(series, errors=errors)
            return converted.astype(self._type_mapper.to_native(data_type))

        if isinstance(data_type, StringType):
            return series.astype("string")

        if isinstance(data_type, BooleanType):
            return series.astype("boolean")

        if isinstance(data_type, TimestampType):
            converted = pd.to_datetime(series, errors=errors)
            if data_type.timezone is not None:
                timezone = getattr(converted.dt, "tz", None)
                if timezone is None:
                    converted = converted.dt.tz_localize(data_type.timezone)
                else:
                    converted = converted.dt.tz_convert(data_type.timezone)
            return converted

        if isinstance(data_type, DateType):
            return pd.to_datetime(series, errors=errors).dt.date

        raise AdapterError(
            f"Pandas casting is not implemented for {type(data_type).__name__!r}."
        )


def _pandas_pivot_aggregate(
    grouped: Any,
    aggregation: PivotAggregation,
) -> Any:
    if aggregation is PivotAggregation.SUM:
        return grouped.sum(min_count=1)
    if aggregation is PivotAggregation.MIN:
        return grouped.min()
    if aggregation is PivotAggregation.MAX:
        return grouped.max()
    if aggregation is PivotAggregation.MEAN:
        return grouped.mean()
    if aggregation is PivotAggregation.COUNT:
        return grouped.count()
    raise AdapterError(f"Unsupported Pandas pivot aggregation {aggregation.value!r}.")


def _pandas_nested_value(value: object, key: str) -> object:
    if value is None or value is pd.NA:
        return pd.NA
    if isinstance(value, Mapping):
        return value.get(key, pd.NA)
    try:
        return getattr(value, key)
    except AttributeError as error:
        raise AdapterError(
            f"Pandas nested value does not expose field {key!r}."
        ) from error


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


def _pandas_internal_name(
    existing: set[str],
    kind: str,
    index: int,
) -> str:
    candidate = f"__pytransformkit_{kind}_{index}__"
    while candidate in existing:
        candidate = f"_{candidate}"
    return candidate


def _pandas_group_aggfunc(
    expression: AggregateExpression,
) -> Any:
    if expression.function is AggregateFunction.COUNT:
        return (lambda values: len(values)) if expression.argument is None else "count"
    if expression.function is AggregateFunction.COUNT_DISTINCT:
        return lambda values: values.nunique(dropna=True)
    if expression.function is AggregateFunction.SUM:
        return lambda values: values.sum(min_count=1)
    if expression.function is AggregateFunction.MIN:
        return "min"
    if expression.function is AggregateFunction.MAX:
        return "max"
    if expression.function is AggregateFunction.MEAN:
        return "mean"
    raise AdapterError(f"Unsupported aggregate function {expression.function.value!r}.")


def _pandas_scalar_aggregate(
    dataframe: Any,
    series: Any | None,
    expression: AggregateExpression,
) -> object:
    if expression.function is AggregateFunction.COUNT:
        if series is None:
            return len(dataframe)
        return int(series.count())
    if series is None:
        raise AdapterError(
            f"{expression.function.value} requires an aggregate argument."
        )
    if expression.function is AggregateFunction.COUNT_DISTINCT:
        return int(series.nunique(dropna=True))
    if expression.function is AggregateFunction.SUM:
        return series.sum(min_count=1)
    if expression.function is AggregateFunction.MIN:
        return series.min()
    if expression.function is AggregateFunction.MAX:
        return series.max()
    if expression.function is AggregateFunction.MEAN:
        return series.mean()
    raise AdapterError(f"Unsupported aggregate function {expression.function.value!r}.")


def _join(
    left: Any,
    right: Any,
    transformation: JoinTransformation,
) -> Any:
    if transformation.how is JoinType.CROSS:
        return left.merge(
            right,
            how="cross",
            suffixes=("", transformation.right_suffix),
            sort=False,
        )

    left_keys = [str(key.left) for key in transformation.keys]
    right_keys = [str(key.right) for key in transformation.keys]

    if transformation.how in {JoinType.SEMI, JoinType.ANTI}:
        left_work, right_work = _prepare_null_join_keys(
            left,
            right,
            left_keys,
            right_keys,
            transformation.nulls,
        )
        right_key_frame = right_work.loc[:, right_keys].drop_duplicates()
        if right_keys != left_keys:
            right_key_frame = right_key_frame.rename(
                columns=dict(zip(right_keys, left_keys, strict=True))
            )
        probe = left_work.loc[:, left_keys].merge(
            right_key_frame,
            on=left_keys,
            how="left",
            indicator=True,
            sort=False,
        )
        matched = probe["_merge"] == "both"
        mask = matched if transformation.how is JoinType.SEMI else ~matched
        return left.loc[mask.to_numpy()].copy()

    left_work, right_work = _prepare_null_join_keys(
        left,
        right,
        left_keys,
        right_keys,
        transformation.nulls,
    )
    how = {
        JoinType.INNER: "inner",
        JoinType.LEFT: "left",
        JoinType.RIGHT: "right",
        JoinType.FULL: "outer",
    }[transformation.how]

    result = left_work.merge(
        right_work,
        left_on=left_keys,
        right_on=right_keys,
        how=how,
        suffixes=("", transformation.right_suffix),
        sort=False,
    )
    if transformation.how in {JoinType.RIGHT, JoinType.FULL}:
        for left_key, right_key in zip(
            left_keys,
            right_keys,
            strict=True,
        ):
            if left_key == right_key or right_key not in result.columns:
                continue
            result[left_key] = result[left_key].where(
                ~result[left_key].isna(),
                result[right_key],
            )
    return _restore_null_sentinels(result)


def _prepare_null_join_keys(
    left: Any,
    right: Any,
    left_keys: list[str],
    right_keys: list[str],
    policy: NullJoinPolicy,
) -> tuple[Any, Any]:
    if policy is NullJoinPolicy.MATCH:
        return left, right

    left_work = left.copy()
    right_work = right.copy()

    for index, (left_key, right_key) in enumerate(
        zip(left_keys, right_keys, strict=True)
    ):
        left_sentinel = _NullSentinel("left", index)
        right_sentinel = _NullSentinel("right", index)
        left_series = left_work[left_key].astype("object")
        right_series = right_work[right_key].astype("object")
        left_work[left_key] = left_series.where(
            ~left_series.isna(),
            left_sentinel,
        )
        right_work[right_key] = right_series.where(
            ~right_series.isna(),
            right_sentinel,
        )

    return left_work, right_work


class _NullSentinel:
    __slots__ = ("side", "index")

    def __init__(self, side: str, index: int) -> None:
        self.side = side
        self.index = index


def _restore_null_sentinels(dataframe: Any) -> Any:
    result = dataframe.copy()
    for column in result.columns:
        if result[column].dtype != "object":
            continue
        result[column] = result[column].map(
            lambda value: pd.NA if isinstance(value, _NullSentinel) else value
        )
    return result


def _filter(dataframe: Any, condition: Any) -> Any:
    if isinstance(condition, pd.Series):
        mask = condition.astype("boolean").fillna(False)
        return dataframe.loc[mask].copy()

    if condition is None or condition is pd.NA:
        return dataframe.iloc[0:0].copy()

    if bool(condition):
        return dataframe.copy()

    return dataframe.iloc[0:0].copy()


def _sort(
    dataframe: Any,
    transformation: SortTransformation,
) -> Any:
    null_orders = {key.nulls.value for key in transformation.keys}
    if len(null_orders) != 1:
        raise AdapterError(
            "Pandas cannot represent mixed per-key NULL ordering "
            "in one native sort operation."
        )

    return dataframe.sort_values(
        by=[str(key.field) for key in transformation.keys],
        ascending=[key.direction.value == "asc" for key in transformation.keys],
        na_position=next(iter(null_orders)),
        kind="mergesort",
    ).copy()


def _package_version() -> str:
    try:
        return version("pytransformkit")
    except PackageNotFoundError:
        return "0.5.0a2"
