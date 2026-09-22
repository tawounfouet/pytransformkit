"""Logical Pipeline node model."""

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.shared.identifiers import NodeId, StepId
from pytransformkit.domain.transformations.base import TransformationSpec


class PipelineNodeKind(StrEnum):
    INPUT = "input"
    TRANSFORMATION = "transformation"
    OUTPUT = "output"


@dataclass(frozen=True, slots=True)
class PipelineNode:
    """Base immutable Pipeline graph node."""

    id: NodeId
    kind: PipelineNodeKind

    def __post_init__(self) -> None:
        if not isinstance(self.id, NodeId):
            raise TypeError("Pipeline node id must be a NodeId.")
        if not isinstance(self.kind, PipelineNodeKind):
            raise TypeError("Pipeline node kind must be a PipelineNodeKind.")


@dataclass(frozen=True, slots=True)
class InputNode(PipelineNode):
    """Single logical Pipeline input for the initial MVP."""

    name: str
    schema: Schema

    def __post_init__(self) -> None:
        super(InputNode, self).__post_init__()
        if self.kind is not PipelineNodeKind.INPUT:
            raise TypeError("InputNode kind must be PipelineNodeKind.INPUT.")
        if not self.name or not self.name.strip():
            raise ValueError("Input node name must not be empty.")
        if not isinstance(self.schema, Schema):
            raise TypeError("Input node schema must be a Schema.")

    @classmethod
    def create(cls, name: str, schema: Schema) -> "InputNode":
        return cls(
            id=NodeId.new(),
            kind=PipelineNodeKind.INPUT,
            name=name,
            schema=schema,
        )


@dataclass(frozen=True, slots=True)
class TransformationNode(PipelineNode):
    """One occurrence of a Transformation inside a Pipeline."""

    step_id: StepId
    transformation: TransformationSpec

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

    @classmethod
    def create(
        cls,
        transformation: TransformationSpec,
    ) -> "TransformationNode":
        return cls(
            id=NodeId.new(),
            kind=PipelineNodeKind.TRANSFORMATION,
            step_id=StepId.new(),
            transformation=transformation,
        )


@dataclass(frozen=True, slots=True)
class OutputNode(PipelineNode):
    """Single logical Pipeline output for the initial MVP."""

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
