"""Immutable logical Pipeline aggregate."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pytransformkit.domain.data.data_types import DataType
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.pipelines.dependencies import Dependency
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.pipelines.validation import PipelineGraphValidator
from pytransformkit.domain.shared.identifiers import PipelineId
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.casting import (
    CastPolicy,
    CastTransformation,
)
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
    DeduplicationStrategy,
)
from pytransformkit.domain.transformations.derivation import (
    DeriveTransformation,
)
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
from pytransformkit.domain.transformations.sorting import (
    NullOrder,
    SortDirection,
    SortKey,
    SortTransformation,
)


@dataclass(frozen=True, slots=True, eq=False)
class Pipeline:
    """Single-input/single-output immutable Pipeline aggregate."""

    id: PipelineId
    name: str
    nodes: tuple[PipelineNode, ...]
    dependencies: tuple[Dependency, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.id, PipelineId):
            raise TypeError("Pipeline id must be a PipelineId.")
        if not self.name or not self.name.strip():
            raise ValueError("Pipeline name must not be empty.")
        if not isinstance(self.nodes, tuple):
            raise TypeError("Pipeline nodes must be provided as a tuple.")
        if not isinstance(self.dependencies, tuple):
            raise TypeError("Pipeline dependencies must be provided as a tuple.")
        PipelineGraphValidator().validate(self.nodes, self.dependencies)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pipeline):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def create(
        cls,
        name: str,
        input_schema: Schema,
        *,
        input_name: str = "input",
        output_name: str = "output",
    ) -> Pipeline:
        input_node = InputNode.create(input_name, input_schema)
        output_node = OutputNode.create(output_name)

        return cls(
            id=PipelineId.new(),
            name=name,
            nodes=(input_node, output_node),
            dependencies=(
                Dependency(
                    source=input_node.id,
                    target=output_node.id,
                ),
            ),
        )

    @property
    def input_node(self) -> InputNode:
        return next(node for node in self.nodes if isinstance(node, InputNode))

    @property
    def output_node(self) -> OutputNode:
        return next(node for node in self.nodes if isinstance(node, OutputNode))

    @property
    def transformation_nodes(self) -> tuple[TransformationNode, ...]:
        return tuple(
            node for node in self.nodes if isinstance(node, TransformationNode)
        )

    def then(
        self,
        transformation: TransformationSpec,
    ) -> Pipeline:
        """Append a Transformation before the Pipeline output."""
        if not isinstance(transformation, TransformationSpec):
            raise TypeError("Pipeline transformation must be a TransformationSpec.")

        output_node = self.output_node
        incoming_to_output = tuple(
            dependency
            for dependency in self.dependencies
            if dependency.target == output_node.id
        )
        predecessor = incoming_to_output[0].source
        new_node = TransformationNode.create(transformation)

        dependencies = tuple(
            dependency
            for dependency in self.dependencies
            if dependency.target != output_node.id
        ) + (
            Dependency(
                source=predecessor,
                target=new_node.id,
            ),
            Dependency(
                source=new_node.id,
                target=output_node.id,
            ),
        )

        nodes = tuple(
            node for node in self.nodes if not isinstance(node, OutputNode)
        ) + (
            new_node,
            output_node,
        )

        return Pipeline(
            id=self.id,
            name=self.name,
            nodes=nodes,
            dependencies=dependencies,
        )

    def select(self, *fields: str) -> Pipeline:
        return self.then(
            SelectTransformation(fields=tuple(FieldPath.of(field) for field in fields))
        )

    def drop(self, *fields: str) -> Pipeline:
        return self.then(
            DropTransformation(fields=tuple(FieldPath.of(field) for field in fields))
        )

    def rename(self, mapping: Mapping[str, str]) -> Pipeline:
        return self.then(RenameTransformation.from_mapping(mapping))

    def filter(self, condition: Expression) -> Pipeline:
        return self.then(FilterTransformation(condition=condition))

    def limit(self, count: int) -> Pipeline:
        return self.then(LimitTransformation(count=count))

    def distinct(self) -> Pipeline:
        return self.then(DistinctTransformation())

    def cast(
        self,
        field: str,
        target_type: DataType,
        *,
        policy: CastPolicy = CastPolicy.RAISE,
    ) -> Pipeline:
        return self.then(
            CastTransformation(
                field=FieldPath.of(field),
                target_type=target_type,
                policy=policy,
            )
        )

    def derive(
        self,
        field_name: str,
        expression: Expression,
        *,
        replace_existing: bool = False,
    ) -> Pipeline:
        return self.then(
            DeriveTransformation(
                field_name=field_name,
                expression=expression,
                replace_existing=replace_existing,
            )
        )

    def sort(
        self,
        *fields: str,
        direction: SortDirection = SortDirection.ASC,
        nulls: NullOrder = NullOrder.LAST,
    ) -> Pipeline:
        return self.then(
            SortTransformation(
                keys=tuple(
                    SortKey(
                        field=FieldPath.of(field),
                        direction=direction,
                        nulls=nulls,
                    )
                    for field in fields
                )
            )
        )

    def deduplicate(
        self,
        *,
        keys: tuple[str, ...],
        keep: DeduplicationStrategy = DeduplicationStrategy.FIRST,
    ) -> Pipeline:
        return self.then(
            DeduplicateTransformation(
                keys=tuple(FieldPath.of(key) for key in keys),
                keep=keep,
            )
        )
