"""Logical Dataset metadata."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    """Portable descriptive metadata attached to a logical Dataset."""

    name: str | None = None
    description: str | None = None
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.name is not None and not self.name.strip():
            raise ValueError("Dataset metadata name must not be blank.")
        if self.description is not None and not self.description.strip():
            raise ValueError("Dataset metadata description must not be blank.")
        if not isinstance(self.tags, frozenset):
            raise TypeError("Dataset metadata tags must be provided as a frozenset.")
        if any(not tag or not tag.strip() for tag in self.tags):
            raise ValueError("Dataset metadata tags must not be blank.")
