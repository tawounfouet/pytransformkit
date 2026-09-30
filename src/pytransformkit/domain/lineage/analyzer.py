"""Static logical-lineage derivation for built-in transformations."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from typing import TypeVar

from pytransformkit.domain.data.data_types import StructType
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.references import DatasetReference
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.dependencies import (
    ExpressionDependencyExtractor,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.window import WindowExpression
from pytransformkit.domain.lineage.model import (
    DatasetLineageEdge,
    FieldDependency,
    FieldDependencyKind,
    FieldDerivationKind,
    FieldLineageEdge,
    FieldReference,
    LineageConfidence,
    ResourceLineageLink,
    ResourceLineageRole,
    TransformationLineage,
)
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan, LogicalPlanNode
from pytransformkit.domain.quality.rules import (
    AllowedValues,
    ExpressionValidation,
    NotNull,
    Range,
    Regex,
    RowCount,
    SchemaValidation,
    Unique,
    ValidationRule,
)
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.shared.identifiers import StepId
from pytransformkit.domain.transformations.aggregation import (
    AggregateTransformation,
    group_output_name,
)
from pytransformkit.domain.transformations.casting import CastTransformation
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
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
    UnionTransformation,
)
from pytransformkit.domain.transformations.reshaping import (
    ExplodeTransformation,
    FlattenTransformation,
    PivotTransformation,
    UnpivotTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.lineage import UnsupportedLineageError


class LineageAnalyzer:
    """Derive PyTransformKit logical lineage without executing physical data."""

    def __init__(
        self,
        dependency_extractor: ExpressionDependencyExtractor | None = None,
    ) -> None:
        self._dependency_extractor = (
            dependency_extractor or ExpressionDependencyExtractor()
        )

    def analyze(
        self,
        plan: LogicalPlan,
        *,
        input_resources: Mapping[str, ResourceReference] | None = None,
        output_resources: Mapping[str, ResourceReference] | None = None,
    ) -> TransformationLineage:
        if not isinstance(plan, LogicalPlan):
            raise TypeError("LineageAnalyzer requires a LogicalPlan.")

        node_by_id = {node.node_id: node for node in plan.nodes}
        references = {
            node.node_id: DatasetReference(node.dataset_id) for node in plan.nodes
        }

        inputs = tuple(
            (node.name, references[node.node_id])
            for node in plan.nodes
            if node.kind is PipelineNodeKind.INPUT and node.name is not None
        )
        outputs = tuple(
            (node.name, references[node.node_id])
            for node in plan.nodes
            if node.kind is PipelineNodeKind.OUTPUT and node.name is not None
        )

        dataset_edges: list[DatasetLineageEdge] = []
        field_edges: list[FieldLineageEdge] = []
        dependencies: list[FieldDependency] = []

        for node in plan.nodes:
            if node.kind is not PipelineNodeKind.TRANSFORMATION:
                continue
            if node.transformation is None or node.step_id is None:
                raise UnsupportedLineageError(
                    "Transformation node is missing transformation lineage metadata."
                )

            source_nodes = tuple(node_by_id[node_id] for node_id in node.input_node_ids)
            source_refs = tuple(references[source.node_id] for source in source_nodes)
            target_ref = references[node.node_id]

            dataset_edges.extend(
                DatasetLineageEdge(
                    source=source_ref,
                    target=target_ref,
                    operation=node.transformation.identifier,
                    step_id=node.step_id,
                    confidence=LineageConfidence.EXACT,
                )
                for source_ref in source_refs
            )

            resolved_edges, resolved_dependencies = self._resolve_transformation(
                node,
                source_nodes,
                source_refs,
                target_ref,
            )
            field_edges.extend(resolved_edges)
            dependencies.extend(resolved_dependencies)

        resource_links = self._resource_links(
            inputs=inputs,
            outputs=outputs,
            input_resources=input_resources or {},
            output_resources=output_resources or {},
        )

        return TransformationLineage(
            plan_id=plan.plan_id,
            inputs=inputs,
            outputs=outputs,
            dataset_edges=_dedupe(dataset_edges),
            field_edges=_dedupe(field_edges),
            dependencies=_dedupe(dependencies),
            resources=resource_links,
        )

    def _resolve_transformation(
        self,
        node: LogicalPlanNode,
        source_nodes: tuple[LogicalPlanNode, ...],
        source_refs: tuple[DatasetReference, ...],
        target_ref: DatasetReference,
    ) -> tuple[tuple[FieldLineageEdge, ...], tuple[FieldDependency, ...]]:
        transformation = node.transformation
        step_id = node.step_id
        assert transformation is not None
        assert step_id is not None

        if isinstance(transformation, SelectTransformation):
            source_ref = _single(source_refs)
            edges = tuple(
                _field_edge(
                    source_ref,
                    field,
                    target_ref,
                    field,
                    FieldDerivationKind.DIRECT,
                    step_id,
                )
                for field in transformation.fields
            )
            return edges, ()

        if isinstance(transformation, DropTransformation):
            return (
                _direct_edges(
                    _single(source_refs),
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                (),
            )

        if isinstance(transformation, RenameTransformation):
            source_ref = _single(source_refs)
            source_by_target = {
                item.target: item.source for item in transformation.renames
            }
            edges = tuple(
                _field_edge(
                    source_ref,
                    source_by_target.get(field.name, FieldPath.of(field.name)),
                    target_ref,
                    FieldPath.of(field.name),
                    (
                        FieldDerivationKind.RENAMED
                        if field.name in source_by_target
                        else FieldDerivationKind.DIRECT
                    ),
                    step_id,
                )
                for field in node.output_schema.fields
            )
            return edges, ()

        if isinstance(transformation, CastTransformation):
            source_ref = _single(source_refs)
            edges = tuple(
                _field_edge(
                    source_ref,
                    FieldPath.of(field.name),
                    target_ref,
                    FieldPath.of(field.name),
                    (
                        FieldDerivationKind.CAST
                        if field.name == str(transformation.field)
                        else FieldDerivationKind.DIRECT
                    ),
                    step_id,
                )
                for field in node.output_schema.fields
            )
            return edges, ()

        if isinstance(transformation, DeriveTransformation):
            source_ref = _single(source_refs)
            edges = [
                _field_edge(
                    source_ref,
                    FieldPath.of(field.name),
                    target_ref,
                    FieldPath.of(field.name),
                    FieldDerivationKind.DIRECT,
                    step_id,
                )
                for field in node.output_schema.fields
                if field.name != transformation.field_name
            ]
            derivation = (
                FieldDerivationKind.WINDOWED
                if isinstance(transformation.expression, WindowExpression)
                else FieldDerivationKind.DERIVED
            )
            edges.extend(
                _field_edge(
                    source_ref,
                    source_path,
                    target_ref,
                    FieldPath.of(transformation.field_name),
                    derivation,
                    step_id,
                )
                for source_path in sorted(
                    self._dependency_extractor.extract(
                        transformation.expression,
                    ),
                    key=str,
                )
            )
            dependencies = self._expression_dependencies(
                transformation.expression,
                source_ref,
                target_ref,
                step_id,
            )
            return tuple(edges), dependencies

        if isinstance(transformation, FilterTransformation):
            source_ref = _single(source_refs)
            return (
                _direct_edges(
                    source_ref,
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                self._path_dependencies(
                    self._dependency_extractor.extract(
                        transformation.condition,
                    ),
                    source_ref,
                    target_ref,
                    FieldDependencyKind.FILTER,
                    step_id,
                ),
            )

        if isinstance(transformation, LimitTransformation):
            return (
                _direct_edges(
                    _single(source_refs),
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                (),
            )

        if isinstance(transformation, DistinctTransformation):
            source_ref = _single(source_refs)
            paths = tuple(FieldPath.of(name) for name in node.output_schema.names())
            return (
                _direct_edges(
                    source_ref,
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                self._path_dependencies(
                    paths,
                    source_ref,
                    target_ref,
                    FieldDependencyKind.DISTINCT,
                    step_id,
                ),
            )

        if isinstance(transformation, SortTransformation):
            source_ref = _single(source_refs)
            return (
                _direct_edges(
                    source_ref,
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                self._path_dependencies(
                    tuple(key.field for key in transformation.keys),
                    source_ref,
                    target_ref,
                    FieldDependencyKind.ORDERING,
                    step_id,
                ),
            )

        if isinstance(transformation, DeduplicateTransformation):
            source_ref = _single(source_refs)
            return (
                _direct_edges(
                    source_ref,
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                self._path_dependencies(
                    transformation.keys,
                    source_ref,
                    target_ref,
                    FieldDependencyKind.DEDUPLICATION,
                    step_id,
                ),
            )

        if isinstance(transformation, AggregateTransformation):
            source_ref = _single(source_refs)
            edges: list[FieldLineageEdge] = []
            dependencies: list[FieldDependency] = []

            for index, expression in enumerate(transformation.group_by):
                output_name = group_output_name(expression, index)
                paths = self._dependency_extractor.extract(expression)
                derivation = (
                    FieldDerivationKind.DIRECT
                    if isinstance(expression, ColumnReference)
                    else FieldDerivationKind.DERIVED
                )
                edges.extend(
                    _field_edge(
                        source_ref,
                        path,
                        target_ref,
                        FieldPath.of(output_name),
                        derivation,
                        step_id,
                    )
                    for path in sorted(paths, key=str)
                )
                dependencies.extend(
                    self._path_dependencies(
                        paths,
                        source_ref,
                        target_ref,
                        FieldDependencyKind.GROUPING,
                        step_id,
                    )
                )

            for metric in transformation.metrics:
                paths = self._dependency_extractor.extract(metric.expression)
                edges.extend(
                    _field_edge(
                        source_ref,
                        path,
                        target_ref,
                        FieldPath.of(metric.name),
                        FieldDerivationKind.AGGREGATED,
                        step_id,
                    )
                    for path in sorted(paths, key=str)
                )

            return tuple(edges), _dedupe(dependencies)

        if isinstance(transformation, JoinTransformation):
            return self._join_lineage(
                transformation,
                node,
                source_nodes,
                source_refs,
                target_ref,
            )

        if isinstance(transformation, UnionTransformation):
            left_ref, right_ref = _binary(source_refs)
            edges: list[FieldLineageEdge] = []
            for field in node.output_schema.fields:
                path = FieldPath.of(field.name)
                edges.append(
                    _field_edge(
                        left_ref,
                        path,
                        target_ref,
                        path,
                        FieldDerivationKind.SET_COMBINED,
                        step_id,
                    )
                )
                edges.append(
                    _field_edge(
                        right_ref,
                        path,
                        target_ref,
                        path,
                        FieldDerivationKind.SET_COMBINED,
                        step_id,
                    )
                )
            return tuple(edges), ()

        if isinstance(transformation, (IntersectTransformation, ExceptTransformation)):
            left_ref, right_ref = _binary(source_refs)
            edges = _direct_edges(
                left_ref,
                target_ref,
                node.output_schema.names(),
                step_id,
            )
            dependencies: list[FieldDependency] = []
            for source_ref, source_node in zip(
                (left_ref, right_ref),
                source_nodes,
                strict=True,
            ):
                dependencies.extend(
                    self._path_dependencies(
                        tuple(
                            FieldPath.of(name)
                            for name in source_node.output_schema.names()
                        ),
                        source_ref,
                        target_ref,
                        FieldDependencyKind.SET_MEMBERSHIP,
                        step_id,
                    )
                )
            return edges, _dedupe(dependencies)

        if isinstance(transformation, PivotTransformation):
            source_ref = _single(source_refs)
            edges: list[FieldLineageEdge] = []
            dependencies: list[FieldDependency] = []
            for path in transformation.index:
                edges.append(
                    _field_edge(
                        source_ref,
                        path,
                        target_ref,
                        FieldPath.of(path.name),
                        FieldDerivationKind.DIRECT,
                        step_id,
                    )
                )
            dependencies.extend(
                self._path_dependencies(
                    transformation.index,
                    source_ref,
                    target_ref,
                    FieldDependencyKind.GROUPING,
                    step_id,
                )
            )
            dependencies.extend(
                self._path_dependencies(
                    (transformation.columns,),
                    source_ref,
                    target_ref,
                    FieldDependencyKind.PIVOT,
                    step_id,
                )
            )
            edges.extend(
                _field_edge(
                    source_ref,
                    transformation.values,
                    target_ref,
                    FieldPath.of(category),
                    FieldDerivationKind.AGGREGATED,
                    step_id,
                )
                for category in transformation.categories
            )
            return tuple(edges), _dedupe(dependencies)

        if isinstance(transformation, UnpivotTransformation):
            source_ref = _single(source_refs)
            edges: list[FieldLineageEdge] = [
                _field_edge(
                    source_ref,
                    path,
                    target_ref,
                    FieldPath.of(path.name),
                    FieldDerivationKind.DIRECT,
                    step_id,
                )
                for path in transformation.id_vars
            ]
            for source_path in transformation.value_vars:
                edges.append(
                    _field_edge(
                        source_ref,
                        source_path,
                        target_ref,
                        FieldPath.of(transformation.variable_name),
                        FieldDerivationKind.RESHAPED,
                        step_id,
                    )
                )
                edges.append(
                    _field_edge(
                        source_ref,
                        source_path,
                        target_ref,
                        FieldPath.of(transformation.value_name),
                        FieldDerivationKind.RESHAPED,
                        step_id,
                    )
                )
            return tuple(edges), ()

        if isinstance(transformation, ExplodeTransformation):
            source_ref = _single(source_refs)
            edges = tuple(
                _field_edge(
                    source_ref,
                    FieldPath.of(field.name),
                    target_ref,
                    FieldPath.of(field.name),
                    (
                        FieldDerivationKind.EXPLODED
                        if field.name == transformation.field.name
                        else FieldDerivationKind.DIRECT
                    ),
                    step_id,
                )
                for field in node.output_schema.fields
            )
            return edges, ()

        if isinstance(transformation, FlattenTransformation):
            source_ref = _single(source_refs)
            source_schema = source_nodes[0].output_schema
            root = source_schema.field(transformation.field.name)
            if not isinstance(root.data_type, StructType):
                raise UnsupportedLineageError(
                    "Flatten lineage requires a statically known StructType."
                )
            edges: list[FieldLineageEdge] = []
            for field in source_schema.fields:
                if field.name != transformation.field.name:
                    edges.append(
                        _field_edge(
                            source_ref,
                            FieldPath.of(field.name),
                            target_ref,
                            FieldPath.of(field.name),
                            FieldDerivationKind.DIRECT,
                            step_id,
                        )
                    )
            for nested in root.data_type.fields:
                edges.append(
                    _field_edge(
                        source_ref,
                        FieldPath(
                            (
                                transformation.field.name,
                                nested.name,
                            )
                        ),
                        target_ref,
                        FieldPath.of(transformation.output_name(nested.name)),
                        FieldDerivationKind.FLATTENED,
                        step_id,
                    )
                )
            return tuple(edges), ()

        if isinstance(transformation, QualityGate):
            source_ref = _single(source_refs)
            dependencies: list[FieldDependency] = []
            for rule in transformation.spec.rules:
                dependencies.extend(
                    self._quality_dependencies(
                        rule,
                        source_ref,
                        target_ref,
                        step_id,
                    )
                )
            return (
                _direct_edges(
                    source_ref,
                    target_ref,
                    node.output_schema.names(),
                    step_id,
                ),
                _dedupe(dependencies),
            )

        raise UnsupportedLineageError(
            f"No logical lineage resolver exists for {type(transformation).__name__!r}."
        )

    def _join_lineage(
        self,
        transformation: JoinTransformation,
        node: LogicalPlanNode,
        source_nodes: tuple[LogicalPlanNode, ...],
        source_refs: tuple[DatasetReference, ...],
        target_ref: DatasetReference,
    ) -> tuple[tuple[FieldLineageEdge, ...], tuple[FieldDependency, ...]]:
        step_id = node.step_id
        assert step_id is not None
        left_ref, right_ref = _binary(source_refs)
        left_schema, right_schema = (
            source_nodes[0].output_schema,
            source_nodes[1].output_schema,
        )

        edges: list[FieldLineageEdge] = [
            _field_edge(
                left_ref,
                FieldPath.of(field.name),
                target_ref,
                FieldPath.of(field.name),
                FieldDerivationKind.DIRECT,
                step_id,
            )
            for field in left_schema.fields
        ]

        if transformation.how not in {JoinType.SEMI, JoinType.ANTI}:
            right_join_keys = {str(key.right) for key in transformation.keys}
            used_names = set(left_schema.names())
            for field in right_schema.fields:
                if field.name in right_join_keys:
                    continue
                output_name = field.name
                if output_name in used_names:
                    output_name = f"{output_name}{transformation.right_suffix}"
                used_names.add(output_name)
                edges.append(
                    _field_edge(
                        right_ref,
                        FieldPath.of(field.name),
                        target_ref,
                        FieldPath.of(output_name),
                        FieldDerivationKind.DIRECT,
                        step_id,
                    )
                )

        dependencies: list[FieldDependency] = []
        for key in transformation.keys:
            dependencies.append(
                _dependency(
                    left_ref,
                    key.left,
                    target_ref,
                    FieldDependencyKind.JOIN,
                    step_id,
                )
            )
            dependencies.append(
                _dependency(
                    right_ref,
                    key.right,
                    target_ref,
                    FieldDependencyKind.JOIN,
                    step_id,
                )
            )

        return tuple(edges), tuple(dependencies)

    def _expression_dependencies(
        self,
        expression: Expression,
        source_ref: DatasetReference,
        target_ref: DatasetReference,
        step_id: StepId,
    ) -> tuple[FieldDependency, ...]:
        if not isinstance(expression, WindowExpression):
            return ()

        dependencies: list[FieldDependency] = []
        if expression.argument is not None:
            dependencies.extend(
                self._path_dependencies(
                    self._dependency_extractor.extract(expression.argument),
                    source_ref,
                    target_ref,
                    FieldDependencyKind.WINDOW,
                    step_id,
                )
            )
        if expression.default is not None:
            dependencies.extend(
                self._path_dependencies(
                    self._dependency_extractor.extract(expression.default),
                    source_ref,
                    target_ref,
                    FieldDependencyKind.WINDOW,
                    step_id,
                )
            )
        dependencies.extend(
            self._path_dependencies(
                expression.spec.partition_keys,
                source_ref,
                target_ref,
                FieldDependencyKind.WINDOW_PARTITION,
                step_id,
            )
        )
        dependencies.extend(
            self._path_dependencies(
                tuple(key.field for key in expression.spec.order_keys),
                source_ref,
                target_ref,
                FieldDependencyKind.WINDOW_ORDERING,
                step_id,
            )
        )
        return _dedupe(dependencies)

    def _quality_dependencies(
        self,
        rule: ValidationRule,
        source_ref: DatasetReference,
        target_ref: DatasetReference,
        step_id: StepId,
    ) -> tuple[FieldDependency, ...]:
        if isinstance(rule, (NotNull, Range, AllowedValues, Regex)):
            paths = (rule.field,)
        elif isinstance(rule, Unique):
            paths = rule.fields
        elif isinstance(rule, ExpressionValidation):
            paths = tuple(self._dependency_extractor.extract(rule.expression))
        elif isinstance(rule, (SchemaValidation, RowCount)):
            paths = ()
        else:
            raise UnsupportedLineageError(
                f"Unsupported quality lineage rule {type(rule).__name__!r}."
            )

        return self._path_dependencies(
            paths,
            source_ref,
            target_ref,
            FieldDependencyKind.QUALITY,
            step_id,
        )

    @staticmethod
    def _path_dependencies(
        paths: Iterable[FieldPath],
        source_ref: DatasetReference,
        target_ref: DatasetReference,
        kind: FieldDependencyKind,
        step_id: StepId,
    ) -> tuple[FieldDependency, ...]:
        return tuple(
            _dependency(
                source_ref,
                path,
                target_ref,
                kind,
                step_id,
            )
            for path in sorted(tuple(paths), key=str)
        )

    @staticmethod
    def _resource_links(
        *,
        inputs: tuple[tuple[str, DatasetReference], ...],
        outputs: tuple[tuple[str, DatasetReference], ...],
        input_resources: Mapping[str, ResourceReference],
        output_resources: Mapping[str, ResourceReference],
    ) -> tuple[ResourceLineageLink, ...]:
        input_by_name = dict(inputs)
        output_by_name = dict(outputs)

        unknown_inputs = set(input_resources) - set(input_by_name)
        unknown_outputs = set(output_resources) - set(output_by_name)
        if unknown_inputs or unknown_outputs:
            raise KeyError(
                "Resource lineage names do not match LogicalPlan bindings: "
                f"unknown_inputs={sorted(unknown_inputs)!r}, "
                f"unknown_outputs={sorted(unknown_outputs)!r}."
            )

        links: list[ResourceLineageLink] = []
        for name, dataset in inputs:
            resource = input_resources.get(name)
            if resource is not None:
                links.append(
                    ResourceLineageLink(
                        name=name,
                        dataset=dataset,
                        resource=resource,
                        role=ResourceLineageRole.INPUT,
                    )
                )
        for name, dataset in outputs:
            resource = output_resources.get(name)
            if resource is not None:
                links.append(
                    ResourceLineageLink(
                        name=name,
                        dataset=dataset,
                        resource=resource,
                        role=ResourceLineageRole.OUTPUT,
                    )
                )
        return tuple(links)


def _field_edge(
    source_dataset: DatasetReference,
    source_path: FieldPath,
    target_dataset: DatasetReference,
    target_path: FieldPath,
    derivation: FieldDerivationKind,
    step_id: StepId,
) -> FieldLineageEdge:
    return FieldLineageEdge(
        source=FieldReference(source_dataset, source_path),
        target=FieldReference(target_dataset, target_path),
        derivation=derivation,
        step_id=step_id,
        confidence=LineageConfidence.EXACT,
    )


def _dependency(
    source_dataset: DatasetReference,
    source_path: FieldPath,
    target_dataset: DatasetReference,
    kind: FieldDependencyKind,
    step_id: StepId,
) -> FieldDependency:
    return FieldDependency(
        field=FieldReference(source_dataset, source_path),
        target_dataset=target_dataset,
        kind=kind,
        step_id=step_id,
        confidence=LineageConfidence.EXACT,
    )


def _direct_edges(
    source_ref: DatasetReference,
    target_ref: DatasetReference,
    field_names: tuple[str, ...],
    step_id: StepId,
) -> tuple[FieldLineageEdge, ...]:
    return tuple(
        _field_edge(
            source_ref,
            FieldPath.of(name),
            target_ref,
            FieldPath.of(name),
            FieldDerivationKind.DIRECT,
            step_id,
        )
        for name in field_names
    )


def _single(
    values: tuple[DatasetReference, ...],
) -> DatasetReference:
    if len(values) != 1:
        raise UnsupportedLineageError(
            f"Unary lineage requires one input Dataset, received {len(values)}."
        )
    return values[0]


def _binary(
    values: tuple[DatasetReference, ...],
) -> tuple[DatasetReference, DatasetReference]:
    if len(values) != 2:
        raise UnsupportedLineageError(
            f"Binary lineage requires two input Datasets, received {len(values)}."
        )
    return values[0], values[1]


_T = TypeVar("_T", bound=Hashable)


def _dedupe(values: Iterable[_T]) -> tuple[_T, ...]:
    return tuple(dict.fromkeys(values))
