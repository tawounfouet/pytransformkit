from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.schema import Schema
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
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.domain.transformations.sorting import (
    SortKey,
    SortTransformation,
)
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.errors.schema import (
    FieldCollisionError,
    FieldNotFoundError,
)
from pytransformkit.errors.transformation import UnsupportedTransformationError
from pytransformkit.functions import col, lower


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


@pytest.fixture
def resolver() -> OutputSchemaResolver:
    return OutputSchemaResolver()


def test_select_resolves_requested_order(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        SelectTransformation(
            fields=(
                FieldPath.of("status"),
                FieldPath.of("customer_id"),
            )
        ),
        schema,
    )

    assert output.names() == ("status", "customer_id")


def test_drop_resolves_remaining_fields(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        DropTransformation(fields=(FieldPath.of("amount"),)),
        schema,
    )

    assert output.names() == ("customer_id", "email", "status")


def test_rename_resolves_simultaneous_mapping(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        RenameTransformation.from_mapping(
            {
                "email": "normalized_email",
                "status": "customer_status",
            }
        ),
        schema,
    )

    assert output.names() == (
        "customer_id",
        "normalized_email",
        "customer_status",
        "amount",
    )


def test_filter_requires_boolean_expression(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    with pytest.raises(ExpressionTypeError, match="BooleanType"):
        resolver.resolve(
            FilterTransformation(condition=col("email")),
            schema,
        )


def test_filter_preserves_schema(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        FilterTransformation(
            condition=col("customer_id").is_not_null()
        ),
        schema,
    )

    assert output is schema


@pytest.mark.parametrize(
    "transformation",
    [
        LimitTransformation(count=10),
        DistinctTransformation(),
    ],
)
def test_row_selection_primitives_preserve_schema(
    schema: Schema,
    resolver: OutputSchemaResolver,
    transformation: TransformationSpec,
) -> None:
    assert resolver.resolve(transformation, schema) is schema


def test_cast_updates_logical_type(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        CastTransformation(
            field=FieldPath.of("amount"),
            target_type=IntegerType(),
        ),
        schema,
    )

    assert output.field("amount").data_type == IntegerType()
    assert output.field("amount").nullable is True


def test_null_cast_policy_makes_output_nullable(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        CastTransformation(
            field=FieldPath.of("status"),
            target_type=IntegerType(),
            policy=CastPolicy.NULL,
        ),
        schema,
    )

    assert output.field("status").nullable is True


def test_derive_appends_typed_field(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        DeriveTransformation(
            field_name="normalized_email",
            expression=lower(col("email")),
        ),
        schema,
    )

    assert output.names() == (
        "customer_id",
        "email",
        "status",
        "amount",
        "normalized_email",
    )
    assert output.field("normalized_email").data_type == StringType()
    assert output.field("normalized_email").nullable is True


def test_derive_rejects_collision_without_explicit_replace(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    with pytest.raises(FieldCollisionError):
        resolver.resolve(
            DeriveTransformation(
                field_name="email",
                expression=lower(col("email")),
            ),
            schema,
        )


def test_derive_can_explicitly_replace_existing_field(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    output = resolver.resolve(
        DeriveTransformation(
            field_name="email",
            expression=lower(col("email")),
            replace_existing=True,
        ),
        schema,
    )

    assert output.names() == schema.names()
    assert output.field("email").data_type == StringType()


def test_sort_validates_key_presence(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    with pytest.raises(FieldNotFoundError):
        resolver.resolve(
            SortTransformation(
                keys=(SortKey(FieldPath.of("missing")),)
            ),
            schema,
        )


def test_deduplicate_validates_key_presence(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    with pytest.raises(FieldNotFoundError):
        resolver.resolve(
            DeduplicateTransformation(
                keys=(FieldPath.of("missing"),)
            ),
            schema,
        )


def test_unknown_transformation_is_rejected(
    schema: Schema,
    resolver: OutputSchemaResolver,
) -> None:
    class UnknownTransformation(TransformationSpec):
        pass

    with pytest.raises(UnsupportedTransformationError):
        resolver.resolve(UnknownTransformation(), schema)
