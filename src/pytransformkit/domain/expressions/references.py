"""Logical column references."""

from dataclasses import dataclass

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.base import Expression


@dataclass(frozen=True, slots=True, eq=False)
class ColumnReference(Expression):
    """Reference to a logical field path."""

    path: FieldPath

    def __post_init__(self) -> None:
        if not isinstance(self.path, FieldPath):
            raise TypeError("ColumnReference path must be a FieldPath.")
