"""Ergonomic authoring builder for immutable TransformationPlan values."""

from __future__ import annotations

from collections.abc import Mapping

from pytransformkit.domain.data.data_types import DataType
from pytransformkit.domain.data.dataset import Dataset
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.metadata import DatasetMetadata
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.aggregate import AggregateExpression
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.pipelines.dependencies import Dependency
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.plans.transformation_plan import TransformationPlan
from pytransformkit.domain.quality.rules import ValidationSpec
from pytransformkit.domain.shared.identifiers import (
    DatasetId,
    NodeId,
    TransformationPlanId,
)
from pytransformkit.domain.transformations.aggregation import AggregateTransformation
from pytransformkit.domain.transformations.base import TransformationSpec
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
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinKey,
    JoinTransformation,
    JoinType,
    NullJoinPolicy,
    UnionTransformation,
)
from pytransformkit.domain.transformations.reshaping import (
    ExplodeTransformation,
    FlattenTransformation,
    PivotAggregation,
    PivotTransformation,
    UnpivotTransformation,
)
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.domain.transformations.sorting import (
    NullOrder,
    SortDirection,
    SortKey,
    SortTransformation,
)
from pytransformkit.errors.pipeline import InvalidPipelineError


class TransformationPlanBuilder:
    """Mutable authoring helper that emits one immutable TransformationPlan."""

    def __init__(
        self,
        name: str,
        *,
        schema_resolver: OutputSchemaResolver | None = None,
    ) -> None:
        if not name or not name.strip():
            raise ValueError("TransformationPlan name must not be empty.")
        self._name = name
        self._nodes: list[PipelineNode] = []
        self._dependencies: list[Dependency] = []
        self._dataset_node: dict[DatasetId, NodeId] = {}
        self._input_names: set[str] = set()
        self._output_names: set[str] = set()
        self._schema_resolver = schema_resolver or OutputSchemaResolver()

    def input(self, name: str, *, schema: Schema) -> Dataset:
        """Declare one named logical plan input."""
        if name in self._input_names:
            raise InvalidPipelineError(
                f"TransformationPlan input {name!r} is already declared."
            )
        node = InputNode.create(name, schema)
        self._nodes.append(node)
        self._input_names.add(name)
        assert node.dataset_id is not None
        return self._new_dataset(name, schema, node.id, node.dataset_id)

    def apply(
        self,
        name: str,
        *,
        source: Dataset,
        transformation: TransformationSpec,
    ) -> Dataset:
        """Apply one unary logical Transformation."""
        source_node = self._node_for(source)
        output_schema = self._schema_resolver.resolve(
            transformation,
            source.schema,
        )
        node = TransformationNode.create(
            transformation,
            name=name,
        )
        self._nodes.append(node)
        self._dependencies.append(
            Dependency(
                source=source_node,
                target=node.id,
                input_index=0,
            )
        )
        assert node.dataset_id is not None
        return self._new_dataset(
            name,
            output_schema,
            node.id,
            node.dataset_id,
        )

    def select(
        self,
        name: str,
        *,
        source: Dataset,
        columns: tuple[str, ...],
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=SelectTransformation(
                fields=tuple(FieldPath.of(column) for column in columns)
            ),
        )

    def drop(
        self,
        name: str,
        *,
        source: Dataset,
        columns: tuple[str, ...],
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=DropTransformation(
                fields=tuple(FieldPath.of(column) for column in columns)
            ),
        )

    def rename(
        self,
        name: str,
        *,
        source: Dataset,
        mapping: Mapping[str, str],
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=RenameTransformation.from_mapping(mapping),
        )

    def filter(
        self,
        name: str,
        *,
        source: Dataset,
        where: Expression,
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=FilterTransformation(condition=where),
        )

    def limit(
        self,
        name: str,
        *,
        source: Dataset,
        count: int,
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=LimitTransformation(count=count),
        )

    def distinct(self, name: str, *, source: Dataset) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=DistinctTransformation(),
        )

    def cast(
        self,
        name: str,
        *,
        source: Dataset,
        field: str,
        target_type: DataType,
        policy: CastPolicy = CastPolicy.RAISE,
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=CastTransformation(
                field=FieldPath.of(field),
                target_type=target_type,
                policy=policy,
            ),
        )

    def derive(
        self,
        name: str,
        *,
        source: Dataset,
        field_name: str,
        expression: Expression,
        replace_existing: bool = False,
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=DeriveTransformation(
                field_name=field_name,
                expression=expression,
                replace_existing=replace_existing,
            ),
        )

    def sort(
        self,
        name: str,
        *,
        source: Dataset,
        by: tuple[str, ...],
        direction: SortDirection = SortDirection.ASC,
        nulls: NullOrder = NullOrder.LAST,
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=SortTransformation(
                keys=tuple(
                    SortKey(
                        field=FieldPath.of(field),
                        direction=direction,
                        nulls=nulls,
                    )
                    for field in by
                )
            ),
        )

    def deduplicate(
        self,
        name: str,
        *,
        source: Dataset,
        keys: tuple[str, ...],
        keep: DeduplicationStrategy = DeduplicationStrategy.FIRST,
    ) -> Dataset:
        return self.apply(
            name,
            source=source,
            transformation=DeduplicateTransformation(
                keys=tuple(FieldPath.of(key) for key in keys),
                keep=keep,
            ),
        )

    def aggregate(
        self,
        name: str,
        *,
        source: Dataset,
        group_by: tuple[Expression, ...] = (),
        metrics: Mapping[str, AggregateExpression],
    ) -> Dataset:
        """Group rows and compute named aggregate metrics."""
        return self.apply(
            name,
            source=source,
            transformation=AggregateTransformation.from_mapping(
                group_by=group_by,
                metrics=metrics,
            ),
        )

    def pivot(
        self,
        name: str,
        *,
        source: Dataset,
        index: tuple[str, ...],
        columns: str,
        values: str,
        categories: tuple[str, ...],
        aggregation: PivotAggregation,
    ) -> Dataset:
        """Pivot explicit categories into deterministic output fields."""
        return self.apply(
            name,
            source=source,
            transformation=PivotTransformation(
                index=tuple(FieldPath.of(field) for field in index),
                columns=FieldPath.of(columns),
                values=FieldPath.of(values),
                categories=categories,
                aggregation=aggregation,
            ),
        )

    def unpivot(
        self,
        name: str,
        *,
        source: Dataset,
        id_vars: tuple[str, ...],
        value_vars: tuple[str, ...],
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> Dataset:
        """Unpivot explicit value columns into variable/value rows."""
        return self.apply(
            name,
            source=source,
            transformation=UnpivotTransformation(
                id_vars=tuple(FieldPath.of(field) for field in id_vars),
                value_vars=tuple(FieldPath.of(field) for field in value_vars),
                variable_name=variable_name,
                value_name=value_name,
            ),
        )

    def explode(
        self,
        name: str,
        *,
        source: Dataset,
        field: str,
    ) -> Dataset:
        """Explode one top-level List field."""
        return self.apply(
            name,
            source=source,
            transformation=ExplodeTransformation(
                field=FieldPath.of(field),
            ),
        )

    def flatten(
        self,
        name: str,
        *,
        source: Dataset,
        field: str,
        prefix: str | None = None,
    ) -> Dataset:
        """Flatten one top-level Struct field into deterministic columns."""
        return self.apply(
            name,
            source=source,
            transformation=FlattenTransformation(
                field=FieldPath.of(field),
                prefix=prefix,
            ),
        )

    def validate(
        self,
        name: str,
        *,
        source: Dataset,
        spec: ValidationSpec,
    ) -> Dataset:
        """Validate logical data without changing rows or Schema."""
        return self.apply(
            name,
            source=source,
            transformation=QualityGate(spec=spec),
        )

    def join(
        self,
        name: str,
        *,
        left: Dataset,
        right: Dataset,
        how: JoinType | str = JoinType.INNER,
        on: tuple[tuple[str, str], ...] | tuple[str, ...] = (),
        nulls: NullJoinPolicy = NullJoinPolicy.MATCH,
        right_suffix: str = "_right",
    ) -> Dataset:
        join_type = how if isinstance(how, JoinType) else JoinType(how)
        keys = _join_keys(on)
        transformation = JoinTransformation(
            keys=keys,
            how=join_type,
            nulls=nulls,
            right_suffix=right_suffix,
        )
        return self._apply_binary(
            name,
            left=left,
            right=right,
            transformation=transformation,
        )

    def union(
        self,
        name: str,
        *,
        left: Dataset,
        right: Dataset,
        all: bool = False,
    ) -> Dataset:
        return self._apply_binary(
            name,
            left=left,
            right=right,
            transformation=UnionTransformation(all=all),
        )

    def intersect(
        self,
        name: str,
        *,
        left: Dataset,
        right: Dataset,
    ) -> Dataset:
        return self._apply_binary(
            name,
            left=left,
            right=right,
            transformation=IntersectTransformation(),
        )

    def except_(
        self,
        name: str,
        *,
        left: Dataset,
        right: Dataset,
    ) -> Dataset:
        return self._apply_binary(
            name,
            left=left,
            right=right,
            transformation=ExceptTransformation(),
        )

    def output(self, name: str, dataset: Dataset) -> TransformationPlanBuilder:
        """Declare one named plan output."""
        if name in self._output_names:
            raise InvalidPipelineError(
                f"TransformationPlan output {name!r} is already declared."
            )
        source_node = self._node_for(dataset)
        node = OutputNode.create(name)
        self._nodes.append(node)
        self._dependencies.append(
            Dependency(
                source=source_node,
                target=node.id,
                input_index=0,
            )
        )
        self._output_names.add(name)
        return self

    def build(self) -> TransformationPlan:
        """Freeze the current declaration into an immutable TransformationPlan."""
        if not self._output_names:
            raise InvalidPipelineError(
                "TransformationPlan requires at least one declared output."
            )
        return TransformationPlan(
            id=TransformationPlanId.new(),
            name=self._name,
            nodes=tuple(self._nodes),
            dependencies=tuple(self._dependencies),
        )

    def _apply_binary(
        self,
        name: str,
        *,
        left: Dataset,
        right: Dataset,
        transformation: TransformationSpec,
    ) -> Dataset:
        left_node = self._node_for(left)
        right_node = self._node_for(right)
        output_schema = self._schema_resolver.resolve_many(
            transformation,
            (left.schema, right.schema),
        )
        node = TransformationNode.create(
            transformation,
            name=name,
        )
        self._nodes.append(node)
        self._dependencies.extend(
            (
                Dependency(
                    source=left_node,
                    target=node.id,
                    input_index=0,
                ),
                Dependency(
                    source=right_node,
                    target=node.id,
                    input_index=1,
                ),
            )
        )
        assert node.dataset_id is not None
        return self._new_dataset(
            name,
            output_schema,
            node.id,
            node.dataset_id,
        )

    def _new_dataset(
        self,
        name: str,
        schema: Schema,
        node_id: NodeId,
        dataset_id: DatasetId,
    ) -> Dataset:
        dataset = Dataset(
            id=dataset_id,
            schema=schema,
            metadata=DatasetMetadata(name=name),
        )
        self._dataset_node[dataset.id] = node_id
        return dataset

    def _node_for(self, dataset: Dataset) -> NodeId:
        if not isinstance(dataset, Dataset):
            raise TypeError("TransformationPlan sources must be Dataset values.")
        try:
            return self._dataset_node[dataset.id]
        except KeyError as error:
            raise InvalidPipelineError(
                "Dataset does not belong to this TransformationPlanBuilder."
            ) from error


def _join_keys(
    value: tuple[tuple[str, str], ...] | tuple[str, ...],
) -> tuple[JoinKey, ...]:
    keys: list[JoinKey] = []
    for item in value:
        if isinstance(item, str):
            keys.append(JoinKey.of(item))
            continue
        if (
            isinstance(item, tuple)
            and len(item) == 2
            and all(isinstance(part, str) for part in item)
        ):
            keys.append(JoinKey.of(item[0], item[1]))
            continue
        raise TypeError(
            "Join on must contain field names or (left, right) field pairs."
        )
    return tuple(keys)
