"""Internal logical-plan node model.

These graph nodes are implementation details shared by the legacy Pipeline facade
and the V1 TransformationPlan authoring model. They are intentionally not part
of the stable package-root API.
"""

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.shared.identifiers import DatasetId, NodeId, StepId
from pytransformkit.domain.transformations.base import TransformationSpec


class PipelineNodeKind(StrEnum):
    INPUT = "input"
    TRANSFORMATION = "transformation"
    OUTPUT = "output"


@dataclass(frozen=True, slots=True)
class PipelineNode:
    """Base immutable internal logical-plan node."""

    id: NodeId
    kind: PipelineNodeKind

    def __post_init__(self) -> None:
        if not isinstance(self.id, NodeId):
            raise TypeError("Logical node id must be a NodeId.")
        if not isinstance(self.kind, PipelineNodeKind):
            raise TypeError("Logical node kind must be a PipelineNodeKind.")


@dataclass(frozen=True, slots=True)
class InputNode(PipelineNode):
    """One named logical input."""

    name: str
    schema: Schema
    dataset_id: DatasetId | None = None

    def __post_init__(self) -> None:
        super(InputNode, self).__post_init__()
        if self.kind is not PipelineNodeKind.INPUT:
            raise TypeError("InputNode kind must be PipelineNodeKind.INPUT.")
        if not self.name or not self.name.strip():
            raise ValueError("Input node name must not be empty.")
        if not isinstance(self.schema, Schema):
            raise TypeError("Input node schema must be a Schema.")
        if self.dataset_id is not None and not isinstance(
            self.dataset_id,
            DatasetId,
        ):
            raise TypeError("Input node dataset_id must be a DatasetId.")

    @classmethod
    def create(cls, name: str, schema: Schema) -> "InputNode":
        return cls(
            id=NodeId.new(),
            kind=PipelineNodeKind.INPUT,
            name=name,
            schema=schema,
            dataset_id=DatasetId.new(),
        )


@dataclass(frozen=True, slots=True)
class TransformationNode(PipelineNode):
    """One occurrence of a Transformation inside a logical plan."""

    step_id: StepId
    transformation: TransformationSpec
    name: str | None = None
    dataset_id: DatasetId | None = None

    def __post_init__(self) -> None:
        super(TransformationNode, self).__post_init__()
        if self.kind is not PipelineNodeKind.TRANSFORMATION:
            raise TypeError(
                "TransformationNode kind must be PipelineNodeKind.TRANSFORMATION."
            )
        if not isinstance(self.step_id, StepId):
            raise TypeError("Transformation node step_id must be a StepId.")
        if not isinstance(self.transformation, TransformationSpec):
            raise TypeError(
                "Transformation node transformation must be a TransformationSpec."
            )
        if self.name is not None and not self.name.strip():
            raise ValueError("Transformation node name must not be blank.")
        if self.dataset_id is not None and not isinstance(
            self.dataset_id,
            DatasetId,
        ):
            raise TypeError("Transformation node dataset_id must be a DatasetId.")

    @classmethod
    def create(
        cls,
        transformation: TransformationSpec,
        *,
        name: str | None = None,
    ) -> "TransformationNode":
        return cls(
            id=NodeId.new(),
            kind=PipelineNodeKind.TRANSFORMATION,
            step_id=StepId.new(),
            transformation=transformation,
            name=name,
            dataset_id=DatasetId.new(),
        )


@dataclass(frozen=True, slots=True)
class OutputNode(PipelineNode):
    """One named logical output."""

    name: str

    def __post_init__(self) -> None:
        super(OutputNode, self).__post_init__()
        if self.kind is not PipelineNodeKind.OUTPUT:
            raise TypeError("OutputNode kind must be PipelineNodeKind.OUTPUT.")
        if not self.name or not self.name.strip():
            raise ValueError("Output node name must not be empty.")

    @classmethod
    def create(cls, name: str) -> "OutputNode":
        return cls(
            id=NodeId.new(),
            kind=PipelineNodeKind.OUTPUT,
            name=name,
        )
