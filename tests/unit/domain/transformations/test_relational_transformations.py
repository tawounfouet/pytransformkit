from __future__ import annotations

import pytest

from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinKey,
    JoinTransformation,
    JoinType,
    NullJoinPolicy,
    UnionTransformation,
    relational_input_count,
)
from pytransformkit.errors.transformation import InvalidTransformationError


def test_join_key_uses_same_field_when_right_is_omitted() -> None:
    key = JoinKey.of("customer_id")

    assert str(key.left) == "customer_id"
    assert str(key.right) == "customer_id"


def test_non_cross_join_requires_keys() -> None:
    with pytest.raises(InvalidTransformationError, match="at least one"):
        JoinTransformation()


def test_cross_join_rejects_equality_keys() -> None:
    with pytest.raises(InvalidTransformationError, match="must not"):
        JoinTransformation(
            how=JoinType.CROSS,
            keys=(JoinKey.of("customer_id"),),
        )


def test_join_rejects_duplicate_keys() -> None:
    key = JoinKey.of("customer_id")

    with pytest.raises(InvalidTransformationError, match="unique"):
        JoinTransformation(keys=(key, key))


def test_join_preserves_explicit_null_policy() -> None:
    transformation = JoinTransformation(
        keys=(JoinKey.of("customer_id"),),
        how=JoinType.LEFT,
        nulls=NullJoinPolicy.NEVER_MATCH,
    )

    assert transformation.how is JoinType.LEFT
    assert transformation.nulls is NullJoinPolicy.NEVER_MATCH


@pytest.mark.parametrize(
    "transformation",
    [
        JoinTransformation(keys=(JoinKey.of("customer_id"),)),
        UnionTransformation(),
        IntersectTransformation(),
        ExceptTransformation(),
    ],
)
def test_relational_transformations_require_two_inputs(
    transformation: object,
) -> None:
    assert relational_input_count(transformation) == 2


def test_union_all_is_explicit() -> None:
    assert UnionTransformation().all is False
    assert UnionTransformation(all=True).all is True
