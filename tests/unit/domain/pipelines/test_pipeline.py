from __future__ import annotations

from pytransformkit.domain.data.data_types import (
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    TransformationNode,
)
from pytransformkit.domain.pipelines.pipeline import Pipeline
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
)
from pytransformkit.domain.transformations.derivation import DeriveTransformation
from pytransformkit.domain.transformations.filtering import FilterTransformation
from pytransformkit.domain.transformations.projection import SelectTransformation
from pytransformkit.functions import col, lower


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def test_create_pipeline_has_single_input_and_output() -> None:
    pipeline = Pipeline.create("customers", _schema())

    assert len(pipeline.nodes) == 2
    assert len(pipeline.dependencies) == 1
    assert isinstance(pipeline.nodes[0], InputNode)
    assert isinstance(pipeline.nodes[1], OutputNode)
    assert pipeline.dependencies[0].source == pipeline.input_node.id
    assert pipeline.dependencies[0].target == pipeline.output_node.id


def test_then_returns_new_immutable_pipeline_with_same_identity() -> None:
    original = Pipeline.create("customers", _schema())
    transformed = original.then(
        FilterTransformation(condition=col("customer_id").is_not_null())
    )

    assert transformed is not original
    assert transformed.id == original.id
    assert transformed == original
    assert len(original.transformation_nodes) == 0
    assert len(transformed.transformation_nodes) == 1


def test_then_inserts_transformation_before_output() -> None:
    pipeline = Pipeline.create("customers", _schema()).then(
        FilterTransformation(condition=col("email").is_not_null())
    )

    transformation_node = pipeline.transformation_nodes[0]
    edges = {
        (dependency.source, dependency.target) for dependency in pipeline.dependencies
    }

    assert (
        pipeline.input_node.id,
        transformation_node.id,
    ) in edges
    assert (
        transformation_node.id,
        pipeline.output_node.id,
    ) in edges


def test_sequential_dsl_builds_expected_transformation_specs() -> None:
    pipeline = (
        Pipeline.create("customers", _schema())
        .select("customer_id", "email", "status")
        .filter(col("customer_id").is_not_null())
        .derive(
            "normalized_email",
            lower(col("email")),
        )
        .deduplicate(keys=("customer_id",))
    )

    transformations = tuple(
        node.transformation for node in pipeline.transformation_nodes
    )

    assert len(transformations) == 4
    assert isinstance(transformations[0], SelectTransformation)
    assert isinstance(transformations[1], FilterTransformation)
    assert isinstance(transformations[2], DeriveTransformation)
    assert isinstance(transformations[3], DeduplicateTransformation)


def test_public_package_exports_pipeline_without_optional_engines() -> None:
    from pytransformkit import Pipeline as PublicPipeline

    assert PublicPipeline is Pipeline


def test_transformation_node_step_ids_are_unique() -> None:
    pipeline = (
        Pipeline.create("customers", _schema())
        .filter(col("email").is_not_null())
        .filter(col("status") == "active")
    )

    step_ids = tuple(
        node.step_id for node in pipeline.nodes if isinstance(node, TransformationNode)
    )

    assert len(step_ids) == len(set(step_ids))
