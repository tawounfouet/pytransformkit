"""Static output Schema resolution for logical Transformations."""

from dataclasses import replace

from pytransformkit.domain.data.data_types import (
    BooleanType,
    DecimalType,
    FloatType,
    IntegerType,
    ListType,
    StringType,
    StructType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.typing import (
    AggregateExpressionTypeResolver,
    ExpressionTypeResolver,
    WindowExpressionTypeResolver,
)
from pytransformkit.domain.expressions.window import WindowExpression
from pytransformkit.domain.quality.rules import (
    AllowedValues,
    ExpressionValidation,
    NotNull,
    Range,
    Regex,
    RowCount,
    SchemaValidation,
    Unique,
)
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
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
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
        aggregate_type_resolver: AggregateExpressionTypeResolver | None = None,
        window_type_resolver: WindowExpressionTypeResolver | None = None,
    ) -> None:
        self._expression_type_resolver = (
            expression_type_resolver or ExpressionTypeResolver()
        )
        self._aggregate_type_resolver = (
            aggregate_type_resolver
            or AggregateExpressionTypeResolver(self._expression_type_resolver)
        )
        self._window_type_resolver = (
            window_type_resolver
            or WindowExpressionTypeResolver(
                self._expression_type_resolver,
                self._aggregate_type_resolver,
            )
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
            if isinstance(transformation.expression, WindowExpression):
                expression_type = self._window_type_resolver.resolve(
                    transformation.expression,
                    input_schema,
                )
            else:
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

        if isinstance(transformation, AggregateTransformation):
            return self._resolve_aggregate(
                transformation,
                input_schema,
            )

        if isinstance(transformation, PivotTransformation):
            return self._resolve_pivot(transformation, input_schema)

        if isinstance(transformation, UnpivotTransformation):
            return self._resolve_unpivot(transformation, input_schema)

        if isinstance(transformation, ExplodeTransformation):
            return self._resolve_explode(transformation, input_schema)

        if isinstance(transformation, FlattenTransformation):
            return self._resolve_flatten(transformation, input_schema)

        if isinstance(transformation, QualityGate):
            self._validate_quality_gate(
                transformation,
                input_schema,
            )
            return input_schema

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

    def _validate_quality_gate(
        self,
        transformation: QualityGate,
        input_schema: Schema,
    ) -> None:
        for rule in transformation.spec.rules:
            if isinstance(rule, NotNull):
                input_schema.resolve_path(rule.field)
                continue

            if isinstance(rule, Unique):
                for field_path in rule.fields:
                    input_schema.resolve_path(field_path)
                continue

            if isinstance(rule, Range):
                input_schema.resolve_path(rule.field)
                continue

            if isinstance(rule, AllowedValues):
                input_schema.resolve_path(rule.field)
                continue

            if isinstance(rule, Regex):
                regex_field = input_schema.resolve_path(rule.field)
                if not isinstance(regex_field.data_type, StringType):
                    raise InvalidTransformationError(
                        "Regex validation requires a StringType field."
                    )
                continue

            if isinstance(rule, SchemaValidation):
                continue

            if isinstance(rule, RowCount):
                continue

            if isinstance(rule, ExpressionValidation):
                expression_type = self._expression_type_resolver.resolve(
                    rule.expression,
                    input_schema,
                )
                if not isinstance(expression_type.data_type, BooleanType):
                    raise ExpressionTypeError(
                        "ExpressionValidation condition must resolve to BooleanType."
                    )
                continue

            raise InvalidTransformationError(
                f"Unsupported ValidationRule {type(rule).__name__!r}."
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

    def _resolve_aggregate(
        self,
        transformation: AggregateTransformation,
        input_schema: Schema,
    ) -> Schema:
        fields: list[Field] = []
        used_names: set[str] = set()

        for index, expression in enumerate(transformation.group_by):
            expression_type = self._expression_type_resolver.resolve(
                expression,
                input_schema,
            )
            name = group_output_name(expression, index)
            if name in used_names:
                raise FieldCollisionError(name)
            fields.append(
                Field(
                    name=name,
                    data_type=expression_type.data_type,
                    nullable=expression_type.nullable,
                )
            )
            used_names.add(name)

        for metric in transformation.metrics:
            if metric.name in used_names:
                raise FieldCollisionError(metric.name)
            expression_type = self._aggregate_type_resolver.resolve(
                metric.expression,
                input_schema,
            )
            fields.append(
                Field(
                    name=metric.name,
                    data_type=expression_type.data_type,
                    nullable=expression_type.nullable,
                )
            )
            used_names.add(metric.name)

        return Schema(tuple(fields))

    @staticmethod
    def _resolve_pivot(
        transformation: PivotTransformation,
        input_schema: Schema,
    ) -> Schema:
        index_fields = tuple(
            input_schema.field(str(path)) for path in transformation.index
        )
        category_field = input_schema.field(str(transformation.columns))
        value_field = input_schema.field(str(transformation.values))

        if not isinstance(category_field.data_type, StringType):
            raise InvalidTransformationError("Pivot columns field must use StringType.")

        used_names = {field.name for field in index_fields}
        output_fields = list(index_fields)

        for category in transformation.categories:
            if category in used_names:
                raise FieldCollisionError(category)
            output_fields.append(
                _pivot_output_field(
                    category,
                    value_field,
                    transformation.aggregation,
                )
            )
            used_names.add(category)

        return Schema(tuple(output_fields))

    @staticmethod
    def _resolve_unpivot(
        transformation: UnpivotTransformation,
        input_schema: Schema,
    ) -> Schema:
        id_fields = tuple(
            input_schema.field(str(path)) for path in transformation.id_vars
        )
        value_fields = tuple(
            input_schema.field(str(path)) for path in transformation.value_vars
        )

        first = value_fields[0]
        for field in value_fields[1:]:
            if field.data_type != first.data_type:
                raise InvalidTransformationError(
                    "Unpivot value fields must use identical logical DataTypes."
                )

        reserved = {field.name for field in id_fields}
        if transformation.variable_name in reserved:
            raise FieldCollisionError(transformation.variable_name)
        if transformation.value_name in reserved:
            raise FieldCollisionError(transformation.value_name)

        return Schema(
            id_fields
            + (
                Field(
                    name=transformation.variable_name,
                    data_type=StringType(),
                    nullable=False,
                ),
                Field(
                    name=transformation.value_name,
                    data_type=first.data_type,
                    nullable=any(field.nullable for field in value_fields),
                ),
            )
        )

    @staticmethod
    def _resolve_explode(
        transformation: ExplodeTransformation,
        input_schema: Schema,
    ) -> Schema:
        field_name = str(transformation.field)
        current = input_schema.field(field_name)
        if not isinstance(current.data_type, ListType):
            raise InvalidTransformationError("Explode requires a ListType field.")
        return input_schema.replace(
            replace(
                current,
                data_type=current.data_type.element_type,
                nullable=True,
            )
        )

    @staticmethod
    def _resolve_flatten(
        transformation: FlattenTransformation,
        input_schema: Schema,
    ) -> Schema:
        field_name = str(transformation.field)
        current = input_schema.field(field_name)
        if not isinstance(current.data_type, StructType):
            raise InvalidTransformationError("Flatten requires a StructType field.")

        existing = {
            field.name for field in input_schema.fields if field.name != field_name
        }
        flattened: list[Field] = []

        for nested in current.data_type.fields:
            output_name = transformation.output_name(nested.name)
            if output_name in existing:
                raise FieldCollisionError(output_name)
            flattened.append(
                Field(
                    name=output_name,
                    data_type=nested.data_type,
                    nullable=current.nullable or nested.nullable,
                )
            )
            existing.add(output_name)

        output_fields: list[Field] = []
        for field in input_schema.fields:
            if field.name == field_name:
                output_fields.extend(flattened)
            else:
                output_fields.append(field)

        return Schema(tuple(output_fields))

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

        right_join_keys = {str(key.right) for key in transformation.keys}

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


def _pivot_output_field(
    name: str,
    value_field: Field,
    aggregation: PivotAggregation,
) -> Field:
    if aggregation is PivotAggregation.COUNT:
        return Field(
            name=name,
            data_type=IntegerType(bits=64),
            nullable=False,
        )

    if aggregation is PivotAggregation.MEAN:
        if not isinstance(
            value_field.data_type,
            (IntegerType, FloatType, DecimalType),
        ):
            raise InvalidTransformationError(
                "Pivot MEAN requires a numeric values field."
            )
        return Field(
            name=name,
            data_type=FloatType(bits=64),
            nullable=True,
        )

    if aggregation is PivotAggregation.SUM:
        if not isinstance(
            value_field.data_type,
            (IntegerType, FloatType, DecimalType),
        ):
            raise InvalidTransformationError(
                "Pivot SUM requires a numeric values field."
            )
        data_type = value_field.data_type
        if isinstance(data_type, IntegerType):
            data_type = IntegerType(bits=64, signed=data_type.signed)
        return Field(
            name=name,
            data_type=data_type,
            nullable=True,
        )

    if aggregation in {PivotAggregation.MIN, PivotAggregation.MAX}:
        return Field(
            name=name,
            data_type=value_field.data_type,
            nullable=True,
        )

    raise UnsupportedTransformationError(
        f"Unsupported pivot aggregation {aggregation.value!r}."
    )
