"""Logical Schema field model."""

from dataclasses import dataclass

from pytransformkit.domain.data.data_types import DataType


@dataclass(frozen=True, slots=True)
class Field:
    """Immutable logical field definition."""

    name: str
    data_type: DataType
    nullable: bool = True
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Field name must not be empty.")
        if not isinstance(self.data_type, DataType):
            raise TypeError("Field data_type must be a PyTransformKit DataType.")
