"""Public logical-lineage API."""

from collections.abc import Mapping

from pytransformkit.application.planning import TransformationCompiler
from pytransformkit.domain.lineage import (
    DatasetLineageEdge,
    FieldDependency,
    FieldDependencyKind,
    FieldDerivationKind,
    FieldLineageEdge,
    FieldReference,
    LineageAnalyzer,
    LineageConfidence,
    LineageImpactAnalyzer,
    ResourceLineageLink,
    ResourceLineageRole,
    TransformationLineage,
)
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.plans import TransformationPlan
from pytransformkit.domain.resources import ResourceReference


def analyze(
    plan: TransformationPlan | LogicalPlan,
    *,
    input_resources: Mapping[str, ResourceReference] | None = None,
    output_resources: Mapping[str, ResourceReference] | None = None,
) -> TransformationLineage:
    """Compile when needed and derive logical lineage without executing data."""
    logical_plan = (
        TransformationCompiler().compile(plan)
        if isinstance(plan, TransformationPlan)
        else plan
    )
    if not isinstance(logical_plan, LogicalPlan):
        raise TypeError("lineage.analyze requires TransformationPlan or LogicalPlan.")
    return LineageAnalyzer().analyze(
        logical_plan,
        input_resources=input_resources,
        output_resources=output_resources,
    )


__all__ = [
    "DatasetLineageEdge",
    "FieldDependency",
    "FieldDependencyKind",
    "FieldDerivationKind",
    "FieldLineageEdge",
    "FieldReference",
    "LineageAnalyzer",
    "LineageConfidence",
    "LineageImpactAnalyzer",
    "ResourceLineageLink",
    "ResourceLineageRole",
    "TransformationLineage",
    "analyze",
]
