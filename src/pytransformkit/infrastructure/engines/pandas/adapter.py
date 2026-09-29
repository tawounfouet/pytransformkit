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
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan
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
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
    NullJoinPolicy,
    UnionTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.pandas.expressions import (
    PandasExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pandas.handle import (
    PandasDatasetHandle,
)
from pytransformkit.infrastructure.engines.pandas.types import PandasTypeMapper

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
                if len(inputs) == 1:
                    values[node.node_id] = self._execute_transformation(
                        inputs[0],
                        node.transformation,
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

            raise AdapterError(
                f"Unsupported LogicalPlan node kind {node.kind!r}."
            )

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
        )

    def _execute_transformation(
        self,
        dataframe: Any,
        transformation: TransformationSpec,
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
            value = self._expression_compiler.compile(
                transformation.expression,
                dataframe,
            )
            return dataframe.assign(**{transformation.field_name: value})

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
            result = (
                left.merge(
                    right.drop_duplicates(),
                    on=columns,
                    how="inner",
                    sort=False,
                )
                .drop_duplicates(keep="first")
            )
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
            result = (
                merged.loc[merged[marker] == "left_only", columns]
                .drop_duplicates(keep="first")
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
                "Pandas relational result is missing expected columns: "
                f"{missing!r}."
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
            lambda value: (
                pd.NA if isinstance(value, _NullSentinel) else value
            )
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
        return "0.2.0a1"
