from __future__ import annotations

from dataclasses import replace

from pytransformkit import TransformationPlan
from pytransformkit.application.planning.optimizer import (
    DEAD_NODE_ELIMINATION_RULE,
    PREDICATE_PUSHDOWN_RULE,
    PROJECTION_PRUNING_RULE,
    LogicalOptimizer,
)
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.lineage import (
    FieldReference,
    LineageAnalyzer,
    LineageImpactAnalyzer,
)
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlanNode
from pytransformkit.domain.shared.identifiers import DatasetId, NodeId
from pytransformkit.domain.transformations.filtering import FilterTransformation
from pytransformkit.domain.transformations.projection import SelectTransformation
from pytransformkit.functions import col, lit
from pytransformkit.planning import TransformationCompiler


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("amount", IntegerType(), nullable=False),
        )
    )


def _optimizable_plan():
    builder = TransformationPlan.builder("optimized_customers")
    source = builder.input("customers", schema=_schema())
    wide = builder.select(
        "wide_projection",
        source=source,
        columns=("customer_id", "status", "amount"),
    )
    narrow = builder.select(
        "narrow_projection",
        source=wide,
        columns=("customer_id", "amount"),
    )
    filtered = builder.filter(
        "positive_amounts",
        source=narrow,
        where=(col("amount") > (lit(1) + lit(1))) & lit(True),
    )
    return TransformationCompiler().compile(
        builder.output("result", filtered).build()
    )


def test_optimizer_can_be_disabled_without_changing_plan_identity() -> None:
    logical = _optimizable_plan()

    result = LogicalOptimizer(enabled=False).optimize_with_report(logical)

    assert result.plan is logical
    assert result.report.enabled is False
    assert result.report.original_fingerprint == logical.fingerprint()
    assert result.report.optimized_fingerprint == logical.fingerprint()
    assert result.report.applications == ()


def test_optimizer_pushes_predicate_and_prunes_upstream_projection() -> None:
    result = LogicalOptimizer().optimize_with_report(_optimizable_plan())

    rules = tuple(item.rule_id for item in result.report.applications)
    assert PREDICATE_PUSHDOWN_RULE in rules
    assert PROJECTION_PRUNING_RULE in rules
    assert "constant-folding" in rules
    assert "boolean-simplification" in rules

    transformations = [
        node.transformation
        for node in result.plan.nodes
        if node.kind is PipelineNodeKind.TRANSFORMATION
    ]
    assert isinstance(transformations[0], FilterTransformation)
    assert isinstance(transformations[1], SelectTransformation)
    assert transformations[1].fields == transformations[2].fields
    assert result.plan.output_schema == _optimizable_plan().output_schema


def test_dead_node_elimination_removes_unreachable_logical_input() -> None:
    logical = _optimizable_plan()
    dead = LogicalPlanNode(
        node_id=NodeId.new(),
        kind=PipelineNodeKind.INPUT,
        input_schema=None,
        output_schema=_schema(),
        dataset_id=DatasetId.new(),
        name="unused",
    )
    with_dead_node = replace(logical, nodes=logical.nodes + (dead,))

    result = LogicalOptimizer().optimize_with_report(with_dead_node)

    assert "unused" not in result.plan.input_names
    assert result.plan.output_schema == logical.output_schema
    assert DEAD_NODE_ELIMINATION_RULE in {
        application.rule_id for application in result.report.applications
    }


def test_optimizer_preserves_transitive_field_lineage() -> None:
    original = _optimizable_plan()
    optimized = LogicalOptimizer().optimize(original)

    original_lineage = LineageAnalyzer().analyze(original)
    optimized_lineage = LineageAnalyzer().analyze(optimized)
    impact = LineageImpactAnalyzer()

    for field_name in optimized.output_schema.names():
        original_target = FieldReference.of(
            original_lineage.output("result"),
            field_name,
        )
        optimized_target = FieldReference.of(
            optimized_lineage.output("result"),
            field_name,
        )
        original_sources = {
            str(reference.field_path)
            for reference in impact.upstream_fields(
                original_lineage,
                original_target,
            )
            if reference.dataset == original_lineage.input("customers")
        }
        optimized_sources = {
            str(reference.field_path)
            for reference in impact.upstream_fields(
                optimized_lineage,
                optimized_target,
            )
            if reference.dataset == optimized_lineage.input("customers")
        }
        assert optimized_sources == original_sources


def test_common_expression_and_fusion_analysis_emit_diagnostics() -> None:
    builder = TransformationPlan.builder("duplicate_expression")
    source = builder.input("customers", schema=_schema())
    first = builder.filter(
        "first_filter",
        source=source,
        where=col("amount") > 10,
    )
    second = builder.filter(
        "second_filter",
        source=first,
        where=col("amount") > 10,
    )
    logical = TransformationCompiler().compile(
        builder.output("result", second).build()
    )

    result = LogicalOptimizer().optimize_with_report(logical)
    codes = {diagnostic.code for diagnostic in result.report.diagnostics}

    assert "PTK-OPT-ANALYSIS-001" in codes
    assert "PTK-OPT-HINT-001" in codes
