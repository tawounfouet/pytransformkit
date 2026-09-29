from __future__ import annotations

import pytest

from pytransformkit import TransformationPlan
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    ListType,
    StringType,
    StructField,
    StructType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.transformations.reshaping import (
    ExplodeTransformation,
    FlattenTransformation,
    PivotAggregation,
    PivotTransformation,
    UnpivotTransformation,
)
from pytransformkit.domain.transformations.schema_resolution import OutputSchemaResolver
from pytransformkit.errors.schema import FieldCollisionError
from pytransformkit.errors.transformation import InvalidTransformationError


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("category", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
            Field("q1", FloatType(), nullable=True),
            Field("q2", FloatType(), nullable=True),
            Field(
                "tags",
                ListType(StringType(), element_nullable=False),
                nullable=False,
            ),
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField("city", StringType(), nullable=False),
                        StructField("score", IntegerType(), nullable=True),
                    )
                ),
                nullable=True,
            ),
        )
    )


def test_pivot_schema_is_static_from_explicit_categories(schema: Schema) -> None:
    transformation = PivotTransformation(
        index=(),
        columns=_path("category"),
        values=_path("amount"),
        categories=("A", "B", "C"),
        aggregation=PivotAggregation.SUM,
    )

    output = OutputSchemaResolver().resolve(transformation, schema)

    assert output.names() == ("A", "B", "C")
    assert all(field.data_type == FloatType() for field in output.fields)
    assert all(field.nullable for field in output.fields)


def test_pivot_count_uses_non_nullable_int64_outputs(schema: Schema) -> None:
    transformation = PivotTransformation(
        index=(_path("customer_id"),),
        columns=_path("category"),
        values=_path("amount"),
        categories=("A", "B"),
        aggregation=PivotAggregation.COUNT,
    )

    output = OutputSchemaResolver().resolve(transformation, schema)

    assert output.names() == ("customer_id", "A", "B")
    assert output.field("A").data_type == IntegerType(bits=64)
    assert output.field("A").nullable is False


def test_pivot_rejects_category_collision_with_index(schema: Schema) -> None:
    transformation = PivotTransformation(
        index=(_path("customer_id"),),
        columns=_path("category"),
        values=_path("amount"),
        categories=("customer_id",),
        aggregation=PivotAggregation.SUM,
    )

    with pytest.raises(FieldCollisionError):
        OutputSchemaResolver().resolve(transformation, schema)


def test_unpivot_requires_identical_value_types(schema: Schema) -> None:
    transformation = UnpivotTransformation(
        id_vars=(_path("customer_id"),),
        value_vars=(_path("q1"), _path("category")),
    )

    with pytest.raises(InvalidTransformationError, match="identical"):
        OutputSchemaResolver().resolve(transformation, schema)


def test_unpivot_schema_is_deterministic(schema: Schema) -> None:
    transformation = UnpivotTransformation(
        id_vars=(_path("customer_id"),),
        value_vars=(_path("q1"), _path("q2")),
        variable_name="quarter",
        value_name="revenue",
    )

    output = OutputSchemaResolver().resolve(transformation, schema)

    assert output.names() == ("customer_id", "quarter", "revenue")
    assert output.field("quarter").data_type == StringType()
    assert output.field("quarter").nullable is False
    assert output.field("revenue").data_type == FloatType()


def test_explode_replaces_list_type_with_nullable_element(schema: Schema) -> None:
    output = OutputSchemaResolver().resolve(
        ExplodeTransformation(field=_path("tags")),
        schema,
    )

    assert output.field("tags").data_type == StringType()
    assert output.field("tags").nullable is True


def test_flatten_replaces_struct_with_prefixed_fields(schema: Schema) -> None:
    output = OutputSchemaResolver().resolve(
        FlattenTransformation(field=_path("profile")),
        schema,
    )

    assert output.names()[-2:] == ("profile_city", "profile_score")
    assert "profile" not in output.names()
    assert output.field("profile_city").data_type == StringType()
    assert output.field("profile_city").nullable is True


def test_builder_authors_all_reshaping_transformations(schema: Schema) -> None:
    builder = TransformationPlan.builder("reshape")
    source = builder.input("source", schema=schema)

    exploded = builder.explode(
        "exploded",
        source=source,
        field="tags",
    )
    flattened = builder.flatten(
        "flattened",
        source=source,
        field="profile",
    )
    unpivoted = builder.unpivot(
        "unpivoted",
        source=source,
        id_vars=("customer_id",),
        value_vars=("q1", "q2"),
    )
    pivoted = builder.pivot(
        "pivoted",
        source=source,
        index=("customer_id",),
        columns="category",
        values="amount",
        categories=("A", "B"),
        aggregation=PivotAggregation.SUM,
    )

    builder.output("exploded", exploded)
    builder.output("flattened", flattened)
    builder.output("unpivoted", unpivoted)
    plan = builder.output("pivoted", pivoted).build()

    assert len(plan.transformation_nodes) == 4


def _path(value: str):
    from pytransformkit.domain.data.field_path import FieldPath

    return FieldPath.of(value)
