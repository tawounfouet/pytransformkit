"""Static output Schema resolution for logical Transformations."""

from dataclasses import replace

from pytransformkit.domain.data.data_types import BooleanType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.typing import ExpressionTypeResolver
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.casting import (
    CastPolicy,
    CastTransformation,
)
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
)
from pytransformkit.domain.transformations.derivation import (
    DeriveTransformation,
)
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
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.errors.schema import FieldCollisionError
from pytransformkit.errors.transformation import (
    UnsupportedTransformationError,
)


class OutputSchemaResolver:
    """Resolve output Schema without executing physical data."""

    def __init__(
        self,
        expression_type_resolver: ExpressionTypeResolver | None = None,
    ) -> None:
        self._expression_type_resolver = (
            expression_type_resolver or ExpressionTypeResolver()
        )

    def resolve(
        self,
        transformation: TransformationSpec,
        input_schema: Schema,
    ) -> Schema:
        if isinstance(transformation, SelectTransformation):
            return input_schema.select(
                tuple(str(field) for field in transformation.fields)
            )

        if isinstance(transformation, DropTransformation):
            return input_schema.drop(
                tuple(str(field) for field in transformation.fields)
            )

        if isinstance(transformation, RenameTransformation):
            return input_schema.rename(
                {
                    str(item.source): item.target
                    for item in transformation.renames
                }
            )

        if isinstance(transformation, FilterTransformation):
            condition_type = self._expression_type_resolver.resolve(
                transformation.condition,
                input_schema,
            )
            if not isinstance(condition_type.data_type, BooleanType):
                raise ExpressionTypeError(
                    "Filter condition must resolve to BooleanType."
                )
            return input_schema

        if isinstance(transformation, LimitTransformation):
            return input_schema

        if isinstance(transformation, DistinctTransformation):
            return input_schema

        if isinstance(transformation, CastTransformation):
            field_name = str(transformation.field)
            current = input_schema.field(field_name)
            nullable = (
                True
                if transformation.policy is CastPolicy.NULL
                else current.nullable
            )
            return input_schema.replace(
                replace(
                    current,
                    data_type=transformation.target_type,
                    nullable=nullable,
                )
            )

        if isinstance(transformation, DeriveTransformation):
            expression_type = self._expression_type_resolver.resolve(
                transformation.expression,
                input_schema,
            )
            derived_field = Field(
                name=transformation.field_name,
                data_type=expression_type.data_type,
                nullable=expression_type.nullable,
            )

            if input_schema.has_field(transformation.field_name):
                if not transformation.replace_existing:
                    raise FieldCollisionError(
                        transformation.field_name
                    )
                return input_schema.replace(derived_field)

            return input_schema.append(derived_field)

        if isinstance(transformation, SortTransformation):
            for key in transformation.keys:
                input_schema.field(str(key.field))
            return input_schema

        if isinstance(transformation, DeduplicateTransformation):
            for key in transformation.keys:
                input_schema.field(str(key))
            return input_schema

        raise UnsupportedTransformationError(
            "No output Schema resolver exists for "
            f"{type(transformation).__name__!r}."
        )
