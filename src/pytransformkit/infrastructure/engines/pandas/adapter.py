"""Pandas reference EngineAdapter."""

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
from pytransformkit.application.execution.results import EngineExecutionResult
from pytransformkit.application.ports.engines import DatasetHandle
from pytransformkit.domain.data.data_types import (
    BooleanType,
    DateType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
)
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
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

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: DatasetHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        if context.mode is ExecutionMode.LAZY:
            raise AdapterError("Pandas does not support LAZY execution mode.")
        if not isinstance(input_handle, PandasDatasetHandle):
            raise AdapterError("PandasAdapter requires a PandasDatasetHandle.")
        if input_handle.engine_id != self.descriptor.id:
            raise AdapterError("Input DatasetHandle engine does not match Pandas.")

        self._compatibility.validate(plan, self.descriptor)
        dataframe = input_handle.dataframe.copy(deep=False)

        for node in plan.nodes:
            if node.transformation is None:
                continue
            dataframe = self._execute_transformation(
                dataframe,
                node.transformation,
            )

        return EngineExecutionResult(
            output_handle=PandasDatasetHandle(dataframe),
            output_schema=plan.output_schema,
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
        return "0.1.0a1"
