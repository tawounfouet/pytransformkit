from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinKey,
    JoinTransformation,
    JoinType,
    UnionTransformation,
)
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.errors.transformation import InvalidTransformationError


def _customers() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("country", StringType(), nullable=False),
            Field("status", StringType(), nullable=False),
        )
    )


def _orders() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("amount", IntegerType(), nullable=False),
        )
    )


def test_inner_join_schema_keeps_one_same_name_key_and_suffixes_collision() -> None:
    output = OutputSchemaResolver().resolve_many(
        JoinTransformation(
            keys=(JoinKey.of("customer_id"),),
            how=JoinType.INNER,
            right_suffix="_order",
        ),
        (_customers(), _orders()),
    )

    assert output.names() == (
        "customer_id",
        "country",
        "status",
        "status_order",
        "amount",
    )


def test_left_join_makes_right_non_key_fields_nullable() -> None:
    output = OutputSchemaResolver().resolve_many(
        JoinTransformation(
            keys=(JoinKey.of("customer_id"),),
            how=JoinType.LEFT,
        ),
        (_customers(), _orders()),
    )

    assert output.field("amount").nullable is True
    assert output.field("customer_id").nullable is False


def test_right_join_makes_left_fields_nullable() -> None:
    output = OutputSchemaResolver().resolve_many(
        JoinTransformation(
            keys=(JoinKey.of("customer_id"),),
            how=JoinType.RIGHT,
        ),
        (_customers(), _orders()),
    )

    assert output.field("customer_id").nullable is True
    assert output.field("country").nullable is True
    assert output.field("amount").nullable is False


def test_semi_and_anti_join_keep_left_schema() -> None:
    resolver = OutputSchemaResolver()

    for how in (JoinType.SEMI, JoinType.ANTI):
        output = resolver.resolve_many(
            JoinTransformation(
                keys=(JoinKey.of("customer_id"),),
                how=how,
            ),
            (_customers(), _orders()),
        )
        assert output == _customers()


def test_join_requires_compatible_key_types() -> None:
    incompatible = Schema(
        fields=(
            Field("customer_id", StringType(), nullable=False),
        )
    )

    with pytest.raises(InvalidTransformationError, match="types"):
        OutputSchemaResolver().resolve_many(
            JoinTransformation(
                keys=(JoinKey.of("customer_id"),),
            ),
            (_customers(), incompatible),
        )


@pytest.mark.parametrize(
    "transformation",
    [
        UnionTransformation(),
        IntersectTransformation(),
        ExceptTransformation(),
    ],
)
def test_set_operations_preserve_identical_schema(
    transformation: UnionTransformation
    | IntersectTransformation
    | ExceptTransformation,
) -> None:
    schema = _customers()

    output = OutputSchemaResolver().resolve_many(
        transformation,
        (schema, schema),
    )

    assert output is schema


def test_set_operations_reject_schema_drift() -> None:
    with pytest.raises(InvalidTransformationError, match="field names"):
        OutputSchemaResolver().resolve_many(
            UnionTransformation(),
            (
                _customers(),
                Schema(
                    fields=(
                        Field("id", IntegerType(), nullable=False),
                        Field("country", StringType(), nullable=False),
                        Field("status", StringType(), nullable=False),
                    )
                ),
            ),
        )
