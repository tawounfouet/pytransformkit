from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import IntegerType
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.transformations.casting import (
    CastPolicy,
    CastTransformation,
)
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
    DeduplicationStrategy,
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
from pytransformkit.domain.transformations.properties import (
    CardinalityEffect,
    SchemaEffect,
)
from pytransformkit.domain.transformations.sorting import (
    NullOrder,
    SortDirection,
    SortKey,
    SortTransformation,
)
from pytransformkit.errors.transformation import InvalidTransformationError
from pytransformkit.functions import col, lower


def test_select_is_portable_projection_spec() -> None:
    transformation = SelectTransformation(
        fields=(FieldPath.of("email"), FieldPath.of("customer_id"))
    )

    assert transformation.identifier == "core.select"
    assert transformation.properties.schema is SchemaEffect.PROJECT
    assert transformation.properties.cardinality is CardinalityEffect.PRESERVE


def test_select_rejects_duplicate_fields() -> None:
    with pytest.raises(InvalidTransformationError, match="unique"):
        SelectTransformation(fields=(FieldPath.of("email"), FieldPath.of("email")))


def test_drop_rejects_duplicate_fields() -> None:
    with pytest.raises(InvalidTransformationError, match="unique"):
        DropTransformation(fields=(FieldPath.of("email"), FieldPath.of("email")))


def test_rename_can_be_built_from_mapping() -> None:
    transformation = RenameTransformation.from_mapping(
        {
            "email": "normalized_email",
            "status": "customer_status",
        }
    )

    assert tuple(str(item.source) for item in transformation.renames) == (
        "email",
        "status",
    )
    assert tuple(item.target for item in transformation.renames) == (
        "normalized_email",
        "customer_status",
    )


def test_rename_requires_at_least_one_field() -> None:
    with pytest.raises(InvalidTransformationError, match="at least one"):
        RenameTransformation.from_mapping({})


def test_filter_requires_expression() -> None:
    with pytest.raises(TypeError, match="Expression"):
        FilterTransformation(condition=True)  # type: ignore[arg-type]


def test_limit_rejects_negative_count() -> None:
    with pytest.raises(InvalidTransformationError, match="non-negative"):
        LimitTransformation(count=-1)


def test_limit_rejects_boolean_count() -> None:
    with pytest.raises(TypeError, match="integer"):
        LimitTransformation(count=True)


def test_distinct_has_stable_identifier() -> None:
    assert DistinctTransformation().identifier == "core.distinct"


def test_cast_preserves_explicit_policy() -> None:
    transformation = CastTransformation(
        field=FieldPath.of("customer_id"),
        target_type=IntegerType(bits=32),
        policy=CastPolicy.NULL,
    )

    assert transformation.policy is CastPolicy.NULL
    assert transformation.target_type == IntegerType(bits=32)


def test_derive_requires_non_empty_name() -> None:
    with pytest.raises(InvalidTransformationError, match="name"):
        DeriveTransformation(
            field_name=" ",
            expression=lower(col("email")),
        )


def test_sort_requires_unique_keys() -> None:
    key = SortKey(
        field=FieldPath.of("created_at"),
        direction=SortDirection.DESC,
        nulls=NullOrder.FIRST,
    )

    with pytest.raises(InvalidTransformationError, match="unique"):
        SortTransformation(keys=(key, key))


def test_deduplicate_requires_key() -> None:
    with pytest.raises(InvalidTransformationError, match="at least one"):
        DeduplicateTransformation(keys=())


def test_deduplicate_preserves_strategy() -> None:
    transformation = DeduplicateTransformation(
        keys=(FieldPath.of("customer_id"),),
        keep=DeduplicationStrategy.LAST,
    )

    assert transformation.keep is DeduplicationStrategy.LAST
    assert transformation.identifier == "core.deduplicate"
