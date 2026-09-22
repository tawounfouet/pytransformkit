"""Logical literal Expressions."""

from dataclasses import dataclass

from pytransformkit.domain.data.data_types import DataType
from pytransformkit.domain.expressions.base import Expression


@dataclass(frozen=True, slots=True, eq=False)
class Literal(Expression):
    """Portable scalar literal used inside an Expression tree."""

    value: object
    data_type: DataType | None = None

    def __post_init__(self) -> None:
        if self.data_type is not None and not isinstance(self.data_type, DataType):
            raise TypeError("Literal data_type must be a PyTransformKit DataType.")
