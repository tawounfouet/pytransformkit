"""Semantics-preserving engine-neutral LogicalPlan optimization."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from pytransformkit.application.planning.expression_optimizer import ExpressionOptimizer
from pytransformkit.application.planning.fingerprint import logical_plan_fingerprint
from pytransformkit.domain.expressions.aggregate import AggregateExpression
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.dependencies import ExpressionDependencyExtractor
from pytransformkit.domain.expressions.fingerprint import expression_fingerprint
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan, LogicalPlanNode
from pytransformkit.domain.quality.rules import ExpressionValidation
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import NodeId
from pytransformkit.domain.transformations.aggregation import (
    AggregateMetric,
    AggregateTransformation,
)
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.derivation import DeriveTransformation
from pytransformkit.domain.transformations.filtering import (
    DistinctTransformation,
    FilterTransformation,
    LimitTransformation,
)
from pytransformkit.domain.transformations.projection import SelectTransformation
from pytransformkit.domain.transformations.properties import (
    Determinism,
    Purity,
)
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    UnionTransformation,
)
from pytransformkit.domain.transformations.reshaping import (
    ExplodeTransformation,
    FlattenTransformation,
    PivotTransformation,
    UnpivotTransformation,
)
from pytransformkit.domain.transformations.schema_resolution import OutputSchemaResolver
from pytransformkit.domain.transformations.sorting import SortTransformation

DEAD_NODE_ELIMINATION_RULE = "dead-node-elimination"
PREDICATE_PUSHDOWN_RULE = "predicate-pushdown"
PROJECTION_PRUNING_RULE = "projection-pruning"


@dataclass(frozen=True, slots=True)
class OptimizationRuleApplication:
    """Provenance for one optimizer rewrite application."""

    rule_id: str
    affected_node_ids: tuple[str, ...]
    summary: str


@dataclass(frozen=True, slots=True)
class OptimizerDiagnostic:
    """Static optimizer analysis or hint."""

    code: str
    summary: str
    rule_id: str | None = None
    node_ids: tuple[str, ...] = ()
    details: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class OptimizationReport:
    """Deterministic optimizer evidence without changing the LogicalPlan type."""

    enabled: bool
    original_fingerprint: Fingerprint
    optimized_fingerprint: Fingerprint
    applications: tuple[OptimizationRuleApplication, ...]
    diagnostics: tuple[OptimizerDiagnostic, ...]
    passes: int


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """LogicalPlan plus optional optimizer evidence."""

    plan: LogicalPlan
    report: OptimizationReport


class LogicalOptimizer:
    """Apply conservative, engine-neutral LogicalPlan rewrites."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_passes: int = 8,
        expression_optimizer: ExpressionOptimizer | None = None,
        schema_resolver: OutputSchemaResolver | None = None,
    ) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a bool.")
        if not isinstance(max_passes, int) or isinstance(max_passes, bool):
            raise TypeError("max_passes must be an integer.")
        if max_passes < 1:
            raise ValueError("max_passes must be >= 1.")
        self._enabled = enabled
        self._max_passes = max_passes
        self._expressions = expression_optimizer or ExpressionOptimizer()
        self._schemas = schema_resolver or OutputSchemaResolver()
        self._dependencies = ExpressionDependencyExtractor()

    def optimize(self, plan: LogicalPlan) -> LogicalPlan:
        """Return an optimized LogicalPlan, or the original plan when disabled."""
        return self.optimize_with_report(plan).plan

    def optimize_with_report(self, plan: LogicalPlan) -> OptimizationResult:
        """Optimize and return deterministic rule provenance and diagnostics."""
        if not isinstance(plan, LogicalPlan):
            raise TypeError("LogicalOptimizer requires a LogicalPlan.")

        original_fingerprint = logical_plan_fingerprint(plan)
        if not self._enabled:
            diagnostic = OptimizerDiagnostic(
                code="PTK-OPT-000",
                summary="Logical optimization is disabled.",
            )
            return OptimizationResult(
                plan=plan,
                report=OptimizationReport(
                    enabled=False,
                    original_fingerprint=original_fingerprint,
                    optimized_fingerprint=original_fingerprint,
                    applications=(),
                    diagnostics=(diagnostic,),
                    passes=0,
                ),
            )

        current = plan
        applications: list[OptimizationRuleApplication] = []

        current, dead_apps = self._eliminate_dead_nodes(current)
        applications.extend(dead_apps)

        pass_count = 0
        for pass_index in range(1, self._max_passes + 1):
            pass_count = pass_index
            changed = False

            current, expression_apps = self._simplify_expressions(current)
            if expression_apps:
                changed = True
                applications.extend(expression_apps)

            current, pushdown_apps = self._push_predicates(current)
            if pushdown_apps:
                changed = True
                applications.extend(pushdown_apps)

            current, pruning_apps = self._prune_projections(current)
            if pruning_apps:
                changed = True
                applications.extend(pruning_apps)

            if not changed:
                break

        diagnostics = (
            self._common_expression_diagnostics(current)
            + self._fusion_hint_diagnostics(current)
            + self._materialization_boundary_diagnostics(current)
        )
        optimized_fingerprint = logical_plan_fingerprint(current)

        return OptimizationResult(
            plan=current,
            report=OptimizationReport(
                enabled=True,
                original_fingerprint=original_fingerprint,
                optimized_fingerprint=optimized_fingerprint,
                applications=tuple(applications),
                diagnostics=diagnostics,
                passes=pass_count,
            ),
        )

    def _eliminate_dead_nodes(
        self,
        plan: LogicalPlan,
    ) -> tuple[LogicalPlan, tuple[OptimizationRuleApplication, ...]]:
        node_by_id = {node.node_id: node for node in plan.nodes}
        output_nodes = tuple(
            node for node in plan.nodes if node.kind is PipelineNodeKind.OUTPUT
        )
        reachable: set[NodeId] = set()
        stack = [node.node_id for node in output_nodes]

        while stack:
            node_id = stack.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            stack.extend(node_by_id[node_id].input_node_ids)

        removed = tuple(node for node in plan.nodes if node.node_id not in reachable)
        if not removed:
            return plan, ()

        kept = tuple(node for node in plan.nodes if node.node_id in reachable)
        rebuilt = self._rebuild(plan, kept)
        application = OptimizationRuleApplication(
            rule_id=DEAD_NODE_ELIMINATION_RULE,
            affected_node_ids=tuple(str(node.node_id) for node in removed),
            summary=f"Removed {len(removed)} node(s) unreachable from plan outputs.",
        )
        return rebuilt, (application,)

    def _simplify_expressions(
        self,
        plan: LogicalPlan,
    ) -> tuple[LogicalPlan, tuple[OptimizationRuleApplication, ...]]:
        rewritten: list[LogicalPlanNode] = []
        rules_by_node: list[tuple[LogicalPlanNode, tuple[str, ...]]] = []

        for node in plan.nodes:
            transformation = node.transformation
            if transformation is None:
                rewritten.append(node)
                continue

            optimized, rules = self._optimize_transformation_expressions(transformation)
            if rules:
                rewritten.append(replace(node, transformation=optimized))
                rules_by_node.append((node, rules))
            else:
                rewritten.append(node)

        if not rules_by_node:
            return plan, ()

        rebuilt = self._rebuild(plan, tuple(rewritten))
        applications = tuple(
            OptimizationRuleApplication(
                rule_id=rule,
                affected_node_ids=(str(node.node_id),),
                summary=f"Applied {rule} within {type(node.transformation).__name__}.",
            )
            for node, rules in rules_by_node
            for rule in rules
        )
        return rebuilt, applications

    def _optimize_transformation_expressions(
        self,
        transformation: TransformationSpec,
    ) -> tuple[TransformationSpec, tuple[str, ...]]:
        if isinstance(transformation, FilterTransformation):
            optimized = self._expressions.optimize(transformation.condition)
            return (
                replace(transformation, condition=optimized.expression),
                optimized.applied_rules,
            )

        if isinstance(transformation, DeriveTransformation):
            optimized = self._expressions.optimize(transformation.expression)
            return (
                replace(transformation, expression=optimized.expression),
                optimized.applied_rules,
            )

        if isinstance(transformation, AggregateTransformation):
            rules: tuple[str, ...] = ()
            group_by: list[Expression] = []
            for expression in transformation.group_by:
                optimized = self._expressions.optimize(expression)
                group_by.append(optimized.expression)
                rules += optimized.applied_rules

            metrics: list[AggregateMetric] = []
            for metric in transformation.metrics:
                optimized = self._expressions.optimize(metric.expression)
                expression = optimized.expression
                if not isinstance(expression, AggregateExpression):
                    expression = metric.expression
                metrics.append(replace(metric, expression=expression))
                rules += optimized.applied_rules

            return (
                replace(
                    transformation,
                    group_by=tuple(group_by),
                    metrics=tuple(metrics),
                ),
                _dedupe(rules),
            )

        if isinstance(transformation, QualityGate):
            rules: tuple[str, ...] = ()
            rewritten_rules = []
            for rule in transformation.spec.rules:
                if isinstance(rule, ExpressionValidation):
                    optimized = self._expressions.optimize(rule.expression)
                    rewritten_rules.append(
                        replace(rule, expression=optimized.expression)
                    )
                    rules += optimized.applied_rules
                else:
                    rewritten_rules.append(rule)

            if not rules:
                return transformation, ()
            spec = replace(
                transformation.spec,
                rules=tuple(rewritten_rules),
            )
            return replace(transformation, spec=spec), _dedupe(rules)

        return transformation, ()

    def _push_predicates(
        self,
        plan: LogicalPlan,
    ) -> tuple[LogicalPlan, tuple[OptimizationRuleApplication, ...]]:
        consumers = _consumers(plan)
        nodes = list(plan.nodes)
        by_id = {node.node_id: index for index, node in enumerate(nodes)}

        for child_index, child in enumerate(nodes):
            if not isinstance(child.transformation, FilterTransformation):
                continue
            if len(child.input_node_ids) != 1:
                continue

            parent_id = child.input_node_ids[0]
            parent_index = by_id.get(parent_id)
            if parent_index is None:
                continue
            parent = nodes[parent_index]
            if parent.kind is not PipelineNodeKind.TRANSFORMATION:
                continue
            if len(consumers[parent.node_id]) != 1:
                continue
            if len(parent.input_node_ids) != 1:
                continue

            parent_transformation = parent.transformation
            if not isinstance(
                parent_transformation,
                (SelectTransformation, SortTransformation),
            ):
                continue

            if isinstance(parent_transformation, SelectTransformation):
                selected = set(parent_transformation.fields)
                dependencies = self._dependencies.extract(
                    child.transformation.condition
                )
                if not dependencies.issubset(selected):
                    continue

            nodes[parent_index] = replace(
                parent,
                transformation=child.transformation,
                step_id=child.step_id,
                name=child.name,
            )
            nodes[child_index] = replace(
                child,
                transformation=parent_transformation,
                step_id=parent.step_id,
                name=parent.name,
            )
            rebuilt = self._rebuild(plan, tuple(nodes))
            application = OptimizationRuleApplication(
                rule_id=PREDICATE_PUSHDOWN_RULE,
                affected_node_ids=(
                    str(parent.node_id),
                    str(child.node_id),
                ),
                summary=(
                    "Moved a filter before a semantics-preserving "
                    f"{type(parent_transformation).__name__}."
                ),
            )
            return rebuilt, (application,)

        return plan, ()

    def _prune_projections(
        self,
        plan: LogicalPlan,
    ) -> tuple[LogicalPlan, tuple[OptimizationRuleApplication, ...]]:
        consumers = _consumers(plan)
        nodes = list(plan.nodes)
        by_id = {node.node_id: index for index, node in enumerate(nodes)}

        for child in nodes:
            child_transformation = child.transformation
            if not isinstance(child_transformation, SelectTransformation):
                continue
            if len(child.input_node_ids) != 1:
                continue

            parent_index = by_id.get(child.input_node_ids[0])
            if parent_index is None:
                continue
            parent = nodes[parent_index]
            parent_transformation = parent.transformation
            if not isinstance(parent_transformation, SelectTransformation):
                continue
            if len(consumers[parent.node_id]) != 1:
                continue

            parent_fields = set(parent_transformation.fields)
            if not set(child_transformation.fields).issubset(parent_fields):
                continue
            if parent_transformation.fields == child_transformation.fields:
                continue

            nodes[parent_index] = replace(
                parent,
                transformation=SelectTransformation(child_transformation.fields),
            )
            rebuilt = self._rebuild(plan, tuple(nodes))
            application = OptimizationRuleApplication(
                rule_id=PROJECTION_PRUNING_RULE,
                affected_node_ids=(str(parent.node_id),),
                summary=(
                    "Narrowed an upstream projection to the fields required "
                    "by its downstream projection."
                ),
            )
            return rebuilt, (application,)

        return plan, ()

    def _rebuild(
        self,
        original: LogicalPlan,
        nodes: tuple[LogicalPlanNode, ...],
    ) -> LogicalPlan:
        output_schema_by_node = {}
        dataset_id_by_node = {}
        rebuilt: list[LogicalPlanNode] = []

        for node in nodes:
            predecessor_schemas = tuple(
                output_schema_by_node[node_id] for node_id in node.input_node_ids
            )

            if node.kind is PipelineNodeKind.INPUT:
                planned = replace(
                    node,
                    input_schema=None,
                    input_node_ids=(),
                    input_schemas=(),
                )
            elif node.kind is PipelineNodeKind.TRANSFORMATION:
                transformation = node.transformation
                if transformation is None:
                    raise ValueError(
                        "Transformation node is missing its transformation."
                    )
                output_schema = self._schemas.resolve_many(
                    transformation,
                    predecessor_schemas,
                )
                planned = replace(
                    node,
                    input_schema=(
                        predecessor_schemas[0]
                        if len(predecessor_schemas) == 1
                        else None
                    ),
                    input_schemas=predecessor_schemas,
                    output_schema=output_schema,
                )
            elif node.kind is PipelineNodeKind.OUTPUT:
                if len(predecessor_schemas) != 1:
                    raise ValueError("Output node requires exactly one predecessor.")
                predecessor_id = node.input_node_ids[0]
                planned = replace(
                    node,
                    input_schema=predecessor_schemas[0],
                    input_schemas=predecessor_schemas,
                    output_schema=predecessor_schemas[0],
                    dataset_id=dataset_id_by_node[predecessor_id],
                )
            else:
                raise ValueError(f"Unknown logical node kind {node.kind!r}.")

            output_schema_by_node[planned.node_id] = planned.output_schema
            dataset_id_by_node[planned.node_id] = planned.dataset_id
            rebuilt.append(planned)

        outputs = tuple(
            (node.name, node.output_schema)
            for node in rebuilt
            if node.kind is PipelineNodeKind.OUTPUT and node.name is not None
        )
        if not outputs:
            raise ValueError("Optimized LogicalPlan requires at least one output.")

        return LogicalPlan(
            pipeline_id=original.pipeline_id,
            pipeline_name=original.pipeline_name,
            nodes=tuple(rebuilt),
            output_schema=outputs[0][1],
            output_schemas=outputs,
        )

    def _common_expression_diagnostics(
        self,
        plan: LogicalPlan,
    ) -> tuple[OptimizerDiagnostic, ...]:
        occurrences: defaultdict[str, list[str]] = defaultdict(list)
        for node in plan.nodes:
            for expression in _expressions_for_node(node):
                occurrences[expression_fingerprint(expression).value].append(
                    str(node.node_id)
                )

        diagnostics = []
        for fingerprint, node_ids in sorted(occurrences.items()):
            if len(node_ids) < 2:
                continue
            diagnostics.append(
                OptimizerDiagnostic(
                    code="PTK-OPT-ANALYSIS-001",
                    summary="Equivalent logical expression occurs more than once.",
                    rule_id="common-expression-analysis",
                    node_ids=tuple(node_ids),
                    details=(
                        ("expression_fingerprint", fingerprint),
                        ("occurrence_count", str(len(node_ids))),
                    ),
                )
            )
        return tuple(diagnostics)

    def _fusion_hint_diagnostics(
        self,
        plan: LogicalPlan,
    ) -> tuple[OptimizerDiagnostic, ...]:
        node_by_id = {node.node_id: node for node in plan.nodes}
        consumers = _consumers(plan)
        diagnostics = []

        for node in plan.nodes:
            if node.kind is not PipelineNodeKind.TRANSFORMATION:
                continue
            if len(node.input_node_ids) != 1:
                continue
            parent = node_by_id[node.input_node_ids[0]]
            if parent.kind is not PipelineNodeKind.TRANSFORMATION:
                continue
            if len(consumers[parent.node_id]) != 1:
                continue
            if _is_materialization_boundary(
                parent
            ) or _is_materialization_boundary(node):
                continue
            if not _pure_deterministic(parent) or not _pure_deterministic(node):
                continue

            diagnostics.append(
                OptimizerDiagnostic(
                    code="PTK-OPT-HINT-001",
                    summary=(
                        "Adjacent pure deterministic transformations are fusion-safe."
                    ),
                    rule_id="safe-fusion-hints",
                    node_ids=(str(parent.node_id), str(node.node_id)),
                )
            )
        return tuple(diagnostics)

    def _materialization_boundary_diagnostics(
        self,
        plan: LogicalPlan,
    ) -> tuple[OptimizerDiagnostic, ...]:
        diagnostics = []
        for node in plan.nodes:
            if not _is_materialization_boundary(node):
                continue
            reason = _boundary_reason(node)
            diagnostics.append(
                OptimizerDiagnostic(
                    code="PTK-OPT-BOUNDARY-001",
                    summary="Optimizer will not reorder across this logical boundary.",
                    rule_id="materialization-boundary-analysis",
                    node_ids=(str(node.node_id),),
                    details=(("reason", reason),),
                )
            )
        return tuple(diagnostics)


def _consumers(plan: LogicalPlan) -> dict[NodeId, tuple[NodeId, ...]]:
    values: defaultdict[NodeId, list[NodeId]] = defaultdict(list)
    for node in plan.nodes:
        for input_node_id in node.input_node_ids:
            values[input_node_id].append(node.node_id)
    return {node.node_id: tuple(values[node.node_id]) for node in plan.nodes}


def _expressions_for_node(node: LogicalPlanNode) -> tuple[Expression, ...]:
    transformation = node.transformation
    if isinstance(transformation, FilterTransformation):
        return (transformation.condition,)
    if isinstance(transformation, DeriveTransformation):
        return (transformation.expression,)
    if isinstance(transformation, AggregateTransformation):
        return transformation.group_by + tuple(
            metric.expression for metric in transformation.metrics
        )
    if isinstance(transformation, QualityGate):
        return tuple(
            rule.expression
            for rule in transformation.spec.rules
            if isinstance(rule, ExpressionValidation)
        )
    return ()


def _pure_deterministic(node: LogicalPlanNode) -> bool:
    transformation = node.transformation
    if transformation is None:
        return False
    return (
        transformation.properties.purity is Purity.PURE
        and transformation.properties.determinism is Determinism.DETERMINISTIC
    )


def _is_materialization_boundary(node: LogicalPlanNode) -> bool:
    transformation = node.transformation
    if transformation is None:
        return False
    return (
        len(node.input_node_ids) > 1
        or isinstance(
            transformation,
            (
                AggregateTransformation,
                DistinctTransformation,
                LimitTransformation,
                QualityGate,
                JoinTransformation,
                UnionTransformation,
                IntersectTransformation,
                ExceptTransformation,
                PivotTransformation,
                UnpivotTransformation,
                ExplodeTransformation,
                FlattenTransformation,
            ),
        )
    )


def _boundary_reason(node: LogicalPlanNode) -> str:
    if len(node.input_node_ids) > 1:
        return "multi_input"
    transformation = node.transformation
    if isinstance(transformation, QualityGate):
        return "quality_evaluation"
    if isinstance(transformation, AggregateTransformation):
        return "aggregation"
    if isinstance(transformation, LimitTransformation):
        return "cardinality_limit"
    if isinstance(transformation, DistinctTransformation):
        return "distinct_rows"
    if isinstance(
        transformation,
        (
            JoinTransformation,
            UnionTransformation,
            IntersectTransformation,
            ExceptTransformation,
        ),
    ):
        return "relational_boundary"
    return "reshape_boundary"


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
