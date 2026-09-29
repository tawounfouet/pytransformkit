"""Logical plan dependencies."""

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.shared.identifiers import NodeId


class DependencyKind(StrEnum):
    DATA = "data"


@dataclass(frozen=True, slots=True)
class Dependency:
    """Directed data dependency between two internal logical-plan nodes."""

    source: NodeId
    target: NodeId
    kind: DependencyKind = DependencyKind.DATA
    input_index: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.source, NodeId):
            raise TypeError("Dependency source must be a NodeId.")
        if not isinstance(self.target, NodeId):
            raise TypeError("Dependency target must be a NodeId.")
        if not isinstance(self.kind, DependencyKind):
            raise TypeError("Dependency kind must be a DependencyKind.")
        if isinstance(self.input_index, bool) or not isinstance(self.input_index, int):
            raise TypeError("Dependency input_index must be an integer.")
        if self.input_index < 0:
            raise ValueError("Dependency input_index must be non-negative.")
        if self.source == self.target:
            raise ValueError("A logical dependency cannot be self-referential.")
