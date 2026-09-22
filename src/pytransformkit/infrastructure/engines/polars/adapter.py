"""Polars EngineAdapter with eager and lazy execution."""

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
from pytransformkit.application.execution.results import EngineExecutionResult
from pytransformkit.application.ports.engines import DatasetHandle
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
from pytransformkit.infrastructure.engines.polars.expressions import (
    PolarsExpressionCompiler,
)
from pytransformkit.infrastructure.engines.polars.handle import (
    PolarsDatasetHandle,
)
from pytransformkit.infrastructure.engines.polars.types import PolarsTypeMapper

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
        EngineCapability.LAZY,
    }
)


class PolarsAdapter:
    """Polars adapter implementing the initial portable Transformation set."""

    def __init__(
        self,
        expression_compiler: PolarsExpressionCompiler | None = None,
        type_mapper: PolarsTypeMapper | None = None,
    ) -> None:
        self._expression_compiler = (
            expression_compiler or PolarsExpressionCompiler()
        )
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

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: DatasetHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        if not isinstance(input_handle, PolarsDatasetHandle):
            raise AdapterError(
                "PolarsAdapter requires a PolarsDatasetHandle."
            )

        self._compatibility.validate(plan, self.descriptor)
        frame = self._prepare_frame(input_handle.frame, context.mode)

        for node in plan.nodes:
            if node.transformation is None:
                continue
            frame = self._execute_transformation(
                frame,
                node.transformation,
            )

        if (
            context.mode is ExecutionMode.EAGER
            and isinstance(frame, pl.LazyFrame)
        ):
            frame = frame.collect()

        return EngineExecutionResult(
            output_handle=PolarsDatasetHandle(frame),
            output_schema=plan.output_schema,
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
    ) -> Any:
        if isinstance(transformation, SelectTransformation):
            return frame.select(
                [str(field) for field in transformation.fields]
            )

        if isinstance(transformation, DropTransformation):
            return frame.drop(
                [str(field) for field in transformation.fields]
            )

        if isinstance(transformation, RenameTransformation):
            return frame.rename(
                {
                    str(item.source): item.target
                    for item in transformation.renames
                }
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
                self._type_mapper.to_native(
                    transformation.target_type
                ),
                strict=transformation.policy is not CastPolicy.NULL,
            )
            return frame.with_columns(expression.alias(field_name))

        if isinstance(transformation, DeriveTransformation):
            expression = self._expression_compiler.compile(
                transformation.expression,
                frame,
            )
            return frame.with_columns(
                expression.alias(transformation.field_name)
            )

        if isinstance(transformation, SortTransformation):
            return frame.sort(
                by=[str(key.field) for key in transformation.keys],
                descending=[
                    key.direction.value == "desc"
                    for key in transformation.keys
                ],
                nulls_last=[
                    key.nulls.value == "last"
                    for key in transformation.keys
                ],
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


def _package_version() -> str:
    try:
        return version("pytransformkit")
    except PackageNotFoundError:
        return "0.1.0a1"
