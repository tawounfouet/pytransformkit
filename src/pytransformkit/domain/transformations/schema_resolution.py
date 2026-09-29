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
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
    UnionTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.errors.schema import FieldCollisionError
from pytransformkit.errors.transformation import (
    InvalidTransformationError,
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
        """Resolve one-input transformation schema."""
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
                {str(item.source): item.target for item in transformation.renames}
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
                True if transformation.policy is CastPolicy.NULL else current.nullable
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
                    raise FieldCollisionError(transformation.field_name)
                return input_schema.replace(derived_field)

            return input_schema.append(derived_field)

        if isinstance(transformation, SortTransformation):
            for key in transformation.keys:
                input_schema.field(str(key.field))
            return input_schema

        if isinstance(transformation, DeduplicateTransformation):
            for field_path in transformation.keys:
                input_schema.field(str(field_path))
            return input_schema

        raise UnsupportedTransformationError(
            f"No output Schema resolver exists for {type(transformation).__name__!r}."
        )

    def resolve_many(
        self,
        transformation: TransformationSpec,
        input_schemas: tuple[Schema, ...],
    ) -> Schema:
        """Resolve a multi-input transformation schema."""
        if not isinstance(input_schemas, tuple):
            raise TypeError("input_schemas must be provided as a tuple.")

        if isinstance(transformation, JoinTransformation):
            if len(input_schemas) != 2:
                raise InvalidTransformationError(
                    "JoinTransformation requires exactly two input Schemas."
                )
            return self._resolve_join(
                transformation,
                input_schemas[0],
                input_schemas[1],
            )

        if isinstance(
            transformation,
            (
                UnionTransformation,
                IntersectTransformation,
                ExceptTransformation,
            ),
        ):
            if len(input_schemas) != 2:
                raise InvalidTransformationError(
                    f"{type(transformation).__name__} requires exactly "
                    "two input Schemas."
                )
            _validate_set_compatible(input_schemas[0], input_schemas[1])
            return input_schemas[0]

        if len(input_schemas) == 1:
            return self.resolve(transformation, input_schemas[0])

        raise UnsupportedTransformationError(
            "No multi-input output Schema resolver exists for "
            f"{type(transformation).__name__!r}."
        )

    @staticmethod
    def _resolve_join(
        transformation: JoinTransformation,
        left: Schema,
        right: Schema,
    ) -> Schema:
        if transformation.how is not JoinType.CROSS:
            for key in transformation.keys:
                left_field = left.field(str(key.left))
                right_field = right.field(str(key.right))
                if left_field.data_type != right_field.data_type:
                    raise InvalidTransformationError(
                        "Join key types must match exactly: "
                        f"{key.left!s}={left_field.data_type!r}, "
                        f"{key.right!s}={right_field.data_type!r}."
                    )

        if transformation.how in {JoinType.SEMI, JoinType.ANTI}:
            return left

        left_nullable = transformation.how in {
            JoinType.RIGHT,
            JoinType.FULL,
        }
        right_nullable = transformation.how in {
            JoinType.LEFT,
            JoinType.FULL,
        }

        fields: list[Field] = [
            replace(field, nullable=True) if left_nullable else field
            for field in left.fields
        ]
        used_names = {field.name for field in fields}

        right_join_keys = {
            str(key.right)
            for key in transformation.keys
        }

        for field in right.fields:
            if field.name in right_join_keys:
                continue

            output_name = field.name
            if output_name in used_names:
                output_name = f"{output_name}{transformation.right_suffix}"
            if output_name in used_names:
                raise FieldCollisionError(output_name)

            output_field = field
            if output_name != field.name or right_nullable:
                output_field = replace(
                    field,
                    name=output_name,
                    nullable=(True if right_nullable else field.nullable),
                )
            fields.append(output_field)
            used_names.add(output_name)

        return Schema(tuple(fields))


def _validate_set_compatible(left: Schema, right: Schema) -> None:
    if len(left.fields) != len(right.fields):
        raise InvalidTransformationError(
            "Set operations require Schemas with the same field count."
        )

    for index, (left_field, right_field) in enumerate(
        zip(left.fields, right.fields, strict=True)
    ):
        if left_field.name != right_field.name:
            raise InvalidTransformationError(
                "Set operations require identical field names and ordering; "
                f"position {index} differs."
            )
        if left_field.data_type != right_field.data_type:
            raise InvalidTransformationError(
                "Set operations require identical logical DataTypes; "
                f"field {left_field.name!r} differs."
            )
        if left_field.nullable != right_field.nullable:
            raise InvalidTransformationError(
                "Set operations require identical nullability; "
                f"field {left_field.name!r} differs."
            )
