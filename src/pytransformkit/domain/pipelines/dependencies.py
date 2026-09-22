"""Logical Pipeline dependencies."""

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.shared.identifiers import NodeId


class DependencyKind(StrEnum):
    DATA = "data"


@dataclass(frozen=True, slots=True)
class Dependency:
    """Directed dependency between two Pipeline nodes."""

    source: NodeId
    target: NodeId
    kind: DependencyKind = DependencyKind.DATA

    def __post_init__(self) -> None:
        if not isinstance(self.source, NodeId):
            raise TypeError("Dependency source must be a NodeId.")
        if not isinstance(self.target, NodeId):
            raise TypeError("Dependency target must be a NodeId.")
        if not isinstance(self.kind, DependencyKind):
            raise TypeError("Dependency kind must be a DependencyKind.")
        if self.source == self.target:
            raise ValueError("A Pipeline dependency cannot be self-referential.")
