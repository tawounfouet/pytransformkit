from __future__ import annotations

from pytransformkit import TransformationPlan, lineage, quality, window
from pytransformkit import functions as fn
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    ListType,
    StringType,
    StructField,
    StructType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.lineage import (
    FieldDependencyKind,
    FieldDerivationKind,
    FieldReference,
    LineageConfidence,
    LineageImpactAnalyzer,
    ResourceLineageRole,
)
from pytransformkit.domain.quality import ValidationPolicy, ValidationSpec
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.transformations.reshaping import PivotAggregation
from pytransformkit.planning import TransformationCompiler


def _customer_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", IntegerType(), nullable=True),
            Field(
                "tags",
                ListType(StringType()),
                nullable=True,
            ),
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField("city", StringType(), nullable=False),
                        StructField("segment", StringType(), nullable=True),
                    )
                ),
                nullable=True,
            ),
        )
    )


def _order_schema() -> Schema:
    return Schema(
        fields=(
            Field("order_id", IntegerType(), nullable=False),
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
            Field("ordered_at", IntegerType(), nullable=False),
        )
    )


def test_compilation_preserves_authored_logical_dataset_identity() -> None:
    builder = TransformationPlan.builder("identity")
    source = builder.input("customers", schema=_customer_schema())
    selected = builder.select(
        "selected",
        source=source,
        columns=("customer_id", "email"),
    )
    plan = builder.output("out", selected).build()

    logical_plan = TransformationCompiler().compile(plan)
    input_node = next(node for node in logical_plan.nodes if node.name == "customers")
    selected_node = next(node for node in logical_plan.nodes if node.name == "selected")
    output_node = next(node for node in logical_plan.nodes if node.name == "out")

    assert input_node.dataset_id == source.id
    assert selected_node.dataset_id == selected.id
    assert output_node.dataset_id == selected.id


def test_rename_cast_and_derive_have_exact_field_lineage() -> None:
    builder = TransformationPlan.builder("customer_enrichment")
    source = builder.input("customers", schema=_customer_schema())
    renamed = builder.rename(
        "renamed",
        source=source,
        mapping={"email": "contact_email"},
    )
    casted = builder.cast(
        "casted",
        source=renamed,
        field="amount",
        target_type=FloatType(),
    )
    derived = builder.derive(
        "derived",
        source=casted,
        field_name="amount_plus_one",
        expression=fn.col("amount") + 1,
    )
    plan = builder.output("out", derived).build()

    evidence = lineage.analyze(plan)

    renamed_edge = next(
        edge
        for edge in evidence.field_edges
        if edge.derivation is FieldDerivationKind.RENAMED
    )
    cast_edge = next(
        edge
        for edge in evidence.field_edges
        if edge.derivation is FieldDerivationKind.CAST
    )
    derived_edge = next(
        edge
        for edge in evidence.field_edges
        if edge.target.field_path == FieldPath.of("amount_plus_one")
    )

    assert renamed_edge.source.field_path == FieldPath.of("email")
    assert renamed_edge.target.field_path == FieldPath.of("contact_email")
    assert cast_edge.source.field_path == FieldPath.of("amount")
    assert cast_edge.target.field_path == FieldPath.of("amount")
    assert derived_edge.source.field_path == FieldPath.of("amount")
    assert derived_edge.derivation is FieldDerivationKind.DERIVED
    assert all(
        edge.confidence is LineageConfidence.EXACT for edge in evidence.field_edges
    )


def test_row_selection_ordering_and_quality_dependencies_remain_distinct() -> None:
    builder = TransformationPlan.builder("selection_dependencies")
    source = builder.input("customers", schema=_customer_schema())
    filtered = builder.filter(
        "active",
        source=source,
        where=fn.col("status") == "ACTIVE",
    )
    sorted_rows = builder.sort(
        "sorted",
        source=filtered,
        by=("amount",),
    )
    deduped = builder.deduplicate(
        "deduped",
        source=sorted_rows,
        keys=("customer_id",),
    )
    distinct = builder.distinct("distinct", source=deduped)
    limited = builder.limit("limited", source=distinct, count=100)
    validated = builder.validate(
        "validated",
        source=limited,
        spec=ValidationSpec(
            name="customer_quality",
            policy=ValidationPolicy.WARN_ONLY,
            rules=(
                quality.not_null("email"),
                quality.expression(
                    fn.col("amount") >= 0,
                    name="non_negative_amount",
                ),
            ),
        ),
    )
    plan = builder.output("out", validated).build()

    evidence = lineage.analyze(plan)

    kinds = {dependency.kind for dependency in evidence.dependencies}
    assert FieldDependencyKind.FILTER in kinds
    assert FieldDependencyKind.ORDERING in kinds
    assert FieldDependencyKind.DEDUPLICATION in kinds
    assert FieldDependencyKind.DISTINCT in kinds
    assert FieldDependencyKind.QUALITY in kinds

    quality_paths = {
        str(dependency.field.field_path)
        for dependency in evidence.dependencies
        if dependency.kind is FieldDependencyKind.QUALITY
    }
    assert quality_paths == {"email", "amount"}


def test_join_lineage_tracks_each_side_and_join_predicates() -> None:
    builder = TransformationPlan.builder("joined")
    customers = builder.input("customers", schema=_customer_schema())
    orders = builder.input("orders", schema=_order_schema())
    joined = builder.join(
        "customer_orders",
        left=customers,
        right=orders,
        how="left",
        on=(("customer_id", "customer_id"),),
        right_suffix="_order",
    )
    plan = builder.output("out", joined).build()

    evidence = lineage.analyze(plan)
    output = evidence.output("out")
    customers_ref = evidence.input("customers")
    orders_ref = evidence.input("orders")

    right_status_edge = next(
        edge
        for edge in evidence.field_edges
        if edge.source.dataset == orders_ref
        and edge.source.field_path == FieldPath.of("status")
    )

    assert right_status_edge.target == FieldReference.of(output, "status_order")
    assert any(
        edge.source.dataset == customers_ref
        and edge.source.field_path == FieldPath.of("customer_id")
        and edge.target == FieldReference.of(output, "customer_id")
        for edge in evidence.field_edges
    )

    join_dependencies = tuple(
        dependency
        for dependency in evidence.dependencies
        if dependency.kind is FieldDependencyKind.JOIN
    )
    assert {
        (
            dependency.field.dataset.dataset_id,
            str(dependency.field.field_path),
        )
        for dependency in join_dependencies
    } == {
        (customers_ref.dataset_id, "customer_id"),
        (orders_ref.dataset_id, "customer_id"),
    }


def test_aggregate_lineage_separates_grouping_from_metric_derivation() -> None:
    builder = TransformationPlan.builder("aggregated")
    orders = builder.input("orders", schema=_order_schema())
    aggregated = builder.aggregate(
        "by_status",
        source=orders,
        group_by=(fn.col("status"),),
        metrics={
            "revenue": fn.sum(fn.col("amount")),
            "order_count": fn.count(fn.col("order_id")),
        },
    )
    plan = builder.output("out", aggregated).build()

    evidence = lineage.analyze(plan)
    output = evidence.output("out")

    revenue_edges = tuple(
        edge
        for edge in evidence.field_edges
        if edge.target == FieldReference.of(output, "revenue")
    )
    assert len(revenue_edges) == 1
    assert revenue_edges[0].source.field_path == FieldPath.of("amount")
    assert revenue_edges[0].derivation is FieldDerivationKind.AGGREGATED

    grouping = tuple(
        dependency
        for dependency in evidence.dependencies
        if dependency.kind is FieldDependencyKind.GROUPING
    )
    assert {str(item.field.field_path) for item in grouping} == {"status"}


def test_window_lineage_exposes_value_partition_and_ordering_dependencies() -> None:
    builder = TransformationPlan.builder("windowed")
    orders = builder.input("orders", schema=_order_schema())
    ranked = builder.derive(
        "ranked",
        source=orders,
        field_name="previous_amount",
        expression=window.lag(fn.col("amount")).over(
            window.partition_by("customer_id").order_by("ordered_at")
        ),
    )
    plan = builder.output("out", ranked).build()

    evidence = lineage.analyze(plan)
    target = FieldReference.of(evidence.output("out"), "previous_amount")
    lineage_edges = tuple(
        edge for edge in evidence.field_edges if edge.target == target
    )

    assert {str(edge.source.field_path) for edge in lineage_edges} == {
        "amount",
        "customer_id",
        "ordered_at",
    }
    assert all(
        edge.derivation is FieldDerivationKind.WINDOWED for edge in lineage_edges
    )

    dependency_pairs = {
        (dependency.kind, str(dependency.field.field_path))
        for dependency in evidence.dependencies
    }
    assert (
        FieldDependencyKind.WINDOW,
        "amount",
    ) in dependency_pairs
    assert (
        FieldDependencyKind.WINDOW_PARTITION,
        "customer_id",
    ) in dependency_pairs
    assert (
        FieldDependencyKind.WINDOW_ORDERING,
        "ordered_at",
    ) in dependency_pairs


def test_reshape_lineage_is_static_for_pivot_unpivot_explode_and_flatten() -> None:
    pivot_builder = TransformationPlan.builder("pivot")
    orders = pivot_builder.input("orders", schema=_order_schema())
    pivoted = pivot_builder.pivot(
        "pivoted",
        source=orders,
        index=("customer_id",),
        columns="status",
        values="amount",
        categories=("PAID", "OPEN"),
        aggregation=PivotAggregation.SUM,
    )
    pivot_lineage = lineage.analyze(pivot_builder.output("out", pivoted).build())

    pivot_output = pivot_lineage.output("out")
    paid_edge = next(
        edge
        for edge in pivot_lineage.field_edges
        if edge.target == FieldReference.of(pivot_output, "PAID")
    )
    assert paid_edge.source.field_path == FieldPath.of("amount")
    assert paid_edge.derivation is FieldDerivationKind.AGGREGATED
    assert any(
        dependency.kind is FieldDependencyKind.PIVOT
        and dependency.field.field_path == FieldPath.of("status")
        for dependency in pivot_lineage.dependencies
    )

    wide_schema = Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("q1", FloatType(), nullable=True),
            Field("q2", FloatType(), nullable=True),
        )
    )
    unpivot_builder = TransformationPlan.builder("unpivot")
    wide = unpivot_builder.input("wide", schema=wide_schema)
    unpivoted = unpivot_builder.unpivot(
        "long",
        source=wide,
        id_vars=("customer_id",),
        value_vars=("q1", "q2"),
        variable_name="quarter",
        value_name="revenue",
    )
    unpivot_lineage = lineage.analyze(unpivot_builder.output("out", unpivoted).build())
    revenue_sources = {
        str(edge.source.field_path)
        for edge in unpivot_lineage.field_edges
        if edge.target == FieldReference.of(unpivot_lineage.output("out"), "revenue")
    }
    assert revenue_sources == {"q1", "q2"}

    explode_builder = TransformationPlan.builder("explode")
    customers = explode_builder.input("customers", schema=_customer_schema())
    exploded = explode_builder.explode(
        "tags",
        source=customers,
        field="tags",
    )
    explode_lineage = lineage.analyze(explode_builder.output("out", exploded).build())
    assert any(
        edge.derivation is FieldDerivationKind.EXPLODED
        and edge.source.field_path == FieldPath.of("tags")
        for edge in explode_lineage.field_edges
    )

    flatten_builder = TransformationPlan.builder("flatten")
    customers = flatten_builder.input("customers", schema=_customer_schema())
    flattened = flatten_builder.flatten(
        "profile",
        source=customers,
        field="profile",
    )
    flatten_lineage = lineage.analyze(flatten_builder.output("out", flattened).build())
    assert any(
        edge.derivation is FieldDerivationKind.FLATTENED
        and edge.source.field_path == FieldPath.of("profile.city")
        and edge.target.field_path == FieldPath.of("profile_city")
        for edge in flatten_lineage.field_edges
    )


def test_set_operation_lineage_distinguishes_union_from_membership() -> None:
    builder = TransformationPlan.builder("sets")
    left = builder.input("left", schema=_order_schema())
    right = builder.input("right", schema=_order_schema())
    unioned = builder.union("unioned", left=left, right=right, all=True)
    intersected = builder.intersect("intersected", left=left, right=right)
    excepted = builder.except_("excepted", left=left, right=right)
    plan = (
        builder.output("union", unioned)
        .output("intersection", intersected)
        .output("difference", excepted)
        .build()
    )

    evidence = lineage.analyze(plan)

    union_output = evidence.output("union")
    union_customer_edges = tuple(
        edge
        for edge in evidence.field_edges
        if edge.target == FieldReference.of(union_output, "customer_id")
    )
    assert len(union_customer_edges) == 2
    assert all(
        edge.derivation is FieldDerivationKind.SET_COMBINED
        for edge in union_customer_edges
    )
    assert any(
        dependency.kind is FieldDependencyKind.SET_MEMBERSHIP
        for dependency in evidence.dependencies
    )


def test_resource_reference_linkage_is_explicit_and_non_executing() -> None:
    builder = TransformationPlan.builder("resources")
    source = builder.input("customers", schema=_customer_schema())
    selected = builder.select(
        "selected",
        source=source,
        columns=("customer_id", "email"),
    )
    plan = builder.output("out", selected).build()

    input_resource = ResourceReference(
        scheme="file",
        locator="/data/customers.parquet",
    )
    output_resource = ResourceReference(
        scheme="file",
        locator="/data/customer_ids.parquet",
    )
    evidence = lineage.analyze(
        plan,
        input_resources={"customers": input_resource},
        output_resources={"out": output_resource},
    )

    assert evidence.resources[0].role is ResourceLineageRole.INPUT
    assert evidence.resources[0].resource == input_resource
    assert evidence.resources[1].role is ResourceLineageRole.OUTPUT
    assert evidence.resources[1].resource == output_resource


def test_impact_analysis_traverses_field_and_dataset_lineage() -> None:
    builder = TransformationPlan.builder("impact")
    source = builder.input("customers", schema=_customer_schema())
    renamed = builder.rename(
        "renamed",
        source=source,
        mapping={"email": "contact_email"},
    )
    normalized = builder.derive(
        "normalized",
        source=renamed,
        field_name="normalized_email",
        expression=fn.lower(fn.col("contact_email")),
    )
    plan = builder.output("out", normalized).build()

    evidence = lineage.analyze(plan)
    impact = LineageImpactAnalyzer()

    source_field = FieldReference.of(evidence.input("customers"), "email")
    output_field = FieldReference.of(evidence.output("out"), "normalized_email")

    upstream = impact.upstream_fields(evidence, output_field)
    downstream = impact.downstream_fields(evidence, source_field)
    upstream_datasets = impact.upstream_datasets(
        evidence,
        evidence.output("out"),
    )

    assert source_field in upstream
    assert output_field in downstream
    assert evidence.input("customers") in upstream_datasets
