"""Logical Dataset statistics."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetStatistics:
    """Optional lightweight statistics associated with a Dataset snapshot."""

    row_count: int | None = None
    byte_size: int | None = None
    field_count: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("row_count", self.row_count),
            ("byte_size", self.byte_size),
            ("field_count", self.field_count),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative.")
